# SecretsCLI
> Secure, simple secrets management for developers

Stop sharing `.env` files over Slack.

[![PyPI version](https://badge.fury.io/py/secretscli-py.svg)](https://badge.fury.io/py/secretscli-py)
[![Python Version](https://img.shields.io/pypi/pyversions/secretscli-py.svg)](https://pypi.org/project/secretscli-py/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## The Problem

We've all been there:
- "Hey, can you send me the database credentials?"
- "Which `.env` file is the latest one?"
- "I just set up a new laptop and now I need to ask everyone for secrets again"

Sharing secrets through Slack, email, or sticky notes is a mess. It's insecure, hard to track, and honestly just annoying.

## What SecretsCLI Does

It's simple: **one command to pull all your secrets, anywhere.**

```bash
pip install secretscli-py
secretscli login
secretscli project use my-app
secretscli secrets pull
```

That's it. Your `.env` file is ready. No asking around. No digging through old messages.

---

## How It Works

1. **You store secrets once** - encrypted, in the cloud
2. **Your team pulls them anywhere** - new laptop, CI/CD, staging server
3. **Server never sees plaintext** - zero-knowledge encryption

No more "which version is correct?" - there's one source of truth.

---

## Getting Started

### First Time Setup

New to SecretsCLI? Here's how to get started:

```bash
pip install secretscli-py

# Create your account
secretscli init

# Create a project for your app
secretscli project create my-app

# Add your secrets
secretscli secrets set DATABASE_URL=postgresql://... API_KEY=sk_live_...

# Or if you already have a .env file, just push it
secretscli secrets push
```

### Setting Up a New Machine

Already have an account? Just pull your secrets:

```bash
pip install secretscli-py
secretscli login

# Connect to your project
secretscli project use my-app

# Pull all secrets
secretscli secrets pull
# Done - your .env is ready
```

### Creating a Project in a Specific Workspace

Want to create a project in a team workspace instead of your personal one?

```bash
# See all your workspaces
secretscli workspace list

# Switch to the workspace you want
secretscli workspace switch "Backend Team"

# Now create your project - it goes into the selected workspace
secretscli project create api-service
```

### Team Collaboration

Got a team? Here's how to share secrets securely:

```bash
# Create a team workspace
secretscli workspace create "Backend Team"

# Invite your teammates
secretscli workspace invite alice@company.com
secretscli workspace invite bob@company.com

# Create a shared project
secretscli project create shared-api

# Your teammates just need to:
pip install secretscli-py
secretscli login
secretscli project use shared-api
secretscli secrets pull
# They now have all the secrets
```

Everyone in the workspace gets the same secrets. When you update something, they get it on their next pull.

---

## Security (the boring-but-important part)

- **Zero-knowledge** - API never sees your plaintext secrets
- **End-to-end encryption** - X25519 + Fernet (industry standard)
- **Your keys, your control** - stored in your system keychain

We can't read your secrets even if we wanted to.

---

## Full Documentation

- **[Command Reference](docs/COMMANDS.md)** - Every command explained
- **[Developer Guide](docs/DEVELOPMENT.md)** - Contributing, testing, architecture

---

## Other Languages

This is the Python implementation, but SecretsCLI can be built in any language - Go, Rust, JavaScript, whatever you prefer.

If you want to create an implementation in another language:
1. [Open an issue](https://github.com/The-17/SecretsCLI/issues/new?title=New%20Language%20Implementation:%20[Language]&body=I%27d%20like%20to%20implement%20SecretsCLI%20in%20[Language]) with the title "New Language Implementation: [Language]"
2. We'll create an official repository under our org
3. You build it, we help maintain it

This keeps all implementations organized and gives contributors proper credit.

---

## Requirements

- Python 3.9+
- Internet connection

---

## Contributing

Found a bug? Got an idea? PRs are welcome.

Check out [CONTRIBUTING.md](CONTRIBUTING.md) to get started.

---

## Links

- [GitHub](https://github.com/The-17/SecretsCLI)
- [PyPI](https://pypi.org/project/secretscli-py/)
- [Report an Issue](https://github.com/The-17/SecretsCLI/issues)

---

If this saves you time, consider giving it a star. It helps others find it.

MIT License
