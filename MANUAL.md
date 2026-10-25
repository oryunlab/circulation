# Circulation, the manual

What every file in this repository is, where it runs, and what you do with it at each phase between now and the end of the funded period (30 November 2026). The project does not target VFCD in September; the whole window goes into building the machine fully, and the capstone is a finished, documented, endurance-tested three-cup system. Read top to bottom once; after that, jump to the phase you are in.

## The one rule everything follows

Each cup is self-sufficient: it senses, computes its Five Elements colour, and glows with no network and no computer. Everything else (hub, TouchDesigner, room) is an optional layer above a system that already works. If a change would break that, do not make the change.

## The map: what each file is

### The shared spec (the artwork's logic, one truth in two languages)

- `src/fiveElements.ts` is the Five Elements (오행) mapping engine: pressure, trend, pulse, regularity, and hold become an element and a colour. This file is also the system description for the paper.
- `src/sync.ts` is the collective layer: the synchronisation score, the room colour, and the 상생 generating-cycle circulation reading (score, flow edges, chain).
- `hardware/cup/cup.ino` is the C++ mirror of the engine plus the presence and afterglow behaviour, running on the cup itself.

Rule: if you change the mapping, change it in `src/fiveElements.ts` AND `cup.ino` together (ask Claude to do both in one pass). If the browser and the cup ever disagree, the project's core claim breaks.

### The site (what you, curators, and the public see)

- `index.html` is the live simulator page: three virtual cups, the flow layer, the room.
- `src/main.ts` is the simulator's code: presence, afterglow marks, light travelling cup to cup, sliders. Interaction tuning happens here first, hardware second.
- `src/cupView.ts` is the rendering shared by `index.html` and `sim.html`: the cup panel, colour helpers, the flow layer, and the presence/afterglow display state. If you touch how a cup is drawn, change it here once for both pages.
- `sim.html` / `src/sim.ts` is the physical computing simulation: the same three-cup stage, but a grip and a heart rate pass through `src/sensorSim.ts` (simulated FSR/MAX30102 sensor behaviour) before reaching the engine, instead of clean sliders. Fault toggles per cup (loose palm seal, fidgeting, never calibrated) rehearse the open questions from `hardware/TECHNICIAN_BRIEF.txt`.
- `src/sensorSim.ts` is the sensor model: raw ADC counts, FSR calibration bounds, the MAX30102 IR contact threshold and confidence formula, and beat-to-beat jitter, mirroring `cup.ino`'s exact constants so tuning it is tuning the firmware's constants.
- `log.html` is the process log. Add an entry every week you build something; it is the grant report, the paper's process documentation, and the curator-facing story in one file.
- `.github/workflows/deploy.yml` deploys automatically: every push to main rebuilds the site at https://circulatorysensing.com/circulation/ in about 30 seconds. You never deploy manually.

### The hardware layer

- `hardware/cup/cup.ino` is the firmware you will flash onto each ESP32. The config block at the top (CUP_ID, Wi-Fi, hub address, pins, FSR calibration, PRESENCE, MARK_FADE_S) is the only part you edit per cup.
- `hardware/cup/README.md` is the wiring and library guide for the firmware.
- `hardware/TECHNICIAN_BRIEF.txt` is the meeting document: build direction (real cups, printed insert), sensors, parts list, contracts, safety line. Copy-paste ready, single-line paragraphs.
- `wokwi/` is a circuit simulation of `cup.ino` itself: a virtual ESP32 + FSR + LED ring (see `wokwi/README.md` for what's real vs. a stand-in), so the firmware's sensor-to-LED logic can be exercised with no hardware, before or alongside a real build.

### The collective layer (after three cups exist)

- `hub/hub.ts` is the sync hub: it listens to all cups over OSC (port 8000), computes sync and the room colour, republishes to TouchDesigner (port 9000), and logs every tick to `logs/session-*.jsonl`. Those logs are the paper's dataset and the 계 archive feed. Runs on your laptop with `npm run hub`.
- `hub/README.md` explains its ports and message schema.
- `touchdesigner/RECIPES.md` is your from-zero TouchDesigner path, one concrete artifact per recipe, ending at a festival-ready show patch. TD sits above the hub and is optional by design.

### The paper and reporting

- `Circulation_Paper_Draft_and_Figure_Prompts.md` is the paper draft (target ISEA 2027) with its figure plan.
- `circulation-figure-prompts.txt` is the extracted figure prompts, copy-paste ready.
- `Circulation_Monthly_Reports_Aug-Nov_2026.md` is the SCD grant reporting skeleton for August to November.

### Plumbing (you rarely touch these)

- `package.json`, `package-lock.json`, `tsconfig.json`, `vite.config.ts`, `.gitignore`, `src/vite-env.d.ts`, and `README.md` (the repo's front page).

## What runs where

- Browser, anywhere: the simulator (live on GitHub Pages, or locally with `npm run dev`).
- The cup (ESP32): `cup.ino`, standalone.
- Your laptop at the venue: the hub (`npm run hub`), and TouchDesigner if used.
- GitHub: hosting, auto-deploy, and the public archive of everything.

## What you do, phase by phase

### Now, before any parts arrive

1. Tune the interaction in the simulator until the mapping feels true. The knobs are all named constants: element thresholds in `src/fiveElements.ts`, sync windows in `src/sync.ts`, `PRESENCE` and `MARK_FADE_S` in `src/main.ts`. Ask Claude to change a value, push, and feel it live two minutes later.
2. Take `hardware/TECHNICIAN_BRIEF.txt` to the technician meeting.
3. Buy a real cupping cup set and order the parts list in the brief. Lead times are the schedule risk.
4. Hold a cup mouth-down on your palm for a minute; the posture decides the insert design.

### Bench week, when parts arrive

1. Install the Arduino IDE, add ESP32 board support (Boards Manager URL: `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`), and install the three libraries named at the top of `cup.ino` (SparkFun MAX3010x, Adafruit NeoPixel, CNMAT OSC).
2. One component at a time, breadboard first: LED ring alone, then FSR alone, then MAX30102 alone, watching the Serial Plotter. Never debug two new parts at once.
3. Note: the pin numbers in `cup.ino` assume a classic ESP32 dev board. If the build uses a Xiao ESP32-C3 (the brief's recommendation, since a full board will not fit the cup), the pins in the config block must be remapped for that board. This is a five-minute job for the technician or Claude; just do not flash blindly.
4. Run the two bench experiments from the brief: palm PPG under seal pressure (the design decider) and BMP280 inside a sealed cup. Uncomment `#define RAW_LOG` in `cup.ino` to print raw sensor values for this. Keep all logs.
5. Verify the afterglow port on real hardware: grip, release, and watch the ring hold and fade over about 40 seconds. It mirrors the simulator but has never run on a physical LED ring.

### MVP gate, end of August

1. One untethered cup: insert in a real cup, battery or power bank, hand to colour, stable for 30 minutes.
2. Calibrate: set `FSR_MIN` and `FSR_MAX` (or the BMP280 equivalents) per cup from RAW_LOG values, and set `CUP_ID` 1, 2, 3.
3. An internal pilot with colleagues (around ten hands) closes the month: log every session, note which grips break the reading.
4. Only after this gate passes: build the other two.

### September: three cups and the collective layer

1. Put the cups and your laptop on one Wi-Fi network, set `WIFI_SSID` and `HUB_HOST` in each cup's config block.
2. Run `npm run hub` in this folder. Cups appear as `/cup` messages; the hub logs every session to `logs/`. Those files are your dataset; back them up.
3. Rehearse the three-body choreography with real people and tune the sync windows in `src/sync.ts` against what real triads do.
4. Iterate the insert and enclosure with what the pilot taught you; September is for making the triad solid, not for shipping it.

### October: the room, and endurance

1. Work through `touchdesigner/RECIPES.md` in order. The hub already speaks to TD on port 9000; TD only listens and paints. The room layer is still optional by architecture (if TD fails, the cups still work), but October is its scheduled month, no longer a cut line.
2. Endurance: full-afternoon soak tests, battery rotation drills, hygiene protocol (alcohol wipes between hands). The machine must run unattended-long, not demo-long.
3. Structured triad sessions with invited participants, logged through the hub: this is the dataset the paper is written from.

### November: finish, document, archive

1. Documentation video and photography of the finished system to submission standard.
2. Launch the standalone project website and 10-year archive (a budgeted deliverable), folding in the simulator, the process log, and rendered session data.
3. A final showing for the school (R&I team, mentor, collaborators): the working triad, run like a rehearsal of a future exhibition. Keep the demo kit ready: spare cup body and insert, charged power banks, wipes, printed contracts, phone hotspot; the serial CSV fallback in `cup.ino` means a cup can be read over a USB cable if Wi-Fi dies.
4. Final seed-funding report and the paper draft. The funded period closes 30 November; the machine, the dataset, the archive, and the draft are the deliverables.

## Command cheat sheet (run in this folder)

- `npm install` once after cloning on a new machine.
- `npm run dev` local simulator at the printed localhost address.
- `npm run hub` the sync hub (needs cups or a test sender on the network).
- `npm run typecheck` and `npm run build` sanity checks; the deploy runs build itself.
- Push to main and the site updates itself; watch the Actions tab on GitHub if unsure.

## Contracts that must not change

- OSC cup to hub, port 8000: `/cup id pressure bpm confidence element r g b`.
- OSC hub to TD, port 9000: `/circulation/sync`, `/circulation/agreement`, `/circulation/room`, `/circulation/cup/<id>`.
- The generating cycle: Wood feeds Fire, Fire feeds Earth, Earth feeds Metal, Metal feeds Water, Water feeds Wood.
- No real suction marks on visitors' skin. The LED afterglow is the mark.
