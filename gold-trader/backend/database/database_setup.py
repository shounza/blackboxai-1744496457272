from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
from database.models import Base
from config import Config
from logger import logger

class Database:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self._setup_database()

    def _setup_database(self):
        """Initialize database connection and create tables."""
        try:
            # Create database engine
            self.engine = create_engine(
                Config.DATABASE_URL,
                echo=Config.DEBUG,
                pool_pre_ping=True,
                pool_recycle=3600
            )

            # Create session factory
            session_factory = sessionmaker(bind=self.engine)
            self.Session = scoped_session(session_factory)

            # Create all tables
            Base.metadata.create_all(self.engine)
            
            logger.info("Database setup completed successfully")
            
        except SQLAlchemyError as e:
            logger.error(f"Database setup failed: {str(e)}")
            raise

    def get_session(self):
        """Get a new database session."""
        return self.Session()

    def close_session(self, session):
        """Safely close a database session."""
        try:
            session.close()
        except Exception as e:
            logger.error(f"Error closing database session: {str(e)}")

    def cleanup(self):
        """Cleanup database connections."""
        try:
            self.Session.remove()
            self.engine.dispose()
            logger.info("Database connections cleaned up")
        except Exception as e:
            logger.error(f"Error during database cleanup: {str(e)}")

class DatabaseManager:
    """Context manager for database sessions."""
    
    def __init__(self):
        self.db = Database()
        self.session = None

    def __enter__(self):
        self.session = self.db.get_session()
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # An error occurred, rollback the transaction
            try:
                self.session.rollback()
                logger.warning(f"Transaction rolled back due to: {exc_type.__name__}: {str(exc_val)}")
            except Exception as e:
                logger.error(f"Error rolling back transaction: {str(e)}")
        
        self.db.close_session(self.session)

def setup_database():
    """Initialize the database."""
    try:
        Database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

def get_db_session():
    """Get a database session using the context manager."""
    return DatabaseManager()

# Example usage:
"""
# Using the context manager
with get_db_session() as session:
    try:
        # Perform database operations
        new_user = User(username='test', email='test@example.com')
        session.add(new_user)
        session.commit()
    except SQLAlchemyError as e:
        # Error handling is automatic through the context manager
        logger.error(f"Database operation failed: {str(e)}")
"""
