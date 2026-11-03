@echo off
rem Usage: render.bat <project-name> [extra args, e.g. --mb 6]
cd /d %~dp0
set PYTHONUTF8=1
if not exist .venv ( python -m venv .venv && .venv\Scripts\pip install -r requirements.txt )
.venv\Scripts\python wbx\parallel.py --project projects\%1 %2 %3 %4 %5
