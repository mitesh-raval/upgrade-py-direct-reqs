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
- Supports Python 3.9–3.13.

---

## GitHub Actions support

This repository includes built-in GitHub Actions CI in `.github/workflows/ci.yml`.

### Quick understanding (for end users)

When code is pushed or a PR is opened, GitHub Actions automatically:

1. Checks out the repository
2. Creates a Python environment (3.9–3.13)
3. Installs dependencies with `pip install .[dev]`
4. Runs `pytest tests/test_cli.py`

### Trigger events

- `push` (to `main`/`master`)
- `pull_request`
- `workflow_dispatch` (manual run from GitHub UI)

### Using private mirrors in Actions

Private mirrors are supported by default. Set your normal pip index configuration in the workflow/job environment (for example `PIP_INDEX_URL`, `PIP_EXTRA_INDEX_URL`, or pip config files + secrets).

### Where to use this in CI/CD (important)

Use this tool in a **dependency-maintenance workflow**, not your main deployment pipeline.

- Main CI/deploy pipelines should usually install already-committed dependencies and validate/build/release.
- Maintenance pipelines (for example scheduled weekly jobs) can run `plan --json --diff`, optionally run `upgrade --yes`, and open a PR with the dependency-file changes for review.
- Developers can still run the tool locally; the pipeline approach simply centralizes and automates the same process with consistent policy checks.

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
upgrade-py-direct-reqs [plan|upgrade] FILE [packages ...] [flags]
```

### Commands

- `plan`: compute upgrade candidates only; does not mutate files.
- `upgrade`: install upgrades and rewrite direct dependency declarations.

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
# Default plan mode (command omitted)
upgrade-py-direct-reqs requirements.txt

# Flags can precede the file and still default to plan
upgrade-py-direct-reqs --json requirements.txt

# Explicit plan mode
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

### Before/after sample (interactive upgrade)

Before (`requirements.txt`):

```txt
requests==2.30.0
flask==2.2.5
```

Command:

```bash
upgrade-py-direct-reqs upgrade requirements.txt
```

Sample output:

```text
ℹ️  Checking outdated packages via pip. This can take a little while depending on network/index speed...
📦 Planned dependency updates:
  flask: 2.2.5 -> 3.0.3 (flask==3.0.3)
  requests: 2.30.0 -> 2.32.3 (requests==2.32.3)

Proceed with upgrade? (y/n): y
```

After (`requirements.txt`):

```txt
requests==2.32.3
flask==3.0.3
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

> In most teams, this sequence is run as a dedicated maintenance pipeline that opens PRs, while regular CI pipelines continue validating pinned dependencies.

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

The project and CI currently target Python 3.9–3.13.

Current automated coverage in `tests/test_cli.py` includes:

- invalid TOML filename validation (`pyproject.toml` naming rule)
- normalized package-name matching behavior in plan mode
- upgrade path behavior when dependencies are not installed
- plan `--json` behavior in missing-installation guard paths
- help output coverage for key option descriptions and examples

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
