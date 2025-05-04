class AnalysisError(Exception):
    """Base class for analysis-related exceptions."""
    pass

class ValidationError(AnalysisError):
    """Raised when input validation fails."""
    pass

class ProcessingError(AnalysisError):
    """Raised when there's an error during analysis processing."""
    pass

class CacheError(AnalysisError):
    """Raised when there's an error with the analysis cache."""
    pass

class NetworkError(AnalysisError):
    """Raised when there's a network-related error during analysis."""
    pass

class ConfigurationError(AnalysisError):
    """Raised when there's an error with analyzer configuration."""
    pass 