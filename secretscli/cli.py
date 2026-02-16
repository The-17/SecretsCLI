"""
SecretsCLI - Main Entry Point

This is the main entry point for the SecretsCLI application.
It defines the Typer application and registers all commands.

STRUCTURE:
---------
- Top-level commands (init, login, guide) are defined here
- Subcommand groups (project, secrets) are imported from commands/

HOW TYPER WORKS:
---------------
Typer is a CLI framework built on Click. Commands are defined as functions
decorated with @app.command(). Subcommand groups use app.add_typer().

Example:
    @app.command()
    def my_command():
        '''This docstring appears in --help'''
        pass

TO ADD A NEW TOP-LEVEL COMMAND:
------------------------------
1. Define your function with @app.command() decorator
2. Use typer.Argument() for required positional args
3. Use typer.Option() for optional flags
4. The function docstring becomes the help text

COMMANDS DEFINED HERE:
---------------------
- init: Initialize SecretsCLI (create account or login)
- login: Login to existing account
- logout: Logout from SecretsCLI
- status
- guide: Show interactive quick-start guide
"""

from secretscli.utils.env_manager import env
import typer
import rich
import questionary
import base64

from rich.console import Console
from rich.panel import Panel

from .config import initialize_global_config, initialize_project_config
from .utils.credentials import CredentialsManager
from .prompts import Form, custom_style
from .auth import Auth, _perform_login_
from .encryption import EncryptionService
from .commands import project_app, secrets_app, workspace_app
from .utils.diff import fetch_cloud_secrets, compare_secrets



app = typer.Typer(name="SecretsCLI", help="SecretsCLI — secure secrets from any device.", add_completion=True, rich_markup_mode="rich")

# Register subcommand groups
app.add_typer(project_app, name="project")
app.add_typer(secrets_app, name="secrets")
app.add_typer(workspace_app, name="workspace")


@app.command()
def init(
    force: bool = typer.Option(False, "--force", "-f", help="Skip reinitialize confirmation")
):
    """
    Initialize SecretsCLI for your account and local environment.
    This sets up the configuration directory and prompts you to create a new account or connect an existing one.
    """
    global_created = initialize_global_config()
    project_created = initialize_project_config()

    if not global_created and not project_created:
        typer.echo("SecretsCLI is already initialized.")
        
        if force or questionary.confirm("Do you want to reinitialize?", default=False, style=custom_style).ask():
            # Reinitialize
            initialize_global_config(re_init=True)
            initialize_project_config(re_init=True)
            typer.echo("SecretsCLI reinitialized successfully!\n")
        else:
            # They said NO, just acknowledge and continue
            typer.echo("Keeping existing configuration.\n")

    typer.secho("✨ Welcome to SecretsCLI!\n", fg=typer.colors.CYAN, bold=True)
    
    choices = [
        "Create a new account",
        "Login to existing account"
    ]

    # Main choice: Login or Sign up
    action = questionary.select("What would you like to do?", choices=choices, style=custom_style).ask()

    if action is None:
        rich.print("SecretCLI initialization complete, connect account to access secrets")
        raise typer.Exit(0)
    
    if "Create" in action:
        credentials = Form.signup_form()
        if credentials is None:
            rich.print("Cancelled by user")
            raise typer.Exit(0)
        
        # Generate keypair and encrypt private key
        private_key, public_key, encrypted_private_key, salt = EncryptionService.setup_user(credentials["password"])
        
        # Prepare credentials for API
        credentials["public_key"] = base64.b64encode(public_key).decode()
        credentials["encrypted_private_key"] = encrypted_private_key  # Already base64 encoded
        credentials["key_salt"] = salt

        # Create account
        signup_result = Auth.signup(credentials)
        if signup_result is None:
            rich.print("[red]Signup failed. Please try again.[/red]")
            raise typer.Exit(1)
        
        # Auto-login after signup to get tokens
        rich.print("[green]Account created! Logging you in...[/green]")
        if not _perform_login_({"email": credentials["email"], "password": credentials["password"]}, (private_key, public_key)):
            rich.print("[red]Auto-login failed. Please run 'secretscli login' manually.[/red]")
            raise typer.Exit(1)
        
        rich.print("[green]✅ You're all set! Run 'secretscli project create <name>' to get started.[/green]")

    else:
        credentials = Form.login_form()
        if credentials is None:
            rich.print("Cancelled by user")
            raise typer.Exit(0)

        if not _perform_login_(credentials):
            raise typer.Exit(1)
        
        rich.print("[green]✅ Logged in successfully![/green]")


@app.command()
def login():
    """
    Login to your SecretsCLI account.
    Use this if you already have an account and need to authenticate on this device.
    """
    credentials = Form.login_form()
    if credentials is None:
        rich.print("Cancelled by user")
        raise typer.Exit(0)

    if not _perform_login_(credentials):
        raise typer.Exit(1)
    
    rich.print("[green]Logged in successfully![/green]")


@app.command()
def logout(
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt")
):
    """
    Logout from SecretsCLI.
    
    Clears all stored credentials:
    - Access/refresh tokens
    - Private key from keychain
    - Workspace cache
    
    Does NOT delete project.json (your project binding is preserved).
    """
    from .utils.credentials import CredentialsManager
    from .api.client import api_client
    
    # Check if logged in
    if not CredentialsManager.is_authenticated():
        rich.print("[yellow]You're not logged in.[/yellow]")
        raise typer.Exit(0)
    
    email = CredentialsManager.get_email()
    
    # Confirm unless --force
    if not force:
        confirm = questionary.confirm(
            f"Logout from {email}?",
            default=True,
            style=custom_style
        ).ask()
        if not confirm:
            rich.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit(0)
    
    # Try to invalidate token on server
    try:
        api_client.call("auth.logout", "POST")
    except Exception:
        pass  # Ignore - we'll clear local credentials anyway
    
    # Clear local session
    CredentialsManager.clear_session()
    
    rich.print(f"[green]Logged out successfully.[/green]")
    rich.print("[dim]Run 'secretscli login' to login again.[/dim]")


@app.command()
def status():
    from .utils.utils import get_relative_time
    
    email = CredentialsManager.get_email()
    workspace_data = CredentialsManager.get_selected_workspace()
    workspace_name = workspace_data.get("name")
    workspace_type = workspace_data.get("type", "team") 
    workspace_display = f"{workspace_name} ({'shared' if workspace_type == 'team' else 'personal'})"
    
    project = CredentialsManager.get_project_name()
    project_workspace = CredentialsManager.get_project_config().get("workspace_name")
    project_display = f"{project} (in {project_workspace})" if project_workspace else project
    
    # Calculate synced status
    local_secrets = env.read()
    cloud_secrets = fetch_cloud_secrets()
    diff = compare_secrets(local_secrets, cloud_secrets)
    
    # Synced = Local secrets that match cloud secrets exactly
    # (Total local) - (Local only) - (Modified values)
    total_local = len(local_secrets)
    unsynced_count = len(diff["only_local"]) + len(diff["different_values"])
    synced_count = total_local - unsynced_count
    
    raw_push = CredentialsManager.get_project_config().get("last_push")
    last_push = get_relative_time(raw_push) if raw_push else "Never"
    
    raw_pull = CredentialsManager.get_project_config().get("last_pull")
    last_pull = get_relative_time(raw_pull) if raw_pull else "Never"

    rich.print(" ")
    rich.print(f"Logged in as: [bold green]{email}[/bold green]")
    rich.print(f"Selected Workspace: [bold blue]{workspace_display}[/bold blue]")
    rich.print(f"Current Project: [bold blue]{project_display}[/bold blue]")
    
    if unsynced_count > 0:
        rich.print(f"Secrets: [green]{synced_count} synced[/green] ([yellow]{unsynced_count} unsynced[/yellow])")
    else:
        rich.print(f"Secrets: [green]{synced_count} synced[/green]")
        
    rich.print(f"Last Push: {last_push} | Last Pull: {last_pull}")
    rich.print(" ")

@app.command()
def guide():
    """
    Show a quick-start guide for SecretsCLI.
    Displays step-by-step instructions for first-time setup or returning users.
    """
    
    console = Console()
    
    # Header
    console.print()
    console.print("[bold cyan]SecretsCLI Quick Start Guide[/bold cyan]")
    console.print()
    
    # Ask what kind of user they are
    user_type = questionary.select(
        "What describes you best?",
        choices=[
            "First time setup (new account)",
            "Returning user (new machine)",
            "Show all commands"
        ],
        style=custom_style
    ).ask()
    
    if user_type is None:
        raise typer.Exit(0)
    
    if "First time" in user_type:
        first_time_guide = """
            [bold yellow]Step 1:[/bold yellow] Create your account
            [dim]$[/dim] [green]secretscli init[/green]

            [bold yellow]Step 2:[/bold yellow] Create your first project
            [dim]$[/dim] [green]secretscli project create my-app[/green]

            [bold yellow]Step 3:[/bold yellow] Add your secrets (choose one method)

            [dim]Option A - Add individually:[/dim]
            [dim]$[/dim] [green]secretscli set DATABASE_URL=postgresql://...[/green]
            [dim]$[/dim] [green]secretscli set API_KEY=sk_live_...[/green]

            [dim]Option B - Push existing .env file:[/dim]
            [dim]$[/dim] [green]secretscli push[/green]

            [bold yellow]Step 4:[/bold yellow] Pull secrets anytime
            [dim]$[/dim] [green]secretscli pull[/green]

            [bold green]✨ That's it! Your secrets are now encrypted and accessible from anywhere.[/bold green]
        """
        console.print(Panel(first_time_guide, title="[bold]🆕 First Time Setup[/bold]", border_style="cyan"))
    
    elif "Returning" in user_type:
        returning_guide = """
            [bold yellow]Step 1:[/bold yellow] Install SecretsCLI
            [dim]$[/dim] [green]pip install secretscli-py[/green]

            [bold yellow]Step 2:[/bold yellow] Login to your account
            [dim]$[/dim] [green]secretscli login[/green]

            [bold yellow]Step 3:[/bold yellow] Connect to your project
            [dim]$[/dim] [green]secretscli project use my-app[/green]

            [bold yellow]Step 4:[/bold yellow] Pull your secrets
            [dim]$[/dim] [green]secretscli pull[/green]

            [bold green]Done! Your .env file is ready.[/bold green]
        """
        console.print(Panel(returning_guide, title="[bold]Returning User Setup[/bold]", border_style="cyan"))
    
    else:
        commands_guide = """
        [bold underline]Account Commands[/bold underline]
        [green]secretscli init[/green]      Create account or login
        [green]secretscli login[/green]     Login to existing account
        [green]secretscli logout[/green]    Logout from current session
        [green]secretscli status[/green]    Show current status

        [bold underline]Project Commands[/bold underline]
        [green]secretscli project create <name>[/green]   Create a new project
        [green]secretscli project list[/green]            List all projects
        [green]secretscli project use <name>[/green]      Set active project
        [green]secretscli project delete <name>[/green]   Delete a project

        [bold underline]Secret Commands[/bold underline]
        [green]secretscli set <KEY>=<value>[/green]   Add or update a secret
        [green]secretscli get <KEY>[/green]           Get a secret value
        [green]secretscli list[/green]                List all secret keys
        [green]secretscli delete <KEY>[/green]        Delete a secret
        [green]secretscli pull[/green]                Download secrets to .env
        [green]secretscli push[/green]                Upload .env to cloud
        [green]secretscli diff[/green]                Compare local vs cloud secrets
        """
        console.print(Panel(commands_guide, title="[bold]All Commands[/bold]", border_style="cyan"))



if __name__ == "__main__":
    app()