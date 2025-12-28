"""
SecretsCLI Configuration Management

Handles creation and management of configuration files:

Global Config (~/.secretscli/):
├── config.json     # User account settings
└── token.json      # Authentication tokens (restricted permissions)

Project Config (./.secretscli/):
└── project.json    # Project binding and sync info

Note: Master key is stored in OS keychain via `keyring`, not in files.
"""

from pathlib import Path
import sys
import logging

from .utils.utils import _create_json_file_

logger = logging.getLogger(__name__)

# Path Definitions
global_config_dir = Path.home() / ".secretscli"
global_config_file = global_config_dir / "config.json"
token_file = global_config_dir / "token.json"

# User account configuration
CONFIG_SCHEMA = {
    "email": None,
}

# Authentication tokens (stored with 0600 permissions)
TOKEN_SCHEMA = {
    "access_token": None,       # JWT access token for API calls
    "refresh_token": None,      # JWT refresh token for renewing access
    "expires_at": None,         # ISO timestamp when access_token expires
}

# Project-level configuration (per-directory)
PROJECT_SCHEMA = {
    "project_id": None,         # UUID of the linked project
    "project_name": None,       # Project name
    "environment": "development",  # Environment: development, staging, production
    "last_pull": None,          # ISO timestamp of last pull
    "last_push": None,          # ISO timestamp of last push
}


# Initialization Functions
def initialize_global_config(re_init: bool = False) -> bool:
    """
    Initialize the global SecretsCLI configuration directory.
    
    Creates ~/.secretscli/ with:
    - config.json: User account settings
    - token.json: Auth tokens (with restricted 0600 permissions)
    
    Args:
        re_init: If True, delete and recreate existing config files
        
    Returns:
        True if any files were newly created, False if all existed
    """
    newly_created = False

    try:
        if not global_config_dir.exists() or re_init:
            global_config_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Created global config directory: %s", global_config_dir)
            newly_created = True

        config_files = [
            (global_config_file, CONFIG_SCHEMA, False),
            (token_file, TOKEN_SCHEMA, True)  # True = secure (0600 permissions)
        ]

        for file_path, default_data, is_secure in config_files:
            # On re-init, remove existing files first
            if re_init and file_path.exists():
                file_path.unlink()
                logger.debug("Removed existing file: %s", file_path)

            if _create_json_file_(file_path, default_data, is_secure):
                newly_created = True

        return newly_created
    
    except PermissionError:
        logger.error("Permission denied creating config at %s", global_config_dir)
        sys.exit(1)
    except Exception as e:
        logger.error("Failed to initialize global config: %s", e)
        sys.exit(1)


def initialize_project_config(re_init: bool = False) -> bool:
    """
    Initialize project-level SecretsCLI configuration.
    
    Creates ./.secretscli/project.json in the current working directory
    to bind this directory to a SecretsCLI project.
    
    Args:
        re_init: If True, delete and recreate existing project config
        
    Returns:
        True if files were newly created, False if all existed
    """
    newly_created = False
    project_config_dir = Path.cwd() / ".secretscli"

    try:
        if not project_config_dir.exists() or re_init:
            project_config_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Created project config directory: %s", project_config_dir)
            newly_created = True

        project_file = project_config_dir / "project.json"
        
        if re_init and project_file.exists():
            project_file.unlink()
            logger.debug("Removed existing file: %s", project_file)

        if _create_json_file_(project_file, PROJECT_SCHEMA, False):
            newly_created = True

        return newly_created

    except PermissionError:
        logger.error("Permission denied creating project config at %s", project_config_dir)
        sys.exit(1)
    except Exception as e:
        logger.error("Failed to initialize project config: %s", e)
        sys.exit(1)

        

