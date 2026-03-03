import json
import os
import subprocess
import sys
from pathlib import Path


def run_cli(args, input_text=""):
    env = dict(os.environ)
    env["VIRTUAL_ENV"] = sys.prefix
    env["PYTHONPATH"] = str(Path("src").resolve())
    return subprocess.run(
        [sys.executable, "src/updr/cli.py", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        input=input_text,
        env=env,
        check=False,
    )


def test_invalid_toml_file_name(tmp_path):
    path = tmp_path / "random.toml"
    path.write_text("", encoding="utf-8")
    result = run_cli(["plan", str(path)])
    assert result.returncode == 3
    assert "Invalid toml file name" in result.stdout


def test_normalized_package_filter_case_insensitive(tmp_path):
    req = tmp_path / "requirements.txt"
    req.write_text("Requests==0.0.1\n", encoding="utf-8")
    result = run_cli(["plan", str(req), "requests", "--json"])
    # exits before network call because dependency is not installed
    assert result.returncode == 4
    assert "NOT installed" in result.stdout


def test_upgrade_requires_confirmation_without_yes(tmp_path):
    req = tmp_path / "requirements.txt"
    req.write_text("Definitely-Missing-Pkg==0.0.1\n", encoding="utf-8")
    result = run_cli(["upgrade", str(req)], input_text="n\n")
    assert result.returncode == 4
    assert "NOT installed" in result.stdout


def test_plan_json_when_missing_installations(tmp_path):
    req = tmp_path / "requirements.txt"
    req.write_text("Definitely-Missing-Pkg==0.0.1\n", encoding="utf-8")
    result = run_cli(["plan", str(req), "--json"])
    assert result.returncode == 4
    assert "NOT installed" in result.stdout


def test_version_flag():
    result = run_cli(["--version"])
    assert result.returncode == 0
    assert result.stdout.strip().startswith("updr ")
