from collections.abc import Iterator
from pathlib import Path
from typing import Any

import click

from ..utils.davinci_backend import Backend, ResolveError, read
from .common import FILE


def clips(pool: Any) -> Iterator[tuple[Any, dict]]:
    """Walk bins in display order. Keep folder names as separate path components."""

    def walk(folder: Any, parents: list[str]) -> Iterator[tuple[Any, dict]]:
        names = [*parents, read(folder, "GetName")]
        for clip in read(folder, "GetClipList"):
            yield (
                clip,
                {
                    "id": read(clip, "GetMediaId"),
                    "name": read(clip, "GetName"),
                    "folder": names,
                },
            )
        for child in read(folder, "GetSubFolderList"):
            yield from walk(child, names)

    yield from walk(read(pool, "GetRootFolder"), [])


def find_clip(pool: Any, selector: str) -> Any:
    matches = []
    source = Path(selector).expanduser().resolve()
    for clip, row in clips(pool):
        if row["id"] == selector:
            return clip
        path = read(clip, "GetClipProperty").get("File Path")
        if row["name"] == selector or (path and Path(path).resolve() == source):
            matches.append(clip)
    if len(matches) != 1:
        raise ResolveError(
            "selection",
            f"{len(matches)} pool clips matched {selector!r}. Use an ID from media list.",
        )
    return matches[0]


@click.group()
def media() -> None:
    """Import and inspect media pool clips and bins."""


@media.command("list")
@click.pass_obj
def list_media(b: Backend) -> list:
    """List clips and media IDs across all bins."""
    return [row for _, row in clips(b.pool)]


@media.command()
@click.argument("query")
@click.pass_obj
def search(b: Backend, query: str) -> list:
    """Find clips whose names contain QUERY (case insensitive)."""
    return [
        row for _, row in clips(b.pool) if query.casefold() in row["name"].casefold()
    ]


@media.command()
@click.argument("selector")
@click.pass_obj
def info(b: Backend, selector: str) -> dict:
    """Read properties by media ID, exact name or imported file path."""
    clip = find_clip(b.pool, selector)
    return {
        "id": read(clip, "GetMediaId"),
        "name": read(clip, "GetName"),
        "properties": read(clip, "GetClipProperty"),
    }


@media.command("import")
@click.argument("paths", nargs=-1, required=True, type=FILE)
@click.pass_obj
def import_media(b: Backend, paths: tuple[Path, ...]) -> list:
    """Import files into the current bin in argument order."""
    imported = []
    for path in paths:
        try:
            items = read(b.pool, "ImportMedia", [{"FilePath": str(path)}])
            if not items:
                raise ResolveError(
                    "rejected",
                    f"Resolve imported no clips from {path}. Check the file and codec.",
                )
            imported.extend(
                {"id": read(c, "GetMediaId"), "name": read(c, "GetName")} for c in items
            )
        except ResolveError as exc:
            exc.details.update(path=str(path), imported=imported)
            raise
    return imported


@media.group()
def folder() -> None:
    """Work with the media pool's current bin."""


@folder.command("list")
@click.pass_obj
def folders(b: Backend) -> dict:
    """List direct children of the current bin."""
    parent = read(b.pool, "GetCurrentFolder")
    return {
        "folder": read(parent, "GetName"),
        "children": [read(f, "GetName") for f in read(parent, "GetSubFolderList")],
    }


@folder.command()
@click.argument("name")
@click.pass_obj
def create(b: Backend, name: str) -> dict:
    """Create a child bin under the current bin."""
    item = read(b.pool, "AddSubFolder", read(b.pool, "GetCurrentFolder"), name)
    return {"name": read(item, "GetName")}
