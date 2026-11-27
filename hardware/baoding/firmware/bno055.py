# Minimal BNO055 driver (MicroPython). Registers from the Bosch BNO055 datasheet.
# Run the I2C bus at 100 kHz with a long timeout: the BNO055 stretches the clock.
import time, struct

ADDR = 0x28
CHIP_ID, PAGE_ID = 0x00, 0x07
EUL, QUA, LIA, GYR = 0x1A, 0x20, 0x28, 0x14
CALIB_STAT, OPR_MODE, PWR_MODE, SYS_TRIGGER, UNIT_SEL = 0x35, 0x3D, 0x3E, 0x3F, 0x3B
# page 1 (interrupts)
INT_MSK, INT_EN, ACC_AM_THRES, ACC_INT_SETTINGS = 0x0F, 0x10, 0x11, 0x12
CONFIG, IMUPLUS, NDOF = 0x00, 0x08, 0x0C


class BNO055:
    def __init__(self, i2c, addr=ADDR, mode=IMUPLUS):
        self.i2c, self.addr = i2c, addr
        for _ in range(20):
            try:
                if self._r8(CHIP_ID) == 0xA0:
                    break
            except OSError:
                pass
            time.sleep_ms(50)
        else:
            raise OSError("BNO055 not found")
        self.mode(CONFIG)
        self._w8(SYS_TRIGGER, 0x20); time.sleep_ms(700)          # reset
        while True:
            try:
                if self._r8(CHIP_ID) == 0xA0:
                    break
            except OSError:
                pass
            time.sleep_ms(20)
        self._w8(PWR_MODE, 0x00); self._w8(PAGE_ID, 0)
        self._w8(UNIT_SEL, 0x00)      # m/s2, dps, degrees, Windows orientation
        self._w8(SYS_TRIGGER, 0x00)
        self.mode(mode)

    def _r8(self, reg):
        return self.i2c.readfrom_mem(self.addr, reg, 1)[0]

    def _w8(self, reg, v):
        self.i2c.writeto_mem(self.addr, reg, bytes([v])); time.sleep_ms(2)

    def mode(self, m):
        self._w8(OPR_MODE, m); time.sleep_ms(30)

    def quaternion(self):            # w, x, y, z
        return tuple(v / 16384 for v in struct.unpack("<hhhh", self.i2c.readfrom_mem(self.addr, QUA, 8)))

    def raw(self):
        """quaternion (int16 x4, 1/16384), linear acc (int16 x3, 1/100 m/s2), gyro (int16 x3, 1/16 dps)"""
        q = struct.unpack("<hhhh", self.i2c.readfrom_mem(self.addr, QUA, 8))
        a = struct.unpack("<hhh", self.i2c.readfrom_mem(self.addr, LIA, 6))
        g = struct.unpack("<hhh", self.i2c.readfrom_mem(self.addr, GYR, 6))
        return q, a, g

    def calibration(self):           # sys, gyro, acc, mag (0-3 each)
        c = self._r8(CALIB_STAT)
        return (c >> 6) & 3, (c >> 4) & 3, (c >> 2) & 3, c & 3

    def arm_motion_wake(self, threshold=4):
        """Any-motion interrupt on the INT pin (active high), for waking from deep sleep.
        Threshold in steps of the accel range (about 3.9 mg each at 2 g). Untested on hardware."""
        self.mode(CONFIG)
        self._w8(PAGE_ID, 1)
        self._w8(ACC_AM_THRES, threshold)
        self._w8(ACC_INT_SETTINGS, 0b00011100 | 0x01)   # x, y, z enabled; duration 2 samples
        self._w8(INT_MSK, 0x40)                          # ACC_AM to the INT pin
        self._w8(INT_EN, 0x40)                           # ACC_AM enabled
        self._w8(PAGE_ID, 0)
        self._w8(SYS_TRIGGER, 0x40)                      # clear any pending interrupt
        self.mode(IMUPLUS)
