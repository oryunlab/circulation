# Minimal SH1106 128x64 I2C driver (MicroPython). 1.3" modules: 132-column RAM, 2-column offset.
import framebuf

class SH1106(framebuf.FrameBuffer):
    def __init__(self, i2c, addr=0x3C, select=None):
        self.i2c, self.addr, self.select = i2c, addr, select or (lambda: None)
        self.buf = bytearray(128 * 8)
        super().__init__(self.buf, 128, 64, framebuf.MONO_VLSB)
        self.select()
        for c in (0xAE, 0xD5, 0x80, 0xA8, 0x3F, 0xD3, 0x00, 0x40, 0xAD, 0x8B, 0xA1, 0xC8,
                  0xDA, 0x12, 0x81, 0x80, 0xD9, 0x22, 0xDB, 0x35, 0xA4, 0xA6, 0xAF):
            self.cmd(c)
        self.fill(0); self.show()

    def cmd(self, c):
        self.i2c.writeto(self.addr, bytes((0x00, c)))

    def contrast(self, v):
        self.select(); self.cmd(0x81); self.cmd(v)

    def show(self):
        self.select()
        mv = memoryview(self.buf)
        for page in range(8):
            self.cmd(0xB0 | page); self.cmd(0x02); self.cmd(0x10)
            self.i2c.writevto(self.addr, (b"\x40", mv[page * 128:(page + 1) * 128]))
