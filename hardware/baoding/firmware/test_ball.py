# Bench test for one ball (run from Thonny with bno055.py on the board). Prints PASS/FAIL per check.
# 1 I2C scan  2 BNO055 chip + mode  3 live motion for 10 s (turn it in your hand)  4 LED ring
import time
from machine import I2C, Pin
import neopixel

res = []
def check(name, ok, info=""):
    res.append(ok); print(("PASS " if ok else "FAIL ") + name, info)

i2c = I2C(0, sda=Pin(5), scl=Pin(6), freq=100_000, timeout=200_000)
found = i2c.scan()
check("I2C scan", 0x28 in found, "found %s (want 40 = 0x28)" % found)
if 0x28 in found:
    from bno055 import BNO055
    imu = BNO055(i2c)
    print("Turn the sensor in your hand for 10 s ...")
    qs, n_err, t0 = [], 0, time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), t0) < 10000:
        try:
            q, a, g = imu.raw(); qs.append(q)
        except OSError:
            n_err += 1
        time.sleep_ms(20)
    check("reads without bus errors", n_err == 0, "%d errors in %d reads" % (n_err, len(qs) + n_err))
    moved = len(set(qs)) > len(qs) // 2
    check("orientation changes while moving", moved, "%d distinct of %d" % (len(set(qs)), len(qs)))
    norms = [sum((c / 16384) ** 2 for c in q) ** 0.5 for q in qs[-20:]] or [0]
    check("quaternion is unit length", all(0.95 < x < 1.05 for x in norms), "%.3f..%.3f" % (min(norms), max(norms)))
    print("calibration (sys, gyro, acc, mag):", imu.calibration())
ring = neopixel.NeoPixel(Pin(1, Pin.OUT), 12)
for i in range(12):
    ring.fill((0, 0, 0)); ring[i] = (40, 0, 76); ring.write(); time.sleep_ms(120)
ring.fill((0, 0, 0)); ring.write()
print("LED ring: did each of the 12 lights come on in turn? (check by eye)")
print("ALL PASS" if all(res) else "SOME FAILED")
