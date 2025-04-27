from typing import Dict, Any
import logging
from datetime import datetime
import traceback

logger = logging.getLogger(__name__)

class EvaluationError(Exception):
    """Base exception for evaluation errors."""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.utcnow()
        self.traceback = traceback.format_exc()
        super().__init__(self.message)

class ValidationError(EvaluationError):
    """Exception for validation errors."""
    pass

class AnalysisError(EvaluationError):
    """Exception for analysis errors."""
    pass

class ResourceError(EvaluationError):
    """Exception for resource-related errors."""
    pass

class DatabaseError(EvaluationError):
    """Exception for database-related errors."""
    pass

class AuthenticationError(EvaluationError):
    """Exception for authentication-related errors."""
    pass

class NetworkError(EvaluationError):
    """Exception for network-related errors."""
    pass

def handle_evaluation_error(error: Exception) -> Dict[str, Any]:
    """
    Handle evaluation errors and return appropriate error response.
    
    Args:
        error: The exception that occurred
        
    Returns:
        Dict[str, Any]: Error response with message and details
    """
    error_response = {
        "message": str(error),
        "timestamp": datetime.utcnow().isoformat(),
        "type": error.__class__.__name__,
        "details": {}
    }
    
    if isinstance(error, EvaluationError):
        logger.error(f"Evaluation error: {error.message}", extra={
            "details": error.details,
            "traceback": error.traceback
        })
        error_response["details"] = error.details
        return error_response
    
    if isinstance(error, ValueError):
        logger.error(f"Validation error: {str(error)}")
        error_response["message"] = f"Invalid input: {str(error)}"
        return error_response
    
    if isinstance(error, TimeoutError):
        logger.error(f"Timeout error: {str(error)}")
        error_response["message"] = "Evaluation timed out. Please try again with a smaller scope."
        return error_response
    
    if isinstance(error, ConnectionError):
        logger.error(f"Connection error: {str(error)}")
        error_response["message"] = "Failed to connect to the target website. Please check the URL and try again."
        return error_response
    
    if isinstance(error, DatabaseError):
        logger.error(f"Database error: {str(error)}")
        error_response["message"] = "Database operation failed. Please try again later."
        return error_response
    
    if isinstance(error, AuthenticationError):
        logger.error(f"Authentication error: {str(error)}")
        error_response["message"] = "Authentication failed. Please check your credentials."
        return error_response
    
    if isinstance(error, NetworkError):
        logger.error(f"Network error: {str(error)}")
        error_response["message"] = "Network operation failed. Please check your connection."
        return error_response
    
    # Default error handling
    logger.error(f"Unexpected error: {str(error)}", exc_info=True)
    error_response["message"] = "An unexpected error occurred during evaluation. Please try again later."
    error_response["details"] = {"traceback": traceback.format_exc()}
    return error_response 