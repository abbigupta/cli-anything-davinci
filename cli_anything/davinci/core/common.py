from collections.abc import Callable
from pathlib import Path
from shutil import copyfileobj
from tempfile import TemporaryDirectory

import click

from ..utils.davinci_backend import ResolveError

FILE = click.Path(
    exists=True, dir_okay=False, readable=True, resolve_path=True, path_type=Path
)
OUTPUT = click.Path(dir_okay=False, resolve_path=True, path_type=Path)
INDEX = click.IntRange(min=1)
TRACK = click.Choice(["video", "audio", "subtitle"])


def export_file(path: Path, suffix: str, write: Callable[[str], object]) -> dict:
    if path.suffix.lower() != suffix or not path.parent.is_dir():
        raise click.BadParameter(f"Use a {suffix} file in an existing directory.")
    if path.exists():
        raise ResolveError(
            "exists", f"Choose a new output path. {path} already exists."
        )
    with TemporaryDirectory(dir=path.parent) as staging:
        output = Path(staging) / path.name
        write(str(output))
        if not output.is_file() or not output.stat().st_size:
            raise ResolveError(
                "export_failed", "Resolve did not write a nonempty export."
            )
        with output.open("rb") as src, path.open("xb") as dst:
            try:
                copyfileobj(src, dst)
            except OSError:
                dst.close()
                path.unlink()
                raise
    return {"path": str(path), "bytes": path.stat().st_size}
