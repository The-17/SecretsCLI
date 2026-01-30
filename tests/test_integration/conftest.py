"""
SecretsCLI Integration Tests - Configuration

Real end-to-end tests that hit the actual API.
These tests create a fresh test account on each run.

Run with: pytest tests/test_integration/ -v --tb=short

Note: Tests are ordered via pytest-ordering. Run in order for proper flow.
"""
import os
import pytest
import uuid
import tempfile
import json
from pathlib import Path
from datetime import datetime

from typer.testing import CliRunner

# Generate unique test identifiers per test run
TEST_RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
TEST_EMAIL = f"test_{TEST_RUN_ID}@secretscli-integration.test"
TEST_PASSWORD = f"TestPass123!{uuid.uuid4().hex[:8]}"

runner = CliRunner()


class TestSession:
    """
    Shared state across all integration tests.
    
    This class stores data that needs to persist between tests:
    - Test account credentials
    - Created project IDs (for cleanup)
    - Workspace info
    """
    email = TEST_EMAIL
    password = TEST_PASSWORD
    
    # Set after signup/login
    access_token = None
    refresh_token = None
    workspace_id = None
    workspace_key = None
    
    # Track created resources for cleanup
    created_projects = []
    
    # Temp directories for test isolation
    home_dir = None
    project_dir = None


@pytest.fixture(scope="session")
def test_session():
    """Provides access to shared test session data."""
    return TestSession


@pytest.fixture(scope="session")
def test_home(tmp_path_factory):
    """
    Create isolated home directory for tests.
    
    This prevents tests from affecting real ~/.secretscli config.
    """
    home = tmp_path_factory.mktemp("secretscli_test_home")
    config_dir = home / ".secretscli"
    config_dir.mkdir()
    
    # Create empty config files
    (config_dir / "config.json").write_text("{}")
    (config_dir / "token.json").write_text("{}")
    
    TestSession.home_dir = home
    
    # Patch home directory for all tests
    import secretscli.config as config_module
    original_dir = config_module.global_config_dir
    original_file = config_module.global_config_file
    original_token = config_module.token_file
    
    config_module.global_config_dir = config_dir
    config_module.global_config_file = config_dir / "config.json"
    config_module.token_file = config_dir / "token.json"
    
    yield home
    
    # Restore
    config_module.global_config_dir = original_dir
    config_module.global_config_file = original_file
    config_module.token_file = original_token


@pytest.fixture(scope="function")
def test_project_dir(tmp_path):
    """
    Create isolated project directory for each test.
    
    Each test gets a fresh .secretscli/project.json and .env
    """
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    config_dir = project_dir / ".secretscli"
    config_dir.mkdir()
    
    # Create empty project config
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
    
    # Create empty .env and .env.example
    (project_dir / ".env").write_text("")
    (project_dir / ".env.example").write_text("")
    
    original_cwd = os.getcwd()
    os.chdir(project_dir)
    
    TestSession.project_dir = project_dir
    
    yield project_dir
    
    os.chdir(original_cwd)


@pytest.fixture(scope="function")
def unique_project_name():
    """Generate unique project name for each test."""
    return f"test-project-{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="session", autouse=True)
def cleanup_on_finish(request, test_home):
    """
    Cleanup after all tests complete.
    
    Attempts to delete any projects created during tests.
    """
    yield
    
    # Cleanup logic runs after all tests
    from secretscli.cli import app
    
    for project_name in TestSession.created_projects:
        try:
            # Switch to the workspace and delete
            runner.invoke(app, ["project", "delete", project_name, "--force"])
        except Exception:
            pass  # Best effort cleanup


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "order(n): Run tests in specified order"
    )
