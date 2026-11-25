import json
from pathlib import Path

import click

from ..utils.davinci_backend import Backend, read
from .common import FILE, INDEX
from .timeline import find_item


@click.group()
def clip() -> None:
    """Work on a timeline item using an ID from timeline clips."""


@clip.command()
@click.argument("item_id")
@click.pass_obj
def properties(b: Backend, item_id: str) -> dict:
    """Read this timeline item's exposed properties."""
    return read(find_item(b.timeline, item_id), "GetProperties")


@clip.command("set")
@click.argument("item_id")
@click.argument("key")
@click.argument("value")
@click.pass_obj
def set_property(b: Backend, item_id: str, key: str, value: str) -> dict:
    """Set one exposed property to a JSON value, e.g. ZoomX 1.2."""
    try:
        parsed = json.loads(value)
    except ValueError as exc:
        raise click.BadParameter("Supply a JSON value.", param_hint="value") from exc
    item = find_item(b.timeline, item_id)
    if key not in read(item, "GetProperties"):
        raise click.BadParameter(f"Unknown property {key!r}. Inspect clip properties.")
    read(item, "SetProperties", {key: parsed})
    return {key: read(item, "GetProperties")[key]}


@clip.command("fusion")
@click.argument("item_id")
@click.option("--add", is_flag=True, help="Create a new Fusion composition first.")
@click.pass_obj
def fusion(b: Backend, item_id: str, add: bool) -> dict:
    """List Fusion compositions attached to a timeline item."""
    item = find_item(b.timeline, item_id)
    if add:
        read(item, "AddFusionComp")
    return {"compositions": read(item, "GetFusionCompNameList")}


@click.group()
def color() -> None:
    """Grade one timeline item on its first node graph layer."""


@color.command()
@click.argument("item_id")
@click.argument("node", type=INDEX)
@click.argument("lut")
@click.pass_obj
def lut(b: Backend, item_id: str, node: int, lut: str) -> dict:
    """Apply a Resolve-discovered LUT by path to a one-based node."""
    graph = read(find_item(b.timeline, item_id), "GetNodeGraph")
    read(graph, "SetLUT", node, lut)
    return {"item_id": item_id, "node": node, "lut": read(graph, "GetLUT", node)}


@color.command()
@click.argument("item_id")
@click.argument("path", type=FILE)
@click.option(
    "--mode",
    type=click.IntRange(0, 2),
    default=0,
    show_default=True,
    help="0 no keyframes, 1 source timecode, 2 start frames.",
)
@click.option("--yes", is_flag=True, help="Confirm replacing the existing grade.")
@click.pass_obj
def grade(b: Backend, item_id: str, path: Path, mode: int, yes: bool) -> dict:
    """Replace the selected graph with a grade from a .drx still."""
    if not yes:
        raise click.UsageError("Use --yes to replace the existing grade.")
    if path.suffix.lower() != ".drx":
        raise click.BadParameter("Use a .drx grade file.")
    graph = read(find_item(b.timeline, item_id), "GetNodeGraph")
    read(graph, "ApplyGradeFromDRX", str(path), mode)
    return {"item_id": item_id, "grade": str(path)}
