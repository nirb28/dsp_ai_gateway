import os
import logging
from typing import Literal
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings."""
    
    # API keys for different providers
    OPENAI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    
    # Default provider and model
    DEFAULT_PROVIDER: Literal["openai", "groq"] = "groq"
    DEFAULT_MODEL: str = "mixtral-8x7b-32768"
    
    # Client configuration directory
    CLIENT_CONFIG_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "app", "clients", "configs")
    
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "DSP AI Gateway"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def __init__(self, **data):
        super().__init__(**data)
        
        # Validate provider
        if self.DEFAULT_PROVIDER not in ["openai", "groq"]:
            raise ValueError(f"Invalid provider: {self.DEFAULT_PROVIDER}. Must be one of: openai, groq")
        
        # Log settings
        logger.info(f"Loaded settings with provider: {self.DEFAULT_PROVIDER}")
        logger.info(f"OpenAI API key present: {bool(self.OPENAI_API_KEY)}")
        logger.info(f"Groq API key present: {bool(self.GROQ_API_KEY)}")
        logger.info(f"Default model: {self.DEFAULT_MODEL}")
        logger.info(f"Client config directory: {self.CLIENT_CONFIG_DIR}")

# Create global settings object
settings = Settings()
