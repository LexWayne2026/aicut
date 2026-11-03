#!/usr/bin/env bash
# Usage: ./render.sh <project-name> [extra args, e.g. --mb 6]
set -e
cd "$(dirname "$0")"
[ -d .venv ] || { python3 -m venv .venv && .venv/bin/pip install -r requirements.txt; }
.venv/bin/python wbx/parallel.py --project "projects/$1" "${@:2}"
