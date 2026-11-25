# CLI-Anything for DaVinci Resolve v0.1.0

This first release provides an installable Python CLI for controlling a running Resolve Studio session. It supports project and media management, timeline assembly and interchange, markers, track controls, clip properties, Fusion compositions, LUT/DRX grading and the render queue.

Agents can use structured JSON, stable exit codes, batch input and a packaged skill. Human users can run the same commands in the interactive REPL.

The offline suite passed on macOS with Python 3.10, 3.11 and 3.14. A real connection attempt against Resolve 21.2 Free returned no external session. A complete Studio render and hosted Windows/Linux runs remain outstanding. See [test evidence](../TEST.md) for the local validation procedure.

Original code is MIT licensed. The bundled upstream REPL skin is Apache-2.0 licensed.
