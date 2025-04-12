import requests
import hmac
import hashlib
import time
from urllib.parse import urlencode
import json
from typing import Dict, Optional, Union
from config import Config
from logger import logger, log_error, log_trade

class PuPrimeAPI:
    def __init__(self):
        self.api_key = Config.PUPRIME_API_KEY
        self.api_secret = Config.PUPRIME_API_SECRET
        self.base_url = Config.PUPRIME_API_URL
        self.session = requests.Session()
        self._init_session()

    def _init_session(self):
        """Initialize session with default headers"""
        self.session.headers.update({
            'Content-Type': 'application/json',
            'X-API-KEY': self.api_key
        })

    def _generate_signature(self, params: Dict) -> str:
        """Generate signature for authenticated requests"""
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                     signed: bool = False, retry_count: int = 3) -> Dict:
        """
        Make HTTP request to PuPrime API with retry mechanism
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Request parameters
            signed: Whether request needs signature
            retry_count: Number of retries on failure
        """
        url = f"{self.base_url}{endpoint}"
        params = params or {}

        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._generate_signature(params)

        for attempt in range(retry_count):
            try:
                if method == 'GET':
                    response = self.session.get(url, params=params)
                elif method == 'POST':
                    response = self.session.post(url, json=params)
                elif method == 'DELETE':
                    response = self.session.delete(url, params=params)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                response.raise_for_status()
                return response.json()

            except requests.exceptions.RequestException as e:
                log_error("API_REQUEST_ERROR", str(e), 
                         endpoint=endpoint, attempt=attempt+1)
                
                if attempt == retry_count - 1:
                    raise
                
                # Exponential backoff
                time.sleep(2 ** attempt)

    def get_account_info(self) -> Dict:
        """Get account information"""
        try:
            response = self._make_request('GET', '/api/v1/account', signed=True)
            logger.info("Successfully retrieved account information")
            return response
        except Exception as e:
            log_error("ACCOUNT_INFO_ERROR", str(e))
            raise

    def get_gold_price(self) -> Dict:
        """Get current GOLD (XAUUSD) price"""
        try:
            response = self._make_request('GET', '/api/v1/ticker/price', 
                                        params={'symbol': 'XAUUSD'})
            logger.info(f"Current GOLD price: {response.get('price')}")
            return response
        except Exception as e:
            log_error("PRICE_FETCH_ERROR", str(e))
            raise

    def place_order(self, order_type: str, side: str, quantity: float, 
                   price: Optional[float] = None, stop_loss: Optional[float] = None,
                   take_profit: Optional[float] = None) -> Dict:
        """
        Place a new order
        
        Args:
            order_type: Type of order (MARKET, LIMIT)
            side: Order side (BUY, SELL)
            quantity: Order quantity in lots
            price: Order price (required for LIMIT orders)
            stop_loss: Stop loss price
            take_profit: Take profit price
        """
        params = {
            'symbol': 'XAUUSD',
            'type': order_type,
            'side': side,
            'quantity': quantity
        }

        if order_type == 'LIMIT':
            if not price:
                raise ValueError("Price is required for LIMIT orders")
            params['price'] = price

        if stop_loss:
            params['stopLoss'] = stop_loss

        if take_profit:
            params['takeProfit'] = take_profit

        try:
            response = self._make_request('POST', '/api/v1/order', params=params, signed=True)
            
            log_trade(
                action=side,
                symbol='XAUUSD',
                price=price or response.get('price'),
                quantity=quantity,
                order_type=order_type,
                status='EXECUTED',
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            return response
            
        except Exception as e:
            log_error("ORDER_PLACEMENT_ERROR", str(e), order_params=params)
            raise

    def cancel_order(self, order_id: str) -> Dict:
        """Cancel an existing order"""
        try:
            response = self._make_request('DELETE', f'/api/v1/order/{order_id}', signed=True)
            logger.info(f"Successfully cancelled order {order_id}")
            return response
        except Exception as e:
            log_error("ORDER_CANCEL_ERROR", str(e), order_id=order_id)
            raise

    def get_open_positions(self) -> Dict:
        """Get all open positions"""
        try:
            response = self._make_request('GET', '/api/v1/openPositions', signed=True)
            logger.info(f"Retrieved {len(response)} open positions")
            return response
        except Exception as e:
            log_error("OPEN_POSITIONS_ERROR", str(e))
            raise

    def modify_position(self, position_id: str, stop_loss: Optional[float] = None,
                       take_profit: Optional[float] = None) -> Dict:
        """
        Modify an existing position's stop loss or take profit
        
        Args:
            position_id: ID of the position to modify
            stop_loss: New stop loss price
            take_profit: New take profit price
        """
        params = {}
        if stop_loss:
            params['stopLoss'] = stop_loss
        if take_profit:
            params['takeProfit'] = take_profit

        try:
            response = self._make_request('POST', f'/api/v1/position/{position_id}/modify',
                                        params=params, signed=True)
            logger.info(f"Successfully modified position {position_id}")
            return response
        except Exception as e:
            log_error("POSITION_MODIFY_ERROR", str(e), 
                     position_id=position_id, modifications=params)
            raise

    def get_order_history(self, start_time: Optional[int] = None,
                         end_time: Optional[int] = None) -> Dict:
        """
        Get historical orders
        
        Args:
            start_time: Start time in milliseconds
            end_time: End time in milliseconds
        """
        params = {}
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time

        try:
            response = self._make_request('GET', '/api/v1/orderHistory',
                                        params=params, signed=True)
            logger.info(f"Retrieved order history from {start_time} to {end_time}")
            return response
        except Exception as e:
            log_error("ORDER_HISTORY_ERROR", str(e), 
                     start_time=start_time, end_time=end_time)
            raise

# Example usage:
"""
api = PuPrimeAPI()

# Get account information
account_info = api.get_account_info()

# Get current GOLD price
gold_price = api.get_gold_price()

# Place a market buy order
order = api.place_order(
    order_type='MARKET',
    side='BUY',
    quantity=0.01,
    stop_loss=1900.00,
    take_profit=1950.00
)
"""
