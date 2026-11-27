# What the four nest screens draw. fb: a MicroPython FrameBuffer (or the sim's stand-in).
import math
from baoding_core import ELEMENTS

W, H = 128, 64


def path(fb, ball, label):
    """screen 1 / 2: the circle this ball traces, newest points brightest (solid), older dotted"""
    fb.fill(0)
    cx, cy, r = 40, 32, 26
    for k in range(0, 360, 12):
        a = math.radians(k)
        fb.pixel(int(cx + r * math.cos(a)), int(cy + r * math.sin(a)), 1)
    n = len(ball.trace)
    for i in range(1, n):
        x0, y0 = ball.trace[i - 1]; x1, y1 = ball.trace[i]
        if i > n - 12 or i % 2:
            fb.line(int(cx + r * x0), int(cy - r * y0), int(cx + r * x1), int(cy - r * y1), 1)
    if n:
        x, y = ball.trace[-1]
        fb.fill_rect(int(cx + r * x) - 2, int(cy - r * y) - 2, 5, 5, 1)
    fb.text(label, 76, 4, 1)
    fb.text("%3d" % abs(round(ball.rpm())), 80, 24, 1); fb.text("rpm", 104, 24, 1)
    d = ball.direction()
    fb.text(d or "--", 84, 44, 1)


def rhythm(fb, pair, t):
    """screen 3: turns, evenness bar, element"""
    fb.fill(0)
    a, b = pair.balls
    turns = max(abs(a.turned), abs(b.turned))
    fb.text("turns", 4, 4, 1); fb.text("%d" % turns, 60, 4, 1)
    e = [x for x in (a.evenness(), b.evenness()) if x is not None]
    fb.text("even", 4, 22, 1)
    fb.rect(44, 22, 80, 8, 1)
    if e:
        fb.fill_rect(46, 24, int(76 * min(e)), 4, 1)
    fb.text(ELEMENTS[pair.element], 4, 42, 1)
    st = pair.state(t)
    fb.text({"rest": "resting", "one": "one ball", "turning": "in step", "unsettled": "settling"}[st], 60, 42, 1)


def breath(fb, t, period=10.0):
    """screen 4: the resting breath, 6 a minute, same as the cups"""
    fb.fill(0)
    s = 0.5 - 0.5 * math.cos(2 * math.pi * t / period)
    r = int(6 + 22 * s)
    cx, cy = 64, 30
    for k in range(0, 360, 4):
        a = math.radians(k)
        fb.pixel(int(cx + r * math.cos(a)), int(cy + r * math.sin(a)), 1)
    fb.text("in" if math.sin(2 * math.pi * t / period) > 0 else "out", 2, 54, 1)
