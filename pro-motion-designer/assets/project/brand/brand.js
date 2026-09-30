// Brand tokens for the compositions. Fill these from brand/BRIEF.md (phase 3) — the real
// colours and fonts from the company's site/guidelines, never guesses. Keep one accent.
export const BRAND = {
  name: 'acme',              // wordmark as it is written (case matters)
  url: 'acme.example',       // PLACEHOLDER
  dot: 22,                   // caret / motif size at ~80px type
  light: {
    bg: '#FAFAF8', surface: '#F2F1EE', raised: '#FFFFFF', ink: '#1B1B1A', muted: '#6B6A67', border: '#DDDAD5',
    accent: '#3B5BDB',       // shapes, fills
    accentText: '#2F49B0',   // accent used as text on light backgrounds (contrast)
    onAccent: '#FFFFFF',
  },
  dark: {
    bg: '#0E0F12', surface: '#16181D', raised: '#1E2027', ink: '#E7E8EA', muted: '#8E9097', border: '#2B2E36',
    accent: '#5B7BFF', accentText: '#7D96FF', onAccent: '#0E0F12',
  },
  // CSS font stacks. Put licensed font files in /fonts and declare them in the composition's index.html.
  fonts: {
    display: "'Display', Georgia, 'Times New Roman', serif",
    ui: "'UI', 'Segoe UI', Arial, sans-serif",
    mono: "'Mono', Consolas, 'Courier New', monospace",
  },
};
