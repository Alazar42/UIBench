from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseModel):
    """Core configuration settings."""
    
    # Evaluation settings
    evaluation_timeout: int = 60
    max_concurrent: int = 10
    max_workers: int = 20
    
    # Analysis settings
    nlp_model: str = "en_core_web_lg"
    zap_scan_depth: int = 5
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = False
    
    # Cache settings
    cache_ttl: int = 3600
    cache_max_size: int = 100
    
    # Security settings
    allowed_origins: list = ["*"]
    allowed_methods: list = ["*"]
    allowed_headers: list = ["*"]
    
    @classmethod
    def from_env(cls):
        """Create settings from environment variables."""
        return cls(
            evaluation_timeout=int(os.getenv("EVALUATION_TIMEOUT", "60")),
            max_concurrent=int(os.getenv("MAX_CONCURRENT", "10")),
            max_workers=int(os.getenv("MAX_WORKERS", "20")),
            nlp_model=os.getenv("NLP_MODEL", "en_core_web_lg"),
            zap_scan_depth=int(os.getenv("ZAP_SCAN_DEPTH", "5")),
            api_host=os.getenv("API_HOST", "0.0.0.0"),
            api_port=int(os.getenv("API_PORT", "8000")),
            api_debug=os.getenv("API_DEBUG", "false").lower() == "true",
            cache_ttl=int(os.getenv("CACHE_TTL", "3600")),
            cache_max_size=int(os.getenv("CACHE_MAX_SIZE", "100")),
            allowed_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
            allowed_methods=os.getenv("ALLOWED_METHODS", "*").split(","),
            allowed_headers=os.getenv("ALLOWED_HEADERS", "*").split(",")
        ) 