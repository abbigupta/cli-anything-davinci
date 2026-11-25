# Architecture

Resolve owns all editing state. Each invocation attaches to the running application through Blackmagic Design's Python module. A REPL line goes through the same Click parser as a one-shot command. There is no project cache or shadow database.

## Implementation plan

1. Locate the vendor module and library on each platform. Probe the live session and report connection failures.
2. Implement projects, media, timelines and render jobs in separate Click command groups. Put shared SDK lookup and result checks in the adapter.
3. Add targeted clip, track, color and Fusion operations where the vendor documents their behavior.
4. Run isolated fake-object tests, installed-command checks and opt-in real project/export/render tests.
5. Build and inspect the distributions. Prepare a registry-only contribution and a local release.

The package uses the shared PEP 420 `cli_anything` namespace. The distribution name and console script follow `cli-anything-<software>`. The included REPL skin is verbatim upstream code under Apache-2.0. Project-specific code uses MIT.

## Upstream references

Checked CLI-Anything main at `34f519533bc175d2fe287ab8316b0dd99bb9cc43`. Standalone submissions have their own repository, installable package, skill and tests. The upstream change consists of one registry entry. The Blender and Shotcut harnesses provide the conventions for Click groups, default REPL, packaged skill and real-output tests.

[Contribution rules](https://github.com/HKUDS/CLI-Anything/blob/34f519533bc175d2fe287ab8316b0dd99bb9cc43/CONTRIBUTING.md) · [Harness methodology](https://github.com/HKUDS/CLI-Anything/blob/34f519533bc175d2fe287ab8316b0dd99bb9cc43/cli-anything-plugin/HARNESS.md) · [Blender](https://github.com/HKUDS/CLI-Anything/tree/main/blender/agent-harness) · [Shotcut](https://github.com/HKUDS/CLI-Anything/tree/main/shotcut/agent-harness)
