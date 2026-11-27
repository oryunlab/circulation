# Circulation Baoding nest v0.1 (XIAO ESP32-S3 + TCA9548A + 4 x 1.3" SH1106 screens). Save as main.py
# together with sh1106.py, baoding_core.py and screens.py.
# Hears both balls (ESP-NOW), works out turns, direction, rpm, evenness and the element, draws the
# four screens and tells the balls what to show. Also broadcasts "Q<rpm>,<dir>,<even>,<el>" twice a
# second for the centre (not used by the centre yet), and prints one JSON line every 50 ms on USB
# for the taiji ink visual (visual/taiji_ink.html, 'Nest (USB)').
# Screens on mux channels 0-3: dragon path, phoenix path, rhythm, breath. Not yet tested on hardware.
import network, espnow, time, struct
from machine import Pin, I2C
from sh1106 import SH1106
from baoding_core import Pair
import screens

SDA, SCL = 5, 6                     # D4, D5
MUX = 0x70
i2c = I2C(0, sda=Pin(SDA), scl=Pin(SCL), freq=400_000)


def sel(ch):
    return lambda: i2c.writeto(MUX, bytes([1 << ch]))


oled = []
for ch in range(4):
    try:
        oled.append(SH1106(i2c, select=sel(ch)))
    except OSError:
        oled.append(None); print("no screen on channel", ch)

sta = network.WLAN(network.STA_IF); sta.active(True); sta.disconnect()
esp = espnow.ESPNow(); esp.active(True)
BROADCAST = b"\xff" * 6
esp.add_peer(BROADCAST)

pair = Pair()
t0 = time.ticks_ms()
turn = 0
last_tx = 0
last_usb = 0
print("Baoding nest | channel", sta.config("channel"))

while True:
    while True:
        host, msg = esp.recv(0)
        if not msg:
            break
        if len(msg) == 24 and msg[0] == ord("B"):
            _, bid, seq, qw, qx, qy, qz, ax, ay, az, gx, gy, gz = struct.unpack("<BBH10h", msg)
            t = time.ticks_diff(time.ticks_ms(), t0) / 1000
            pair.update(bid & 1, t, (qw / 16384, qx / 16384, qy / 16384, qz / 16384),
                        (ax / 100, ay / 100, az / 100), (gx / 16, gy / 16, gz / 16))
    now = time.ticks_ms()
    t = time.ticks_diff(now, t0) / 1000
    # one screen per pass keeps the radio loop quick (4 screens = ~10 updates a second each)
    fb = oled[turn]
    if fb:
        if turn == 0:
            screens.path(fb, pair.balls[0], "dragon")
        elif turn == 1:
            screens.path(fb, pair.balls[1], "phoenix")
        elif turn == 2:
            screens.rhythm(fb, pair, t)
        else:
            screens.breath(fb, t)
        try:
            fb.show()
        except OSError:
            pass
    turn = (turn + 1) % 4
    if time.ticks_diff(now, last_usb) > 50:       # to the taiji ink visual (USB serial, one JSON line)
        last_usb = now
        parts = []
        for bl in pair.balls:
            e = bl.evenness()
            parts.append("[%.3f,%.3f,%.2f,%d]" % (bl.phi, bl.rate, -1 if e is None else e, 1 if bl.resting(t) else 0))
        print('{"t":%.2f,"d":%s,"p":%s,"el":%d}' % (t, parts[0], parts[1], pair.element))
    if time.ticks_diff(now, last_tx) > 200:
        last_tx = now
        a, b = pair.balls
        rpm = int(max(abs(a.rpm()), abs(b.rpm())))
        esp.send(BROADCAST, b"N%d,%s,%d" % (pair.element, pair.state(t), rpm), False)
        if (now // 500) % 2 == 0:
            e = [x for x in (a.evenness(), b.evenness()) if x is not None]
            esp.send(BROADCAST, b"Q%d,%s,%d,%d" % (rpm, (a.direction() or "-"), int(100 * min(e)) if e else -1,
                                                    pair.element), False)
