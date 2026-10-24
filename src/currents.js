// The home page's hero, grown from the mark rather than showing it. Seven five-petal currents
// (z(t) = e^{it} + k·e^{-4it}, each with its own k, size and turn) drift apart through a field of orbits
// that precess at different tilts, like an armillary sphere. Every so often, and whenever someone holds,
// the field gathers: every current and every orbit eases into the same knot and the same orbit, and the
// Circulatory Sensing mark appears for a moment, then opens out again. Five held in one line, becoming
// what lies between.
//   · Move: the lines part around your hand like water around a finger.
//   · Tap: the field gathers into the mark and a ripple leaves through the orbit.
//   · Hold: it stays gathered while you hold.
//   · Drag sideways: turns the whole sphere of orbits.
//   · Every touch on a phone counts; with two or more, an arc of light joins the people touching.
// Lines and light only. Colour flows Fire → purple → Water around the centre.
export function startCurrents(cv, area) {
  const NIGHT = { ground: [16, 20, 24], knot: [233, 236, 234], fire: [255, 45, 85], ja: [173, 85, 255], water: [41, 121, 255], add: true, line: .55 };
  const PAPER = { ground: [243, 239, 231], knot: [28, 34, 39], fire: [219, 43, 78], ja: [109, 45, 181], water: [39, 107, 220], add: false, line: .7 };
  const ctx = cv.getContext('2d');
  const still = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const N = 480, M = 220;
  let W, H, C, S;

  // the currents: each a five-petal curve with its own spread state; gathered, all become the mark (k .78, size 1)
  const CURRENTS = [   // nested like a rose window, each turning slowly its own way
    { k: .78, s: 1, w: .02 }, { k: .62, s: .62, w: -.05 }, { k: .9, s: 1.32, w: .035 },
    { k: .7, s: 1.64, w: -.025 }, { k: .84, s: 1.96, w: .018 }, { k: .55, s: .36, w: .07 },
  ];
  // the orbits: nested rings at neighbouring tilts, precessing at different speeds
  const ORBITS = [
    { r: 1.6, p: 1.27, v: .12 }, { r: 2.05, p: 1.22, v: .085 }, { r: 2.5, p: 1.32, v: .06 }, { r: 2.95, p: 1.18, v: .04 },
  ];

  const knotLayer = document.createElement('canvas'), kctx = knotLayer.getContext('2d');
  const glowLayer = document.createElement('canvas'), gctx = glowLayer.getContext('2d');

  function size() {
    const dpr = Math.min(devicePixelRatio || 1, 2);
    W = cv.clientWidth; H = cv.clientHeight;
    for (const c of [cv, knotLayer]) { c.width = W * dpr; c.height = H * dpr; }
    glowLayer.width = Math.ceil(W / 4); glowLayer.height = Math.ceil(H / 4);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0); kctx.setTransform(dpr, 0, 0, dpr, 0, 0); gctx.setTransform(.25, 0, 0, .25, 0, 0);
    S = W > H ? Math.min(H * .19, W * .16) : W * .23;
    C = W > H ? [W * .5, H * .42] : [W * .5, H * .34];
  }

  const touches = new Map();   // pointerId -> { x, y, down, t0 }
  const ripples = [];
  const O = { yaw: 0, vyaw: 0 };
  let g = 0, boost = 0, drag = null;

  const lerp = (a, b, u) => a + (b - a) * u;
  const mixc = (a, b, u) => a.map((v, i) => v + (b[i] - v) * u);
  const rgb = (c, a = 1) => `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${a})`;
  const smooth = u => (u = Math.max(0, Math.min(1, u)), u * u * (3 - 2 * u));

  // colour by angle around the centre: Fire → purple → Water → purple, turning with the flow
  function flowGradient(c, T, rot, alpha) {
    const gr = c.createConicGradient(rot, C[0], C[1]);
    [T.fire, T.ja, T.water, T.ja, T.fire].forEach((col, i) => gr.addColorStop(i / 4, rgb(col, alpha)));
    return gr;
  }

  // the lines part around each hand
  function warp(x, y, amt) {
    for (const q of touches.values()) {
      const dx = x - q.x, dy = y - q.y, d = Math.hypot(dx, dy) + .001, R = S * 1.1;
      if (d < R) { const f = Math.pow(1 - d / R, 2) * S * .32 * amt; x += dx / d * f; y += dy / d * f; }
    }
    return [x, y];
  }

  function currentPath(cur, t, gg, scale) {
    const k = lerp(cur.k, .78, gg), s = lerp(cur.s, 1, gg), rot = (1 - gg) * (cur.w * t * 6.283 + cur.k * 3);
    const R = S * s * scale / (1 + k), cr = Math.cos(rot), sr = Math.sin(rot), pts = [];
    for (let i = 0; i <= N; i++) {
      const a = 2 * Math.PI * i / N;
      let x = Math.cos(a) + k * Math.cos(-4 * a), y = Math.sin(a) + k * Math.sin(-4 * a);
      [x, y] = [y, -x];                                   // Wood petal up
      [x, y] = [x * cr - y * sr, x * sr + y * cr];
      pts.push(warp(C[0] + x * R, C[1] + y * R, 1 - .7 * gg));
    }
    return pts;
  }

  function orbitPath(o, t, gg, scale = 1) {
    const R = S * lerp(o.r, 1.6, gg) * scale, pitch = lerp(o.p, 1.27, gg), yaw = O.yaw + lerp(o.v * t, .12 * t, gg);
    const lean = -20 * Math.PI / 180;
    const cy = Math.cos(yaw), sy = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch), cl = Math.cos(lean), sl = Math.sin(lean);
    const pts = [], z = [];
    for (let i = 0; i <= M; i++) {
      const a = 2 * Math.PI * i / M;
      let x = R * Math.cos(a), y = R * Math.sin(a), zz = 0;
      [x, zz] = [x * cy, x * sy];
      [y, zz] = [y * cp - zz * sp, y * sp + zz * cp];
      [x, y] = [x * cl - y * sl, x * sl + y * cl];
      pts.push(warp(C[0] + x, C[1] + y, .6 * (1 - gg))); z.push(zz / R);
    }
    return { pts, z };
  }

  // stroke the part of an orbit on one side (behind or in front)
  function strokeHalf(c, o, front) {
    c.beginPath();
    let on = false;
    for (let i = 0; i <= M; i++) {
      const f = o.z[i] > 0;
      if (f === front) { on ? c.lineTo(o.pts[i][0], o.pts[i][1]) : c.moveTo(o.pts[i][0], o.pts[i][1]); on = true; } else on = false;
    }
    c.stroke();
  }

  // the knot as one filled line (the mark), for the gathered moment
  function edges(pts, widths) {
    const n = pts.length, L = [], R = [];
    for (let j = 0; j < n; j++) {
      const a = pts[(j - 1 + n) % n], b = pts[(j + 1) % n], dx = b[0] - a[0], dy = b[1] - a[1], d = Math.hypot(dx, dy) || 1, w = widths[j] / 2;
      L.push([pts[j][0] - dy / d * w, pts[j][1] + dx / d * w]); R.push([pts[j][0] + dy / d * w, pts[j][1] - dx / d * w]);
    }
    return [L, R];
  }
  function ribbon(c, L, R) {
    c.beginPath(); L.forEach(([x, y], i) => i ? c.lineTo(x, y) : c.moveTo(x, y)); c.closePath();
    c.moveTo(R[0][0], R[0][1]); for (let i = R.length - 1; i >= 0; i--) c.lineTo(R[i][0], R[i][1]); c.closePath();
    c.fill('evenodd');
  }

  let last = 0, t = 0, flow = 0;
  function frame(ms) {
    const time = ms / 1000, dt = Math.min(.05, time - (last || time)); last = time;
    const T = document.documentElement.dataset.theme === 'light' ? PAPER : NIGHT;
    const downs = [...touches.values()].filter(q => q.down);
    // the field gathers by itself once every 16 s, lingers, and opens again; a hold keeps it gathered
    const cycle = .5 - .5 * Math.cos(time * Math.PI * 2 / 16);
    const target = Math.max(still ? 1 : Math.pow(cycle, 8), downs.length ? 1 : 0, boost);
    g += (target - g) * (target > g ? .05 : .025);
    boost *= Math.pow(.35, dt);
    t += dt * (1 + 1.5 * downs.length);
    flow += dt * (.06 + .2 * g);
    O.yaw += O.vyaw * dt; O.vyaw *= Math.pow(.3, dt);
    const gg = smooth(g), breath = .5 - .5 * Math.cos(time * Math.PI * 2 / 10), scale = 1 + .03 * breath;

    const orbits = ORBITS.map(o => orbitPath(o, t, gg, scale));
    const currents = CURRENTS.map(cu => currentPath(cu, t, gg, scale));

    const scene = (c, glow) => {
      c.lineJoin = 'round'; c.lineCap = 'round';
      const lw = Math.max(.8, S * .007) * (glow ? 2.5 : 1);
      // orbits behind
      orbits.forEach((o, j) => {
        c.lineWidth = lw * (j ? 1 : 1 + 2 * gg);
        c.strokeStyle = flowGradient(c, T, flow * 6.283 + j, T.line * .35 * (j ? 1 - .6 * gg : 1)); strokeHalf(c, o, false);
      });
      // the currents
      currents.forEach((p, j) => {
        c.lineWidth = lw * (1 + 1.2 * gg);
        c.strokeStyle = flowGradient(c, T, flow * 6.283 + j * .9 + 1.5, T.line * (1 - .5 * smooth((gg - .6) / .4)));
        c.beginPath(); p.forEach(([x, y], i) => i ? c.lineTo(x, y) : c.moveTo(x, y)); c.stroke();
      });
      // the mark, as the field gathers into it
      const show = smooth((gg - .7) / .3);
      if (show > .01) { c.save(); c.globalAlpha *= show; c.drawImage(knotLayer, 0, 0, W, H); c.restore(); }
      // orbits in front
      orbits.forEach((o, j) => {
        c.lineWidth = lw * (j ? 1.4 : 1.4 + 3 * gg);
        c.strokeStyle = flowGradient(c, T, flow * 6.283 + j, T.line * (j ? 1 - .6 * gg : 1)); strokeHalf(c, o, true);
      });
      // ripples, and the arcs between people touching at once
      for (const r of ripples) {
        const s = r.r / (S * 1.6), o = orbits[0];
        c.lineWidth = lw * (1 + 2 * r.a); c.strokeStyle = flowGradient(c, T, flow * 6.283, r.a);
        c.beginPath(); o.pts.forEach(([x, y], i) => { const X = C[0] + (x - C[0]) * s, Y = C[1] + (y - C[1]) * s; i ? c.lineTo(X, Y) : c.moveTo(X, Y); }); c.stroke();
      }
      if (downs.length > 1) {
        c.lineWidth = lw * 2; c.strokeStyle = rgb(T.ja, .8);
        for (let i = 0; i < downs.length; i++) {
          const a = downs[i], b = downs[(i + 1) % downs.length];
          c.beginPath(); c.moveTo(a.x, a.y); c.quadraticCurveTo(C[0], C[1], b.x, b.y); c.stroke();
        }
      }
    };

    // the mark's knot, prepared on its own layer and cut where the front of the main orbit crosses it
    const show = smooth((gg - .7) / .3);
    if (show > .01) {
      const pts = currents[0].slice(0, N);
      const lo = S * .018, hi = S * .175;
      const ws = pts.map(([x, y]) => lo + (hi - lo) * Math.pow(Math.min(1, Math.hypot(x - C[0], y - C[1]) / (S * 1.03)), 2.2));
      const [L, R] = edges(pts, ws);
      kctx.globalCompositeOperation = 'source-over'; kctx.clearRect(0, 0, W, H);
      kctx.fillStyle = rgb(T.knot);   // opaque here; faded as a whole when drawn, so overlaps never show
      for (let s = 0; s < 120; s++) {   // filled in overlapping pieces so the crossings stay solid
        const a0 = Math.floor(s * N / 120), a1 = Math.floor((s + 1) * N / 120);
        kctx.beginPath();
        for (let j = a0 - 1; j <= a1 + 1; j++) { const q = L[(j + N) % N]; j === a0 - 1 ? kctx.moveTo(q[0], q[1]) : kctx.lineTo(q[0], q[1]); }
        for (let j = a1 + 1; j >= a0 - 1; j--) { const q = R[(j + N) % N]; kctx.lineTo(q[0], q[1]); }
        kctx.closePath(); kctx.fill();
      }
      const o = orbits[0];
      kctx.globalCompositeOperation = 'destination-out'; kctx.strokeStyle = '#000';
      kctx.lineWidth = Math.max(.8, S * .007) * (1.4 + 3 * gg) + S * .05; kctx.lineCap = 'butt';
      strokeHalf(kctx, o, true);
    }

    ctx.globalCompositeOperation = 'source-over';
    ctx.fillStyle = rgb(T.ground); ctx.fillRect(0, 0, W, H);
    if (T.add) {
      gctx.clearRect(0, 0, W * 4, H * 4); gctx.filter = 'blur(3px)'; scene(gctx, true); gctx.filter = 'none';
      ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = .5 + .4 * gg; ctx.drawImage(glowLayer, 0, 0, W, H);
      ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
    }
    scene(ctx, false);

    for (const r of ripples) { r.r += dt * S * (1.2 + r.r / S); r.a -= dt * .5; }
    for (let i = ripples.length - 1; i >= 0; i--) if (ripples[i].a <= 0) ripples.splice(i, 1);
    if (!still) requestAnimationFrame(frame);
  }

  // ---- input: every pointer is a person ----
  const local = e => { const b = cv.getBoundingClientRect(); return [e.clientX - b.left, e.clientY - b.top]; };
  area.addEventListener('pointermove', e => {
    const [x, y] = local(e), q = touches.get(e.pointerId) || { down: false };
    if (drag && drag.id === e.pointerId) {
      const dx = x - drag.x, dts = Math.max(.016, (e.timeStamp - drag.t) / 1000);
      O.yaw += dx / S * .8; O.vyaw = dx / S * .8 / dts; drag.moved += Math.abs(dx) + Math.abs(y - drag.y);
      drag.x = x; drag.y = y; drag.t = e.timeStamp;
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
    if (q && q.down && !(drag && drag.id === e.pointerId && drag.moved > 14)) {   // a tap or a hold: gather, and ripple out
      boost = 1; ripples.push({ r: S * .5, a: Math.min(1, .7 + (e.timeStamp - q.t0) / 2000) });
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
if (cv) startCurrents(cv, cv.parentElement);
