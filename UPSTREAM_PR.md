# Register DaVinci Resolve with CLI-Hub

## Proposed change

Append the following object to `registry.json`’s top-level `clis` array. The existing video category and the identifier `davinci` were checked against upstream main at `34f519533bc175d2fe287ab8316b0dd99bb9cc43`. The distribution and executable use the upstream `cli-anything-<name>` convention. The GitHub account `abbigupta` matches the configured fork remote and authenticated account.

```json
{
  "name": "davinci",
  "display_name": "DaVinci Resolve",
  "version": "0.1.0",
  "description": "Manage Resolve projects and media, edit and grade timelines, and queue renders through the official scripting API.",
  "requires": "DaVinci Resolve Studio with Local external scripting, 64-bit Python 3.10+",
  "homepage": "https://www.blackmagicdesign.com/products/davinciresolve",
  "source_url": "https://github.com/abbigupta/cli-anything-davinci",
  "install_cmd": "pip install git+https://github.com/abbigupta/cli-anything-davinci.git",
  "entry_point": "cli-anything-davinci",
  "skill_md": "https://raw.githubusercontent.com/abbigupta/cli-anything-davinci/main/skills/cli-anything-davinci/SKILL.md",
  "category": "video",
  "contributors": [
    {
      "name": "abbigupta",
      "url": "https://github.com/abbigupta"
    }
  ]
}
```

## Standalone contribution checklist

- [x] Independent repository, local origin configured for the intended public destination.
- [x] Own test suite, documented real-backend limits and GitHub Actions configuration.
- [x] Discoverable canonical skill with YAML frontmatter and an identical wheel resource.
- [x] Registry object contains the twelve required fields, the target product homepage and a raw skill URL.
- [x] Project name, package name, console script, version and video category agree with the registry proposal.
- [x] Published the standalone repository, tag, wheel and source distribution. [v0.1.0 release](https://github.com/abbigupta/cli-anything-davinci/releases/tag/v0.1.0)
- [x] Installed v0.1.0 at `d8baedd` using the exact public Git install command in a fresh virtual environment. The console entry point and dependency check passed. The downloaded raw skill matched the installed and canonical copies byte for byte.
- [ ] Submit the one-file PR. CLI-Hub reads the merged registry from main. Users can then run `cli-hub search davinci`, `cli-hub info davinci` and `cli-hub install davinci`.

[Standalone requirements](https://github.com/HKUDS/CLI-Anything/blob/main/CONTRIBUTING.md) · [Registry](https://github.com/HKUDS/CLI-Anything/blob/main/registry.json) · [Upstream PR template](https://github.com/HKUDS/CLI-Anything/blob/main/.github/PULL_REQUEST_TEMPLATE.md) · [Issue #707](https://github.com/HKUDS/CLI-Anything/issues/707)

## Completed v0.1.0 publication

The following commands are retained for reference. Continue at the registry PR section for the pending submission.

```sh
git status --short
git show -s --oneline v0.1.0
gh repo create abbigupta/cli-anything-davinci --public \
  --description "CLI-Anything harness for DaVinci Resolve"
git push -u origin main
git push origin v0.1.0
gh release create v0.1.0 dist/*.whl dist/*.tar.gz \
  --repo abbigupta/cli-anything-davinci --verify-tag \
  --title "v0.1.0" --notes-file docs/RELEASE-v0.1.0.md
```

## Verify the public install and prepare the registry PR

Run these blocks in the same shell from the standalone checkout. The fork `abbigupta/CLI-Anything` already exists. A fresh clone keeps the existing fork checkout and its branches untouched.

```sh
set -eu
standalone=$(pwd -P)
work=$(mktemp -d)
python3 -m venv "$work/verify"
(
  . "$work/verify/bin/activate"
  cd "$work"
  pip install git+https://github.com/abbigupta/cli-anything-davinci.git
  cli-anything-davinci --version
  cli-anything-davinci --help
)
git ls-remote --exit-code https://github.com/abbigupta/cli-anything-davinci.git refs/tags/v0.1.0
curl -fsSL https://raw.githubusercontent.com/abbigupta/cli-anything-davinci/main/skills/cli-anything-davinci/SKILL.md \
  | cmp - "$standalone/skills/cli-anything-davinci/SKILL.md"

git clone --depth 1 https://github.com/HKUDS/CLI-Anything.git "$work/CLI-Anything"
cd "$work/CLI-Anything"
git switch -c registry/davinci
git remote add fork https://github.com/abbigupta/CLI-Anything.git
```

Apply the proposed object while preserving the rest of the file byte for byte. The checks stop on a duplicate name, a schema discrepancy or an unexpected file layout.

```sh
python3 - "$standalone/UPSTREAM_PR.md" <<'PY'
import json
import sys
from pathlib import Path
from textwrap import indent

doc = Path(sys.argv[1]).read_text(encoding="utf-8")
entry = json.loads(doc.split("```json\n", 1)[1].split("\n```", 1)[0])
path = Path("registry.json")
before = path.read_bytes().decode()
registry = json.loads(before)
assert entry["name"] not in {c["name"] for c in registry["clis"]}
shotcut = next(c for c in registry["clis"] if c["name"] == "shotcut")
assert set(entry) == set(shotcut) and entry["category"] == shotcut["category"]
prefix, end, tail = before.rpartition("\n  ]")
assert end and tail.strip() == "}"
after = prefix + ",\n" + indent(json.dumps(entry, indent=2), "    ") + end + tail
registry["clis"].append(entry)
assert json.loads(after) == registry
path.write_bytes(after.encode())
PY
git diff --check
git diff -- registry.json
git add registry.json
git commit -m "feat: register standalone DaVinci Resolve CLI"
git push -u fork registry/davinci
sed -n '/^<!-- PR BODY START -->$/,/^<!-- PR BODY END -->$/p' "$standalone/UPSTREAM_PR.md" \
  | sed '1d;$d' > "$work/pr.md"
gh pr create --repo HKUDS/CLI-Anything --base main --head abbigupta:registry/davinci \
  --title "Register standalone DaVinci Resolve CLI" --body-file "$work/pr.md"
```

## Proposed pull request description

The public installation and raw skill checks have passed. Update the live results if a Studio run is available at submission time.

<!-- PR BODY START -->
## Description

Register the independent DaVinci Resolve CLI in the video category. The package uses Resolve's official external scripting API for projects, media, timeline editing, color grades and render jobs. This PR adds one entry to `registry.json`. Fixes #707.

[Standalone repository](https://github.com/abbigupta/cli-anything-davinci) · [Agent skill](https://raw.githubusercontent.com/abbigupta/cli-anything-davinci/main/skills/cli-anything-davinci/SKILL.md)

## Type of change

- [x] New software CLI (standalone repository)

## Standalone checklist

- [x] Package installs from the public Git URL using the exact registry install command.
- [x] External repository includes a discoverable SKILL.md and its own test suite.
- [x] Registry entry includes the external source_url and full raw skill_md URL.
- [x] CLI follows the naming convention and supports JSON output.
- [x] Commit follows upstream conventions and the change was tested locally.

## Test results

Offline suite on macOS, Python 3.10, 3.11 and 3.14: 49 passed, 2 opt-in live tests skipped per interpreter. All six hosted CI jobs passed on macOS, Ubuntu and Windows across Python 3.10 and 3.14. Resolve 21.2 Free returned no external session. The live connection test failed and the editing fixture stopped during setup. Studio editing and rendering remain unverified. [CI run](https://github.com/abbigupta/cli-anything-davinci/actions/runs/45543237149). [Test details](https://github.com/abbigupta/cli-anything-davinci/blob/main/TEST.md)
<!-- PR BODY END -->
