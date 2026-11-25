from unittest.mock import Mock

import pytest


def test_recursive_media_list_search(b, clip, run):
    root = b.pool.GetRootFolder.return_value
    child = Mock()
    child.GetName.return_value = "Shots"
    child.GetClipList.return_value = [clip]
    child.GetSubFolderList.return_value = []
    root.GetClipList.return_value = []
    root.GetSubFolderList.return_value = [child]
    rows = run("media", "list")
    assert rows == [{"id": "media-42", "name": "Take 1", "folder": ["Master", "Shots"]}]
    assert run("media", "search", "tAkE") == rows
    assert run("media", "search", "XYZ") == []


@pytest.mark.parametrize("selector", ["Take 1", "media-42", "/clips/take-1.mov"])
def test_lookup(clip, run, selector):
    assert run("media", "info", selector)["properties"] == {
        "File Path": "/clips/take-1.mov"
    }


def test_ambiguous_name(b, clip, run):
    b.pool.GetRootFolder.return_value.GetClipList.return_value = [clip, clip]
    assert run("media", "info", "Take 1", code=1)["code"] == "selection"


def test_batch_import_partial_failure(b, clip, run, tmp_path):
    paths = [tmp_path / "first.mov", tmp_path / "second.mov"]
    for p in paths:
        p.touch()
    b.pool.ImportMedia.side_effect = [[clip], []]
    error = run("media", "import", *paths, code=1)
    assert error["details"] == {
        "path": str(paths[1]),
        "imported": [{"id": "media-42", "name": "Take 1"}],
    }
    assert b.pool.ImportMedia.call_args_list[0].args == ([{"FilePath": str(paths[0])}],)


def test_folder_commands(b, run):
    root = b.pool.GetCurrentFolder.return_value
    root.GetName.return_value = "Master"
    child = b.pool.AddSubFolder.return_value
    child.GetName.return_value = "Shots"
    root.GetSubFolderList.return_value = [child]
    assert run("media", "folder", "create", "Shots") == {"name": "Shots"}
    b.pool.AddSubFolder.assert_called_once_with(root, "Shots")
    assert run("media", "folder", "list") == {"folder": "Master", "children": ["Shots"]}
