import os
import tempfile

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Use a temporary database file that's guaranteed to be writable
    TEMP_DIR = tempfile.gettempdir()
    DB_PATH = os.path.join(TEMP_DIR, 'automated_blog_system.db')
    
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Add the missing USE_MOCK_DATA attribute
    USE_MOCK_DATA = True  # Set to True for development, False for production
    
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    # WordPress credentials removed in headless architecture pivot
    
    @classmethod
    def init_app(cls, app):
        print(f"Database will be created at: {cls.DB_PATH}")

