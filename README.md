# n0conflict

> AI-powered Git merge conflict resolver.

[![CI](https://github.com/yourusername/n0conflict/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/n0conflict/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/n0conflict)](https://pypi.org/project/n0conflict/)
[![Python](https://img.shields.io/pypi/pyversions/n0conflict)](https://pypi.org/project/n0conflict/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

`n0conflict` resolves Git merge conflicts using AI. Instead of forcing one side over the other, it reads both versions of the conflicting code and produces a single output that preserves the intent of each. When a conflict truly cannot be resolved automatically, it tells you why.

---

## Features

- **Intelligent merging** — understands the intent of both sides, not just the text
- **Honest failures** — explains clearly when a conflict cannot be auto-resolved
- **Multi-language aware** — detects Python, TypeScript, Go, Rust, and [more](n0conflict/git.py)
- **Three commands** — `resolve`, `scan`, and `explain`
- **Safe by default** — never writes to disk unless you pass `--write`

---

## Installation

```bash
pip install n0conflict
```

Requires Python 3.10+.

---

## Configuration

`n0conflict` uses the Anthropic API. Set your key in the environment before running:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Alternatively, use `N0CONFLICT_API_KEY` if you prefer to keep it separate.

---

## Usage

### Resolve conflicts in a file

```bash
# Preview what the resolved file would look like
n0conflict resolve src/app.py --dry-run

# Write the resolved file in place
n0conflict resolve src/app.py --write
```

### Scan a repository for conflicted files

```bash
n0conflict scan
n0conflict scan /path/to/repo
```

### Inspect conflicts without resolving

```bash
n0conflict explain src/app.py
```

### Other

```bash
n0conflict --version
n0conflict --help
```

---

## Example

```
$ n0conflict resolve app.py --write

n0conflict — app.py
  Found 2 conflict block(s)

  ✓ Conflict 1: Conflict resolved successfully.
  ✓ Conflict 2: Conflict resolved successfully.

✓ Written to app.py
```

When a conflict cannot be resolved:

```
  ✗ Conflict 1: cannot be resolved automatically

  ╭─ Why it can't be resolved ────────────────────────────────────────────────╮
  │ Both sides remove the authentication middleware but replace it with        │
  │ incompatible implementations — one using JWT, the other using sessions.    │
  │ Keeping both would cause duplicate request handling.                       │
  ╰───────────────────────────────────────────────────────────────────────────╯
```

---

## Contributing

Contributions are welcome. Please open an issue before submitting a pull request for large changes.

```bash
git clone https://github.com/yourusername/n0conflict
cd n0conflict
pip install -e ".[dev]"
pytest
```

---

## License

MIT
