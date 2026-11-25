"""Opt-in subprocess tests. Resolve owns the media, edit, export and render."""

import json
import os
import shutil
import subprocess
import time
from uuid import uuid4

import pytest

from cli_anything.davinci.utils.davinci_backend import Backend

pytestmark = pytest.mark.resolve


def command(*args):
    exe = shutil.which("cli-anything-davinci")
    assert exe, "Install the package and activate its virtual environment."
    result = subprocess.run(
        [exe, "--json", *map(str, args)],
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"]
    return payload["data"]


def test_live_connection():
    assert command("doctor")["connected"]


@pytest.fixture
def scratch():
    pm = Backend().manager
    db = pm.GetCurrentDatabase()
    expected = os.getenv("DAVINCI_TEST_LIBRARY")
    assert expected and db["DbName"] == expected, (
        "Select the dedicated DAVINCI_TEST_LIBRARY in Resolve first."
    )
    folder = pm.GetCurrentFolder()
    previous = pm.GetCurrentProject()
    anchor = "CLI-Anything Test Anchor"
    assert not previous or previous.GetName() == anchor, (
        f"Open the project manager or a saved, empty '{anchor}' in the dedicated library."
    )
    if previous:
        assert not previous.IsRenderingInProgress(), "The scratch library is rendering."
    name = f"cli-anything-test-{uuid4().hex}"
    owned = []

    def guard():
        assert pm.GetCurrentDatabase() == db and pm.GetCurrentFolder() == folder, (
            "Test library or folder changed."
        )

    def active():
        guard()
        p = pm.GetCurrentProject()
        assert p and p.GetName() == name, (
            "The isolated test project is no longer active."
        )

    try:
        guard()
        assert command("project", "create", name)["name"] == name
        owned.append(name)
        active()
        yield name, active, owned
    finally:
        guard()
        current = pm.GetCurrentProject()
        if current and current.GetName() in owned:
            if current.IsRenderingInProgress():
                current.StopRendering()
                assert not current.IsRenderingInProgress(), (
                    "Render is still active. Retaining the scratch project."
                )
            assert pm.CloseProject(current)
        for created in reversed(owned):
            assert pm.DeleteProject(created), (
                f"Could not remove scratch project {created}"
            )
        if previous and owned and not pm.GetCurrentProject():
            assert pm.LoadProject(anchor)


def test_edit_export_render(scratch, tmp_path):
    name, active, owned = scratch

    def edit(*args):
        active()
        return command(*args)

    src = tmp_path / "red.mov"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=red:size=640x360:rate=24",
            "-t",
            "1",
            "-c:v",
            "prores_ks",
            "-pix_fmt",
            "yuv422p10le",
            str(src),
        ],
        check=True,
        timeout=60,
    )
    media = edit("media", "import", src)
    edit("timeline", "create", "Test Cut")
    edit("timeline", "append", media[0]["id"])
    assert edit("timeline", "clips")[0]["name"]
    edit("timeline", "marker", "add", 0, "Opening")
    assert edit("timeline", "marker", "list")[0]["name"] == "Opening"
    edit("project", "save")
    drp = tmp_path / "edit.drp"
    edit("project", "export", drp)
    otio = tmp_path / "cut.otio"
    edit("timeline", "export", otio)
    assert json.loads(otio.read_text(encoding="utf-8"))["tracks"]["children"]
    output = tmp_path / "delivery"
    output.mkdir()
    codec = os.getenv("DAVINCI_TEST_CODEC", "ProRes422")
    assert codec in edit("render", "codecs", "mov").values(), (
        "Set DAVINCI_TEST_CODEC to a supported mov video codec ID."
    )
    edit(
        "render",
        "configure",
        "--mode",
        "single",
        "--format",
        "mov",
        "--codec",
        codec,
        "--directory",
        output,
        "--name",
        "cut",
        "--all-frames",
    )
    job = edit("render", "queue")["job_id"]
    edit("render", "start", job)
    deadline = time.monotonic() + 180
    while True:
        status = edit("render", "status", job)["status"]
        if status["JobStatus"] == "Complete":
            break
        assert (
            status["JobStatus"] not in {"Failed", "Cancelled", "Canceled"}
            and time.monotonic() < deadline
        ), status
        time.sleep(1)
    movie = output / "cut.mov"
    probe = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_streams", "-of", "json", str(movie)],
        timeout=30,
    )
    assert any(s["codec_type"] == "video" for s in json.loads(probe)["streams"])
    rgb = subprocess.check_output(
        [
            "ffmpeg",
            "-v",
            "error",
            "-ss",
            "0.3",
            "-i",
            str(movie),
            "-frames:v",
            "1",
            "-vf",
            "scale=1:1",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-",
        ],
        timeout=30,
    )
    red, green, blue = rgb
    assert red > 120 and red > 2 * max(green, blue), rgb
    copy = name + "-import"
    edit("project", "import", drp, "--name", copy)
    owned.append(copy)
    assert copy in command("project", "list")
    command("project", "open", copy)
    assert command("timeline", "current")["name"] == "Test Cut"
