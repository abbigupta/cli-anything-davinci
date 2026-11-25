# Test plan and results

| Layer | Coverage |
| --- | --- |
| Discovery and adapter | macOS, Windows and Linux path layouts, explicit paths, missing SDK, native load errors, unavailable sessions and missing methods |
| Mocked Click commands | Projects, bins and media, timeline selection and editing, markers, export constants, track enable, Fusion, grade and LUT calls, async render jobs and cancellation |
| Failure paths | Missing context, ambiguous media, partial import or render configuration, refused operations, existing export files, empty exports and invalid CLI arguments |
| Packaging and shell | Console script outside the checkout, skill resource, JSON errors, help and version, fail-fast piped REPL and a fresh backend per line |
| Real subprocess workflow | Doctor, UUID-named project, generated red video, media import, edit, marker, DRP round trip, OTIO structure, render progress, ffprobe video stream and decoded red pixel |

## Local evidence — 24 November 2026

- macOS arm64, Python 3.10.22, 3.11.15 and 3.14.6. Default suite on each interpreter: **49 passed, 2 live tests skipped**.
- Ruff lint and format checks passed. The canonical skill passed the skill frontmatter validator.
- The installed macOS 21.2.0 Free application was running. The CLI found the vendor module and native library, identified the Lite bundle and returned **exit 3** because `scriptapp("Resolve")` returned no session.
- The opt-in live run produced one failed connection test and one fixture setup error. Both stopped at SDK connection. The fixture never created its scratch project, so editing, export and rendering remain unverified.
- All six hosted CI jobs passed on macOS, Ubuntu and Windows with Python 3.10 and 3.14. [GitHub Actions run](https://github.com/abbigupta/cli-anything-davinci/actions/runs/45543237149)

## Offline checks

Run from the repository root. On a fresh checkout, create the virtual environment with `python3 -m venv .venv`. On Windows, activate it with `.\.venv\Scripts\Activate.ps1` in PowerShell.

```sh
. .venv/bin/activate
python -m pip install -e ".[dev]"
ruff check .
ruff format --check .
python -m pytest -q
python -m build
python -m twine check --strict dist/*
```

## Run the real workflow

Use **Resolve Studio with Local external scripting**, an exclusive test session, and a separate disposable local project library. Install ffmpeg and ffprobe for the source fixture and output checks. Select the test library in Resolve. Leave the project manager open with no active project, or open a saved empty project named `CLI-Anything Test Anchor` there. The suite checks the library and current project before creating a unique project. It deletes its own test projects on teardown. Use a new test run if you switch libraries during the test.

```sh
. .venv/bin/activate
export DAVINCI_TEST_LIBRARY='CLI Harness Tests'
export DAVINCI_TEST_CODEC='ProRes422'
cli-anything-davinci doctor && python -m pytest --resolve -m resolve -v
```

In PowerShell set `$env:DAVINCI_TEST_LIBRARY = 'CLI Harness Tests'` and `$env:DAVINCI_TEST_CODEC` before running the same pytest command. Use `render codecs mov` in the scratch project to discover codec IDs. The fixture and rendered movie are in pytest's temporary directory. Tests that explicitly request the live backend fail if a prerequisite is missing.

The acceptance check requires a nonempty exported project that Resolve can reimport, a timeline in that project, an OTIO file with tracks, a completed render job and a movie with a video stream and the expected red frame.
