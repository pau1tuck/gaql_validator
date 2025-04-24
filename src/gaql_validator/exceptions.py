"""
Custom exception classes for GAQL validator.
"""

class GaqlError(Exception):
    """Base exception for all GAQL-related errors."""


class GaqlSyntaxError(GaqlError):
    """Exception raised for syntax errors in GAQL queries."""
    
    def __init__(self, message: str, position: int | None = None) -> None:
        self.position = position
        super().__init__(message)


class GaqlValidationError(GaqlError):
    """Exception raised for validation errors in GAQL queries."""


class GaqlResourceError(GaqlError):
    """Exception raised for errors related to GAQL resources."""


class GaqlFieldError(GaqlError):
    """Exception raised for errors related to GAQL fields."""
