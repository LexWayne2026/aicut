# Installing aicut on Windows

## Needs
- **Claude Code** (desktop app or CLI).
- **Python 3.12** from https://www.python.org/downloads/. In the installer, tick **Add python.exe to PATH**.
- **ffmpeg**: open PowerShell and run `winget install Gyan.FFmpeg`, then open a new terminal.
- About 2 GB free: Python packages plus the Whisper speech model, which downloads on first use.

## Install
1. Unzip `aicut-skill.zip` anywhere. You get an `aicut` folder.
2. Double-click `aicut\install-windows.bat`. It:
   - copies the skill to `%USERPROFILE%\.claude\skills\aicut`;
   - creates the Python environment at `%USERPROFILE%\.wbx-venv`, or at `C:\wbx-venv` if your user name has non-ASCII
     characters such as Chinese (OpenCV cannot open files under such a folder);
   - installs skia-python, numpy, opencv and faster-whisper;
   - checks ffmpeg, then draws one test frame for each template.
3. It should end with `OK: aicut is ready`. Restart Claude Code and ask for "aicut Template 1", "Template 2" or "Template 3" with your clip.

## What is inside
| Folder | Contents |
|---|---|
| `wbx/` | Render engine: Template 1 (`core`, `icons`, `components`), Template 2 (`popcard`), Template 3 (`softglass`), audio, layout, parallel render |
| `tools/` | New project, probe, transcription, contact sheets, render-kit packaging, self-test |
| `fonts/` | LXGW WenKai, Resource Han Rounded, Outfit and Noto Sans SC, with their open licences |
| `music/` | Four Holizna CC0 tracks for Template 1 (Templates 2 and 3 use synthesized sound effects, no files) |
| `templates/` | Starter projects for each template and the render-kit launchers |
| `examples/` | The approved OTC projects for all three templates (scenes, timeline, transcript; the clip is not included) |
| `references/` | Style rules, APIs and your feedback log per template |

## Troubleshooting
- **"Python not found"** although it is installed: Windows may be opening the Microsoft Store stub. Turn off
  *Settings > Apps > Advanced app settings > App execution aliases > python.exe*, or reinstall Python with PATH ticked.
- **ffmpeg not found** right after winget: open a new terminal so PATH updates.
- **Self-test fails on Template N:** the message shows the Python error. Send it to Claude.
- Rendering a kit made on another machine needs only Python and ffmpeg: run `render.bat <project-name>` inside the unzipped kit.
