---
name: pro-motion-designer
description: End-to-end studio for making a company's own SaaS / software product video (launch film, product demo, promo, reel) in code — brand brief, reference breakdown, music beat-grid, scene-by-scene motion design, 60fps render with motion blur, SFX placed on their measured peaks, loudness mix and an automated frame-by-frame self-check. Use this skill whenever someone wants a product video, launch video, demo video, promo, explainer-style motion piece or social reel for an app, startup, SaaS or web product — even if they only say "make a video like this one for my product", share a reference video, ask to "break down" a SaaS ad, or want to set up a reusable video pipeline for their brand. It interviews the user for requirements, installs dependencies, builds or ingests the brand brief, recommends where to find references, components and FX, and stops for approval at every decision point.
---

# Pro Motion Designer — SaaS product video studio

This skill turns a company's product into a finished, brand-true product video, the way a small motion studio would: brief → references → music → structure → build → render → self-check → delivery. Everything is authored as an HTML composition whose every frame is a pure function of time, rendered deterministically with Playwright + ffmpeg. No After Effects needed.

It was distilled from a real production (a 48 s launch film for a media-tech startup). The hard-won lessons from that production are written into the references; read them before building, they save hours.

## How to work with the user

- **Speak the user's language** (if they write in Spanish, answer in Spanish, and write on-screen copy in their brand's language/voice).
- **Stop at every gate** marked ⛔ below. At a gate, summarise what you have, list the decisions you need, and wait. Use AskUserQuestion for choices with clear options; plain questions otherwise. Never barrel through a gate because you could guess — the brief, the content and the look are the client's calls.
- **Ask for downloads.** Before downloading any file (music, SFX, fonts, images, footage), list filename, source and size and wait for a yes. Prefer measuring with metadata/HEAD requests first.
- **Never type credentials.** If product content sits behind a login, open the page and let the user sign in themselves.
- **Real content only.** Product titles, data, quotes and UI strings shown in the video are copied verbatim from the real product. Never invent product data, user counts or metrics. If something shows broken characters, leave it out rather than "fixing" it — or ask.
- **Say what you verified and what you didn't.** If a check failed, say so; if you guessed, say so.

## Phases

Keep a todo list with these phases. Each phase ends in a concrete file the user can look at.

### 1. Intake ⛔
Ask everything at once (group it, don't drip-feed). Read `references/intake.md` for the full question list. The essentials:
- Company, product, URL, what it does in one sentence, audience, the one thing the video must make people feel/do.
- Channel(s), format(s) (16:9 / 1:1 / 4:5 / 9:16), duration, deadline, who approves.
- Do they have a **brand brief / guidelines**? (If yes: get it. If no: you will draft one in phase 3.)
- Assets they can give: logo files, fonts, product screenshots/recordings, access to the product, reference videos they like, music taste, things to avoid (legal, claims, competitors).
Output: `brand/INTAKE.md` summarising answers + open questions.

### 2. Environment setup
Run `python <skill>/scripts/check_env.py` — it reports Node, npm, Python packages, ffmpeg, Playwright/Chromium and prints the install command for this OS. Install what's missing (tell the user what you're installing; system package managers like winget/brew/apt may need their OK). `sudo` commands need the user's password, and Claude Code's `!` prefix can't pass it on: ask the user to run them in their own terminal. If the check says this Python is externally managed (PEP 668), put the Python packages in a venv in the project folder, as the check prints, and run every `studio/*.py` with `.venv/bin/python` (`.venv\Scripts\python` on Windows) instead of `python`. Then scaffold the project:

```bash
python <skill>/scripts/new_project.py --dir <project-folder> --name <slug> --size 1920x1080 --fps 60 --duration 48
cd <project-folder> && npm install && npx playwright install chromium
node studio/render.mjs comps/test-pill/index.html out/test-pill.mp4
```
Show the user the first and last frame of the test render (`ffmpeg -ss ... -frames:v 1`). This proves the pipeline before any creative work.

### 3. Brand brief ⛔
The brief is what every later decision leans on (copy, colours, what may and may not be claimed). Read `references/brand-brief.md`.
- **They have one:** normalise it into `brand/BRIEF.md` (keep their text; add an "updates" block for anything the user corrects later — e.g. "the web app is already public" — so it isn't reverted).
- **They don't:** draft it from their website (pull real fonts and colour tokens from the site's CSS, real copy, screenshots), the intake, and a short interview. Mark every inferred item as *inferred* until confirmed.
- Fill `brand/brand.js` (tokens: colours for light/dark, fonts, accent, radius) from the brief.
- Write the **do/don't list** as data in `project.json → brand_lint` so the self-check enforces it.
Get explicit approval of the brief before moving on.

### 4. References & inspiration ⛔
- Recommend where to look (`references/resources.md`: reference galleries, communities, component/FX libraries, music/SFX/footage/fonts with licence notes). Tailor it: 5–8 picks that fit this brand, not the whole list.
- If the user shares a reference video, break it down: `python studio/reference_frames.py <video> out/ref --fps 2` → contact sheets → read them → write `brand/REFERENCE_BREAKDOWN.md` (beats, how each scene turns into the next, camera moves, colours sampled from frames, fonts). Method in `references/structure.md`.
- Propose what to borrow and what to leave (anything that clashes with the brief or the house rules).
Stop and confirm direction.

### 5. Music & sound ⛔
Read `references/audio.md`. Find 1–3 licence-clear tracks (~120 BPM with a clear drop suits product films) and one SFX per event type (typing, whoosh, click, pop, chime, impact). Screen candidates without downloading when the source exposes waveform/metadata. Present filename/source/size/licence → wait for approval → download to `audio/` → set paths in `project.json` → `python studio/analyze_audio.py`. Report BPM, first downbeat, drop time, the section map, and each SFX's peak; flag SFX that don't behave as their name promises (e.g. a "riser" that doesn't rise). Choose `music.start` so the drop lands on the film's key moment (`analyze_audio.py --drop-at <seconds>` prints it).

### 6. Structure ⛔
Read `references/house-rules.md` and `references/structure.md`. Write `brand/STRUCTURE.md`:
- the rules for this film (default: the 7 house rules — ask if they want to change any),
- a **scene chain** where each scene's last shape is the next scene's first shape,
- a **beat map** with an event on every beat (bigger events on downbeats),
- a **cue list** (every click/whoosh has a real sound),
- the verbatim product content each scene needs, and where it comes from.
Lint the copy against the brief's don'ts before showing it. Get approval. This is the cheapest place to change the film.

### 7. Build
Read `references/toolkit.md` first (composition API + the gotchas list). Build in `comps/<name>/` starting from the template (`comps/main/`), with product strings in `data.js`. Work scene by scene and check with stills:

```bash
node studio/render.mjs comps/<name>/index.html --stills 1.2,5.5,12 --outdir out/stills
python studio/sheet.py out/stills out/review 3 9 640
```
Look at every sheet yourself and fix what's wrong before showing anything. ⛔ Show the user 3–4 key stills (opening, a product moment, the key message, the end card) before the full render.

### 8. Render, mix, self-check
```bash
node studio/render.mjs comps/<name>/index.html out/<name>.mp4 --subframes 4 --shutter 0.5
python studio/mix_audio.py out/<name>.timeline.json out/<name>_mix.wav
python studio/check_film.py out/<name>.mp4 out/<name>.timeline.json out/<name>_mix.wav comps/<name>
```
The renderer picks its worker count from free RAM and cores and prints it; leave `--workers` off unless you have a reason. Each worker (a Chromium page + an x264 encoder) needs ~1 GB at 1080p, and too many can crash the machine; WSL is the usual case, since it only gets part of the host's RAM. If a render dies, delete the leftover `out/<name>.seg*.mp4` files and render again with fewer workers.
`check_film.py` checks every frame (no cuts, no single-frame pops, no long freezes; small elements that switch on or off in one frame are a warning — look at each and make it shrink, rise or be covered), motion on every beat, camera moves, spring presets, no fades in code, every click/whoosh has a sound whose peak lands on its event, SFX-vs-music balance, loudness, and the brand lint. Pops (reveals and landings) aren't covered by the automatic timing check: verify them with `studio/sync_probe.py` — reveals sound at their onset, landings at the impact, no two sounds within 150 ms. **Do not show the video until it passes.** When it fails, find the real cause (look at the frames around the timestamp), fix the composition, re-render. Then build a 2 fps contact sheet of the final and look at all of it.

### 9. Deliver ⛔
Mux (`ffmpeg -i video -i mix -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -shortest -movflags +faststart <Brand>_<format>_<dur>_v<n>.mp4`), send the file, and report in a short message: what it is, what was verified (the check report), decisions you took that they should review (content choices, anything risky vs the brief, skipped assets), and open questions. Offer next steps: other formats (re-laid out, not cropped), a handoff roadmap for their team, turning their project into a reusable kit.

## Files in this skill
- `scripts/check_env.py` — dependency check + install commands per OS.
- `scripts/new_project.py` — scaffolds a project from `assets/project/`.
- `assets/project/` — the studio (renderer, audio analysis, mixer, self-check, contact sheets, reference breakdown), the composition kit (`lib/kit.js`, `lib/spring.js`), a working template composition, brand/brief templates.
- `references/intake.md`, `brand-brief.md`, `resources.md`, `audio.md`, `house-rules.md`, `structure.md`, `toolkit.md` — read each at its phase.
