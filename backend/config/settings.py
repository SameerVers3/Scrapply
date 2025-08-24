import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application Configuration
    APP_NAME: str = "Nexus Platform"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    
    # Database Configuration
    DATABASE_URL: str = None
    DATABASE_URL_SYNC: Optional[str] = None
    DATABASE_ECHO: bool = False
    
    # AI Configuration
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_BASE_URL: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # Security Configuration
    SANDBOX_TIMEOUT: int = 30
    SANDBOX_MEMORY_LIMIT: int = 512
    MAX_CONCURRENT_JOBS: int = 5
    
    # Web Scraping Configuration
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    REQUEST_TIMEOUT: int = 10
    MAX_PAGE_SIZE: int = 2000000  # 2MB max page size
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()
