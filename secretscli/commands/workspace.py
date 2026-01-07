"""
Workspace Commands

Manage workspaces for team collaboration and secret sharing.

COMMANDS:
    list    - List all workspaces you have access to
    create  - Create a new team workspace
    switch  - Switch active workspace
    invite  - Invite a user to the current workspace
    members - List members of the current workspace
    remove  - Remove a member from the workspace

USAGE:
    secretscli workspace list
    secretscli workspace create "Team Backend"
    secretscli workspace switch "Team Backend"
    secretscli workspace invite alice@example.com --role member
    secretscli workspace members
    secretscli workspace remove alice@example.com
"""

import base64
from typing import Optional

import typer
import rich
from rich.table import Table
from rich.console import Console

from ..api.client import api_client
from ..encryption import EncryptionService
from ..utils.credentials import CredentialsManager
from ..utils.decorators import require_auth


workspace_app = typer.Typer(name="workspace", help="Manage workspaces and teams.")
console = Console()


@workspace_app.command("list")
@require_auth
def list_workspaces():
    """List all workspaces you have access to."""
    workspaces = CredentialsManager.get_workspace_keys()
    
    if not workspaces:
        rich.print("[yellow]No workspaces found. Create one with 'secretscli workspace create <name>'[/yellow]")
        return
    
    project_ws = CredentialsManager.get_project_workspace_id()
    selected_ws = CredentialsManager.get_selected_workspace_id()
    
    table = Table(title="Your Workspaces", show_header=True, header_style="bold cyan")
    table.add_column("Name", style="white")
    table.add_column("Type", style="dim")
    table.add_column("Role", style="dim")
    table.add_column("", style="green")

    for ws_id, ws in workspaces.items():
        # Show which is current project's workspace and which is selected for new projects
        indicators = []
        if ws_id == project_ws:
            indicators.append("(Current Project)")
        if ws_id == selected_ws:
            indicators.append("(Selected)")
        table.add_row(ws.get("name", ws_id), ws.get("type", "—"), ws.get("role", "—"), " ".join(indicators))
    
    console.print()
    console.print(table)
    console.print()


@workspace_app.command("create")
@require_auth
def create_workspace(name: str = typer.Argument(..., help="Name for the new workspace")):
    """Create a new team workspace."""
    # Generate workspace key
    workspace_key = EncryptionService.generate_workspace_key()
    
    # Get our public key from keychain
    public_key = CredentialsManager.get_public_key()
    
    if not public_key:
        rich.print("[red]Public key not found. Please login again.[/red]")
        raise typer.Exit(1)
    
    # Encrypt workspace key with our public key
    encrypted_workspace_key = EncryptionService.encrypt_for_user(public_key, workspace_key)
    
    # Send to API
    response = api_client.call(
        "workspaces.create",
        "POST",
        data={
            "name": name,
            "encrypted_workspace_key": base64.b64encode(encrypted_workspace_key).decode()
        }
    )
    
    if response.status_code != 201:
        rich.print(f"[red]Failed to create workspace: {response.text}[/red]")
        raise typer.Exit(1)
    
    ws_data = response.json().get("data", {})
    ws_id = ws_data.get("id")
    
    # Store workspace key locally
    workspaces = CredentialsManager.get_workspace_keys()
    workspaces[ws_id] = {
        "name": name,
        "key": base64.b64encode(workspace_key).decode(),
        "role": "owner",
        "type": "team"
    }
    CredentialsManager.store_workspace_keys(workspaces)
    
    rich.print(f"[green]Workspace '{name}' created run 'secretscli workspace switch {name}' to use this workspace for this project[/green]")


@workspace_app.command("switch")
@require_auth
def switch_workspace(name: str = typer.Argument(..., help="Workspace name or 'personal' to switch to")):
    """
    Select a workspace for NEW project creation.
    
    Use 'personal' to quickly switch to your personal workspace.
    This does NOT change the workspace of your current project.
    To work on a project in a different workspace, use 'secretscli project use <name>'.
    """
    workspaces = CredentialsManager.get_workspace_keys()
    current_selected = CredentialsManager.get_selected_workspace_id()
    
    # Handle "personal" keyword
    if name.lower() == "personal":
        for ws_id, ws in workspaces.items():
            if ws.get("type") == "personal":
                if ws_id == current_selected:
                    rich.print(f"[yellow]Personal workspace is already selected for new projects.[/yellow]")
                    return
                CredentialsManager.set_selected_workspace(ws_id)
                rich.print(f"[green]Selected personal workspace for new projects[/green]")
                rich.print(f"[dim]Run 'secretscli project create <name>' to create a project in this workspace[/dim]")
                return
        rich.print("[red]Personal workspace not found.[/red]")
        raise typer.Exit(1)
    
    # Find workspace by name
    for ws_id, ws in workspaces.items():
        if ws.get("name", "").lower() == name.lower():
            # Check if already selected
            if ws_id == current_selected:
                rich.print(f"[yellow]Workspace '{ws.get('name')}' is already selected for new projects.[/yellow]")
                return
            # Update GLOBAL selected workspace (for new project creation)
            CredentialsManager.set_selected_workspace(ws_id)
            rich.print(f"[green]Selected workspace '{ws.get('name')}' for new projects[/green]")
            rich.print(f"[dim]Run 'secretscli project create <name>' to create a project in this workspace[/dim]")
            return
    
    rich.print(f"[red]Workspace '{name}' not found. Run 'secretscli workspace list' to see available workspaces.[/red]")
    raise typer.Exit(1)


@workspace_app.command("invite")
@require_auth
def invite_member(
    email: str = typer.Argument(..., help="Email of the user to invite"),
    role: str = typer.Option("member", "--role", "-r", help="Role: owner, admin, member, read_only")
):
    """
    Invite a user to the selected workspace.
    
    Uses the workspace set by 'workspace switch'. To invite to a different
    workspace, switch to it first with 'secretscli workspace switch <name>'.
    
    For inviting to a specific project's workspace, use 'project invite' instead.
    """
    workspace_id = CredentialsManager.get_selected_workspace_id()
    if not workspace_id:
        rich.print("[red]No workspace selected. Run 'secretscli workspace switch <name>' first.[/red]")
        raise typer.Exit(1)
    
    # Get workspace info for display
    workspace = CredentialsManager.get_workspace(workspace_id)
    workspace_name = workspace.get("name", "workspace")
    
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
    
    # Get workspace key from global cache
    workspace_key = CredentialsManager.get_workspace_key(workspace_id)
    if not workspace_key:
        rich.print("[red]Workspace key not found. Please re-login.[/red]")
        raise typer.Exit(1)
    
    # Encrypt workspace key for invitee
    encrypted_for_invitee = EncryptionService.encrypt_for_user(invitee_public_key, workspace_key)
    
    # Send invite
    response = api_client.call(
        "workspaces.invite",
        "POST",
        workspace_id=workspace_id,
        data={
            "email": email,
            "role": role if role is not None else "member",
            "encrypted_workspace_key": base64.b64encode(encrypted_for_invitee).decode()
        }
    )
    
    if response.status_code not in (200, 201):
        rich.print(f"[red]Failed to invite user: {response.text}[/red]")
        raise typer.Exit(1)
    
    rich.print(f"[green]Invited {email} to '{workspace_name}' as {role}![/green]")


@workspace_app.command("members")
@require_auth
def list_members():
    """
    List members of the selected workspace.
    
    Uses the workspace set by 'workspace switch'.
    """
    workspace_id = CredentialsManager.get_selected_workspace_id()
    if not workspace_id:
        rich.print("[red]No workspace selected. Run 'secretscli workspace switch <name>' first.[/red]")
        raise typer.Exit(1)
    
    response = api_client.call(
        "workspaces.members",
        "GET",
        workspace_id=workspace_id
    )
    
    if response.status_code != 200:
        rich.print(f"[red]Failed to list members: {response.text}[/red]")
        raise typer.Exit(1)
    
    members = response.json().get("data", {})
    
    if not members:
        rich.print("[yellow]No members found in this workspace.[/yellow]")
        return
    
    workspaces = CredentialsManager.get_workspace_keys()
    ws_name = workspaces.get(workspace_id, {}).get("name", "Workspace")
    
    table = Table(title=f"Members of '{ws_name}'", show_header=True, header_style="bold cyan")
    table.add_column("Email", style="white")
    table.add_column("Role", style="dim")
    table.add_column("Status", style="dim")
    
    for member in members:
        table.add_row(
            member.get("email", "—"),
            member.get("role", "—"),
            member.get("status", "active")
        )
    
    console.print()
    console.print(table)
    console.print()


@workspace_app.command("remove")
@require_auth
def remove_member(email: str = typer.Argument(..., help="Email of the user to remove")):
    """
    Remove a member from the selected workspace.
    
    Uses the workspace set by 'workspace switch'.
    """
    workspace_id = CredentialsManager.get_selected_workspace_id()
    if not workspace_id:
        rich.print("[red]No workspace selected. Run 'secretscli workspace switch <name>' first.[/red]")
        raise typer.Exit(1)
    
    # Get workspace name for display
    workspace = CredentialsManager.get_workspace(workspace_id)
    workspace_name = workspace.get("name", "workspace")
    
    response = api_client.call(
        "workspaces.remove_member",
        "DELETE",
        workspace_id=workspace_id,
        email=email
    )
    
    if response.status_code != 200:
        rich.print(f"[red]Failed to remove member: {response.text}[/red]")
        raise typer.Exit(1)
    
    rich.print(f"[green]Removed {email} from '{workspace_name}'![/green]")
