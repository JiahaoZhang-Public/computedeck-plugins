#!/bin/bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen mypy network/src shell-credentials/src scripts
uv run --frozen pytest -q
PYTHONPATH=examples/hello/src uv run --frozen pytest examples/hello/tests -q
npm --prefix examples/hello/web ci
npm --prefix examples/hello/web run build
npm run lint
npm run format:check
npm run typecheck
npm test
npm run build
uv build --package computedeck-network --no-sources
uv build --package computedeck-shell-credentials --no-sources
