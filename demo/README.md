# Demo projects

The same 35-second script rendered in all three templates. The script is a made-up explainer about choosing fish
oil, written for this demo, and the presenter is a drawn stand-in. No real footage or speech is used, so anyone can
render these and copy their patterns.

```bash
python demo/make_demo.py                                   # draws the stand-in clip, writes data/ and input/
python wbx/render.py --project demo/softglass --preview    # or demo/popcard, demo/whiteboard
```

| Project | Template | Shows |
|---|---|---|
| `whiteboard/` | 1 | Lower-third titles over the presenter, taped photo, price bars, tablet rows with a counter, stamp, flip-in form cards |
| `popcard/` | 2 | Bottles whipping in, colour sheets, big numbers, bouncing capsules, a slammed form grid |
| `softglass/` | 3 | Glass rows over video, gradient odometer, hero card shrinking to an avatar, bar chart, form tiles with a selection ring |

Each project's `timeline.py` derives every time from the script with `at("phrase", "word")`, and `scenes.py` draws each
scene as a function of time. To use a real clip instead, scaffold a project with `tools/new_project.py` and copy these
two files in as a starting point.

The script's numbers are plain arithmetic for the demo (300 mg × 3 = 900 mg), not health advice.
