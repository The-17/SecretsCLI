# SecretsCLI Architecture

How SecretsCLI is structured - for contributors who want to understand the codebase.

---

## Directory Structure

```
secretscli/
├── cli.py               # Main entry point, top-level commands
├── config.py            # Configuration paths & schemas
├── auth.py              # Login/signup helpers
├── encryption.py        # Symmetric + Asymmetric encryption
├── prompts.py           # Questionary prompts & styling
│
├── api/
│   └── client.py        # API client for server communication
│
├── commands/
│   ├── project.py       # Project management commands
│   ├── secrets.py       # Secret management commands
│   └── workspace.py     # Workspace & team management
│
└── utils/
    ├── credentials.py   # Token, key, and config storage
    ├── decorators.py    # @require_auth decorator
    ├── env_manager.py   # .env file read/write
    └── utils.py         # Misc helpers
```

---

## How Commands Flow

1. User runs a command (e.g., `secretscli secrets set`)
2. `cli.py` routes to the appropriate command file
3. `@require_auth` decorator checks/refreshes tokens
4. Command uses `CredentialsManager` for config, `EncryptionService` for crypto
5. `api_client` sends requests to the server
6. Results saved locally (`.env`, `project.json`, etc.)

---

## Encryption Model

SecretsCLI uses zero-knowledge encryption. The server never sees plaintext secrets.

### Key Types

**User Key** - Derived from password using PBKDF2 (100k iterations). Never stored.

**Private Key** - X25519 key for decrypting workspace keys. Stored in OS keychain.

**Public Key** - Others use this to encrypt workspace keys for you. Stored on API.

**Workspace Key** - Fernet key for encrypting/decrypting secrets. Each workspace has one.

### Flow

Password → User Key → decrypts Private Key → decrypts Workspace Key → decrypts Secrets

---

## Data Flows

### Registration

1. Generate X25519 keypair
2. Derive user_key from password (PBKDF2)
3. Encrypt private_key with user_key
4. Send to API: `{email, password, public_key, encrypted_private_key, salt}`
5. Store private_key in OS keychain

### Login

1. API returns: `{tokens, encrypted_private_key, salt, workspaces}`
2. Derive user_key from password
3. Decrypt private_key
4. For each workspace: decrypt its workspace_key
5. Cache everything locally

### Setting a Secret

1. Get workspace_id from project config
2. Fetch workspace_key from global config cache
3. Encrypt value with workspace_key (Fernet)
4. Send to API: `{project_id, key, encrypted_value}`
5. Write plaintext to local `.env`

### Inviting a Team Member (Project Invite)

**From Personal Workspace:**
1. Generate new workspace key
2. Re-encrypt all secrets with new key
3. Encrypt workspace key for owner + invitee (NaCl SealedBox)
4. API creates shared workspace, migrates project, updates secrets
5. CLI updates local project.json with new workspace info

**From Shared Workspace:**
1. Fetch existing workspace key from global cache
2. Encrypt workspace key for invitee (NaCl SealedBox)
3. API adds invitee as member
4. When they login, they decrypt it with their private_key

---

## Module Responsibilities

**cli.py** - Entry point, registers commands

**auth.py** - Login/signup flows

**encryption.py** - Symmetric (Fernet) + Asymmetric (NaCl) crypto

**api/client.py** - HTTP requests with auth headers

**utils/credentials.py** - Tokens, keys, workspace config storage

**utils/decorators.py** - `@require_auth` with auto token refresh

**utils/env_manager.py** - Parse and write .env files

**commands/project.py** - Project CRUD

**commands/secrets.py** - Secrets CRUD + pull/push

**commands/workspace.py** - Workspace & member management

---

## Adding a New Command

1. Choose the right file based on what it does
2. Add the auth decorator if it needs login:
   ```python
   from ..utils.decorators import require_auth
   
   @app.command()
   @require_auth
   def my_command():
       pass
   ```

3. Access workspace key if needed:
   ```python
   from ..utils.credentials import CredentialsManager
   # workspace_key is fetched from global config via workspace_id
   workspace_key = CredentialsManager.get_project_workspace_key()
   ```

---

## Related Docs

- [CRYPTO_STANDARD.md](./CRYPTO_STANDARD.md) - Crypto algorithms for cross-language compatibility
- [DEVELOPMENT.md](./DEVELOPMENT.md) - Testing and contributing
