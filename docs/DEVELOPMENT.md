# SecretsCLI Developer Guide

For developers working on SecretsCLI.

---

## Quick Start

```bash
git clone https://github.com/The-17/SecretsCLI.git
cd SecretsCLI
poetry install --with dev
poetry run pytest tests/ -v
```

---

## Project Structure

```
secretscli/
├── cli.py               # Main Typer app, command groups
├── auth.py              # Login/signup/logout flows
├── encryption.py        # Cryptographic operations
├── config.py            # Configuration schemas
├── api/
│   └── client.py        # API client wrapper
├── commands/
│   ├── project.py       # Project CRUD commands
│   ├── secrets.py       # Secret management
│   └── workspace.py     # Workspace management
└── utils/
    ├── credentials.py   # Token/key storage
    ├── decorators.py    # @require_auth decorator
    └── env_manager.py   # .env file handling
```

---

## Key Concepts

### Workspace Selection vs Project Binding

**Selected Workspace** - Stored in global config (`~/.secretscli/config.json`). Used as default for NEW project creation.

**Project Workspace** - Stored in project config (`.secretscli/project.json`). Permanent binding for THIS project.

`workspace switch` only changes where NEW projects are created. It doesn't affect existing projects.

### Encryption Model

**User Keypair (X25519)** - Private key stored in OS keychain, public key on server.

**Workspace Key (Fernet)** - Each workspace has one. Encrypted for each user with their public key.

**Secret Encryption** - Secrets encrypted/decrypted with workspace key.

Password → User Key → decrypts Private Key → decrypts Workspace Key → decrypts Secrets

### Authentication Flow

1. POST /auth/login (email, password)
2. Receive JWT tokens + encrypted workspace keys
3. Store tokens in ~/.secretscli/token.json
4. Decrypt workspace keys using private key
5. Cache workspaces in global config
6. Set personal workspace as default selection

---

## Running Tests

```bash
# All tests (unit + integration)
poetry run pytest tests/ -v

# Unit tests only (mocked, fast)
poetry run pytest tests/ --ignore=tests/test_integration/ -v

# Integration tests only (real API, requires network)
poetry run pytest tests/test_integration/ -v

# With coverage
poetry run pytest tests/ --cov=secretscli --cov-report=html

# Specific file
poetry run pytest tests/test_encryption.py -v

# Specific class
poetry run pytest tests/test_credentials.py::TestWorkspaceCaching -v
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
└── test_integration/        # Real API tests (no mocks)
    ├── conftest.py          # Integration fixtures & test account
    ├── test_01_auth.py      # Signup, login, token storage
    ├── test_02_project.py   # Create, list, use, delete projects
    ├── test_03_secrets.py   # Set, get, push, pull, diff secrets
    └── test_04_workspace.py # Workspace operations
```

### Unit Tests (Mocked)

- **Keyring** - Mocked with in-memory dict (for CI/CD)
- **API Client** - Mocked responses, no network calls
- **File System** - Temp directories for config files

### Integration Tests (Real API)

- Creates a fresh test account each run
- Hits the real API with no mocks
- Tests full end-to-end flows
- Cleans up test projects after completion

> **Note:** Integration tests require network access and take longer (~1-5 minutes).

---

## Adding New Commands

1. Create the command in the appropriate file
2. Use `@require_auth` decorator if login is required
3. Register in `cli.py` if it's a new command group
4. Write tests

Example:

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

---

## Code Style

```bash
# Format code
poetry run black secretscli/ tests/

# Check without changing
poetry run black --check secretscli/ tests/
```

---

## Common Issues

**"No workspace key found"** - User hasn't run `project use <name>` or workspace key wasn't cached on login. Re-login to fix.

**"Private key not found"** - Keys not stored in OS keychain. User needs to run `secretscli init` again.

**Token expired** - Decorator auto-refreshes, but if refresh fails, user needs to `secretscli login` again.

---

## Release Checklist

- [ ] All tests passing: `poetry run pytest tests/ -v`
- [ ] Code formatted: `poetry run black --check secretscli/`
- [ ] Version bumped in `pyproject.toml`
- [ ] CHANGELOG updated
- [ ] Git tagged: `git tag v0.x.x`
- [ ] Published: `poetry publish`
