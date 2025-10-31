"""
ASTRAEUS SDK Exceptions

Sprint 6: Multi-Language SDKs
"""

from typing import Optional, Dict, Any


class AstraeusError(Exception):
    """Base exception for ASTRAEUS SDK"""
    pass


class AuthenticationError(AstraeusError):
    """Authentication failed - invalid API key"""
    pass


class APIError(AstraeusError):
    """API request failed"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class RateLimitError(AstraeusError):
    """Rate limit exceeded"""
    pass


class ValidationError(AstraeusError):
    """Invalid request data"""
    pass
