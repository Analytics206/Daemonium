"""
Configuration management for Daemonium API
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    api_title: str = "Daemonium Philosopher Chatbot API"
    api_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    # MongoDB Settings
    mongodb_host: str = "localhost"
    mongodb_port: int = 27018
    mongodb_database: str = "daemonium"
    mongodb_username: str = "admin"
    mongodb_password: str = "ch@ng3m300"
    
    # Redis Settings
    redis_host: str = "localhost"
    redis_port: int = 6380
    redis_password: str = "ch@ng3m300"
    redis_db: int = 0
    
    # CORS Settings
    cors_origins: list = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list = ["*"]
    cors_allow_headers: list = ["*"]
    
    model_config = {"env_file": ".env"}

def load_config_from_yaml() -> Dict[str, Any]:
    """Load configuration from YAML file"""
    # Get the project root directory
    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    config_path = project_root / "config" / "default.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    
    return config

@lru_cache()
def get_settings() -> Settings:
    """Get application settings (cached)"""
    # Load YAML config
    yaml_config = load_config_from_yaml()
    
    # Create settings with YAML overrides and Docker environment variables
    settings = Settings(
        # MongoDB settings from YAML with Docker environment overrides
        mongodb_host=os.getenv('MONGODB_HOST', yaml_config.get('mongodb', {}).get('host', 'localhost')),
        mongodb_port=int(os.getenv('MONGODB_PORT', yaml_config.get('mongodb', {}).get('port', 27018))),
        mongodb_database=yaml_config.get('mongodb', {}).get('database', 'daemonium'),
        mongodb_username=yaml_config.get('mongodb', {}).get('username', 'admin'),
        mongodb_password=yaml_config.get('mongodb', {}).get('password', 'ch@ng3m300'),
        
        # Redis settings with Docker environment overrides
        redis_host=os.getenv('REDIS_HOST', yaml_config.get('redis', {}).get('host', 'localhost')),
        redis_port=int(os.getenv('REDIS_PORT', yaml_config.get('redis', {}).get('port', 6380))),
        redis_password=os.getenv('REDIS_PASSWORD', yaml_config.get('redis', {}).get('password', 'ch@ng3m300')),
        redis_db=int(os.getenv('REDIS_DB', yaml_config.get('redis', {}).get('db', 0))),

        # App settings from YAML
        debug=yaml_config.get('app', {}).get('debug', False),
        log_level=yaml_config.get('app', {}).get('log_level', 'INFO'),
    )
    
    return settings

def get_mongodb_connection_string(settings: Settings) -> str:
    """Get MongoDB connection string with URL encoding"""
    from urllib.parse import quote_plus
    
    username = quote_plus(settings.mongodb_username)
    password = quote_plus(settings.mongodb_password)
    
    return (
        f"mongodb://{username}:{password}@{settings.mongodb_host}:"
        f"{settings.mongodb_port}/{settings.mongodb_database}?authSource=admin"
    )
