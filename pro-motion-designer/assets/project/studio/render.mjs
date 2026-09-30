// Deterministic frame renderer: loads a composition, calls window.seek(t) per (sub)frame,
// screenshots it and pipes PNGs into ffmpeg.
// Run from the project root (the folder with project.json):
//   node studio/render.mjs <comp.html> [out.mp4] [--subframes 4] [--shutter 0.5] [--workers 4]
//   node studio/render.mjs <comp.html> --stills 0,5.5,12.25 [--outdir dir]   (PNG stills)
//   node studio/render.mjs <comp.html> [out.mp4] --timeline-only            (sound edits: re-export events only)
// Also writes <out>.timeline.json (window.TIMELINE) for mix_audio.py and check_film.py.
// Motion blur: N subframes spread over `shutter` of a frame interval, centred on the frame
// time, averaged with ffmpeg tmix. Workers render contiguous frame ranges in parallel.
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import path from 'node:path';

const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf('--' + k); return i >= 0 ? args[i + 1] : d; };
const positional = args.filter((a, i) => !a.startsWith('--') && !(i > 0 && args[i - 1].startsWith('--')));
const comp = path.resolve(positional[0] ?? 'comps/main/index.html');
const out = path.resolve(positional[1] ?? `out/${path.basename(path.dirname(comp))}.mp4`);
const SUB = +opt('subframes', 1), SHUTTER = +opt('shutter', 0.5), WORKERS = +opt('workers', 1);
const stills = opt('stills', null);
mkdirSync(path.dirname(out), { recursive: true });

// Serve the project root over http (ES module imports don't work from file://; /project.json is read by the kit).
// Note: this server has no range requests, so load video footage as a blob URL inside the composition.
const root = path.resolve('.');
const types = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.mp4': 'video/mp4', '.woff': 'font/woff', '.otf': 'font/otf', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.ttf': 'font/ttf', '.json': 'application/json' };
const server = createServer(async (req, res) => {
  try {
    const f = path.join(root, decodeURIComponent(new URL(req.url, 'http://x').pathname));
    if (!f.startsWith(root)) throw new Error('outside root');
    res.writeHead(200, { 'content-type': types[path.extname(f)] ?? 'application/octet-stream' });
    res.end(await readFile(f));
  } catch { res.writeHead(404).end(); }
}).listen(0, '127.0.0.1');
await new Promise((r) => server.once('listening', r));
const url = `http://127.0.0.1:${server.address().port}/${path.relative(root, comp).split(path.sep).join('/')}`;

const browser = await chromium.launch();
async function openPage() {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  await page.goto(url);
  await page.waitForFunction(() => window.COMP && (window.ready ? true : window.seek));
  await page.evaluate(async () => { if (window.ready) await window.ready; await document.fonts.ready; });
  if (errors.length) throw new Error('page errors:\n' + errors.join('\n'));
  const meta = await page.evaluate(() => window.COMP);
  await page.setViewportSize({ width: meta.width, height: meta.height });
  return { page, meta, errors };
}

if (args.includes('--timeline-only')) { // sound-only iterations: re-export window.TIMELINE without re-rendering frames
  const { page, meta } = await openPage();
  const timeline = await page.evaluate(() => window.TIMELINE || []);
  writeFileSync(out.replace(/\.mp4$/, '.timeline.json'), JSON.stringify({ meta, events: timeline }, null, 1));
  console.log(`timeline (${timeline.length} events) -> ${out.replace(/\.mp4$/, '.timeline.json')}`);
} else if (stills) {
  const { page } = await openPage();
  const dir = path.resolve(opt('outdir', 'out/stills')); mkdirSync(dir, { recursive: true });
  for (const t of stills.split(',').map(Number)) {
    await page.evaluate((t) => window.seek(t), t);
    await page.screenshot({ path: path.join(dir, `t${t.toFixed(3).padStart(7, '0')}.png`) });
  }
  console.log(`stills → ${dir}`);
} else {
  const { page: first, meta } = await openPage();
  const { fps, duration } = meta;
  const frames = Math.round(duration * fps);
  // timeline for the audio mix and the self-check
  const timeline = await first.evaluate(() => window.TIMELINE || []);
  writeFileSync(out.replace(/\.mp4$/, '.timeline.json'), JSON.stringify({ meta, events: timeline }, null, 1));
  await first.close();
  const per = Math.ceil(frames / WORKERS);
  const segs = [];
  const t0 = Date.now(); let done = 0;
  await Promise.all(Array.from({ length: WORKERS }, async (_, w) => {
    const a = w * per, b = Math.min(frames, a + per); if (a >= b) return;
    const { page } = await openPage();
    const seg = out.replace(/\.mp4$/, `.seg${w}.mp4`); segs[w] = seg;
    const vf = SUB > 1 ? ['-vf', `tmix=frames=${SUB},select='eq(mod(n\\,${SUB})\\,${SUB - 1})',setpts=N/(${fps}*TB)`] : [];
    const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(fps * SUB), '-i', '-', ...vf,
      '-r', String(fps), '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-pix_fmt', 'yuv420p', seg], { stdio: ['pipe', 'inherit', 'inherit'] });
    for (let i = a; i < b; i++) {
      for (let k = 0; k < SUB; k++) {
        const off = SUB > 1 ? (k - (SUB - 1) / 2) / SUB * SHUTTER : 0;
        const t = Math.min(duration - 1e-4, Math.max(0, (i + off) / fps));
        await page.evaluate((t) => window.seek(t), t);
        const png = await page.screenshot({ type: 'png' });
        if (!ff.stdin.write(png)) await new Promise((r) => ff.stdin.once('drain', r));
      }
      done++;
      if (done % 60 === 0) process.stdout.write(`frames ${done}/${frames}  ${((Date.now() - t0) / 1000).toFixed(0)}s\r`);
    }
    ff.stdin.end();
    await new Promise((r, j) => ff.on('close', (c) => (c === 0 ? r() : j(new Error(`ffmpeg exited ${c}`)))));
    await page.close();
  }));
  const list = out.replace(/\.mp4$/, '.segs.txt');
  writeFileSync(list, segs.filter(Boolean).map((s) => `file '${s.replace(/\\/g, '/')}'`).join('\n'));
  await new Promise((r, j) => spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', '-movflags', '+faststart', out], { stdio: 'inherit' })
    .on('close', (c) => (c === 0 ? r() : j(new Error('concat failed')))));
  for (const s of segs.filter(Boolean)) rmSync(s); rmSync(list);
  console.log(`\n${frames} frames @ ${fps}fps${SUB > 1 ? ` (${SUB} subframes, shutter ${SHUTTER})` : ''} → ${out}  in ${((Date.now() - t0) / 1000).toFixed(0)}s`);
}
await browser.close();
server.close();
