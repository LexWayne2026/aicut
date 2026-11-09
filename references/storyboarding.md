# Storyboarding a talking-head explainer

## From transcript to beats
1. Read `data/transcript.txt` end to end. Mark the structure: hook (first 5–8 s), thesis, chapters
   (often announced: "第一步… 第三步…", "first… second…"), examples with numbers, verdict lines, ending.
2. One idea per scene. A scene usually spans 1–4 caption lines (5–15 s). Split long explanations into
   sub-scenes (e.g. "drug" then "supplement") instead of crowding one board.
3. Every visual beat lands on a word: define cues in `timeline.T` with `at(line, word)`. Elements enter
   on the word that names them, or up to ~0.13 s after; never earlier (text before sound feels wrong).
   Never hard-code seconds.
4. Use `pauses()` / `data/silences.json` for scene cuts and transitions — cut in the breath, not mid-word.

## Presenter choreography
- `full` for: the hook/title, thesis statements, "remember…" verdicts, the closing line. Pair with a
  lower-third (layer "over") that says the line in big handwritten type + doodles; mute captions there.
- `pip` (taped corner photo) for explanations; `hidden` when the board needs the whole frame.
- Switch on phrase boundaries (≥ 1.5 s apart). Each morph gets a "swish" sfx.

## Motion vocabulary (pick per beat, vary across the video)
| beat | treatment |
|---|---|
| introduce a thing | `icon_in` draws it, label rises in; product objects (`bottle`, `tablet`) pop with spring |
| compare A vs B | two paper cards / bars; A appears, then B; highlight the difference (marker, bracket, gap line) |
| a number | `counter` rolls, `bar_chart` grows, `progress_ring` fills; show units |
| a rule / definition | `stamp` slam ("药品", "OK", "NO") or `sticky` note |
| "not equal" / myth | `neq` drawn + red `annotate(... "strike"/"crossed")` + knock sfx |
| list / steps | `checklist`, numbered doodle circles, chapter header with progress bar + icon |
| process / decision | flow nodes connected by drawn lines, icons at the right end |
| overlap / duplication | Venn with hatched intersection |
| emphasis | highlighter swipe, circle, squiggle underline, sparkle, burst lines |
| finale | bouncing big type, highlighter + squiggle, confetti, bell |

## Remotion-derived principles (adopted from remotion-dev/skills)
- Drive everything from time with explicit keyframes (`interpolate`) and clamp; ease entrances with
  `bezier(0.16, 1, 0.3, 1)`, moves with in-out, use heavily damped "push" springs when bounce is wrong.
- Animate scale perceptually (geometric), not linearly.
- Posterize deliberately for hand-made feel (line boil at 6 fps) — never posterize the camera or text.
- Treat scenes as a TransitionSeries: consecutive scenes with presentations (slide, wipe, iris, flip) and
  overlays at cut points (light-leak "flash") that don't shorten the timeline.
- Text annotations follow rough-notation: highlight, circle, underline, strike-through, crossed-off, box,
  bracket — always progress-driven so they draw on.
- Optional motion blur by sub-frame averaging (`--mb 6`, 180° shutter) for the final render.
- Captions: one line at a time, active word highlighted (TikTok style); keep inside the safe area.
- Video layout: decide what the viewer notices first in each scene; keep key text ≥ 80 px from the sides;
  headline ≥ 84 px, important supporting text ≥ 44 px (scale with width); no redundant elements.

## Comfort rules (measured)
Adapted from talking-video-skills' analysis of two Chinese explainer channels (about 150 minutes, 30 fps). These are
the numbers behind "easy to watch"; treat them as defaults, and let the chosen template's reference win on look.
- **Cuts follow sentences.** Most scene changes sit within ±3 frames of a caption line start (aim for ~70% of
  them). Cut in the breath before the line, never mid-word.
- **Not every line gets a new scene.** One main picture per 2–3 lines (about 4–7 s); keep it alive with build-ons
  (labels, annotations, counters) instead of hard cuts. But no 10-second window without any cut or new element:
  at most ~10% of the video.
- **Dense start.** The first 20–30 s has the most changes; after that alternate ~15 s busy, ~15–20 s calm.
- **Text follows the word.** An on-screen keyword appears 0 to +4 frames after the word starts (−2 at most). Fewer
  than 1 in 10 elements may land early.
- **Motion lengths come in three tiers:** hard cut (0), fast (~6 frames, 0.2 s), standard (~12–14 frames, 0.4 s).
  Anything that appears stays at least ~40 frames (1.3 s). Exits mirror entrances or cut hard.
- **The face comes back.** The full-frame presenter returns every 15–20 s for 3–6 s; any stretch with the
  presenter hidden stays ≤ 10 s (pip counts as visible).
- **Little on screen.** At most one headline and 3–4 elements per frame; headline ~8–14% of frame height.
- **Captions never move.** One style, one position for the whole video; drop them only where a full-frame
  statement says the same words (CAPTION_MUTE).
- **Sound effects stay sparse and quiet.** ≤ 0.8 events per second overall (priority: reveal/impact > chapter
  swish > pop/slide > tick), the same kind ≥ 0.25 s apart, always on or just after the visual event; sfx sit well
  under the voice (≥ 10 dB) so the voice stays on top.
- **Feedback redoes only what it names.** "Scene 7 is too fast" changes scene 7, not the storyboard.

## Checklist before preview
- Stills sheet covers every scene + a transition mid-way + every full-frame overlay.
- Smoke test: render every 0.1 s at tiny scale (catches exceptions in rarely-hit branches).
- Nothing overlaps the corner photo (x > ~780, y < ~380 in stage space near the top), header or captions.
- Every element that appears has a sound in `sfx_events()` (within the density rule above).
- `tools/check_sync.py P` passes (caption edges on the waveform) before cues are trusted.
- After the preview: `tools/qc.py P` passes; send its numbers with the preview, including any ✗.
