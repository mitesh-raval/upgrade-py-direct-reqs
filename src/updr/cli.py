#!/usr/bin/env python3
"""
upgrade-py-direct-reqs

Upgrade only direct dependencies listed in requirements.txt or pyproject.toml safely.
"""

import argparse
import json
import subprocess
import sys
import os
import tempfile
import re
from pathlib import Path
from typing import Optional, Tuple, Dict

import toml
from updr.symbols import Symbols


class CommandError(Exception):
    """Custom exception for failed subprocess commands."""


def run_cmd(cmd: list[str], capture: bool = False) -> str:
    """Runs a command and handles errors, optionally capturing output."""
    try:
        result = subprocess.run(cmd, check=True, capture_output=capture, text=True)
        return result.stdout.strip() if capture else ""
    except subprocess.CalledProcessError as e:
        raise CommandError(f"Command failed: {' '.join(cmd)}") from e
    except FileNotFoundError as exc:
        raise CommandError(f"Command not found: {cmd[0]}") from exc


def list_outdated() -> Dict[str, Tuple[str, str]]:
    """Lists outdated pip packages using 'pip list'."""
    cmd = [sys.executable, "-m", "pip", "list", "-o", "--format=json"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    # An empty JSON array is valid if no packages are outdated.
    # It will result in an empty dictionary, which is the correct behavior.
    data = json.loads(result.stdout)
    return {
        pkg["name"].lower(): (pkg["version"], pkg["latest_version"]) for pkg in data
    }


def load_requirements(req_path: Path) -> Dict[str, str]:
    """Loads dependencies from a requirements.txt file."""
    deps: Dict[str, str] = {}
    with open(req_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                pkg = line.split("==")[0].lower()
                deps[pkg] = line
    return deps


def load_toml_deps(toml_path: Path) -> Tuple[Optional[Dict[str, str]], Optional[dict]]:
    """Loads dependencies from a pyproject.toml file."""
    toml_data: dict = toml.loads(toml_path.read_text(encoding="utf-8"))
    if "project" not in toml_data or "dependencies" not in toml_data["project"]:
        print("{sym.WARN}  No [project.dependencies] found in pyproject.toml.")
        print(
            "   PEP 621 recommends using [project.dependencies]: https://peps.python.org/pep-0621/"
        )
        return None, None

    deps = {
        re.split(r"[=<>~]", dep)[0].lower().strip(): dep
        for dep in toml_data["project"]["dependencies"]
    }
    print(f" Using pyproject.toml for direct dependencies: {toml_path}")
    return deps, toml_data


def check_conflicting_sources(
    req_file_path: Path, toml_path: Path, sym: Symbols
) -> bool:
    """Checks for dependencies in both requirements.txt and pyproject.toml."""
    if toml_path.exists():
        toml_data = toml.loads(toml_path.read_text(encoding="utf-8"))
        if "project" in toml_data and "dependencies" in toml_data["project"]:
            print(f"{sym.WARN}  Multiple dependency sources detected:")
            print(
                f"   - {req_file_path.name} and pyproject.toml both declare dependencies."
            )
            print("   - Only one source can be upgraded at a time.")
            print("   - PEP 621 recommends [project.dependencies] in pyproject.toml:")
            print("     https://peps.python.org/pep-0621/")
            print(
                f"{sym.ERR} Resolve the conflict by using only one file for direct dependencies."
            )
            return True
    return False


def _get_file_dependencies(
    file_path: Path, sym: Symbols
) -> Tuple[Optional[Dict[str, str]], Optional[dict]]:
    """Loads dependencies from the specified file, handling conflicts."""
    deps: Dict[str, str] = {}
    toml_data: Optional[dict] = None

    if file_path.name.lower() == "pyproject.toml":
        deps, toml_data = load_toml_deps(file_path)
        if deps is None:
            return None, None
    else:
        if check_conflicting_sources(
            file_path, file_path.parent / "pyproject.toml", sym
        ):
            return None, None
        deps = load_requirements(file_path)

    return deps, toml_data


def _get_upgrade_candidates(
    deps: Dict[str, str], sym: Symbols
) -> Optional[Dict[str, Tuple[str, str]]]:
    """Identifies which direct dependencies are outdated."""
    print(f"{sym.INFO}  Finding outdated deps... [this may take some time]")
    outdated = list_outdated()
    candidates = {pkg: outdated[pkg] for pkg in outdated if pkg in deps}

    if not candidates:
        print(f"{sym.OK} All direct dependencies are up to date.")
        return None

    print(f"\n{sym.PKG} Outdated direct dependencies:")
    for pkg, (current, latest) in candidates.items():
        print(f"  {pkg}: {current} → {latest}")
    return candidates


def _confirm_and_upgrade(candidates: Dict[str, Tuple[str, str]], sym: Symbols) -> bool:
    """Asks for user confirmation and upgrades packages if approved."""
    print(
        f"\n{sym.WARN} Please review package revisions listed above before upgrading."
    )
    print(
        "   Check release notes on pypi.org for BREAKING changes or necessary code updates."
    )

    confirm = input("\nProceed with upgrade? (y/n): ").strip().lower()
    if confirm != "y":
        print(f"{sym.ERR} Upgrade cancelled.")
        return False

    upgrade_file = ""
    try:
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as tmp:
            for pkg in candidates:
                tmp.write(pkg + "\n")
            upgrade_file = tmp.name

        print(f"{sym.UPG} Upgrading {len(candidates)} packages...")
        run_cmd(
            [sys.executable, "-m", "pip", "install", "--upgrade", "-r", upgrade_file]
        )
        return True
    finally:
        if upgrade_file and os.path.exists(upgrade_file):
            os.remove(upgrade_file)


def _repin_dependencies(
    file_path: Path,
    deps: Dict[str, str],
    toml_data: Optional[dict],
    candidates: Dict[str, Tuple[str, str]],
    sym: Symbols,
) -> None:
    """Updates the dependency file with newly pinned versions."""
    print(f"{sym.PIN} Repinning direct dependencies...")
    freeze_output = run_cmd([sys.executable, "-m", "pip", "freeze"], capture=True)
    frozen = {line.split("==")[0].lower(): line for line in freeze_output.splitlines()}

    if file_path.name.lower() == "pyproject.toml":
        toml_data["project"]["dependencies"] = [
            frozen[pkg] if pkg in candidates else dep for pkg, dep in deps.items()
        ]
        with open(file_path, "w", encoding="utf-8") as f:
            toml.dump(toml_data, f)
        print(f"{sym.OK} pyproject.toml [project.dependencies] updated: {file_path}")
    else:
        with open(file_path, "w", encoding="utf-8", newline="\n") as f:
            for pkg_name, pkg_line in deps.items():
                f.write(f"{frozen.get(pkg_name, pkg_line)}\n")
        print(f"{sym.OK} Requirements updated: {file_path}")


def _prepare_file(
    file_path: Path, sym: Symbols
) -> Tuple[Optional[Dict[str, str]], Optional[dict]]:
    """Validates the file and loads dependencies."""
    if not file_path.exists():
        print(f"{sym.ERR} File not found: {file_path}")
        return None, None
    if file_path.is_dir():
        print(f"{sym.ERR} Path is a directory, not a file: {file_path}")
        print("   Please provide a path to a dependency file like 'requirements.txt'.")
        return None, None

    fn = file_path.name.lower().split(".")
    if fn[1] == "toml" and fn[0] != "pyproject":
        print(
            f"{sym.ERR} Invalid toml file name: {file_path}. "
            "File name must be pyproject.toml [PEP 621]\n"
        )
        return None, None

    print(f"{sym.INFO}  Analyzing deps for {file_path}... ")
    deps, toml_data = _get_file_dependencies(file_path, sym)
    if not deps:
        print(f"{sym.ERR} No direct dependencies found to process.")
        return None, None

    return deps, toml_data


def main() -> None:
    """Main entry point for the CLI tool."""
    parser = argparse.ArgumentParser(
        description="Upgrade only direct dependencies from requirements.txt or pyproject.toml"
    )
    parser.add_argument("file", help="Path to requirements.txt or pyproject.toml")
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable emojis for simpler terminals (e.g., Windows, CI)",
    )
    args = parser.parse_args()
    sym = Symbols(args.no_color)

    try:
        file_path = Path(args.file).resolve()
        deps, toml_data = _prepare_file(file_path, sym)
        if not deps:
            return

        candidates = _get_upgrade_candidates(deps, sym)
        if not candidates:
            return

        upgraded = _confirm_and_upgrade(candidates, sym)
        if not upgraded:
            return

        _repin_dependencies(file_path, deps, toml_data, candidates, sym)
    except CommandError as e:
        print(f"{sym.ERR} {e}")
    except KeyboardInterrupt:
        print(f"\n{sym.ERR} Operation cancelled by user.")


if __name__ == "__main__":
    main()
