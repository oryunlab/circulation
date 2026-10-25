// Collective synchronisation: the metric that makes three cups become one.
//
// As participants synchronise (pulses converging, grip pressures aligning), the
// score rises toward 1 and the room colour blooms from the three cup colours.
// The metric is kept deliberately legible and slow so convergence feels earned,
// not arbitrary: the risk this project must avoid is synchronisation reading as
// mood lighting. Tune the two windows below against real triads.

import { ELEMENTS, type Element } from './fiveElements';

export interface CupState {
  bpm: number;
  pressure: number; // 0..1
}

const BPM_CONVERGE = 22; // within this spread, pulses count as converging
const PRESSURE_ALIGN = 0.45; // within this spread, grips count as aligned

/** 0..1 collective synchronisation from the current cup states (before smoothing). */
export function syncScore(cups: CupState[]): number {
  const active = cups.filter((c) => c.bpm > 20);
  if (active.length < 2) return 0;
  const bpms = active.map((c) => c.bpm);
  const ps = active.map((c) => c.pressure);
  const bpmSpread = Math.max(...bpms) - Math.min(...bpms);
  const pSpread = Math.max(...ps) - Math.min(...ps);
  const bpmConv = 1 - Math.min(1, bpmSpread / BPM_CONVERGE);
  const pAlign = 1 - Math.min(1, pSpread / PRESSURE_ALIGN);
  const pairs = active.length / cups.length; // 2 of 3 present counts less than 3 of 3
  return Math.max(0, Math.min(1, (0.6 * bpmConv + 0.4 * pAlign) * pairs));
}

/**
 * The room colour: the average of the cup colours, brought to life by the sync
 * score. Low sync leaves it muted and grey; high sync makes it a vivid, unified
 * field. The cups are the seed; the room is the bloom.
 */
export function roomColour(cupRgb: Array<[number, number, number]>, sync: number): [number, number, number] {
  if (cupRgb.length === 0) return [20, 20, 24];
  const avg: [number, number, number] = [0, 0, 0];
  for (const c of cupRgb) { avg[0] += c[0]; avg[1] += c[1]; avg[2] += c[2]; }
  avg[0] /= cupRgb.length; avg[1] /= cupRgb.length; avg[2] /= cupRgb.length;
  // desaturate toward grey when unsynced, saturate + brighten when synced
  const grey = (avg[0] + avg[1] + avg[2]) / 3;
  const k = 0.25 + 0.75 * sync;
  return [
    Math.round((grey + (avg[0] - grey) * k) * (0.55 + 0.45 * sync)),
    Math.round((grey + (avg[1] - grey) * k) * (0.55 + 0.45 * sync)),
    Math.round((grey + (avg[2] - grey) * k) * (0.55 + 0.45 * sync)),
  ];
}

// --- Circulation along the generating cycle (상생) ---
//
// Synchronisation is agreement; circulation is passage. The generating cycle,
// wood feeds fire feeds earth feeds metal feeds water feeds wood, gives the
// project's title its literal mechanic: when the group's elements sit adjacent
// on the cycle, light travels from cup to cup in the generating direction.
// Like the rest of this file it is part of the shared spec: the hub republishes
// it and the firmware can mirror it.

/** The generating order: each element feeds the next, water feeds wood. */
export const GENERATING: Element[] = ['wood', 'fire', 'earth', 'metal', 'water'];

/** True when element a generates (feeds) element b on the 상생 cycle. */
export function generates(a: Element, b: Element): boolean {
  return GENERATING[(GENERATING.indexOf(a) + 1) % GENERATING.length] === b;
}

export interface CirculationReading {
  score: number; // 0..1: how much of a full generating chain the held cups form
  edges: Array<{ from: number; to: number }>; // cup indices, in the generating direction
  chain: number[]; // the longest generating chain, cup indices in flow order
}

/**
 * Flow along the generating cycle, from the cups' dominant elements.
 * Pass null for a cup that is not being held; released cups do not circulate.
 */
export function circulationReading(elements: Array<Element | null>): CirculationReading {
  const held: Array<{ e: Element; i: number }> = [];
  elements.forEach((e, i) => { if (e !== null) held.push({ e, i }); });

  const edges: Array<{ from: number; to: number }> = [];
  for (const a of held) {
    for (const b of held) {
      if (a.i !== b.i && generates(a.e, b.e)) edges.push({ from: a.i, to: b.i });
    }
  }

  // Longest generating chain (cup count is tiny, brute force is legible).
  let chain: number[] = [];
  const extend = (path: number[]): void => {
    if (path.length > chain.length) chain = [...path];
    const tip = path[path.length - 1];
    for (const ed of edges) {
      if (ed.from === tip && !path.includes(ed.to)) extend([...path, ed.to]);
    }
  };
  for (const h of held) extend([h.i]);

  const score = held.length < 2 ? 0 : Math.max(0, chain.length - 1) / (held.length - 1);
  return { score, edges, chain };
}

/** How aligned the three cups' dominant elements are, for a readout (0..1). */
export function elementAgreement(elements: Element[]): number {
  if (elements.length < 2) return 0;
  const counts = {} as Record<Element, number>;
  for (const e of ELEMENTS) counts[e] = 0;
  for (const e of elements) counts[e]++;
  const top = Math.max(...ELEMENTS.map((e) => counts[e]));
  return (top - 1) / (elements.length - 1);
}
