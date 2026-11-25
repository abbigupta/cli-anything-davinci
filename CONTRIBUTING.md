# Contributing

Create a virtual environment, activate it and install `python -m pip install -e ".[dev]"`. Run `ruff check .`, `ruff format --check .`, and `python -m pytest`. For live SDK changes, follow the isolated Studio workflow in [TEST.md](TEST.md).

Keep SDK calls small and document the vendor method, argument types, return values and edition limits in [API compatibility](docs/API_COMPATIBILITY.md). Add a test for the success and rejection paths of new commands. Keep the canonical skill and its package copy identical. Use conventional commit subjects.

Submit implementation changes to this standalone repository. Release and upstream registration instructions are in [UPSTREAM_PR.md](UPSTREAM_PR.md).
