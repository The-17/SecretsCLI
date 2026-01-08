# SecretsCLI Command Reference

Complete reference for all SecretsCLI commands.

---

## Account Commands

### `secretscli init`
Create a new account or setup an existing one interactively.

```bash
secretscli init
```

Prompts for email and password. Creates encryption keys stored securely in your system keychain.

---

### `secretscli login`
Login to an existing account.

```bash
secretscli login
```

Prompts for email and password. Retrieves your encryption keys and workspace access.


### `secretscli guide`
Interactive quick-start guide for users.

```bash
secretscli guide
```

---

## Project Commands

### `secretscli project create`
Create a new project in the currently selected workspace.

```bash
secretscli project create <name> [-d "description"]
```

**Options:**
- `-d, --description` - Optional project description

**Examples:**
```bash
secretscli project create my-api
secretscli project create my-api -d "Backend API for mobile app"
```

---

### `secretscli project list`
List all projects you have access to, grouped by workspace.

```bash
secretscli project list
```

Shows project name, description, and workspace.

---

### `secretscli project use`
Set the active project for the current directory. Creates `.secretscli/project.json`.

```bash
secretscli project use <name>
```

**Example:**
```bash
cd /path/to/my-project
secretscli project use my-api
```

---

### `secretscli project update`
Update project name or description.

```bash
secretscli project update <current-name> [-n new-name] [-d "new description"]
```

**Options:**
- `-n, --name` - New project name
- `-d, --description` - New description

---

### `secretscli project delete`
Delete a project and all its secrets.

```bash
secretscli project delete <name> [-f]
```

**Options:**
- `-f, --force` - Skip confirmation prompt

⚠️ **Warning:** This permanently deletes all secrets in the project.

---

### `secretscli project invite`
Invite a user to collaborate on the current project.

```bash
secretscli project invite <email> [--role member]
```

**Options:**
- `-r, --role` - Role for the invitee: `admin`, `member`, `read_only` (default: `member`)

**Behavior:**
- **Personal workspace** → Creates a new shared workspace, migrates the project, re-encrypts secrets
- **Already shared** → Adds the user to the existing workspace

The invited user receives access to the project's workspace and all its secrets.

---

## Secret Commands

### `secretscli secrets set`
Add or update one or more secrets.

```bash
secretscli secrets set KEY=value [KEY2=value2 ...]
```

**Examples:**
```bash
# Single secret
secretscli secrets set DATABASE_URL=postgresql://localhost:5432/mydb

# Multiple secrets
secretscli secrets set API_KEY=sk_live_123 STRIPE_SECRET=sk_test_456

# With spaces (use quotes)
secretscli secrets set MESSAGE="Hello World"
```

Secrets are encrypted before sending to the server and saved to `.env`.

---

### `secretscli secrets get`
Retrieve and decrypt a single secret.

```bash
secretscli secrets get <KEY>
```

**Example:**
```bash
secretscli secrets get DATABASE_URL
# Output: postgresql://localhost:5432/mydb
```

---

### `secretscli secrets list`
List all secret keys in the current project.

```bash
secretscli secrets list [-v]
```

**Options:**
- `-v, --value` - Also show decrypted values

---

### `secretscli secrets delete`
Delete a secret from the project.

```bash
secretscli secrets delete <KEY> [-f]
```

**Options:**
- `-f, --force` - Skip confirmation prompt

---

### `secretscli secrets pull`
Download all secrets from the cloud and write to `.env`.

```bash
secretscli secrets pull
```

Overwrites the local `.env` file with cloud secrets.

---

### `secretscli secrets push`
Upload all secrets from `.env` to the cloud.

```bash
secretscli secrets push
```

Reads local `.env` file, encrypts each secret, and uploads to server.

---

## Workspace Commands

### `secretscli workspace list`
List all workspaces you have access to.

```bash
secretscli workspace list
```

Shows:
- Workspace name and type (personal/team)
- Your role (owner/member)
- `(Selected)` - Default for new projects
- `(Current Project)` - Workspace of active project

---

### `secretscli workspace switch`
Change the default workspace for creating new projects.

```bash
secretscli workspace switch <name>
```

**Special keywords:**
- `personal` - Switch to your personal workspace

**Example:**
```bash
secretscli workspace switch "Backend Team"
secretscli workspace switch personal
```

> **Note:** This only affects NEW projects. Existing projects remain in their workspace.

---

### `secretscli workspace create`
Create a new team workspace.

```bash
secretscli workspace create <name>
```

Creates a new workspace with you as owner. Invite team members with `workspace invite`.

---

### `secretscli workspace invite`
Invite a user to the currently selected workspace.

```bash
secretscli workspace invite <email> [--role member]
```

**Options:**
- `-r, --role` - Role for the invitee: `admin`, `member`, `read_only` (default: `member`)

The invited user receives an encrypted copy of the workspace key that only they can decrypt.

**Requirements:**
- Must have a workspace selected (`workspace switch` first)
- User must have a SecretsCLI account

> **Note:** Uses the *selected* workspace, not the project workspace. Use `project invite` to invite to a project's workspace.

---

### `secretscli workspace members`
List all members of the currently selected workspace.

```bash
secretscli workspace members
```

Shows member email, role (owner/admin/member), and status.

> **Note:** Uses the *selected* workspace. Use `workspace switch` to change which workspace to view.

---

### `secretscli workspace remove`
Remove a member from the currently selected workspace.

```bash
secretscli workspace remove <email>
```

Revokes their access to all secrets in the workspace.

> **Note:** Uses the *selected* workspace. Use `workspace switch` first to select which workspace to modify.

---

## Configuration Files

### Global Config: `~/.secretscli/`

| File | Purpose |
|------|---------|
| `config.json` | Workspace cache, selected workspace |
| `token.json` | JWT access/refresh tokens |
| Keychain | Private/public keys (system secure storage) |

### Project Config: `.secretscli/`

| File | Purpose |
|------|---------|
| `project.json` | Project ID, workspace binding, environment |

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (authentication, API, or validation) |
| 2 | Missing arguments (Typer/CLI) |

---

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `SECRETSCLI_API_URL` | Override API endpoint (for self-hosted) |
