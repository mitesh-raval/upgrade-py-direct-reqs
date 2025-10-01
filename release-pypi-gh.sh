#!/bin/bash
# release-pypi-gh.sh
# Automates GitHub release and PyPI upload for upgrade-py-direct-reqs (PEP 621 pyproject.toml)
# Uses gh CLI for all GitHub operations, no direct git commands

set -uo pipefail   # do not exit on error automatically

# --- Handle 'clean' target ---
if [[ ${1-} == "clean" ]]; then
    echo "🧹 Cleaning build artifacts..."
    rm -rf build/ dist/ *.egg-info/ || echo "⚠️ Nothing to clean"
    echo "✅ Clean complete"
    exit 0
fi

# --- Prompt for new version ---
read -p "Enter new version (e.g., 0.1.1): " new_version

# --- Update version in pyproject.toml ---
sed -i -E "s/^version = \".*\"/version = \"$new_version\"/" pyproject.toml || echo "⚠️ Failed to update version"


echo "📄 Updated version to $new_version in pyproject.toml"

# --- Skip PR creation (optional) ---
echo "ℹ️ Skipping automatic PR creation step"

# --- Create GitHub release (handles existing tag) ---
if gh release view "v$new_version" >/dev/null 2>&1; then
    echo "⚠️ Release v$new_version already exists. Skipping creation."
else
    gh release create "v$new_version" --target main --title "v$new_version" --notes "Release $new_version" || echo "⚠️ Failed to create GitHub release"
    echo "✅ GitHub release created (if no warnings above)"
fi

# --- Build distribution ---
python3 -m pip install --upgrade build twine || echo "⚠️ Failed to install build tools"
python3 -m build || echo "⚠️ Build failed"

echo "📦 Build completed: dist/*"

# --- Upload to PyPI ---
python3 -m twine upload dist/* || echo "⚠️ PyPI upload failed"

echo "✅ Uploaded to PyPI (if no errors above)"

# --- Done ---
echo "🎉 Release process completed (check above for any warnings)"