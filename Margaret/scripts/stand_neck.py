"""Swan-neck display stand for Margaret (Revision 10): a thin bevelled oval base, ONE neck rising just ahead of the
ballast bulb's nose and leaning back 45 deg under the hull, and a fork head that cradles the hull bottom either side of
the fin root.  No pins, nothing enters the model.

* Fork: the head's top is the hull-bottom height field (the boat rests on two pads beside the fin and on the keel line
  just ahead of it), and a fin slot is cut through it: the fin's swept section (everything that passes on the way in)
  plus SLOT_CLEAR per side.  The slot's front end follows the fin's leading edge, so the closed front of the fork stops
  the boat going forward, and the fin in the slot stops it rolling.
* Lock: a small chock on the base sits CHOCK_CLEAR under the bulb's rising aft underside, so the boat cannot walk out
  aft: lift her LIFT mm, slide her aft, lift her off (audited: no hull/appendage vertex enters the stand on that path).
* Printable upright without supports: every downward face is <= 45-50 deg from vertical (audited).

Run: MARGARET_OUT=<v7 build dir> STAND_OUT=<dir> [DISPLAY_SAIL_JSON=<display_sail.json>]
     blender -b --factory-startup -P stand_neck.py
Writes Stand.stl (assembled boat coordinates, mm), Stand-bed.stl (placed on a 256 mm bed) and stand.json."""
import os, json, math, struct, re, bpy, bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

OUT, SOUT = os.environ["MARGARET_OUT"], os.environ["STAND_OUT"]
os.makedirs(SOUT, exist_ok=True)
HULL = ["Lower_blue", "Lower_white", "Lower_ink", "Upper_white", "Upper_ink", "Upper_teak"]
FIN = ["Fin_cap", "Ballast_cup"]
RUD = ["Rudder", "Rudder_ink"]
SLOT_CLEAR = 0.4            # fin to slot wall, per side
CHEEK_T = 2.4               # fork cheek thickness beside the slot
BULB_GAP = 2.5              # bulb flat above the base top
BASE_T, BASE_BEVEL, BASE_FOOT = 1.8, 0.8, 0.3
BASE_HW = 30.0              # base half-width (y)
BASE_MARGIN = 3.5           # base edge beyond the neck root fillet and the chock
NECK_GAP = 2.2              # neck rear face ahead of the bulb nose
NECK_T = 6.0                # neck fore-aft thickness where it stands vertical
NECK_T45 = 5.0              # neck thickness square to its 45 deg lean
NECK_HW = 2.6               # neck half-width (y)
LIP_X, LIP_D = -9.0, 1.5    # aft tip of the fork pads; pad depth there
FRONT_TOP_X = 9.5           # front face of the fork head
R_REAR, R_FRONT = 12.0, 18.0
FRONT_BLEND = 12.0          # smooth flare of the neck's front face into the head
ROOT_R = 2.5                # neck-to-base fillet radius
HEAD_R = 2.5                # plan corner radius of neck and head
SLIDE = 32.0                # lift-off path: up LIFT (set by the chock), aft SLIDE, then up
CHOCK_LOCK, CHOCK_CLEAR, CHOCK_LEN, CHOCK_HW = 1.6, 0.4, 5.0, 3.0
CHOCK_WRAP = 3.0            # saddle rises around the tail at most this far above the bulb flat
Z_TOP = -10.0               # neck stack top (above the hull bottom; trimmed by the height field)
OVERHANG_MAX = 50.0
PLA_STAND_G_PER_CM3 = 1.10  # thin, mostly-solid part: estimate until sliced
S2 = math.sqrt(2.0)


def load(names):
    verts, polys = [], []
    for n in names:
        p = os.path.join(OUT, n+".stl")
        if not os.path.exists(p):
            continue
        bpy.ops.wm.stl_import(filepath=p)
        ob = bpy.context.selected_objects[0]
        base = len(verts)
        verts += [ob.matrix_world @ v.co for v in ob.data.vertices]
        polys += [tuple(base+i for i in pl.vertices) for pl in ob.data.polygons]
        bpy.data.objects.remove(ob, do_unlink=True)
    return verts, polys


hv, hp = load(HULL)
fv, fp = load(FIN)
rv, rp = load(RUD)
cv, cpl = load(["Ballast_cup"])
fin = BVHTree.FromPolygons(fv, fp)
cup = BVHTree.FromPolygons(cv, cpl)
allt = BVHTree.FromPolygons(hv+fv, hp+[tuple(i+len(hv) for i in p) for p in fp])
z_flat = min(v.z for v in cv)
ZB = z_flat-BULB_GAP                                       # base top
Z_BED = ZB-BASE_T
BULB_NOSE_X = max(v.x for v in cv)
BULB_TAIL_X = min(v.x for v in cv)


# ---------------- tail chock (saddle) location; it sets the lift-off height ----------------
chock_ok = None
xsamp = np.arange(-49.0, -20.0, 0.1)


def bulb_bottom(x):
    zz = []
    for y in np.linspace(-CHOCK_HW, CHOCK_HW, 9):
        h = cup.ray_cast(Vector((x, y, -80.0)), Vector((0, 0, 1)))
        if h[0] is not None:
            zz.append(h[0].z)
    return min(zz) if zz else None


Z_CHOCK = z_flat+CHOCK_LOCK
XC1 = None
for x in xsamp[::-1]:
    zb = bulb_bottom(x)
    if zb is not None and zb >= Z_CHOCK+CHOCK_CLEAR:
        XC1 = float(x)
        break
XC0 = XC1-CHOCK_LEN
# chock: a saddle under the bulb's tail whose top follows the underside CHOCK_CLEAR below it
CG = 0.1
ER = CHOCK_CLEAR+0.05                                      # ball offset radius (true 3D clearance, not vertical)
ne = int(math.ceil(ER/CG))
cxs = np.arange(XC0-0.5, XC1+0.5+1e-9, CG)
cys = np.arange(-CHOCK_HW-0.5, CHOCK_HW+0.5+1e-9, CG)
exs = np.arange(cxs[0]-ne*CG, cxs[-1]+ne*CG+1e-9, CG)[:len(cxs)+2*ne]
eys = np.arange(cys[0]-ne*CG, cys[-1]+ne*CG+1e-9, CG)[:len(cys)+2*ne]
ZU = np.full((len(exs), len(eys)), z_flat+9.0)
for i, x in enumerate(exs):
    for j, y in enumerate(eys):
        h = cup.ray_cast(Vector((x, y, -80.0)), Vector((0, 0, 1)))
        if h[0] is not None:
            ZU[i, j] = h[0].z
CH = np.full((len(cxs), len(cys)), np.inf)
for di in range(-ne, ne+1):
    for dj in range(-ne, ne+1):
        d2 = (di*CG)**2+(dj*CG)**2
        if d2 > ER*ER:
            continue
        CH = np.minimum(CH, ZU[ne+di:ne+di+len(cxs), ne+dj:ne+dj+len(cys)]-math.sqrt(ER*ER-d2))
CH = np.minimum(CH, z_flat+CHOCK_WRAP)
CHOCK_TOP = float(CH.max())
LIFT = math.ceil((CHOCK_TOP-z_flat+0.7)*2)/2            # the bulb flat must clear the saddle's highest point


def smax(a, b, k):
    h = max(k-abs(a-b), 0.0)/k
    return max(a, b)+h*h*k/4


# ---------------- fin slot: swept fin section + clearance ----------------
Z_ROOT = -12.25                                            # below the hull bottom beside the fin (-12.22 lowest)
GX0, GX1, GDX = -32.0, 12.0, 0.1
GZ0, GDZ = -34.0, 0.1
gx = np.arange(GX0, GX1+1e-9, GDX)
gz = np.arange(GZ0, Z_ROOT+1e-9, GDZ)
hb = np.zeros((len(gz), len(gx)))
for j, z in enumerate(gz):
    for i, x in enumerate(gx):
        m = 0.0
        for s in (1, -1):
            h = fin.ray_cast(Vector((x, s*20.0, z)), Vector((0, -s, 0)))
            if h[0] is not None:
                m = max(m, abs(h[0].y))
        hb[j, i] = m
suf = np.maximum.accumulate(hb[:, ::-1], axis=1)[:, ::-1]  # everything ahead passes x on the way in (boat slides fwd)
nl = int(round(LIFT/GDZ))
nc = int(round(SLOT_CLEAR/GDZ))                            # vertical clearance under downward steps of the fin
lw = np.array([suf[max(0, j-nl):j+nc+1].max(axis=0) for j in range(len(gz))])   # boat carried LIFT higher on the way in
nk = int(round(SLOT_CLEAR/GDX))
hw = np.zeros_like(lw)
for d in range(-nk, nk+1):
    r = math.sqrt(max(0.0, SLOT_CLEAR**2-(d*GDX)**2))
    sh = np.roll(lw, -d, axis=1)
    if d > 0:
        sh[:, -d:] = 0
    elif d < 0:
        sh[:, :-d] = 0
    hw = np.maximum(hw, np.where(sh > 0, sh+r, 0.0))
x_end = np.array([gx[np.nonzero(row > 0)[0].max()] if (row > 0).any() else GX0 for row in hw])
HW_MAX = float(hw.max())
W_HEAD = HW_MAX+CHEEK_T


def slot_hw(z, x):
    j = min(len(gz)-1, max(0, int(round((z-GZ0)/GDZ))))
    return float(np.interp(x, gx, hw[j])), float(x_end[j])


# ---------------- neck + head profile (side view) ----------------
XR0 = BULB_NOSE_X+NECK_GAP
XF0 = XR0+NECK_T
lip_hits = [allt.ray_cast(Vector((LIP_X, y, -30.0)), Vector((0, 0, 1)))[0] for y in (W_HEAD-0.5, -(W_HEAD-0.5))]
Z_LIP = min(h.z for h in lip_hits if h is not None)-LIP_D
C_R = LIP_X+Z_LIP                                          # rear 45 deg line: x + z = C_R
C_F = C_R+NECK_T45*S2
Z_A = C_R-XR0+R_REAR*(1-S2)                                # rear arc start (vertical below)
Z_Bf = C_F-XF0+R_FRONT*(1-S2)


def x_rear(z):
    if z <= Z_A:
        xr = XR0
    elif z <= Z_A+R_REAR/S2:
        xr = XR0-R_REAR*(1-math.cos(math.asin((z-Z_A)/R_REAR)))
    else:
        xr = C_R-z
    return smax(xr, LIP_X, 1.5)


def x_front(z):
    if z <= Z_Bf:
        xf = XF0
    elif z <= Z_Bf+R_FRONT/S2:
        xf = XF0-R_FRONT*(1-math.cos(math.asin((z-Z_Bf)/R_FRONT)))
    else:
        xf = C_F-z
    return smax(xf, FRONT_TOP_X, FRONT_BLEND)


# crotch: lowest height of the unbroken run, from the root down, where the fin slot still reaches the head's rear face
crotch = Z_ROOT
for z in gz[::-1]:
    if slot_hw(z, 0.0)[1] < x_rear(z)-0.01:
        break
    crotch = float(z)
Z_W1 = crotch-0.6
Z_W0 = Z_W1-6.0


def width(z):
    if z >= Z_W1:
        return W_HEAD
    if z <= Z_W0:
        return NECK_HW
    t = (z-Z_W0)/(Z_W1-Z_W0)
    return NECK_HW+(W_HEAD-NECK_HW)*t*t*(3-2*t)


def flare(z):
    d = z-ZB
    if d <= 0:
        return ROOT_R
    if d >= ROOT_R:
        return 0.0
    return ROOT_R-math.sqrt(max(0.0, ROOT_R**2-(ROOT_R-d)**2))


def rrect(x0, x1, y0, y1, r, seg=10):
    r = max(0.05, min(r, (x1-x0)/2-0.01, (y1-y0)/2-0.01))
    pts = []
    for cx, cy, a0 in ((x1-r, y0+r, -90), (x1-r, y1-r, 0), (x0+r, y1-r, 90), (x0+r, y0+r, 180)):
        for k in range(seg+1):
            a = math.radians(a0+90*k/seg)
            pts.append((cx+r*math.cos(a), cy+r*math.sin(a)))
    return pts


def link(name, bm):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    return ob


def rings_solid(name, rings):
    bm = bmesh.new()
    R = [[bm.verts.new(p) for p in r] for r in rings]
    for r0, r1 in zip(R, R[1:]):
        L = len(r0)
        for j in range(L):
            bm.faces.new((r0[j], r0[(j+1) % L], r1[(j+1) % L], r1[j]))
    bm.faces.new(list(reversed(R[0]))); bm.faces.new(R[-1])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return link(name, bm)


def boolean(a, b, op):
    m = a.modifiers.new("b", "BOOLEAN"); m.operation = op; m.object = b; m.solver = "EXACT"
    me = bpy.data.meshes.new_from_object(a.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    a.modifiers.remove(m)
    old = a.data; a.data = me; bpy.data.meshes.remove(old)
    bpy.data.objects.remove(b, do_unlink=True)


def heightfield_cutter(name, xs, ys, Hm, ztop):
    """Closed solid between the height field Hm[i, j] (bottom) and the plane ztop over the xs x ys grid."""
    bm = bmesh.new()
    bot = [[bm.verts.new((x, y, Hm[i, j])) for j, y in enumerate(ys)] for i, x in enumerate(xs)]
    top = [[bm.verts.new((x, y, ztop)) for j, y in enumerate(ys)] for i, x in enumerate(xs)]
    nx, ny = len(xs), len(ys)
    for i in range(nx-1):
        for j in range(ny-1):
            bm.faces.new((bot[i][j], bot[i][j+1], bot[i+1][j+1], bot[i+1][j]))
            bm.faces.new((top[i][j], top[i+1][j], top[i+1][j+1], top[i][j+1]))
    loop = [(i, 0) for i in range(nx)]+[(nx-1, j) for j in range(1, ny)]+[(i, ny-1) for i in range(nx-2, -1, -1)] + \
        [(0, j) for j in range(ny-2, 0, -1)]
    for a, b in zip(loop, loop[1:]+loop[:1]):
        bm.faces.new((bot[a[0]][a[1]], bot[b[0]][b[1]], top[b[0]][b[1]], top[a[0]][a[1]]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return link(name, bm)


def volume(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    v = bm.calc_volume(signed=False); bm.free()
    return v


# neck + head: horizontal plan sections stacked in z
zs, z = [], ZB-0.6
while z < Z_TOP-1e-6:
    zs.append(z)
    z += 0.1 if z < ZB+ROOT_R+0.5 else 0.2
zs.append(Z_TOP)
rings = []
for z in zs:
    f = flare(z)
    W = width(z)+f
    rings.append([(x, y, z) for x, y in rrect(x_rear(z)-f, x_front(z)+f, -W, W, HEAD_R+f)])
neck = rings_solid("Stand", rings)
v_neck_raw = volume(neck)

# height-field cutter: the hull bottom (and anything of the boat) above the head is removed -> conforming pads
HX0, HX1, HY = LIP_X-3.0, FRONT_TOP_X+6.0, W_HEAD+ROOT_R+1.0
hxs = np.arange(HX0, HX1+1e-9, 0.2)
hys = np.arange(-HY, HY+1e-9, 0.2)
H = np.full((len(hxs), len(hys)), np.nan)
for i, x in enumerate(hxs):
    for j, y in enumerate(hys):
        h = allt.ray_cast(Vector((x, y, -30.0)), Vector((0, 0, 1)))
        if h[0] is not None and -12.8 <= h[0].z <= -10.5:
            H[i, j] = h[0].z
    ok = ~np.isnan(H[i])
    for j in np.nonzero(~ok)[0]:                           # inside the fin / socket: nearest valid |y| (slot cuts it)
        k = np.nonzero(ok)[0]
        H[i, j] = H[i, k[np.argmin(np.abs(k-j))]]
hcut = heightfield_cutter("HullCut", hxs, hys, H, -5.0)
boolean(neck, hcut, "DIFFERENCE")

# fin slot cutter: plan sections stacked in z, from below the crotch to above the head
NS = 160
slot_rings = []
zsl = [z for z in np.arange(crotch-3.0, Z_ROOT+1e-9, 0.2)]+[Z_ROOT+0.3, -8.0]
for z in zsl:
    zz = min(z, Z_ROOT)
    _, xe = slot_hw(zz, 0.0)
    xa = GX0+1.0
    side = []
    for k in range(NS):
        x = xa+(xe-xa)*math.sin(0.5*math.pi*k/NS)
        side.append((x, max(slot_hw(zz, x)[0], 0.02)))
    tip = (xe+0.01, 0.0)
    ring = [(x, y, z) for x, y in side]+[(tip[0], 0.0, z)]+[(x, -y, z) for x, y in reversed(side)]
    slot_rings.append(ring)
slot = rings_solid("Slot", slot_rings)
boolean(neck, slot, "DIFFERENCE")
v_head = volume(neck)

# base: bevelled ellipse
x_hi = XF0+ROOT_R+BASE_MARGIN
x_lo = XC0-BASE_MARGIN
XC, A = (x_lo+x_hi)/2, (x_hi-x_lo)/2


def ellipse(a, b, z, n=180):
    return [(XC+a*math.cos(2*math.pi*k/n), b*math.sin(2*math.pi*k/n), z) for k in range(n)]


base = rings_solid("Base", [ellipse(A-BASE_FOOT, BASE_HW-BASE_FOOT, Z_BED), ellipse(A, BASE_HW, Z_BED+BASE_FOOT),
                            ellipse(A, BASE_HW, ZB-BASE_BEVEL), ellipse(A-BASE_BEVEL, BASE_HW-BASE_BEVEL, ZB)])
chock = rings_solid("Chock", [[(x, y, z) for x, y in rrect(XC0, XC1, -CHOCK_HW, CHOCK_HW, 1.6)] for z in (ZB-0.6, CHOCK_TOP+1.0)])
boolean(chock, heightfield_cutter("ChockCut", cxs, cys, CH, -30.0), "DIFFERENCE")
v_base, v_chock = volume(base), volume(chock)
boolean(neck, base, "UNION")
boolean(neck, chock, "UNION")
stand = neck

bm = bmesh.new(); bm.from_mesh(stand.data)
bmesh.ops.triangulate(bm, faces=list(bm.faces))
nonman = sum(1 for e in bm.edges if not e.is_manifold)
vol = bm.calc_volume(signed=False)
lo = Vector([min(v.co[i] for v in bm.verts) for i in range(3)])
hi = Vector([max(v.co[i] for v in bm.verts) for i in range(3)])
tris = [tuple(v.co.copy() for v in f.verts) for f in bm.faces]
# printability: downward faces above the bed
over_area, over_max, down_area = 0.0, 0.0, 0.0
for f in bm.faces:
    n = f.normal
    c = f.calc_center_median()
    if n.z < -1e-6 and c.z > Z_BED+0.05:
        ang = math.degrees(math.asin(min(1.0, -n.z)))
        a = f.calc_area()
        down_area += a
        if a > 0.05:
            over_max = max(over_max, ang)
        if ang > OVERHANG_MAX and a > 1e-4:
            over_area += a
bm.free()
st_tree = BVHTree.FromPolygons([v for t in tris for v in t], [(3*i, 3*i+1, 3*i+2) for i in range(len(tris))])


def write_stl(path, ts, off):
    with open(path, "wb") as f:
        f.write(bytes(80)+struct.pack("<I", len(ts)))
        for t in ts:
            a, b, c = [p+off for p in t]
            n = (b-a).cross(c-a)
            n = n.normalized() if n.length > 0 else n
            f.write(struct.pack("<12fH", *n, *a, *b, *c, 0))


write_stl(os.path.join(SOUT, "Stand.stl"), tris, Vector())
bed_off = Vector((128-(lo.x+hi.x)/2, 128-(lo.y+hi.y)/2, -lo.z))
write_stl(os.path.join(SOUT, "Stand-bed.stl"), tris, bed_off)

# ---------------- clearance audits at the resting position ----------------


def min_gap(points):
    best, at = 99.0, None
    for p in points:
        n = st_tree.find_nearest(p)
        if n[0] is not None and n[3] < best:
            best, at = n[3], (round(p.x, 2), round(p.y, 2), round(p.z, 2))
    return round(best, 3), at


fin_pts = [v for v in fv if -30.0 < v.z < Z_ROOT-0.1 and v.x > LIP_X-1.0]
bulb_pts = [v for v in fv if v.z < -40.0]
chock_pts = [v for v in cv if v.x < XC1+3.0 and v.z < Z_CHOCK+3.0]
gaps = {"fin_to_slot_mm": min_gap(fin_pts), "bulb_to_neck_mm": min_gap([v for v in bulb_pts if v.x > 0.0]),
        "bulb_to_chock_mm": min_gap(chock_pts), "bulb_to_base_mm": round(z_flat-ZB, 3),
        "rudder_to_stand_mm": min_gap(rv)}
if gaps["fin_to_slot_mm"][0] < SLOT_CLEAR-0.06 or gaps["bulb_to_neck_mm"][0] < NECK_GAP-0.3 or gaps["bulb_to_chock_mm"][0] < CHOCK_CLEAR-0.06:
    raise RuntimeError("clearance %s" % gaps)
# contact pads: height-field cells inside the head plan, outside the slot
nx, ny = len(hxs), len(hys)
pad = [(float(hxs[i]), float(hys[j])) for i in range(nx) for j in range(ny)
       if x_rear(H[i, j]-0.05) <= hxs[i] <= x_front(H[i, j]-0.05) and abs(hys[j]) <= W_HEAD
       and abs(hys[j]) >= slot_hw(Z_ROOT, hxs[i])[0]]
PAD_X = (min(p[0] for p in pad), max(p[0] for p in pad))

# ---------------- lift-off path: up LIFT, aft SLIDE, up 40 ----------------
P = np.array([[v.x, v.y, v.z] for v in hv+fv+rv])
path = [(0.0, 0.0, t) for t in np.arange(0.25, LIFT+1e-9, 0.25)]
path += [(-s, 0.0, LIFT) for s in np.arange(0.5, SLIDE+1e-9, 0.5)]
path += [(-SLIDE, 0.0, LIFT+t) for t in np.arange(2.0, 40.1, 2.0)]
PAR_D = Vector((0.123, 0.981, 0.149)).normalized()


def inside(p):
    o, k = Vector(p), 0
    while True:
        h = st_tree.ray_cast(o, PAR_D)
        if h[0] is None:
            return k % 2 == 1
        k += 1; o = h[0]+PAR_D*1e-4


bb_lo, bb_hi = np.array(lo)-0.01, np.array(hi)+0.01
hits, checked = {}, 0
for o in path:
    Q = P+np.array(o)
    m = np.all((Q >= bb_lo) & (Q <= bb_hi), axis=1)
    cnt = 0
    for q in Q[m]:
        checked += 1
        if q[2] < ZB-0.01 and ((q[0]-XC)/A)**2+(q[1]/BASE_HW)**2 <= 1.0:
            cnt += 1
        elif inside(q):
            cnt += 1
    if cnt:
        hits["%.2f,%.2f" % (o[0], o[2])] = cnt
EXPLORE = os.environ.get("STAND_EXPLORE") == "1"
if hits and not EXPLORE:
    raise RuntimeError("lift-off path blocked %s" % hits)

# ---------------- stability ----------------
cvol, cmom = 0.0, Vector()
for a, b, c in tris:
    v6 = a.dot(b.cross(c))
    cvol += v6; cmom += v6*(a+b+c)/4.0
stand_cg = cmom/cvol
stand_g, stand_g_src = vol/1000*PLA_STAND_G_PER_CM3, "estimate %.2f g/cm3" % PLA_STAND_G_PER_CM3
tt = os.path.join(SOUT, "slice", "times.txt")
if os.path.exists(tt):
    mg = re.search(r"total filament weight \[g\] : ([\d.]+)", open(tt).read())
    if mg:
        stand_g, stand_g_src = float(mg.group(1)), "BambuStudio slice"
hj = json.load(open(os.path.join(OUT, "hydro_check.json")))
M, Lm, Lc, G = hj["mass_g"]["total"], hj["mass_g"]["lead"], Vector(hj["lead_centroid"]), Vector(hj["G"])
cases = {"sailing trim (full lead, paper sail)": (M, G), "no lead": (M-Lm, (G*M-Lc*Lm)/(M-Lm))}
ds = os.environ.get("DISPLAY_SAIL_JSON")
if ds and os.path.exists(ds):
    dj = json.load(open(ds))
    dm = dj["mass_g"]-dj["replaces_paper_g"]
    cases["full lead, printed display sail"] = (M+dm, (G*M+Vector(dj["centroid"])*dm)/(M+dm))


def tip_deg(p, H_, ux, uy):
    hsup = ux*XC+math.sqrt((A*ux)**2+(BASE_HW*uy)**2)
    return math.degrees(math.atan2(hsup-(ux*p.x+uy*p.y), H_))


stab = {"stand_mass_g": round(stand_g, 1), "stand_mass_source": stand_g_src, "stand_cg": [round(v, 2) for v in stand_cg],
        "cases": {}}
for k, (m, g) in cases.items():
    tot = (g*m+stand_cg*stand_g)/(m+stand_g)
    H_ = tot.z-Z_BED
    dirs = [(math.cos(math.radians(a)), math.sin(math.radians(a))) for a in range(0, 360, 2)]
    stab["cases"][k] = {
        "boat_mass_g": round(m, 2), "G": [round(v, 2) for v in g],
        "G_margin_to_pads_aft_mm": round(g.x-PAD_X[0], 2), "G_margin_to_pads_fore_mm": round(PAD_X[1]-g.x, 2),
        "roll": "held by the fin in the slot (%.1f mm per side)" % SLOT_CLEAR,
        "assembly_tip_deg": {"sideways": round(tip_deg(tot, H_, 0, 1), 1), "forward": round(tip_deg(tot, H_, 1, 0), 1),
                             "aft": round(tip_deg(tot, H_, -1, 0), 1),
                             "any_direction_min": round(min(tip_deg(tot, H_, ux, uy) for ux, uy in dirs), 1)}}
    if not (PAD_X[0]+5.0 < g.x < PAD_X[1]-5.0):
        raise RuntimeError("G %.2f not over the pads with 5 mm margin" % g.x)
report = {
    "type": "swan-neck",
    "base": {"shape": "ellipse", "length_mm": round(2*A, 1), "width_mm": 2*BASE_HW, "thickness_mm": BASE_T,
             "x_range": [round(x_lo, 2), round(x_hi, 2)], "top_z": round(ZB, 2), "top_bevel_mm": BASE_BEVEL,
             "volume_cm3": round(v_base/1000, 2)},
    "neck": {"root_x": [round(XR0, 2), round(XF0, 2)], "section_at_root_mm": [NECK_T, 2*NECK_HW],
             "section_at_lean_mm": [NECK_T45, 2*NECK_HW], "lean_deg": 45.0, "gap_to_bulb_nose_mm": NECK_GAP,
             "root_fillet_mm": ROOT_R, "rear_arc_r": R_REAR, "front_arc_r": R_FRONT},
    "fork": {"pads_x": [round(v, 2) for v in PAD_X], "head_half_width_mm": round(W_HEAD, 2),
             "slot_half_width_max_mm": round(HW_MAX, 2), "cheek_mm": CHEEK_T, "slot_clearance_mm": SLOT_CLEAR,
             "slot_end_x_at_root": round(slot_hw(Z_ROOT, 0)[1], 2), "crotch_z": round(crotch, 2),
             "lip_z": round(Z_LIP, 2), "pad_cells": len(pad), "contact": "zero gap: pads follow the hull bottom"},
    "chock": {"x": [round(XC0, 2), round(XC1, 2)], "front_top_z": round(Z_CHOCK, 2), "max_top_z": round(CHOCK_TOP, 2),
              "half_width_mm": CHOCK_HW, "shape": "saddle following the bulb tail underside",
              "lock_height_over_bulb_flat_mm": [CHOCK_LOCK, round(CHOCK_TOP-z_flat, 2)], "clearance_mm": CHOCK_CLEAR,
              "lift_to_remove_mm": LIFT},
    "clearances": gaps,
    "lift_off": {"path": "lift %.1f mm, slide aft %.0f mm, lift off" % (LIFT, SLIDE), "steps": len(path),
                 "vertex_checks": checked, "hits": hits},
    "printability": {"downward_area_mm2": round(down_area, 1), "area_over_%d_deg_mm2" % OVERHANG_MAX: round(over_area, 2),
                     "max_overhang_from_vertical_deg_faces_over_0.05mm2": round(over_max, 1), "supports": "none"},
    "stability": stab,
    "nonmanifold_edges": nonman, "volume_cm3": round(vol/1000, 2),
    "volume_parts_cm3": {"base": round(v_base/1000, 2), "neck_head": round(v_head/1000, 2), "chock": round(v_chock/1000, 3)},
    "size_mm": [round(hi[i]-lo[i], 1) for i in range(3)],
    "assembled_bbox": [[round(v, 2) for v in lo], [round(v, 2) for v in hi]]}
json.dump(report, open(os.path.join(SOUT, "stand.json"), "w"), indent=1)
print("STAND", json.dumps(report))
if nonman:
    raise RuntimeError("stand non-manifold")
