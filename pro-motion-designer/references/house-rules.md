# House rules (default for every film — confirm or adjust with the client)

| # | Rule | In practice | How it's checked |
|---|---|---|---|
| 1 | **Nothing fades in; things change shape.** A button grows into the next page. | No opacity or blur tweens. Things enter by growing out of something already on screen (usually the motif) or by being typed; they leave by shrinking into something or rising out through a mask line. Masks and draw-ons count as shape changes. | Lint: no animated `opacity` / `blur` in composition code. |
| 2 | **No cuts.** Every scene comes out of the last one. | Each scene starts from the previous scene's final shape (the "Out → next" column). No cut to black; the film ends holding its end card. Hard camera resets only while the frame is fully covered (e.g. by a flood). | Render: no frame where >40% of pixels change at once. |
| 3 | **Something happens on every beat.** | Beat map with an event per beat; bigger events on downbeats. At 120 BPM: 2 events per second. | Render: visible change within ±2 frames of every beat. |
| 4 | **Things bounce a tiny bit when they land.** | `LAND` (≈4.6% overshoot, settles 0.30 s) for landings, `MORPH` (≈4.3%, 0.40 s) for shape changes. Both settle before the next beat. Cameras don't bounce. | Overshoot 2–8% and settle < 1 beat, computed from `lib/spring.js`. |
| 5 | **The camera does one move at a time.** | Push, pull, pan or orbit — never two at once; moves start and end on beats (`cameraMove`). | Timeline: camera moves never overlap; start on a beat. |
| 6 | **Every click and whoosh has a real sound.** | Recorded SFX only (never synthesised), each placed so its measured peak lands on its event. | Stem cross-correlation: peak within 1 frame; balance vs music; loudness. |
| 7 | **It checks its own work before anyone watches it.** | `check_film.py` + a 2 fps contact sheet you actually look at. Fix the cause, re-render, re-check. | The report ends in PASSED; it ships with the video. |

Plus the brand's own rules from its brief (banned words, claims, colour codings), enforced by `brand_lint` and the human checklist.

## Why these rules
They make a film feel like one continuous, physical object instead of a slideshow: shapes persist, the eye is never asked to re-find its place (no cuts), the rhythm is readable (every beat), motion feels material (tiny bounce), attention isn't split (one camera move), and nothing is silent that looks like it should make a sound. The self-check exists because a 2880-frame film has too many frames to trust by eye — and because a single-frame glitch is exactly what viewers notice.
