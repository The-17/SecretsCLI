"""
Secrets Commands

Commands for managing secrets:
- set: Add or update one or more secrets
- get: Retrieve a secret value  
- list: List all secret keys
- delete: Remove a secret
- pull: Download secrets to .env
- push: Upload .env secrets to cloud
"""

import typer
import rich
from typing import List

from ..api.client import api_client
from ..utils.credentials import CredentialsManager
from ..encryption import EncryptionService
from ..utils.env_manager import env


secrets_app = typer.Typer(name="secrets", help="Manage your secrets. Run 'secretscli secrets --help' for subcommands.")


@secrets_app.command("set")
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

    if not CredentialsManager.is_authenticated():
        rich.print("[red]You are not logged in. Please log in first.[/red]")
        raise typer.Exit(1)

    email = CredentialsManager.get_email()
    master_key = CredentialsManager.get_master_key(email)
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
        encrypted_value = EncryptionService.encrypt_secret(value, master_key)
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
def get_secret(
    key: str = typer.Argument(..., help="The key of the secret to retrieve")
    ):
    """
    Retrieve a secret value.
    
    Args:
        key: The key of the secret to retrieve
    """
    if not CredentialsManager.is_authenticated():
        rich.print("[red]You are not logged in. Please log in first.[/red]")
        raise typer.Exit(1)

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
    data = (response.json()["data"])

    email = CredentialsManager.get_email()
    master_key = CredentialsManager.get_master_key(email)

    decrypted_value = EncryptionService.decrypt_secret(data["value"], master_key)

    rich.print(f"{key}={decrypted_value}")

@secrets_app.command("list")
def list_secrets(
    values: bool = typer.Option(False, "--values", "-v", help="Show secret values")
):
    """
    List all secrets.
    """
    if not CredentialsManager.is_authenticated():
        rich.print("[red]You are not logged in. Please log in first.[/red]")
        raise typer.Exit(1)
    
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

    email = CredentialsManager.get_email()
    master_key = CredentialsManager.get_master_key(email)

    
    for secret in secrets:
        if values:
            decrypted_secret = EncryptionService.decrypt_secret(secret["value"], master_key)
            rich.print(f"{secret['key']}={decrypted_secret}")
        else:
            rich.print(secret["key"])

@secrets_app.command("pull")
def pull_secrets():
    """
    Download secrets to .env file.
    """
    if not CredentialsManager.is_authenticated():
        rich.print("[red]You are not logged in. Please log in first.[/red]")
        raise typer.Exit(1)
    
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

    email = CredentialsManager.get_email()
    master_key = CredentialsManager.get_master_key(email)
    
    for secret in secrets:
        decrypted_secret = EncryptionService.decrypt_secret(secret["value"], master_key)
        secrets_dict[secret["key"]] = decrypted_secret
    
    env.write(secrets_dict)
    rich.print(f"[green]Successfully pulled secrets to .env file[/green]")


@secrets_app.command("push")
def push_secrets():
    """
    Upload secrets from .env file to API.
    """
    if not CredentialsManager.is_authenticated():
        rich.print("[red]You are not logged in. Please log in first.[/red]")
        raise typer.Exit(1)

    secrets = env.read()
    api_secrets = []
    
    email = CredentialsManager.get_email()
    master_key = CredentialsManager.get_master_key(email)

    for key, value in secrets.items():
        encrypted_secret = EncryptionService.encrypt_secret(value, master_key)
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

    rich.print(f"[green]Successfully pushed .env secrets[/green]")
    

# TODO: Implement commands
# @secrets_app.command("delete")
# @secrets_app.command("push")

