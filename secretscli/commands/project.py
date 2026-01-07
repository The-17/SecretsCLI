"""
Project Commands

This module defines all project-related CLI commands.
Projects are containers that organize related secrets (like folders).

COMMANDS:
--------
- create <name> [-d]: Create a new project and bind to current directory
- list: List all your projects in a table
- use <name>: Select a project for the current directory
- update <name> [-n] [-d]: Update project name or description
- delete <name> [-f]: Delete a project (with confirmation)

ARCHITECTURE:
------------
This module uses Typer's subcommand pattern:
    secretscli project <command>

The `project_app` Typer instance is registered in cli.py via:
    app.add_typer(project_app, name="project")

PROJECT CONFIGURATION:
---------------------
When you "use" a project, it stores the binding in:
    .secretscli/project.json

This file contains:
    - project_id: UUID of the project
    - project_name: Human-readable name
    - description: Optional description
    - environment: development/staging/production

TO ADD A NEW PROJECT COMMAND:
----------------------------
    @project_app.command("command-name")
    def my_command(arg: str = typer.Argument(...)):
        '''Docstring becomes help text'''
        # 1. Check authentication
        if not CredentialsManager.is_authenticated():
            ...
        # 2. Call API
        response = api_client.call("projects.action", "METHOD", ...)
        # 3. Update local config if needed
        CredentialsManager.config_project(...)
"""


import typer
import rich
import questionary
from rich.table import Table
from rich.console import Console
import base64

from ..api.client import api_client
from ..utils.credentials import CredentialsManager
from ..utils.env_manager import env
from ..utils.decorators import require_auth
from ..prompts import custom_style
from ..encryption import EncryptionService


project_app = typer.Typer(name="project", help="Manage your projects. Run 'secretscli project --help' for subcommands.")
console = Console()


@project_app.command("create")
@require_auth
def create(
    project_name: str = typer.Argument(..., help="Name for the new project"),
    description: str = typer.Option(None, "--description", "-d", help="Optional project description")
    ):
    """
    Create a new project and bind it to the current directory.
    
    Uses workspace from project.json, or defaults to personal workspace.
    """
    
    if not project_name:
        rich.print("[red]Project name is required.[/red]")
        raise typer.Exit(1)
    
    # For project CREATE, ALWAYS use the SELECTED workspace (set by workspace switch)
    # NOT the existing project.json workspace - that's for a different project
    workspace_id = CredentialsManager.get_selected_workspace_id()
    
    # Fallback: find personal workspace
    if not workspace_id:
        workspaces = CredentialsManager.get_workspace_keys()
        for ws_id, ws in workspaces.items():
            if ws.get("type") == "personal":
                workspace_id = ws_id
                break
        if not workspace_id and workspaces:
            workspace_id = list(workspaces.keys())[0]
    
    if not workspace_id:
        rich.print("[red]No workspace available. Please login first.[/red]")
        raise typer.Exit(1)
    
    # Build request data
    data = {
        "name": project_name,
        "workspace_id": workspace_id
    }
    if description:
        data["description"] = description
    
    response = api_client.call(
        "projects.create", 
        "POST", 
        data
    )

    if response.status_code != 201:
        rich.print(f"[red]Failed to create project: {response.text}[/red]")
        raise typer.Exit(1)
    
    # Get project and workspace info from API response
    project_data = response.json().get("data", {})
    project_id = project_data.get("id")
    workspace_id = project_data.get("workspace_id")
    
    # Get workspace info from global cache
    workspace = CredentialsManager.get_workspace(workspace_id)
    
    # Set project.json from API response (workspace_key is NOT stored here)
    CredentialsManager.config_project(
        project_id=project_id,
        project_name=project_name,
        description=description,
        environment="development",
        workspace_id=workspace_id,
        workspace_name=workspace.get("name"),
        last_pull=None,
        last_push=None
    )
    
    rich.print(f"[green]✅ Project '{project_name}' created (workspace: {workspace.get('name')})[/green]")


@project_app.command("list")
@require_auth
def list_projects():
    """
    List all your projects, grouped by workspace.
    """
    response = api_client.call("projects.list", "GET")

    if response.status_code != 200:
        rich.print(f"[red]Failed to list projects: {response.text}[/red]")
        raise typer.Exit(1)

    data = response.json()
    projects = data.get("data", [])
    
    if not projects:
        rich.print("[yellow]No projects found. Create one with 'secretscli project create <name>'[/yellow]")
        return
    
    # Group projects by workspace
    workspaces = CredentialsManager.get_workspace_keys()
    
    # Sort projects by workspace name for grouping
    def get_workspace_name(project):
        ws_id = project.get("workspace_id")
        ws = workspaces.get(ws_id, {})
        return ws.get("name", "Unknown")
    
    projects_sorted = sorted(projects, key=get_workspace_name)
    
    table = Table(title="Your Projects", show_header=True, header_style="bold cyan")
    table.add_column("Project", style="green", no_wrap=True)
    table.add_column("Workspace", style="cyan")
    table.add_column("Description", style="dim")
    
    current_workspace = None
    for project in projects_sorted:
        ws_id = project.get("workspace_id")
        ws = workspaces.get(ws_id, {})
        ws_name = ws.get("name", "Unknown")
        
        # Add separator row when workspace changes
        if current_workspace is not None and current_workspace != ws_name:
            table.add_row("", "", "")  # Visual separator
        current_workspace = ws_name
        
        name = project.get("name", "—")
        desc = project.get("description") or "—"
        table.add_row(name, ws_name, desc)
    
    console.print()
    console.print(table)
    console.print()


@project_app.command("use")
@require_auth
def use_project(project_name: str):
    """
    Use a project.
    
    Sets project config with workspace_id. Workspace key is looked up
    from global config at runtime, not stored in project.json.
    """
    
    if not project_name:
        rich.print("[red]Project name is required.[/red]")
        raise typer.Exit(1)
    
    response = api_client.call("projects.get", "GET", project_name=project_name)
    if response.status_code != 200:
        rich.print(f"[red]Failed to get project: {response.text}[/red]")
        raise typer.Exit(1)
    
    project = response.json()
    project_data = project.get("data", {})
    project_id = project_data.get("id")
    
    # Get workspace info from global cache
    workspace_id = project_data.get("workspace_id")
    workspace = CredentialsManager.get_workspace(workspace_id)
    workspace_name = workspace.get("name")
    
    # Store project config (workspace_key is NOT stored here)
    CredentialsManager.config_project(
        project_id=project_id,
        project_name=project_name,
        description=project_data.get("description"),
        environment="development",
        workspace_id=workspace_id,
        workspace_name=workspace_name,
        last_pull=None,
        last_push=None
    )
    
    if workspace_name:
        rich.print(f"[green]✅ Project '{project_name}' selected (workspace: {workspace_name})[/green]")
    else:
        rich.print(f"[green]✅ Project '{project_name}' selected![/green]")


@project_app.command("update")
@require_auth
def update_project(
    project_name: str = typer.Argument(..., help="Current project name (used to identify the project)"),
    name: str = typer.Option(None, "--name", "-n", help="New name for the project"),
    description: str = typer.Option(None, "--description", "-d", help="New description for the project")
):
    """
    Update a project's name or description.
    
    The PROJECT_NAME argument identifies which project to update.
    Use --name to change the project name, --description to change the description,
    or both to update them together.
    
    Examples:
        secretscli project update my-app --description "Updated description"
        secretscli project update my-app --name new-app-name
        secretscli project update my-app -n new-name -d "New description"
    """
    if not project_name:
        rich.print("[red]Project name is required.[/red]")
        raise typer.Exit(1)
    
    # Require at least one update field
    if not name and not description:
        rich.print("[red]Please provide at least one field to update: --name or --description[/red]")
        raise typer.Exit(1)
    
    # Build update payload (only include provided fields)
    data = {}
    if name:
        data["name"] = name
    if description:
        data["description"] = description
    
    response = api_client.call(
        "projects.update", 
        "PATCH", 
        data=data, 
        project_name=project_name
    )

    if response.status_code != 200:
        rich.print(f"[red]Failed to update project: {response.text}[/red]")
        raise typer.Exit(1)
    
    rich.print(f"[green]✅ Project '{project_name}' updated![/green]")
    


@project_app.command("delete")
@require_auth
def delete_project(
    project_name: str = typer.Argument(..., help="Project name to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation")
):
    """
    Delete a project.
    """
    if not project_name:
        rich.print("[red]Project name is required.[/red]")
        raise typer.Exit(1)
    
    # Confirm deletion unless --force is used
    if not force:
        confirm = questionary.confirm(
            f"Are you sure you want to delete project '{project_name}'? This cannot be undone",
            default=False,
            style=custom_style
        ).ask()
        if not confirm:
            rich.print("[yellow]Deletion cancelled.[/yellow]")
            raise typer.Exit(0)
    
    response = api_client.call(
        "projects.delete", 
        "DELETE", 
        project_name=project_name
    )

    if response.status_code != 200:
        rich.print(f"[red]Failed to delete project: {response.text}[/red]")
        raise typer.Exit(1)
    
    rich.print(f"[green]✅ Project '{project_name}' deleted![/green]")


@project_app.command("invite")
@require_auth
def invite_to_project(
    email: str = typer.Argument(..., help="Email of the user to invite"),
    role: str = typer.Option("member", "--role", "-r", help="Role: owner, admin, member, read_only")
):
    """
    Invite a user to the current project.
    
    If this is the first time sharing, a shared workspace is auto-created.
    The project is moved to the shared workspace and the user is invited.
    
    Example:
        secretscli project invite alice@example.com
        secretscli project invite bob@example.com --role admin
    """
    
    # Get current project
    project_name = CredentialsManager.get_project_name()
    if not project_name:
        rich.print("[red]No project selected. Run 'secretscli project use <name>' first.[/red]")
        raise typer.Exit(1)
    
    # Get invitee's public key
    response = api_client.call(
        "users.public_key",
        "GET", 
        email=email
    )

    if response.status_code != 200:
        rich.print(f"[red]User '{email}' not found or does not have a public key.[/red]")
        raise typer.Exit(1)
    
    invitee_public_key = base64.b64decode(response.json()["data"]["public_key"])
    
    # Get our public key from keychain
    my_public_key = CredentialsManager.get_public_key()
    if not my_public_key:
        rich.print("[red]Public key not found. Please re-login.[/red]")
        raise typer.Exit(1)
    
    secrets = env.read()
    decrypted_secrets = {}
    api_secrets = []

    # decryt secrets for re-encryption with new workspace key
    for key, value in secrets.items():
        decrypted_value = EncryptionService.decrypt_secret(value)
        decrypted_secrets[key] = decrypted_value
    
    # Generate NEW workspace key for the shared workspace
    new_workspace_key = EncryptionService.generate_workspace_key()

    # encrypt with new workspace key
    for key, value in decrypted_secrets.items():
        encrypted_value = EncryptionService.encrypt_secret(value, new_workspace_key)
        api_secrets.append({"key":key, "value":encrypted_value})
    
    # Encrypt workspace key for both parties
    encrypted_for_owner = EncryptionService.encrypt_for_user(my_public_key, new_workspace_key)
    encrypted_for_invitee = EncryptionService.encrypt_for_user(invitee_public_key, new_workspace_key)
    
    # Send to API - it handles workspace creation and project migration
    response = api_client.call(
        "projects.invite",
        "POST",
        project_name=project_name,
        data={
            "email": email,
            "role": role,
            "encrypted_workspace_key_owner": base64.b64encode(encrypted_for_owner).decode(),
            "encrypted_workspace_key_invitee": base64.b64encode(encrypted_for_invitee).decode(),
            "secrets": api_secrets
        }
    )
    
    if response.status_code not in (200, 201):
        rich.print(f"[red]Failed to invite user: {response.text}[/red]")
        raise typer.Exit(1)
    
    result = response.json().get("data", {})
    ws_name = result.get("workspace_name", "shared workspace")
    
    # Update local workspace keys
    workspace_id = result.get("workspace_id")
    if workspace_id:
        workspaces = CredentialsManager.get_workspace_keys()
        workspaces[workspace_id] = {
            "name": ws_name,
            "key": base64.b64encode(new_workspace_key).decode(),
            "role": "owner",
            "type": "shared"
        }
        CredentialsManager.store_workspace_keys(workspaces)
    
    rich.print(f"[green]✅ Invited {email} to project![/green]")
    rich.print(f"[dim]Created shared workspace: {ws_name}[/dim]")

