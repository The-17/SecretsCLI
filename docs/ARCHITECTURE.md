# SecretsCLI Architecture

This document explains how SecretsCLI is structured to help contributors understand the codebase quickly.

---

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                           USER                                       │
│                    (runs CLI commands)                               │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         cli.py                                       │
│                   (Main Entry Point)                                 │
│                                                                      │
│  • init, login, guide commands                                       │
│  • Registers subcommand groups (project, secrets, workspace)         │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ project.py    │   │ secrets.py    │   │ workspace.py  │
│               │   │               │   │               │
│ create, list  │   │ set, get      │   │ create, list  │
│ use, delete   │   │ pull, push    │   │ invite, switch│
└───────┬───────┘   └───────┬───────┘   └───────┬───────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         ▼                  ▼                  ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  api/client  │   │  encryption  │   │  env_manager │
│              │   │              │   │              │
│ Talks to API │   │ Symmetric +  │   │ Read/write   │
│ server       │   │ Asymmetric   │   │ .env files   │
└──────────────┘   └──────────────┘   └──────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     SecretsCLI API Server                            │
│                  (Stores encrypted secrets)                          │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
secretscli/
├── __init__.py          # Package initialization
├── cli.py               # 🚀 MAIN: Typer app, top-level commands
├── config.py            # Configuration paths & schemas
├── auth.py              # Authentication (login, signup helpers)
├── encryption.py        # 🔐 Symmetric + Asymmetric encryption
├── prompts.py           # Questionary prompts & styling
│
├── api/
│   └── client.py        # 🌐 API client for server communication
│
├── commands/
│   ├── __init__.py      # Exports app instances
│   ├── project.py       # Project management commands
│   ├── secrets.py       # Secret management commands
│   └── workspace.py     # Workspace & team management (NEW)
│
└── utils/
    ├── __init__.py
    ├── credentials.py   # 🔑 Token, key, and config storage
    ├── decorators.py    # @require_auth decorator
    ├── env_manager.py   # 📄 .env file read/write
    └── utils.py         # Misc helper functions
```

---

## Workspace-Based Encryption Model

### How Secrets Are Protected

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ZERO-KNOWLEDGE ARCHITECTURE                       │
│                                                                      │
│  The server NEVER sees:                                              │
│    • Your plaintext secrets                                          │
│    • Your private key                                                │
│    • Your workspace keys                                             │
│                                                                      │
│  The server ONLY stores encrypted blobs.                             │
└─────────────────────────────────────────────────────────────────────┘

Password
    │
    ▼ (PBKDF2)
User Key ──────────────────┐
    │                      │
    │ encrypts             │
    ▼                      │
Private Key ◄──────────────┘
    │
    │ decrypts
    ▼
Workspace Key (per workspace)
    │
    │ encrypts/decrypts
    ▼
Secrets
```

### Key Hierarchy

| Key | Purpose | Stored Where | Encrypted With |
|-----|---------|--------------|----------------|
| User Key | Derived from password | Never stored | — |
| Private Key | Decrypt workspace keys | API + Keychain | User Key |
| Public Key | Others encrypt for you | API (public) | — |
| Workspace Key | Encrypt/decrypt secrets | API (per-member) | Recipient's Public Key |

---

## Data Flows

### 1. Registration

```
CLI                                    API
 │                                      │
 │ 1. Generate keypair (X25519)         │
 │ 2. Derive user_key from password     │
 │ 3. Encrypt private_key with user_key │
 │                                      │
 │ ──POST /register──────────────────►  │
 │   {email, password, public_key,      │
 │    encrypted_private_key, key_salt}  │
 │                                      │
 │ ◄─────────────────────────────────── │
 │   {user, personal_workspace}         │
 │                                      │
 │ 4. Store private_key in OS keychain  │
```

### 2. Login

```
CLI                                    API
 │                                      │
 │ ──POST /login─────────────────────►  │
 │   {email, password}                  │
 │                                      │
 │ ◄─────────────────────────────────── │
 │   {tokens, key_salt,                 │
 │    encrypted_private_key,            │
 │    workspaces: [{                    │
 │      id, name,                       │
 │      encrypted_workspace_key         │
 │    }]}                               │
 │                                      │
 │ 1. Derive user_key from password     │
 │ 2. Decrypt private_key               │
 │ 3. For each workspace:               │
 │    decrypt workspace_key             │
 │ 4. Store keys in keychain/config     │
```

### 3. Setting a Secret

```
User: secretscli secrets set API_KEY=sk_live_123

CLI                                    API
 │                                      │
 │ 1. Get active workspace_key          │
 │ 2. Encrypt: workspace_key(value)     │
 │                                      │
 │ ──POST /secrets────────────────────► │
 │   {project_id, key, encrypted_value} │
 │                                      │
 │ 3. Optionally write plain to .env    │
```

### 4. Inviting a Team Member

```
Alice invites Bob to workspace

CLI (Alice)                            API
 │                                      │
 │ ──GET /users/bob@.../public-key───►  │
 │ ◄─────────────────────────────────── │
 │   {public_key}                       │
 │                                      │
 │ 1. Encrypt workspace_key with        │
 │    Bob's public_key (NaCl SealedBox) │
 │                                      │
 │ ──POST /workspaces/{id}/members───►  │
 │   {email: bob, role: member,         │
 │    encrypted_workspace_key}          │
 │                                      │

Next time Bob logs in, he receives
the encrypted_workspace_key and can
decrypt it with his private key.
```

---

## Module Responsibilities

| Module | Responsibility |
|--------|----------------|
| `cli.py` | Entry point, registers commands |
| `auth.py` | Login/signup flows |
| `encryption.py` | Symmetric (Fernet) + Asymmetric (NaCl) crypto |
| `api/client.py` | HTTP requests with auth |
| `utils/credentials.py` | Tokens, keys, workspace config storage |
| `utils/decorators.py` | `@require_auth` with auto token refresh |
| `utils/env_manager.py` | Parse and write .env files |
| `commands/project.py` | Project CRUD |
| `commands/secrets.py` | Secrets CRUD + pull/push |
| `commands/workspace.py` | Workspace & member management |

---

## Cryptography

See [CRYPTO_STANDARD.md](./CRYPTO_STANDARD.md) for:
- Required algorithms for cross-language compatibility
- Wire formats for registration/login/invite
- Implementation examples in Python, Go, Rust

---

## Adding a New Command

1. **Choose the right file:**
   - Top-level → `cli.py`
   - Project-related → `commands/project.py`
   - Secrets-related → `commands/secrets.py`
   - Workspace-related → `commands/workspace.py`

2. **Use the auth decorator:**
   ```python
   from ..utils.decorators import require_auth
   
   @app.command()
   @require_auth
   def my_command():
       # Auth guaranteed, tokens refreshed if needed
       pass
   ```

3. **Access workspace context:**
   ```python
   from ..utils.credentials import CredentialsManager
   
   workspace_key = CredentialsManager.get_active_workspace_key()
   ```

---

## Questions?

- Open an issue on GitHub
- Check [CRYPTO_STANDARD.md](./CRYPTO_STANDARD.md) for crypto details
- Check [CONTRIBUTING.md](./CONTRIBUTING.md) for contribution guidelines
