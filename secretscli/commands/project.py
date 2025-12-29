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

from ..api.client import api_client
from ..utils.credentials import CredentialsManager


project_app = typer.Typer(name="project", help="Manage your projects")


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



# TODO: Implement commands
# @project_app.command("list")
# @project_app.command("use")
# @project_app.command("delete")

