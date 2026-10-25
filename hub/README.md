# Sync hub

The collective layer. The three cups each glow on their own; the hub adds
synchronisation and the room. It listens for the cups over OSC, computes the
sync score and the room colour (reusing `src/sync.ts`, the same logic the
simulator uses), republishes to TouchDesigner, and logs every tick.

```
npm install
npm run hub
```

## Config (top of hub/hub.ts)

- `LISTEN_PORT` (8000): the cups send `/cup` here.
- `TD_HOST` / `TD_PORT` (127.0.0.1 : 9000): TouchDesigner's OSC In CHOP.
- `TICK_HZ` (20): republish + log rate.

## In (from the cups)

```
/cup  <id:int> <pressure:float> <bpm:float> <confidence:float>
      <element:int 0..4> <r:int> <g:int> <b:int>
```

## Out (to TouchDesigner)

```
/circulation/sync        <score:float 0..1>
/circulation/agreement   <element agreement:float 0..1>
/circulation/room        <r:int> <g:int> <b:int>
/circulation/cup/<id>    <pressure> <bpm> <confidence> <element> <r> <g> <b>
```

Point TouchDesigner's OSC In CHOP at port 9000 (see `touchdesigner/RECIPES.md`).

## The log (the point of the hub)

Each run writes `logs/session-<timestamp>.jsonl`, one JSON object per tick:
timestamp, each cup's pressure / bpm / confidence / element, the sync score,
element agreement, and the room colour. This is the interaction dataset the paper
is written from, and the feed for Oryn's 계 (Gye) archive. Keep every session
file, from bench tests to the structured triad sessions.
