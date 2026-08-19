import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file located in backend directory
basedir = Path(__file__).resolve().parent
load_dotenv(basedir / ".env")

class Config:
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    PORT = int(os.getenv("PORT", 5000))
    DEBUG = FLASK_ENV == "development"
    
    # Mock / Agent flags
    MOCK_MODE = os.getenv("MOCK_MODE", "true").strip().lower() in ("true", "1", "yes")
    AGENT_URL = os.getenv("AGENT_URL", "http://localhost:8000").rstrip("/")
    AGENT_TIMEOUT_SECONDS = float(os.getenv("AGENT_TIMEOUT_SECONDS", "6.0"))
    
    # Database
    db_path = basedir / "urbanshield.db"
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{db_path}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API configuration
    API_VERSION = "v1"
    API_PREFIX = "/api"
