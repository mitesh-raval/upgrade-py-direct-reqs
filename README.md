# upgrade-py-direct-reqs

**Upgrade only direct dependencies listed in `requirements.txt` safely.**

A Python CLI tool that lets you review and upgrade **only direct dependencies** in a project’s `requirements.txt` or `pyproject.toml`, while keeping your pinned versions up to date.

Developed by Miteshkumar N Raval with guidance and scripting assistance from coding agents.
---

## Features

- Lists outdated direct dependencies.
- Prompts for confirmation before upgrading.
- Supports both `requirements.txt` and `pyproject.toml` (with `[project.dependencies]`).
- Updates `requirements.txt` with new pinned versions.
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
# Explicitly specify your requirements file
upgrade-py-direct-reqs requirements.txt

# Or specify your pyproject.toml
upgrade-py-direct-reqs pyproject.toml
```

- The CLI lists outdated direct dependencies.
- Review versions and confirm before upgrading.
- After upgrade, the `requirements.txt` file is updated with pinned versions.

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
``` 
 1. pip install .[dev]  (to install dev deps listed in pyproject.toml)
 2. Ensure pytest is installed in your environment: pip install pytest
 3. Run tests from the project root:
       pytest tests/test_cli.py
 4. Tests cover:
       - requirements.txt only
       - pyproject.toml only
       - conflicting dependencies in both files
       - empty requirements.txt
       - invalid toml file name (refer PEP 621 for more details)
```

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
