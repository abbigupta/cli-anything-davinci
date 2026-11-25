import json
from unittest.mock import Mock

import pytest
from click.testing import CliRunner

from cli_anything.davinci.davinci_cli import cli
from cli_anything.davinci.utils.davinci_backend import Backend


def pytest_addoption(parser):
    parser.addoption("--resolve", action="store_true", help="Run live Resolve tests.")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--resolve"):
        for item in items:
            if item.get_closest_marker("resolve"):
                item.add_marker(
                    pytest.mark.skip(reason="live backend requires --resolve")
                )


@pytest.fixture
def b():
    backend = Backend()
    backend.resolve = Mock(
        spec=[
            "GetVersionString",
            "GetProductName",
            "GetProjectManager",
            "EXPORT_EDL",
            "EXPORT_NONE",
        ]
    )
    backend.resolve.GetVersionString.return_value = "21.2.0"
    backend.resolve.GetProductName.return_value = "DaVinci Resolve Studio"
    backend.manager = backend.resolve.GetProjectManager.return_value
    backend.project = backend.manager.GetCurrentProject.return_value
    backend.project.GetName.return_value = "Demo"
    backend.pool = backend.project.GetMediaPool.return_value
    backend.timeline = backend.project.GetCurrentTimeline.return_value
    backend.timeline.GetName.return_value = "Main"
    return backend


@pytest.fixture
def run(b):
    def invoke(*args, code=0):
        result = CliRunner().invoke(cli, ["--json", *map(str, args)], obj=b)
        assert result.exit_code == code, result.output
        response = json.loads(result.output)
        assert response["ok"] is (code == 0)
        return response["data" if code == 0 else "error"]

    return invoke


@pytest.fixture
def clip(b):
    root = b.pool.GetRootFolder.return_value
    root.GetName.return_value = "Master"
    root.GetSubFolderList.return_value = []
    item = Mock(spec=["GetMediaId", "GetName", "GetClipProperty"])
    item.GetName.return_value = "Take 1"
    item.GetMediaId.return_value = "media-42"
    item.GetClipProperty.return_value = {"File Path": "/clips/take-1.mov"}
    root.GetClipList.return_value = [item]
    return item


@pytest.fixture
def item(b):
    tl = b.timeline
    tl.GetTrackCount.side_effect = lambda k: int(k == "video")
    clip = Mock()
    clip.GetUniqueId.return_value = "item-1"
    clip.GetName.return_value = "Shot"
    clip.GetStart.return_value = 10
    clip.GetEnd.return_value = 42
    tl.GetItemListInTrack.return_value = [clip]
    return clip
