"""
Project Commands

Commands for managing projects:
- create: Create a new project
- list: List all projects
- use: Set active project for current directory
- delete: Delete a project
"""

import typer
import rich
import questionary
from rich.table import Table
from rich.console import Console

from ..api.client import api_client
from ..utils.credentials import CredentialsManager
from ..prompts import custom_style


project_app = typer.Typer(name="project", help="Manage your projects. Run 'secretscli project --help' for subcommands.")
console = Console()


@project_app.command("create")
def create(
    project_name: str = typer.Argument(..., help="Name for the new project"),
    description: str = typer.Option(None, "--description", "-d", help="Optional project description")
    ):
    """
    Create a new project and bind it to the current directory.
    """
    if not project_name:
        rich.print("[red]Project name is required.[/red]")
        raise typer.Exit(1)
    
    # Build request data
    data = {"name": project_name}
    if description:
        data["description"] = description
    
    response = api_client.call("projects.create", "POST", data)
    if response.status_code != 201:
        rich.print(f"[red]Failed to create project: {response.text}[/red]")
        raise typer.Exit(1)
    
    project = response.json()
    project_data = project.get("data", {})
    project_id = project_data.get("id")
    
    # Store project config locally
    CredentialsManager.config_project(
        project_id=project_id,
        project_name=project_name,
        description=description,
        environment="development",
        last_pull=None,
        last_push=None
    )
    
    rich.print(f"[green]✅ Project '{project_name}' created and linked to this directory![/green]")


@project_app.command("list")
def list_projects():
    """
    List all your projects.
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
    
    # Create a pretty table
    table = Table(title="Your Projects", show_header=True, header_style="bold cyan")
    table.add_column("Name", style="green", no_wrap=True)
    table.add_column("Description", style="dim")
    
    for project in projects:
        name = project.get("name", "—")
        desc = project.get("description") or "—"
        table.add_row(name, desc)
    
    console.print()
    console.print(table)
    console.print()


@project_app.command("use")
def use_project(project_name: str):
    """
    Use a project.
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
    
    # Store project config locally
    CredentialsManager.config_project(
        project_id=project_id,
        project_name=project_name,
        description=project_data.get("description"),
        environment="development",
        last_pull=None,
        last_push=None
    )
    
    rich.print(f"[green]✅ Project '{project_name}' selected![/green]")


@project_app.command("update")
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
    
    response = api_client.call("projects.update", "PUT", data=data, project_name=project_name)
    if response.status_code != 200:
        rich.print(f"[red]Failed to update project: {response.text}[/red]")
        raise typer.Exit(1)
    
    rich.print(f"[green]✅ Project '{project_name}' updated![/green]")
    


@project_app.command("delete")
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
    
    response = api_client.call("projects.delete", "DELETE", project_name=project_name)
    if response.status_code != 200:
        rich.print(f"[red]Failed to delete project: {response.text}[/red]")
        raise typer.Exit(1)
    
    rich.print(f"[green]✅ Project '{project_name}' deleted![/green]")

