from pathlib import Path

import click

from ..utils.davinci_backend import Backend, read
from .common import FILE, OUTPUT, export_file


@click.group()
def project() -> None:
    """Manage projects in the active project library folder."""


@project.command("list")
@click.pass_obj
def list_projects(b: Backend) -> list:
    """List project names in the current library folder."""
    return sorted(read(b.manager, "GetProjectListInCurrentFolder"))


@project.command()
@click.pass_obj
def current(b: Backend) -> dict:
    """Show the active project."""
    return {"name": read(b.project, "GetName")}


@project.command()
@click.argument("name")
@click.pass_obj
def create(b: Backend, name: str) -> dict:
    """Create and activate a project with a unique name."""
    obj = read(b.manager, "CreateProject", name)
    return {"name": read(obj, "GetName")}


@project.command("open")
@click.argument("name")
@click.pass_obj
def open_project(b: Backend, name: str) -> dict:
    """Load a project by its exact name."""
    obj = read(b.manager, "LoadProject", name)
    return {"name": read(obj, "GetName")}


@project.command()
@click.pass_obj
def save(b: Backend) -> dict:
    """Save the current project."""
    name = read(b.project, "GetName")
    read(b.manager, "SaveProject")
    return {"saved": name}


@project.command()
@click.option(
    "--yes", is_flag=True, help="Confirm closing and discarding unsaved edits."
)
@click.pass_obj
def close(b: Backend, yes: bool) -> dict:
    """Close the current project without saving."""
    if not yes:
        raise click.UsageError("Save edits first, then use project close --yes.")
    name = read(b.project, "GetName")
    read(b.manager, "CloseProject", b.project)
    return {"closed": name}


@project.command("export")
@click.argument("path", type=OUTPUT)
@click.pass_obj
def export_project(b: Backend, path: Path) -> dict:
    """Export the active project to a new .drp file."""
    name = read(b.project, "GetName")
    return export_file(
        path, ".drp", lambda dest: read(b.manager, "ExportProject", name, dest)
    )


@project.command("import")
@click.argument("path", type=FILE)
@click.option("--name", help="Assign the imported project a new name.")
@click.pass_obj
def import_project(b: Backend, path: Path, name: str | None) -> dict:
    """Import a .drp into the current library folder."""
    if path.suffix.lower() != ".drp":
        raise click.BadParameter("Expected a .drp project.")
    args = [name] if name else []
    read(b.manager, "ImportProject", str(path), *args)
    return {"imported": str(path)}
