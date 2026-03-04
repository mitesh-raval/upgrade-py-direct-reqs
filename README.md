# upgrade-py-direct-reqs

**Upgrade only direct dependencies listed in `requirements.txt` safely.**

A Python CLI tool that lets you review and upgrade **only direct dependencies** in a project’s `requirements.txt` or `pyproject.toml`, while keeping your pinned versions up to date.

Developed by coding agents with guidance from Miteshkumar N Raval.
---

## Features

- Lists outdated direct dependencies.
- `plan` command provides deterministic, zero-mutation upgrade planning.
- Supports both `requirements.txt` and `pyproject.toml` (with `[project.dependencies]`).
- `upgrade` command applies upgrades with optional package selection.
- Cross-platform: works on Linux, macOS, and Windows.
- CLI installable via pip in a virtual environment or globally.

---

## Installation

```bash
# Recommended: install inside your existing project virtual environment
source myenv/bin/activate  # or myenv\Scripts\activate on Windows
pip install upgrade-py-direct-reqs

# Optional: install the CLI globally with pipx
pipx install upgrade-py-direct-reqs
```

> **Important:** Even when installed via `pipx`, activate your project's virtual
> environment before running `upgrade-py-direct-reqs` so upgrades are applied to
> the correct environment.

---

## Usage

```bash
# Plan updates (default command, no file mutation)
upgrade-py-direct-reqs plan requirements.txt

# Plan with machine-readable output for CI/agents
upgrade-py-direct-reqs plan requirements.txt --json --diff

# Upgrade specific packages only
upgrade-py-direct-reqs upgrade requirements.txt requests fastapi --yes

# Allow major bumps explicitly
upgrade-py-direct-reqs upgrade pyproject.toml --allow-major --yes

# Show tool version
upgrade-py-direct-reqs --version
```

- `plan` is safe by default and never mutates files.
- `upgrade` performs installation and rewrites direct dependency entries.
- Package names are normalized for matching (`requests`, `Requests`, `requests>=...`).

---

## Example

### Before

`requirements.txt`:
```txt
requests==2.30.0
flask==2.2.5
```

### Command
```bash
upgrade-py-direct-reqs requirements.txt
```

### Output (sample)
```
📦 Outdated direct dependencies:

  requests: 2.30.0 → 2.32.3
  flask: 2.2.5 → 3.0.3

⚠️  Please review package revisions listed above before upgrading.
   Check release notes on pypi.org for BREAKING changes or necessary code updates.

Proceed with upgrade? (y/n): y
⬆️  Upgrading 2 packages...
✅ Requirements updated: requirements.txt
```

### After

`requirements.txt`:
```txt
requests==2.32.3
flask==3.0.3
```

---

## Test instructions

### To run CLI tests with pytest:
```bash
pip install .[dev]
pytest tests/test_cli.py
```

Current automated coverage in `tests/test_cli.py` includes:
- invalid TOML filename validation (`pyproject.toml` naming rule)
- normalized package-name matching behavior in plan mode
- upgrade path behavior when dependencies are not installed
- plan `--json` behavior in missing-installation guard paths

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
