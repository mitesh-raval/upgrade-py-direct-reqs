# upgrade-py-direct-reqs

[![CI](https://github.com/mitesh-raval/upgrade-py-direct-reqs/actions/workflows/ci.yml/badge.svg)](https://github.com/mitesh-raval/upgrade-py-direct-reqs/actions/workflows/ci.yml)

**Upgrade only direct dependencies listed in `requirements.txt` safely.**

A Python CLI tool that lets you review and upgrade **only direct dependencies** in a project’s `requirements.txt` or `pyproject.toml`, while keeping your pinned versions up to date.

Developed by coding agents with guidance from Miteshkumar N Raval.

---

## Features

- Lists outdated direct dependencies.
- `plan` command provides deterministic, zero-mutation upgrade planning.
- Supports both `requirements.txt` and `pyproject.toml` (with `[project.dependencies]`).
- `upgrade` command applies upgrades with optional package selection.
- Blocks major upgrades by default unless explicitly allowed.
- Offers machine-readable JSON payloads for CI and agent automation.
- Produces optional unified diff previews before applying changes.
- **Supports private package mirrors by default** (Artifactory, Nexus, Azure Artifacts, internal indexes, etc.) because package resolution is delegated to `pip` and your existing pip configuration.
- Cross-platform: works on Linux, macOS, and Windows.

---

## GitHub Actions support

This repository includes built-in GitHub Actions CI in `.github/workflows/ci.yml`.

### What the workflow does

- Runs on `push`, `pull_request`, and manual `workflow_dispatch`.
- Tests on Python 3.8–3.12.
- Installs the package with dev dependencies (`pip install .[dev]`).
- Executes `pytest tests/test_cli.py`.

If your project uses private mirrors, configure credentials using standard GitHub Actions secrets and `pip` index settings (for example `PIP_INDEX_URL`, `PIP_EXTRA_INDEX_URL`, or pip config files).

---

## Installation

```bash
# Recommended: install inside your existing project virtual environment
source myenv/bin/activate  # or myenv\Scripts\activate on Windows
pip install upgrade-py-direct-reqs

# Optional: install the CLI globally with pipx
pipx install upgrade-py-direct-reqs
```

> **Important:** Even when installed via `pipx`, activate your project's virtual environment before running `upgrade-py-direct-reqs` so upgrades are applied to the correct environment.

---

## CLI reference

Syntax:

```bash
upgrade-py-direct-reqs {plan,upgrade} FILE [packages ...] [flags]
```

### Commands

- `plan`: compute upgrade candidates only; does not mutate files.
- `upgrade`: install upgrades and rewrite direct dependency declarations.

> **Note:** With the current CLI argument ordering, you should provide the command explicitly (`plan` or `upgrade`).

### Positional arguments

- `FILE`: dependency file to process (`requirements.txt` or `pyproject.toml`).
- `packages ...`: optional package names to restrict plan/upgrade scope.

### Flags

- `--python PYTHON_PATH`:
  - Use a specific Python executable.
  - Default behavior uses the Python from the active virtual environment (`VIRTUAL_ENV`).
- `--json`:
  - Emit machine-readable JSON output (especially useful for CI/agents).
- `--yes`, `-y`:
  - Skip interactive confirmation for `upgrade`.
- `--allow-major`:
  - Allow major-version bumps. Without this flag, major bumps are blocked and command exits with code `2`.
- `--tighten`:
  - Rewrite upgraded constraints as exact pins (`==`).
- `--widen`:
  - Widen `<`/`<=` style upper-bound constraints to latest available version (rewritten as `<=latest`).
- `--diff`:
  - Print a unified diff preview of planned changes.
- `--no-color`:
  - Disable emoji/status symbols.
- `-v`, `--version`:
  - Show installed CLI version and exit.
- `-h`, `--help`:
  - Show help and usage.

---

## Example usage

```bash
# Plan mode
upgrade-py-direct-reqs plan requirements.txt

# Plan + JSON + diff output (CI/agents)
upgrade-py-direct-reqs plan requirements.txt --json --diff

# Plan only for selected packages
upgrade-py-direct-reqs plan requirements.txt requests fastapi

# Upgrade selected packages and skip prompt
upgrade-py-direct-reqs upgrade requirements.txt requests fastapi --yes

# Upgrade from pyproject and allow major versions
upgrade-py-direct-reqs upgrade pyproject.toml --allow-major --yes

# Use explicit Python interpreter
upgrade-py-direct-reqs plan requirements.txt --python .venv/bin/python

# Force exact pins in planned/updated lines
upgrade-py-direct-reqs plan requirements.txt --tighten

# Preview patch-style output
upgrade-py-direct-reqs plan pyproject.toml --diff

# Show version
upgrade-py-direct-reqs --version
```

---

## AI agent section

When integrating with coding agents (or any automation), use a predictable, policy-driven sequence:

1. Discover options using `upgrade-py-direct-reqs --help`.
2. Run `plan` with structured output: `upgrade-py-direct-reqs plan <file> --json --diff`.
3. Parse and evaluate:
   - `candidates`
   - `major_blocked`
   - `changed`
   - `diff` (if requested)
4. Enforce your policy (for example: block major upgrades unless explicitly approved).
5. Execute `upgrade ... --yes` only after policy passes.

### Exit code guidance for agents

- `0`: success.
- `1`: interactive cancellation.
- `2`: major upgrades blocked without `--allow-major`.
- `3`: invalid input file / no direct dependencies found.
- `4`: environment issue (missing virtualenv or declared dependencies not installed).
- `5`: subprocess failure during upgrade.

### Private mirrors for agents

No special tool flags are required for private mirrors. If your environment already uses pip mirror/index configuration, `upgrade-py-direct-reqs` will use it automatically.

---

## Tests

```bash
pip install .[dev]
pytest tests/test_cli.py
```

Current automated coverage in `tests/test_cli.py` includes:

- invalid TOML filename validation (`pyproject.toml` naming rule)
- normalized package-name matching behavior in plan mode
- upgrade path behavior when dependencies are not installed
- plan `--json` behavior in missing-installation guard paths
- help output coverage for key option descriptions and examples

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
