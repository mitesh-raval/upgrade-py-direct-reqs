#!/usr/bin/env python3
"""
upgrade-py-direct-reqs

Upgrade only direct dependencies listed in requirements.txt safely.
"""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def run_cmd(cmd, capture=False):
    try:
        if capture:
            return subprocess.check_output(cmd, text=True).strip()
        else:
            subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
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
    with open(req_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                pkg = line.split("==")[0].lower()
                deps[pkg] = line
    return deps


def main():
    parser = argparse.ArgumentParser(
        description="Upgrade only direct dependencies from requirements.txt"
    )
    parser.add_argument("requirements", help="Path to requirements.txt")
    args = parser.parse_args()

    req_path = Path(args.requirements).resolve()
    if not req_path.exists():
        print(f"❌ requirements file not found: {req_path}")
        sys.exit(1)

    print(f"📄 Using requirements: {req_path}\n")

    outdated = list_outdated()
    direct = load_requirements(req_path)

    candidates = {pkg: outdated[pkg] for pkg in direct if pkg in outdated}

    if not candidates:
        print("✅ No direct dependencies are outdated.\n")
        return

    print("📦 Outdated direct dependencies:")
    for pkg, (current, latest) in candidates.items():
        print(f"  {pkg}: {current} → {latest}")
    print()

    print("⚠️  Please review package revisions listed above before upgrading.")
    print(
        "   Check release notes on pypi.org for BREAKING changes or necessary code updates."
    )
    print()

    confirm = input("Proceed with upgrade? (y/n): ").strip().lower()
    if confirm != "y":
        print("❌ Upgrade cancelled.\n")
        return

    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        for pkg in candidates:
            tmp.write(pkg + "\n")
        upgrade_file = tmp.name

    print(f"⬆️  Upgrading {len(candidates)} packages...\n")
    run_cmd([sys.executable, "-m", "pip", "install", "--upgrade", "-r", upgrade_file])

    print("📌 Repinning direct dependencies into requirements.txt...")
    freeze_output = run_cmd([sys.executable, "-m", "pip", "freeze"], capture=True)
    frozen = {line.split("==")[0].lower(): line for line in freeze_output.splitlines()}

    with open(req_path, "w") as f:
        for pkg in direct:
            if pkg in frozen:
                f.write(f"{frozen[pkg]}\n")
            else:
                f.write(direct[pkg] + "\n")

    print(f"✅ Requirements updated: {req_path}\n")


if __name__ == "__main__":
    main()
