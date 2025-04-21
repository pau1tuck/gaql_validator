"""
Custom exception classes for GAQL validator.
"""

class GaqlError(Exception):
    """Base exception for all GAQL-related errors."""
    pass


class GaqlSyntaxError(GaqlError):
    """Exception raised for syntax errors in GAQL queries."""
    
    def __init__(self, message: str, position: int = None) -> None:
        self.position = position
        super().__init__(message)


class GaqlValidationError(GaqlError):
    """Exception raised for validation errors in GAQL queries."""
    pass


class GaqlResourceError(GaqlError):
    """Exception raised for errors related to GAQL resources."""
    pass


class GaqlFieldError(GaqlError):
    """Exception raised for errors related to GAQL fields."""
    pass
