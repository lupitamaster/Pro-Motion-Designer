"""Measure the music (tempo, beat grid, downbeats, drop, section map) and every SFX (peak timing).

  python studio/analyze_audio.py                 # reads project.json, writes audio/analysis.json + audio/analysis.png
  python studio/analyze_audio.py --drop-at 5.5   # also prints the music.start that puts the drop at 5.5 s of the film

numpy only for the analysis (ffmpeg decodes, matplotlib draws the check plot).
Lessons baked in: the grid is fitted on the kick band only (full-band onsets lock onto off-beat
hi-hats in house/pop and put the grid exactly half a beat late); peaks are measured per channel
(an ffmpeg mono downmix can exceed full scale); the per-bar section map shows where the drop,
breakdown and return are so music edits land on phrase boundaries.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

SR = 44100
HOP = 256
N_FFT = 2048
ROOT = Path.cwd()


def load(path, stereo=False):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).astype(np.float64).reshape(-1, 2)
    return x if stereo else x.mean(1)


def stft_mag(x):
    win = np.hanning(N_FFT)
    n = 1 + (len(x) - N_FFT) // HOP
    idx = np.arange(N_FFT)[None, :] + HOP * np.arange(n)[:, None]
    return np.abs(np.fft.rfft(x[idx] * win, axis=1))


def onset_envelope(mag, lo_hz=0, hi_hz=None):
    freqs = np.fft.rfftfreq(N_FFT, 1 / SR)
    band = (freqs >= lo_hz) & (freqs < (hi_hz or SR))
    flux = np.maximum(np.diff(np.log1p(1000 * mag[:, band]), axis=0), 0).sum(1)
    flux = np.concatenate([[0], flux])
    flux -= np.convolve(flux, np.ones(16) / 16, 'same')
    flux = np.maximum(flux, 0)
    return flux / (flux.max() + 1e-12)


def frame_time(i):
    return (i * HOP + N_FFT / 2) / SR


def grid_score(env, t_env, bpm, step=0.004):
    period = 60 / bpm
    best = (-1, 0.0)
    for ph in np.arange(0, period, step):
        s = np.interp(np.arange(ph, t_env[-1], period), t_env, env).mean()
        if s > best[0]:
            best = (s, ph)
    return best


def beat_grid(env, lo=70, hi=180):
    """Tempo = the candidate whose grid lands on the most kick energy.
    Candidates: the strongest autocorrelation peaks plus their 2x, 1/2x, 3/2x and 2/3x relatives
    (autocorrelation alone often picks a related false tempo, e.g. 160 for a 120 track).
    A mild prior favours 90-150 BPM, the range product films live in."""
    fps = SR / HOP
    x = env - env.mean()
    ac = np.fft.irfft(np.abs(np.fft.rfft(x, 2 * len(x))) ** 2)[: len(x)]
    lags = np.arange(int(fps * 60 / hi), int(fps * 60 / lo))
    order = lags[np.argsort(ac[lags])[::-1]]
    peaks = []
    for L in order:
        if all(abs(L - p) > 3 for p in peaks):
            peaks.append(L)
        if len(peaks) == 5:
            break
    cands = set()
    for L in peaks:
        b = 60 * fps / L
        for r in (1, 2, 0.5, 1.5, 2 / 3):
            if lo <= b * r <= hi:
                cands.add(round(b * r, 1))
    t_env = frame_time(np.arange(len(env)))
    prior = lambda b: np.exp(-0.5 * (np.log(b / 120) / 0.35) ** 2)
    scored = sorted(((grid_score(env, t_env, b)[0] * (0.7 + 0.3 * prior(b)), b) for b in cands), reverse=True)
    coarse = scored[0][1]
    best = (-1, None, None)
    for bpm in np.arange(coarse - 1.5, coarse + 1.5, 0.01):
        s, ph = grid_score(env, t_env, bpm, 0.002)
        if s > best[0]:
            best = (s, bpm, ph)
    return best[1], best[2], coarse


def db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)


def sfx_stats(xs):
    x = xs.mean(1)
    a = np.abs(xs).max(1)
    sample_peak = int(np.argmax(a))
    rms = np.sqrt(np.convolve(x ** 2, np.ones(int(0.010 * SR)) / int(0.010 * SR), 'same'))
    loud = np.sqrt(np.convolve(x ** 2, np.ones(int(0.100 * SR)) / int(0.100 * SR), 'same'))
    rp, lp = int(np.argmax(rms)), int(np.argmax(loud))
    onset = int(np.argmax(a > a[sample_peak] * 0.01))
    tail = np.flatnonzero(rms > rms[rp] * 0.01)[-1] / SR
    hits, last = [], -SR
    for i in np.flatnonzero(rms > rms[rp] * 10 ** (-12 / 20)):
        if i - last > 0.06 * SR:
            hits.append(i)
        elif rms[i] > rms[hits[-1]]:
            hits[-1] = i
        last = i
    # does the level actually build? (for risers): loudness in the last third vs the first third
    n3 = max(1, len(loud) // 3)
    build = 20 * np.log10((loud[-n3:].mean() + 1e-9) / (loud[:n3].mean() + 1e-9))
    return {'duration_s': round(len(x) / SR, 3), 'onset_s': round(onset / SR, 3), 'sample_peak_s': round(sample_peak / SR, 3),
            'rms10_peak_s': round(rp / SR, 3), 'loudness100_peak_s': round(lp / SR, 3),
            'peak_dbfs': round(20 * np.log10(a[sample_peak] + 1e-12), 1), 'tail_end_s': round(tail, 3),
            'hits_s': [round(h / SR, 3) for h in hits], 'level_build_db': round(float(build), 1)}


def main():
    pj = json.loads((ROOT / 'project.json').read_text(encoding='utf8'))
    out = {'music': None, 'sfx': {}}
    mcfg = pj.get('music') or {}
    mfile = ROOT / mcfg.get('file', '')
    if mcfg.get('file') and mfile.exists():
        x = load(mfile)
        mag = stft_mag(x)
        env_lo = onset_envelope(mag, 30, 180)
        env_hi = onset_envelope(mag, 5000)
        bpm, phase, coarse = beat_grid(env_lo)
        period = 60 / bpm
        beats = np.arange(phase, len(x) / SR, period)
        t_env = frame_time(np.arange(len(env_lo)))
        kick_on = float(np.interp(beats, t_env, env_lo).mean()); kick_off = float(np.interp(beats + period / 2, t_env, env_lo).mean())
        # loudness per bar → sections; drop candidates = biggest bar-to-bar jumps
        w = int(0.05 * SR)
        rms = np.sqrt(np.convolve(x ** 2, np.ones(w) / w, 'same')[::w]); t_r = np.arange(len(rms)) * 0.05
        ldb = 20 * np.log10(rms + 1e-9)
        k = int(4 / 0.05)
        jumps = [(ldb[i:i + k].mean() - ldb[i - k:i].mean(), t_r[i]) for i in range(k, len(ldb) - k)]
        cands = []
        for j, tt in sorted(jumps, reverse=True):
            if j < 6 or any(abs(tt - c['coarse_s']) < 6 for c in cands):
                continue
            m = (t_env > tt - 0.35) & (t_env < tt + 0.35)
            exact = float(t_env[np.flatnonzero(m)[np.argmax(env_lo[m])]])
            nb = float(beats[np.argmin(np.abs(beats - exact))])
            cands.append({'coarse_s': round(float(tt), 2), 'exact_s': round(exact, 3), 'nearest_beat_s': round(nb, 3), 'jump_db': round(float(j), 1)})
            if len(cands) == 3:
                break
        drop = cands[0] if cands else None
        db_idx = int(np.argmin(np.abs(beats - drop['exact_s']))) if drop else 0
        downbeats = beats[db_idx % 4::4]
        bars = []
        for i, b in enumerate(downbeats[:-1]):
            seg = x[int(b * SR):int(downbeats[i + 1] * SR)]
            kb = float(np.interp(b + np.arange(4) * period, t_env, env_lo).mean())
            bars.append({'bar': i + 1, 'start_s': round(float(b), 3), 'db': round(float(db(seg)), 1), 'kick': round(kb, 2)})
        out['music'] = {'file': mcfg['file'], 'duration_s': round(len(x) / SR, 3), 'bpm': round(bpm, 2), 'coarse_bpm': round(coarse, 2),
                        'beat_period_s': round(period, 4), 'first_beat_s': round(float(phase), 3), 'first_downbeat_s': round(float(downbeats[0]), 3),
                        'grid_check': {'kick_on_beat': round(kick_on, 3), 'kick_off_beat': round(kick_off, 3)},
                        'drop': drop, 'drop_candidates': cands, 'bars': bars,
                        'beats_s': [round(float(b), 3) for b in beats], 'downbeats_s': [round(float(b), 3) for b in downbeats]}
        print(f"music: {bpm:.2f} BPM (coarse {coarse:.1f}), first downbeat {downbeats[0]:.3f}s, kick on/off beat {kick_on:.2f}/{kick_off:.2f}")
        if kick_off > kick_on:
            print('  WARNING: kicks land off the grid - check the grid on the plot before trusting it')
        for c in cands:
            print(f"  drop candidate {c['exact_s']:.3f}s (+{c['jump_db']} dB), {1000 * (c['exact_s'] - c['nearest_beat_s']):+.0f} ms from grid")
        print('  bars (start s, dB, kick):')
        for b in bars:
            print(f"    {b['bar']:3d} {b['start_s']:8.3f} {b['db']:6.1f} {b['kick']:.2f} " + '#' * int(max(0, b['db'] + 45)))
        if '--drop-at' in sys.argv and drop:
            at = float(sys.argv[sys.argv.index('--drop-at') + 1])
            start = drop['exact_s'] - at
            print(f"\n  set project.json music.start = {start:.3f}  -> drop lands at {at}s of the film"
                  + ('' if start >= 0 else '  (negative: the film is longer before the drop than the track - pick an earlier drop or shorten the intro)'))
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(2, 1, figsize=(14, 6))
            tt = np.arange(len(x)) / SR
            ax[0].plot(tt[::40], x[::40], lw=.3, color='#555'); ax[0].plot(t_r, ldb / 100, color='C1', lw=.8)
            if drop: ax[0].axvline(drop['exact_s'], color='r')
            if drop:
                z = (drop['exact_s'] - 4, drop['exact_s'] + 4); m = (tt > z[0]) & (tt < z[1])
                ax[1].plot(tt[m][::4], x[m][::4], lw=.3, color='#555')
                for b in beats[(beats > z[0]) & (beats < z[1])]: ax[1].axvline(b, color='#9ab', lw=.8)
                for b in downbeats[(downbeats > z[0]) & (downbeats < z[1])]: ax[1].axvline(b, color='#136', lw=1.6)
                ax[1].axvline(drop['exact_s'], color='r', ls='--'); ax[1].set_xlim(*z)
                ax[1].set_title('±4 s around the drop: kicks should sit on the dark/light lines')
            fig.tight_layout(); fig.savefig(ROOT / 'audio' / 'analysis.png', dpi=100)
        except Exception as e:  # plotting is optional
            print('  (plot skipped:', e, ')')
    else:
        print('music: none configured / file missing (project.json -> music.file)')

    for kind, f in (pj.get('sfx') or {}).items():
        p = ROOT / f
        if not p.exists():
            print(f'sfx {kind}: missing file {f}')
            continue
        st = sfx_stats(load(p, stereo=True))
        out['sfx'][kind] = {'file': f, **st}
        note = ''
        if kind == 'riser' and st['level_build_db'] < 3:
            note = '  WARNING: this riser does not build (level flat) - pick another'
        if kind == 'type' and len(st['hits_s']) < 5:
            note = '  WARNING: few distinct keystrokes - typing will sound repetitive'
        print(f"sfx {kind:7s} peak {st['sample_peak_s']:.3f}s  {st['peak_dbfs']} dBFS  onset {st['onset_s']:.3f}  tail {st['tail_end_s']:.3f}/{st['duration_s']}s  hits {len(st['hits_s'])}{note}")
    (ROOT / 'audio').mkdir(exist_ok=True)
    (ROOT / 'audio' / 'analysis.json').write_text(json.dumps(out, indent=1), encoding='utf8')
    print('-> audio/analysis.json')


if __name__ == '__main__':
    main()
