import pytest


def test_render_setup(b, run, tmp_path):
    p = b.project
    p.GetRenderFormats.return_value = {"QuickTime": "mov"}
    p.GetRenderCodecs.return_value = {"ProRes": "ProRes422"}
    p.GetRenderPresetList.return_value = ["Archive"]
    assert run("render", "formats") == {"QuickTime": "mov"}
    assert run("render", "codecs", "mov") == {"ProRes": "ProRes422"}
    p.GetRenderCodecs.assert_called_once_with("mov")
    assert run("render", "presets") == ["Archive"]
    run(
        "render",
        "configure",
        "--preset",
        "Archive",
        "--mode",
        "single",
        "--format",
        "mov",
        "--codec",
        "ProRes422",
        "--directory",
        tmp_path,
        "--name",
        "Cut",
        "--all-frames",
    )
    p.LoadRenderPreset.assert_called_once_with("Archive")
    p.SetCurrentRenderMode.assert_called_once_with(1)
    p.SetCurrentRenderFormatAndCodec.assert_called_once_with("mov", "ProRes422")
    p.SetRenderSettings.assert_called_once_with(
        {"TargetDir": str(tmp_path), "CustomName": "Cut", "SelectAllFrames": True}
    )


def test_partial_configuration(b, run):
    b.project.SetCurrentRenderFormatAndCodec.return_value = False
    error = run(
        "render",
        "configure",
        "--preset",
        "Draft",
        "--format",
        "mov",
        "--codec",
        "bad",
        code=1,
    )
    assert error["details"]["applied"] == {"preset": "Draft"}


def test_jobs_use_string_ids_and_start_asynchronously(b, run):
    p = b.project
    p.AddRenderJob.return_value = "job-A"
    p.GetRenderJobList.return_value = [{"JobId": "job-A"}]
    p.GetRenderJobStatus.return_value = {
        "JobStatus": "Rendering",
        "CompletionPercentage": 50,
    }
    p.IsRenderingInProgress.return_value = True
    assert run("render", "queue") == {"job_id": "job-A", "timeline": "Main"}
    run("render", "start", "missing", code=1)
    run("render", "start", code=2)
    p.StartRendering.assert_not_called()
    assert run("render", "start", "job-A")["started"] == ["job-A"]
    p.StartRendering.assert_called_once_with(["job-A"], False)
    run("render", "start", "--all")
    p.StartRendering.assert_called_with(["job-A"], False)
    assert run("render", "status")["rendering"] is True
    assert run("render", "status", "job-A")["status"]["JobStatus"] == "Rendering"


def test_invalid_queue_and_unknown_status(b, run):
    b.project.AddRenderJob.return_value = ""
    b.project.GetRenderJobStatus.return_value = {}
    assert run("render", "queue", code=1)["code"] == "api_error"
    assert run("render", "status", "absent", code=1)["code"] == "selection"


@pytest.mark.parametrize(
    ("states", "exit_code"),
    [([True, False], 0), ([False], 1), ([True, True], 1), ([True, None], 1)],
)
def test_cancel_checks_observed_state(b, run, states, exit_code):
    run("render", "cancel", code=2)
    b.project.StopRendering.assert_not_called()
    b.project.StopRendering.return_value = None
    b.project.IsRenderingInProgress.side_effect = states
    run("render", "cancel", "--yes", code=exit_code)
    assert b.project.StopRendering.call_count == int(states[0])
