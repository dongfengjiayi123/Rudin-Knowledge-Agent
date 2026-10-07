#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
[ -d .venv ] || python3 -m venv .venv
.venv/bin/python -m pip install -e .
[ -f .env ] || cp .env.example .env
exec .venv/bin/python -m rudin_agent.cli serve
