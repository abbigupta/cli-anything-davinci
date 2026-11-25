# Command reference

Prefix commands with `cli-anything-davinci`. Use `--json` for machine-readable operational output. `--help` and `--version` print text. Root `--verbose` logs to stderr. Unquoted uppercase words below are arguments.

| Command | Result |
| --- | --- |
| `doctor` / `status` | Diagnose discovery and manager access / read connected product and version |
| `repl` or no arguments | Enter the interactive shell. `help` shows commands; `exit`, `quit` or EOF ends the session |
| `project list` / `project current` | Project names in the current library folder / active project |
| `project create NAME` / `project open NAME` | Create or open a named project |
| `project save` / `project close --yes` | Save / close and discard unsaved changes |
| `project export FILE.drp` / `project import FILE.drp [--name NAME]` | Export the active project / import into the current library folder |
| `media list` / `media search TEXT` | List media IDs across bins / filter by case-insensitive name substring |
| `media import FILE...` / `media info SELECTOR` | Import files in order / read one media item's properties |
| `media folder list` / `media folder create NAME` | List child bins / add a bin under the current bin |
| `timeline list` / `timeline current` | Names and indexes / current name |
| `timeline create NAME` / `timeline select INDEX` | Create and activate a timeline / activate by one-based index |
| `timeline append SELECTOR...` | Append whole pool clips in the supplied order |
| `timeline info` / `timeline tracks` / `timeline clips` | Timecode and frame bounds / tracks / item IDs and positions |
| `timeline marker add FRAME NAME [--color COLOR] [--duration FRAMES] [--note NOTE]` | Add a marker at a zero-based offset; defaults to Blue and one frame |
| `timeline marker list` | Markers in frame order |
| `timeline export FILE` | Write .drt, .otio, .csv or .edl (plain EDL) |
| `timeline track add KIND` / `timeline track enable KIND INDEX on\|off` | Append track / enable or disable video, audio or subtitle track |
| `clip properties ITEM_ID` / `clip set ITEM_ID KEY JSON_VALUE` | Inspect properties / set and read back one value |
| `clip fusion ITEM_ID [--add]` | List compositions, optionally create one first |
| `color lut ITEM_ID NODE LUT_PATH` | Apply a discovered LUT to an existing node |
| `color grade ITEM_ID FILE.drx --yes [--mode 0\|1\|2]` | Replace the grade; use no keyframes, source timecode or start-frame alignment |
| `render formats` / `render codecs FORMAT_ID` / `render presets` | Discover locally available output formats, codecs and presets |
| `render configure [--preset NAME] [--mode single\|individual] [--format ID --codec ID] [--directory DIR] [--name NAME] [--all-frames]` | Apply at least one setting; the format and codec must be paired |
| `render queue` | Add the current timeline to the queue and return its string job ID |
| `render start JOB_ID...` / `render start --all` | Start specified jobs or the entire queue |
| `render status [JOB_ID]` | List queue and active state or read job-specific progress |
| `render cancel --yes` | Stop all active renders in the current project |

A media selector can be a media pool ID, exact name, or imported source path. Duplicate matches require an ID. An item ID identifies one timeline instance, including its track. Quote names and paths with spaces. Use `--` before positional values beginning with a dash.

In the REPL, double or single quotes group arguments. Backslashes in Windows paths are literal. Piped command input stops at the first failure and propagates its exit code. Use only operational commands in a JSON Lines batch.

| Exit | Meaning |
| --- | --- |
| 0 | Requested operation succeeded |
| 1 | SDK rejection, unsupported feature, selection, I/O or other operation error |
| 2 | Invalid command or arguments |
| 3 | External Resolve scripting session unavailable |
| 130 | Interrupted |
