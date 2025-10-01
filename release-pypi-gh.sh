#!/bin/bash
# release-pypi-gh.sh
# Automates GitHub release and PyPI upload for upgrade-py-direct-reqs (PEP 621 pyproject.toml)

set -euo pipefail

# --- Prompt for new version ---
read -p "Enter new version (e.g., 0.1.1): " new_version

# --- Update version in pyproject.toml ---
sed -i -E "s/^version = \".*\"/version = \"$new_version\"/" pyproject.toml

echo "📄 Updated version to $new_version in pyproject.toml"

# --- Commit changes and tag ---
git add pyproject.toml
git commit -m "Bump version to $new_version"
git tag "v$new_version"
git push origin main --tags

echo "✅ Git commit and tag created and pushed"

# --- Create GitHub release ---
# Requires gh CLI: https://cli.github.com/
gh release create "v$new_version" --title "v$new_version" --notes "Release $new_version"
echo "✅ GitHub release created"

# --- Build distribution ---
python3 -m pip install --upgrade build twine
python3 -m build

echo "📦 Build completed: dist/*"

# --- Upload to PyPI ---
python3 -m twine upload dist/*
echo "✅ Uploaded to PyPI"

# --- Done ---
echo "🎉 Release process completed successfully"