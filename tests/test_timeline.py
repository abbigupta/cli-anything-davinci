from pathlib import Path


def test_timeline_commands(b, run):
    p = b.project
    p.GetTimelineCount.return_value = 1
    tl = p.GetTimelineByIndex.return_value
    tl.GetName.return_value = "Rough"
    b.pool.CreateEmptyTimeline.return_value = tl
    assert run("timeline", "list") == [{"index": 1, "name": "Rough"}]
    assert run("timeline", "create", "Rough") == {"name": "Rough"}
    assert run("timeline", "current") == {"name": "Main"}
    assert run("timeline", "select", 1) == {"index": 1, "name": "Rough"}
    p.SetCurrentTimeline.assert_called_with(tl)
    b.timeline.GetStartFrame.return_value = 0
    b.timeline.GetEndFrame.return_value = 42
    b.timeline.GetStartTimecode.return_value = "00:00:00:00"
    assert run("timeline", "info")["start_frame"] == 0


def test_append_resolves_before_editing(b, run, clip, item):
    assert (
        run("timeline", "append", "media-42", "absent", code=1)["code"] == "selection"
    )
    b.pool.AppendToTimeline.assert_not_called()
    b.pool.AppendToTimeline.return_value = [item]
    assert run("timeline", "append", "media-42")["item_ids"] == ["item-1"]
    b.pool.AppendToTimeline.assert_called_once_with([{"mediaPoolItem": clip}])


def test_tracks_clips_and_markers(b, run, item):
    tl = b.timeline
    tl.GetTrackName.return_value = "V1"
    tl.GetIsTrackEnabled.return_value = False
    assert run("timeline", "tracks") == [
        {"type": "video", "index": 1, "name": "V1", "enabled": False}
    ]
    assert run("timeline", "clips")[0]["id"] == "item-1"
    assert run("timeline", "marker", "add", 0, "Intro")["frame"] == 0
    tl.AddMarker.assert_called_once_with(0, "Blue", "Intro", "", 1, "")
    tl.GetMarkers.return_value = {32.0: {"name": "Later"}, 0.0: {"name": "Intro"}}
    assert [r["frame"] for r in run("timeline", "marker", "list")] == [0, 32]


def test_edl_export_constants(b, run, tmp_path):
    b.resolve.EXPORT_EDL, b.resolve.EXPORT_NONE = 11, 0

    def export(path, format_id, subtype):
        assert (format_id, subtype) == (11, 0)
        Path(path).write_text("TITLE: DEMO")
        return True

    b.timeline.Export.side_effect = export
    assert run("timeline", "export", tmp_path / "out.edl")["bytes"] == 11
    assert (
        run("timeline", "export", tmp_path / "out.otio", code=1)["code"]
        == "unsupported"
    )


def test_advanced_clip_and_tracks(b, run, item, tmp_path):
    item.GetProperties.side_effect = [{"ZoomX": 1}, {"ZoomX": 1}, {"ZoomX": 1.5}]
    assert run("clip", "properties", "item-1") == {"ZoomX": 1}
    assert run("clip", "set", "item-1", "ZoomX", "1.5") == {"ZoomX": 1.5}
    item.SetProperties.assert_called_once_with({"ZoomX": 1.5})
    item.GetFusionCompNameList.return_value = ["Composition 1"]
    assert run("clip", "fusion", "item-1", "--add")["compositions"] == ["Composition 1"]
    item.AddFusionComp.assert_called_once_with()
    graph = item.GetNodeGraph.return_value
    graph.GetLUT.return_value = "Film.cube"
    assert run("color", "lut", "item-1", 1, "Film.cube")["lut"] == "Film.cube"
    graph.SetLUT.assert_called_once_with(1, "Film.cube")
    grade = tmp_path / "test.drx"
    grade.touch()
    run("color", "grade", "item-1", grade, code=2)
    graph.ApplyGradeFromDRX.assert_not_called()
    run("color", "grade", "item-1", grade, "--yes", "--mode", 2)
    graph.ApplyGradeFromDRX.assert_called_once_with(str(grade), 2)
    run("timeline", "track", "add", "audio")
    b.timeline.AddTrack.assert_called_once_with("audio", {"audioType": "stereo"})
    run("timeline", "track", "enable", "audio", 1, "off")
    b.timeline.SetTrackEnable.assert_called_once_with("audio", 1, False)
