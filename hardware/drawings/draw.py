"""Tiny SVG drafting kit: sheets in mm, dimensions, title block. Used by the drawing scripts."""
import math, html
LINE, THIN, HAIR = 0.5, 0.25, 0.18
INK, MUTE, CUT, FILL = "#111", "#666", "#c33", "#e8e4dc"
FONT = "Helvetica Neue, Helvetica, Arial, sans-serif"


class Sheet:
    def __init__(self, w=420, h=297):
        self.w, self.h, self.o = w, h, []

    def add(self, s): self.o.append(s)

    # --- primitives (sheet mm) ---
    def line(self, x1, y1, x2, y2, sw=LINE, col=INK, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" stroke="{col}" stroke-width="{sw}"{d} stroke-linecap="round"/>')

    def circle(self, cx, cy, r, sw=LINE, col=INK, fill="none", dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<circle cx="{cx:.3f}" cy="{cy:.3f}" r="{r:.3f}" stroke="{col}" stroke-width="{sw}" fill="{fill}"{d}/>')

    def rect(self, x, y, w, h, sw=LINE, col=INK, fill="none", rx=0, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" rx="{rx}" stroke="{col}" stroke-width="{sw}" fill="{fill}"{d}/>')

    def poly(self, pts, sw=LINE, col=INK, fill="none", closed=True, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        tag = "polygon" if closed else "polyline"
        self.add(f'<{tag} points="{" ".join(f"{x:.3f},{y:.3f}" for x, y in pts)}" stroke="{col}" stroke-width="{sw}" fill="{fill}"{d} stroke-linejoin="round"/>')

    def path(self, d, sw=LINE, col=INK, fill="none", dash=None):
        dd = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<path d="{d}" stroke="{col}" stroke-width="{sw}" fill="{fill}"{dd} stroke-linejoin="round"/>')

    def text(self, x, y, s, size=2.8, anchor="start", weight=400, col=INK, rot=0, italic=False):
        tr = f' transform="rotate({rot} {x:.3f} {y:.3f})"' if rot else ""
        st = ' font-style="italic"' if italic else ""
        self.add(f'<text x="{x:.3f}" y="{y:.3f}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" fill="{col}"{st}{tr}>{html.escape(s)}</text>')

    def lines(self, x, y, rows, size=2.6, lh=1.45, col=INK, weight=400):
        for i, r in enumerate(rows):
            w = 700 if r.startswith("**") else weight
            self.text(x, y + i * size * lh, r.strip("*"), size, col=col, weight=w)

    def image(self, x, y, w, h, href):
        self.add(f'<image x="{x}" y="{y}" width="{w}" height="{h}" href="{href}" preserveAspectRatio="xMidYMid meet"/>')

    # --- drafting ---
    def arrow(self, x, y, ang, size=2.2):
        a1, a2 = ang + math.radians(160), ang - math.radians(160)
        self.poly([(x, y), (x + size * math.cos(a1), y + size * math.sin(a1)), (x + size * math.cos(a2), y + size * math.sin(a2))], sw=0.1, fill=INK)

    def dim(self, p1, p2, off, label, size=2.6, ext=1.5):
        """Aligned dimension between sheet points p1,p2, dimension line offset by `off` (mm, left-normal)."""
        (x1, y1), (x2, y2) = p1, p2
        L = math.hypot(x2 - x1, y2 - y1); ux, uy = (x2 - x1) / L, (y2 - y1) / L
        nx, ny = -uy, ux
        a1 = (x1 + nx * off, y1 + ny * off); a2 = (x2 + nx * off, y2 + ny * off)
        sgn = 1 if off >= 0 else -1
        self.line(x1 + nx * sgn * 0.8, y1 + ny * sgn * 0.8, a1[0] + nx * sgn * ext, a1[1] + ny * sgn * ext, HAIR, MUTE)
        self.line(x2 + nx * sgn * 0.8, y2 + ny * sgn * 0.8, a2[0] + nx * sgn * ext, a2[1] + ny * sgn * ext, HAIR, MUTE)
        ang = math.atan2(uy, ux)
        if L < 7:   # outside arrows
            self.line(a1[0] - ux * 5, a1[1] - uy * 5, a2[0] + ux * 5, a2[1] + uy * 5, THIN)
            self.arrow(*a1, ang); self.arrow(*a2, ang + math.pi)
        else:
            self.line(*a1, *a2, THIN); self.arrow(*a1, ang + math.pi); self.arrow(*a2, ang)
        mx, my = (a1[0] + a2[0]) / 2, (a1[1] + a2[1]) / 2
        deg = math.degrees(ang)
        if deg > 90 or deg <= -90: deg += 180
        tx, ty = mx + nx * sgn * 1.0, my + ny * sgn * 1.0
        # text sits on the outer side of the dim line
        if abs(deg) < 1: ty = my - 1.0 if sgn * ny <= 0 or True else my + size
        if L < 7 and abs(deg) < 1: tx = a2[0] + 6
        self.text(tx, ty, label, size, "middle" if not (L < 7 and abs(deg) < 1) else "start", rot=deg if abs(deg) > 1 else 0)

    def hdim(self, x1, x2, y, at, label, **k):   # horizontal: features at y, dim line at `at`
        self.dim((x1, y), (x2, y), -(at - y), label, **k) if at < y else self._hdim_below(x1, x2, y, at, label, **k)

    def _hdim_below(self, x1, x2, y, at, label, size=2.6):
        self.line(x1, y + 0.8, x1, at + 1.5, HAIR, MUTE); self.line(x2, y + 0.8, x2, at + 1.5, HAIR, MUTE)
        L = abs(x2 - x1)
        if L < 7:
            self.line(min(x1, x2) - 5, at, max(x1, x2) + 5, at, THIN); self.arrow(min(x1, x2), at, 0); self.arrow(max(x1, x2), at, math.pi)
            self.text(max(x1, x2) + 6, at + 1, label, size)
        else:
            self.line(x1, at, x2, at, THIN); self.arrow(x1, at, math.pi); self.arrow(x2, at, 0)
            self.text((x1 + x2) / 2, at + size + 0.6, label, size, "middle")

    def vdim(self, x, y1, y2, at, label, size=2.6):
        side = 1 if at > x else -1
        self.line(x + side * 0.8, y1, at + side * 1.5, y1, HAIR, MUTE); self.line(x + side * 0.8, y2, at + side * 1.5, y2, HAIR, MUTE)
        L = abs(y2 - y1); lo, hi = min(y1, y2), max(y1, y2)
        if L < 7:
            self.line(at, lo - 5, at, hi + 5, THIN); self.arrow(at, lo, math.pi / 2); self.arrow(at, hi, -math.pi / 2)
            self.text(at + side * 1.2, hi + 5 + 2.6 if side > 0 else hi + 5 + 2.6, label, size, "start" if side > 0 else "end")
        else:
            self.line(at, lo, at, hi, THIN); self.arrow(at, lo, -math.pi / 2); self.arrow(at, hi, math.pi / 2)
            self.text(at + side * 1.2, (lo + hi) / 2 + 1, label, size, "start" if side > 0 else "end")

    def hdim_top(self, x1, x2, y, at, label, size=2.6):
        self.line(x1, y - 0.8, x1, at - 1.5, HAIR, MUTE); self.line(x2, y - 0.8, x2, at - 1.5, HAIR, MUTE)
        L = abs(x2 - x1); lo, hi = min(x1, x2), max(x1, x2)
        if L < 7:
            self.line(lo - 5, at, hi + 5, at, THIN); self.arrow(lo, at, 0); self.arrow(hi, at, math.pi)
            self.text(hi + 6, at + 1, label, size)
        else:
            self.line(lo, at, hi, at, THIN); self.arrow(lo, at, math.pi); self.arrow(hi, at, 0)
            self.text((lo + hi) / 2, at - 0.9, label, size, "middle")

    def leader(self, x, y, tx, ty, label, size=2.6, dot=False):
        if dot: self.circle(x, y, 0.5, 0.1, fill=INK)
        else: self.arrow(x, y, math.atan2(y - ty, x - tx))
        self.line(x, y, tx, ty, THIN)
        end = tx + (8 if tx >= x else -8)
        self.line(tx, ty, end, ty, THIN)
        self.text(end + (0.8 if tx >= x else -0.8), ty + 0.9, label, size, "start" if tx >= x else "end")

    def diam(self, cx, cy, r, ang_deg, label, out=12, size=2.6):
        a = math.radians(ang_deg)
        px, py = cx + r * math.cos(a), cy - r * math.sin(a)
        tx, ty = cx + (r + out) * math.cos(a), cy - (r + out) * math.sin(a)
        self.leader(px, py, tx, ty, label, size)

    def centre(self, cx, cy, r):
        self.line(cx - r, cy, cx + r, cy, HAIR, MUTE, "4 1 1 1"); self.line(cx, cy - r, cx, cy + r, HAIR, MUTE, "4 1 1 1")

    def hatch_clip(self, cid, d):
        self.add(f'<clipPath id="{cid}"><path d="{d}"/></clipPath>')

    def hatch(self, d, cid, spacing=1.2, col="#888"):
        self.hatch_clip(cid, d)
        xs = []
        self.add(f'<g clip-path="url(#{cid})">')
        for i in range(-400, 800):
            x = i * spacing
            self.add(f'<line x1="{x}" y1="0" x2="{x - 300}" y2="300" stroke="{col}" stroke-width="0.12"/>')
        self.add("</g>")
        self.path(d, LINE)

    def view_title(self, x, y, title, scale):
        self.text(x, y, title, 3.4, weight=700)
        self.text(x, y + 4.2, scale, 2.5, col=MUTE)

    def frame(self, title, part, dwg_no, scale, sheet="1/1", rev="A", date="23 Nov 2026", notes_tbc=None):
        W, H = self.w, self.h
        self.rect(10, 10, W - 20, H - 20, 0.6)
        x0, y0, bw, bh = W - 10 - 160, H - 10 - 34, 160, 34
        self.rect(x0, y0, bw, bh, 0.5, fill="#fff")
        self.line(x0, y0 + 12, x0 + bw, y0 + 12, THIN)
        self.text(x0 + 3, y0 + 5.5, "CIRCULATION · Bin Youn, RMIT Vietnam · SCD Seed Funding 2026", 2.3, col=MUTE)
        self.text(x0 + 3, y0 + 10.2, title, 3.6, weight=700)
        cells = [("PART", part), ("DWG NO.", dwg_no), ("SCALE", scale), ("UNITS", "mm"), ("REV", rev), ("DATE", date), ("SHEET", sheet), ("FOR", "MLF Production")]
        cw = bw / 4
        for i, (k, v) in enumerate(cells):
            cx, cy = x0 + (i % 4) * cw, y0 + 12 + (i // 4) * 11
            self.rect(cx, cy, cw, 11, THIN)
            self.text(cx + 1.5, cy + 3.4, k, 1.9, col=MUTE)
            self.text(cx + 1.5, cy + 8.6, v, 2.6 if len(v) < 22 else 2.1, weight=600)
        self.text(14, H - 13, "Do not scale from a print unless the 50 mm check bar below measures 50 mm.  Third-angle projection.  General tolerance ±0.3 printed, ±0.5 cut.", 2.2, col=MUTE)
        self.line(14, H - 18.5, 64, H - 18.5, 0.6); self.line(14, H - 20, 14, H - 17, 0.4); self.line(64, H - 20, 64, H - 17, 0.4)
        self.text(66, H - 17.6, "50 mm", 2.0, col=MUTE)

    def svg(self):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}mm" height="{self.h}mm" viewBox="0 0 {self.w} {self.h}" '
                f'font-family="{FONT}">\n<rect width="{self.w}" height="{self.h}" fill="#fff"/>\n' + "\n".join(self.o) + "\n</svg>")


def save(sheets, out_pdf, title="drawing", page=(420, 297)):
    """Write one HTML with every sheet as an A3 landscape page, then print it to PDF with headless Edge/Chrome."""
    import subprocess, pathlib, os
    out_pdf = pathlib.Path(out_pdf)
    pw, ph = page
    page = ('<!doctype html><html><head><meta charset="utf-8"><title>%s</title><style>@page{size:%smm %smm;margin:0}'
            'html,body{margin:0;padding:0}svg{display:block;width:%smm;height:%smm;page-break-after:always}</style></head><body>%s</body></html>'
            % (html.escape(title), pw, ph, pw, ph, "".join(s.svg() for s in sheets)))
    h = out_pdf.with_suffix(".html"); h.write_text(page)
    for b in ("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"):
        if os.path.exists(b):
            subprocess.run([b, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={out_pdf}", h.resolve().as_uri()],
                           capture_output=True, timeout=120)
            break
    return out_pdf
