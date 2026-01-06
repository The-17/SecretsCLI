# SecretsCLI Developer Guide

> A comprehensive guide for developers working on SecretsCLI.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/The-17/SecretsCLI.git
cd SecretsCLI

# Install with dev dependencies
poetry install --with dev

# Activate virtual environment
poetry shell

# Run tests
pytest tests/ -v
```

---

## Architecture Overview

```
secretscli/
├── cli.py                 # Main Typer app, command groups
├── auth.py                # Login/signup/logout flows
├── encryption.py          # Cryptographic operations
├── config.py              # Configuration schemas
├── api/
│   └── client.py          # API client wrapper
├── commands/
│   ├── project.py         # Project CRUD commands
│   ├── secrets.py         # Secret management
│   └── workspace.py       # Workspace management
└── utils/
    ├── credentials.py     # Token/key storage
    ├── decorators.py      # @require_auth decorator
    └── env_manager.py     # .env file handling
```

---

## Key Concepts

### 1. Workspace Selection vs Project Binding

| Concept | Storage | Purpose |
|---------|---------|---------|
| **Selected Workspace** | Global config (`~/.secretscli/config.json`) | Default for NEW project creation |
| **Project Workspace** | Project config (`.secretscli/project.json`) | Permanent binding for THIS project |

**Important**: `workspace switch` only changes where NEW projects are created. It does NOT affect existing projects.

### 2. Encryption Model

```
User Keypair (X25519)
├── Private Key → Stored in OS keychain
└── Public Key → Sent to server

Workspace Key (Fernet)
├── Encrypted for each user with their public key
├── Stored in global cache (base64)
└── Copied to project.json for active project

Secret Encryption
├── Encrypt: plaintext → Fernet(workspace_key) → ciphertext
└── Decrypt: ciphertext → Fernet(workspace_key) → plaintext
```

### 3. Authentication Flow

```
login
├── POST /auth/login (email, password)
├── Receive JWT tokens + encrypted workspace keys
├── Store tokens in ~/.secretscli/token.json
├── Decrypt workspace keys using private key
├── Cache workspaces in global config
└── Set personal workspace as default selection
```

---

## Running Tests

```bash
# All tests with verbose output
pytest tests/ -v

# With coverage report
pytest tests/ --cov=secretscli --cov-report=html

# Specific test file
pytest tests/test_encryption.py -v

# Specific test class
pytest tests/test_credentials.py::TestWorkspaceCaching -v

# Run only fast unit tests
pytest tests/test_encryption.py tests/test_credentials.py -v
```

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures (mocks, temp dirs)
├── test_encryption.py       # Encryption unit tests
├── test_credentials.py      # Credentials manager tests
├── test_auth.py             # Login/signup tests
├── test_commands/
│   ├── test_project.py      # Project command tests
│   ├── test_secrets.py      # Secrets command tests
│   └── test_workspace.py    # Workspace command tests
└── test_integration.py      # End-to-end flows
```

### Mocking Strategy

- **Keyring**: Mocked with in-memory dict (for CI/CD)
- **API Client**: Mocked responses, no network calls
- **File System**: Temp directories for config files

---

## Adding New Commands

### 1. Create the command

```python
# secretscli/commands/myfeature.py
import typer
from ..utils.decorators import require_auth

myfeature_app = typer.Typer()

@myfeature_app.command("action")
@require_auth
def do_action():
    """Description of the command."""
    pass
```

### 2. Register in CLI

```python
# secretscli/cli.py
from .commands.myfeature import myfeature_app
app.add_typer(myfeature_app, name="myfeature")
```

### 3. Write tests

```python
# tests/test_commands/test_myfeature.py
def test_action_success():
    result = runner.invoke(app, ["myfeature", "action"])
    assert result.exit_code == 0
```

---

## Code Style

```bash
# Format code
black secretscli/ tests/

# Check without changing
black --check secretscli/ tests/
```

---

## Common Issues

### "No workspace key found"
- User hasn't run `project use <name>` to set up project.json
- Workspace key wasn't cached on login (re-login to fix)

### "Private key not found"
- Keys not stored in OS keychain
- User needs to run `secretscli signup` to regenerate

### Token expired
- Decorator auto-refreshes, but if refresh fails:
- User needs to `secretscli login` again

---

## Release Checklist

- [ ] All tests passing: `pytest tests/ -v`
- [ ] Code formatted: `black --check secretscli/`
- [ ] Version bumped in `pyproject.toml`
- [ ] CHANGELOG updated
- [ ] Git tagged: `git tag v0.x.x`
- [ ] Published: `poetry publish`
