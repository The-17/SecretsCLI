"""
API Client

This module handles all HTTP communication with the SecretsCLI API server.

ARCHITECTURE:
------------
- ENDPOINT_MAP: Defines all API endpoints in a structured format
- PUBLIC_ENDPOINTS: Endpoints that don't require authentication tokens
- APIClient: Main class for making HTTP requests

ENDPOINT FORMAT:
---------------
Endpoints are referenced as "category.action", e.g.:
- "auth.login" → POST /api/auth/login/
- "secrets.get" → GET /api/secrets/{project_id}/{key}/
- "projects.create" → POST /api/projects/

URL PARAMETERS:
--------------
Endpoints with {placeholders} need URL parameters. Pass them as kwargs:
    api_client.call("secrets.get", "GET", project_id="uuid", key="API_KEY")
    # Results in: GET /api/secrets/uuid/API_KEY/

AUTHENTICATION:
--------------
- Most endpoints auto-include the Authorization header with JWT token
- PUBLIC_ENDPOINTS (signup, login, refresh) skip authentication
- Override with authenticated=False if needed

USAGE:
-----
    from secretscli.api.client import api_client
    
    # POST with data
    response = api_client.call("auth.login", "POST", data={"email": "...", "password": "..."})
    
    # GET with URL params
    response = api_client.call("secrets.get", "GET", project_id="uuid", key="API_KEY")
    
    # Check response
    if response.status_code == 200:
        data = response.json()
"""

from typing import Optional, Dict, Any
import requests
from ..utils.credentials import CredentialsManager


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
        "get": "projects/{workspace_id}/{project_name}/",
        "update": "projects/{workspace_id}/{project_name}/",
        "delete": "projects/{workspace_id}/{project_name}/",
        "invite": "projects/{workspace_id}/{project_name}/invite/",
    },
    "workspaces": {
        "list": "workspaces/",
        "create": "workspaces/",
        "get": "workspaces/{workspace_id}/",
        "update": "workspaces/{workspace_id}/",
        "delete": "workspaces/{workspace_id}/",
        "members": "workspaces/{workspace_id}/members/",
        "invite": "workspaces/{workspace_id}/members/",
        "remove_member": "workspaces/{workspace_id}/members/{email}/",
    },
    "users": {
        "public_key": "users/{email}/public-key/",
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