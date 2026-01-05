"""
Secrets Commands

This module defines all secret-related CLI commands.
Secrets are encrypted key-value pairs stored in the cloud and synced to .env files.

COMMANDS:
--------
- set KEY=value...: Add/update one or more secrets (encrypts and saves)
- get <key>: Retrieve and decrypt a single secret
- list [-v]: List all secret keys (optionally show values)
- delete <key>: Remove a secret from API and .env
- pull: Download all secrets from cloud to local .env
- push: Upload local .env secrets to cloud

DATA FLOW (set command):
-----------------------
    User Input → Parse → Encrypt → API + .env
    
    "API_KEY=sk_123"
         ↓
    key="API_KEY", value="sk_123"
         ↓
    ┌─────────────────────────────────────────┐
    │ local_secrets: [{key, value}]  → .env   │  (plain text)
    │ api_secrets:   [{key, encrypted}] → API │  (encrypted)
    └─────────────────────────────────────────┘

ENCRYPTION:
----------
- Secrets are encrypted with user's master key before sending to API
- Server stores only encrypted values (zero-knowledge)
- On pull/get, secrets are decrypted locally

UTILITIES USED:
--------------
- EncryptionService: encrypt/decrypt secrets
- CredentialsManager: get master key, project ID
- EnvManager (env): read/write .env files
- api_client: communicate with API server

TO ADD A NEW SECRETS COMMAND:
----------------------------
    @secrets_app.command("command-name")
    def my_command():
        # 1. Check auth
        if not CredentialsManager.is_authenticated():
            ...
        # 2. Get credentials
        email = CredentialsManager.get_email()
        master_key = CredentialsManager.get_master_key(email)
        project_id = CredentialsManager.get_project_id()
        # 3. Call API and/or update .env
        ...
"""


import typer
import rich
from typing import List
from datetime import datetime, timezone

from ..api.client import api_client
from ..utils.credentials import CredentialsManager
from ..utils.decorators import require_auth
from ..encryption import EncryptionService
from ..utils.env_manager import env


secrets_app = typer.Typer(name="secrets", help="Manage your secrets. Run 'secretscli secrets --help' for subcommands.")


@secrets_app.command("set")
@require_auth
def set_secret(
    secrets: List[str] = typer.Argument(..., help="One or more secrets in KEY=VALUE format")
):
    """
    Add or update one or more secrets.
    
    Pass secrets as KEY=VALUE pairs. You can set multiple secrets at once.
    
    Examples:
        secretscli secrets set API_KEY=sk_live_123
        secretscli secrets set DB_URL=postgres://... REDIS_URL=redis://...
    """
    if not secrets:
        rich.print("[red]At least one secret is required.[/red]")
        raise typer.Exit(1)

    project_id = CredentialsManager.get_project_id()
    
    # Build two lists:
    # - local_secrets: plain text for .env (local development)
    # - api_secrets: encrypted for API (cloud storage)
    local_secrets = []
    api_secrets = []
    
    for secret in secrets:
        if "=" not in secret:
            rich.print(f"[red]Invalid format: '{secret}'. Use KEY=VALUE format.[/red]")
            raise typer.Exit(1)
        
        key, value = secret.split("=", 1)
        if not key:
            rich.print("[red]Invalid secret: key cannot be empty.[/red]")
            raise typer.Exit(1)

        # Plain text for .env
        local_secrets.append({"key": key, "value": value})
        
        # Encrypted for API
        encrypted_value = EncryptionService.encrypt_secret(value)
        api_secrets.append({"key": key, "value": encrypted_value})
        
        rich.print(f"[green]✅ Set {key}[/green]")
    
    # Write plain text to .env (for local development)
    env.write(local_secrets)

    data = {
        "project_id": project_id,
        "secrets": api_secrets
    }
    
    response = api_client.call(
        "secrets.create",
        "POST",
        data=data,
        authenticated=True  
    )
    
    if response.status_code != 201:
        rich.print(f"[red]Failed to set secrets: {response.text}[/red]")
        raise typer.Exit(1)

    rich.print(f"[green]Successfully set {len(secrets)} secret(s).[/green]")


@secrets_app.command("get")
@require_auth
def get_secret(
    key: str = typer.Argument(..., help="The key of the secret to retrieve")
):
    """
    Retrieve a secret value.
    
    Args:
        key: The key of the secret to retrieve
    """
    project_id = CredentialsManager.get_project_id()
    
    response = api_client.call(
        "secrets.get",
        "GET",
        project_id=project_id,
        key=key,
        authenticated=True
    )
    
    if response.status_code != 200:
        rich.print(f"[red]Failed to get secret: {response.text}[/red]")
        raise typer.Exit(1)
    
    rich.print(f"[green]Successfully retrieved {key}[/green]")
    data = response.json()["data"]

    # Auto-fetches master key
    decrypted_value = EncryptionService.decrypt_secret(data["value"])

    rich.print(f"{key}={decrypted_value}")

@secrets_app.command("list")
@require_auth
def list_secrets(
    values: bool = typer.Option(False, "--values", "-v", help="Show secret values")
):
    """
    List all secrets.
    """
    project_id = CredentialsManager.get_project_id()
    
    response = api_client.call(
        "secrets.list",
        "GET",
        project_id=project_id,
        authenticated=True
    )
    
    if response.status_code != 200:
        rich.print(f"[red]Failed to list secrets: {response.text}[/red]")
        raise typer.Exit(1)
    
    rich.print(f"[green]Successfully listed secrets[/green]")
    secrets = response.json()["data"]["secrets"]
    
    for secret in secrets:
        if values:
            decrypted_secret = EncryptionService.decrypt_secret(secret["value"])
            rich.print(f"{secret['key']}={decrypted_secret}")
        else:
            rich.print(secret["key"])

@secrets_app.command("pull")
@require_auth
def pull_secrets():
    """
    Download secrets to .env file.
    """
    project_id = CredentialsManager.get_project_id()
    
    response = api_client.call(
        "secrets.list",
        "GET",
        project_id=project_id,
        authenticated=True
    )
    
    if response.status_code != 200:
        rich.print(f"[red]Failed to pull secrets: {response.text}[/red]")
        raise typer.Exit(1)
    
    rich.print(f"[green]Successfully pulled secrets[/green]")
    secrets = response.json()["data"]["secrets"]
    secrets_dict = {}
    
    for secret in secrets:
        decrypted_secret = EncryptionService.decrypt_secret(secret["value"])
        secrets_dict[secret["key"]] = decrypted_secret
    
    env.write(secrets_dict)
    
    # Update last_pull timestamp
    CredentialsManager.update_project_config(last_pull=datetime.now(timezone.utc).isoformat())
    
    rich.print(f"[green]Successfully pulled secrets to .env file[/green]")


@secrets_app.command("push")
@require_auth
def push_secrets():
    """
    Upload secrets from .env file to API.
    """
    secrets = env.read()
    api_secrets = []

    for key, value in secrets.items():
        encrypted_secret = EncryptionService.encrypt_secret(value)
        api_secrets.append({"key": key, "value": encrypted_secret})

    project_id = CredentialsManager.get_project_id()

    data = {
        "project_id": project_id,
        "secrets": api_secrets
    }
    
    response = api_client.call(
        "secrets.create",
        "POST",
        data=data,
        authenticated=True  
    )
    
    if response.status_code != 201:
        rich.print(f"[red]Failed to push secrets: {response.text}[/red]")
        raise typer.Exit(1)
    
    # Update last_push timestamp
    CredentialsManager.update_project_config(last_push=datetime.now(timezone.utc).isoformat())

    rich.print(f"[green]Successfully pushed .env secrets[/green]")
    

@secrets_app.command("delete")
@require_auth
def delete_secret(
    key: str = typer.Argument(..., help="The key of the secret to delete")
):
    """
    Delete a secret from API and local .env file.
    """
    project_id = CredentialsManager.get_project_id()
    
    # Delete from API first
    response = api_client.call(
        "secrets.delete",
        "DELETE",
        project_id=project_id,
        key=key,
        authenticated=True
    )
    
    if response.status_code != 200:
        rich.print(f"[red]Failed to delete secret: {response.text}[/red]")
        raise typer.Exit(1)
    
    # Only delete locally if API succeeded
    env.delete(key)
    
    rich.print(f"[green]Successfully deleted {key}[/green]")
