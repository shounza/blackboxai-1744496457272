import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Server Configuration
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///gold_trader.db')
    
    # PuPrime API Configuration
    PUPRIME_API_KEY = os.getenv('PUPRIME_API_KEY')
    PUPRIME_API_SECRET = os.getenv('PUPRIME_API_SECRET')
    PUPRIME_API_URL = os.getenv('PUPRIME_API_URL', 'https://api.puprime.com')  # Replace with actual API URL
    
    # Trading Configuration
    SYMBOL = 'XAUUSD'  # Gold trading pair
    TIMEFRAME = '1h'   # Default timeframe for analysis
    
    # Risk Management
    MAX_POSITION_SIZE = float(os.getenv('MAX_POSITION_SIZE', 0.01))  # Maximum position size in lots
    STOP_LOSS_PERCENT = float(os.getenv('STOP_LOSS_PERCENT', 1.5))   # Stop loss percentage
    TAKE_PROFIT_PERCENT = float(os.getenv('TAKE_PROFIT_PERCENT', 3)) # Take profit percentage
    MAX_DAILY_LOSS = float(os.getenv('MAX_DAILY_LOSS', 5))          # Maximum daily loss percentage
    MAX_WEEKLY_LOSS = float(os.getenv('MAX_WEEKLY_LOSS', 10))       # Maximum weekly loss percentage
    
    # Technical Indicators Configuration
    FAST_EMA = int(os.getenv('FAST_EMA', 12))
    SLOW_EMA = int(os.getenv('SLOW_EMA', 26))
    RSI_PERIOD = int(os.getenv('RSI_PERIOD', 14))
    RSI_OVERBOUGHT = float(os.getenv('RSI_OVERBOUGHT', 70))
    RSI_OVERSOLD = float(os.getenv('RSI_OVERSOLD', 30))
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))  # 1 hour
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    @staticmethod
    def validate():
        """Validate required configuration variables."""
        required_vars = [
            'PUPRIME_API_KEY',
            'PUPRIME_API_SECRET',
            'JWT_SECRET_KEY'
        ]
        
        missing_vars = [var for var in required_vars if not getattr(Config, var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True

# Example .env file template
ENV_TEMPLATE = """
# Server Configuration
PORT=5000
DEBUG=True

# Database Configuration
DATABASE_URL=sqlite:///gold_trader.db

# PuPrime API Configuration
PUPRIME_API_KEY=your_api_key_here
PUPRIME_API_SECRET=your_api_secret_here
PUPRIME_API_URL=https://api.puprime.com

# Risk Management
MAX_POSITION_SIZE=0.01
STOP_LOSS_PERCENT=1.5
TAKE_PROFIT_PERCENT=3
MAX_DAILY_LOSS=5
MAX_WEEKLY_LOSS=10

# Technical Indicators
FAST_EMA=12
SLOW_EMA=26
RSI_PERIOD=14
RSI_OVERBOUGHT=70
RSI_OVERSOLD=30

# JWT Configuration
JWT_SECRET_KEY=your-secret-key
JWT_ACCESS_TOKEN_EXPIRES=3600

# Logging Configuration
LOG_LEVEL=INFO
"""
