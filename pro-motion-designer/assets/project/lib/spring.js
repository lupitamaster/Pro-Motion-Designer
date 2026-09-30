// Analytic damped spring (closed form, so any frame can be sampled in any order).
// Returns progress 0→1 at time t (seconds) for a unit step from rest.
export function spring(t, { stiffness = 170, damping = 26, mass = 1, velocity = 0 } = {}) {
  if (t <= 0) return 0;
  const w0 = Math.sqrt(stiffness / mass);
  const zeta = damping / (2 * Math.sqrt(stiffness * mass));
  const x0 = -1; // displacement from target
  const v0 = velocity;
  let x;
  if (zeta < 1) {
    const wd = w0 * Math.sqrt(1 - zeta * zeta);
    x = Math.exp(-zeta * w0 * t) * (x0 * Math.cos(wd * t) + ((v0 + zeta * w0 * x0) / wd) * Math.sin(wd * t));
  } else if (zeta === 1) {
    x = Math.exp(-w0 * t) * (x0 + (v0 + w0 * x0) * t);
  } else {
    const r1 = -w0 * (zeta - Math.sqrt(zeta * zeta - 1));
    const r2 = -w0 * (zeta + Math.sqrt(zeta * zeta - 1));
    const b = (v0 - r1 * x0) / (r2 - r1);
    x = (x0 - b) * Math.exp(r1 * t) + b * Math.exp(r2 * t);
  }
  return 1 + x;
}

export const lerp = (a, b, p) => a + (b - a) * p;

// House presets (things bounce a tiny bit when they land). Both settle within 2% in under one
// beat at 120 BPM (0.5 s), so a landing never bleeds into the next beat. check_film.py verifies this.
export const LAND = { stiffness: 400, damping: 28 };  // ζ 0.70 · overshoot 4.6% · settles 0.30 s — small objects landing
export const MORPH = { stiffness: 220, damping: 21 }; // ζ 0.71 · overshoot 4.3% · settles 0.40 s — shape → next shape

// Camera moves are not springs: they start and end exactly on beats and never bounce.
// cameraMove(t, startBeat, beats, beatLen) -> 0..1, eased in and out over a whole number of beats.
export const BEAT = 0.5; // seconds at 120 BPM (default)
export function cameraMove(t, startBeat, beats, beatLen = BEAT) {
  const p = Math.min(1, Math.max(0, (t - startBeat * beatLen) / (beats * beatLen)));
  return p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2; // easeInOutCubic
}
