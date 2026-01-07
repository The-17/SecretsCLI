"""
SecretsCLI Test Configuration

Shared fixtures for mocking API, keyring, file system, and authentication.
"""
import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import base64
import os
import tempfile


# ============================================================
# AUTH BYPASS - For command tests that need authenticated context
# ============================================================

@pytest.fixture
def bypass_auth():
    """
    Bypass @require_auth decorator for command tests.
    Use this fixture explicitly in tests that invoke CLI commands.
    """
    with patch('secretscli.utils.decorators.CredentialsManager.get_access_token', return_value="mock_access_token"):
        with patch('secretscli.utils.decorators.CredentialsManager.get_tokens', return_value={
            "access_token": "mock_access_token",
            "refresh_token": "mock_refresh_token",
            "expires_at": "2099-12-31T23:59:59+00:00"  # Far future
        }):
            with patch('secretscli.utils.decorators.CredentialsManager.get_email', return_value="test@example.com"):
                with patch('secretscli.utils.decorators.CredentialsManager.get_private_key', return_value=b"mock_private_key_32bytes_here!!"):
                    yield


# ============================================================
# KEYRING MOCK - For CI/CD without system keyring
# ============================================================

@pytest.fixture
def mock_keyring():
    """Mock keyring storage - stores passwords in memory."""
    storage = {}
    
    def set_password(service, key, value):
        storage[(service, key)] = value
    
    def get_password(service, key):
        return storage.get((service, key))
    
    def delete_password(service, key):
        storage.pop((service, key), None)
    
    with patch('keyring.set_password', side_effect=set_password):
        with patch('keyring.get_password', side_effect=get_password):
            with patch('keyring.delete_password', side_effect=delete_password):
                yield storage


# ============================================================
# API CLIENT MOCK - For testing without network calls
# ============================================================

@pytest.fixture
def mock_api():
    """Mock API client with configurable responses."""
    with patch('secretscli.api.client.api_client.call') as mock:
        yield mock


def make_api_response(status_code: int, data=None, error: str = None):
    """Helper to create mock API responses."""
    response = MagicMock()
    response.status_code = status_code
    if data is not None:
        response.json.return_value = {"data": data}
        response.text = json.dumps({"data": data})
    elif error:
        response.json.return_value = {"error": error}
        response.text = json.dumps({"error": error})
    else:
        response.json.return_value = {}
        response.text = "{}"
    return response


# ============================================================
# FILE SYSTEM FIXTURES - Isolated temp directories
# ============================================================

@pytest.fixture
def temp_home(tmp_path):
    """Create isolated temp home directory with .secretscli config folder."""
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    config_dir = home_dir / ".secretscli"
    config_dir.mkdir()
    
    # Create empty config files
    (config_dir / "config.json").write_text("{}")
    (config_dir / "token.json").write_text("{}")
    
    # Patch Path.home() to return our temp home
    with patch('secretscli.utils.credentials.Path.home', return_value=home_dir):
        yield home_dir


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create temp project directory with .secretscli folder."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    config_dir = project_dir / ".secretscli"
    config_dir.mkdir()
    
    # Create empty project.json
    project_config = {
        "project_id": None,
        "project_name": None,
        "description": None,
        "environment": "development",
        "workspace_id": None,
        "workspace_name": None,
        "last_pull": None,
        "last_push": None
    }
    (config_dir / "project.json").write_text(json.dumps(project_config, indent=2))
    
    # Create empty .env
    (project_dir / ".env").write_text("")
    
    original_cwd = os.getcwd()
    os.chdir(project_dir)
    
    yield project_dir
    
    os.chdir(original_cwd)


@pytest.fixture
def temp_env_file(temp_project_dir):
    """Create temp .env file with test secrets."""
    env_content = """DATABASE_URL=postgres://localhost:5432/mydb
API_KEY=sk_test_12345
SECRET_TOKEN=super_secret_value"""
    (temp_project_dir / ".env").write_text(env_content)
    yield temp_project_dir / ".env"


# ============================================================
# SAMPLE DATA FIXTURES
# ============================================================

@pytest.fixture
def sample_workspace_key():
    """Generate a sample Fernet key for testing."""
    from cryptography.fernet import Fernet
    return Fernet.generate_key()


@pytest.fixture
def sample_keypair():
    """Generate a sample X25519 keypair for testing."""
    from nacl.public import PrivateKey
    private_key = PrivateKey.generate()
    return bytes(private_key), bytes(private_key.public_key)


@pytest.fixture
def sample_workspaces(sample_workspace_key):
    """Sample workspaces dict as stored in global config."""
    key_b64 = base64.b64encode(sample_workspace_key).decode()
    return {
        "ws-personal-123": {
            "name": "Personal Workspace",
            "key": key_b64,
            "role": "owner",
            "type": "personal"
        },
        "ws-team-456": {
            "name": "Team Workspace",
            "key": key_b64,
            "role": "member",
            "type": "team"
        }
    }


@pytest.fixture
def sample_projects():
    """Sample projects list as returned from API."""
    return [
        {
            "id": "proj-1",
            "name": "my-api",
            "description": "My API project",
            "workspace_id": "ws-personal-123"
        },
        {
            "id": "proj-2",
            "name": "team-app",
            "description": "Team application",
            "workspace_id": "ws-team-456"
        }
    ]


# ============================================================
# INTEGRATION FIXTURES - Combine multiple mocks
# ============================================================

@pytest.fixture
def full_mock_env(mock_keyring, temp_home, temp_project_dir, sample_workspaces, bypass_auth):
    """
    Full mock environment for integration tests.
    
    Provides:
    - Mocked keyring
    - Temp home with config dir  
    - Temp project dir with project.json
    - Sample workspaces pre-loaded
    - Auth bypass for CLI commands
    """
    # Pre-populate global config with workspaces
    config = {
        "email": "test@example.com",
        "workspaces": sample_workspaces,
        "selected_workspace_id": "ws-personal-123"
    }
    config_file = temp_home / ".secretscli" / "config.json"
    config_file.write_text(json.dumps(config, indent=2))
    
    yield {
        "home": temp_home,
        "project": temp_project_dir,
        "keyring": mock_keyring,
        "workspaces": sample_workspaces
    }
