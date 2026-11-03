# Template 1 style guide: grid whiteboard + pencil

## Look
- **Board:** warm paper `#F8F7F2`, light-blue grid (40 px minor, 200 px major), faint grain, soft vignette.
- **Line:** graphite `#26262B`, every stroke drawn with a seeded wobble in two passes (`sketch`, `pencil`);
  lines "boil" at 6 fps (posterized jitter, `BOIL_FPS` in core) like hand-drawn animation.
- **Fill:** pencil hatching (`hatch`) in an accent, never flat glossy fills; no glows on paper.
- **Emphasis:** yellow highlighter swipe (`marker`), hand-drawn circles/underlines/strikes (`annotate`).
- **Type:** LXGW WenKai (handwritten, OFL), weights 300/400/500, ≥700 = synthetic bold. Headline ≥ 84 px,
  important supporting text ≥ 44 px, kicker labels ≥ 24 px (on 1080-wide), 80 px side safe area.
- **Colour semantics:** blue pencil = accent/structure; green = good / OTC / drug; orange = imported /
  pricier / supplement; red = "≠", wrong, warning; teal = secondary highlight; yellow = highlighter.
- **Cards:** paper cards pinned on the board (white, pencil outline, soft shadow). Sticky notes, tape,
  stamps and sketched icons are welcome — the board should feel hand-made and alive.

## Presenter
- **Full frame** (hook, verdicts, "remember" lines, the ending): NO panels or boards over the video. Only a
  semi-transparent dark gradient at the bottom, white handwritten text with a soft shadow, colours switch to
  brighter tints (`on_video()` does this). Make these moments lively: bouncing letters (`style="bounce"`),
  hand-drawn circles, squiggles, sparkles, burst lines, highlighter swipes, confetti on the final line.
- **Corner photo** (explanations): taped polaroid at top-right, -2° tilt, white border, landing wobble.
  Crop is face-aware: 3:4, face centred, eyes ~1/3 from the top, collar in frame, no shelf band on top.
  The morph between full and corner is one virtual camera (geometric zoom), so the face never distorts.
- **Hidden** for dense grids (e.g. six tiles).

## Motion
- Entrances: springs with slight overshoot or the house ease-out `EXPO_OUT = bezier(0.16, 1, 0.3, 1)`;
  characters stagger in with rise + blur; icons draw on stroke by stroke then hatch fills in.
- Exits: blur-out (default) or a TransitionSeries-style presentation: eraser wipe between chapters,
  slide-left within a chapter, iris / page / flip / pop for variety; a warm paper "light-leak" flash at
  chapter cuts. Stage scenes slowly push in (camera drift) so nothing is ever static.
- Scale animations interpolate geometrically (`pscale`) so growth looks even.

## Sound
- Voice untouched except a high-pass and gentle compression.
- Music bed: a CC0 lo-fi track (Holizna), ducked under speech (voice ≈ 10 dB above the bed).
- Foley on every visual event: pencil scribble (checks/strikes/underlines), marker squeak, paper slide
  (cards), marimba pops (items), pen taps (labels), knocks (≠), rising arpeggio (values climb), bell
  (new chapter), photo swish (presenter morph), stamp thump, eraser rub, sticky-note flap, icon draw.
- Master -14 LUFS (−12 for Douyin), true peak ≤ −1 dB.

## Content rules
- On-screen text is the speaker's own words or a direct, literal condensation. No invented numbers.
- Fix ASR mistakes with the user before building (they will notice wrong subtitles).
- Captions: on, one line, active character pops in the accent colour; muted while an on-screen statement
  repeats the same words.

## Delivery (user preference)
- Show stills/contact sheets while building; send a low-res preview with audio.
- Package a render kit zip; the user renders the master on a more powerful machine.
- Output size and aspect ratio = the source clip's.

## Feedback log (keep appending)
- v1 dark Apple-style tech look → user wanted brighter: grid whiteboard + pencil feel.
- Full-screen presenter with a white paper panel at the bottom looked bad → text only on a gradient.
- Corner photo crop was too loose / face too low → face-aware crop rule above.
- "More motion effects and assets" → icon library with draw-on, stamps, stickies, counters, charts,
  transitions, camera drift, line boil, confetti.
