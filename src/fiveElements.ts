// The Five Elements (오행) mapping engine: the conceptual core of Circulation.
//
// A cup reads a two-signal portrait of the body holding it, grip pressure (from
// a force sensor) and pulse (from a PPG sensor), and maps that present state to
// one of the Five Elements, each an organ system and a colour. This is a display
// convention, not a diagnosis: it reads present state, not fixed constitution.
//
// The same spec is implemented in C++ on the ESP32 (hardware/cup/cup.ino), so
// what is tuned in the browser simulator is exactly what runs in the cup.
//
// Interaction logic (from the grant):
//   strong grip + elevated pulse        -> Fire  (red,    activation)
//   slow sustained hold + calm pulse     -> Water (blue,   stillness)
//   steady medium grip + regular rhythm  -> Earth (yellow, grounding)
//   building, expanding hold             -> Wood  (green,  growth)
//   releasing, irregular grip            -> Metal (white,  release)

export type Element = 'wood' | 'fire' | 'earth' | 'metal' | 'water';

export const ELEMENTS: Element[] = ['wood', 'fire', 'earth', 'metal', 'water'];

export const ELEMENT_INFO: Record<Element, { hanja: string; ko: string; organ: string; state: string; rgb: [number, number, number] }> = {
  wood: { hanja: '목', ko: '목', organ: 'Liver / Gallbladder', state: 'growth', rgb: [95, 174, 106] },
  fire: { hanja: '화', ko: '화', organ: 'Heart / Small Intestine', state: 'activation', rgb: [229, 84, 75] },
  earth: { hanja: '토', ko: '토', organ: 'Spleen / Stomach', state: 'grounding', rgb: [224, 178, 60] },
  metal: { hanja: '금', ko: '금', organ: 'Lung / Large Intestine', state: 'release', rgb: [238, 241, 244] },
  water: { hanja: '수', ko: '수', organ: 'Kidney / Bladder', state: 'stillness', rgb: [47, 93, 138] },
};

/** One frame of a cup's two-signal reading, already conditioned by the caller. */
export interface CupSignal {
  pressure: number; // 0..1 grip force (calibrated)
  pressureTrend: number; // -1..1 rising (building) vs falling (releasing), short window
  bpm: number; // pulse rate
  regularity: number; // 0..1 beat steadiness (1 = very regular)
  hold: number; // 0..1 sustained, still hold (from duration + steadiness)
  confidence: number; // 0..1 pulse confidence; low leans the reading on pressure
}

export interface ElementReading {
  element: Element; // dominant
  weights: Record<Element, number>; // normalized blend, sums to 1
  rgb: [number, number, number]; // blended colour, 0..255
}

function smoothstep(edge0: number, edge1: number, x: number): number {
  const t = Math.max(0, Math.min(1, (x - edge0) / (edge1 - edge0)));
  return t * t * (3 - 2 * t);
}

/** Map a conditioned cup signal to a Five Elements reading. Pure, deterministic. */
export function readElement(s: CupSignal): ElementReading {
  const bpmHi = smoothstep(70, 105, s.bpm); // activation
  const bpmLo = 1 - smoothstep(55, 85, s.bpm); // calm
  const pressureMedium = 1 - Math.min(1, Math.abs(s.pressure - 0.5) * 2);
  const conf = Math.max(0, Math.min(1, s.confidence));

  // Raw element affinities. Pulse-dependent elements (fire, water) are damped
  // when pulse confidence is low, so a noisy PPG never invents activation.
  const raw: Record<Element, number> = {
    fire: s.pressure * bpmHi * (0.35 + 0.65 * conf),
    water: s.hold * bpmLo * (0.5 + 0.5 * (1 - s.pressure)) * (0.4 + 0.6 * conf),
    earth: pressureMedium * s.regularity,
    wood: Math.max(0, s.pressureTrend),
    metal: Math.max(0, -s.pressureTrend) * 0.7 + (1 - s.regularity) * 0.5,
  };

  // Normalize to blend weights (with a small floor so it never collapses).
  let sum = 0;
  for (const e of ELEMENTS) sum += raw[e];
  const weights = {} as Record<Element, number>;
  if (sum < 1e-4) {
    for (const e of ELEMENTS) weights[e] = e === 'earth' ? 1 : 0; // default: grounding
  } else {
    for (const e of ELEMENTS) weights[e] = raw[e] / sum;
  }

  // Dominant + blended colour.
  let element: Element = 'earth';
  let best = -1;
  const rgb: [number, number, number] = [0, 0, 0];
  for (const e of ELEMENTS) {
    if (weights[e] > best) { best = weights[e]; element = e; }
    const c = ELEMENT_INFO[e].rgb;
    rgb[0] += c[0] * weights[e];
    rgb[1] += c[1] * weights[e];
    rgb[2] += c[2] * weights[e];
  }
  return { element, weights, rgb: [Math.round(rgb[0]), Math.round(rgb[1]), Math.round(rgb[2])] };
}
