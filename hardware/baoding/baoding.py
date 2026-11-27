"""Circulation: two sensing Baoding balls + their nest. v0.1, 25 Nov 2026. Units: mm.

Two balls (dragon / phoenix), each with a XIAO ESP32-S3, a BNO055 (DFRobot SEN0374), a 402030
LiPo (~200-250 mAh) and a 12-LED ring (37 mm, same as the cups). The balls stream their motion
over ESP-NOW to the nest, which holds them and shows four 1.3" screens (via a TCA9548A).

BALL  Ø50, wall 2.5 (inside Ø45). Two parts with a 3-lug bayonet (25° clockwise twist, like a jar lid, with a click), seam at z = +8
      (above the equator, so the lower part takes the carrier from the top).
      lower   bigger part; band with 3 L-slots; 3 ribs carry the carrier at z = -4; USB-C port
              at the side (z = -6.6, counterbored so the plug reaches the recessed XIAO), TPU plug.
      cap     smaller dome; spigot with 3 lugs; ledge for the LED ring at z = 10.
      carrier disc Ø38.8 x 2. XIAO under it (upside down, USB-C to the port), battery on top,
              BNO055 on a bridge over the battery (chip about 4 mm above the ball centre, on
              the spin axis, so the ball's own spin barely shows in the readings).
NEST  170 x 90 x 30 pebble block. Two seats for the balls, four screen windows in front.
      Hollow, open below; a lid clips in. XIAO + TCA9548A inside; USB-C in at the back.

Part sizes marked TBC are from listings, not measured: XIAO 21 x 17.8, BNO055 board ~21 x 19,
LiPo 402030 = 4 x 20 x 30, OLED module ~35.5 x 33.8 with the glass offset. Measure first.
Print: ball parts pole-down with tree supports at the pole, 0.12 layers, translucent PETG; sand
and coat with the clear epoxy. Nest in white PLA/PETG, top up. Build: python baoding.py [outdir]
"""
import math, sys, os
from build123d import *

# ---------------- ball ----------------
R_O, WALL = 25.0, 2.5
R_I = R_O - WALL
SEAM = 8.0
SPIG_RI, SPIG_RO = 18.0, 19.6           # spigot on the cap
BAND_RI = 19.8                          # band on the lower part (0.2 radial clearance)
SPIG_Z0 = 2.6
LUG_Z0, LUG_H, LUG_RO, LUG_ARC = 3.6, 1.4, 20.9, 17
SLOT_Z0, SLOT_Z1, SLOT_RO = 3.4, 5.2, 21.2
ENTRY_ARC, TWIST = 20, 25
LUGS = [90, 210, 330]
CARRIER_R, CARRIER_Z0, CARRIER_T = 19.4, -4.0, 2.0
RIBS = [100, 180, 260]                  # 180 has the key tab
USB_Z, USB_W, USB_H = -6.6, 10.0, 4.2
RING_LEDGE_Z = 10.0
BIG = 200


def box_z(z0, z1):
    return Pos(0, 0, (z0 + z1) / 2) * Box(BIG, BIG, z1 - z0)


def sector(r0, r1, z0, z1, a0, arc):
    """annular sector: radius r0..r1, height z0..z1, from angle a0 (deg, anticlockwise from +X) through arc"""
    with BuildPart() as sp:
        with BuildSketch(Plane.XZ):
            with Locations(((r0 + r1) / 2, (z0 + z1) / 2)):
                Rectangle(r1 - r0, z1 - z0)
        revolve(axis=Axis.Z, revolution_arc=arc)
    part = sp.part
    # Plane.XZ's normal is -Y, so the revolve may run clockwise: find where it went and turn it to a0
    import math as _m
    mid = (r0 + r1) / 2
    probe = lambda d: part.is_inside(Vector(mid * _m.cos(_m.radians(d)), mid * _m.sin(_m.radians(d)), (z0 + z1) / 2))
    start = 0 if probe(min(arc, 359) / 2) else -arc
    return Rot(0, 0, a0 - start) * part


def ring(r0, r1, z0, z1):
    return sector(r0, r1, z0, z1, 0, 360)


def shell():
    return Sphere(R_O) - Sphere(R_I)


def ball_lower() -> Part:
    p = shell() & box_z(-BIG, SEAM)
    # band: material inside the wall between z 0.5 and the seam, 45° underneath so it prints
    with BuildPart() as b:
        with BuildSketch(Plane.XZ):
            Polygon((BAND_RI, SEAM), (BAND_RI, 3.0), (R_I - 0.1, 0.4), (R_I + 1.5, 0.4),
                    (R_I + 1.5, SEAM), align=None)
        revolve(axis=Axis.Z)
    p = p + (b.part & Sphere(R_O - 0.2))
    # L-slots: entry from the seam, then the twist channel
    for a in LUGS:
        p = p - sector(BAND_RI - 0.5, SLOT_RO, SLOT_Z0, SEAM + 1, a - ENTRY_ARC / 2, ENTRY_ARC)
        # channel runs clockwise from the entry (seen from the top), so the cap locks like a jar lid
        p = p - sector(BAND_RI - 0.5, SLOT_RO, SLOT_Z0, SLOT_Z1, a - TWIST - LUG_ARC / 2,
                       ENTRY_ARC / 2 + TWIST + LUG_ARC / 2)
        # small detent on the channel floor just before the locked position: the lug (0.2 above the
        # floor) rides over 0.35 of bump = a soft click that holds the cap against unscrewing
        p = p + sector(BAND_RI + 0.1, SLOT_RO, SLOT_Z0, SLOT_Z0 + 0.35, a - TWIST + LUG_ARC / 2 + 0.5, 1.2)
    # ribs for the carrier (+ key tab on one)
    for a in RIBS:
        rib = sector(CARRIER_R - 0.8, 23.5, CARRIER_Z0 - 2.0, CARRIER_Z0, a - 5, 10)
        p = p + rib
    p = p + sector(CARRIER_R - 0.6, R_I + 0.5, CARRIER_Z0, CARRIER_Z0 + 1.5, 180 - 4, 8)
    # USB-C port (XIAO connector faces +X)
    with BuildPart() as u:
        with BuildSketch(Plane.YZ.offset(16)):
            with Locations((0, USB_Z)):
                SlotOverall(USB_W, USB_H)
        extrude(amount=12)
    with BuildPart() as u2:                       # counterbore so the plug's moulding enters ~3 mm
        with BuildSketch(Plane.YZ.offset(R_O - 3.2)):
            with Locations((0, USB_Z)):
                SlotOverall(13.0, 7.5)
        extrude(amount=6)
    p = p - u.part - u2.part
    return p


def ball_cap() -> Part:
    p = shell() & box_z(SEAM, BIG)
    p = p + ring(SPIG_RI, SPIG_RO, SPIG_Z0, SEAM + 0.5)
    for a in LUGS:
        p = p + sector(SPIG_RO - 0.3, LUG_RO, LUG_Z0, LUG_Z0 + LUG_H, a - LUG_ARC / 2, LUG_ARC)
    # ledge for the LED ring (Ø37), 45° underside
    with BuildPart() as l:
        with BuildSketch(Plane.XZ):
            Polygon((17.4, RING_LEDGE_Z), (R_I + 1, RING_LEDGE_Z), (R_I + 1, SEAM + 0.5),
                    (20.4, SEAM + 0.5), align=None)
        revolve(axis=Axis.Z)
    p = p + (l.part & Sphere(R_O - 0.2))
    return p


def port_plug() -> Part:
    """TPU plug for the USB-C port: a stem in the slot and a cap flush with the ball's surface."""
    with BuildPart() as c:
        with BuildSketch(Plane.YZ.offset(R_O - 3.2)):
            with Locations((0, USB_Z)):
                SlotOverall(12.7, 7.2)
        extrude(amount=4)
    cap = c.part & Sphere(R_O)
    with BuildPart() as st:
        with BuildSketch(Plane.YZ.offset(R_O - 5.6)):
            with Locations((0, USB_Z)):
                SlotOverall(9.8, 4.0)
        extrude(amount=2.6)
    with BuildPart() as tab:                      # a fingernail notch to pull it out
        with BuildSketch(Plane.YZ.offset(R_O - 1.0)):
            with Locations((0, USB_Z + 2.6)):
                Rectangle(5, 1.2)
        extrude(amount=2)
    return cap + st.part - tab.part


def carrier() -> Part:
    z0 = CARRIER_Z0
    p = Pos(0, 0, z0) * Cylinder(CARRIER_R, CARRIER_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
    p = p - Pos(-CARRIER_R, 0, z0 + 1) * Box(4.4, 3.4, 4)               # key notch at 180°
    # bridge over the battery for the BNO055 (deck 18 x 24 at z 2.6..3.6)
    for y in (-11.5, 11.5):
        p = p + Pos(0, y, (z0 + CARRIER_T + 2.6) / 2) * Box(18, 1.6, 2.6 - (z0 + CARRIER_T))
    deck = Pos(0, 0, 3.1) * Box(18, 24.6, 1.0) - Pos(0, 0, 3.1) * Box(10, 12, 2)
    p = p + deck
    # rails under the disc that locate the XIAO (x -4..17, y ±8.9)
    for y in (-9.7, 9.7):
        p = p + Pos(6.5, y, z0 - 0.75) * Box(15, 1.2, 1.5)
    p = p + Pos(-4.8, 0, z0 - 0.75) * Box(1.2, 12, 1.5)
    # wire holes
    for x, y in ((-12, 14), (-12, -14), (14, -12.5)):
        p = p - Pos(x, y, z0 + 1) * Cylinder(2.0, 4)
    return p


# ---------------- nest ----------------
NL, NW, NH = 170, 90, 30
SEAT_X, SEAT_Y, SEAT_DEPTH, SEAT_R = 42, 20, 12, 25.6
SCR_PITCH, SCR_Y = 39, -24
SCR_WIN = (30.5, 15.5)                  # active area 29.4 x 14.7 (TBC)
SCR_PCB = (36.5, 34.5)                  # module 35.5 x 33.8 (TBC)
SCR_WIN_DY = 2.5                        # glass sits above the PCB centre (pins at the top edge, TBC)
TOP = 2.2


def nest() -> Part:
    with BuildPart() as n:
        Box(NL, NW, NH, align=(Align.CENTER, Align.CENTER, Align.MIN))
        fillet(n.edges().filter_by(Axis.Z), 22)
        fillet(n.edges().group_by(Axis.Z)[-1], 8)
    p = n.part
    for sx in (-SEAT_X, SEAT_X):
        p = p - Pos(sx, SEAT_Y, NH + SEAT_R - SEAT_DEPTH) * Sphere(SEAT_R)
    # cavity (open below), keeping walls 3 and material under the seats
    cav = Pos(0, 0, 0) * Box(NL - 6, NW - 6, NH - 16, align=(Align.CENTER, Align.CENTER, Align.MIN))
    with BuildPart() as c:
        add(cav)
        fillet(c.edges().filter_by(Axis.Z), 19)
    p = p - Pos(0, 0, -1) * c.part
    xs = [(i - 1.5) * SCR_PITCH for i in range(4)]
    for x in xs:
        p = p - Pos(x, SCR_Y, (NH - 16 - 1 + NH - TOP) / 2) * Box(*SCR_PCB, NH - TOP - (NH - 16 - 1))
        win = Pos(x, SCR_Y + SCR_WIN_DY, NH - TOP / 2) * Box(*SCR_WIN, TOP + 2)
        p = p - win
    # USB-C cable in at the back + lid ledge
    p = p - Pos(0, NW / 2, 7) * Box(14, 12, 8)
    return p


def nest_lid() -> Part:
    with BuildPart() as l:
        with BuildSketch():
            RectangleRounded(NL - 6.4, NW - 6.4, 18.8)
        extrude(amount=2.5)
    p = l.part
    with BuildPart() as k:
        with BuildSketch(Plane.XY.offset(2.5)):
            RectangleRounded(NL - 6.4, NW - 6.4, 18.8)
            RectangleRounded(NL - 10.4, NW - 10.4, 16.8, mode=Mode.SUBTRACT)
        extrude(amount=4)
    return Pos(0, 0, -2.5) * (p + k.part)


def check(lower, cap, car):
    from build123d import Solid
    ok = True
    def vol(x): return sum(s.volume for s in x.solids())
    for name, a, b in (("cap/lower", cap, lower), ("carrier/lower", car, lower), ("carrier/cap", car, cap)):
        v = vol(a & b)
        print(f"overlap {name}: {v:.2f} mm3"); ok &= v < 0.5
    # the parts' interior envelopes
    def inside(pt): return math.dist(pt, (0, 0, 0)) < R_I
    pts = {"XIAO pcb corner": (17, 8.9, -5.0), "XIAO shield corner": (17, 8.9, -8.2),
           "USB-C tip": (17.6, 4.5, -8.2), "battery corner": (15, 10, 2.0),
           "BNO board corner": (10.5, 9.5, 4.8), "LED ring top edge": (18.5, 0, 11.6)}
    for k, p in pts.items():
        clr = R_I - math.dist(p, (0, 0, 0)); print(f"{k}: clearance to wall {clr:.2f}"); ok &= clr > 0.3
    # through the band opening
    for k, r in (("carrier", CARRIER_R), ("XIAO corner", math.hypot(17, 8.9)), ("battery", math.hypot(15, 10))):
        print(f"{k} radius {r:.2f} vs band opening {BAND_RI}"); ok &= r < BAND_RI - 0.2
    print("CHECKS", "OK" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out, exist_ok=True)
    lo, cp, ca, pl = ball_lower(), ball_cap(), carrier(), port_plug()
    ne, li = nest(), nest_lid()
    for name, part in (("ball_lower", lo), ("ball_cap", cp), ("ball_carrier", ca), ("ball_port_plug", pl), ("nest", ne), ("nest_lid", li)):
        export_step(part, f"{out}/baoding_{name}.step"); export_stl(part, f"{out}/baoding_{name}.stl")
        bb = part.bounding_box(); print(f"{name}: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f}  vol {part.volume/1000:.1f} cm3")
    shell_g = (lo.volume + cp.volume + ca.volume) / 1000 * 1.27
    print(f"printed ball mass ~{shell_g:.0f} g (PETG) + electronics ~15 g")
    check(lo, cp, ca)
