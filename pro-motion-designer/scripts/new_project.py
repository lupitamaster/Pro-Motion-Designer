"""Scaffold a product-video project from the skill's template.

  python new_project.py --dir ./acme-video --name acme-launch --size 1920x1080 --fps 60 --duration 48 [--bpm 120]

Creates:
  <dir>/project.json      single source of truth: size, fps, duration, bpm, music, sfx, loudness, brand lint
  <dir>/package.json      playwright dev dependency + render script
  <dir>/studio/           render.mjs, analyze_audio.py, mix_audio.py, check_film.py, sheet.py, reference_frames.py
  <dir>/lib/              kit.js (composition toolkit), spring.js (springs, camera easing)
  <dir>/comps/main/       working template composition (copy it for each film)
  <dir>/comps/test-pill/  2 s pipeline test
  <dir>/brand/            BRIEF.md, INTAKE.md, STRUCTURE.md templates, brand.js tokens
  <dir>/audio/ fonts/ out/
Refuses to overwrite an existing project.json unless --force.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL / 'assets' / 'project'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', required=True)
    ap.add_argument('--name', required=True)
    ap.add_argument('--size', default='1920x1080')
    ap.add_argument('--fps', type=int, default=60)
    ap.add_argument('--duration', type=float, default=48)
    ap.add_argument('--bpm', type=float, default=120)
    ap.add_argument('--force', action='store_true')
    a = ap.parse_args()
    w, h = map(int, a.size.lower().split('x'))
    dst = Path(a.dir).resolve()
    if (dst / 'project.json').exists() and not a.force:
        sys.exit(f'{dst / "project.json"} already exists (use --force to overwrite the template files)')
    dst.mkdir(parents=True, exist_ok=True)
    for item in TEMPLATE.iterdir():
        target = dst / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target)
    for d in ('audio', 'fonts', 'out', 'comps/main/img'):
        (dst / d).mkdir(parents=True, exist_ok=True)
    pj = json.loads((dst / 'project.json').read_text(encoding='utf8'))
    pj.update({'name': a.name, 'width': w, 'height': h, 'fps': a.fps, 'duration': a.duration, 'bpm': a.bpm})
    (dst / 'project.json').write_text(json.dumps(pj, indent=2, ensure_ascii=False), encoding='utf8')
    pk = json.loads((dst / 'package.json').read_text(encoding='utf8'))
    pk['name'] = a.name
    (dst / 'package.json').write_text(json.dumps(pk, indent=2), encoding='utf8')
    print(f'project scaffolded at {dst}')
    print('next: cd there, npm install, npx playwright install chromium, node studio/render.mjs comps/test-pill/index.html out/test-pill.mp4')


if __name__ == '__main__':
    main()
