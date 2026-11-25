import json
import shutil
import subprocess
from importlib.metadata import distribution
from importlib.resources import files
from pathlib import Path


def test_packaged_skill_and_entry_point():
    root = Path(__file__).resolve().parents[1]
    skill = root / "skills/cli-anything-davinci/SKILL.md"
    assert (
        files("cli_anything.davinci").joinpath("skills/SKILL.md").read_bytes()
        == skill.read_bytes()
    )
    dist = distribution("cli-anything-davinci")
    entry = dist.entry_points["cli-anything-davinci"]
    assert entry.group == "console_scripts" and callable(entry.load())


def test_installed_cli_outside_checkout(tmp_path, monkeypatch):
    exe = shutil.which("cli-anything-davinci")
    assert exe, "Activate the environment containing the installed entry point."
    monkeypatch.setenv("RESOLVE_SCRIPT_API", str(tmp_path / "not-installed"))

    def run(*args):
        return subprocess.run(
            [exe, *args],
            cwd=tmp_path,
            text=True,
            capture_output=True,
            check=False,
            timeout=20,
        )

    assert run("--help").returncode == 0
    result = run("--json", "doctor")
    assert result.returncode == 3
    assert json.loads(result.stdout)["error"]["code"] == "unavailable"
