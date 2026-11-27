"""Baoding balls v0.1: two A3 drawing sheets (ball, nest). python baoding_drawing.py out.pdf"""
import sys, math, base64, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "baoding"))
from draw import *
from build123d import Face, Plane, Rot, Pos
import baoding as m

HERE = pathlib.Path(__file__).resolve().parent
BAO = HERE.parent / "baoding"
PURPLE, PURPLE_F = "#7a4fb5", "#efe7f8"
DATE = "25 Nov 2026"


def wire_pts(w, n=24):
    ps = []
    for e in (w.order_edges() if hasattr(w, "order_edges") else w.edges()):
        k_ = 2 if "LINE" in str(e.geom_type) else max(n, int(e.length / 0.6))
        seg = [e @ (i / k_) for i in range(k_ + 1)]
        if ps and (seg[0] - ps[-1]).length > (seg[-1] - ps[-1]).length: seg = seg[::-1]
        ps += seg
    return ps


def xz_path(fc, sx, sy, k):        # section on the XZ plane: sheet x = X, sheet y = -Z
    return " ".join("M" + " L".join(f"{sx + p.X * k:.3f},{sy - p.Z * k:.3f}" for p in wire_pts(w)) + "Z"
                    for w in [fc.outer_wire()] + list(fc.inner_wires()))


def xy_path(fc, sx, sy, k):        # plan: sheet x = X, sheet y = -Y
    return " ".join("M" + " L".join(f"{sx + p.X * k:.3f},{sy - p.Y * k:.3f}" for p in wire_pts(w)) + "Z"
                    for w in [fc.outer_wire()] + list(fc.inner_wires()))


def yz_path(fc, sx, sy, k):
    return " ".join("M" + " L".join(f"{sx + p.Y * k:.3f},{sy - p.Z * k:.3f}" for p in wire_pts(w)) + "Z"
                    for w in [fc.outer_wire()] + list(fc.inner_wires()))


def cut(part, plane):
    return part.intersect(Face.make_rect(600, 600, plane)).faces()


def img(s, path, x, y, w, h):
    b = base64.b64encode(pathlib.Path(path).read_bytes()).decode()
    s.add(f'<image x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid meet" href="data:image/png;base64,{b}"/>')


lo, cp, ca, pl = m.ball_lower(), m.ball_cap(), m.carrier(), m.port_plug()
cpL = Rot(0, 0, -m.TWIST) * cp            # cap in its locked position
sheets = []

# ======================= sheet 1: the ball =======================
s = Sheet(); sheets.append(s)
s.frame("Baoding ball v0.1 (x2: dragon, phoenix)", "Lower, cap, carrier, plug", "CIRC-BB-01", "2:1", sheet="1/2", rev="A", date=DATE)

# --- Section A-A (XZ plane, through the USB port), 2:1 ---
k, ox, oy = 2.0, 150, 128
s.view_title(60, 40, "SECTION A-A", "2:1 · through the USB-C port, cap locked")
for i, (part, col) in enumerate(((lo, "#888"), (cpL, "#888"), (ca, "#bbb"))):
    for j, fc in enumerate(cut(part, Plane.XZ)):
        s.hatch(xz_path(fc, ox, oy, k), f"a{i}_{j}", 0.9, col)
for j, fc in enumerate(cut(pl, Plane.XZ)):
    s.path(xz_path(fc, ox, oy, k), THIN, "#333", fill="#555")
# parts (outlines, phantom)
def box(x0, x1, z0, z1, label, col=MUTE, lx=None, ly=None, side=1):
    s.rect(ox + x0 * k, oy - z1 * k, (x1 - x0) * k, (z1 - z0) * k, THIN, col, dash="1.2 0.8")
for x0, x1, z0, z1 in ((-4, 17, -5, -4), (-1, 14, -8.2, -5)):          # XIAO pcb + shield/USB-C
    box(x0, x1, z0, z1, "")
box(-15, 15, -2, 2, "")                                                  # LiPo
box(-10.5, 10.5, 3.6, 5.2, "")                                           # BNO055
for sx_ in (-1, 1):
    s.rect(ox + sx_ * 11.5 * k if sx_ > 0 else ox - 18.5 * k, oy - 11.6 * k, 7 * k, 1.6 * k, THIN, PURPLE, fill=PURPLE_F)
s.centre(ox, oy, 27 * k)
s.leader(ox + 6 * k, oy + 6.6 * k, ox + 31 * k, oy + 21 * k, "XIAO ESP32-S3 (upside down)")
s.leader(ox - 8 * k, oy, ox - 31 * k, oy + 15 * k, "LiPo 402030 under the bridge")
s.leader(ox - 6 * k, oy - 4.4 * k, ox - 31 * k, oy - 14 * k, "BNO055 on the bridge deck (chip ~4 above centre)")
s.leader(ox - 15 * k, oy - 11.6 * k, ox - 31 * k, oy - 26 * k, "12-LED ring Ø37 on the cap ledge")
s.leader(ox + 24.6 * k, oy + 6.6 * k, ox + 31 * k, oy + 12 * k, "TPU port plug")
s.leader(ox - 20.5 * k, oy - 4.3 * k, ox - 31 * k, oy - 2 * k, "lug in its channel (locked)")
s.leader(ox + 18 * k, oy + 5 * k, ox + 31 * k, oy + 2 * k, "carrier rib (3x)")
s.vdim(ox + 25 * k, oy - 25 * k, oy + 25 * k, ox + 28 * k, "Ø50")
s.vdim(ox - 25 * k, oy - m.SEAM * k, oy + 25 * k, ox - 29 * k, "33 (seam at +8)")
s.hdim(ox - m.R_I * k, ox + m.R_I * k, oy, oy - 31 * k, "Ø45 inside (wall 2.5)")

# --- Section B-B: plan at z = 4.3 through the lugs, 2:1 ---
k2, bx, by = 2.0, 296, 128
s.view_title(246, 40, "SECTION B-B", "2:1 · plan at z +4.3, through the lugs (cap locked)")
for i, (part, col) in enumerate(((lo, "#888"), (cpL, "#bbb"))):
    for j, fc in enumerate(cut(part, Plane.XY.offset(4.3))):
        s.hatch(xy_path(fc, bx, by, k2), f"b{i}_{j}", 0.9, col)
s.centre(bx, by, 27 * k2)
s.diam(bx, by, m.BAND_RI * k2, 120, "band Ø39.6 (opening)", out=14)
s.diam(bx, by, m.SPIG_RO * k2, 300, "spigot Ø39.2 (cap)", out=16)
a = math.radians(90 - m.TWIST)
s.leader(bx + 20.2 * k2 * math.cos(a), by - 20.2 * k2 * math.sin(a), bx - 4 * k2, by - 36 * k2, "3 lugs, 17° wide, locked 25° clockwise")
s.text(bx - 55, by + 64, "Entry slots 20° at 90°/210°/330°; lugs drop in, turn 25° clockwise (seen from the top).", 2.4, col=MUTE)
s.text(bx - 55, by + 68, "A 0.35 detent on each channel floor gives a light drag over the last 15°; the end wall stops it.", 2.4, col=MUTE)

# --- exploded render ---
img(s, BAO / "baoding_ball_exploded.png", 352, 22, 56, 75)
s.text(380, 101, "Exploded view", 2.2, "middle", col=MUTE)

# --- notes ---
notes = [
    "PARTS PER BALL",
    "1  Lower: translucent PETG, pole down, tree supports from the plate, 0.12 layers",
    "2  Cap: translucent PETG, pole down, tree supports; lugs and spigot must print clean",
    "3  Carrier: PETG, flat side down, no supports",
    "4  Port plug: TPU 85-95A, cap down",
    "5  Bought: XIAO ESP32-S3, DFRobot BNO055 (SEN0374), LiPo 402030 with protection,",
    "    NeoPixel ring 12 / Ø37 (as the cups), 3-pin micro plug for the ring",
    "",
    "FIT (from the model, check on the first print)",
    "Twist lock radial clearance 0.2; lug to channel 0.2 above and below",
    "Tightest: XIAO shield 1.6 to the wall; LED ring 0.7 to the cap",
    "Everything inside passes the band opening Ø39.6",
    "",
    "TBC: measure the real BNO055 board, LiPo and XIAO before printing (sizes from listings).",
    "Finish: sand 400-1000, then a thin coat of clear epoxy after the ball is tested.",
    "Mass: printed ~30 g + parts ~15 g. Battery ~2-3 h with lights.",
]
s.lines(28, 205, notes, 2.45, 1.5)

# ======================= sheet 2: the nest =======================
ne, li = m.nest(), m.nest_lid()
s = Sheet(); sheets.append(s)
s.frame("Baoding ball nest v0.1", "Nest + lid", "CIRC-BB-02", "1:1", sheet="2/2", rev="A", date=DATE)
k, px, py = 1.0, 125, 92
s.view_title(28, 36, "PLAN", "1:1 · seats behind, screens in front")
for j, fc in enumerate(cut(ne, Plane.XY.offset(m.NH - 0.2))):
    s.path(xy_path(fc, px, py, k), LINE, fill="#fff")
for sx_ in (-m.SEAT_X, m.SEAT_X):
    rr = math.sqrt(m.SEAT_R ** 2 - (m.SEAT_R - m.SEAT_DEPTH) ** 2)
    s.circle(px + sx_ * k, py - m.SEAT_Y * k, rr * k, LINE)
    s.circle(px + sx_ * k, py - m.SEAT_Y * k, 25 * k, HAIR, PURPLE, dash="2 1")
    s.centre(px + sx_ * k, py - m.SEAT_Y * k, 28 * k)
labels = ["1 dragon path", "2 phoenix path", "3 rhythm", "4 breath"]
for i in range(4):
    x = (i - 1.5) * m.SCR_PITCH
    s.rect(px + (x - m.SCR_PCB[0] / 2) * k, py - (m.SCR_Y + m.SCR_PCB[1] / 2) * k, m.SCR_PCB[0] * k, m.SCR_PCB[1] * k, HAIR, MUTE, dash="1.5 1")
    s.text(px + x * k, py - (m.SCR_Y - 12) * k, labels[i], 2.3, "middle", col=MUTE)
s.hdim(px - m.NL / 2 * k, px + m.NL / 2 * k, py + m.NW / 2 * k, py + (m.NW / 2 + 10) * k, "170")
s.vdim(px + m.NL / 2 * k, py - m.NW / 2 * k, py + m.NW / 2 * k, px + (m.NL / 2 + 10) * k, "90")
s.hdim(px - m.SEAT_X * k, px + m.SEAT_X * k, py - m.SEAT_Y * k, py - (m.NW / 2 + 8) * k, "84 (seat centres)")
s.leader(px + m.SEAT_X * k + 17, py - m.SEAT_Y * k - 10, px + (m.NL / 2 + 8) * k, py - 40, "seat Ø43.2 at the top, 12 deep (ball Ø50 dashed)")
s.leader(px + 1.5 * m.SCR_PITCH * k + 15, py - (m.SCR_Y + m.SCR_WIN_DY) * k, px + (m.NL / 2 + 8) * k, py + 34, "window 30.5 x 15.5; pocket 36.5 x 34.5 from below")

# front section through the screens (XZ at y = SCR_Y)
k, fx, fy = 1.0, 125, 222
s.view_title(28, 168, "SECTION C-C", "1:1 · through the screens")
for j, fc in enumerate(cut(Pos(0, -m.SCR_Y, 0) * ne, Plane.XZ)):
    s.hatch(xz_path(fc, fx, fy, k), f"c{j}", 1.0)
for j, fc in enumerate(cut(Pos(0, -m.SCR_Y, 0) * li, Plane.XZ)):
    s.hatch(xz_path(fc, fx, fy, k), f"cl{j}", 1.0, "#bbb")
s.vdim(fx + m.NL / 2 * k, fy, fy - m.NH * k, fx + (m.NL / 2 + 10) * k, "30")
s.leader(fx - 1.5 * m.SCR_PITCH * k, fy - (m.NH - 3) * k, fx - 30, fy - 40, "screen pocket, glass up to the 2.2 skin")
s.leader(fx + 60, fy + 2, fx + 70, fy + 16, "lid clips in from below (lip 4)")

# side section through a seat (YZ at x = SEAT_X)
k, sx0, sy0 = 1.0, 330, 222
s.view_title(262, 150, "SECTION D-D", "1:1 · through a seat")
for j, fc in enumerate(cut(Pos(-m.SEAT_X, 0, 0) * ne, Plane.YZ)):
    s.hatch(yz_path(fc, sx0, sy0, k), f"d{j}", 1.0)
s.circle(sx0 + m.SEAT_Y * k, sy0 - (m.NH + m.SEAT_R - m.SEAT_DEPTH - 0.6) * k, 25 * k, THIN, PURPLE, dash="2 1")
s.text(sx0 + m.SEAT_Y * k, sy0 - 74, "ball Ø50", 2.3, "middle", col=PURPLE)

notes = [
    "NEST",
    "White PLA or PETG, matte. Print upside down (top on the plate), no supports.",
    "Lid: flat side down. Four felt pads under the lid.",
    "Inside: XIAO ESP32-S3 + TCA9548A (0x70) on D4/D5; screens on channels 0-3 (all 0x3C).",
    "USB-C in at the back (14 x 8 opening): power + data to the laptop for the visual.",
    "Screens: 1.3\" SH1106 128 x 64, glass held to the window, hot glue on the board edge only.",
    "TBC: screen module size and where its glass sits; check one before printing.",
]
s.lines(262, 70, notes, 2.45, 1.5)

out = sys.argv[1] if len(sys.argv) > 1 else str(HERE / "Circulation_baoding_balls_v0.1_CIRC-BB-01-02_25Nov2026.pdf")
save(sheets, out, "Baoding balls CIRC-BB"); print(out)
