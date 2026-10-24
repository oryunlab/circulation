// The home page's hero: the Circulatory Sensing mark, alive. One five-petal knot drawn as a single line
// (a hairline where it crosses the centre, full at each tip), held in a tilted orbit whose colour flows
// Fire → purple → Water and back. The orbit passes behind the knot and in front of it; where it passes in
// front, the knot is cut away (never painted over), so it works on night and on paper.
// The mark breathes six times a minute, the colour circulates along the orbit, and the pointer tilts it.
export function startOrbit(cv) {
  const NIGHT = { ground: '#101418', knot: [233, 236, 234], fire: [255, 45, 85], ja: [173, 85, 255], water: [41, 121, 255], glow: 18 };
  const PAPER = { ground: '#f3efe7', knot: [28, 34, 39], fire: [219, 43, 78], ja: [109, 45, 181], water: [39, 107, 220], glow: 0 };
  const ctx = cv.getContext('2d');
  const still = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const N = 900, M = 360;   // points along the knot and along the orbit
  let W, H, C, S;
  const P = { tx: 0, ty: 0, x: 0, y: 0 };

  // the knot in unit space: z(t) = e^{it} + 0.78 e^{-4it}, Wood petal up
  const unit = [];
  let rmax = 0;
  for (let i = 0; i < N; i++) {
    const t = 2 * Math.PI * i / N;
    const x = Math.cos(t) + .78 * Math.cos(-4 * t), y = Math.sin(t) + .78 * Math.sin(-4 * t);
    unit.push([y, -x]);
    rmax = Math.max(rmax, Math.hypot(x, y));
  }

  const knotLayer = document.createElement('canvas');
  const kctx = knotLayer.getContext('2d');

  function size() {
    const dpr = Math.min(devicePixelRatio || 1, 2);
    W = cv.clientWidth; H = cv.clientHeight;
    for (const c of [cv, knotLayer]) { c.width = W * dpr; c.height = H * dpr; }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0); kctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    S = W > H ? Math.min(H * .19, W * .16) : W * .23;   // knot radius in px; the orbit reaches about 1.6 times this
    C = W > H ? [W * .5, H * .42] : [W * .5, H * .34];
  }

  // left and right edges of a line whose width changes point by point
  function edges(pts, widths) {
    const n = pts.length, L = [], R = [];
    for (let j = 0; j < n; j++) {
      const [x0, y0] = pts[(j - 1 + n) % n], [x1, y1] = pts[(j + 1) % n], [x, y] = pts[j];
      const dx = x1 - x0, dy = y1 - y0, d = Math.hypot(dx, dy) || 1, nx = -dy / d, ny = dx / d, w = widths[j] / 2;
      L.push([x + nx * w, y + ny * w]); R.push([x - nx * w, y - ny * w]);
    }
    return [L, R];
  }
  function band(c, L, R, idx) {
    c.beginPath();
    idx.forEach((j, k) => k ? c.lineTo(L[j][0], L[j][1]) : c.moveTo(L[j][0], L[j][1]));
    for (let k = idx.length - 1; k >= 0; k--) c.lineTo(R[idx[k]][0], R[idx[k]][1]);
    c.closePath(); c.fill();
  }
  const mix = (a, b, u) => a.map((v, i) => Math.round(v + (b[i] - v) * u));
  const rgb = (c, a = 1) => `rgba(${c[0]},${c[1]},${c[2]},${a})`;

  let last = 0, flow = 0;
  function frame(ms) {
    const time = ms / 1000, dt = Math.min(.05, time - (last || time)); last = time;
    flow += dt * .06;
    P.x += (P.tx - P.x) * .05; P.y += (P.ty - P.y) * .05;
    const T = document.documentElement.dataset.theme === 'light' ? PAPER : NIGHT;
    const breath = still ? .5 : .5 - .5 * Math.cos(time * Math.PI * 2 / 10);   // 6 breaths a minute
    const k = S * (1 + .03 * breath) / rmax;

    ctx.globalCompositeOperation = 'source-over';
    ctx.fillStyle = T.ground; ctx.fillRect(0, 0, W, H);

    // knot, on its own layer so the orbit can cut it
    const pts = unit.map(([x, y]) => [C[0] + x * k, C[1] + y * k]);
    const lo = S * .018, hi = S * .175;
    const ws = pts.map(([x, y]) => lo + (hi - lo) * Math.pow(Math.hypot(x - C[0], y - C[1]) / (S * 1.03), 2.2));
    const [KL, KR] = edges(pts, ws);
    kctx.globalCompositeOperation = 'source-over';
    kctx.clearRect(0, 0, W, H);
    kctx.fillStyle = rgb(T.knot);
    const seg = 120;
    for (let s = 0; s < seg; s++) {
      const a0 = Math.floor(s * N / seg), a1 = Math.floor((s + 1) * N / seg), idx = [];
      for (let j = a0 - 2; j <= a1 + 2; j++) idx.push((j + N) % N);
      band(kctx, KL, KR, idx);
    }

    // orbit: tilt follows the pointer a little
    const rx = S * 1.55, ry = S * (.48 + .06 * P.y), ph = (-20 + 6 * P.x) * Math.PI / 180;
    const opts = [], ows = [], ocol = [];
    for (let i = 0; i < M; i++) {
      const a = 2 * Math.PI * i / M, x = rx * Math.cos(a), y = ry * Math.sin(a);
      opts.push([C[0] + x * Math.cos(ph) - y * Math.sin(ph), C[1] + x * Math.sin(ph) + y * Math.cos(ph)]);
      const front = (1 + Math.sin(a)) / 2;                          // 1 at the front, 0 at the back
      ows.push(S * (.012 + .05 * front));
      // colour circulates: Fire → purple → Water → purple → Fire, moving along the orbit
      const u = ((i / M + flow) % 1) * 4, q = Math.floor(u), f = u - q;
      const stops = [T.fire, T.ja, T.water, T.ja];
      const c = mix(stops[q % 4], stops[(q + 1) % 4], f);
      ocol.push(mix(c, T === NIGHT ? [16, 20, 24] : [243, 239, 231], .55 * (1 - front)));
    }
    const [OL, OR] = edges(opts, ows);
    const [HL, HR] = edges(opts, ows.map(w => w + S * .05));
    const drawOrbit = (c, frontHalf) => {
      for (let i = 0; i < M; i += 2) {
        const a = 2 * Math.PI * (i + 1) / M;
        if ((Math.sin(a) >= 0) !== frontHalf) continue;
        const idx = [i - 1, i, i + 1, i + 2, i + 3].map(j => (j + M) % M);
        c.fillStyle = rgb(ocol[i]); band(c, OL, OR, idx);
      }
    };

    // cut the knot where the front of the orbit passes over it
    kctx.globalCompositeOperation = 'destination-out';
    kctx.fillStyle = '#000';
    for (let i = 0; i < M; i += 2) {
      const a = 2 * Math.PI * (i + 1) / M;
      if (Math.sin(a) < 0) continue;
      band(kctx, HL, HR, [i - 1, i, i + 1, i + 2, i + 3].map(j => (j + M) % M));
    }

    const paint = () => {
      drawOrbit(ctx, false);
      ctx.drawImage(knotLayer, 0, 0, W, H);
      drawOrbit(ctx, true);
    };
    if (T.glow) { ctx.save(); ctx.filter = `blur(${T.glow * S / 260}px)`; ctx.globalAlpha = .7; paint(); ctx.restore(); }
    paint();
    if (!still) requestAnimationFrame(frame);
  }

  addEventListener('pointermove', e => { P.tx = e.clientX / innerWidth * 2 - 1; P.ty = e.clientY / innerHeight * 2 - 1; }, { passive: true });
  addEventListener('resize', () => { size(); if (still) frame(0); });
  size();
  requestAnimationFrame(frame);
  // redraw at once when the theme changes, even with reduced motion
  new MutationObserver(() => { if (still) frame(0); }).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
}

const cv = document.getElementById('field');
if (cv) startOrbit(cv);
