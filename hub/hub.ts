import osc from 'osc';
import { mkdirSync, createWriteStream } from 'node:fs';
import { join } from 'node:path';
import { syncScore, roomColour, elementAgreement, type CupState } from '../src/sync';
import { ELEMENTS, type Element } from '../src/fiveElements';

// The sync hub. Ingests the three cups over OSC, computes the collective
// synchronisation score and the room colour, republishes to TouchDesigner (the
// generative colour fields and the room layer), and logs a timestamped record of
// every tick. That log is both the paper's dataset and the Oryn 계 (Gye) feed.
//
// The cups already glow on their own; this hub only adds the collective layer.
// Run: npm run hub

const LISTEN_PORT = 8000; // the cups send /cup here
const TD_HOST = '127.0.0.1'; // the TouchDesigner machine
const TD_PORT = 9000; // TouchDesigner's OSC In CHOP port
const TICK_HZ = 20;
const CUP_TIMEOUT_MS = 2000;

interface CupRecord {
  pressure: number;
  bpm: number;
  confidence: number;
  element: number;
  rgb: [number, number, number];
  lastSeen: number;
}
const cups = new Map<number, CupRecord>();

// session log (one file per run)
mkdirSync('logs', { recursive: true });
const stamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
const logFile = join('logs', `session-${stamp}.jsonl`);
const log = createWriteStream(logFile, { flags: 'a' });
console.log('sync hub, logging to', logFile);

const udp = new osc.UDPPort({
  localAddress: '0.0.0.0',
  localPort: LISTEN_PORT,
  remoteAddress: TD_HOST,
  remotePort: TD_PORT,
  metadata: false,
});

udp.on('ready', () => console.log(`listening on ${LISTEN_PORT}, republishing to TouchDesigner at ${TD_HOST}:${TD_PORT}`));
udp.on('error', (e: Error) => console.error('osc error:', e.message));
udp.on('message', (m: { address: string; args: number[] }) => {
  if (m.address === '/cup' && m.args.length >= 8) {
    const [id, pressure, bpm, confidence, element, r, g, b] = m.args as number[];
    cups.set(id!, { pressure: pressure!, bpm: bpm!, confidence: confidence!, element: element!, rgb: [r!, g!, b!], lastSeen: Date.now() });
  }
});
udp.open();

setInterval(() => {
  const now = Date.now();
  for (const [id, c] of cups) if (now - c.lastSeen > CUP_TIMEOUT_MS) cups.delete(id);
  const list = [...cups.entries()].sort((a, b) => a[0] - b[0]);

  const states: CupState[] = list.map(([, c]) => ({ bpm: c.bpm, pressure: c.pressure }));
  const sync = syncScore(states);
  const room = roomColour(list.map(([, c]) => c.rgb), sync);
  const agree = elementAgreement(list.map(([, c]) => (ELEMENTS[c.element] ?? 'earth') as Element));

  // republish the collective layer to TouchDesigner
  udp.send({ address: '/circulation/sync', args: [sync] });
  udp.send({ address: '/circulation/agreement', args: [agree] });
  udp.send({ address: '/circulation/room', args: [room[0], room[1], room[2]] });
  for (const [id, c] of list) {
    udp.send({ address: `/circulation/cup/${id}`, args: [c.pressure, c.bpm, c.confidence, c.element, c.rgb[0], c.rgb[1], c.rgb[2]] });
  }

  // log the tick (paper dataset + Oryn 계 feed)
  log.write(
    JSON.stringify({
      t: new Date().toISOString(),
      cups: Object.fromEntries(list.map(([id, c]) => [id, { pressure: +c.pressure.toFixed(3), bpm: Math.round(c.bpm), confidence: +c.confidence.toFixed(2), element: c.element }])),
      sync: +sync.toFixed(3),
      agreement: +agree.toFixed(3),
      room,
    }) + '\n',
  );
}, 1000 / TICK_HZ);
