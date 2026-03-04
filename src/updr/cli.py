#!/usr/bin/env python3
"""upgrade-py-direct-reqs CLI."""

import argparse
import difflib
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version as package_version
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import toml
from packaging.version import Version
from updr.symbols import Symbols


def get_updr_version() -> str:
    """Return installed package version for CLI display."""
    try:
        return package_version("upgrade-py-direct-reqs")
    except PackageNotFoundError:
        return "0.0.0"


class CommandError(Exception):
    """Custom exception for failed subprocess commands."""


@dataclass
class DepSpec:
    """Represents one direct dependency declaration."""

    raw: str
    canonical_name: str
    operator: Optional[str]
    version: Optional[str]


OPERATORS = ("==", "~=", ">=", "<=", "!=", ">", "<")


def normalize_package_name(name: str) -> str:
    """Normalize package names for safe matching (PEP 503 style)."""
    return re.sub(r"[-_.]+", "-", name).lower().strip()


def parse_dep_spec(line: str) -> Optional[DepSpec]:
    """Parse dependency specifier into a normalized representation."""
    text = line.strip()
    if not text or text.startswith("#"):
        return None

    # Basic parser to cover common direct dependency forms.
    match = re.match(r"^\s*([A-Za-z0-9_.-]+)\s*(.*)$", text)
    if not match:
        return None

    name = match.group(1)
    tail = match.group(2).strip()
    operator = None
    version = None
    for op in OPERATORS:
        if tail.startswith(op):
            operator = op
            version = tail[len(op) :].strip()
            break

    return DepSpec(raw=text, canonical_name=normalize_package_name(name), operator=operator, version=version)


def run_cmd(cmd: List[str], capture: bool = False) -> str:
    """Runs a command and handles errors, optionally capturing output."""
    try:
        result = subprocess.run(cmd, check=True, capture_output=capture, text=True)
        return result.stdout.strip() if capture else ""
    except subprocess.CalledProcessError as exc:
        raise CommandError(f"Command failed: {' '.join(cmd)}") from exc
    except FileNotFoundError as exc:
        raise CommandError(f"Command not found: {cmd[0]}") from exc


def get_python_cmd(sym: Symbols, explicit_python: Optional[str]) -> Optional[str]:
    """Resolve python executable from flag or active virtual environment."""
    if explicit_python:
        if Path(explicit_python).exists():
            return explicit_python
        print(f"{sym.ERR} Python executable not found: {explicit_python}")
        return None

    venv = os.environ.get("VIRTUAL_ENV")
    if not venv:
        print(f"{sym.ERR} No virtual environment detected.")
        print("   Please activate your project venv or pass --python.")
        return None

    python_path = Path(venv) / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python_path.exists():
        print(f"{sym.ERR} Could not locate python in activated virtual environment.")
        print(f"   Expected path: {python_path}")
        return None
    return str(python_path)


def list_outdated(python_cmd: str) -> Dict[str, Tuple[str, str]]:
    """Lists outdated pip packages using 'pip list'."""
    cmd = [python_cmd, "-m", "pip", "list", "-o", "--format=json"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    return {
        normalize_package_name(pkg["name"]): (pkg["version"], pkg["latest_version"]) for pkg in data
    }


def load_requirements(req_path: Path) -> Dict[str, DepSpec]:
    """Loads direct dependencies from requirements file."""
    deps: Dict[str, DepSpec] = {}
    with open(req_path, encoding="utf-8") as handle:
        for line in handle:
            spec = parse_dep_spec(line)
            if spec:
                deps[spec.canonical_name] = spec
    return deps


def check_not_installed(deps: Dict[str, DepSpec], sym: Symbols, python_cmd: str) -> bool:
    """Warn if declared direct dependencies are not installed."""
    missing = []
    for pkg in deps:
        result = subprocess.run(
            [python_cmd, "-m", "pip", "show", pkg], capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            missing.append(pkg)

    if missing:
        print(f"{sym.WARN} The following direct dependencies are NOT installed:")
        for pkg in missing:
            print(f"  - {pkg}")
        print("   Install them before attempting upgrades.")
        return False

    return True


def load_toml_deps(toml_path: Path, sym: Symbols) -> Tuple[Optional[Dict[str, DepSpec]], Optional[dict]]:
    """Load dependencies from a pyproject.toml file."""
    toml_data: dict = toml.loads(toml_path.read_text(encoding="utf-8"))
    if "project" not in toml_data or "dependencies" not in toml_data["project"]:
        print(f"{sym.WARN}  No [project.dependencies] found in pyproject.toml.")
        print("   PEP 621 recommends using [project.dependencies]: https://peps.python.org/pep-0621/")
        return None, None

    deps: Dict[str, DepSpec] = {}
    for dep in toml_data["project"]["dependencies"]:
        spec = parse_dep_spec(dep)
        if spec:
            deps[spec.canonical_name] = spec
    print(f" Using pyproject.toml for direct dependencies: {toml_path}")
    return deps, toml_data


def check_conflicting_sources(req_file_path: Path, toml_path: Path, sym: Symbols) -> bool:
    """Check for dependencies in both requirements and pyproject.toml."""
    if toml_path.exists():
        toml_data = toml.loads(toml_path.read_text(encoding="utf-8"))
        if "project" in toml_data and "dependencies" in toml_data["project"]:
            print(f"{sym.WARN}  Multiple dependency sources detected:")
            print(f"   - {req_file_path.name} and pyproject.toml both declare dependencies.")
            print("   - Only one source can be upgraded at a time.")
            print(f"{sym.ERR} Resolve the conflict by using only one file for direct dependencies.")
            return True
    return False


def _get_file_dependencies(file_path: Path, sym: Symbols) -> Tuple[Optional[Dict[str, DepSpec]], Optional[dict]]:
    if file_path.name.lower() == "pyproject.toml":
        return load_toml_deps(file_path, sym)

    if check_conflicting_sources(file_path, file_path.parent / "pyproject.toml", sym):
        return None, None
    return load_requirements(file_path), None


def _get_upgrade_candidates(deps: Dict[str, DepSpec], python_cmd: str, package_filter: Optional[set[str]]) -> Dict[str, Tuple[str, str]]:
    outdated = list_outdated(python_cmd)
    candidates = {pkg: outdated[pkg] for pkg in outdated if pkg in deps}
    if package_filter:
        candidates = {pkg: val for pkg, val in candidates.items() if pkg in package_filter}
    return candidates


def _is_major_bump(current: str, latest: str) -> bool:
    try:
        return Version(latest).major > Version(current).major
    except Exception:
        return False


def _planned_line(spec: DepSpec, latest: str, tighten: bool, widen: bool) -> str:
    if spec.operator is None:
        return f"{spec.canonical_name}=={latest}"
    if spec.operator == "==" or tighten:
        return f"{spec.canonical_name}=={latest}"
    if widen and spec.operator in {"<=", "<"}:
        return f"{spec.canonical_name}<={latest}"
    return f"{spec.canonical_name}{spec.operator}{latest}"


def _build_plan(
    deps: Dict[str, DepSpec],
    candidates: Dict[str, Tuple[str, str]],
    tighten: bool,
    widen: bool,
) -> Dict[str, str]:
    return {pkg: _planned_line(deps[pkg], latest, tighten, widen) for pkg, (_, latest) in candidates.items()}


def _render_diff(file_path: Path, deps: Dict[str, DepSpec], plan_lines: Dict[str, str]) -> str:
    before = file_path.read_text(encoding="utf-8").splitlines(keepends=True)
    if file_path.name.lower() == "pyproject.toml":
        new_data = toml.loads(file_path.read_text(encoding="utf-8"))
        existing = new_data["project"]["dependencies"]
        rewritten = []
        for dep in existing:
            spec = parse_dep_spec(dep)
            if spec and spec.canonical_name in plan_lines:
                rewritten.append(plan_lines[spec.canonical_name])
            else:
                rewritten.append(dep)
        new_data["project"]["dependencies"] = rewritten
        after_text = toml.dumps(new_data)
    else:
        out_lines = []
        for line in before:
            spec = parse_dep_spec(line)
            if spec and spec.canonical_name in plan_lines:
                out_lines.append(plan_lines[spec.canonical_name] + "\n")
            else:
                out_lines.append(line)
        after_text = "".join(out_lines)

    return "".join(
        difflib.unified_diff(before, after_text.splitlines(keepends=True), fromfile=str(file_path), tofile=str(file_path))
    )


def _apply_upgrade(python_cmd: str, candidates: Dict[str, Tuple[str, str]]) -> None:
    upgrade_file = ""
    try:
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as tmp:
            for pkg in candidates:
                tmp.write(pkg + "\n")
            upgrade_file = tmp.name
        run_cmd([python_cmd, "-m", "pip", "install", "--upgrade", "-r", upgrade_file])
    finally:
        if upgrade_file and os.path.exists(upgrade_file):
            os.remove(upgrade_file)


def _write_updates(file_path: Path, deps: Dict[str, DepSpec], toml_data: Optional[dict], plan_lines: Dict[str, str]) -> None:
    if file_path.name.lower() == "pyproject.toml":
        assert toml_data is not None
        toml_data["project"]["dependencies"] = [
            plan_lines.get(parse_dep_spec(dep).canonical_name, dep) if parse_dep_spec(dep) else dep
            for dep in toml_data["project"]["dependencies"]
        ]
        file_path.write_text(toml.dumps(toml_data), encoding="utf-8")
        return

    original = file_path.read_text(encoding="utf-8").splitlines()
    out = []
    for line in original:
        spec = parse_dep_spec(line)
        out.append(plan_lines.get(spec.canonical_name, line) if spec else line)
    file_path.write_text("\n".join(out) + "\n", encoding="utf-8")


def _prepare_file(file_path: Path, sym: Symbols) -> Tuple[Optional[Dict[str, DepSpec]], Optional[dict]]:
    if not file_path.exists():
        print(f"{sym.ERR} File not found: {file_path}")
        return None, None
    if file_path.is_dir():
        print(f"{sym.ERR} Path is a directory, not a file: {file_path}")
        return None, None

    if file_path.suffix == ".toml" and file_path.name != "pyproject.toml":
        print(f"{sym.ERR} Invalid toml file name: {file_path}. File name must be pyproject.toml [PEP 621]")
        return None, None

    deps, toml_data = _get_file_dependencies(file_path, sym)
    if not deps:
        print(f"{sym.ERR} No direct dependencies found to process.")
        return None, None
    return deps, toml_data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="upgrade-py-direct-reqs", description="Plan or upgrade direct dependencies"
    )
    parser.add_argument("command", nargs="?", choices=["plan", "upgrade"], default="plan")
    parser.add_argument("file", nargs="?", help="Path to requirements.txt or pyproject.toml")
    parser.add_argument("packages", nargs="*", help="Optional package filter for plan/upgrade")
    parser.add_argument("--python", dest="python_path", help="Python executable path")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt for upgrades")
    parser.add_argument("--allow-major", action="store_true", help="Allow major version bumps")
    parser.add_argument("--tighten", action="store_true", help="Rewrite upgraded specs to exact pins")
    parser.add_argument("--widen", action="store_true", help="Widen upper-bound operators when upgrading")
    parser.add_argument("--diff", action="store_true", help="Print unified diff of planned file changes")
    parser.add_argument("--no-color", action="store_true", help="Disable emojis")
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"upgrade-py-direct-reqs {get_updr_version()}",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.file:
        parser.error("the following arguments are required: file")

    sym = Symbols(args.no_color or args.json)
    python_cmd = get_python_cmd(sym, args.python_path)
    if not python_cmd:
        sys.exit(4)

    file_path = Path(args.file).resolve()
    deps, toml_data = _prepare_file(file_path, sym)
    if not deps:
        sys.exit(3)

    if not check_not_installed(deps, sym, python_cmd):
        sys.exit(4)

    package_filter = {normalize_package_name(pkg) for pkg in args.packages} if args.packages else None
    candidates = _get_upgrade_candidates(deps, python_cmd, package_filter)
    major_blocked = [pkg for pkg, (cur, lat) in candidates.items() if _is_major_bump(cur, lat)]

    plan_lines = _build_plan(deps, candidates, args.tighten, args.widen)
    diff = _render_diff(file_path, deps, plan_lines) if args.diff else ""

    payload = {
        "command": args.command,
        "file": str(file_path),
        "candidates": [
            {"name": pkg, "current": cur, "latest": lat, "planned": plan_lines[pkg]} for pkg, (cur, lat) in sorted(candidates.items())
        ],
        "major_blocked": major_blocked,
        "changed": bool(candidates),
    }
    if args.diff:
        payload["diff"] = diff

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        if not candidates:
            print(f"{sym.OK} All direct dependencies are up to date.")
        else:
            print(f"{sym.PKG} Planned dependency updates:")
            for pkg, (current, latest) in sorted(candidates.items()):
                print(f"  {pkg}: {current} -> {latest} ({plan_lines[pkg]})")
            if major_blocked and not args.allow_major:
                print(f"{sym.WARN} Major version bump blocked for: {', '.join(sorted(major_blocked))}")
            if args.diff and diff:
                print(diff)

    if args.command == "plan":
        if major_blocked and not args.allow_major:
            sys.exit(2)
        sys.exit(0)

    if major_blocked and not args.allow_major:
        sys.exit(2)

    if not candidates:
        sys.exit(0)

    if not args.yes:
        confirm = input("Proceed with upgrade? (y/n): ").strip().lower()
        if confirm != "y":
            print(f"{sym.ERR} Upgrade cancelled.")
            sys.exit(1)

    try:
        _apply_upgrade(python_cmd, candidates)
        _write_updates(file_path, deps, toml_data, plan_lines)
    except CommandError as exc:
        print(f"{sym.ERR} {exc}")
        sys.exit(5)


if __name__ == "__main__":
    main()
