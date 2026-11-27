# Bench test for the nest (run from Thonny with sh1106.py on the board).
# 1 multiplexer found  2 a screen on each channel 0-3  3 each screen shows its number and a frame
# 4 listens 10 s for the balls' ESP-NOW packets (switch the balls on)
import time, network, espnow
from machine import I2C, Pin

res = []
def check(name, ok, info=""):
    res.append(ok); print(("PASS " if ok else "FAIL ") + name, info)

i2c = I2C(0, sda=Pin(5), scl=Pin(6), freq=400_000)
found = i2c.scan()
check("multiplexer", 0x70 in found, "found %s (want 112 = 0x70)" % found)
if 0x70 in found:
    from sh1106 import SH1106
    names = ("dragon", "phoenix", "rhythm", "breath")
    for ch in range(4):
        i2c.writeto(0x70, bytes([1 << ch]))
        ok = 0x3C in i2c.scan()
        check("screen on channel %d" % ch, ok)
        if ok:
            s = SH1106(i2c, select=lambda ch=ch: i2c.writeto(0x70, bytes([1 << ch])))
            s.rect(0, 0, 128, 64, 1); s.text("%d %s" % (ch + 1, names[ch]), 8, 28, 1); s.show()
    print("Each screen: a full frame touching all four edges? (2-pixel shift = wrong chip)")

sta = network.WLAN(network.STA_IF); sta.active(True); sta.disconnect()
esp = espnow.ESPNow(); esp.active(True)
seen, t0 = {}, time.ticks_ms()
print("Listening 10 s for the balls ...")
while time.ticks_diff(time.ticks_ms(), t0) < 10000:
    host, msg = esp.recv(100)
    if msg and len(msg) == 24 and msg[0] == ord("B"):
        seen[msg[1]] = seen.get(msg[1], 0) + 1
check("dragon ball heard", seen.get(0, 0) > 100, "%d packets (want ~500)" % seen.get(0, 0))
check("phoenix ball heard", seen.get(1, 0) > 100, "%d packets (want ~500)" % seen.get(1, 0))
print("ALL PASS" if all(res) else "SOME FAILED")
