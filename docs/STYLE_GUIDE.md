# SecretsCLI Style Guide

This guide ensures consistency across the codebase and makes collaboration easier.

## Python Style Guide

### General Principles
- **Readability counts** - Code is read more than written
- **Explicit is better than implicit**
- **Simple is better than complex**
- **Consistency matters**

### Formatting

#### Code Formatter
Use **Black** with default settings (88 character line length):
```bash
black secretscli/
```

#### Line Length
- Maximum 88 characters (Black default)
- Break long lines naturally at logical points

#### Imports
Organize imports in three groups:

1. Standard library
2. Third-party packages
3. Local imports

```python
# Standard library
import os
import sys
from typing import Dict, List, Optional

# Third-party
import click
import requests
from cryptography.fernet import Fernet

# Local
from secretscli.auth import AuthManager
from secretscli.encryption import CLIEncryption
```

Use absolute imports:
```python
# Good
from secretscli.auth import AuthManager

# Avoid
from .auth import AuthManager  # Relative imports
```

### Naming Conventions

#### Variables and Functions
- Use `snake_case`
- Be descriptive
- Avoid single-letter names (except loops)
```python
# Good
user_email = "user@example.com"
def get_user_projects(user_id):
    pass

# Avoid
e = "user@example.com"
def gup(u):
    pass
```

#### Classes
- Use `PascalCase`
- Noun phrases
```python
# Good
class AuthManager:
    pass

class ProjectSerializer:
    pass

# Avoid
class auth_manager:
    pass
```

#### Constants
- Use `UPPER_SNAKE_CASE`
- Define at module level
```python
API_BASE_URL = "https://api.secretscli.com"
MAX_RETRY_ATTEMPTS = 3
DEFAULT_TIMEOUT = 30
```

#### Private Members
- Prefix with single underscore and suffix with single underscore
- Not enforced, just convention
```python
class User:
    def __init__(self):
        self._password = None  # Private
        
    def _validate_email_(self, email):  # Private method
        pass
```

### Type Hints

Use type hints for function signatures:
```python
from typing import Dict, List, Optional

def get_secret(key: str, project_id: str) -> Optional[str]:
    """Get a secret value."""
    pass

def list_projects(user_id: int) -> List[Dict[str, str]]:
    """List all projects for a user."""
    pass
```

Type hints are **encouraged** but not strictly required for internal functions.

### Docstrings

Use **Google-style** docstrings:
```python
def encrypt_secret(plaintext: str, key: bytes) -> str:
    """
    Encrypt a secret value.
    
    Args:
        plaintext: The secret value to encrypt
        key: Encryption key (32 bytes)
    
    Returns:
        Base64-encoded encrypted string
    
    Raises:
        ValueError: If plaintext is empty
        InvalidToken: If encryption fails
    
    Example:
        >>> key = Fernet.generate_key()
        >>> encrypted = encrypt_secret("my-secret", key)

    Dependencies:
        
    """
    pass
```

For simple functions, a one-line docstring is fine:
```python
def is_logged_in() -> bool:
    """Check if user is currently logged in."""
    pass
```

### Error Handling

#### Specific Exceptions
Catch specific exceptions, not bare `except`:
```python
# Good
try:
    user = authenticate(email, password)
except InvalidCredentialsError:
    print("Invalid credentials")
except NetworkError:
    print("Network error")

# Avoid
try:
    user = authenticate(email, password)
except:  # Too broad
    print("Something went wrong")
```

#### Custom Exceptions
Create custom exceptions for domain-specific errors:
```python
class SecretsCLIError(Exception):
    """Base exception for SecretsCLI."""
    pass

class AuthenticationError(SecretsCLIError):
    """Authentication failed."""
    pass

class ProjectNotFoundError(SecretsCLIError):
    """Project does not exist."""
    pass
```

### Functions

#### Length
Keep functions focused and short:
- Aim for < 50 lines
- One responsibility per function
- Extract complex logic into helper functions

#### Parameters
- Maximum 5 parameters
- Use `**kwargs` for optional parameters
- Provide defaults where sensible
```python
# Good
def create_project(name: str, description: str = "", owner_id: Optional[int] = None):
    pass

# Avoid (too many parameters)
def create_project(name, desc, owner, created, updated, status, tags, meta):
    pass
```

#### Return Values
- Be consistent with return types
- Use `None` for "not found" cases
- Return same type or raise exception
```python
# Good
def get_secret(key: str) -> Optional[str]:
    if key in secrets:
        return secrets[key]
    return None

# Avoid (inconsistent return)
def get_secret(key: str):
    if key in secrets:
        return secrets[key]
    return False  # Should be None
```

### Comments

#### When to Comment
- Why, not what
- Complex algorithms
- Non-obvious decisions
- Workarounds or hacks
```python
# Good - Explains WHY
# Use PBKDF2 with 100k iterations to prevent brute force attacks
# while maintaining reasonable performance on standard hardware
key = derive_key(password, salt, iterations=100000)

# Avoid - Explains WHAT (obvious from code)
# Set x to 5
x = 5
```

#### TODO Comments
Format: `# TODO(username): Description`
```python
# TODO(john): Add retry logic for network failures
def fetch_secrets():
    pass
```

### Testing

#### Test File Structure
Mirror the source structure:
```
secretscli/
  auth.py
  encryption.py
tests/
  test_auth.py
  test_encryption.py
```

#### Test Function Names
Be descriptive, use `test_` prefix:
```python
def test_login_with_valid_credentials():
    pass

def test_login_with_invalid_password():
    pass

def test_encryption_with_empty_string_raises_error():
    pass
```

#### Arrange-Act-Assert Pattern
```python
def test_create_project():
    # Arrange
    user = create_test_user()
    project_name = "test-project"
    
    # Act
    project = create_project(user, project_name)
    
    # Assert
    assert project.name == project_name
    assert project.owner == user
```

### CLI Output

#### Messages
- Be concise and clear
- Use emojis sparingly for visual cues
- Provide actionable information
```python
# Good
click.echo("✅ Secret 'DATABASE_URL' created successfully")
click.echo("❌ Project not found. Run 'secretscli project list' to see available projects")

# Avoid
click.echo("Done!")  # Too vague
click.echo("🎉🔥💯 SUPER AWESOME SECRET CREATED 🚀✨🎊")  # Too many emojis
```

#### Progress Indicators
Use spinners or progress bars for long operations:
```python
with click.progressbar(secrets, label='Encrypting secrets') as bar:
    for secret in bar:
        encrypt(secret)
```

### Logging

Use structured logging:
```python
import logging

logger = logging.getLogger(__name__)

# Different levels for different severity
logger.debug("Fetching user projects")  # Detailed info
logger.info("User logged in successfully")  # General info
logger.warning("API rate limit approaching")  # Warning
logger.error("Failed to decrypt secret")  # Error
logger.critical("Database connection lost")  # Critical issue
```

Include context in log messages:
```python
# Good
logger.info(f"User {user.email} created project '{project.name}'")

# Avoid
logger.info("Project created")  # No context
```

---


## General Best Practices (All Languages)

### Security
- Never log sensitive data (passwords, tokens, secrets)
- Validate all user input
- Use secure random generators
- Clear sensitive data from memory when done

### Performance
- Don't optimize prematurely
- Profile before optimizing
- Cache expensive operations
- Use async I/O for network calls

### Dependencies
- Minimize dependencies
- Keep dependencies updated
- Pin versions in production
- Review security advisories

### Git Commits
- Atomic commits (one logical change)
- Present tense ("Add feature" not "Added feature")
- Imperative mood ("Fix bug" not "Fixes bug")
- Reference issues when applicable

---

## Resources

### Python
- [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- [Black Documentation](https://black.readthedocs.io/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)

**Consistency is key. When in doubt, follow the existing code style in the project.**