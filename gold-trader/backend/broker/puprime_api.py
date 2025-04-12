import time
from typing import Dict, Optional, List
from datetime import datetime
from config import Config
from logger import logger, log_error

class PuPrimeAPI:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PuPrimeAPI, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self._setup_exchange()
            self._mock_data = {
                'balance': 10000.0,
                'positions': [],
                'orders': [],
                'price': 2000.0  # Mock GOLD price
            }

    def _setup_exchange(self):
        """Initialize mock connection for development."""
        try:
            self.exchange = {
                'apiKey': Config.PUPRIME_API_KEY,
                'secret': Config.PUPRIME_API_SECRET,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',
                }
            }
            logger.info("Mock PuPrime API connection initialized")
        except Exception as e:
            log_error("EXCHANGE_SETUP_ERROR", str(e))
            raise

    def get_market_data(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> List[Dict]:
        """Mock market data fetch."""
        try:
            # Generate mock OHLCV data
            data = []
            base_price = self._mock_data['price']
            
            for i in range(limit):
                timestamp = datetime.now().timestamp() * 1000 - (i * 3600 * 1000)  # 1-hour intervals
                data.append({
                    'timestamp': datetime.fromtimestamp(timestamp / 1000),
                    'open': base_price + (i % 10),
                    'high': base_price + (i % 10) + 5,
                    'low': base_price + (i % 10) - 5,
                    'close': base_price + (i % 10) + 2,
                    'volume': 1000 + (i * 10)
                })
            
            return data
            
        except Exception as e:
            log_error("MARKET_DATA_FETCH_ERROR", str(e))
            return []

    def get_current_price(self, symbol: str) -> float:
        """Get mock current price."""
        try:
            # Simulate small price movements
            self._mock_data['price'] += (time.time() % 2 - 1) * 0.5
            return self._mock_data['price']
        except Exception as e:
            log_error("PRICE_FETCH_ERROR", str(e))
            return 0.0

    def get_account_balance(self) -> float:
        """Get mock account balance."""
        try:
            return self._mock_data['balance']
        except Exception as e:
            log_error("BALANCE_FETCH_ERROR", str(e))
            return 0.0

    def place_order(self, symbol: str, order_type: str, side: str, 
                   quantity: float, price: Optional[float] = None,
                   stop_loss: Optional[float] = None, 
                   take_profit: Optional[float] = None) -> Dict:
        """Place mock order."""
        try:
            order = {
                'id': str(len(self._mock_data['orders']) + 1),
                'symbol': symbol,
                'type': order_type,
                'side': side,
                'quantity': quantity,
                'price': price or self._mock_data['price'],
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'status': 'EXECUTED',
                'timestamp': datetime.utcnow().timestamp()
            }
            
            self._mock_data['orders'].append(order)
            
            # Update mock positions
            position = {
                'id': str(len(self._mock_data['positions']) + 1),
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'entry_price': order['price'],
                'current_price': order['price'],
                'unrealized_pnl': 0.0
            }
            
            self._mock_data['positions'].append(position)
            
            logger.info(f"Mock order placed: {order}")
            return order

        except Exception as e:
            log_error("ORDER_PLACEMENT_ERROR", str(e))
            return {}

    def close_position(self, symbol: str) -> bool:
        """Close mock position."""
        try:
            positions = [p for p in self._mock_data['positions'] if p['symbol'] == symbol]
            if not positions:
                return True

            for position in positions:
                current_price = self.get_current_price(symbol)
                pnl = (current_price - position['entry_price']) * position['quantity']
                if position['side'] == 'SELL':
                    pnl = -pnl

                # Update mock balance
                self._mock_data['balance'] += pnl
                
                # Remove position
                self._mock_data['positions'] = [
                    p for p in self._mock_data['positions'] if p['id'] != position['id']
                ]

            return True

        except Exception as e:
            log_error("POSITION_CLOSURE_ERROR", str(e))
            return False

    def get_position(self, symbol: str) -> Dict:
        """Get mock position."""
        try:
            positions = [p for p in self._mock_data['positions'] if p['symbol'] == symbol]
            return positions[0] if positions else {}
        except Exception as e:
            log_error("POSITION_FETCH_ERROR", str(e))
            return {}

    def get_order_status(self, order_id: str, symbol: str) -> Dict:
        """Get mock order status."""
        try:
            orders = [o for o in self._mock_data['orders'] if o['id'] == order_id]
            return orders[0] if orders else {}
        except Exception as e:
            log_error("ORDER_STATUS_FETCH_ERROR", str(e))
            return {}

    def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel mock order."""
        try:
            self._mock_data['orders'] = [
                o for o in self._mock_data['orders'] if o['id'] != order_id
            ]
            return True
        except Exception as e:
            log_error("ORDER_CANCELLATION_ERROR", str(e))
            return False

    def get_trading_fees(self, symbol: str) -> Dict:
        """Get mock trading fees."""
        try:
            return {
                'maker': 0.001,  # 0.1%
                'taker': 0.002   # 0.2%
            }
        except Exception as e:
            log_error("FEE_FETCH_ERROR", str(e))
            return {}

    def get_order_book(self, symbol: str, limit: int = 20) -> Dict:
        """Get mock order book."""
        try:
            current_price = self.get_current_price(symbol)
            asks = [(current_price + (i * 0.1), 1.0) for i in range(limit)]
            bids = [(current_price - (i * 0.1), 1.0) for i in range(limit)]
            
            return {
                'asks': asks,
                'bids': bids
            }
        except Exception as e:
            log_error("ORDER_BOOK_FETCH_ERROR", str(e))
            return {'asks': [], 'bids': []}

    def get_open_positions(self) -> List[Dict]:
        """Get all mock open positions."""
        try:
            return self._mock_data['positions']
        except Exception as e:
            log_error("OPEN_POSITIONS_FETCH_ERROR", str(e))
            return []

    def get_account_info(self) -> Dict:
        """Get mock account information."""
        try:
            return {
                'balance': self._mock_data['balance'],
                'equity': self._mock_data['balance'],
                'margin': 0.0,
                'free_margin': self._mock_data['balance'],
                'margin_level': 100.0,
                'positions': len(self._mock_data['positions'])
            }
        except Exception as e:
            log_error("ACCOUNT_INFO_FETCH_ERROR", str(e))
            return {}
