import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration class."""
    
    # Flask Configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key-change-in-production")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "database", "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    
    # WordPress Configuration
    WORDPRESS_API_URL = os.getenv("WORDPRESS_API_URL")
    WORDPRESS_USERNAME = os.getenv("WORDPRESS_USERNAME")
    WORDPRESS_PASSWORD = os.getenv("WORDPRESS_PASSWORD")
    
    # Affiliate Program Configuration
    AMAZON_ASSOCIATES_TAG = os.getenv("AMAZON_ASSOCIATES_TAG")
    AMAZON_ACCESS_KEY = os.getenv("AMAZON_ACCESS_KEY")
    AMAZON_SECRET_KEY = os.getenv("AMAZON_SECRET_KEY")
    
    # SEO Configuration
    GOOGLE_ADS_CUSTOMER_ID = os.getenv("GOOGLE_ADS_CUSTOMER_ID")
    GOOGLE_ADS_DEVELOPER_TOKEN = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")
    
    # System Configuration
    USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "True").lower() == "true"
    CONTENT_UPDATE_INTERVAL_HOURS = int(os.getenv("CONTENT_UPDATE_INTERVAL_HOURS", "24"))
    MAX_ARTICLES_PER_DAY = int(os.getenv("MAX_ARTICLES_PER_DAY", "5"))
    
    @classmethod
    def validate_config(cls):
        """Validate that required configuration is present."""
        required_keys = []
        
        if not cls.USE_MOCK_DATA:
            required_keys.extend([
                "OPENAI_API_KEY",
                "WORDPRESS_API_URL",
                "WORDPRESS_USERNAME",
                "WORDPRESS_PASSWORD"
            ])
        
        missing_keys = [key for key in required_keys if not getattr(cls, key)]
        
        if missing_keys:
            raise ValueError(f"Missing required configuration: {', '.join(missing_keys)}")
        
        return True

