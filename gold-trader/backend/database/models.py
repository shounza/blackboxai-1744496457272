from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

Base = declarative_base()

class OrderType(enum.Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    TAKE_PROFIT = "TAKE_PROFIT"

class OrderStatus(enum.Enum):
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    api_key = Column(String(100))
    api_secret = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    # Relationships
    trades = relationship("Trade", back_populates="user")
    strategies = relationship("Strategy", back_populates="user")

class Trade(Base):
    __tablename__ = 'trades'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    symbol = Column(String(20), nullable=False)  # e.g., 'XAUUSD'
    order_type = Column(Enum(OrderType), nullable=False)
    status = Column(Enum(OrderStatus), nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float)
    quantity = Column(Float, nullable=False)
    take_profit = Column(Float)
    stop_loss = Column(Float)
    profit_loss = Column(Float)
    commission = Column(Float, default=0.0)
    entry_time = Column(DateTime, default=datetime.utcnow)
    exit_time = Column(DateTime)
    strategy_id = Column(Integer, ForeignKey('strategies.id'))
    notes = Column(String(500))

    # Relationships
    user = relationship("User", back_populates="trades")
    strategy = relationship("Strategy", back_populates="trades")

class Strategy(Base):
    __tablename__ = 'strategies'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    symbol = Column(String(20), nullable=False)  # e.g., 'XAUUSD'
    timeframe = Column(String(10), nullable=False)  # e.g., '1h', '4h', '1d'
    is_active = Column(Boolean, default=True)
    
    # Risk Parameters
    position_size = Column(Float, nullable=False)  # in lots
    stop_loss_percent = Column(Float, nullable=False)
    take_profit_percent = Column(Float, nullable=False)
    max_daily_loss = Column(Float, nullable=False)
    
    # Technical Indicators
    fast_ema = Column(Integer)
    slow_ema = Column(Integer)
    rsi_period = Column(Integer)
    rsi_overbought = Column(Float)
    rsi_oversold = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="strategies")
    trades = relationship("Trade", back_populates="strategy")

class PerformanceMetrics(Base):
    __tablename__ = 'performance_metrics'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    strategy_id = Column(Integer, ForeignKey('strategies.id'))
    date = Column(DateTime, nullable=False)
    
    # Trading Metrics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    
    # Financial Metrics
    total_profit_loss = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    profit_factor = Column(Float, default=0.0)
    average_win = Column(Float, default=0.0)
    average_loss = Column(Float, default=0.0)
    risk_reward_ratio = Column(Float, default=0.0)
    
    # Risk Metrics
    sharpe_ratio = Column(Float, default=0.0)
    sortino_ratio = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
