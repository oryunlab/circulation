"""Simulate two Baoding balls and run the nest's analysis on them (computer only).
python3 sim_baoding.py [out_dir]  ->  checks printed, screens_<t>.png + sim_timeline.png
Script: 0-3 s at rest | 3-15 s even, clockwise 0.8 turns/s | 15-21 s stumbling (uneven) |
21-31 s even, anticlockwise 1.2 turns/s | 31-36 s phoenix put down | 36-42 s both at rest.
Each ball has its own random 'north' (IMUPLUS, no compass), its own spin, hand tremor and noise."""
import math, random, sys, os
from baoding_core import Pair, ELEMENTS
import screens

random.seed(int(os.environ.get("SEED", 7)))
OUT = sys.argv[1] if len(sys.argv) > 1 else "."
DT = 0.02
R_ORBIT = 0.018                      # m, ball centre circle in the palm


def qmul(a, b):
    w1, x1, y1, z1 = a; w2, x2, y2, z2 = b
    return (w1*w2 - x1*x2 - y1*y2 - z1*z2, w1*x2 + x1*w2 + y1*z2 - z1*y2,
            w1*y2 - x1*z2 + y1*w2 + z1*x2, w1*z2 + x1*y2 - y1*x2 + z1*w2)


def qaxis(ax, ang):
    s = math.sin(ang / 2); return (math.cos(ang / 2), ax[0]*s, ax[1]*s, ax[2]*s)


def inv_rotate(q, v):
    w, x, y, z = q
    from baoding_core import rotate
    return rotate((w, -x, -y, -z), v)


def script(t):
    """(turns per second, signed: + = anticlockwise; phoenix on? ; jitter)"""
    if t < 3: return 0.0, True, 0
    if t < 15: return -0.8, True, 0.0
    if t < 21: return -0.8 * (1 + 0.45 * math.sin(2 * math.pi * 0.7 * t) + 0.25 * math.sin(5.3 * t)), True, 0.3
    if t < 31: return 1.2, True, 0.0
    if t < 36: return 1.2, False, 0.0
    return 0.0, False, 0


class FB:
    """stand-in for MicroPython's FrameBuffer, enough for screens.py"""
    def __init__(self):
        self.p = [[0] * 128 for _ in range(64)]
    def fill(self, c):
        for r in self.p: r[:] = [c] * 128
    def pixel(self, x, y, c):
        if 0 <= x < 128 and 0 <= y < 64: self.p[y][x] = c
    def line(self, x0, y0, x1, y1, c):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            self.pixel(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n), c)
    def rect(self, x, y, w, h, c):
        self.line(x, y, x + w - 1, y, c); self.line(x, y + h - 1, x + w - 1, y + h - 1, c)
        self.line(x, y, x, y + h - 1, c); self.line(x + w - 1, y, x + w - 1, y + h - 1, c)
    def fill_rect(self, x, y, w, h, c):
        for j in range(h):
            for i in range(w): self.pixel(x + i, y + j, c)
    def text(self, s, x, y, c):
        self.texts = getattr(self, "texts", []) + [(s, x, y)]


def save_screens(fbs, path):
    from PIL import Image, ImageDraw, ImageFont
    S = 3; im = Image.new("RGB", (4 * 128 * S + 5 * 12, 64 * S + 24), (40, 40, 44)); d = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 8 * S - 4)
    except OSError:
        font = ImageFont.load_default()
    for k, fb in enumerate(fbs):
        ox, oy = 12 + k * (128 * S + 12), 12
        d.rectangle([ox, oy, ox + 128 * S - 1, oy + 64 * S - 1], fill=(0, 0, 0))
        for y in range(64):
            for x in range(128):
                if fb.p[y][x]:
                    d.rectangle([ox + x * S, oy + y * S, ox + x * S + S - 1, oy + y * S + S - 1], fill=(200, 225, 255))
        for s, x, y in getattr(fb, "texts", []):
            d.text((ox + x * S, oy + y * S - 2), s, font=font, fill=(200, 225, 255))
    im.save(path)


pair = Pair()
balls = []
for i in range(2):
    balls.append(dict(north=random.uniform(0, 2 * math.pi), spin=0.0, theta=math.pi * i, tilt=random.uniform(0, 0.25)))
log = []
snap_at = {9.0, 18.0, 27.0, 34.0, 40.0}
t = 0.0
while t < 42:
    f, phoenix_on, jit = script(t)
    for i, b in enumerate(balls):
        on = phoenix_on or i == 0
        w = 2 * math.pi * f if on else 0.0
        b["theta"] += w * DT
        b["spin"] += -2.2 * w * DT            # rolling: spins about its own vertical axis
        # world linear acc: centripetal toward the palm centre + hand tremor + jitter
        acc = (-R_ORBIT * w * w * math.cos(b["theta"]), -R_ORBIT * w * w * math.sin(b["theta"]), 0.0)
        trem = 0.12 + jit
        acc = (acc[0] + random.gauss(0, trem), acc[1] + random.gauss(0, trem), random.gauss(0, 0.1))
        # orientation = its arbitrary north, then its spin, slightly tilted in the hand
        q = qmul(qaxis((1, 0, 0), b["tilt"] * math.sin(0.5 * t + i)), qaxis((0, 0, 1), b["north"] + b["spin"]))
        n = math.sqrt(sum(c * c for c in q)); q = tuple(c / n for c in q)
        lia = inv_rotate(q, acc)
        gyr = inv_rotate(q, (0, 0, math.degrees(-2.2 * w)))
        # quantise as the BNO055 / the packet does
        q = tuple(round(c * 16384) / 16384 for c in q)
        lia = tuple(round(c * 100) / 100 for c in lia)
        gyr = tuple(round(c * 16) / 16 for c in gyr)
        pair.update(i, t, q, lia, gyr)
    if round(t / DT) % 5 == 0:
        a, b = pair.balls
        log.append((t, f, a.rpm(), b.rpm(), a.evenness(), pair.state(t), pair.element, a.turned, b.turned))
    if any(abs(t - s) < DT / 2 for s in snap_at):
        fbs = [FB() for _ in range(4)]
        screens.path(fbs[0], pair.balls[0], "dragon"); screens.path(fbs[1], pair.balls[1], "phoenix")
        screens.rhythm(fbs[2], pair, t); screens.breath(fbs[3], t)
        save_screens(fbs, os.path.join(OUT, "screens_%02ds.png" % round(t)))
    t += DT


def at(tt):
    return min(log, key=lambda r: abs(r[0] - tt))


ok = True
def check(name, cond, info):
    global ok
    print(("PASS " if cond else "FAIL ") + name + ": " + info); ok &= bool(cond)

r = at(14); check("even CW speed", abs(r[2] + 48) < 6, "dragon %.1f rpm (true -48)" % r[2])
check("even CW state", r[5] == "turning", r[5])
check("even CW evenness", r[4] is not None and r[4] > 0.8, "%s" % r[4])
r = at(20.5); check("stumble lowers evenness", r[4] is not None and r[4] < 0.7, "%s" % r[4])
r = at(30); check("CCW speed", abs(r[2] - 72) < 7, "dragon %.1f rpm (true +72)" % r[2])
check("CCW state", r[5] == "turning", r[5])
r = at(35); check("phoenix put down", r[5] == "one", r[5])
r = at(41.5); check("rest", r[5] == "rest", r[5])
print("turns (net, signed): dragon %d, phoenix %d (true about %+.1f / %+.1f)" % (log[-1][7], log[-1][8], -0.8 * 18 + 1.2 * 15, -0.8 * 18 + 1.2 * 10))

# timeline plot
try:
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    T = [r[0] for r in log]
    fig, ax = plt.subplots(3, 1, figsize=(11, 7), sharex=True)
    ax[0].plot(T, [r[1] * 60 for r in log], "k--", lw=1, label="true")
    ax[0].plot(T, [r[2] for r in log], label="dragon"); ax[0].plot(T, [r[3] for r in log], label="phoenix")
    ax[0].set_ylabel("rpm (+ = anticlockwise)"); ax[0].legend(loc="upper left", fontsize=8)
    ax[1].plot(T, [r[4] if r[4] is not None else float("nan") for r in log]); ax[1].set_ylabel("evenness"); ax[1].set_ylim(0, 1.05)
    st = {"rest": 0, "one": 1, "unsettled": 2, "turning": 3}
    ax[2].step(T, [st[r[5]] for r in log], where="post"); ax[2].set_yticks(range(4)); ax[2].set_yticklabels(list(st))
    ax2 = ax[2].twinx(); ax2.step(T, [r[6] for r in log], "r", where="post", alpha=.5); ax2.set_yticks(range(5)); ax2.set_yticklabels(ELEMENTS, fontsize=7)
    for a_ in ax:
        for x in (3, 15, 21, 31, 36): a_.axvline(x, color="0.8", lw=.8)
    ax[2].set_xlabel("s   |  rest | even CW 0.8/s | stumble | even CCW 1.2/s | one ball | rest")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "sim_timeline.png"), dpi=110)
except ImportError:
    print("(matplotlib not installed: no timeline plot)")
print("ALL PASS" if ok else "SOME FAILED")
