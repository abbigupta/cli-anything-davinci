from pathlib import Path

import click

from ..utils.davinci_backend import Backend, ResolveError, flag, invoke, read


@click.group()
def render() -> None:
    """Configure delivery, queue timelines and monitor rendering."""


@render.command()
@click.pass_obj
def formats(b: Backend) -> dict:
    """List format descriptions and their format IDs."""
    return read(b.project, "GetRenderFormats")


@render.command()
@click.argument("format_id")
@click.pass_obj
def codecs(b: Backend, format_id: str) -> dict:
    """List codec descriptions and IDs for a format ID such as mov."""
    return read(b.project, "GetRenderCodecs", format_id)


@render.command()
@click.pass_obj
def presets(b: Backend) -> list:
    """List the render presets available in this installation."""
    return read(b.project, "GetRenderPresetList")


@render.command()
@click.option("--preset", help="Load this Resolve render preset first.")
@click.option("--format", "format_id", help="Format ID from render formats.")
@click.option("--codec", help="Codec ID from render codecs.")
@click.option(
    "--directory",
    type=click.Path(
        exists=True, file_okay=False, writable=True, resolve_path=True, path_type=Path
    ),
)
@click.option("--name", help="Output base name.")
@click.option("--all-frames", is_flag=True, help="Render the entire timeline.")
@click.pass_obj
def configure(
    b: Backend,
    preset: str | None,
    format_id: str | None,
    codec: str | None,
    directory: Path | None,
    name: str | None,
    all_frames: bool,
) -> dict:
    """Apply a preset, format/codec pair and/or output settings."""
    if bool(format_id) != bool(codec):
        raise click.UsageError("Supply --format and --codec together.")
    if not any([preset, format_id, directory, name, all_frames]):
        raise click.UsageError("Provide at least one render setting.")
    if name and (name in {".", ".."} or "/" in name or "\\" in name):
        raise click.BadParameter(
            "Use a filename without directory components.", param_hint="--name"
        )
    settings = {}
    if directory:
        settings["TargetDir"] = str(directory)
    if name:
        settings["CustomName"] = name
    if all_frames:
        settings["SelectAllFrames"] = True
    applied = {}
    try:
        if preset:
            read(b.project, "LoadRenderPreset", preset)
            applied["preset"] = preset
        if format_id:
            read(b.project, "SetCurrentRenderFormatAndCodec", format_id, codec)
            applied.update(format=format_id, codec=codec)
        if settings:
            read(b.project, "SetRenderSettings", settings)
            applied.update(settings)
    except ResolveError as exc:
        exc.details["applied"] = applied
        raise
    return applied


@render.command()
@click.pass_obj
def queue(b: Backend) -> dict:
    """Queue the active timeline using current delivery settings."""
    timeline = read(b.timeline, "GetName")
    job_id = read(b.project, "AddRenderJob")
    if not isinstance(job_id, str) or not job_id:
        raise ResolveError(
            "api_error",
            "Resolve returned no job ID. Inspect render status before retrying.",
        )
    return {"job_id": job_id, "timeline": timeline}


@render.command()
@click.argument("job_ids", nargs=-1)
@click.option("--all", "all_jobs", is_flag=True, help="Start the entire project queue.")
@click.pass_obj
def start(b: Backend, job_ids: tuple[str, ...], all_jobs: bool) -> dict:
    """Start specific job IDs and return immediately."""
    if bool(job_ids) == all_jobs:
        raise click.UsageError("Supply job IDs or --all.")
    queued = [job["JobId"] for job in read(b.project, "GetRenderJobList")]
    if not queued or set(job_ids).difference(queued):
        raise ResolveError(
            "selection", "Queue is empty or a job ID is unknown. Inspect render status."
        )
    if all_jobs:
        read(b.project, "StartRendering")
    else:
        read(b.project, "StartRendering", list(job_ids), False)
    return {"started": "all" if all_jobs else list(job_ids)}


@render.command()
@click.argument("job_id", required=False)
@click.pass_obj
def status(b: Backend, job_id: str | None) -> dict:
    """Show a single job's progress or list the whole queue."""
    if job_id:
        state = read(b.project, "GetRenderJobStatus", job_id)
        if not state:
            raise ResolveError(
                "selection", f"No status for job {job_id!r}. Inspect render status."
            )
        return {"job_id": job_id, "status": state}
    return {
        "rendering": flag(b.project, "IsRenderingInProgress"),
        "jobs": read(b.project, "GetRenderJobList"),
    }


@render.command()
@click.option("--yes", is_flag=True, help="Confirm stopping all active renders.")
@click.pass_obj
def cancel(b: Backend, yes: bool) -> dict:
    """Stop active rendering for this project. Queued jobs are retained."""
    if not yes:
        raise click.UsageError("Use render cancel --yes to stop active renders.")
    if not flag(b.project, "IsRenderingInProgress"):
        raise ResolveError("idle", "There is no active render.")
    # StopRendering has a void return. Confirm with the documented state getter.
    invoke(b.project, "StopRendering")
    if flag(b.project, "IsRenderingInProgress"):
        raise ResolveError(
            "still_rendering",
            "Stop requested. Resolve is still rendering. Check render status.",
        )
    return {"rendering": False}
