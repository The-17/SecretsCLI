# Contributing to SecretsCLI

Thank you for your interest in contributing to SecretsCLI! We welcome contributions from everyone.

## Ways to Contribute

### 1. Report Bugs
Found a bug? Please create an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version, SecretsCLI version)

### 2. Suggest Features
Have an idea? Open an issue with:
- Feature description
- Use case explanation
- Proposed implementation (optional)

### 3. Improve Documentation
- Fix typos or unclear explanations
- Add examples
- Translate documentation

### 4. Submit Code
- Fix bugs
- Implement new features
- Optimize performance
- Add tests

### 5. Create Language Implementations
Implement SecretsCLI in your favorite language! See the "Creating a New Implementation" section below.

## Getting Started

### Prerequisites
- Python 3.9 or higher
- Git
- pip

### Development Setup

1. **Fork and Clone**
```bash
   git clone https://github.com/The-17/secretscli.git
   cd secretscli
```

2. **Create Virtual Environment**
```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Dependencies**
```bash
   pip install -e ".[dev]"
```

4. **Run Tests**
```bash
   pytest
```

### Project Structure
```
secretscli/
├── secretscli/              # Main package
│   ├── __init__.py
│   ├── cli.py              # CLI entry point
│   ├── auth.py             # Authentication
│   ├── api_client.py       # API communication
│   ├── encryption.py       # Encryption logic
│   ├── config.py           # Configuration
│   └── utils.py            # Utilities
├── tests/                   # Test suite
│   ├── test_auth.py
│   ├── test_encryption.py
│   └── test_cli.py
├── docs/                    # Documentation
├── setup.py                 # Package setup
└── README.md
```

## Development Workflow

### 1. Create a Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions/changes

### 2. Make Changes
- Write clean, readable code
- Follow the style guide (see [STYLE_GUIDE.md](docs/STYLE_GUIDE.md))
- Add tests for new functionality
- Update documentation as needed

### 3. Test Your Changes
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=secretscli

# Run linting
flake8 secretscli/
black --check secretscli/
```

### 4. Commit Your Changes
Write clear, descriptive commit messages:
```bash
git commit -m "Add feature: bulk secret import"
```

Good commit message format:
```
<type>: <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Example:
```
feat: add multi-environment support

Allow users to specify environment when pulling secrets.
Adds --env flag to pull command.

Closes #123
```

### 5. Push and Create Pull Request
```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear title and description
- Reference to related issues
- Screenshots (if UI changes)
- Checklist of changes

## Pull Request Checklist

Before submitting, ensure:

- [ ] Code follows the style guide
- [ ] All tests pass
- [ ] New code has tests
- [ ] Documentation is updated
- [ ] Commit messages are clear
- [ ] Branch is up to date with main
- [ ] No merge conflicts

## Testing Guidelines

### Writing Tests
- Test file names: `test_*.py`
- Test function names: `test_*`
- Use descriptive names: `test_login_with_invalid_credentials`
- Mock external API calls
- Test edge cases and error conditions

### Test Coverage
- Aim for 80%+ coverage
- Critical paths should have 100% coverage
- Test both success and failure scenarios

## Documentation Guidelines

### Code Documentation
- Use docstrings for all functions and classes
- Follow Google or NumPy docstring format
- Include parameter types and return values
- Add usage examples for complex functions

### User Documentation
- Write for beginners
- Include examples
- Keep it concise
- Update docs with code changes

## Code Style

See [STYLE_GUIDE.md](docs/STYLE_GUIDE.md) for detailed style guidelines.

Quick reference:
- Use Black for formatting (88 character line length)
- Follow PEP 8
- Use type hints where beneficial
- Meaningful variable names
- Keep functions focused and small

## Creating a New Language Implementation

Want to implement SecretsCLI in another language? Great! Here's what you need to know:

### Requirements
Your implementation must:
1. **Communicate with the API** - Use the same REST endpoints
2. **Handle authentication** - Support email/password login and JWT tokens
3. **Encrypt secrets locally** - Before sending to API
4. **Store credentials securely** - Use system keychain or equivalent
5. **Provide the same commands** - Similar CLI interface

### You Can Choose:
- **Any encryption algorithm** - Fernet, AES-GCM, ChaCha20, etc.
- **Any CLI framework** - Click, Cobra, Clap, Commander, etc.
- **Your own architecture** - As long as it meets the API contract

### Steps to Create an Implementation

1. **Read the Architecture docs** - Understand how SecretsCLI works
   - [ARCHITECTURE.md](docs/ARCHITECTURE.md)
   - [docs/ENCRYPTION.md](docs/ENCRYPTION.md)

2. **Review the API documentation** - Available at the API docs URL

3. **Implement core features**:
   - User registration and login
   - Master key generation and storage
   - Secret encryption/decryption
   - Project management
   - Secret CRUD operations

4. **Follow naming conventions**:
   - Repository: `secretscli-{language}` (e.g., `secretscli-go`)
   - Package name: `secretscli`
   - Commands: Same as Python implementation

5. **Document your implementation**:
   - Installation instructions
   - Platform-specific notes
   - Differences from Python version (if any)

6. **Submit to the community**:
   - Let us know via GitHub issue
   - We'll add it to the official list
   - Consider cross-linking in READMEs

### Implementation Checklist
- [ ] Authentication (register, login, logout)
- [ ] Master key management
- [ ] Local encryption
- [ ] Secure credential storage
- [ ] Project commands
- [ ] Secret commands (set, get, list, delete)
- [ ] Pull command
- [ ] .env file generation
- [ ] Error handling
- [ ] Tests
- [ ] Documentation

### Getting Help
- Join discussions in GitHub Issues
- Ask questions with `[lang-impl]` tag
- Check existing implementations for reference

## Reporting Security Issues

**Do not open public issues for security vulnerabilities.**

Instead, email security@secretscli.com with:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (optional)

We'll respond within 48 hours.

## Code of Conduct

### Our Standards
- Be respectful and inclusive
- Welcome newcomers
- Accept constructive criticism
- Focus on what's best for the community

### Unacceptable Behavior
- Harassment or discriminatory language
- Trolling or insulting comments
- Publishing others' private information
- Unprofessional conduct

### Enforcement
Violations may result in:
- Warning
- Temporary ban
- Permanent ban

Report issues to conduct@secretscli.com

## Recognition

Contributors are recognized in:
- Release notes
- CONTRIBUTORS.md file
- Project README

Thank you for making SecretsCLI better!

## Questions?

- GitHub Discussions
- Email: contribute@secretscli.com
- Twitter: @secretscli

---

**Happy Contributing!**