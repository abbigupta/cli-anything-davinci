"""Console script, JSON contract and interactive shell."""

import logging
import shlex
import sys
from importlib.metadata import version
from typing import Any

import click

from .core.clip import clip, color
from .core.media import media
from .core.project import project
from .core.render import render
from .core.timeline import timeline
from .utils.davinci_backend import Backend, ResolveError
from .utils.output import show
from .utils.repl_skin import ReplSkin

VERSION = version("cli-anything-davinci")


class Root(click.Group):
    def main(self, args=None, standalone_mode=True, **kwargs) -> int:
        # Accept --json anywhere before the literal argument delimiter.
        args = list(sys.argv[1:] if args is None else args)
        boundary = args.index("--") if "--" in args else len(args)
        machine = "--json" in args[:boundary]
        if machine:
            args = [
                "--json",
                *(a for a in args[:boundary] if a != "--json"),
                *args[boundary:],
            ]
        try:
            result = super().main(args=args, standalone_mode=False, **kwargs)
            if isinstance(result, (dict, list)):
                show(result, machine)
            if isinstance(result, int) and result:
                if standalone_mode:
                    raise SystemExit(result)
                return result
            return 0
        except click.ClickException as exc:
            status, code, message, details = (
                exc.exit_code,
                "usage",
                exc.format_message(),
                {},
            )
        except ResolveError as exc:
            status = 3 if exc.code == "unavailable" else 1
            code, message, details = exc.code, str(exc), exc.details
        except (KeyboardInterrupt, click.Abort):
            status, code, message, details = (
                130,
                "interrupted",
                "Command interrupted.",
                {},
            )
        except OSError as exc:
            status, code, message, details = 1, "io_error", str(exc), {}
        except Exception as exc:
            logging.getLogger(__name__).debug(
                "Unexpected command failure", exc_info=True
            )
            status, code, message, details = 1, "internal_error", str(exc), {}
        show(
            {"code": code, "message": message, "details": details}, machine, failed=True
        )
        if standalone_mode:
            raise SystemExit(status)
        return status


@click.group(
    cls=Root,
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.option(
    "--json", "machine", is_flag=True, help="Emit one JSON response per command."
)
@click.option("--verbose", is_flag=True, help="Log SDK calls to stderr.")
@click.version_option(VERSION)
@click.pass_context
def cli(ctx: click.Context, machine: bool, verbose: bool) -> None:
    """Control the running DaVinci Resolve session. No arguments opens the REPL."""
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    if ctx.obj is None:
        ctx.obj = Backend()
    if ctx.invoked_subcommand is None:
        ctx.invoke(repl)


@cli.command()
@click.pass_obj
def status(b: Backend) -> dict:
    """Report the connected Resolve product and version."""
    return b.status()


@cli.command()
@click.pass_obj
def doctor(b: Backend) -> dict:
    """Inspect SDK discovery and verify access to the project manager."""
    report = b.diagnostics()
    try:
        report.update(b.status())
        _ = b.manager
    except ResolveError as exc:
        exc.details.update(report, connected=False)
        raise
    return report


@cli.command()
@click.pass_context
def repl(ctx: click.Context) -> None:
    """Read commands until exit, quit or EOF. Pipe commands with --json for JSON Lines."""
    if ctx.find_root().meta.get("inside_repl"):
        raise click.UsageError("Already in the REPL. Enter a subcommand or exit.")
    machine = ctx.find_root().params["machine"]
    interactive = sys.stdin.isatty() and not machine
    skin = ReplSkin("davinci", VERSION) if interactive else None
    prompt = None
    if skin:
        skin.skill_install_cmd = "npx skills add abbigupta/cli-anything-davinci --skill cli-anything-davinci -g -y"
        skin.print_banner()
        prompt = skin.create_prompt_session()
    while True:
        try:
            line = skin.get_input(prompt) if skin else input()
        except EOFError:
            break
        except KeyboardInterrupt:
            if not skin:
                raise
            continue
        if line.strip() in {"quit", "exit"}:
            break
        try:
            lexer = shlex.shlex(line, posix=True)
            lexer.whitespace_split, lexer.escape, lexer.commenters = True, "", ""
            args = list(lexer)
        except ValueError as exc:
            if not interactive:
                raise click.UsageError(str(exc)) from exc
            show(
                {"code": "usage", "message": str(exc), "details": {}},
                machine,
                failed=True,
            )
            continue
        if not args:
            continue
        if args == ["help"]:
            args = ["--help"]
        if machine:
            args.insert(0, "--json")
        with click.Context(cli) as parent:
            parent.meta["inside_repl"] = True
            status = cli.main(args, standalone_mode=False, parent=parent)
            if status and not interactive:
                ctx.exit(status)
    if skin:
        skin.print_goodbye()


for group in (project, media, timeline, render, clip, color):
    cli.add_command(group)


def main() -> Any:
    return cli(prog_name="cli-anything-davinci")
