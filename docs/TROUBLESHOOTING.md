# Troubleshooting

Start with `cli-anything-davinci --json doctor`. To see the SDK module and method names on stderr, use `cli-anything-davinci --verbose doctor`.

| Observation | Action |
| --- | --- |
| No module or native load error | Check the reported module directories and library. Use the files from the same Resolve install. Check Python and Resolve CPU architecture, especially Rosetta on macOS. |
| SDK loads, session unavailable (exit 3) | Start Resolve Studio, allow it to finish loading and select Local external scripting. Confirm you launched Studio if both editions are installed. |
| `no_project` or `no_timeline` | Open a project in the selected library folder. Use `timeline list` and `timeline select INDEX`, or create a timeline. |
| Ambiguous or missing media | Use `media search TEXT` and pass the pool ID. Import a path before appending it. Timeline commands use the current project. |
| `unsupported` or `rejected` | Inspect the installed version, edition and active selection. Confirm that the operation and inputs are available in the GUI. Resolve sometimes returns only a boolean failure. |
| Property or LUT rejected | Read `clip properties ITEM_ID`; some keys are read-only. Install the LUT in Resolve and refresh the LUT list in the GUI. Node indexes start at 1. |
| Render fails | Check the selected timeline and a writable output directory. Enumerate the workstation's formats and codecs, then inspect the job-specific status and Resolve's Deliver page. |
| Partial batch failure | Inspect `error.details.imported`, `appended_ids` or `applied`. Query Resolve before retrying a mutation. |
| Export destination exists | Choose a new filename. Project and timeline exports create new files. |
| Render stop still pending | Poll `render status`. The stop API acts on all running jobs and exposes no per-job cancellation. |
