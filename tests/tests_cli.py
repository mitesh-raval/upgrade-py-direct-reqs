import subprocess
import sys
from pathlib import Path
import tempfile
import pytest


def run_cli(file_path):
    """Run the CLI and capture output"""
    result = subprocess.run(
        [sys.executable, "src/updr/cli.py", str(file_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        input="n\n",  # cancel upgrades
        check=True,
    )
    return result.stdout


# Primary fixture renamed to avoid outer-scope warnings
@pytest.fixture(name="pkgs")
def _pkgs_fixture_impl():
    """Provides an immutable tuple of package names for tests."""
    return ("toml==0.0.1", "pytest==0.0.1")


@pytest.fixture(name="setup_req_file")
def _setup_req_file_impl(pkgs):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "requirements_test.txt"
        path.write_text("\n".join(pkgs) + "\n")
        yield path


@pytest.fixture(name="setup_toml_file")
def _setup_toml_file_impl(pkgs):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "pyproject.toml"
        path.write_text(
            f"""
[project]
dependencies = {list(pkgs)}
"""
        )
        yield path


@pytest.fixture(name="setup_conflicting_files")
def _setup_conflicting_files_impl(pkgs):
    with tempfile.TemporaryDirectory() as tmpdir:
        req_path = Path(tmpdir) / "requirements_test.txt"
        req_path.write_text("\n".join(pkgs) + "\n")
        toml_path = Path(tmpdir) / "pyproject.toml"
        toml_path.write_text(
            f"""
[project]
dependencies = {list(pkgs)}
"""
        )
        yield req_path, toml_path


@pytest.fixture(name="setup_empty_file")
def _setup_empty_file_impl():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "requirements_empty.txt"
        path.write_text("")
        yield path


@pytest.fixture(name="setup_invalid_toml_file_name")
def _setup_invalid_toml_file_name_impl():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "pyproj.toml"
        path.write_text("")
        yield path


def test_requirements_only(setup_req_file):
    out = run_cli(setup_req_file)
    assert (
        "Outdated direct dependencies" in out
        or "All direct dependencies are up to date" in out
        or "No direct dependencies found" in out
    )


def test_toml_only(setup_toml_file):
    out = run_cli(setup_toml_file)
    assert "Using pyproject.toml" in out
    assert (
        "Outdated direct dependencies" in out
        or "All direct dependencies are up to date" in out
        or "No direct dependencies found" in out
    )


def test_conflicting_files(setup_conflicting_files):
    req_file, _ = setup_conflicting_files
    out = run_cli(req_file)
    assert "Multiple dependency sources detected" in out


def test_empty_requirements(setup_empty_file):
    out = run_cli(setup_empty_file)
    assert (
        "No direct dependencies found" in out
        or "All direct dependencies are up to date" in out
    )


def test_invalid_toml_file_name(setup_invalid_toml_file_name):
    out = run_cli(setup_invalid_toml_file_name)
    assert "Invalid toml file name" in out
    assert "File name must be pyproject.toml" in out
