#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if command -v uv >/dev/null 2>&1; then
    (cd "${ROOT}" && uv run --no-project --with pytest pytest tests)
else
    (cd "${ROOT}" && python3 -m pytest tests)
fi
