import threading
import time
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from database.database_setup import get_db_session
from database.models import Trade, Strategy, User, OrderType, OrderStatus
from broker.puprime_api import PuPrimeAPI
from utils.indicators import TechnicalIndicators
from config import Config
from logger import logger, log_trade, log_strategy, log_error

class TradingEngine:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(TradingEngine, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.running = False
            self.broker = PuPrimeAPI()
            self.strategies: Dict[int, Strategy] = {}
            self.active_trades: Dict[int, Trade] = {}
            self.thread: Optional[threading.Thread] = None

    def start(self):
        """Start the trading engine."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run)
            self.thread.daemon = True
            self.thread.start()
            logger.info("Trading engine started")

    def stop(self):
        """Stop the trading engine."""
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join()
            logger.info("Trading engine stopped")

    def _run(self):
        """Main trading loop."""
        while self.running:
            try:
                self._process_strategies()
                self._monitor_trades()
                time.sleep(1)  # Prevent excessive CPU usage
            except Exception as e:
                log_error("TRADING_ENGINE_ERROR", str(e))
                time.sleep(5)  # Wait before retrying

    def _process_strategies(self):
        """Process all active trading strategies."""
        with get_db_session() as session:
            active_strategies = session.query(Strategy).filter_by(is_active=True).all()
            
            for strategy in active_strategies:
                try:
                    # Get market data
                    market_data = self.broker.get_market_data(
                        symbol=strategy.symbol,
                        timeframe=strategy.timeframe
                    )
                    
                    # Convert market data to DataFrame
                    df = pd.DataFrame(market_data)
                    
                    # Initialize technical indicators
                    tech_indicators = TechnicalIndicators(df)
                    
                    # Calculate indicators
                    indicators = {
                        'fast_ema': tech_indicators.calculate_ema(strategy.fast_ema).iloc[-1],
                        'slow_ema': tech_indicators.calculate_ema(strategy.slow_ema).iloc[-1],
                        'rsi': tech_indicators.calculate_rsi(strategy.rsi_period).iloc[-1]
                    }
                    
                    # Generate trading signals
                    signal = self._generate_signal(strategy, indicators)
                    
                    if signal:
                        self._execute_trade(strategy, signal, indicators)
                        
                except Exception as e:
                    log_error("STRATEGY_PROCESSING_ERROR", 
                            f"Error processing strategy {strategy.name}: {str(e)}")

    def _generate_signal(self, strategy: Strategy, indicators: Dict) -> Optional[str]:
        """Generate trading signals based on strategy parameters and indicators."""
        try:
            rsi = indicators.get('rsi', 0)
            fast_ema = indicators.get('fast_ema', 0)
            slow_ema = indicators.get('slow_ema', 0)
            
            # RSI conditions
            oversold = rsi < strategy.rsi_oversold
            overbought = rsi > strategy.rsi_overbought
            
            # EMA crossover conditions
            ema_bullish = fast_ema > slow_ema
            ema_bearish = fast_ema < slow_ema
            
            # Generate signals
            if oversold and ema_bullish:
                return "BUY"
            elif overbought and ema_bearish:
                return "SELL"
                
            return None
            
        except Exception as e:
            log_error("SIGNAL_GENERATION_ERROR", str(e))
            return None

    def _execute_trade(self, strategy: Strategy, signal: str, indicators: Dict):
        """Execute trades based on strategy signals."""
        try:
            # Check if we can trade based on risk management rules
            if not self._check_risk_limits(strategy):
                return
                
            # Calculate position size
            position_size = self._calculate_position_size(strategy)
            
            # Get current market price
            current_price = self.broker.get_current_price(strategy.symbol)
            
            # Calculate stop loss and take profit levels
            stop_loss = self._calculate_stop_loss(current_price, strategy, signal)
            take_profit = self._calculate_take_profit(current_price, strategy, signal)
            
            # Execute order
            order = self.broker.place_order(
                symbol=strategy.symbol,
                order_type=OrderType.MARKET,
                side=signal,
                quantity=position_size,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            # Log trade
            log_trade(
                action=signal,
                symbol=strategy.symbol,
                price=current_price,
                quantity=position_size,
                order_type="MARKET",
                status="EXECUTED",
                stop_loss=stop_loss,
                take_profit=take_profit,
                strategy=strategy.name,
                indicators=indicators
            )
            
            # Save trade to database
            with get_db_session() as session:
                trade = Trade(
                    user_id=strategy.user_id,
                    strategy_id=strategy.id,
                    symbol=strategy.symbol,
                    order_type=OrderType.MARKET,
                    status=OrderStatus.EXECUTED,
                    entry_price=current_price,
                    quantity=position_size,
                    stop_loss=stop_loss,
                    take_profit=take_profit
                )
                session.add(trade)
                session.commit()
                
        except Exception as e:
            log_error("TRADE_EXECUTION_ERROR", str(e))

    def _monitor_trades(self):
        """Monitor and update active trades."""
        try:
            with get_db_session() as session:
                active_trades = session.query(Trade).filter_by(
                    status=OrderStatus.EXECUTED,
                    exit_time=None
                ).all()
                
                for trade in active_trades:
                    current_price = self.broker.get_current_price(trade.symbol)
                    
                    # Check stop loss and take profit
                    if self._should_close_trade(trade, current_price):
                        self._close_trade(trade, current_price)
                        
        except Exception as e:
            log_error("TRADE_MONITORING_ERROR", str(e))

    def _should_close_trade(self, trade: Trade, current_price: float) -> bool:
        """Determine if a trade should be closed."""
        if trade.stop_loss and current_price <= trade.stop_loss:
            return True
        if trade.take_profit and current_price >= trade.take_profit:
            return True
        return False

    def _close_trade(self, trade: Trade, exit_price: float):
        """Close a trade and update the database."""
        try:
            # Close position with broker
            self.broker.close_position(trade.symbol)
            
            # Calculate profit/loss
            profit_loss = (exit_price - trade.entry_price) * trade.quantity
            
            # Update trade in database
            with get_db_session() as session:
                trade.exit_price = exit_price
                trade.exit_time = datetime.utcnow()
                trade.profit_loss = profit_loss
                trade.status = OrderStatus.CLOSED
                session.commit()
                
            # Log trade closure
            log_trade(
                action="CLOSE",
                symbol=trade.symbol,
                price=exit_price,
                quantity=trade.quantity,
                order_type="MARKET",
                status="CLOSED",
                profit_loss=profit_loss
            )
            
        except Exception as e:
            log_error("TRADE_CLOSURE_ERROR", str(e))

    def _check_risk_limits(self, strategy: Strategy) -> bool:
        """Check if trading is allowed based on risk management rules."""
        try:
            with get_db_session() as session:
                # Check daily loss limit
                daily_loss = self._calculate_daily_loss(strategy, session)
                if abs(daily_loss) >= strategy.max_daily_loss:
                    logger.warning(f"Daily loss limit reached for strategy {strategy.name}")
                    return False
                    
                # Check weekly loss limit
                weekly_loss = self._calculate_weekly_loss(strategy, session)
                if abs(weekly_loss) >= Config.MAX_WEEKLY_LOSS:
                    logger.warning(f"Weekly loss limit reached for strategy {strategy.name}")
                    return False
                    
                return True
                
        except Exception as e:
            log_error("RISK_CHECK_ERROR", str(e))
            return False

    def _calculate_position_size(self, strategy: Strategy) -> float:
        """Calculate position size based on risk parameters."""
        try:
            account_balance = self.broker.get_account_balance()
            risk_amount = account_balance * (strategy.stop_loss_percent / 100)
            position_size = min(
                strategy.position_size,
                risk_amount / strategy.stop_loss_percent
            )
            return position_size
            
        except Exception as e:
            log_error("POSITION_SIZE_CALCULATION_ERROR", str(e))
            return 0.0

    def _calculate_stop_loss(self, current_price: float, strategy: Strategy, signal: str) -> float:
        """Calculate stop loss level."""
        if signal == "BUY":
            return current_price * (1 - strategy.stop_loss_percent / 100)
        else:
            return current_price * (1 + strategy.stop_loss_percent / 100)

    def _calculate_take_profit(self, current_price: float, strategy: Strategy, signal: str) -> float:
        """Calculate take profit level."""
        if signal == "BUY":
            return current_price * (1 + strategy.take_profit_percent / 100)
        else:
            return current_price * (1 - strategy.take_profit_percent / 100)

    def _calculate_daily_loss(self, strategy: Strategy, session) -> float:
        """Calculate total loss for the current day."""
        today = datetime.utcnow().date()
        daily_trades = session.query(Trade).filter(
            Trade.strategy_id == strategy.id,
            Trade.exit_time >= today
        ).all()
        
        return sum(trade.profit_loss or 0 for trade in daily_trades)

    def _calculate_weekly_loss(self, strategy: Strategy, session) -> float:
        """Calculate total loss for the current week."""
        # Get Monday of current week
        today = datetime.utcnow().date()
        monday = today - timedelta(days=today.weekday())
        
        weekly_trades = session.query(Trade).filter(
            Trade.strategy_id == strategy.id,
            Trade.exit_time >= monday
        ).all()
        
        return sum(trade.profit_loss or 0 for trade in weekly_trades)

    def add_strategy(self, strategy_data: Dict):
        """Add a new trading strategy."""
        try:
            with get_db_session() as session:
                strategy = Strategy(**strategy_data)
                session.add(strategy)
                session.commit()
                self.strategies[strategy.id] = strategy
                logger.info(f"Added new strategy: {strategy.name}")
                
        except Exception as e:
            log_error("STRATEGY_ADDITION_ERROR", str(e))

    def remove_strategy(self, strategy_id: int):
        """Remove a trading strategy."""
        try:
            with get_db_session() as session:
                strategy = session.query(Strategy).get(strategy_id)
                if strategy:
                    strategy.is_active = False
                    session.commit()
                    self.strategies.pop(strategy_id, None)
                    logger.info(f"Removed strategy: {strategy.name}")
                    
        except Exception as e:
            log_error("STRATEGY_REMOVAL_ERROR", str(e))

    def get_active_trades(self) -> List[Trade]:
        """Get list of currently active trades."""
        try:
            with get_db_session() as session:
                return session.query(Trade).filter_by(
                    status=OrderStatus.EXECUTED,
                    exit_time=None
                ).all()
                
        except Exception as e:
            log_error("ACTIVE_TRADES_FETCH_ERROR", str(e))
            return []
