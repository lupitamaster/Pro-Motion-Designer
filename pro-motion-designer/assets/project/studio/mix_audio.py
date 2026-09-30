"""Build the soundtrack from a composition's timeline.

  python studio/mix_audio.py out/<name>.timeline.json out/<name>_mix.wav

Reads project.json (music file/start/fade/bed level, sfx files, balance, loudness target) and
audio/analysis.json (measured peaks). Every event in the timeline whose type has a sound in
project.json → sfx is placed so the sound's *measured peak* lands on the event time. 'type'
events place one keystroke per character (sliced from the typing recording at its measured hits).
Balance is adaptive: each sound sits a fixed number of dB over the music around its own peak,
within absolute limits, so a whoosh in a quiet intro isn't deafening and one in the chorus isn't lost.
Writes the mix (loudness-normalised, two-pass loudnorm), plus <out>.sfx.wav / <out>.music.wav stems
and <out>.wav.placed.json, which check_film.py uses to verify timing and balance.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

SR = 48000
ROOT = Path.cwd()
DEFAULT_BALANCE = {'whoosh': [3, -26, -2], 'impact': [5, -14, 0], 'click': [3, -18, 0], 'chime': [3, -20, -2],
                   'pop': [-3, -28, -8], 'type': [-4, -30, -10]}


def load(path, start=None, dur=None):
    cmd = ['ffmpeg', '-v', 'error']
    if start:
        cmd += ['-ss', f'{start:.4f}']
    cmd += ['-i', str(path)]
    if dur is not None:
        cmd += ['-t', f'{dur:.4f}']
    cmd += ['-ac', '2', '-ar', str(SR), '-f', 'f32le', '-']
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64).reshape(-1, 2)


def db(g):
    return 10 ** (g / 20)


def rms(x):
    return np.sqrt(np.mean(x ** 2) + 1e-12)


def main(timeline_path, out_path):
    pj = json.loads((ROOT / 'project.json').read_text(encoding='utf8'))
    tl = json.loads(Path(timeline_path).read_text(encoding='utf8'))
    dur = tl['meta']['duration']
    n = int(round(dur * SR))
    an = json.loads((ROOT / 'audio' / 'analysis.json').read_text(encoding='utf8'))['sfx']
    bal = {**DEFAULT_BALANCE, **{k: v for k, v in (pj.get('sfx_balance') or {}).items() if not k.startswith('_')}}
    clips = {k: load(ROOT / f) for k, f in (pj.get('sfx') or {}).items() if (ROOT / f).exists() and k in an}

    mc = pj.get('music') or {}
    if mc.get('file') and (ROOT / mc['file']).exists():
        music = load(ROOT / mc['file'], mc.get('start', 0), dur)
        music = np.pad(music, ((0, max(0, n - len(music))), (0, 0)))[:n]
        fade = np.ones(n)
        f0 = int((dur - mc.get('fade_out', 1.2)) * SR)
        fade[f0:] = np.cos(np.linspace(0, np.pi / 2, n - f0)) ** 2
        music *= fade[:, None] * db(mc.get('bed_db', -3))
    else:
        print('no music file: mixing SFX only')
        music = np.zeros((n, 2))
    mono_music = music.mean(1)

    keys = []
    if 'type' in clips:
        for h in an['type']['hits_s']:
            a, b = int((h - 0.012) * SR), int((h + 0.075) * SR)
            k = clips['type'][max(0, a):b].copy()
            k[:48] *= np.linspace(0, 1, 48)[:, None]
            k[-240:] *= np.linspace(1, 0, 240)[:, None]
            keys.append(k)

    sfx = np.zeros((n, 2))
    placed, skipped = [], {}

    def put(clip, peak, t, extra, kind, target):
        over, lo, hi = bal.get(kind, [0, -30, 0])
        c, p = int(t * SR), int(peak * SR)
        m = rms(mono_music[max(0, c - 2400):c + 2400])
        s_ = rms(clip.mean(1)[max(0, p - 2400):p + 2400])
        g = min(hi, max(lo, 20 * np.log10(m / s_) + over + extra))
        start = int(round((t - peak) * SR))
        a, b = max(0, start), min(n, start + len(clip))
        if b <= a:
            return
        sfx[a:b] += clip[a - start:b - start] * db(g)
        placed.append({'t': t, 'kind': kind, 'target': target, 'gain_db': round(g, 1), 'peak_at': round((start + peak * SR) / SR, 5)})

    last_key, ki = -1.0, 0
    for e in tl['events']:
        kind = e['type']
        if kind == 'camera':
            continue
        if kind == 'type':
            if not keys:
                skipped['type'] = skipped.get('type', 0) + 1
                continue
            for c in e['chars']:
                if c - last_key < 0.038:
                    continue
                put(keys[ki % len(keys)], 0.012, c, -2 if ki % 3 else 0, 'type', e['target'])
                ki += 1
                last_key = c
            continue
        if kind not in clips:
            skipped[kind] = skipped.get(kind, 0) + 1
            continue
        clip, peak = clips[kind], an[kind]['sample_peak_s']
        if kind == 'pop':  # small deterministic pitch variation so repeats don't machine-gun
            r = 2 ** ([0, 2, -1, 1, -2, 0.5][len(placed) % 6] / 12)
            idx = np.arange(0, len(clip) - 1, r)
            clip = np.stack([np.interp(idx, np.arange(len(clip)), clip[:, ch]) for ch in (0, 1)], axis=1)
            peak = peak / r
        put(clip, peak, e['t'], e.get('gain', 0) / 2, kind, e['target'])

    mix = music + sfx
    pk = np.abs(mix).max()
    if pk > 0.98:
        mix, sfx, music = mix * 0.98 / pk, sfx * 0.98 / pk, music * 0.98 / pk
    out = Path(out_path)
    raw = out.with_suffix('.raw.wav')
    write_wav(raw, mix)
    write_wav(out.with_suffix('.sfx.wav'), sfx)
    write_wav(out.with_suffix('.music.wav'), music)
    L = pj.get('loudness') or {}
    loudnorm(raw, out, L.get('lufs', -14), L.get('true_peak', -1))
    raw.unlink()
    Path(str(out) + '.placed.json').write_text(json.dumps(placed, indent=1), encoding='utf8')
    print(f'{len(placed)} sounds placed -> {out}')
    if skipped:
        print('events with no sound configured (add them to project.json -> sfx):', skipped)


def write_wav(path, x):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-', '-c:a', 'pcm_s24le', str(path)],
                   input=np.clip(x, -1, 1).astype(np.float32).tobytes(), check=True)


def loudnorm(src, dst, I=-14.0, TP=-1.0, LRA=11.0):
    first = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(src), '-af', f'loudnorm=I={I}:TP={TP}:LRA={LRA}:print_format=json', '-f', 'null', '-'],
                           capture_output=True, text=True, check=True).stderr
    m = json.loads(first[first.rindex('{'):first.rindex('}') + 1])
    if m['input_i'] in ('-inf', 'inf'):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(src), '-c:a', 'pcm_s24le', str(dst)], check=True)
        return
    af = (f"loudnorm=I={I}:TP={TP}:LRA={LRA}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(src), '-af', af, '-ar', str(SR), '-c:a', 'pcm_s24le', str(dst)], check=True)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
