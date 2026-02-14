"""
Application configuration using Pydantic settings.
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 5060
    debug: bool = False
    
    # Database Configuration
    database_url: str = "postgresql+asyncpg://jeeves@localhost/jeeves"
    
    # Football Data API Configuration
    football_data_api_key: Optional[str] = None
    football_data_base_url: str = "https://api.football-data.org/v4"
    football_data_timeout: int = 30
    football_data_retry_count: int = 3
    football_data_retry_delay: float = 1.0
    
    # CORS Configuration
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:8080"
    ]
    
    # Logging
    log_level: str = "INFO"
    
    # Application Configuration
    app_name: str = "Sports Dashboard API"
    app_version: str = "0.1.0"

    # Season Configuration
    current_season: int = 2025
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()