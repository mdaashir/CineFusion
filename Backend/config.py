"""
CineFusion Configuration
Centralized configuration for production and development environments
"""

import os
import json
from pathlib import Path
from typing import List, Optional, Dict, Any


def load_config() -> Dict[str, Any]:
    """Load application configuration from JSON file"""
    # First try to load from root directory (new location)
    config_path = Path(__file__).parent.parent / "config.json"

    # Fallback to old location for compatibility
    if not config_path.exists():
        config_path = Path(__file__).parent / "data" / "config.json"

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
            # If it's the new unified config, extract backend section
            if "backend" in config_data:
                return config_data["backend"]
            else:
                # Legacy config format
                return config_data
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in configuration file: {e}")


# Load the JSON configuration
APP_CONFIG = load_config()


class Config:
    """Base configuration class"""

    # Application Info from JSON
    APP_NAME: str = APP_CONFIG.get("application", {}).get("name", "CineFusion")
    APP_VERSION: str = APP_CONFIG.get("application", {}).get("version", "1.0.0")
    APP_DESCRIPTION: str = APP_CONFIG.get("application", {}).get(
        "description", "Movie discovery platform"
    )
    APP_AUTHOR: str = APP_CONFIG.get("application", {}).get("author", "CineFusion Team")
    APP_LICENSE: str = APP_CONFIG.get("application", {}).get("license", "MIT")

    # Server Configuration
    HOST: str = os.getenv("HOST", APP_CONFIG["server"]["host"])
    PORT: int = int(os.getenv("PORT", APP_CONFIG["server"]["port"]))
    DEBUG: bool = (
        os.getenv("DEBUG", str(APP_CONFIG["server"]["debug"])).lower() == "true"
    )
    RELOAD: bool = (
        os.getenv("RELOAD", str(APP_CONFIG["server"]["reload"])).lower() == "true"
    )
    WORKER_COUNT: int = int(os.getenv("WORKER_COUNT", APP_CONFIG["server"]["workers"]))
    TIMEOUT_SECONDS: int = int(
        os.getenv("TIMEOUT_SECONDS", APP_CONFIG["server"]["timeout"])
    )

    # CORS Configuration
    CORS_ORIGINS: List[str] = APP_CONFIG["cors"]["allow_origins"]
    CORS_ALLOW_CREDENTIALS: bool = APP_CONFIG["cors"]["allow_credentials"]
    CORS_ALLOW_METHODS: List[str] = APP_CONFIG["cors"]["allow_methods"]
    CORS_ALLOW_HEADERS: List[str] = APP_CONFIG["cors"]["allow_headers"]
    CORS_MAX_AGE: int = APP_CONFIG["cors"].get("max_age", 86400)  # Default 24 hours

    # API Configuration from JSON
    API_PREFIX: str = APP_CONFIG["api"]["prefix"]
    API_VERSION: str = APP_CONFIG["api"]["version"]
    API_TITLE: str = APP_CONFIG["api"]["title"]
    OPENAPI_URL: str = APP_CONFIG["api"]["openapi_url"]
    DOCS_URL: str = APP_CONFIG["api"]["docs_url"]
    REDOC_URL: str = APP_CONFIG["api"]["redoc_url"]

    # Database Configuration
    DATA_DIR: Path = Path(__file__).parent / "data"
    MOVIE_CSV_PATH: Path = DATA_DIR / APP_CONFIG["database"]["csv_file"]
    DB_ENCODING: str = APP_CONFIG["database"]["encoding"]
    DB_CHUNK_SIZE: int = APP_CONFIG["database"]["chunk_size"]

    # Search Configuration from JSON
    MAX_SEARCH_RESULTS: int = APP_CONFIG["search"]["max_limit"]
    DEFAULT_SEARCH_LIMIT: int = APP_CONFIG["search"]["default_limit"]
    MIN_QUERY_LENGTH: int = APP_CONFIG["search"]["min_query_length"]
    MAX_QUERY_LENGTH: int = APP_CONFIG["search"].get(
        "max_query_length", 100
    )  # Default fallback
    SEARCH_TIMEOUT_MS: int = 5000  # Default fallback

    # Suggestions Configuration from JSON
    MAX_SUGGESTIONS: int = APP_CONFIG["suggestions"]["max_suggestions"]
    DEFAULT_SUGGESTIONS_LIMIT: int = APP_CONFIG["suggestions"]["max_suggestions"]
    MIN_SUGGESTIONS_QUERY_LENGTH: int = APP_CONFIG["suggestions"]["min_query_length"]
    MAX_SUGGESTIONS_QUERY_LENGTH: int = APP_CONFIG["suggestions"].get(
        "max_query_length", 50
    )  # Default fallback

    # Performance Configuration
    ENABLE_CACHING: bool = (
        os.getenv("ENABLE_CACHING", str(APP_CONFIG["cache"]["enabled"])).lower()
        == "true"
    )
    CACHE_TTL_SECONDS: int = int(
        os.getenv("CACHE_TTL_SECONDS", APP_CONFIG["cache"]["ttl"])
    )
    CACHE_MAX_SIZE: int = APP_CONFIG["cache"]["max_size"]
    CACHE_CLEANUP_INTERVAL: int = APP_CONFIG["cache"].get(
        "cleanup_interval_seconds", 3600
    )  # Default 1 hour

    # Rate Limiting from JSON
    RATE_LIMIT_REQUESTS: int = int(
        os.getenv(
            "RATE_LIMIT_REQUESTS", APP_CONFIG["rate_limiting"]["requests_per_minute"]
        )
    )
    RATE_LIMIT_WINDOW: int = int(
        os.getenv(
            "RATE_LIMIT_WINDOW", APP_CONFIG["rate_limiting"].get("block_duration", 300)
        )
    )

    # Security Configuration from JSON
    API_KEY_HEADER: str = APP_CONFIG["security"].get("api_key_header", "X-API-Key")
    TRUSTED_HOSTS: List[str] = APP_CONFIG["security"].get(
        "trusted_hosts", ["localhost", "127.0.0.1"]
    )

    # Monitoring Configuration from JSON
    HEALTH_CHECK_INTERVAL: int = APP_CONFIG["monitoring"]["health_check_interval"]
    METRICS_RETENTION_HOURS: int = APP_CONFIG["monitoring"]["metrics_retention_hours"]
    ALERT_THRESHOLDS: Dict[str, float] = APP_CONFIG["monitoring"]["alert_thresholds"]

    # Fallback Data from JSON
    FALLBACK_MOVIES: List[Dict[str, Any]] = APP_CONFIG["fallback_data"]["movies"]

    # Error Messages from JSON
    ERROR_MESSAGES: Dict[str, str] = APP_CONFIG["error_messages"]

    # Response Headers from JSON
    RESPONSE_HEADERS: Dict[str, str] = APP_CONFIG["response_headers"]

    # Direct access to raw configuration data for flexible usage
    @property
    def data(self) -> Dict[str, Any]:
        """Access to raw configuration data for flexible usage"""
        return APP_CONFIG


class DevelopmentConfig(Config):
    """Development configuration"""

    DEBUG: bool = True
    RELOAD: bool = True
    CORS_ORIGINS: List[str] = ["http://localhost:8000", "http://127.0.0.1:8000", "*"]


class ProductionConfig(Config):
    """Production configuration"""

    DEBUG: bool = False
    RELOAD: bool = False
    CORS_ORIGINS: List[str] = (
        os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else []
    )

    # Enhanced security for production from JSON
    RATE_LIMIT_REQUESTS: int = APP_CONFIG["rate_limiting"].get(
        "requests_per_minute", 60
    )
    RATE_LIMIT_WINDOW: int = APP_CONFIG["rate_limiting"].get("block_duration", 300)


class TestConfig(Config):
    """Test configuration"""

    DEBUG: bool = True
    # Use in-memory fallback data for testing
    USE_FALLBACK_DATA: bool = True


def get_config() -> Config:
    """Get configuration based on environment"""
    env = os.getenv("ENVIRONMENT", "development").lower()

    if env == "production":
        return ProductionConfig()
    elif env == "test":
        return TestConfig()
    else:
        return DevelopmentConfig()


# Global config instance
config = get_config()
