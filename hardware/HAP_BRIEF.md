# Circulation: Hap production brief

Prepared 23 October 2026 for the technician. Bin Youn, RMIT Vietnam. SCD Seed Funding 2026.
Funded build ends **30 November 2026**.

**Drawings and live simulator:** https://circulatorysensing.com/circulation/design.html
(top view, section, exploded light box, socket and mounting details, cup pad band, parts schedule).
Open it first; this brief refers to it.

**Name.** The round table with the light box at its centre is called the **Hap** (Korean 합, Vietnamese hợp, Chinese 合): the meeting point where flows join, from the classical five transport points (井 well · 滎 spring · 輸 stream · 經 river · 合 Hap). In this brief, "the Hap" means the whole table.

This brief **replaces the build direction in `TECHNICIAN_BRIEF.txt` (11 July)**. What changed:

| July brief | Now |
|---|---|
| Transparent vacuum cupping cups, palm seals the mouth | Custom 3D-printed cup, Ø7 cm, dome on a band with **five finger pads** |
| Pressure (BMP280 or FSR) + pulse (MAX30102) | **Five FSRs per cup, no pulse sensor** |
| Cups untethered on battery | Cups **dock in the Hap** (the table) and take power through the seat |
| Room layer optional (TouchDesigner) | Physical centre piece: a **light box with 31 acrylic rods** in the table |

Unchanged: no suction on skin, cups must be alcohol-wipeable, 2× spares of everything, keep all raw sensor logs.

---

## 1. What it is

Three people sit around a round table. Each presses a small cup with all five fingertips.
Each finger pad lights its own colour at once. The light runs down a groove in the cup,
then steps inward along a "vessel" in the tabletop to a light box in the centre, where
acrylic rods glow. When the three hands press in similar patterns, the colours in the
centre move inward and merge.

## 2. Key dimensions

| Part | Size |
|---|---|
| Table | Ø100 cm round, 18 mm ply top, seated height 74 cm (seated vs standing still to confirm) |
| Cup seats | 3 at 120°, cup centre 40 cm from table centre (10 cm in from the edge) |
| Cup | Ø7 cm; height from CAD (drawings assume 7.5 cm) |
| Finger pads | 5 per cup, about 2.2 × 2.6 cm oval, 4.4 cm pitch around the 22.0 cm circumference |
| Groove rods in cup | Ø3 mm clear acrylic, one under each pad, running down to the base |
| Vessels | ~23 cm from cup seat to light box, in a 10 mm groove in the tabletop; rod segments 6–8 cm, Ø4 → 6 → 8 mm toward the centre |
| Light box (drum) | Ø26 cm, 6 cm deep, hangs under the tabletop by a flange; lid flush with the top |
| Rods | Outer ring Ø22 cm: 14 × Ø4 mm × 8 cm · middle Ø14 cm: 10 × Ø5 mm × 15 cm · inner Ø7 cm: 6 × Ø6 mm × 22 cm · core 1 × Ø12 mm × 30 cm (heights above the lid) |

## 3. Electronics (proposed; please challenge)

**Per cup** (keeps the rule that a cup still glows if the table controller fails):
- Small ESP32 board with at least 5 ADC pins (e.g. Seeed XIAO ESP32-S3). Note: the XIAO ESP32-C3 has only 4 usable analog pins, not enough.
- 5 × FSR (one behind each pad), each with a voltage-divider resistor.
- 5 × single NeoPixel (one behind each pad, lighting the pad and the top of its groove rod).
- 1 × 7-pixel NeoPixel jewel under the dome.
- 1 × 10 mm coin vibration motor + small NPN transistor/MOSFET and flyback diode.
- Connection through the seat: **4 contacts (5 V, GND, TX, RX)**. Magnetic pogo connector preferred so the cup lifts out for cleaning. Your call on the connector.

**In the table:**
- 1 × ESP32 table controller driving all table pixels on one data line through a 3.3 → 5 V level shifter.
- Pixels: 3 merge nodes + 9 vessel nodes + 31 rod pixels + 7-pixel core jewel = **50**.
- Rod pixels are single WS2812B pixels (cut strip or single-pixel boards) placed under each rod. Ready-made concentric ring sets are too small (≈10 cm) for the 22 cm outer ring.
- 5 V 4 A supply (85 pixels total; brightness capped in firmware). Fuse the supply line.
- Talks to the cups over the seat UART, and to the laptop (hub, TouchDesigner, sound) over Wi-Fi OSC.
- Speaker: **Patrick specifies the sound hardware.** Reserve space in the service tray and a grille in the drum wall.

## 4. Light box build (see exploded view and detail A/B on the page)

Top to bottom:
1. **Rods** drop into sockets in the lid and stop 0–0.5 mm above their pixel.
2. **Lid:** 5 mm frosted acrylic, Ø26 cm, laser-cut holes = rod Ø + 0.25 mm. Sits in a 5 mm rebate, flush with the tabletop, lifts out.
3. **Light baffle:** black PETG print, 15 mm deep, one tube per rod so colours don't bleed.
4. **Pixel plate:** 3 mm, 31 single pixels + core jewel, daisy-chained ring by ring (outer → core).
5. **Drum:** Ø26 × 6 cm, printed in segments or bent ply, flange screwed under the tabletop, three vessel ports at 120°.
6. **Service tray:** ESP32, supply, level shifter, sound; drops out from below for repairs.

Rod finishing: cut, polish the bottom end flat (it sits on the LED), polish the sides (light
stays inside), sand the top tip (light comes out there). In the cup, sand the 3 mm groove
rods along their length so they glow. Print the pad band in opaque black PETG so the five
channels stay separate; print the dome white or translucent.

## 5. Bench tests before fabrication (please do these first)

1. **Light-pipe coupon.** One pixel; rods Ø3, 5 and 8 mm at 10 and 25 cm; ends polished, frosted, or notched. Photograph each in a dark room. This fixes rod sizes and finishes.
2. **Socket tolerance coupon.** Print a strip of holes from rod Ø + 0.1 to + 0.4 mm in 0.05 mm steps; pick the fit that holds without force.
3. **FSR under a printed pad.** Log raw values (light touch to firm press) for 3 people, 60 s each. We need a clean, repeatable 0–1 range per finger.
4. **Vibration through the cup.** Can a 10 mm coin motor be felt clearly through the dome in a 150 ms buzz, without rattling?
5. **Seat connector.** Lift and replace a cup 200 times; check for dropouts.

Keep every raw log; they become the project dataset.

## 6. Parts to order (quantities include spares)

| Part | Needed | Order |
|---|---|---|
| ESP32 boards with ≥5 ADC pins (cups) | 3 | 5 |
| ESP32 dev board (table) | 1 | 2 |
| FSR, small round (~12 mm) | 15 | 25 |
| WS2812B pixels (single boards or 60/m strip) | 15 cup + 43 table | 100 |
| NeoPixel 7-pixel jewel | 4 | 6 |
| 10 mm coin vibration motor | 3 | 6 |
| Clear acrylic rod Ø3 mm (thanh mica tròn đặc) | 15 short | 2 m |
| Clear acrylic rod Ø4 / 5 / 6 mm | 14 / 10 / 6 | 3 m / 3 m / 2 m |
| Clear acrylic rod Ø8 mm (vessels) and Ø12 mm (core) | — | 1 m / 0.5 m |
| 5 mm frosted acrylic sheet (lid) | Ø26 cm | 2 lids |
| Magnetic pogo connectors, 4-pin | 3 pairs | 6 pairs |
| 5 V 4 A supply, inline fuse, level shifter (74AHCT125) | 1 | 2 |
| Black PETG + white/translucent PLA or PETG | — | 1 kg each |
| 18 mm ply for the tabletop | Ø100 cm | 1 sheet |

## 7. Fixed interfaces

- Each cup reports five calibrated pressures, 0 to 1, thumb to little finger. Firmware will send `/cup id p1 p2 p3 p4 p5 element r g b`. **This replaces the July `/cup id pressure bpm confidence ...` contract.** The engine and firmware rewrite is in progress on the software side.
- Table controller to hub and TouchDesigner: port 9000. Hub to sound (Patrick): port 9001. Message list is on the design page under "Sound brief for Patrick".
- Keep a `RAW_LOG` serial mode on every board for calibration.

## 8. Proposed schedule to 30 November

| Week of | Goal |
|---|---|
| 27 Oct | Bench tests 1–5; order parts |
| 3 Nov | One cup working end to end; light box lid + baffle + plate prototype |
| 10 Nov | Three cups; tabletop cut with seats, vessel grooves, rebate |
| 17 Nov | Integration: cups → table → light box; first three-person sessions |
| 24 Nov | Endurance runs (2+ hours), fixes, documentation shoot |

## 9. Open questions for you

- Seat connector: magnetic pogo, or something more robust?
- One controller per cup over UART, or a simpler design with all FSRs wired into the table? (The first keeps cups standalone; the second is fewer boards.)
- Drum: printed segments or bent ply?
- Anything here you'd build differently. Please say so before ordering.
