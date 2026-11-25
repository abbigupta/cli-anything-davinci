import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from cli_anything.davinci.utils import davinci_backend as sdk


@pytest.mark.parametrize(
    ("system", "script", "lib"),
    [
        ("Darwin", "/Library/Application Support", "fusionscript.so"),
        ("Windows", "Support/Developer/Scripting", "fusionscript.dll"),
        ("Linux", "/opt/resolve", "fusionscript.so"),
    ],
)
def test_discovery_layout(system, script, lib):
    roots, libs = sdk.locations(system)
    assert any(script in p.as_posix() for p in roots)
    assert libs[0].name == lib


@pytest.mark.parametrize("use_modules", [True, False])
def test_explicit_module_and_library(tmp_path, monkeypatch, use_modules):
    modules = tmp_path / "Modules"
    modules.mkdir()
    (modules / "DaVinciResolveScript.py").write_text(
        "def scriptapp(name):\n    assert name == 'Resolve'\n    return 'live'\n"
    )
    lib = tmp_path / "fusionscript.so"
    lib.touch()
    monkeypatch.setenv("RESOLVE_SCRIPT_API", str(modules if use_modules else tmp_path))
    monkeypatch.setenv("RESOLVE_SCRIPT_LIB", str(lib))
    monkeypatch.delitem(sys.modules, "DaVinciResolveScript", raising=False)
    try:
        b = sdk.Backend()
        assert b.resolve == "live"
        assert b.diagnostics()["module_dir"] == str(modules)
        assert str(modules) not in sys.path
    finally:
        sys.modules.pop("DaVinciResolveScript", None)


def test_bad_override_is_actionable(tmp_path, monkeypatch):
    monkeypatch.setenv("RESOLVE_SCRIPT_API", str(tmp_path))
    with pytest.raises(sdk.ResolveError, match="RESOLVE_SCRIPT_API"):
        _ = sdk.Backend().resolve


@pytest.mark.parametrize(
    "problem",
    [ImportError("module not installed"), OSError("wrong architecture"), None],
)
def test_no_connection(monkeypatch, problem):
    monkeypatch.delenv("RESOLVE_SCRIPT_API", raising=False)
    monkeypatch.delenv("RESOLVE_SCRIPT_LIB", raising=False)
    monkeypatch.setattr(sdk, "locations", lambda system: ([], []))

    def load(name):
        if problem:
            raise problem
        return SimpleNamespace(scriptapp=lambda name: None)

    monkeypatch.setattr(sdk.importlib, "import_module", load)
    with pytest.raises(sdk.ResolveError, match="Studio") as failure:
        _ = sdk.Backend().resolve
    assert failure.value.code == "unavailable"


def test_unsupported_and_disconnected():
    with pytest.raises(sdk.ResolveError, match="unavailable"):
        sdk.read(object(), "SetLUT", 1, "lut")

    def disconnected():
        raise RuntimeError("lost connection")

    with pytest.raises(sdk.ResolveError, match="lost connection"):
        sdk.read(SimpleNamespace(GetName=disconnected), "GetName")


def test_mac_app_bundle_discovery():
    scripts, libs = sdk.locations("Darwin")
    assert (
        Path("/Applications/DaVinci Resolve.app/Contents/Resources/Developer/Scripting")
        in scripts
    )
    assert any("Resolve/DaVinci Resolve.app" in p.as_posix() for p in libs)
