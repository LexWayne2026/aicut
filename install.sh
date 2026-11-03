#!/usr/bin/env bash
# aicut skill installer for macOS / Linux. Run it from the cloned or unzipped aicut folder: ./install.sh
# Copies the skill to ~/.claude/skills/aicut (unless it is already there) and creates the Python environment it uses.
set -e
SRC="$(cd "$(dirname "$0")" && pwd)"
DST="$HOME/.claude/skills/aicut"
VENV="$HOME/.wbx-venv"
PY="$(command -v python3.12 || command -v python3.11 || command -v python3.10 || command -v python3)"

"$PY" -c "import sys; sys.exit(0 if (3,10) <= sys.version_info[:2] <= (3,13) else 1)" ||
    { echo "[!] Python 3.10 to 3.13 is required (found $("$PY" --version))"; exit 1; }

if [ "$SRC" != "$DST" ]; then
    echo "copying skill to $DST ..."
    mkdir -p "$DST" && cp -R "$SRC/." "$DST/"
fi
[ -x "$VENV/bin/python" ] || { echo "creating Python environment at $VENV ..."; "$PY" -m venv "$VENV"; }
echo "installing packages (skia, numpy, opencv, faster-whisper) ..."
"$VENV/bin/python" -m pip install -q --upgrade pip
"$VENV/bin/python" -m pip install -q -r "$DST/requirements.txt" "opencv-python-headless>=4.8,<5" faster-whisper

command -v ffmpeg >/dev/null && command -v ffprobe >/dev/null ||
    echo "[!] ffmpeg / ffprobe not on PATH. macOS: brew install ffmpeg   Debian/Ubuntu: sudo apt install ffmpeg"
"$VENV/bin/python" "$DST/tools/selftest.py"
echo "done. Restart Claude Code, then ask for \"aicut Template 1/2/3\" with your clip."
