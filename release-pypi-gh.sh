#!/bin/bash
# release-pypi-gh.sh
# Automates GitHub release and PyPI upload for upgrade-py-direct-reqs (PEP 621 pyproject.toml)

# Intentionally avoid `set -e` so failures stay visible in terminal output
# and the script can print a final summary instead of exiting abruptly.
set -uo pipefail

# Prevent interactive git username/password prompts in release flows.
# If credentials are missing, fail fast for that step with a clear message.
export GIT_TERMINAL_PROMPT=0

failures=0

warn_step() {
  local msg="$1"
  echo "⚠️ $msg"
  failures=$((failures + 1))
}

require_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "❌ $cmd is required but not found in PATH."
    return 1
  fi
  return 0
}

run_or_warn() {
  local description="$1"
  shift
  echo "▶️ $description"
  if "$@"; then
    echo "✅ $description"
  else
    warn_step "$description failed"
  fi
}

require_cmd git || exit 1
require_cmd python3 || exit 1
require_cmd gh || exit 1

echo "🧹 Cleaning build artifacts..."
rm -rf build/ dist/ *.egg-info/ src/*.egg-info || warn_step "Clean step encountered an issue"
echo "✅ Clean complete"

if [[ ${1-} == "clean" ]]; then
  exit 0
fi

read -r -p "Enter new version (e.g., 0.1.1): " new_version
if [[ -z "$new_version" ]]; then
  echo "❌ Version cannot be empty."
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "❌ gh is not authenticated. Run: gh auth login"
  exit 1
fi

origin_url="$(git remote get-url origin 2>/dev/null || true)"
if [[ -z "$origin_url" ]]; then
  echo "❌ Could not resolve git remote 'origin'."
  exit 1
fi

if [[ "$origin_url" == https://* ]]; then
  echo "ℹ️ Detected HTTPS remote: $origin_url"
  echo "   If git push fails with auth prompts, either:"
  echo "   1) run: gh auth setup-git"
  echo "   2) or switch to SSH remote: git remote set-url origin git@github.com:<owner>/<repo>.git"
fi

echo "🔐 Validating push access to origin..."
if ! git ls-remote --exit-code origin >/dev/null 2>&1; then
  echo "❌ Cannot access origin with current git credentials."
  echo "   Ensure git credential helper is configured, or use SSH remote auth."
  exit 1
fi

run_or_warn "Update version in pyproject.toml" python3 - <<PY
from pathlib import Path
import re

path = Path("pyproject.toml")
text = path.read_text(encoding="utf-8")
new = re.sub(r'^version\s*=\s*"[^"]+"', f'version = "${new_version}"', text, count=1, flags=re.M)
if new == text:
    raise SystemExit("Unable to update version in pyproject.toml")
path.write_text(new, encoding="utf-8")
PY

echo "📄 Version update attempted for $new_version"

run_or_warn "Stage pyproject.toml" git add pyproject.toml
if git diff --cached --quiet; then
  echo "ℹ️ No version changes to commit."
else
  run_or_warn "Commit version bump" git commit -m "chore: release v$new_version"
fi

run_or_warn "Create/update tag v$new_version" git tag -f "v$new_version"

run_or_warn "Push commit to main" git push origin HEAD:main
run_or_warn "Push tag v$new_version" git push origin "v$new_version" --force

if gh release view "v$new_version" >/dev/null 2>&1; then
  run_or_warn "Edit existing GitHub release v$new_version" gh release edit "v$new_version" --title "v$new_version" --notes "Release $new_version"
else
  run_or_warn "Create GitHub release v$new_version" gh release create "v$new_version" --target main --title "v$new_version" --notes "Release $new_version"
fi

run_or_warn "Install build tools" python3 -m pip install --upgrade build twine
run_or_warn "Build distribution" python3 -m build
run_or_warn "Upload to PyPI" python3 -m twine upload dist/*

if [[ "$failures" -gt 0 ]]; then
  echo "⚠️ Release completed with $failures warning(s). Review logs above."
  exit 1
fi

echo "🎉 Release process completed successfully"
