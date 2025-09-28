# upgrade-py-direct-reqs

**Upgrade only direct dependencies listed in `requirements.txt` safely.**

A Python CLI tool that lets you review and upgrade **only direct dependencies** in a project’s `requirements.txt` (or `pyproject.toml` in future versions), while keeping your pinned versions up to date.

Developed by Miteshkumar N Raval with guidance and scripting assistance from OpenAI ChatGPT.

---

## Features

- Lists outdated direct dependencies.
- Prompts for confirmation before upgrading.
- Updates `requirements.txt` with new pinned versions.
- Cross-platform: works on Linux, macOS, and Windows.
- CLI installable via [pipx](https://pypa.github.io/pipx/).

---

## Installation

```bash
# Recommended: install globally using pipx
pipx install upgrade-py-direct-reqs
```

Or via pip in a venv:

```bash
pip install upgrade-py-direct-reqs
```

---

## Usage

```bash
# Explicitly specify your requirements file
upgrade-py-direct-reqs path/to/requirements.txt
```

- The CLI will list outdated direct dependencies.
- You can review versions and confirm before upgrading.
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

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
