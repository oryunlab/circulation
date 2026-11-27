"""Blender (workbench) preview: nest with two balls + one ball exploded.
blender -b -P render_baoding.py -- <dir with STLs> out.png [iso|top]"""
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
D, OUT = a[0], a[1]; VIEW = a[2] if len(a) > 2 else "iso"
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
def mat(n, c):
    m = bpy.data.materials.new(n); m.diffuse_color = (*c, 1); return m
NEST, BALL, BALL2, CAR = mat("n", (.93, .92, .89)), mat("b", (.86, .80, .95)), mat("b2", (.95, .88, .80)), mat("c", (.55, .55, .58))
PCB, BAT, LED, BNO, SCR, FELT = (mat("p", (.15, .35, .2)), mat("bt", (.75, .7, .35)), mat("l", (.6, .3, .85)),
                                  mat("s", (.2, .3, .6)), mat("sc", (.05, .05, .07)), mat("f", (.12, .12, .14)))
def imp(name, loc, m, rot=(0, 0, 0)):
    bpy.ops.wm.stl_import(filepath=f"{D}/baoding_{name}.stl"); o = bpy.context.selected_objects[0]
    o.location = loc; o.rotation_euler = rot; o.data.materials.append(m)
    bpy.context.view_layer.objects.active = o; bpy.ops.object.shade_auto_smooth(angle=math.radians(35)); return o
def box(size, loc, m):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object
    o.scale = size; o.data.materials.append(m); return o
def torus(R, r, loc, m):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=loc); o = bpy.context.object
    o.data.materials.append(m); return o
box((420, 260, 2), (40, 10, -1), FELT)
imp("nest", (0, 0, 0), NEST)
H = 30 + 25.6 - 12 - 0.6
for sx, m in ((-42, BALL), (42, BALL2)):
    imp("ball_lower", (sx, 20, H), m); imp("ball_cap", (sx, 20, H), m)
for i in range(4):   # screens
    box((29.4, 14.7, .4), ((i - 1.5) * 39, -24 + 2.5, 30.05), SCR)
# exploded ball at the right
ex, ey = 150, -5
imp("ball_lower", (ex, ey, 25), BALL)
imp("ball_carrier", (ex, ey, 25 + 30), CAR)
box((21, 17.8, 4.2), (ex + 6.5, ey, 25 + 30 - 4 - 2.1), PCB)          # XIAO (under the carrier)
box((30, 20, 4), (ex, ey, 25 + 30 + 9), BAT)                          # LiPo (slides under the bridge)
box((21, 19, 1.6), (ex, ey, 25 + 30 + 20), BNO)                       # BNO055 on the deck
torus(15.2, 3.2, (ex, ey, 25 + 30 + 34), LED)                         # LED ring
imp("ball_cap", (ex, ey, 25 + 72), BALL)
imp("ball_port_plug", (ex + 14, ey, 25), mat("tpu", (.3, .3, .32)))
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.clip_end = 20000
if VIEW == "ball":                       # close-up of the exploded ball only
    cam.data.ortho_scale = 150; tgt = Vector((ex, ey, 62)); cam.location = tgt + Vector((420, -900, 300))
elif VIEW == "top":
    cam.data.ortho_scale = 250; tgt = Vector((0, 0, 30)); cam.location = tgt + Vector((0, -1, 1000))
else:
    cam.data.ortho_scale = 380; tgt = Vector((45, 0, 45)); cam.location = tgt + Vector((420, -900, 520))
d = bpy.data.objects.new("t", None); sc.collection.objects.link(d); d.location = tgt
c = cam.constraints.new("TRACK_TO"); c.target = d; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading
sh.light = "STUDIO"; sh.color_type = "MATERIAL"; sh.show_cavity = True; sh.show_object_outline = True
sh.show_shadows = True; sh.shadow_intensity = .3
sc.render.resolution_x, sc.render.resolution_y = {"iso": (1800, 1100), "ball": (900, 1200)}.get(VIEW, (1400, 900))
sc.view_settings.view_transform = 'Standard'
sc.world = bpy.data.worlds.new("w"); sc.world.color = (1, 1, 1); sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
