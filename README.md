# CLI-Anything for DaVinci Resolve

Edit a running DaVinci Resolve project from a terminal or an agent. Import footage, assemble a timeline, apply a LUT or a DRX grade, and start a render through Blackmagic Design's Python scripting API.

**v0.1.0 verification.** The offline suite passes on macOS. The local Resolve 21.2 Free build loads the SDK and returns no external session. Editing and rendering still need a live Studio run. [Test results and reproduction](TEST.md)

## Install and connect

Use 64-bit Python 3.10+ and a running DaVinci Resolve Studio installation. In Resolve, select **Preferences → System → General → External scripting using → Local**. The CLI targets the 21.1+ scripting interface.

```sh
# From this checkout
python -m pip install -e ".[dev]"
cli-anything-davinci doctor

# From GitHub after publication
pip install git+https://github.com/abbigupta/cli-anything-davinci.git
```

The adapter checks the macOS application bundles and system support directory, Windows ProgramData and Program Files, and Linux Resolve directories. Use `RESOLVE_SCRIPT_API` and `RESOLVE_SCRIPT_LIB` for a custom installation. Resolve Free may include internal scripts and the SDK. The external scripting preference is documented for Studio. [Platform setup](docs/INSTALLATION.md)

## Make a cut

Use a new project name and video footage that Resolve can decode. Creating or opening a project changes the active project in the application.

```sh
cli-anything-davinci project create "First Cut"
cli-anything-davinci media import "./footage.mov"
cli-anything-davinci timeline create "Main"
cli-anything-davinci timeline append "./footage.mov"
cli-anything-davinci timeline marker add 0 "Opening"
cli-anything-davinci project save
cli-anything-davinci timeline export "./first-cut.otio"
```

Run `cli-anything-davinci` with no arguments for the interactive shell. Enter `help` for command groups or `timeline --help` for editing commands. To import multiple sources in a specific order, use [the rough-cut example](examples/rough_cut.sh).

## Render the timeline

Inspect formats and codecs on this workstation. The following shell example uses a QuickTime codec ID supplied in `CODEC` and `jq` to capture the job ID. Choose a fresh delivery directory.

```sh
cli-anything-davinci render formats
cli-anything-davinci render codecs mov
# Set CODEC to a value returned by the previous command.
mkdir delivery
cli-anything-davinci render configure --mode single --format mov --codec "${CODEC:?Set a supported codec ID}" \
  --directory ./delivery --name first-cut --all-frames
job=$(cli-anything-davinci --json render queue | jq -er '.data.job_id')
cli-anything-davinci render start "$job"
cli-anything-davinci --json render status "$job"
```

Render start returns when Resolve accepts the job. Poll the job until completion and inspect the resulting file. Use `render cancel --yes` to stop all active renders in the project.

## Command groups

| Group | Operations |
| --- | --- |
| `project` | List, create, open, save, close, import and export .drp files |
| `media` | Import files, search across bins, inspect clip properties and manage bins |
| `timeline` | Create, select, append clips in order, inspect tracks and clips, mute or add tracks, place markers, export DRT, OTIO, CSV or EDL |
| `clip` and `color` | Set exposed timeline item properties, list/add Fusion compositions, apply LUTs and DRX grades |
| `render` | Discover presets and codecs, configure delivery, queue, start, poll and cancel |
| `doctor` and `status` | Inspect SDK discovery, connection, product and version |

[CLI reference](docs/CLI_REFERENCE.md) · [Verified SDK methods and limits](docs/API_COMPATIBILITY.md)

## Agent usage

Use `--json` with one-shot commands. For example, if the current library folder contains a project named Demo, `cli-anything-davinci --json project list` returns:

```json
{"ok":true,"data":["Demo"]}
```

A failed operation returns a nonzero exit code and one JSON object on stdout. For example, `cli-anything-davinci --json render start` without a job ID or `--all` returns exit 2:

```json
{"ok":false,"error":{"code":"usage","message":"Supply job IDs or --all.","details":{}}}
```

Use pool IDs to identify imported media and timeline item IDs to identify edited instances. Close, render cancellation and grade replacement require explicit confirmation flags. The packaged skill describes command sequencing, partial failures and render polling. [Agent skill](skills/cli-anything-davinci/SKILL.md)

After registry acceptance, discover and install with `cli-hub search davinci`, `cli-hub info davinci` and `cli-hub install davinci`. [Registry submission](UPSTREAM_PR.md)

## Troubleshooting and development

If doctor reports exit 3, check the SDK paths, application edition, CPU architecture and Local scripting preference. For rejected commands, inspect the active project or timeline and the inputs returned by Resolve. [Troubleshooting](docs/TROUBLESHOOTING.md)

```sh
python -m pip install -e ".[dev]"
ruff check .
ruff format --check .
python -m pytest
python -m build
```

Development work stays in this repository. The next milestone is verifying a complete edit, export and render on Studio and recording platform-specific codec results. [Architecture](docs/ARCHITECTURE.md) · [Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md)

## License and attribution

Original code is MIT licensed. The shared REPL skin comes from HKUDS/CLI-Anything under Apache-2.0. DaVinci Resolve and its scripting SDK are Blackmagic Design products and are installed separately. This is an independent community integration for wishlist issue #707. [MIT license](LICENSE) · [Third-party attribution](licenses/ATTRIBUTION.txt) · [Upstream issue](https://github.com/HKUDS/CLI-Anything/issues/707)
