"""Self-check for a rendered film. Nothing is shown to the client until this passes.

  python studio/check_film.py out/<name>.mp4 out/<name>.timeline.json out/<name>_mix.wav comps/<name>

Checks (reads project.json for fps, bpm, sfx files and the brand lint):
  video   every frame: no cuts (>40% of pixels change at once), no single-frame pops (change > 3x
          its neighbours), no frozen stretch > 1 s, visible change on every beat
  motion  camera moves never overlap and start on a beat; LAND/MORPH overshoot 2-8% and settle in a beat;
          no opacity/blur animation in the composition code
  sound   every click/whoosh/chime/impact event has a sound whose peak lands within 1 frame (verified by
          cross-correlating the SFX stem); each sound's level vs the music; integrated loudness + true peak
  brand   on-screen strings in the composition: banned words from project.json, exclamation marks
Exits 1 on any failure.
"""
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

video, timeline, mixwav, compdir = sys.argv[1:5]
ROOT = Path.cwd()
pj = json.loads((ROOT / 'project.json').read_text(encoding='utf8'))
FPS = pj.get('fps', 60)
BEAT = 60 / pj.get('bpm', 120)
W, H = 480, 270
fails, warns, lines = [], [], []
ok = lambda m: lines.append('  PASS  ' + m)
bad = lambda m: (fails.append(m), lines.append('  FAIL  ' + m))
warn = lambda m: (warns.append(m), lines.append('  WARN  ' + m))

# ------------------------------------------------------------------ video, every frame
st = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v', '-show_entries',
                                'stream=r_frame_rate,nb_read_frames,width,height', '-of', 'json', video],
                               capture_output=True, text=True, check=True).stdout)['streams'][0]
nframes = int(st['nb_read_frames'])
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', video, '-vf', f'scale={W}:{H},format=gray', '-f', 'rawvideo', '-'], capture_output=True, check=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.int16)
lines.append(f'Video: {st["width"]}x{st["height"]}, {st["r_frame_rate"]} fps, {nframes} frames')
(ok if st['r_frame_rate'] == f'{FPS}/1' else bad)(f'{FPS} fps')
diff = np.abs(np.diff(fr, axis=0))
d = np.concatenate([[0], diff.mean(axis=(1, 2))])
frac = np.concatenate([[0], (diff > 40).mean(axis=(1, 2))])
moved = np.concatenate([[0], (diff > 12).sum(axis=(1, 2))])
cuts = [(i, frac[i]) for i in range(1, len(d)) if frac[i] > 0.40]
(bad if cuts else ok)(f'no cuts (frames where >40% of pixels change at once): {len(cuts)}' + ''.join(f'\n          t={i / FPS:.3f}s ({f:.0%})' for i, f in cuts[:10]))
pops = []
for i in range(3, len(d) - 3):
    base = max(np.median(np.concatenate([d[i - 3:i], d[i + 1:i + 4]])), 0.25)
    if d[i] > 3 * base and d[i] > 1.2:
        pops.append((i, d[i], base))
(bad if pops else ok)(f'no single-frame pops (change > 3x neighbours): {len(pops)}' + ''.join(f'\n          t={i / FPS:.3f}s  change {v:.2f} vs {b:.2f}  (look at these frames)' for i, v, b in pops[:15]))
run = longest = where = 0
for i in range(1, len(d)):
    run = run + 1 if d[i] < 0.02 else 0
    if run > longest:
        longest, where = run, i
(ok if longest <= FPS else warn)(f'longest frozen stretch: {longest / FPS:.2f}s (ends {where / FPS:.2f}s)')
nbeats = int(round(nframes / FPS / BEAT))
silent = []
for n in range(nbeats):
    f = int(round(n * BEAT * FPS))
    a, b = (1, 7) if n == 0 else (max(1, f - 2), min(len(d), f + 3))  # beat 0 has no frames before it
    m = moved[a:b].max() if b > a else 0
    if m < 8:
        silent.append((n, m))
(bad if silent else ok)(f'every beat has visible change (>=8 px at {W}x{H} within 2 frames): {nbeats - len(silent)}/{nbeats}' + ''.join(f'\n          beat {n} ({n * BEAT:.2f}s) changed pixels {m}' for n, m in silent))

# ------------------------------------------------------------------ motion rules
ev = json.loads(Path(timeline).read_text(encoding='utf8'))['events']
cams = sorted([e for e in ev if e['type'] == 'camera'], key=lambda e: e['t'])
overlap = [(a['t'], b['t']) for a, b in zip(cams, cams[1:]) if b['t'] < a['end'] - 1e-6]
offgrid = [e['t'] for e in cams if abs(e['t'] / BEAT - round(e['t'] / BEAT)) > 1e-6]
(bad if overlap else ok)(f'camera: {len(cams)} moves, none overlapping' + (f' (overlaps {overlap})' if overlap else ''))
(ok if not offgrid else warn)('camera moves start on a beat' + (f' (off-grid: {offgrid})' if offgrid else ''))


def spring(t, k, c):
    w0, z = math.sqrt(k), c / (2 * math.sqrt(k))
    wd = w0 * math.sqrt(1 - z * z)
    return 1 + math.exp(-z * w0 * t) * (-math.cos(wd * t) - (z * w0 / wd) * math.sin(wd * t))


src = (ROOT / 'lib' / 'spring.js').read_text(encoding='utf8')
for name in ('LAND', 'MORPH'):
    k, c = map(float, re.search(name + r' = \{ stiffness: (\d+), damping: (\d+)', src).groups())
    vals = [spring(i / 1000, k, c) for i in range(1, 2000)]
    over = max(vals) - 1
    settle = max([i / 1000 for i, v in enumerate(vals, 1) if abs(v - 1) > 0.02] or [0])
    (ok if 0.02 <= over <= 0.08 and settle < BEAT else bad)(f'{name}: overshoot {over:.1%}, settles {settle:.2f}s (beat {BEAT:.2f}s)')
code = '\n'.join(p.read_text(encoding='utf8') for p in Path(compdir).glob('*.js'))
fade_hits = [m.group(0) for m in re.finditer(r'\.opacity\s*=|opacity:\s*[^0-9\'"]|filter\s*[:=][^;\n]*blur|blur\(', code)]
(bad if fade_hits else ok)('no opacity/blur animation in the composition' + (f': {fade_hits[:5]}' if fade_hits else ''))

# ------------------------------------------------------------------ sound
mix = Path(mixwav)
if mix.exists() and mix.with_suffix('.sfx.wav').exists():
    def load(path):
        r = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-ac', '1', '-ar', '48000', '-f', 'f32le', '-'], capture_output=True, check=True).stdout
        return np.frombuffer(r, np.float32).astype(np.float64)
    SR = 48000
    sfx, music = load(mix.with_suffix('.sfx.wav')), load(mix.with_suffix('.music.wav'))
    placed = json.loads(Path(str(mix) + '.placed.json').read_text(encoding='utf8'))
    an = json.loads((ROOT / 'audio' / 'analysis.json').read_text(encoding='utf8'))['sfx']
    need = [e for e in ev if e['type'] in ('click', 'whoosh', 'chime', 'impact')]
    have = {(p['kind'], round(p['t'], 3)) for p in placed}
    missing = [e for e in need if (e['type'], round(e['t'], 3)) not in have]
    (bad if missing else ok)(f'every click/whoosh/chime/impact event has a sound: {len(need) - len(missing)}/{len(need)}' + ''.join(f"\n          missing {e['type']} at {e['t']}s ({e['target']})" for e in missing))
    errs, bal, templ = [], {}, {}
    for e in need:
        if e['type'] not in an:
            continue
        if e['type'] not in templ:
            templ[e['type']] = load(ROOT / pj['sfx'][e['type']])
        t_ = templ[e['type']]
        p = int(an[e['type']]['sample_peak_s'] * SR)
        seg = t_[max(0, p - 2400):p + 2400]
        c = int(e['t'] * SR)
        win = sfx[max(0, c - 4800):c + 4800]
        if len(win) < len(seg):
            continue
        lag = int(np.argmax(np.abs(np.correlate(win, seg, 'valid'))))
        found = (max(0, c - 4800) + lag + (p - max(0, p - 2400))) / SR
        errs.append(abs(found - e['t']))
        a, b = max(0, c - 2400), c + 2400
        r = lambda x: 20 * np.log10(np.sqrt(np.mean(x[a:b] ** 2)) + 1e-9)
        bal.setdefault(e['type'], []).append(r(sfx) - r(music))
    worst = max(errs) if errs else 0
    (ok if worst <= 1 / FPS else bad)(f'sound peaks land on their events: worst offset {worst * 1000:.1f} ms (limit {1000 / FPS:.1f} ms)')
    for kind, v in bal.items():
        (ok if min(v) > -6 and max(v) < 16 else warn)(f'balance {kind}: {min(v):+.1f} to {max(v):+.1f} dB over the music at its peak')
    er = subprocess.run(['ffmpeg', '-hide_banner', '-i', mixwav, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    s = er[er.rindex('Summary'):]
    I = float(re.search(r'I:\s+(-?[\d.]+) LUFS', s).group(1)); TP = float(re.search(r'Peak:\s+(-?[\d.]+) dBFS', s).group(1))
    L = pj.get('loudness') or {}
    (ok if abs(I - L.get('lufs', -14)) <= 0.5 and TP <= L.get('true_peak', -1) + 0.1 else bad)(f"loudness {I:.1f} LUFS (target {L.get('lufs', -14)}), true peak {TP:.1f} dBTP")
else:
    warn('sound checks skipped (no mix / stems yet — run studio/mix_audio.py)')

# ------------------------------------------------------------------ brand lint (on-screen strings)
lint = pj.get('brand_lint') or {}
STR = r"'([^'\n]*)'|\"([^\"\n]*)\"|`([^`]*)`"
strings = lambda path: [s for g in re.findall(STR, path.read_text(encoding='utf8')) for s in g if s]
content = []  # data files + brand tokens: every string there is on-screen content
for p in list(Path(compdir).glob('data*.js')) + [ROOT / 'brand' / 'brand.js']:
    if p.exists():
        content += strings(p)
code_like = re.compile(r'[{}();=<>$]|^[\w.-]+$|\dpx|#[0-9a-f]{3,}', re.I)
for p in Path(compdir).glob('*.js'):  # composition code: only strings that read like prose
    if not p.name.startswith('data'):
        content += [s for s in strings(p) if re.search(r'[^\W\d_]{2,}', s) and not code_like.search(s)]
# typed copy is often split into chunks ('Your product,' ' in one' ' sentence.'): lint the chunks
# joined as well as spaced, whitespace-normalised
joined = re.sub(r'\s+', ' ', ''.join(content)).lower()
prose = re.sub(r'\s+', ' ', ' '.join(content)).lower()
hits = [b for b in lint.get('banned', []) if any(re.search(r'(?<!\w)' + re.escape(b.lower()), x) for x in (joined, prose))]
excl = [] if lint.get('allow_exclamation') else re.findall(r'[^\W\d_]!|¡', prose)
(bad if hits or excl else ok)('brand lint (banned words from the brief, exclamation marks)' + (f': {hits + excl}' if hits or excl else ''))
if re.search(r'PLACEHOLDER', '\n'.join(p.read_text(encoding='utf8') for p in Path(compdir).glob('data*.js'))):
    warn('data.js still marked PLACEHOLDER — product content must be verbatim from the real product before delivery')

print('\n'.join(lines))
print(f'\n{"FAILED" if fails else "PASSED"}: {len(fails)} failures, {len(warns)} warnings')
sys.exit(1 if fails else 0)
