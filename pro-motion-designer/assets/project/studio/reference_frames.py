"""Break a reference video into frames + labelled contact sheets, and sample its palette.

  python studio/reference_frames.py <video> out/ref [--fps 2] [--cols 4] [--per 16]

Writes out/ref/frames/fNNN.png (with the time in the name), out/ref/sheet_N.png (16 frames per
sheet, time stamped) and out/ref/palette.txt (the most common colours per sheet, as hex), then
prints the video's duration, size and fps. Read every sheet before writing the breakdown.
"""
import argparse
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def font(size):
    for f in ('C:/Windows/Fonts/arial.ttf', '/System/Library/Fonts/Supplemental/Arial.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            continue
    return ImageFont.load_default()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video'); ap.add_argument('out')
    ap.add_argument('--fps', type=float, default=2); ap.add_argument('--cols', type=int, default=4); ap.add_argument('--per', type=int, default=16)
    a = ap.parse_args()
    out = Path(a.out); frames = out / 'frames'; frames.mkdir(parents=True, exist_ok=True)
    info = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=width,height,r_frame_rate,codec_type', '-of', 'json', a.video],
                                     capture_output=True, text=True, check=True).stdout)
    print(json.dumps(info, indent=1))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', a.video, '-vf', f'fps={a.fps}', str(frames / 'f%03d.png')], check=True)
    files = sorted(frames.glob('f*.png'))
    f = font(22)
    for s in range(0, len(files), a.per):
        chunk = files[s:s + a.per]
        tw = 480; im0 = Image.open(chunk[0]); th = int(tw * im0.height / im0.width)
        rows = (len(chunk) + a.cols - 1) // a.cols
        sheet = Image.new('RGB', (a.cols * (tw + 4) + 4, rows * (th + 4) + 4), (60, 60, 60))
        pal = {}
        for i, p in enumerate(chunk):
            k = s + i
            t = k / a.fps
            im = Image.open(p).convert('RGB')
            q = im.resize((64, 36)).quantize(8).convert('RGB')
            for cnt, col in q.getcolors(64 * 36) or []:
                pal[col] = pal.get(col, 0) + cnt
            im = im.resize((tw, th))
            d = ImageDraw.Draw(im); lab = f'{t:05.1f}s'
            d.rectangle([0, 0, 14 * len(lab) + 10, 30], fill=(0, 0, 0)); d.text((6, 3), lab, fill=(255, 220, 0), font=f)
            sheet.paste(im, (4 + (i % a.cols) * (tw + 4), 4 + (i // a.cols) * (th + 4)))
        n = s // a.per + 1
        sheet.save(out / f'sheet_{n}.png')
        top = sorted(pal.items(), key=lambda x: -x[1])[:8]
        with open(out / 'palette.txt', 'a', encoding='utf8') as fh:
            fh.write(f'sheet_{n}: ' + ' '.join('#%02x%02x%02x' % c for c, _ in top) + '\n')
        print(out / f'sheet_{n}.png')


if __name__ == '__main__':
    main()
