import json

import pytest
from click.testing import CliRunner

from cli_anything.davinci.davinci_cli import cli
from cli_anything.davinci.utils.davinci_backend import Backend


def test_status_and_doctor(run):
    assert run("status")["product"] == "DaVinci Resolve Studio"
    assert run("doctor")["connected"] is True


@pytest.mark.parametrize(
    "args",
    [
        ["project", "unknown"],
        ["timeline", "select", "0"],
        ["render", "configure", "--format", "mov"],
    ],
)
def test_usage_json(run, args):
    assert run(*args, code=2)["code"] == "usage"


def test_doctor_reports_failed_discovery(monkeypatch, tmp_path):
    monkeypatch.setenv("RESOLVE_SCRIPT_API", str(tmp_path))
    result = CliRunner().invoke(cli, ["doctor", "--json"])
    assert result.exit_code == 3
    error = json.loads(result.output)["error"]
    assert error["details"]["connected"] is False
    assert error["details"]["module_dirs"] == [str(tmp_path / "Modules")]


def test_empty_project_and_timeline(b, run):
    del b.project
    b.manager.GetCurrentProject.return_value = None
    assert run("project", "current", code=1)["code"] == "no_project"
    del b.timeline
    b.manager.GetCurrentProject.return_value = b.pool
    b.pool.GetCurrentTimeline.return_value = None
    assert run("timeline", "current", code=1)["code"] == "no_timeline"


def test_repl_json_batch_and_reconnection(monkeypatch):
    reads = []

    def status(b):
        reads.append(b)
        return {"connected": True}

    monkeypatch.setattr(Backend, "status", status)
    result = CliRunner().invoke(cli, ["--json"], input="status\nstatus\nexit\n")
    assert result.exit_code == 0
    assert [json.loads(s)["ok"] for s in result.output.splitlines()] == [True, True]
    assert reads[0] is not reads[1]


@pytest.mark.parametrize("line", ["unknown", 'project open "bad quote', "repl"])
def test_batch_stops_at_first_error(line):
    result = CliRunner().invoke(cli, ["--json"], input=f"{line}\nstatus\n")
    assert result.exit_code == 2
    assert json.loads(result.output)["error"]["code"] == "usage"


def test_help_version_and_readable_output(b):
    runner = CliRunner()
    assert "0.1.0" in runner.invoke(cli, ["--version"]).output
    assert "marker" in runner.invoke(cli, ["timeline", "--help"]).output
    assert "DaVinci Resolve Studio" in runner.invoke(cli, ["status"], obj=b).output
