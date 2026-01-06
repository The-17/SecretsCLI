# Contributing to SecretsCLI

Thanks for your interest in contributing! Here's how you can help.

---

## Ways to Contribute

**Report Bugs** - Open an issue with steps to reproduce

**Suggest Features** - Open an issue with your idea

**Improve Documentation** - Fix typos, add examples, clarify things

**Submit Code** - Fix bugs, add features, write tests

**Create Language Implementations** - See the section below

---

## Development Setup

```bash
# Clone and install
git clone https://github.com/The-17/SecretsCLI.git
cd SecretsCLI
poetry install --with dev

# Run tests
poetry run pytest tests/ -v

# Format code
poetry run black secretscli/ tests/
```

---

## Making Changes

1. Create a branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Run tests: `poetry run pytest`
4. Commit: `git commit -m "Add feature: description"`
5. Push and create a Pull Request

---

## Pull Request Checklist

- [ ] Tests pass
- [ ] Code is formatted (`black`)
- [ ] New code has tests
- [ ] Documentation updated if needed

---

## Creating a Language Implementation

Want to build SecretsCLI in Go, Rust, JavaScript, or another language?

**Process:**
1. [Open an issue](https://github.com/The-17/SecretsCLI/issues/new?title=New%20Language%20Implementation:%20[Language]) with title "New Language Implementation: [Language]"
2. We'll create an official repository under our org
3. You build it, we help maintain it

**Your implementation must:**
- Use the same API endpoints
- Support email/password auth with JWT tokens
- Encrypt secrets locally before sending to API
- Use **X25519 + NaCl SealedBox** for asymmetric encryption (keypairs) - this is mandatory for compatibility
- Use compatible symmetric encryption (Fernet recommended, AES-GCM also works)

See [CRYPTO_STANDARD.md](./CRYPTO_STANDARD.md) for full crypto requirements.

---

## Security Issues

For security vulnerabilities, please **do not** open a public issue. Instead, open a private security advisory on GitHub or contact us directly.

---

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Accept constructive criticism
- Focus on what's best for the community

---

Thanks for making SecretsCLI better!