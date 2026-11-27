# Circulation Baoding ball v0.1 (XIAO ESP32-S3 + BNO055 + 12-LED ring + LiPo). Save as main.py.
# Set BALL_ID: 0 = dragon (low tone), 1 = phoenix (high tone).
# Sends its motion 50 times a second to the nest over ESP-NOW; the nest does the analysis and
# answers with the element and state, which the ball shows on its ring.
# Light: resting purple breath (as the cups); turning = the element colour, brighter with speed;
# a soft chase runs round the ring at the ball's own turning rate. Cap 30% (76/255), as the cups.
# Sleep: still for 60 s -> deep sleep; the BNO055 wakes it when picked up (INT on D1).
# Ring power: v0.1 wires the ring to 3V3 (it draws ~10 mA even dark, so a sleeping ball lasts ~1 day).
# v0.2 adds a P-MOSFET on the ring's +: set RING_SWITCH = True and sleep draws only the XIAO + BNO055.
# Not yet tested on hardware.
import network, espnow, time, math, struct, machine, neopixel, esp32
from machine import Pin, I2C
from bno055 import BNO055

BALL_ID = 0
LED_PIN, NUM_LEDS = 1, 12          # D0
RING_SWITCH = False                # v0.2 wiring: ring + through a P-MOSFET (AO3401) gated by D2
RING_EN_PIN = 3                    # D2: low = ring on, high = off (100k pull-up to 3V3 keeps it off)
INT_PIN = 2                        # D1, BNO055 INT
SDA, SCL = 5, 6                    # D4, D5
CAP = 0.30
SLEEP_AFTER_S = 60
ELEMENTS = [(0, 255, 70), (255, 15, 0), (255, 180, 0), (255, 255, 255), (0, 30, 255)]  # as the cups
IDLE = (150, 0, 255)

if RING_SWITCH:
    ring_en = Pin(RING_EN_PIN, Pin.OUT, value=0, hold=False)   # ring power on
_strip0 = neopixel.NeoPixel(Pin(LED_PIN, Pin.OUT), NUM_LEDS)
_strip0.fill((0, 0, 0)); _strip0.write()           # lights off at the first line
strip = _strip0

i2c = I2C(0, sda=Pin(SDA), scl=Pin(SCL), freq=100_000, timeout=200_000)
imu = BNO055(i2c)

sta = network.WLAN(network.STA_IF); sta.active(True); sta.disconnect()
esp = espnow.ESPNow(); esp.active(True)
BROADCAST = b"\xff" * 6
esp.add_peer(BROADCAST)


def lim(c, k):
    m = max(c) or 1
    s = min(k, 1.0) * CAP * 255 / m
    return (int(c[0] * s), int(c[1] * s), int(c[2] * s))


element, state, rpm = 2, "rest", 0
seq = 0
t0 = time.ticks_ms()
last_move = t0
spin_phase = 0.0
print("Baoding ball", BALL_ID, "| channel", sta.config("channel"))

while True:
    now = time.ticks_ms()
    try:
        q, a, g = imu.raw()
    except OSError:
        time.sleep_ms(5); continue
    seq = (seq + 1) & 0xFFFF
    esp.send(BROADCAST, struct.pack("<BBH10h", ord("B"), BALL_ID, seq, *q, *a, *g), False)

    # hear the nest: b"N<el>,<state>,<rpm>"
    while True:
        host, msg = esp.recv(0)
        if not msg:
            break
        if msg[:1] == b"N":
            try:
                p = msg[1:].decode().split(",")
                element, state, rpm = int(p[0]) % 5, p[1], int(p[2])
            except (ValueError, IndexError):
                pass

    moving = abs(a[0]) + abs(a[1]) + abs(a[2]) > 40 or abs(g[2]) > 160   # 0.4 m/s2 or 10 dps
    if moving:
        last_move = now
    t = time.ticks_diff(now, t0) / 1000
    if state in ("turning", "unsettled") and time.ticks_diff(now, last_move) < 3000:
        spin_phase += (g[2] / 16) / 360 * NUM_LEDS * 0.02          # follow the ball's own spin
        level = 0.35 + 0.65 * min(1.0, abs(rpm) / 120)
        col = ELEMENTS[element]
        for i in range(NUM_LEDS):
            d = (i - spin_phase) % NUM_LEDS
            k = 0.45 + 0.55 * max(0.0, 1 - min(d, NUM_LEDS - d) / 3)
            strip[i] = lim(col, level * k)
    else:
        b = 0.5 - 0.5 * math.cos(2 * math.pi * t / 10)              # 6 breaths a minute
        strip.fill(lim(IDLE, 0.08 + 0.25 * b))
    strip.write()

    if time.ticks_diff(now, last_move) > SLEEP_AFTER_S * 1000:
        strip.fill((0, 0, 0)); strip.write()
        if RING_SWITCH:                                           # cut the ring's ~10 mA idle draw
            Pin(LED_PIN, Pin.OUT, value=0)                        # data low so it can't back-power the ring
            Pin(RING_EN_PIN, Pin.OUT, value=1, hold=True)         # gate high = off, held through sleep
        imu.arm_motion_wake()
        esp32.wake_on_ext0(Pin(INT_PIN, Pin.IN), esp32.WAKEUP_ANY_HIGH)
        machine.deepsleep()
    time.sleep_ms(max(0, 20 - time.ticks_diff(time.ticks_ms(), now)))
