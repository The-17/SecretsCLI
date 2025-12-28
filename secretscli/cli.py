import typer
import rich
import questionary
from rich.console import Console
from rich.panel import Panel

from .config import initialize_global_config, initialize_project_config
from .prompts import Form, custom_style
from .auth import Auth, _perform_login_
from .encryption import EncryptionService


app = typer.Typer(name="SecretsCLI", help="SecretsCLI — secure secrets from any device.", add_completion=True, rich_markup_mode="rich")


@app.command()
def init():
    """
    Initialize SecretsCLI for your account and local environment.
    This sets up the configuration directory and prompts you to create a new account or connect an existing one.
    """
    global_created = initialize_global_config()
    project_created = initialize_project_config()

    if not global_created and not project_created:
        typer.echo("SecretsCLI is already initialized.")
        
        if questionary.confirm("Do you want to reinitialize?", default=False, style=custom_style).ask():
            # Only reinitialize if they said YES
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
            
        master_key, encrypted_master_key, salt = EncryptionService.setup_user(credentials["password"])
        credentials["encrypted_master_key"] = encrypted_master_key
        credentials["key_salt"] = salt

        # Create account
        signup_result = Auth.signup(credentials)
        if signup_result is None:
            rich.print("[red]Signup failed. Please try again.[/red]")
            raise typer.Exit(1)
        
        # Auto-login after signup to get tokens
        rich.print("[green]Account created! Logging you in...[/green]")
        if not _perform_login_({"email": credentials["email"], "password": credentials["password"]}, master_key):
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
    
    rich.print("[green]✅ Logged in successfully![/green]")


@app.command()
def guide():
    """
    Show a quick-start guide for SecretsCLI.
    Displays step-by-step instructions for first-time setup or returning users.
    """
    
    console = Console()
    
    # Header
    console.print()
    console.print("[bold cyan]📚 SecretsCLI Quick Start Guide[/bold cyan]")
    console.print()
    
    # Ask what kind of user they are
    user_type = questionary.select(
        "What describes you best?",
        choices=[
            "🆕 First time setup (new account)",
            "🔄 Returning user (new machine)",
            "📋 Show all commands"
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
  [dim]$[/dim] [green]pip install secretscli[/green]

[bold yellow]Step 2:[/bold yellow] Login to your account
  [dim]$[/dim] [green]secretscli login[/green]

[bold yellow]Step 3:[/bold yellow] Connect to your project
  [dim]$[/dim] [green]secretscli project use my-app[/green]

[bold yellow]Step 4:[/bold yellow] Pull your secrets
  [dim]$[/dim] [green]secretscli pull[/green]

[bold green]✨ Done! Your .env file is ready.[/bold green]
"""
        console.print(Panel(returning_guide, title="[bold]🔄 Returning User Setup[/bold]", border_style="cyan"))
    
    else:
        commands_guide = """
[bold underline]Account Commands[/bold underline]
  [green]secretscli init[/green]      Create account or login
  [green]secretscli login[/green]     Login to existing account
  [green]secretscli logout[/green]    Logout from current session
  [green]secretscli status[/green]    Show current login status

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
"""
        console.print(Panel(commands_guide, title="[bold]📋 All Commands[/bold]", border_style="cyan"))



if __name__ == "__main__":
    app()