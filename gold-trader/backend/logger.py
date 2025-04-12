import logging
import sys
from logging.handlers import RotatingFileHandler
import os
from config import Config

class Logger:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self._setup_logger()

    def _setup_logger(self):
        """Set up the logger with both file and console handlers."""
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')

        # Create main logger
        self.logger = logging.getLogger('GoldTrader')
        self.logger.setLevel(getattr(logging, Config.LOG_LEVEL))

        # Prevent adding handlers multiple times
        if not self.logger.handlers:
            # Create formatters
            formatter = logging.Formatter(Config.LOG_FORMAT)

            # File Handler (Trading Log)
            trading_handler = RotatingFileHandler(
                'logs/trading.log',
                maxBytes=10000000,  # 10MB
                backupCount=5
            )
            trading_handler.setFormatter(formatter)
            trading_handler.setLevel(logging.INFO)

            # File Handler (Error Log)
            error_handler = RotatingFileHandler(
                'logs/error.log',
                maxBytes=10000000,  # 10MB
                backupCount=5
            )
            error_handler.setFormatter(formatter)
            error_handler.setLevel(logging.ERROR)

            # Console Handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.INFO)

            # Add handlers to logger
            self.logger.addHandler(trading_handler)
            self.logger.addHandler(error_handler)
            self.logger.addHandler(console_handler)

    def get_logger(self):
        """Return the configured logger instance."""
        return self.logger

# Create logger instance
logger = Logger().get_logger()

def log_trade(action, symbol, price, quantity, order_type, status, **kwargs):
    """
    Log trading activity with standardized format.
    
    Args:
        action (str): 'BUY' or 'SELL'
        symbol (str): Trading symbol (e.g., 'XAUUSD')
        price (float): Entry/Exit price
        quantity (float): Trade quantity
        order_type (str): Type of order (e.g., 'MARKET', 'LIMIT')
        status (str): Order status
        **kwargs: Additional parameters to log
    """
    trade_info = {
        'action': action,
        'symbol': symbol,
        'price': price,
        'quantity': quantity,
        'order_type': order_type,
        'status': status,
        **kwargs
    }
    logger.info(f"TRADE: {trade_info}")

def log_strategy(strategy_name, signal_type, indicators, **kwargs):
    """
    Log strategy signals and indicator values.
    
    Args:
        strategy_name (str): Name of the trading strategy
        signal_type (str): Type of signal generated
        indicators (dict): Dictionary of indicator values
        **kwargs: Additional parameters to log
    """
    strategy_info = {
        'strategy': strategy_name,
        'signal': signal_type,
        'indicators': indicators,
        **kwargs
    }
    logger.info(f"STRATEGY: {strategy_info}")

def log_error(error_type, message, **kwargs):
    """
    Log error messages with additional context.
    
    Args:
        error_type (str): Type of error
        message (str): Error message
        **kwargs: Additional context parameters
    """
    error_info = {
        'type': error_type,
        'message': message,
        **kwargs
    }
    logger.error(f"ERROR: {error_info}")

def log_performance(metrics):
    """
    Log trading performance metrics.
    
    Args:
        metrics (dict): Dictionary containing performance metrics
    """
    logger.info(f"PERFORMANCE: {metrics}")
