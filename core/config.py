from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class NetworkSettings(BaseModel):
    """Network-related settings."""
    request_timeout: int = Field(default=30, description="Timeout for HTTP requests in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retries for failed requests")
    retry_delay: float = Field(default=1.0, description="Initial delay between retries in seconds")
    retry_backoff: float = Field(default=2.0, description="Multiplier for delay after each retry")
    max_concurrent_requests: int = Field(default=10, description="Maximum number of concurrent HTTP requests")
    user_agent: str = Field(
        default="UIBench/1.0",
        description="User agent string for HTTP requests"
    )

class CacheSettings(BaseModel):
    """Cache-related settings."""
    enabled: bool = Field(default=True, description="Whether caching is enabled")
    ttl: int = Field(default=3600, description="Time-to-live for cache entries in seconds")
    max_size: int = Field(default=100 * 1024 * 1024, description="Maximum cache size in bytes")
    compression: bool = Field(default=True, description="Whether to compress cached data")
    
    # Analysis cache settings
    analysis_ttl: int = Field(default=86400, description="TTL for analysis results")
    analysis_max_size: int = Field(default=500 * 1024 * 1024, description="Max size for analysis cache")

class ResourceSettings(BaseModel):
    """Resource management settings."""
    max_browsers: int = Field(default=5, description="Maximum number of concurrent browser instances")
    max_pages_per_browser: int = Field(default=5, description="Maximum pages per browser instance")
    browser_timeout: int = Field(default=30, description="Browser operation timeout in seconds")
    max_memory_mb: int = Field(default=1024, description="Maximum memory usage in MB")
    cleanup_interval: int = Field(default=300, description="Resource cleanup interval in seconds")

class PerformanceSettings(BaseModel):
    """Performance-related settings."""
    batch_size: int = Field(default=10, description="Size of batches for parallel processing")
    max_workers: int = Field(default=20, description="Maximum number of worker threads")
    max_concurrent: int = Field(default=10, description="Maximum concurrent operations")
    profiling_enabled: bool = Field(default=False, description="Whether to enable performance profiling")
    optimization_level: str = Field(
        default="balanced",
        description="Performance optimization level (minimal, balanced, aggressive)"
    )

class Settings(BaseModel):
    """Core configuration settings."""
    
    # Network settings
    network: NetworkSettings = Field(default_factory=NetworkSettings)
    
    # Cache settings
    cache: CacheSettings = Field(default_factory=CacheSettings)
    
    # Resource settings
    resources: ResourceSettings = Field(default_factory=ResourceSettings)
    
    # Performance settings
    performance: PerformanceSettings = Field(default_factory=PerformanceSettings)
    
    # Analysis settings
    nlp_model: str = Field(default="en_core_web_lg", description="NLP model to use")
    zap_scan_depth: int = Field(default=5, description="Depth for ZAP security scans")
    
    # API settings
    api_host: str = Field(default="0.0.0.0", description="API host address")
    api_port: int = Field(default=8000, description="API port number")
    api_debug: bool = Field(default=False, description="Enable API debug mode")
    
    # Security settings
    allowed_origins: list = Field(default=["*"], description="Allowed CORS origins")
    allowed_methods: list = Field(default=["*"], description="Allowed HTTP methods")
    allowed_headers: list = Field(default=["*"], description="Allowed HTTP headers")
    
    @classmethod
    def from_env(cls) -> 'Settings':
        """Create settings from environment variables."""
        
        def get_nested_env(prefix: str, defaults: Dict[str, Any]) -> Dict[str, Any]:
            """Get nested environment variables with prefix."""
            result = {}
            for key, default in defaults.items():
                env_key = f"{prefix}_{key}".upper()
                if isinstance(default, (int, float)):
                    result[key] = type(default)(os.getenv(env_key, default))
                elif isinstance(default, bool):
                    result[key] = os.getenv(env_key, str(default)).lower() == "true"
                else:
                    result[key] = os.getenv(env_key, default)
            return result
        
        # Create network settings
        network_defaults = NetworkSettings().dict()
        network_settings = NetworkSettings(**get_nested_env("NETWORK", network_defaults))
        
        # Create cache settings
        cache_defaults = CacheSettings().dict()
        cache_settings = CacheSettings(**get_nested_env("CACHE", cache_defaults))
        
        # Create resource settings
        resource_defaults = ResourceSettings().dict()
        resource_settings = ResourceSettings(**get_nested_env("RESOURCE", resource_defaults))
        
        # Create performance settings
        performance_defaults = PerformanceSettings().dict()
        performance_settings = PerformanceSettings(**get_nested_env("PERF", performance_defaults))
        
        return cls(
            network=network_settings,
            cache=cache_settings,
            resources=resource_settings,
            performance=performance_settings,
            nlp_model=os.getenv("NLP_MODEL", "en_core_web_lg"),
            zap_scan_depth=int(os.getenv("ZAP_SCAN_DEPTH", "5")),
            api_host=os.getenv("API_HOST", "0.0.0.0"),
            api_port=int(os.getenv("API_PORT", "8000")),
            api_debug=os.getenv("API_DEBUG", "false").lower() == "true",
            allowed_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
            allowed_methods=os.getenv("ALLOWED_METHODS", "*").split(","),
            allowed_headers=os.getenv("ALLOWED_HEADERS", "*").split(",")
        ) 