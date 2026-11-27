# Baoding balls v0.1 (next version, not for 27 Nov)

Two sensing Baoding balls, dragon (low tone) and phoenix (high tone), and the nest that holds
them and shows four screens. Uses the 18 Nov Long Binh parts: 2 x BNO055 (DFRobot SEN0374),
4 x 1.3" OLED, 1 x TCA9548A. Status: CAD and firmware done, simulated; nothing printed or
tested on hardware yet.

## Files
| File | What |
|---|---|
| `baoding.py` | CAD (build123d): ball lower, cap, carrier, nest, nest lid. `python baoding.py .` builds STEP + STL and runs the fit checks |
| `baoding_*.step / .stl` | print files (ball lower, cap, carrier, port plug; nest, lid) |
| `../drawings/Circulation_baoding_balls_v0.1_CIRC-BB-01-02_25Nov2026.pdf` | 2 A3 sheets: ball sections A-A, B-B; nest plan + sections |
| `render_baoding.py` | Blender preview: `Blender -b -P render_baoding.py -- . baoding_preview.png iso` |
| `firmware/ball_main.py` | ball (save as `main.py`; set `BALL_ID` 0 or 1) + `bno055.py` |
| `firmware/nest_main.py` | nest (save as `main.py`) + `sh1106.py`, `baoding_core.py`, `screens.py` |
| `firmware/test_ball.py`, `test_nest.py` | bench tests (run from Thonny; print PASS/FAIL) |
| `firmware/sim_baoding.py` | runs the nest's analysis on two simulated balls: `python3 sim_baoding.py ../sim` |
| `sim/` | simulated screens at 9, 18, 27, 34, 40 s and the timeline |
| `visual/taiji_ink.html` | the taiji ink visual: open in Chrome/Edge. Sources: simulated balls, your hand (circle the mouse), or the nest over USB |

## Ball (Ø50, x2)
- Translucent PETG, wall 2.5. Two parts with a 3-lug bayonet (25° twist); seam at z +8.
- Inside, bottom to top: XIAO ESP32-S3 (upside down under the carrier, USB-C to the side port),
  carrier disc, LiPo 402030 (~200-250 mAh, slides under the bridge), BNO055 on the bridge
  (chip ~4 mm above the centre, on the spin axis), 12-LED ring (Ø37) glued on the ledge in the cap.
- Charging: open the side port's TPU plug, USB-C in (the XIAO charges the LiPo).
- Printed mass ~30 g + ~15 g parts. Traditional balls are heavier; add brass (not steel) later if
  the hand wants weight.
- Wiring: BNO055 SDA/SCL to D4/D5, INT to D1; ring DIN to D0; 3V3/GND; LiPo to the XIAO's
  BAT pads. The ring's 3 wires run down beside the bridge (use a small plug so the cap comes off).

## Nest (170 x 90 x 30)
- Two seats; four screen windows: dragon path, phoenix path, rhythm (turns, evenness, element,
  state), resting breath (6 a minute, as the cups).
- Inside: XIAO ESP32-S3 + TCA9548A on D4/D5; screens on mux channels 0-3 (all 0x3C).
  USB-C cable in at the back. Lid clips in from below.

## What the balls measure
The ball's centre circles the palm, so its linear acceleration points to the circle's centre.
Turning that into the world frame (BNO055 quaternion, IMUPLUS mode, no compass) gives an angle
that goes round once per orbit: turns, direction, rpm and evenness (how steady each turn is).
'In step' = both balls turning the same way at a similar rate. One full turn = one step round the
generating cycle (Wood > Fire > Earth > Metal > Water; the other way goes back).

## Simulation (25 Nov)
`sim_baoding.py`: rest, even clockwise 48 rpm, stumbling, even anticlockwise 72 rpm, one ball put
down, rest. Speeds within 1 rpm, states right, evenness ~0.9 when even. In 7 of 8 random runs
the stumble pulls evenness below 0.7; in one it read 0.74. Net turn counts within 1 turn.
Limits: needs a clear orbit (about 0.15 m/s2, i.e. ~0.5 turns/s or faster at an 18 mm circle);
very slow turning will read as rest. Tune `MOVE_MIN` on hardware.

## Before printing (TBC: measured from listings, not parts)
- XIAO 21 x 17.8; BNO055 board ~21 x 19 x 4 (and where the chip sits on it); LiPo 4 x 20 x 30;
  OLED module ~35.5 x 33.8 with the glass 2.5 mm above centre.
- First print: one lower + cap + carrier only, to test the bayonet (0.2 clearance) and the fit.

## Not yet done
- Hardware tests: BNO055 on the ESP32 bus (100 kHz, long timeout), motion wake, screens.
- Sound (dragon/phoenix tones through the centre speaker): the nest broadcasts `Q<rpm>,<dir>,<even>,<el>`
  but the centre doesn't use it yet.
- TPU port plug, brass weight, battery voltage readout.

## Taiji ink visual (25 Nov)
`visual/taiji_ink.html`, one file, no install. The two balls hold two brushes: dragon in ink,
phoenix in cinnabar. Their paths trade radius (one spirals out as the other spirals in), so the
strokes cross twice a turn like the two halves of the taiji. Faster = thinner stroke; the ink runs
dry over the turns (flying white) and refills when the balls rest (the brush is dipped); an uneven
hand wavers and splashes; turning the other way paints a grey wash. After 4 s at rest the scroll
is sealed (element character, turns, evenness, date); picking the balls up again moves it to the
row of past scrolls along the bottom (the room of rhythms) and starts a fresh one.
Keys: H hides the panel, F full screen. 'Save PNG' saves the scroll. URL options: `?theme=night`
(projection), `?speed=2`, `?prerun=40` (fast-forward the simulation), `?panel=0`.
The nest prints one JSON line every 50 ms on USB for the 'Nest (USB)' source (Web Serial, 115200).

## Changes later on 25 Nov
- Twist lock now turns clockwise (like a jar lid), 25°, with a light detent drag; end wall stops it.
- Fixed: the arc helper in `baoding.py` produced empty shapes, so the first build had no lugs, slots
  or ribs (the fit checks passed on nothing). Rebuilt; the lock path is now checked in the model
  (cap drops in only at the entry angle, locks at 25°, carrier sits on the ribs).
- TPU port plug part (`baoding_ball_port_plug`).
- Ring power switch (v0.2 wiring): AO3401 P-MOSFET on the ring's +, gate on D2 with 100k pull-up;
  set `RING_SWITCH = True` in `ball_main.py`. Cuts the ring's ~10 mA sleep drain.
- Visual: 'Taiji' path (each brush traces one fish; eyes added at the seal), chime duet
  (Sound button; dragon low, phoenix higher, on the element's tone each half turn), past scrolls kept
  in the browser between sessions ('Clear wall' empties it). URL: `?path=taiji`.
