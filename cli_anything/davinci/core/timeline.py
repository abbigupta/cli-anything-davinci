from collections.abc import Iterator
from pathlib import Path
from typing import Any

import click

from ..utils.davinci_backend import Backend, ResolveError, flag, read
from .common import INDEX, OUTPUT, TRACK, export_file
from .media import find_clip


def tracks_of(tl: Any) -> Iterator[tuple[str, int]]:
    for kind in TRACK.choices:
        for index in range(1, read(tl, "GetTrackCount", kind) + 1):
            yield kind, index


def items_of(tl: Any) -> Iterator[tuple[str, int, Any]]:
    for kind, index in tracks_of(tl):
        for item in read(tl, "GetItemListInTrack", kind, index):
            yield kind, index, item


def find_item(tl: Any, item_id: str) -> Any:
    for _, _, item in items_of(tl):
        if read(item, "GetUniqueId") == item_id:
            return item
    raise ResolveError("selection", "Unknown timeline clip ID. Use timeline clips.")


@click.group()
def timeline() -> None:
    """Edit the active project's timelines."""


@timeline.command("list")
@click.pass_obj
def timelines(b: Backend) -> list:
    """List timeline names and their one-based indexes."""
    p = b.project
    return [
        {"index": i, "name": read(read(p, "GetTimelineByIndex", i), "GetName")}
        for i in range(1, read(p, "GetTimelineCount") + 1)
    ]


@timeline.command()
@click.argument("name")
@click.pass_obj
def create(b: Backend, name: str) -> dict:
    """Create an empty timeline and select it."""
    tl = read(b.pool, "CreateEmptyTimeline", name)
    try:
        read(b.project, "SetCurrentTimeline", tl)
    except ResolveError as exc:
        exc.details["created"] = name
        raise
    return {"name": read(tl, "GetName")}


@timeline.command()
@click.pass_obj
def current(b: Backend) -> dict:
    """Show the current timeline name."""
    return {"name": read(b.timeline, "GetName")}


@timeline.command()
@click.argument("index", type=INDEX)
@click.pass_obj
def select(b: Backend, index: int) -> dict:
    """Activate a timeline by its index from timeline list."""
    tl = read(b.project, "GetTimelineByIndex", index)
    read(b.project, "SetCurrentTimeline", tl)
    return {"index": index, "name": read(tl, "GetName")}


@timeline.command()
@click.argument("selectors", nargs=-1, required=True)
@click.pass_obj
def append(b: Backend, selectors: tuple[str, ...]) -> dict:
    """Append imported clips by ID, name or source path, in argument order."""
    tl = b.timeline
    name = read(tl, "GetName")
    sources = [find_clip(b.pool, s) for s in selectors]
    ids = []
    for selector, clip in zip(selectors, sources):
        try:
            added = read(b.pool, "AppendToTimeline", [{"mediaPoolItem": clip}])
            if not added:
                raise ResolveError(
                    "rejected", f"Resolve appended no items for {selector!r}."
                )
            ids.extend(read(item, "GetUniqueId") for item in added)
        except ResolveError as exc:
            exc.details.update(selector=selector, appended_ids=ids)
            raise
    return {"timeline": name, "item_ids": ids}


@timeline.command()
@click.pass_obj
def info(b: Backend) -> dict:
    """Read the timeline frame range and start timecode."""
    tl = b.timeline
    return {
        "name": read(tl, "GetName"),
        "start_frame": read(tl, "GetStartFrame"),
        "end_frame": read(tl, "GetEndFrame"),
        "start_timecode": read(tl, "GetStartTimecode"),
    }


@timeline.command()
@click.pass_obj
def tracks(b: Backend) -> list:
    """List video, audio and subtitle tracks."""
    tl = b.timeline
    return [
        {
            "type": k,
            "index": i,
            "name": read(tl, "GetTrackName", k, i),
            "enabled": flag(tl, "GetIsTrackEnabled", k, i),
        }
        for k, i in tracks_of(tl)
    ]


@timeline.command()
@click.pass_obj
def clips(b: Backend) -> list:
    """List timeline item IDs, track positions and frame ranges."""
    return [
        {
            "id": read(item, "GetUniqueId"),
            "name": read(item, "GetName"),
            "track_type": kind,
            "track_index": i,
            "start": read(item, "GetStart"),
            "end": read(item, "GetEnd"),
        }
        for kind, i, item in items_of(b.timeline)
    ]


@timeline.group()
def marker() -> None:
    """Manage timeline markers by frame offset."""


@marker.command()
@click.argument("frame", type=click.IntRange(min=0))
@click.argument("name")
@click.option("--color", default="Blue", show_default=True)
@click.option("--note", default="")
@click.option("--duration", type=INDEX, default=1, show_default=True)
@click.pass_obj
def add(
    b: Backend, frame: int, name: str, color: str, note: str, duration: int
) -> dict:
    """Add a marker at a frame offset from the timeline start."""
    read(b.timeline, "AddMarker", frame, color, name, note, duration, "")
    return {"frame": frame, "name": name}


@marker.command("list")
@click.pass_obj
def markers(b: Backend) -> list:
    """List markers in frame order."""
    values = read(b.timeline, "GetMarkers")
    return [{"frame": frame, **values[frame]} for frame in sorted(values, key=float)]


@timeline.command("export")
@click.argument("path", type=OUTPUT)
@click.pass_obj
def export(b: Backend, path: Path) -> dict:
    """Write a new .drt, .otio, .csv or .edl file."""
    suffix = path.suffix.lower()
    formats = {
        ".drt": "EXPORT_DRT",
        ".otio": "EXPORT_OTIO",
        ".csv": "EXPORT_TEXT_CSV",
        ".edl": "EXPORT_EDL",
    }
    if suffix not in formats:
        raise click.BadParameter("Use a .drt, .otio, .csv or .edl extension.")
    args = [getattr(b.resolve, key, None) for key in (formats[suffix], "EXPORT_NONE")]
    if None in args:
        raise ResolveError(
            "unsupported", f"This Resolve build lacks an export constant for {suffix}."
        )
    return export_file(
        path, suffix, lambda dest: read(b.timeline, "Export", dest, *args)
    )


@timeline.group()
def track() -> None:
    """Add tracks or change their enabled state."""


@track.command("add")
@click.argument("kind", type=TRACK)
@click.pass_obj
def add_track(b: Backend, kind: str) -> dict:
    """Append a track. Audio tracks use stereo."""
    args = ["stereo"] if kind == "audio" else []
    read(b.timeline, "AddTrack", kind, *args)
    return {"added": kind}


@track.command("enable")
@click.argument("kind", type=TRACK)
@click.argument("index", type=INDEX)
@click.argument("state", type=click.Choice(["on", "off"]))
@click.pass_obj
def enable(b: Backend, kind: str, index: int, state: str) -> dict:
    """Enable or disable a track. Disabling audio mutes the track."""
    read(b.timeline, "SetTrackEnable", kind, index, state == "on")
    return {"type": kind, "index": index, "enabled": state == "on"}
