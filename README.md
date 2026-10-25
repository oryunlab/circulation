# circulation

**Cupping, Colour, and Collective Sensing.** Three handheld cupping-form devices
read the body through grip pressure and pulse, and glow the colour of its present
state in the Five Elements (오행). As three participants synchronise, pulses
converging and grips aligning, the colours harmonise and, where the venue allows,
the room blooms with a collective colour field. The cups are the seed; the room
is the bloom.

Cupping (부항 / giác hơi / 拔罐) is a shared Asia Pacific care practice. The hold
itself is the diagnostic gesture, after the O-ring test (오링 테스트): how firmly,
steadily, and long a hand grips. This is a design source and cultural coordinate
system, **not medical advice**; it reads present state, not fixed constitution.

SCD Seed Funding 2026, funded build June to November 2026. Part of Øryn (륜).
Grounded in the artist's practice of Korean hand acupuncture (수지침).

## What is here now

- **The system (live simulator):** `index.html`. Three virtual cups running the
  real Five Elements engine and synchronisation metric, so the interaction can be
  designed and tuned before the hardware exists. Drag the sliders.
- **The process log:** `log.html`. A dated record of the build.
- **The cup firmware:** `hardware/cup/`. ESP32 + FSR + MAX30102 + LED ring,
  computing the same colour on-device and streaming over OSC.

## How it is built

- `src/fiveElements.ts` — the mapping engine. Grip pressure, its trend, pulse
  rate, pulse regularity, and sustained hold map to one of the Five Elements and
  a colour. One specification, implemented here in TypeScript and in C++ on the
  cup, so the two can never disagree. This is also the paper's system description.
- `src/sync.ts` — collective synchronisation (pulse convergence + pressure
  alignment) and the room colour, kept slow and legible so convergence feels
  earned, not arbitrary.
- `src/main.ts` — the simulator.

## Architecture

Each cup is self-sufficient: it computes its own reading and drives its own LED,
with no dependency on the hub or on TouchDesigner. A small hub ingests the three
cups over OSC, computes the synchronisation score, and republishes to
TouchDesigner (generative colour fields, the room layer) and back to the cups. So
the object installation survives even if TouchDesigner, the network, or the room
layer is unavailable.

## Run it

```
npm install
npm run dev
```

## Deploy

Push to `main`; GitHub Actions builds and publishes to GitHub Pages. Vite `base`
is set to the repo name.

## Five Elements colour map

| Element | Colour | Organ | State |
| --- | --- | --- | --- |
| Wood (목) | green | Liver / Gallbladder | growth |
| Fire (화) | red | Heart / Small Intestine | activation |
| Earth (토) | yellow | Spleen / Stomach | grounding |
| Metal (금) | white | Lung / Large Intestine | release |
| Water (수) | deep blue | Kidney / Bladder | stillness |
