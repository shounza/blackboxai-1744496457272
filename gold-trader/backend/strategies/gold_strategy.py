import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from datetime import datetime
from utils.indicators import TechnicalIndicators
from broker.puprime_api import PuPrimeAPI
from database.database_setup import get_db_session
from database.models import Trade, Strategy, PerformanceMetrics
from config import Config
from logger import logger, log_trade, log_strategy, log_error

class GoldStrategy:
    def __init__(self, strategy_config: Dict):
        """
        Initialize the GOLD trading strategy
        
        Args:
            strategy_config: Dictionary containing strategy parameters
        """
        self.config = strategy_config
        self.broker = PuPrimeAPI()
        self.position_size = self.config.get('position_size', Config.MAX_POSITION_SIZE)
        self.stop_loss_percent = self.config.get('stop_loss_percent', Config.STOP_LOSS_PERCENT)
        self.take_profit_percent = self.config.get('take_profit_percent', Config.TAKE_PROFIT_PERCENT)
        self.indicators = None
        self.current_position = None

    def initialize_indicators(self, data: pd.DataFrame):
        """Initialize technical indicators with price data"""
        try:
            self.indicators = TechnicalIndicators(data)
            logger.info("Technical indicators initialized successfully")
        except Exception as e:
            log_error("INDICATOR_INIT_ERROR", str(e))
            raise

    def calculate_position_size(self, account_balance: float) -> float:
        """
        Calculate position size based on risk parameters
        
        Args:
            account_balance: Current account balance
        """
        try:
            # Risk per trade (e.g., 1% of account balance)
            risk_amount = account_balance * (self.stop_loss_percent / 100)
            
            # Get current GOLD price
            current_price = float(self.broker.get_gold_price().get('price'))
            
            # Calculate position size in lots
            position_size = min(
                risk_amount / (current_price * self.stop_loss_percent / 100),
                self.position_size
            )
            
            return round(position_size, 2)
        except Exception as e:
            log_error("POSITION_SIZE_CALC_ERROR", str(e))
            raise

    def check_trend(self, data: pd.DataFrame) -> str:
        """
        Determine the current trend using multiple timeframes
        
        Returns:
            str: 'UPTREND', 'DOWNTREND', or 'NEUTRAL'
        """
        try:
            # Calculate EMAs
            ema_short = self.indicators.calculate_ema(9)
            ema_medium = self.indicators.calculate_ema(21)
            ema_long = self.indicators.calculate_ema(50)
            
            # Get latest values
            current_ema_short = ema_short.iloc[-1]
            current_ema_medium = ema_medium.iloc[-1]
            current_ema_long = ema_long.iloc[-1]
            
            # Determine trend
            if current_ema_short > current_ema_medium > current_ema_long:
                return 'UPTREND'
            elif current_ema_short < current_ema_medium < current_ema_long:
                return 'DOWNTREND'
            else:
                return 'NEUTRAL'
                
        except Exception as e:
            log_error("TREND_CHECK_ERROR", str(e))
            raise

    def check_support_resistance(self, price: float) -> Tuple[Optional[float], Optional[float]]:
        """
        Find nearest support and resistance levels
        
        Args:
            price: Current price
        """
        try:
            support_levels, resistance_levels = self.indicators.calculate_support_resistance()
            
            # Find nearest support
            supports_below = [s for s in support_levels if s < price]
            nearest_support = max(supports_below) if supports_below else None
            
            # Find nearest resistance
            resistances_above = [r for r in resistance_levels if r > price]
            nearest_resistance = min(resistances_above) if resistances_above else None
            
            return nearest_support, nearest_resistance
            
        except Exception as e:
            log_error("SUPPORT_RESISTANCE_ERROR", str(e))
            raise

    def check_entry_conditions(self, data: pd.DataFrame) -> Tuple[bool, str, Dict]:
        """
        Check if entry conditions are met
        
        Returns:
            Tuple containing:
            - Boolean indicating if entry conditions are met
            - Trading side ('BUY' or 'SELL')
            - Dictionary with analysis details
        """
        try:
            # Get current price
            current_price = data['close'].iloc[-1]
            
            # Get trend
            trend = self.check_trend(data)
            
            # Calculate indicators
            rsi = self.indicators.calculate_rsi()
            current_rsi = rsi.iloc[-1]
            
            macd_line, signal_line, histogram = self.indicators.calculate_macd()
            current_macd = macd_line.iloc[-1]
            current_signal = signal_line.iloc[-1]
            
            bb_upper, bb_middle, bb_lower = self.indicators.calculate_bollinger_bands()
            
            # Get nearest support/resistance
            nearest_support, nearest_resistance = self.check_support_resistance(current_price)
            
            analysis = {
                'trend': trend,
                'rsi': current_rsi,
                'macd_line': current_macd,
                'macd_signal': current_signal,
                'nearest_support': nearest_support,
                'nearest_resistance': nearest_resistance
            }
            
            # Buy conditions
            if (trend == 'UPTREND' and
                current_rsi < 70 and
                current_macd > current_signal and
                current_price > bb_middle.iloc[-1] and
                nearest_support is not None):
                
                return True, 'BUY', analysis
                
            # Sell conditions
            elif (trend == 'DOWNTREND' and
                  current_rsi > 30 and
                  current_macd < current_signal and
                  current_price < bb_middle.iloc[-1] and
                  nearest_resistance is not None):
                  
                return True, 'SELL', analysis
                
            return False, None, analysis
            
        except Exception as e:
            log_error("ENTRY_CONDITIONS_ERROR", str(e))
            raise

    def calculate_exit_prices(self, entry_price: float, side: str) -> Tuple[float, float]:
        """
        Calculate stop loss and take profit prices
        
        Args:
            entry_price: Entry price
            side: Trading side ('BUY' or 'SELL')
        """
        try:
            if side == 'BUY':
                stop_loss = entry_price * (1 - self.stop_loss_percent / 100)
                take_profit = entry_price * (1 + self.take_profit_percent / 100)
            else:
                stop_loss = entry_price * (1 + self.stop_loss_percent / 100)
                take_profit = entry_price * (1 - self.take_profit_percent / 100)
                
            return round(stop_loss, 2), round(take_profit, 2)
            
        except Exception as e:
            log_error("EXIT_PRICE_CALC_ERROR", str(e))
            raise

    def execute_trade(self, side: str, analysis: Dict) -> Dict:
        """
        Execute a trade based on strategy signals
        
        Args:
            side: Trading side ('BUY' or 'SELL')
            analysis: Dictionary containing analysis details
        """
        try:
            # Get account information
            account_info = self.broker.get_account_info()
            account_balance = float(account_info.get('balance', 0))
            
            # Calculate position size
            position_size = self.calculate_position_size(account_balance)
            
            # Get current price
            current_price = float(self.broker.get_gold_price().get('price'))
            
            # Calculate stop loss and take profit
            stop_loss, take_profit = self.calculate_exit_prices(current_price, side)
            
            # Place order
            order = self.broker.place_order(
                order_type='MARKET',
                side=side,
                quantity=position_size,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            # Log trade
            log_strategy(
                strategy_name="GOLD_STRATEGY",
                signal_type=side,
                indicators=analysis,
                entry_price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size=position_size
            )
            
            # Store trade in database
            with get_db_session() as session:
                trade = Trade(
                    symbol='XAUUSD',
                    order_type='MARKET',
                    status='EXECUTED',
                    entry_price=current_price,
                    quantity=position_size,
                    take_profit=take_profit,
                    stop_loss=stop_loss,
                    entry_time=datetime.utcnow()
                )
                session.add(trade)
                session.commit()
            
            return order
            
        except Exception as e:
            log_error("TRADE_EXECUTION_ERROR", str(e))
            raise

    def check_exit_conditions(self, position: Dict, data: pd.DataFrame) -> bool:
        """
        Check if exit conditions are met for current position
        
        Args:
            position: Current position information
            data: Price data DataFrame
        """
        try:
            current_price = data['close'].iloc[-1]
            entry_price = float(position['entry_price'])
            position_side = position['side']
            
            # Calculate indicators
            rsi = self.indicators.calculate_rsi()
            current_rsi = rsi.iloc[-1]
            
            macd_line, signal_line, _ = self.indicators.calculate_macd()
            
            # Exit conditions for long positions
            if position_side == 'BUY':
                if (current_rsi > 70 or
                    macd_line.iloc[-1] < signal_line.iloc[-1] or
                    current_price < entry_price * (1 - self.stop_loss_percent / 100)):
                    return True
                    
            # Exit conditions for short positions
            elif position_side == 'SELL':
                if (current_rsi < 30 or
                    macd_line.iloc[-1] > signal_line.iloc[-1] or
                    current_price > entry_price * (1 + self.stop_loss_percent / 100)):
                    return True
                    
            return False
            
        except Exception as e:
            log_error("EXIT_CONDITIONS_ERROR", str(e))
            raise

    def update_performance_metrics(self, trade: Dict):
        """
        Update strategy performance metrics
        
        Args:
            trade: Completed trade information
        """
        try:
            with get_db_session() as session:
                # Get or create metrics for today
                today = datetime.utcnow().date()
                metrics = session.query(PerformanceMetrics).filter(
                    PerformanceMetrics.date == today
                ).first()
                
                if not metrics:
                    metrics = PerformanceMetrics(date=today)
                    session.add(metrics)
                
                # Update metrics
                metrics.total_trades += 1
                
                if trade['profit_loss'] > 0:
                    metrics.winning_trades += 1
                else:
                    metrics.losing_trades += 1
                
                metrics.total_profit_loss += trade['profit_loss']
                metrics.win_rate = (metrics.winning_trades / metrics.total_trades) * 100
                
                session.commit()
                
            logger.info(f"Performance metrics updated for {today}")
            
        except Exception as e:
            log_error("METRICS_UPDATE_ERROR", str(e))
            raise

    def run(self, data: pd.DataFrame):
        """
        Run the trading strategy
        
        Args:
            data: Price data DataFrame
        """
        try:
            # Initialize indicators
            self.initialize_indicators(data)
            
            # Check for open positions
            open_positions = self.broker.get_open_positions()
            
            # If we have an open position, check exit conditions
            if open_positions:
                for position in open_positions:
                    if self.check_exit_conditions(position, data):
                        # Close position
                        self.broker.modify_position(
                            position_id=position['id'],
                            stop_loss=None,  # Remove stop loss to close at market
                            take_profit=None  # Remove take profit to close at market
                        )
                        logger.info(f"Closed position {position['id']}")
                        
            # If no open positions, check entry conditions
            else:
                entry_signal, side, analysis = self.check_entry_conditions(data)
                
                if entry_signal and side:
                    # Execute trade
                    order = self.execute_trade(side, analysis)
                    logger.info(f"Executed {side} order: {order}")
                    
        except Exception as e:
            log_error("STRATEGY_RUN_ERROR", str(e))
            raise

# Example usage:
"""
# Create strategy configuration
strategy_config = {
    'position_size': 0.01,
    'stop_loss_percent': 1.5,
    'take_profit_percent': 3.0
}

# Initialize strategy
strategy = GoldStrategy(strategy_config)

# Get historical data
# ... fetch historical data ...

# Run strategy
strategy.run(historical_data)
"""
