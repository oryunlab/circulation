import { readElement, ELEMENT_INFO, type CupSignal } from './fiveElements';
import { syncScore, roomColour, elementAgreement, circulationReading, type CupState } from './sync';
import { rgbCss, createCupPanel, ctl, createFlow, createCupVisual, stepCupVisual, type CupVisual } from './cupView';

// Browser simulator for Circulation. Three virtual cups run the real Five
// Elements engine, the real synchronisation metric, and the real generating-
// cycle (상생) circulation reading, so the interaction can be designed and tuned
// before any hardware exists (and this ships on the site as living
// documentation). Pressure trend and sustained-hold are derived from how you
// move the sliders over time, exactly as they will be on the cup.
//
// This is an idealised model, clean 0..1 inputs, to feel out the mapping
// itself. sim.html runs the same engine through simulated sensor noise.

const CUP_COUNT = 3;
const PRESENCE = 0.12; // grip below this reads as a released cup

interface Cup extends CupVisual {
  // raw slider values
  pressure: number;
  bpm: number;
  regularity: number;
  confidence: number;
  // derived over time
  prevPressure: number;
  trend: number;
  holdT: number;
}

const cupsEl = document.getElementById('cups')!;
const stageEl = document.getElementById('stage')!;
const flowEl = document.getElementById('flow') as HTMLCanvasElement;
const roomBar = document.getElementById('room-bar')!;
const roomMeta = document.getElementById('room-meta')!;
const cups: Cup[] = [];

for (let i = 0; i < CUP_COUNT; i++) {
  const dom = createCupPanel(cupsEl);
  dom.controls.innerHTML = `
    ${ctl('pressure', 0, 1, 0.01, 0)}
    ${ctl('pulse bpm', 40, 120, 1, 68)}
    ${ctl('regularity', 0, 1, 0.01, 0.7)}
    ${ctl('pulse confidence', 0, 1, 0.01, 0.9)}
  `;

  const inputs = dom.controls.querySelectorAll('input');
  const cup: Cup = {
    ...createCupVisual(dom),
    pressure: 0, bpm: 68, regularity: 0.7, confidence: 0.9,
    prevPressure: 0, trend: 0, holdT: 0,
  };
  (inputs[0] as HTMLInputElement).addEventListener('input', (e) => { cup.pressure = parseFloat((e.target as HTMLInputElement).value); });
  (inputs[1] as HTMLInputElement).addEventListener('input', (e) => { cup.bpm = parseFloat((e.target as HTMLInputElement).value); });
  (inputs[2] as HTMLInputElement).addEventListener('input', (e) => { cup.regularity = parseFloat((e.target as HTMLInputElement).value); });
  (inputs[3] as HTMLInputElement).addEventListener('input', (e) => { cup.confidence = parseFloat((e.target as HTMLInputElement).value); });
  cups.push(cup);
}

const flow = createFlow(stageEl, flowEl, cups);

// --- Main loop ---

let last = performance.now();
function loop(now: number): void {
  const dt = Math.min(0.05, (now - last) / 1000);
  last = now;

  for (const c of cups) {
    // derive trend from slider motion (rising = building/Wood, falling = releasing/Metal)
    const dp = c.pressure - c.prevPressure;
    c.trend = Math.max(-1, Math.min(1, c.trend * 0.86 + dp * 9));
    c.prevPressure = c.pressure;
    // derive sustained-hold: accumulates on a steady, present grip
    if (c.pressure > 0.15 && Math.abs(c.trend) < 0.12) c.holdT += dt; else c.holdT *= 0.7;
    const hold = Math.min(1, c.holdT / 4);

    const present = c.pressure > PRESENCE;
    const signal: CupSignal = {
      pressure: c.pressure, pressureTrend: c.trend, bpm: c.bpm,
      regularity: c.regularity, hold, confidence: c.confidence,
    };
    stepCupVisual(c, dt, present, present ? readElement(signal) : null, c.trend);
  }

  // collective
  const states: CupState[] = cups.map((c) => ({ bpm: c.bpm, pressure: c.pressure }));
  const sync = syncScore(states);
  const room = roomColour(cups.map((c) => c.shown), sync); // fading marks still tint the room
  const heldElements = cups.filter((c) => c.present).map((c) => c.element);
  const agree = elementAgreement(heldElements);
  const circ = circulationReading(cups.map((c) => (c.present ? c.element : null)));

  flow.draw(dt, circ.edges);

  const chainText = circ.chain.length >= 2
    ? circ.chain.map((i) => `${cups[i]!.element} ${ELEMENT_INFO[cups[i]!.element].hanja}`).join(' feeds ')
    : '';
  const status = circ.score >= 1 && heldElements.length >= 3
    ? `the cycle turns: ${chainText}`
    : chainText
      ? chainText
      : sync > 0.7 ? 'the room blooms' : sync > 0.35 ? 'beginning to harmonise' : 'separate bodies';

  roomBar.style.background = rgbCss([Math.round(room[0]), Math.round(room[1]), Math.round(room[2])] as [number, number, number]);
  roomMeta.innerHTML =
    `<div>synchronisation <b>${Math.round(sync * 100)}</b></div>` +
    `<div>circulation <b>${Math.round(circ.score * 100)}</b></div>` +
    `<div>element agreement <b>${Math.round(agree * 100)}</b></div>` +
    `<div>${status}</div>`;

  requestAnimationFrame(loop);
}
requestAnimationFrame(loop);
