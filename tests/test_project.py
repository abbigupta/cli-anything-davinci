from pathlib import Path

import pytest


def test_project_commands(b, run):
    pm = b.manager
    pm.GetProjectListInCurrentFolder.return_value = ["Z", "A"]
    pm.CreateProject.return_value.GetName.return_value = "New"
    pm.LoadProject.return_value.GetName.return_value = "Old"
    assert run("project", "list") == ["A", "Z"]
    assert run("project", "current") == {"name": "Demo"}
    assert run("project", "create", "New") == {"name": "New"}
    pm.CreateProject.assert_called_once_with("New")
    assert run("project", "open", "Old") == {"name": "Old"}
    pm.LoadProject.assert_called_once_with("Old")
    assert run("project", "save") == {"saved": "Demo"}
    assert run("project", "close", code=2)["code"] == "usage"
    pm.CloseProject.assert_not_called()
    assert run("project", "close", "--yes") == {"closed": "Demo"}
    pm.CloseProject.assert_called_once_with(b.project)


def test_rejected_project(b, run):
    b.manager.CreateProject.return_value = None
    assert run("project", "create", "Busy", code=1)["code"] == "rejected"


def test_project_roundtrip_arguments(b, run, tmp_path):
    path = tmp_path / "a.drp"

    def export(name, dest):
        assert name == "Demo"
        Path(dest).write_bytes(b"test-project")
        return True

    b.manager.ExportProject.side_effect = export
    assert run("project", "export", path)["bytes"] == 12
    assert path.read_bytes() == b"test-project"
    assert run("project", "export", path, code=1)["code"] == "exists"
    assert run("project", "import", path, "--name", "Copy")["imported"] == str(path)
    b.manager.ImportProject.assert_called_once_with(str(path), "Copy")


@pytest.mark.parametrize("reply", [True, False])
def test_no_empty_exports(b, run, tmp_path, reply):
    path = tmp_path / "a.drp"
    b.manager.ExportProject.return_value = reply
    assert run("project", "export", path, code=1)["code"] in {
        "rejected",
        "export_failed",
    }
    assert not path.exists()
