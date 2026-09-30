"""Tile PNG stills into labelled contact sheets.  python studio/sheet.py <dir> <out_prefix> [cols] [per_sheet] [thumb_w]"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

src, prefix = Path(sys.argv[1]), sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 3
per = int(sys.argv[4]) if len(sys.argv) > 4 else 9
tw = int(sys.argv[5]) if len(sys.argv) > 5 else 640
files = sorted(src.glob('*.png'))
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 22)
for s in range(0, len(files), per):
    chunk = files[s:s + per]
    im0 = Image.open(chunk[0]); th = round(tw * im0.height / im0.width)  # keep the film's aspect (4:5, 9:16, 16:9)
    rows = (len(chunk) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * (tw + 6) + 6, rows * (th + 6) + 6), (90, 90, 90))
    for i, f in enumerate(chunk):
        im = Image.open(f).convert('RGB').resize((tw, th), Image.LANCZOS)
        d = ImageDraw.Draw(im)
        label = f.stem.lstrip('t').lstrip('0') or '0'
        d.rectangle([0, 0, 12 + 14 * len(label), 30], fill=(0, 0, 0))
        d.text((6, 3), label, fill=(255, 220, 0), font=font)
        sheet.paste(im, (6 + (i % cols) * (tw + 6), 6 + (i // cols) * (th + 6)))
    out = f'{prefix}_{s // per + 1}.png'
    sheet.save(out)
    print(out)
