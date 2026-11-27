# Baoding analysis: shared by nest_main.py (on the XIAO) and sim_baoding.py (on a computer).
# Each ball sends its orientation (quaternion), linear acceleration and gyro in its own body frame.
# The ball's centre circles the palm; its linear acceleration points to the circle's centre, so in
# the world frame the angle of the horizontal acceleration turns once per orbit. That angle gives
# turns, direction and rhythm without knowing which way the ball faces (IMUPLUS has no compass,
# so each ball's 'north' is arbitrary; only changes in angle are used).
import math

TWO_PI = 2 * math.pi
ELEMENTS = ("Wood", "Fire", "Earth", "Metal", "Water")     # generating cycle
MOVE_MIN = 0.15        # m/s2 of horizontal acc below which the orbit angle is not trusted
HOLD_S = 0.6           # a weak moment shorter than this keeps the count going
REST_S = 3.0           # still this long = resting
ALPHA = 0.2            # low-pass on the horizontal acc (at 50 Hz, about 1.8 Hz)


def rotate(q, v):
    """rotate body vector v into the world frame with unit quaternion q = (w, x, y, z)"""
    w, x, y, z = q
    vx, vy, vz = v
    # t = 2 * cross(q.xyz, v); v' = v + w t + cross(q.xyz, t)
    tx, ty, tz = 2 * (y * vz - z * vy), 2 * (z * vx - x * vz), 2 * (x * vy - y * vx)
    return (vx + w * tx + y * tz - z * ty, vy + w * ty + z * tx - x * tz, vz + w * tz + x * ty - y * tx)


def wrap(a):
    while a > math.pi:
        a -= TWO_PI
    while a <= -math.pi:
        a += TWO_PI
    return a


class Ball:
    def __init__(self, name, trace_len=40):
        self.name = name
        self.ax = self.ay = 0.0
        self.theta = None          # current orbit angle (rad)
        self.phi = 0.0             # unwrapped angle travelled (rad, + = anticlockwise seen from above)
        self.mark = 0.0            # phi at the last whole turn
        self.t_mark = None
        self.periods = []          # seconds per turn, recent
        self.rate = 0.0            # turns per second, signed, smoothed
        self.spin = 0.0            # own spin about the vertical, dps
        self.t_last = None
        self.t_move = None
        self.trace = []            # recent (x, y) on the unit circle, scaled by effort
        self.trace_len = trace_len
        self.turned = 0            # whole turns this session (signed)
        self.above = 0
        self.last_step = 0

    def update(self, t, q, lia, gyr):
        dt = 0.02 if self.t_last is None else max(1e-3, t - self.t_last)
        self.t_last = t
        wa = rotate(q, lia)
        self.ax += ALPHA * (wa[0] - self.ax)
        self.ay += ALPHA * (wa[1] - self.ay)
        self.spin = rotate(q, gyr)[2]
        mag = math.sqrt(self.ax * self.ax + self.ay * self.ay)
        if mag < MOVE_MIN:
            self.above = 0
            if self.t_move is None or t - self.t_move > HOLD_S:
                self.rate *= 0.95
                self.theta = None
            return
        self.above += 1
        if self.above < 4:                      # tremor spikes are single samples; turning is not
            return
        gap = 0 if self.t_move is None else t - self.t_move
        self.t_move = t
        th = math.atan2(self.ay, self.ax)
        if self.theta is not None and gap < 0.3:
            d = wrap(th - self.theta)
            self.phi += d
            self.rate += 0.08 * (d / dt / TWO_PI - self.rate)
        self.theta = th
        if self.t_mark is None:
            self.t_mark, self.mark = t, self.phi
        if abs(self.phi - self.mark) >= TWO_PI:
            step = 1 if self.phi > self.mark else -1
            if step != self.last_step:           # turned the other way: start the rhythm again
                self.periods = []
            self.last_step = step
            self.periods = (self.periods + [t - self.t_mark])[-6:]
            self.mark += step * TWO_PI
            self.t_mark = t
            self.turned += step
        # the ball sits opposite the acceleration (which points to the orbit centre)
        k = min(1.0, mag / 2.0)
        self.trace = (self.trace + [(-math.cos(th) * (0.6 + 0.4 * k), -math.sin(th) * (0.6 + 0.4 * k))])[-self.trace_len:]

    def resting(self, t):
        return self.t_move is None or t - self.t_move > REST_S

    def evenness(self):
        """1 = every turn takes the same time; 0 = very uneven. Needs 3 turns."""
        p = self.periods[-4:]
        if len(p) < 3:
            return None
        m = sum(p) / len(p)
        sd = math.sqrt(sum((x - m) ** 2 for x in p) / len(p))
        return max(0.0, min(1.0, 1 - 4 * sd / m))

    def rpm(self):
        # from the last whole turns when they are recent (steadier), else the running estimate
        p = self.periods[-3:]
        if p and self.t_last is not None and self.t_mark is not None and abs(self.rate) > 0.1 \
                and self.t_last - self.t_mark < 1.5 * p[-1]:
            return (60 if self.rate > 0 else -60) * len(p) / sum(p)
        return self.rate * 60

    def direction(self):
        """'CW' / 'CCW' seen from above (palm up), or None"""
        if abs(self.rate) < 0.1:
            return None
        return "CCW" if self.rate > 0 else "CW"


class Pair:
    def __init__(self):
        self.balls = (Ball("dragon"), Ball("phoenix"))
        self.element = 2           # start on Earth (the centre)
        self._last = 0

    def update(self, i, t, q, lia, gyr):
        self.balls[i].update(t, q, lia, gyr)
        # one full turn of the pair = one step round the generating cycle
        n = max(self.balls, key=lambda b: abs(b.turned)).turned
        if n != self._last:
            self.element = (self.element + (n - self._last)) % 5
            self._last = n

    def in_step(self, t):
        """both balls turning the same way at about the same rate (they share one palm)"""
        a, b = self.balls
        if a.resting(t) or b.resting(t) or abs(a.rate) < 0.1 or abs(b.rate) < 0.1:
            return False
        return (a.rate > 0) == (b.rate > 0) and abs(abs(a.rate) - abs(b.rate)) < 0.25 * max(abs(a.rate), abs(b.rate))

    def state(self, t):
        a, b = self.balls
        if a.resting(t) and b.resting(t):
            return "rest"
        if a.resting(t) or b.resting(t):
            return "one"            # one ball put down or dropped
        return "turning" if self.in_step(t) else "unsettled"
