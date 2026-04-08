"""Exceptions for Cerebrum SDK."""


class CerebrumError(Exception):
    """Base exception for Cerebrum SDK errors."""
    
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AuthenticationError(CerebrumError):
    """Raised when API key is invalid or missing."""
    
    def __init__(self, message: str = "Invalid or missing API key"):
        super().__init__(message, status_code=401)


class RateLimitError(CerebrumError):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)


class BlockNotFoundError(CerebrumError):
    """Raised when requested block is not found."""
    
    def __init__(self, message: str = "Block not found"):
        super().__init__(message, status_code=404)


class ExecutionError(CerebrumError):
    """Raised when block execution fails."""
    
    def __init__(self, message: str = "Execution failed"):
        super().__init__(message, status_code=500)


class ValidationError(CerebrumError):
    """Raised when request validation fails."""
    
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, status_code=400)
