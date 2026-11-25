---
name: cli-anything-davinci
description: Control a running DaVinci Resolve Studio session from the terminal to manage projects and media, edit timelines, apply a grade, and queue or inspect renders.
---

Install with `pip install git+https://github.com/abbigupta/cli-anything-davinci.git` using 64-bit Python 3.10+. Enable Local external scripting in Studio and run `cli-anything-davinci --json doctor`. A successful connection reports the product and version. An unavailable session returns exit 3.

Use one-shot commands for automation. Invoke with no arguments for the interactive REPL. Use `--help` on any group. Operational commands accept `--json` and return one object on stdout. Read `data` when `ok` is true. On failure inspect `error.code`, `error.message`, and `error.details`. Exit 2 means invalid command input, exit 1 means the operation failed.

| Group | Scope |
| --- | --- |
| project | List, create, open, save, close, import and export projects in the active library folder |
| media | Import files into the current bin, find clips recursively, list or create bins |
| timeline | Create and select timelines, append media, inspect tracks and clips, add markers, export |
| timeline track | Add a track or change its enabled state, including audio mute |
| clip | Read and set exposed item properties, list or add Fusion compositions |
| color | Apply an indexed LUT or replace one item's grade from a DRX file |
| render | Inspect formats, codecs and presets, configure delivery, queue, start, poll and cancel |

```sh
cli-anything-davinci --json project current
cli-anything-davinci --json project create "Rough Cut"
cli-anything-davinci --json media import "./footage.mov"
cli-anything-davinci --json timeline create Main
cli-anything-davinci --json timeline append "./footage.mov"
cli-anything-davinci --json timeline marker add 0 Opening
cli-anything-davinci --json project save
```

Resolve's current project, timeline and media bin persist across processes. Creating or opening a project changes the active GUI context. Use media IDs from import or list when names repeat. Timeline item IDs from `timeline clips` identify the edited instance for clip and color commands. Track, timeline and node indexes start at 1. Marker offsets start at 0.

Use an existing, fresh output directory. Inspect `render formats` and `render codecs FORMAT_ID` for this workstation. Pass their values to `render configure --mode single --format FORMAT_ID --codec CODEC_ID --directory DIR --name NAME --all-frames`. Capture `data.job_id` from `render queue`, call `render start JOB_ID`, then poll `render status JOB_ID` until `data.status.JobStatus` reaches a terminal state. Check the output file after completion.

`project close --yes` discards unsaved edits. `render cancel --yes` stops active renders for the project. `color grade --yes` replaces a graph. Batch import, append and render configuration can partly succeed. Inspect the error details and current Resolve state before retrying.
