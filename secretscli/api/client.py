import requests
from typing import Optional, Dict, Any


# API Endpoint Configuration
ENDPOINT_MAP = {
    "auth": {
        "signup": "auth/register/",
        "login": "auth/login/",
        "logout": "auth/logout/",
        "refresh": "auth/refresh/",
    },
    "secrets": {
        "list": "secrets/{project_id}/",
        "create": "secrets/",
        "get": "secrets/{project_id}/{key}/",
        "update": "secrets/{project_id}/{key}/",
        "delete": "secrets/{project_id}/{key}/",
    },
    "projects": {
        "list": "projects/",
        "create": "projects/",
        "get": "projects/{project_name}/",
        "update": "projects/{project_name}/",
        "delete": "projects/{project_name}/",
    }
}

# Endpoints that don't require authentication
PUBLIC_ENDPOINTS = {"auth.signup", "auth.login", "auth.refresh"}


class APIClient:
    def __init__(self):
        self.api_url = "https://secrets-api-orpin.vercel.app/api"

    def _get_endpoint_(self, endpoint_key, **url_params):
        """
        Get the full endpoint URL from a key like 'auth.login'.
        
        Args:
            endpoint_key: Dot-separated key like 'auth.login' or 'secrets.get'
            **url_params: URL parameters like secret_id=123 for parameterized endpoints
        
        Returns:
            Full endpoint path
            
        Example:
            _get_endpoint_('auth.login') -> 'auth/login/'
            _get_endpoint_('secrets.get', secret_id=123) -> 'secrets/123/'
        """
        try:
            parts = endpoint_key.split(".")
            if len(parts) != 2:
                raise ValueError(f"Endpoint key must be in format 'category.action', got: {endpoint_key}")

            category, action = parts
            endpoint_path = ENDPOINT_MAP[category][action]
            
            # Replace any parameters in the path (e.g., {secret_id})
            if url_params:
                endpoint_path = endpoint_path.format(**url_params)

            return endpoint_path

        except KeyError:
            raise ValueError(f"Unknown endpoint: {endpoint_key}. Check ENDPOINT_MAP.")

    def _get_auth_header_(self) -> dict:
        """Get authorization header with access token from stored credentials."""
        from ..utils.credentials import CredentialsManager
        
        access_token = CredentialsManager.get_access_token()
        if access_token:
            return {"Authorization": f"Bearer {access_token}"}
        return {}

    def call(self, endpoint_key: str, method: str, data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None, authenticated: Optional[bool] = None, **url_params):
        """
        Make an API call.
        
        Args:
            endpoint_key: Dot-separated key like 'auth.login' or 'projects.create'
            method: HTTP method (GET, POST, PUT, DELETE)
            data: Request body data (JSON)
            params: Query parameters
            authenticated: Whether to include auth header. 
                           Defaults to True for non-public endpoints.
            **url_params: URL path parameters like secret_id=123
        
        Returns:
            requests.Response object
        """
        endpoint_path = self._get_endpoint_(endpoint_key, **url_params)
        url = f"{self.api_url}/{endpoint_path}"
        
        # Build headers
        headers = {"Content-Type": "application/json"}
        
        # Auto-detect if authentication is needed
        if authenticated is None:
            authenticated = endpoint_key not in PUBLIC_ENDPOINTS
        
        if authenticated:
            headers.update(self._get_auth_header_())

        response = requests.request(
            method=method.upper(),
            url=url,
            json=data,
            params=params,
            headers=headers
        )

        return response


api_client = APIClient()