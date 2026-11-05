#!/bin/sh
# The checks .github/workflows/ci.yml runs (gitleaks and osv-scanner as CLIs here, as actions there). Run by the pre-push hook: scripts/install-hooks.sh
set -eu
cd "$(git rev-parse --show-toplevel)"
uv lock --check
uv run ruff check .
uv run pytest -q
uv run flight-deals check-destinations
gitleaks git --no-banner .
osv-scanner scan --lockfile=uv.lock
uvx --from 'actionlint-py==1.7.12.*' actionlint
uvx zizmor==1.31.1 --min-severity=low .github/workflows
