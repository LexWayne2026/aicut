# Template 2 style guide and API: Pop Card

Code: `wbx/popcard.py`. Example: `examples/popcard/`. Set `TEMPLATE = 2` in `timeline.py`.

## Look
- **Colour:** one full-bleed colour per chapter: lime `#7BE800`, pink `#FF5C93`, yellow `#FFE500`, sky `#2EB6FF`, violet `#7C3AED`, or ink `#111114` for contrast. Orange `#FF9F1C` is an accent. Semantics carry over: lime = OTC/drug, orange = imported/supplement, pink = emphasis.
- **Cards:** white, large radius (about 48), 1-3° tilt, soft shadow tinted with a dark shade of the background (not grey). The curved white sheet (`dome`) is the other main surface.
- **Objects:** flat fill plus a 7-unit ink outline, in the same family as `bottle tablet capsule coated liposome gummy dropper leaf globe`. Add new ones in that style. Cartoonish, never childish: no faces except on gummies, no bubble type.
- **Step marker:** `badge`, the black squircle with a number or sparkle.
- **Type:** Resource Han Rounded CN Heavy for Chinese and Outfit ExtraBold for Latin/numerals. `heavy=False` gives the Medium weights for small labels. Headline at least 84, supporting text at least 44, 66 side margin.
- Text on screen is the speaker's own words or a literal condensation. No invented numbers.

## Presenter
- **Always live video, never a still.** The renderer feeds the tile every frame.
- **Not limited to the top-right.** Place it wherever the layout leaves room and move it during a scene when that helps; a swap of sides or a shrink into a corner is a good beat.
- `PRESENTER = [(time, slot), ...]`. A slot is `"full"`, `"hidden"`, a name from `SLOTS` (`tl tr bl br center left right`) or `(x, y, w, h[, rot])` in reference space. Moves spring with an arc and overshoot. Keep tiles 3:4 when you can; other shapes trim the crop rather than stretch the face.
- **Full frame:** no panels over the video. Text, chips and sticker objects on the bottom gradient only.

## Motion
No linear moves. Each element gets one verb:
| Verb | Call | Use for |
|---|---|---|
| Pop in | `pop(c, t, t0, cx, cy, draw, w, z, spin)` | Cards, chips, icons: overshoot + squash |
| Whip & snap | `whip(c, t, t0, cx, cy, draw, dist, sign, spin)` | Slide-ins, bottles, labels |
| Drop & bounce | `drop_text(c, s, x, y, size, color, t, t0, stag, align, fall)` | Headlines, one character at a time |
| Sheet slam | scene `enter="slam"` | Chapter changes; `slam2` sets the leading colour (default violet) |
| Pulse | `k = pulse(t, t0, a)` with `around(c, cx, cy, k, k)` | Emphasis on a word |
| Exit | `back_out(c, t, t1, cx, cy, draw)` | Grow a touch, then shrink away |
| Secondary | `burst(c, x, y, t, t0, color)`, `idle(t, seed, amp)` | Sparks on impacts; float so nothing is ever still |

`draw` is a zero-argument lambda using absolute coordinates; `cx, cy` is the pivot. For a falling object, use `drop` and `m_drop` (see the tablet in the example).

## Scenes
`SCENES = [dict(t0, t1, fn, bg=colour, layer="stage"|"over", enter="slam"|None)]`. `fn(c, t)` draws in the 1080x1440 reference space (auto-fitted to any aspect).
Stage scenes sit under the presenter; `over` scenes sit above it, on full-frame shots. With no scene active, a full-frame presenter with captions shows.
Other helpers: `text text_w pill card badge dome rays star`. `card(...)` returns a closure: call it to end the card's local coordinates.

## Sound
Sound effects on every visual event and no music by default (`MUSIC = None`). Master -14 LUFS (-12 for Douyin), true peak at most -1 dB. SFX kinds are the same as Template 1; `pop`, `swish`, `stamp` and `rise` suit this look best.

## Feedback log (keep appending)
- Wanted a WebUI look: white cards, vibrant palette, cartoonish but not childish, better type, non-linear bouncy MG motion.
- The animation effects were approved.
- A frozen corner tile was wrong: the presenter must be live video.
- Background music removed; sound effects kept.
- The presenter must not be limited to the top-right.
