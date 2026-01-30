"""
Secrets Diff Utilities

Helper functions for comparing local .env secrets with cloud secrets.
Used by the diff command and the push command to show differences.
"""

from typing import Dict
import rich

from ..api.client import api_client
from ..encryption import EncryptionService
from .credentials import CredentialsManager


def fetch_cloud_secrets() -> Dict[str, str]:
    """
    Fetch and decrypt all secrets from the cloud.
    
    Returns:
        Dictionary of {KEY: decrypted_value} pairs
    """
    project_id = CredentialsManager.get_project_id()
    
    response = api_client.call(
        "secrets.list",
        "GET",
        project_id=project_id,
        authenticated=True
    )
    
    if response.status_code != 200:
        return {}
    
    secrets = response.json()["data"]["secrets"]
    result = {}
    
    for secret in secrets:
        decrypted_value = EncryptionService.decrypt_secret(secret["value"])
        result[secret["key"]] = decrypted_value
    
    return result


def compare_secrets(local: Dict[str, str], cloud: Dict[str, str]) -> dict:
    """
    Compare local and cloud secrets.
    
    Args:
        local: Dictionary of local secrets {KEY: VALUE}
        cloud: Dictionary of cloud secrets {KEY: VALUE}
    
    Returns:
        Dictionary with:
        - only_local: Keys only in local (will be added on push)
        - only_cloud: Keys only in cloud (missing locally)
        - different_values: Keys with different values
        - has_changes: True if any differences exist
    """
    local_keys = set(local.keys())
    cloud_keys = set(cloud.keys())
    
    different = {
        key for key in local_keys & cloud_keys
        if local[key] != cloud[key]
    }
    
    return {
        "only_local": local_keys - cloud_keys,
        "only_cloud": cloud_keys - local_keys,
        "different_values": different,
        "has_changes": bool(
            (local_keys - cloud_keys) or 
            (cloud_keys - local_keys) or 
            different
        )
    }


def show_diff(diff_result: dict) -> None:
    """
    Display diff results to user.
    
    Args:
        diff_result: Result from compare_secrets()
    """
    if not diff_result["has_changes"]:
        rich.print("[green]Local and cloud secrets are in sync.[/green]")
        return
    
    rich.print() 
    
    if diff_result["only_local"]:
        rich.print("[cyan]➕ New (local only - will be added to cloud):[/cyan]")
        for key in sorted(diff_result["only_local"]):
            rich.print(f"   {key}")
    
    if diff_result["only_cloud"]:
        rich.print("[yellow]⚠️  Missing locally (only in cloud):[/yellow]")
        for key in sorted(diff_result["only_cloud"]):
            rich.print(f"   {key}")
    
    if diff_result["different_values"]:
        rich.print("[magenta]Modified (different values):[/magenta]")
        for key in sorted(diff_result["different_values"]):
            rich.print(f"   {key}")
    
    rich.print()
