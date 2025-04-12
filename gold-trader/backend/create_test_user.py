from database.database_setup import get_db_session
from database.models import User
from werkzeug.security import generate_password_hash
from datetime import datetime

def create_test_user():
    with get_db_session() as session:
        # Check if test user already exists
        existing_user = session.query(User).filter_by(username='test').first()
        if existing_user:
            print("Test user already exists")
            return

        # Create test user
        test_user = User(
            username='test',
            email='test@example.com',
            password_hash=generate_password_hash('test123'),
            api_key='test_api_key',
            api_secret='test_api_secret',
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        session.add(test_user)
        session.commit()
        print("Test user created successfully")

if __name__ == '__main__':
    create_test_user()
