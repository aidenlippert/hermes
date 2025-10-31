"""
ASTRAEUS Python SDK - Main Client

Sprint 6: Multi-Language SDKs
"""

import requests
from typing import Optional, Dict, Any
from .resources import (
    AgentsResource,
    ContractsResource,
    PaymentsResource,
    OrchestrationResource,
    AnalyticsResource,
    SecurityResource
)
from .exceptions import AuthenticationError, APIError, RateLimitError


class AstraeusClient:
    """
    Main client for ASTRAEUS API.

    Args:
        api_key: API key for authentication
        base_url: Base URL for API (default: https://api.astraeus.ai)
        timeout: Request timeout in seconds (default: 30)

    Example:
        client = AstraeusClient(api_key="sk_...")
        agents = client.agents.list()
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.astraeus.ai",
        timeout: int = 30
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # Initialize resources
        self.agents = AgentsResource(self)
        self.contracts = ContractsResource(self)
        self.payments = PaymentsResource(self)
        self.orchestration = OrchestrationResource(self)
        self.analytics = AnalyticsResource(self)
        self.security = SecurityResource(self)

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "astraeus-python/1.0.0"
        }

    def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to ASTRAEUS API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., "/api/v1/agents")
            data: Request body data
            params: Query parameters

        Returns:
            Response data as dictionary

        Raises:
            AuthenticationError: Invalid API key
            RateLimitError: Rate limit exceeded
            APIError: Other API errors
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self._get_headers(),
                json=data,
                params=params,
                timeout=self.timeout
            )

            # Handle errors
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            elif response.status_code == 429:
                raise RateLimitError("Rate limit exceeded")
            elif response.status_code >= 400:
                error_data = response.json() if response.content else {}
                raise APIError(
                    f"API error: {response.status_code}",
                    status_code=response.status_code,
                    response=error_data
                )

            return response.json() if response.content else {}

        except requests.exceptions.Timeout:
            raise APIError("Request timeout")
        except requests.exceptions.ConnectionError:
            raise APIError("Connection error")
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request"""
        return self.request("GET", endpoint, params=params)

    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make POST request"""
        return self.request("POST", endpoint, data=data)

    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make PUT request"""
        return self.request("PUT", endpoint, data=data)

    def delete(self, endpoint: str) -> Dict[str, Any]:
        """Make DELETE request"""
        return self.request("DELETE", endpoint)
