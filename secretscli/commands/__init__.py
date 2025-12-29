"""
SecretsCLI Command Groups

This module exports all subcommand Typer apps to be registered with the main app.
"""

from .project import project_app
from .secrets import secrets_app

__all__ = ["project_app", "secrets_app"]
