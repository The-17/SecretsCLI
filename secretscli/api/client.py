import requests
from typing import Optional, Dict, Any


# ============================================================
# API Endpoint Configuration
# ============================================================
ENDPOINT_MAP = {
    "auth": {
        "signup": "auth/register/",
        "login": "auth/login/",
        "logout": "auth/logout/",
        "refresh": "auth/refresh/",
    },
    "secrets": {
        "list": "secrets/",
        "create": "secrets/",
        "get": "secrets/{secret_id}/",
        "update": "secrets/{secret_id}/",
        "delete": "secrets/{secret_id}/",
    },
    "projects": {
        "list": "projects/",
        "create": "projects/",
        "get": "projects/{project_id}/",
    }
}

class APIClient:
    def __init__(self):
        self.api_url = "https://secrets-api-orpin.vercel.app/api"

    def _get_endpoint_(self, endpoint_key, *params):
        """
        Get the full endpoint URL from a key like 'auth.login'.
        
        Args:
            endpoint_key: Dot-separated key like 'auth.login' or 'secrets.get'
            **params: URL parameters like secret_id=123 for parameterized endpoints
        
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

            category, action =parts
            endpoint_path = ENDPOINT_MAP[category][action]
            
            # Replace any parameters in the path (e.g., {secret_id})
            if params:
                endpoint_path = endpoint_path.format(**params)

            return endpoint_path

        except KeyError:
            raise ValueError(f"Unknown endpoint: {endpoint_key}. Check ENDPOINT_MAP.")

    def call(self, endpoint_key: str, method: str, data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None, **url_params: dict):
        endpoint_path = self._get_endpoint_(endpoint_key, **url_params)
        url = f"{self.api_url}/{endpoint_path}"

        response = requests.request(
            method=method.upper(),
            url=url,
            json=data,
            params=params
        )

        return response

api_client = APIClient()

    