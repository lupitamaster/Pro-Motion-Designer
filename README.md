# Pro Motion Designer

A Claude Code skill that works like a small motion studio: it takes a company from "we need a product video" to a finished, brand-true SaaS product film — launch video, product demo, promo or social reel — authored in code and checked frame by frame before anyone watches it.

No After Effects. Every frame of the film is a pure function of time in an HTML composition, rendered deterministically with Playwright + ffmpeg at 60 fps with motion blur.

## What it does

The skill guides Claude through nine phases and **stops for your approval at every decision point**:

1. **Intake** — asks for everything up front: product, audience, channel, format, duration, brand assets, references, constraints.
2. **Environment** — checks and installs dependencies, scaffolds a project, renders a pipeline test.
3. **Brand brief** — ingests yours, or drafts one from your website's real CSS tokens and copy plus a short interview. The brief's don'ts become lint rules.
4. **References** — recommends galleries, communities, component/FX libraries, music, SFX and fonts (with licence notes); breaks down any reference video into timestamped contact sheets and a palette.
5. **Music & sound** — screens licence-clear tracks, asks before downloading, measures tempo, beat grid, drop and section map, and each SFX's peak.
6. **Structure** — a scene chain with no cuts, an event on every beat, a cue list, and the verbatim product content each scene needs.
7. **Build** — composes scene by scene with a tested toolkit (typed lines, mask reveals, floods, camera, cursor), reviewed on stills.
8. **Render, mix, self-check** — 60 fps with motion blur; every SFX placed on its measured peak; −14 LUFS mix; an automated check of every frame, beat, camera move, sound and brand rule. Nothing is shown until it passes.
9. **Delivery** — the film, the check report, and a short list of decisions to review.

### House rules (defaults, adjustable per film)
1. Nothing fades in; things change shape.
2. No cuts; every scene comes out of the last one.
3. Something happens on every beat.
4. Things bounce a tiny bit when they land.
5. The camera does one move at a time.
6. Every click and whoosh has a real sound.
7. It checks its own work before you watch it.

## Install

Copy the `pro-motion-designer` folder into your Claude Code skills directory:

```bash
git clone https://github.com/lupitamaster/Pro-Motion-Designer.git
cp -r Pro-Motion-Designer/pro-motion-designer ~/.claude/skills/
```

Then ask Claude Code something like *"make a 45-second launch video for our product"* or *"break down this SaaS ad and make one like it for us"*.

### Requirements
Node 18+, Python 3.9+ (numpy, pillow, matplotlib), ffmpeg, and Playwright with Chromium. The skill's `scripts/check_env.py` reports what's missing and prints the install command for your OS.

## What's inside

```
pro-motion-designer/
├── SKILL.md                  the workflow and its approval gates
├── scripts/
│   ├── check_env.py          dependency check + install commands per OS
│   └── new_project.py        scaffolds a project from assets/project
├── references/               read by Claude at each phase
│   ├── intake.md  brand-brief.md  resources.md  audio.md
│   └── house-rules.md  structure.md  toolkit.md
└── assets/project/           the studio copied into every new project
    ├── project.json          size, fps, duration, bpm, music, sfx, balance, loudness, brand lint
    ├── studio/               render.mjs · analyze_audio.py · mix_audio.py · check_film.py
    │                         reference_frames.py · sheet.py
    ├── lib/                  kit.js (composition toolkit) · spring.js (springs, camera easing)
    ├── comps/main/           an 8 s template film that passes every check
    ├── comps/test-pill/      2 s pipeline test
    └── brand/                BRIEF / INTAKE / STRUCTURE templates · brand.js tokens
```

## Español

Una skill de Claude Code que arma el video de producto SaaS de cualquier empresa como lo haría un estudio de motion design: entrevista inicial, brief de marca, referencias, música, estructura por beats, construcción, render a 60 fps con motion blur, mezcla y una revisión automática cuadro por cuadro. Se frena en cada decisión para preguntar o pedir aprobación, pide permiso antes de descargar cualquier archivo y solo muestra contenido real del producto.

## License

MIT — see [LICENSE](LICENSE). Music, SFX, fonts and footage you download while using the skill keep their own licences; the skill asks you to check each one.
