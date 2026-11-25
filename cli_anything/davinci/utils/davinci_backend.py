"""Discover the vendor SDK and call the live, dynamically typed Resolve objects."""

import importlib
import logging
import os
import platform
import plistlib
import sys
from functools import cached_property
from pathlib import Path
from typing import Any

LOG = logging.getLogger(__name__)
CONNECT_HINT = (
    "Start Resolve Studio, wait for startup, then enable Preferences > System > "
    "General > External scripting using > Local. Use 64-bit Python matching Resolve."
)


class ResolveError(Exception):
    def __init__(self, code: str, message: str, **details: Any):
        super().__init__(message)
        self.code = code
        self.details = details


def locations(system: str) -> tuple[list[Path], list[Path]]:
    vendor = Path("Blackmagic Design/DaVinci Resolve")
    if system == "Darwin":
        apps = [
            Path("/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents"),
            Path("/Applications/DaVinci Resolve.app/Contents"),
        ]
        scripts = [
            Path("/Library/Application Support") / vendor / "Developer/Scripting"
        ]
        return scripts + [p / "Resources/Developer/Scripting" for p in apps], [
            p / "Libraries/Fusion/fusionscript.so" for p in apps
        ]
    if system == "Windows":
        data = Path(os.getenv("PROGRAMDATA", "C:/ProgramData")) / vendor
        install = Path(os.getenv("ProgramFiles", "C:/Program Files")) / vendor
        return [data / "Support/Developer/Scripting"], [install / "fusionscript.dll"]
    if system == "Linux":
        roots = [Path("/opt/resolve"), Path("/home/resolve")]
        return [p / "Developer/Scripting" for p in roots], [
            p / "libs/Fusion/fusionscript.so" for p in roots
        ]
    return [], []


class Backend:
    def __init__(self) -> None:
        self.system = platform.system()
        scripts, libraries = locations(self.system)
        override = os.getenv("RESOLVE_SCRIPT_API")
        self.modules = [
            p if p.name == "Modules" else p / "Modules"
            for p in ([Path(override).expanduser()] if override else scripts)
        ]
        override = os.getenv("RESOLVE_SCRIPT_LIB")
        self.library = (
            Path(override).expanduser()
            if override
            else next((p for p in libraries if p.is_file()), None)
        )

    @cached_property
    def module_dir(self) -> Path | None:
        return next(
            (p for p in self.modules if (p / "DaVinciResolveScript.py").is_file()), None
        )

    def diagnostics(self) -> dict:
        report = {
            "platform": self.system,
            "python": platform.python_version(),
            "architecture": platform.machine(),
            "module_dirs": list(map(str, self.modules)),
            "module_dir": str(self.module_dir) if self.module_dir else None,
            "library": str(self.library) if self.library else None,
        }
        if self.system == "Darwin" and self.library:
            plist = self.library.parent.parent.parent / "Info.plist"
            if plist.is_file():
                with plist.open("rb") as f:
                    info = plistlib.load(f)
                report.update(
                    installed_version=info.get("CFBundleShortVersionString"),
                    bundle_id=info.get("CFBundleIdentifier"),
                )
        return report

    @cached_property
    def resolve(self) -> Any:
        if os.getenv("RESOLVE_SCRIPT_API") and not self.module_dir:
            raise ResolveError(
                "unavailable",
                "RESOLVE_SCRIPT_API must contain Modules/DaVinciResolveScript.py.",
            )
        if self.library:
            if not self.library.is_file():
                raise ResolveError(
                    "unavailable",
                    "RESOLVE_SCRIPT_LIB must point to the installed fusionscript library.",
                )
            os.environ["RESOLVE_SCRIPT_LIB"] = str(self.library.resolve())
        if self.module_dir:
            sys.path.insert(0, str(self.module_dir))
        try:
            module = importlib.import_module("DaVinciResolveScript")
            LOG.debug(
                "Loaded scripting module from %s", getattr(module, "__file__", None)
            )
            resolve = module.scriptapp("Resolve")
        except (ImportError, OSError, AttributeError, RuntimeError, SystemError) as exc:
            raise ResolveError(
                "unavailable",
                f"Could not load or connect to the Resolve SDK ({exc}). Set RESOLVE_SCRIPT_API and RESOLVE_SCRIPT_LIB. {CONNECT_HINT}",
            ) from exc
        finally:
            if self.module_dir:
                sys.path.remove(str(self.module_dir))
        if not resolve:
            raise ResolveError(
                "unavailable", f"The SDK returned no Resolve session. {CONNECT_HINT}"
            )
        return resolve

    @cached_property
    def manager(self) -> Any:
        return read(self.resolve, "GetProjectManager")

    @cached_property
    def project(self) -> Any:
        project = invoke(self.manager, "GetCurrentProject")
        if not project:
            raise ResolveError(
                "no_project", "Open or create a project in Resolve first."
            )
        return project

    @cached_property
    def pool(self) -> Any:
        return read(self.project, "GetMediaPool")

    @cached_property
    def timeline(self) -> Any:
        timeline = invoke(self.project, "GetCurrentTimeline")
        if not timeline:
            raise ResolveError("no_timeline", "Create or select a timeline first.")
        return timeline

    def status(self) -> dict:
        return {
            "connected": True,
            "product": read(self.resolve, "GetProductName"),
            "version": read(self.resolve, "GetVersionString"),
        }


def invoke(obj: Any, method: str, *args: Any) -> Any:
    try:
        fn = getattr(obj, method, None)
        if not callable(fn):
            raise ResolveError(
                "unsupported",
                f"{method} is unavailable in this Resolve version or edition.",
            )
        LOG.debug("Resolve.%s", method)
        return fn(*args)
    except (OSError, RuntimeError, SystemError, TypeError) as exc:
        raise ResolveError(
            "api_error", f"{method} failed ({exc}). Check the session with doctor."
        ) from exc


def read(obj: Any, method: str, *args: Any) -> Any:
    result = invoke(obj, method, *args)
    if result is None or result is False:
        raise ResolveError(
            "rejected",
            f"Resolve rejected {method}. Check the active selection, arguments, and edition.",
        )
    return result


def flag(obj: Any, method: str, *args: Any) -> bool:
    value = invoke(obj, method, *args)
    if not isinstance(value, bool):
        raise ResolveError(
            "api_error", f"{method} returned no boolean state. Run doctor."
        )
    return value
