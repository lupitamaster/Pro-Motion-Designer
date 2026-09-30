"""Check that sounds sit where the eye notices things, region by region.

  python studio/sync_probe.py out/<name>.mp4 out/<name>_mix.wav  "label:t0-t1:y0-y1[:x0-x1]" ...

For each probe it measures, inside that region and time window:
  onset   — the first frame where the region visibly changes (a reveal's first letters/edges)
  arrival — when the region settles (within 5% of its final look)
and prints the nearest placed sound's offset from each. Then it lists sounds closer than 150 ms
to each other (clusters that read as a pile-up).

What "in sync" means (learned from a client review):
  reveals (word sweeps, text rising from a mask, pills growing) → sound at the ONSET, ±40 ms;
  landings (a hop or drop hitting its spot) → sound at the impact (≈ arrival of the moving object).
Putting a reveal's sound at its arrival makes every sound late and piles them up at the end.
A whole-frame version of this check was tried and rejected: with several things moving at once
it flags correct sounds as often as wrong ones — probe regions instead.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

video, mix, probes = sys.argv[1], sys.argv[2], sys.argv[3:]
info = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v', '-show_entries', 'stream=width,height,r_frame_rate', '-of', 'json', video],
                                 capture_output=True, text=True, check=True).stdout)['streams'][0]
W, H = info['width'], info['height']
num, den = map(int, info['r_frame_rate'].split('/'))
fps = num / den
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', video, '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], capture_output=True, check=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W)
placed = sorted((p for p in json.loads(Path(str(mix) + '.placed.json').read_text(encoding='utf8')) if p['kind'] != 'type'), key=lambda p: p['peak_at'])
near = lambda t: min(placed, key=lambda p: abs(p['peak_at'] - t)) if placed else None
for pr in probes:
    parts = pr.split(':')
    label, (t0, t1), (y0, y1) = parts[0], map(float, parts[1].split('-')), map(int, parts[2].split('-'))
    x0, x1 = map(int, parts[3].split('-')) if len(parts) > 3 else (0, W)
    a, b = int(t0 * fps), int(t1 * fps)
    seg = fr[a:b + 1, y0:y1, x0:x1].astype(np.int16)
    from_start = np.array([(np.abs(f - seg[0]) > 24).mean() for f in seg])
    onset = (a + int(np.argmax(from_start > 0.002))) / fps
    dist = np.array([np.abs(f - seg[-1]).mean() for f in seg])
    arrival = (a + int(np.argmax(dist <= 0.05 * max(dist.max(), 1e-6)))) / fps
    n = near(onset)
    print(f"{label:14s} onset {onset:7.3f}s  arrival {arrival:7.3f}s | nearest {n['kind']:6s} {n['peak_at']:7.3f}s ({n['target']})"
          f"  vs onset {1000 * (n['peak_at'] - onset):+5.0f} ms  vs arrival {1000 * (n['peak_at'] - arrival):+5.0f} ms")
close = [(p, q) for p, q in zip(placed, placed[1:]) if q['peak_at'] - p['peak_at'] < 0.15]
print(f"\nsounds closer than 150 ms: {len(close)}" + ''.join(f"\n  {p['peak_at']:.3f} {p['kind']} ({p['target']})  +{1000 * (q['peak_at'] - p['peak_at']):.0f} ms  {q['kind']} ({q['target']})" for p, q in close))
