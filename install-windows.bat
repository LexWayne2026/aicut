@echo off
rem aicut skill installer for Windows. Double-click it, or run it from the unzipped aicut folder.
rem Copies the skill to %USERPROFILE%\.claude\skills\aicut and creates the Python environment it uses.
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
set "SRC=%~dp0"
set "DST=%USERPROFILE%\.claude\skills\aicut"

where python >nul 2>nul || (
  echo [!] Python not found. Install Python 3.12 from https://www.python.org/downloads/
  echo     and tick "Add python.exe to PATH", then run this again.
  goto :end
)
python -c "import sys; sys.exit(0 if (3,10) <= sys.version_info[:2] <= (3,13) else 1)" || (
  echo [!] Python 3.10 to 3.13 is required; faster-whisper and skia wheels lag behind newer versions.
  goto :end
)

rem 1. copy the skill
if /i "%SRC:~0,-1%"=="%DST%" (
  echo skill already in place: %DST%
) else (
  echo copying skill to %DST% ...
  robocopy "%SRC:~0,-1%" "%DST%" /E /NFL /NDL /NJH /NJS /XD __pycache__ >nul
  if errorlevel 8 ( echo [!] copy failed & goto :end )
)

rem 2. venv on an ASCII path (OpenCV cannot open files under a non-ASCII user folder)
set "VENV=%USERPROFILE%\.wbx-venv"
python -c "import os,sys; sys.exit(0 if os.environ['USERPROFILE'].isascii() else 1)" || set "VENV=C:\wbx-venv"
if not exist "%VENV%\Scripts\python.exe" (
  echo creating Python environment at %VENV% ...
  python -m venv "%VENV%" || ( echo [!] venv failed & goto :end )
)
echo installing packages (skia, numpy, opencv, faster-whisper) ...
"%VENV%\Scripts\python.exe" -m pip install --upgrade pip >nul
"%VENV%\Scripts\python.exe" -m pip install -r "%DST%\requirements.txt" "opencv-python-headless>=4.8,<5" faster-whisper || ( echo [!] pip install failed & goto :end )

rem 3. ffmpeg
where ffmpeg >nul 2>nul && where ffprobe >nul 2>nul && (
  echo ffmpeg found.
) || (
  echo [!] ffmpeg / ffprobe not on PATH. Install it with:  winget install Gyan.FFmpeg
  echo     then open a new terminal so PATH updates.
)

rem 4. self-test: load every template's fonts and draw a frame
"%VENV%\Scripts\python.exe" "%DST%\tools\selftest.py" || echo [!] self-test failed, see above

echo.
echo done. Skill: %DST%
echo      Python: %VENV%\Scripts\python.exe
echo Restart Claude Code, then ask for "aicut Template 1/2/3" with your clip.
:end
pause
