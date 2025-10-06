#!/usr/bin/env python3
"""
upgrade-py-direct-reqs

Upgrade only direct dependencies listed in requirements.txt or pyproject.toml safely.
"""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import toml

# pylint: disable=R1710 # inconsistent-return-statements
# pylint: disable=R0914 # too-many-locals


def run_cmd(cmd, capture=False):
    try:
        if capture:
            return subprocess.check_output(cmd, text=True).strip()
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        print(f"❌ Command failed: {' '.join(cmd)}")
        sys.exit(1)


def list_outdated():
    output = subprocess.check_output(
        [sys.executable, "-m", "pip", "list", "-o", "--format=json"], text=True
    )
    data = json.loads(output)
    return {
        pkg["name"].lower(): (pkg["version"], pkg["latest_version"]) for pkg in data
    }


def load_requirements(req_path):
    deps = {}
    with open(req_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                pkg = line.split("==")[0].lower()
                deps[pkg] = line
    return deps


def main():
    parser = argparse.ArgumentParser(
        description="Upgrade only direct dependencies from requirements.txt or pyproject.toml"
    )
    parser.add_argument("file", help="Path to requirements.txt or pyproject.toml")
    args = parser.parse_args()

    file_path = Path(args.file).resolve()
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)

    is_requirements = file_path.suffix == ".txt"
    is_toml = file_path.suffix == ".toml"

    if not (is_requirements or is_toml):
        print(
            "❌ Unsupported file type. Only requirements.txt or pyproject.toml are supported."
        )
        return

    deps = {}

    if is_requirements:
        deps = load_requirements(file_path)
        toml_path = file_path.parent / "pyproject.toml"
        if toml_path.exists():
            print("⚠️  Multiple dependency sources detected:")
            toml_data = toml.loads(toml_path.read_text(encoding="utf-8"))
            if "project" in toml_data and "dependencies" in toml_data["project"]:
                print(
                    "   - requirements.txt and pyproject.toml both declare dependencies."
                )
                print("   - Only one source can be upgraded at a time.")
                print(
                    "   - PEP 621 recommends [project.dependencies] in pyproject.toml:"
                )
                print("     https://peps.python.org/pep-0621/")
                print("❌ Resolve the conflict before proceeding.")
                return

            print(
                "   - requirements.txt will be used because pyproject.toml does not define [project.dependencies]."
            )
            print(
                "   - See PEP 621 for modern dependency management: https://peps.python.org/pep-0621/"
            )

    if is_toml:
        toml_data = toml.loads(file_path.read_text(encoding="utf-8"))
        if "project" not in toml_data or "dependencies" not in toml_data["project"]:
            print("⚠️  No [project.dependencies] found in pyproject.toml.")
            print(
                "   PEP 621 recommends using [project.dependencies]: https://peps.python.org/pep-0621/"
            )
            return
        deps = {
            dep.split("==")[0].lower(): dep
            for dep in toml_data["project"]["dependencies"]
        }
        print(f"📄 Using pyproject.toml for direct dependencies: {file_path}")

    if not deps:
        print("❌ No direct dependencies found.")
        return

    outdated = list_outdated()
    candidates = {pkg: outdated[pkg] for pkg in outdated if pkg in deps}

    if not candidates:
        print("✅ All direct dependencies are up to date.")
        return

    print("\n📦 Outdated direct dependencies:")
    for pkg, (current, latest) in candidates.items():
        print(f"  {pkg}: {current} → {latest}")
    print("\n⚠️  Please review package revisions listed above before upgrading.")
    print(
        "   Check release notes on pypi.org for BREAKING changes or necessary code updates."
    )

    confirm = input("\nProceed with upgrade? (y/n): ").strip().lower()
    if confirm != "y":
        print("❌ Upgrade cancelled.")
        return

    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as tmp:
        for pkg in candidates:
            tmp.write(pkg + "\n")
        upgrade_file = tmp.name

    print(f"⬆️  Upgrading {len(candidates)} packages...")
    run_cmd([sys.executable, "-m", "pip", "install", "--upgrade", "-r", upgrade_file])

    print("📌 Repinning direct dependencies...")
    freeze_output = run_cmd([sys.executable, "-m", "pip", "freeze"], capture=True)
    frozen = {line.split("==")[0].lower(): line for line in freeze_output.splitlines()}

    if is_requirements:
        with open(file_path, "w", encoding="utf-8") as f:
            for pkg_name, pkg_line in deps.items():
                if pkg_name in frozen:
                    f.write(f"{frozen[pkg_name]}\n")
                else:
                    f.write(pkg_line + "\n")
        print(f"✅ Requirements updated: {file_path}")
    else:
        # Update TOML
        toml_data["project"]["dependencies"] = [
            frozen.get(pkg, dep) for pkg, dep in deps.items()
        ]
        with open(file_path, "w", encoding="utf-8") as f:
            toml.dump(toml_data, f)
        print(f"✅ pyproject.toml [project.dependencies] updated: {file_path}")


if __name__ == "__main__":
    main()
