# SecretsCLI
> Secure, simple secrets management for developers across all environments.

SecretsCLI is a command-line tool that makes managing environment variables and secrets effortless. Install once, login anywhere, and access your secrets instantly - no file sharing, no copy-pasting, no security risks.

[![PyPI version](https://badge.fury.io/py/secretscli.svg)](https://badge.fury.io/py/secretscli)
[![Python Version](https://img.shields.io/pypi/pyversions/secretscli.svg)](https://pypi.org/project/secretscli/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://github.com/The-17/secretscli/tree/main/docs)

## Why SecretsCLI?

**The Problem:**
- Sharing `.env` files via Slack/email is insecure
- Setting up new machines means manually copying secrets
- Team members need constant access to updated credentials
- Rotating secrets requires notifying everyone

**The Solution:**
SecretsCLI provides encrypted, centralized secret storage with instant access from any machine.

## Quick Start

### Installation
```bash
pip install secretscli
```

### First Time Setup
```bash
# Create an account
secretscli init

# Create your first project
secretscli project create my-app

# Add secrets (multiple at once)
secretscli secrets set DATABASE_URL=postgresql://... API_KEY=sk_live_... STRIPE_SECRET=sk_test_...

# Or add one at a time
secretscli secrets set DATABASE_URL=postgresql://...

# If you already have a .env file, push them to the cloud
secretscli secrets push
```

### On a New Machine
```bash
# Install and login
pip install secretscli
secretscli login

# Connect to your project
secretscli project use my-app

# Pull your secrets
secretscli secrets pull

# That's it! Your .env file is ready
```

## Key Features

### **End-to-End Encryption**
- Zero-knowledge architecture - API never sees your plaintext secrets
- Each user has unique encryption keys

### **Cross-Device Access**
- Login from any machine, all you have to do is install the package
- Instant access to all your secrets
- No manual file transfers

### **Project Organization**
- Group secrets by project
- Clean namespace management

### **Developer Experience**
- Simple, intuitive commands
- Automatic `.env` and `.env.example` files generation
- Works with any framework or language


## Core Concepts

### Projects
Projects are containers that organize related secrets. Think of them as folders for your environment variables.

Example projects:
- `my-web-app-prod` - Production secrets
- `my-web-app-staging` - Staging secrets
- `mobile-app` - Mobile application secrets

### Secrets
Secrets are encrypted key-value pairs (environment variables) stored within projects.

Examples:
- `DATABASE_URL=postgresql://...`
- `API_KEY=sk_live_...`
- `STRIPE_SECRET=sk_test_...`


## Command Reference

### Account Management
- `secretscli init` - Create a new account or setup existing
- `secretscli login` - Login to your account
- `secretscli guide` - Interactive quick-start guide

### Project Management
- `secretscli project create <name> [-d "description"]` - Create a new project
- `secretscli project list` - List all projects
- `secretscli project use <name>` - Set active project for current directory
- `secretscli project update <name> [-n new-name] [-d "desc"]` - Update project
- `secretscli project delete <name> [-f]` - Delete a project

### Secret Management
- `secretscli secrets set KEY=value [KEY2=value2...]` - Create or update secrets
- `secretscli secrets get <KEY>` - Get a single secret value
- `secretscli secrets list [-v]` - List all secret keys (use -v to show values)
- `secretscli secrets delete <KEY>` - Delete a secret
- `secretscli secrets pull` - Download all secrets to .env
- `secretscli secrets push` - Upload .env secrets to cloud

For detailed command documentation, see [COMMANDS.md](docs/COMMANDS.md).


## Multi-Language Implementations

SecretsCLI is designed to support implementations in any programming language:

### Official Implementation
- **Python** - This repository

### Community Implementations - Feel free to implement any of this!
- **Go** - Coming soon
- **Rust** - Coming soon
- **JavaScript/Node** - Coming soon
- **Java** - Coming soon

Want to create an implementation in your language? Check out [CONTRIBUTING.md](CONTRIBUTING.md)!

## Contributing

We welcome contributions! Whether you're:
- Fixing bugs
- Adding features
- Improving documentation
- Creating implementations in other languages

Please read our [CONTRIBUTING.md](CONTRIBUTING.md) guide.


## Requirements

- Python 3.9 or higher
- pip
- Internet connection for API access


## License

SecretsCLI is open-source software licensed under the [MIT License](LICENSE).


## Links

- **Documentation**: [docs/](docs/)
- **API Documentation**: [API documentation](secrets-api-orpin.vercel.app)
- **GitHub**: [https://github.com/The-17/secretscli](https://github.com/The-17/secretscli)
- **PyPI**: [https://pypi.org/project/secretscli/](https://pypi.org/project/secretscli/)
- **Issues**: [https://github.com/The-17/secretscli/issues](https://github.com/The-17/secretscli/issues)

## Support

- [Documentation](docs/)
- [Report a Bug](https://github.com/The-17/secretscli/issues)
- [Request a Feature](https://github.com/The-17/secretscli/issues)

## Show Your Support

If SecretsCLI helps you manage secrets better, please give it a star on GitHub!
