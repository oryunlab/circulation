// The home page's hero: the Circulatory Sensing mark, alive and answering. A five-petal knot drawn as one line
// (a hairline at the centre, full at each tip) is held by an orbit that turns in three dimensions, passing
// behind the knot and in front of it; where it passes in front, the knot is cut away, never painted over.
//   · Light circulates: streaks of Fire, purple and Water run along the knot, through the shared centre.
//   · Move near the knot and it answers where you are: the nearest petal warms and sends light on.
//   · Drag to turn the orbit like a gyroscope; it keeps turning, then settles back to its slow precession.
//   · Tap to send five streaks at once, one from each petal, and a ripple out through the orbit.
//   · Hold, and the circulation quickens and the glow deepens; release, and a ripple carries it outward.
//   · Every touch on a phone counts, so several people can play it together.
// Lines and light only. Six breaths a minute. Reduced motion shows the mark still.
export function startOrbit(cv, area) {
  const NIGHT = { ground: [16, 20, 24], knot: [233, 236, 234], fire: [255, 45, 85], ja: [173, 85, 255], water: [41, 121, 255], add: true };
  const PAPER = { ground: [243, 239, 231], knot: [28, 34, 39], fire: [219, 43, 78], ja: [109, 45, 181], water: [39, 107, 220], add: false };
  const ctx = cv.getContext('2d');
  const still = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const N = 1000, M = 360;
  let W, H, C, S;

  // the knot in unit space: z(t) = e^{it} + 0.78 e^{-4it}, Wood petal up
  const unit = [];
  let rmax = 0;
  for (let i = 0; i < N; i++) {
    const t = 2 * Math.PI * i / N;
    const x = Math.cos(t) + .78 * Math.cos(-4 * t), y = Math.sin(t) + .78 * Math.sin(-4 * t);
    unit.push([y, -x]); rmax = Math.max(rmax, Math.hypot(x, y));
  }
  const tips = [0, 1, 2, 3, 4].map(e => Math.round(e * N / 5));   // petal tips along the line

  const knotLayer = document.createElement('canvas'), kctx = knotLayer.getContext('2d');
  const glowLayer = document.createElement('canvas'), gctx = glowLayer.getContext('2d');

  function size() {
    const dpr = Math.min(devicePixelRatio || 1, 2);
    W = cv.clientWidth; H = cv.clientHeight;
    for (const c of [cv, knotLayer]) { c.width = W * dpr; c.height = H * dpr; }
    glowLayer.width = Math.ceil(W / 4); glowLayer.height = Math.ceil(H / 4);   // glow is drawn small and scaled up
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0); kctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    gctx.setTransform(.25, 0, 0, .25, 0, 0);
    S = W > H ? Math.min(H * .19, W * .16) : W * .23;
    C = W > H ? [W * .5, H * .42] : [W * .5, H * .34];
  }

  // ---- state ----
  const pulses = [];   // light running along the knot: { p, v, life, hue }
  const ripples = [];  // rings leaving through the orbit plane: { r, a }
  const touches = new Map();   // pointerId -> { x, y, down, t0 }
  const O = { yaw: 0, pitch: 0, vyaw: 0, vpitch: 0 };   // orbit rotation added by hand, and its momentum
  let hold = 0, near = -1, nearAmt = 0, lastSpawn = 0, drag = null;

  const mix = (a, b, u) => a.map((v, i) => v + (b[i] - v) * u);
  const rgb = (c, a = 1) => `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${a})`;
  const flowColour = (T, u) => {   // u in [0,1): Fire → purple → Water → purple → Fire
    const s = [T.fire, T.ja, T.water, T.ja], q = (((u % 1) + 1) % 1) * 4, i = Math.floor(q);
    return mix(s[i % 4], s[(i + 1) % 4], q - i);
  };

  function edges(pts, widths) {
    const n = pts.length, L = [], R = [];
    for (let j = 0; j < n; j++) {
      const a = pts[(j - 1 + n) % n], b = pts[(j + 1) % n];
      const dx = b[0] - a[0], dy = b[1] - a[1], d = Math.hypot(dx, dy) || 1, nx = -dy / d, ny = dx / d, w = widths[j] / 2;
      L.push([pts[j][0] + nx * w, pts[j][1] + ny * w]); R.push([pts[j][0] - nx * w, pts[j][1] - ny * w]);
    }
    return [L, R];
  }
  function band(c, L, R, idx) {
    c.beginPath();
    idx.forEach((j, k) => k ? c.lineTo(L[j][0], L[j][1]) : c.moveTo(L[j][0], L[j][1]));
    for (let k = idx.length - 1; k >= 0; k--) c.lineTo(R[idx[k]][0], R[idx[k]][1]);
    c.closePath(); c.fill();
  }
  const run = (a, b, n) => { const idx = []; for (let j = Math.floor(a); j <= Math.ceil(b); j++) idx.push(((j % n) + n) % n); return idx; };

  function spawn(p, hue, v = 1) { if (pulses.length < 40) pulses.push({ p, v: (.13 + Math.random() * .05) * v, life: 1, hue }); }

  // the orbit as a circle in 3D: tilted back, slowly precessing, turned by hand
  function orbitPoints(t) {
    const R = S * 1.6, lean = -20 * Math.PI / 180, tilt = 1.27;   // tilt ≈ 73° away from facing
    const yaw = O.yaw + t * .12, pitch = tilt + O.pitch;
    const cy = Math.cos(yaw), sy = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch), cr = Math.cos(lean), sr = Math.sin(lean);
    const pts = [], z = [];
    for (let i = 0; i < M; i++) {
      const a = 2 * Math.PI * i / M;
      let x = R * Math.cos(a), y = R * Math.sin(a), zz = 0;
      [x, zz] = [x * cy - zz * sy, x * sy + zz * cy];   // precession about the vertical
      [y, zz] = [y * cp - zz * sp, y * sp + zz * cp];   // tilt back
      [x, y] = [x * cr - y * sr, x * sr + y * cr];      // the mark's -20° lean
      pts.push([C[0] + x, C[1] + y]); z.push(zz / R);
    }
    return { pts, z };
  }

  let last = 0, flow = 0, t = 0;
  function frame(ms) {
    const time = ms / 1000, dt = Math.min(.05, time - (last || time)); last = time;
    const T = document.documentElement.dataset.theme === 'light' ? PAPER : NIGHT;
    const anyDown = [...touches.values()].some(q => q.down);
    hold += ((anyDown ? 1 : 0) - hold) * (anyDown ? .03 : .05);
    t += dt * (1 + 2.5 * hold);
    flow += dt * (.05 + .25 * hold);
    O.yaw += O.vyaw * dt; O.pitch += O.vpitch * dt;
    O.vyaw *= Math.pow(.25, dt); O.vpitch *= Math.pow(.25, dt);
    if (!drag) O.pitch *= Math.pow(.4, dt);
    const breath = still ? .5 : .5 - .5 * Math.cos(time * Math.PI * 2 / 10);
    const k = S * (1 + (.03 + .04 * hold) * breath) / rmax;

    // ground, cleared every frame (an afterglow trail stacks into visible steps)
    ctx.globalCompositeOperation = 'source-over';
    ctx.fillStyle = rgb(T.ground); ctx.fillRect(0, 0, W, H);

    // knot
    const pts = unit.map(([x, y]) => [C[0] + x * k, C[1] + y * k]);
    const lo = S * .018, hi = S * .175;
    const ws = pts.map(([x, y]) => lo + (hi - lo) * Math.pow(Math.hypot(x - C[0], y - C[1]) / (S * 1.03), 2.2));
    const [KL, KR] = edges(pts, ws);

    // which petal is a visitor nearest?
    let best = -1, bd = 1e9;
    for (const q of touches.values()) for (let e = 0; e < 5; e++) {
      const [x, y] = pts[tips[e]], d = Math.hypot(q.x - x, q.y - y);
      if (d < bd) { bd = d; best = e; }
    }
    const reach = S * 1.1;
    nearAmt += ((bd < reach ? 1 - bd / reach : 0) - nearAmt) * .1;
    if (best >= 0 && bd < reach) near = best;
    if (!still && near >= 0 && nearAmt > .25 && time - lastSpawn > .45 - .3 * hold) { spawn(tips[near] - 60, near / 5); lastSpawn = time; }
    if (!still && pulses.length < 3 + 6 * hold && Math.random() < dt * (1.2 + 5 * hold)) spawn(Math.random() * N, Math.random());

    kctx.globalCompositeOperation = 'source-over';
    kctx.clearRect(0, 0, W, H);
    kctx.fillStyle = rgb(T.knot);
    for (let s = 0; s < 125; s++) band(kctx, KL, KR, run(s * N / 125 - 2, (s + 1) * N / 125 + 2, N));
    // the petal a visitor is near warms with the colour of the flow
    if (near >= 0 && nearAmt > .02) {
      // nested from the tip outward, so the warmth fades with no hard edge
      kctx.fillStyle = rgb(flowColour(T, near / 5 + flow), 1 - Math.pow(1 - .6 * nearAmt, 1 / 24));
      for (let s = 1; s <= 24; s++) band(kctx, KL, KR, run(tips[near] - 95 * s / 24, tips[near] + 95 * s / 24, N));
    }
    // light running along the line: a streak with a fading tail
    for (const P of pulses) {
      if (!still) { P.p = (P.p + P.v * N * dt * (1 + 1.5 * hold)) % N; P.life -= dt * .22; }
      // nested bands that all start at the head, each one whole, so the tail fades smoothly with no seams
      const c = flowColour(T, P.hue + flow), tail = 120, n = 32, life = Math.max(0, P.life);
      const a = 1 - Math.pow(1 - .9 * life, 1 / n);
      kctx.fillStyle = rgb(c, a);
      for (let s = 1; s <= n; s++) band(kctx, KL, KR, run(P.p - tail * s / n, P.p, N));
      if (T.add) {
        kctx.fillStyle = rgb(mix(c, [255, 255, 255], .5), 1 - Math.pow(1 - .5 * life, 1 / 8));
        for (let s = 1; s <= 8; s++) band(kctx, KL, KR, run(P.p - 24 * s / 8, P.p, N));
      }
    }
    for (let i = pulses.length - 1; i >= 0; i--) if (pulses[i].life <= 0) pulses.splice(i, 1);

    // orbit
    const { pts: op, z } = orbitPoints(t);
    const ows = z.map(v => S * (.012 + .05 * (1 + v) / 2) * (1 + .5 * hold));
    const [OL, OR] = edges(op, ows), [HL, HR] = edges(op, ows.map(w => w + S * .05));
    const quad = i => [i - 1, i, i + 1, i + 2, i + 3].map(j => (j + M) % M);
    // cut the knot wherever the orbit passes in front of it
    kctx.globalCompositeOperation = 'destination-out'; kctx.fillStyle = '#000';
    for (let i = 0; i < M; i += 2) if (z[(i + 1) % M] > 0) band(kctx, HL, HR, quad(i));

    const orbitHalf = (c, front) => {
      for (let i = 0; i < M; i += 2) {
        const zi = z[(i + 1) % M];
        if ((zi > 0) !== front) continue;
        c.fillStyle = rgb(mix(flowColour(T, i / M + flow), T.ground, .6 * (1 - (1 + zi) / 2)));
        band(c, OL, OR, quad(i));
      }
    };
    // ripples leave through the plane of the orbit
    const rippleRings = c => {
      for (const r of ripples) {
        const s = r.r / (S * 1.6), alpha = Math.max(0, r.a);
        c.strokeStyle = rgb(flowColour(T, flow + r.r / (S * 6)), alpha); c.lineWidth = S * .012 * (1 + 2 * alpha);
        c.beginPath();
        op.forEach(([x, y], i) => { const X = C[0] + (x - C[0]) * s, Y = C[1] + (y - C[1]) * s; i ? c.lineTo(X, Y) : c.moveTo(X, Y); });
        c.closePath(); c.stroke();
      }
    };
    for (const r of ripples) { r.r += dt * S * (1.4 + r.r / S); r.a -= dt * .55; }
    for (let i = ripples.length - 1; i >= 0; i--) if (ripples[i].a <= 0) ripples.splice(i, 1);

    const paint = c => { orbitHalf(c, false); c.drawImage(knotLayer, 0, 0, W, H); orbitHalf(c, true); rippleRings(c); };
    if (T.add) {   // soft glow: the scene drawn small, blurred, and added on
      gctx.clearRect(0, 0, W * 4, H * 4);
      gctx.filter = `blur(${2 + 2 * hold}px)`; paint(gctx); gctx.filter = 'none';
      ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = Math.min(1, .55 + .35 * hold + .2 * nearAmt);
      ctx.drawImage(glowLayer, 0, 0, W, H); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
    }
    paint(ctx);
    if (!still) requestAnimationFrame(frame);
  }

  // ---- input: every pointer is a person ----
  const local = e => { const b = cv.getBoundingClientRect(); return [e.clientX - b.left, e.clientY - b.top]; };
  area.addEventListener('pointermove', e => {
    const [x, y] = local(e), q = touches.get(e.pointerId) || { down: false };
    if (drag && drag.id === e.pointerId) {
      const dx = x - drag.x, dy = y - drag.y, dts = Math.max(.016, (e.timeStamp - drag.t) / 1000);
      O.yaw += dx / S * .9; O.pitch = Math.max(-.6, Math.min(.6, O.pitch + dy / S * .6));
      O.vyaw = dx / S * .9 / dts; O.vpitch = dy / S * .6 / dts;
      drag.x = x; drag.y = y; drag.t = e.timeStamp; drag.moved += Math.abs(dx) + Math.abs(dy);
    }
    touches.set(e.pointerId, { ...q, x, y });
  }, { passive: true });
  area.addEventListener('pointerdown', e => {
    if (e.target.closest('a, button')) return;
    const [x, y] = local(e);
    touches.set(e.pointerId, { x, y, down: true, t0: e.timeStamp });
    if (!drag) drag = { id: e.pointerId, x, y, t: e.timeStamp, moved: 0 };
  });
  const up = e => {
    const q = touches.get(e.pointerId);
    if (q && q.down) {
      const held = (e.timeStamp - q.t0) / 1000, moved = drag && drag.id === e.pointerId ? drag.moved : 0;
      if (moved < 12) {   // a tap or a hold, not a drag: light from every petal, and a ripple
        for (let p = 0; p < 5; p++) spawn(tips[p], p / 5, 1 + Math.min(1, held));
        ripples.push({ r: S * .4, a: Math.min(1, .6 + held * .5) });
      }
    }
    if (drag && drag.id === e.pointerId) drag = null;
    if (e.pointerType === 'mouse') touches.set(e.pointerId, { ...(q || {}), down: false }); else touches.delete(e.pointerId);
  };
  area.addEventListener('pointerup', up);
  area.addEventListener('pointercancel', up);
  area.addEventListener('pointerleave', e => { if (e.pointerType === 'mouse') touches.delete(e.pointerId); });

  addEventListener('resize', () => { size(); if (still) frame(0); });
  size();
  requestAnimationFrame(frame);
  new MutationObserver(() => { if (still) frame(0); }).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
}

const cv = document.getElementById('field');
if (cv) startOrbit(cv, cv.parentElement);
