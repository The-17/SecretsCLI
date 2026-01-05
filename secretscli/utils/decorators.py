"""
Authentication Decorators

Decorators for CLI commands that require authentication.

USAGE:
-----
    from ..utils.decorators import require_auth
    
    @app.command()
    @require_auth
    def my_command():
        # User is guaranteed to be authenticated here
        # Token has been refreshed if it was expired
        pass

HOW IT WORKS:
------------
1. Checks if access token exists
2. Checks if token is expired (using expires_at)
3. If expired, attempts to refresh using refresh token
4. If refresh fails, prompts user to login again
5. Only then runs the actual command
"""

from functools import wraps
from datetime import datetime, timezone

import typer
import rich

from .credentials import CredentialsManager
from ..api.client import api_client


def require_auth(func):
    """
    Decorator that ensures user is authenticated before running command.
    
    - Checks for valid tokens
    - Auto-refreshes expired access tokens using refresh token
    - Exits with error if not authenticated
    
    Example:
        @app.command()
        @require_auth
        def my_command():
            # Auth is guaranteed here
            pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Check if we have an access token at all
        if not CredentialsManager.get_access_token():
            rich.print("[red]You are not logged in. Run 'secretscli login' first.[/red]")
            raise typer.Exit(1)
        
        # Check token expiry and refresh if needed
        tokens = CredentialsManager.get_tokens()
        if tokens and tokens.get("expires_at"):
            try:
                # Parse ISO format datetime
                expires_at_str = tokens["expires_at"]
                # Handle both "Z" suffix and "+00:00" formats
                if expires_at_str.endswith("Z"):
                    expires_at_str = expires_at_str[:-1] + "+00:00"
                expires_at = datetime.fromisoformat(expires_at_str)
                
                # Check if token is expired
                if datetime.now(timezone.utc) >= expires_at:
                    rich.print("[yellow]Session expired, refreshing...[/yellow]")
                    if not _refresh_token():
                        rich.print("[red]Session expired. Run 'secretscli login' to continue.[/red]")
                        raise typer.Exit(1)
                    rich.print("[green]Session refreshed![/green]")
            except (ValueError, KeyError):
                # If we can't parse expiry, proceed anyway (token might still be valid)
                pass
        
        # Check private key exists
        email = CredentialsManager.get_email()
        if not CredentialsManager.get_private_key(email):
            rich.print("[red]Private key not found. Run 'secretscli login' to restore your session.[/red]")
            raise typer.Exit(1)
        
        return func(*args, **kwargs)
    return wrapper


def _refresh_token() -> bool:
    """
    Attempt to refresh the access token using refresh token.
    
    Returns:
        True if refresh successful, False otherwise
    """
    tokens = CredentialsManager.get_tokens()
    if not tokens or not tokens.get("refresh_token"):
        return False
    
    try:
        response = api_client.call(
            "auth.refresh",
            "POST",
            data={"refresh": tokens["refresh_token"]},
            authenticated=False
        )

        print(response.text)

        if response.status_code == 200:
            data = response.json()["data"]
            CredentialsManager.store_tokens(
                data["access"],
                data.get("refresh", tokens["refresh_token"]),  # Fallback to existing
                data["expires_at"]
            )
            return True
    except Exception:
        pass
    
    return False
