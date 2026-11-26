"""Swan-neck display stand for Margaret (Revision 11, T4): a thin egg-shaped base and ONE neck that rises between the
rudder and the ballast bulb's tail, leans forward 48 deg under the hull, and ends in a fork head that cradles the hull
bottom either side of the fin root.  No pins, nothing enters the model.

* Fork: the head's top is the hull-bottom height field (zero-gap pads either side of the fin).  The fin slot is CLOSED
  at the rear (a stop SLOT_CLEAR behind the fin's trailing edge, so she cannot go aft) and open forward.  Near the stop
  it is the fin's swept section plus SLOT_CLEAR per side (she cannot roll); forward it flares so that, once she has slid
  SLIDE forward, the ballast bulb can pass up through it.
* Lock: a saddle chock on the base sits CHOCK_CLEAR under the bulb's rising nose, so she cannot walk forward.
  To take her off: lift LIFT, slide forward SLIDE, lift off (audited: every hull/keel/rudder vertex on that path).
* Printed upright.  Base, root fillet and neck are support-free (<= 48 deg, audited); tree supports only under the
  fork head, which is hidden under the hull.

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
LIFT_CLEAR = 0.8            # bulb to the flared slot wall on the final lift
CHEEK_T = 2.4               # fork cheek thickness beside the slot
W_BRIDGE = 4.6              # head half-width aft of the slot (neck widens to this under the head)
WIDEN = 8.0                 # neck widening length below the head: lean + widening stay <= 50 deg at the corners
BULB_GAP = 8.0              # bulb flat above the base top: the boat stands visibly raised
BASE_T, BASE_BEVEL, BASE_FOOT = 1.4, 0.8, 0.3
BASE_B, BASE_K = 31.0, 0.25  # egg: y = B sin t (1 + K cos t), widest ahead of centre
BASE_X_HI = 28.0            # base front (chock and G well inside)
BASE_MARGIN = 4.5           # base edge beyond the neck root fillet (aft)
XR0, XF0 = -60.0, -53.5     # neck root: rear and front faces (between the rudder and the bulb tail)
NECK_HW = 2.8               # neck half-width (y)
ROOT_R = 4.0                # neck-to-base fillet radius
HEAD_R = 2.5                # neck plan corner radius = head rear corner radius
LEAN = 48.0                 # neck lean from vertical (print overhang limit 50)
ZA_F, R_F = -42.0, 10.0     # front face vertical up to ZA_F, then an R_F arc into the lean
R_R, T_L = 16.0, 5.0        # rear arc radius; neck thickness square to the lean
X_TIP, TIP_R = 5.0, 1.5     # fork prong tips (at the fin's leading edge) and their plan corner radius
SLIDE = 29.0                # lift-off: up LIFT (set by the chock), forward SLIDE, then up
CHOCK_LOCK, CHOCK_CLEAR, CHOCK_LEN, CHOCK_HW = 1.6, 0.4, 5.5, 3.0
CHOCK_WRAP = 2.0            # saddle rises around the nose at most this far above the bulb flat
Z_TOP = -8.0                # head stack top (trimmed by the hull height field)
Z_ROOT = -12.25             # fin sections above this are inside the hull socket
OVERHANG_MAX = 50.0
PLA_STAND_G_PER_CM3 = 1.10  # estimate until sliced
TL, CL, SL = math.tan(math.radians(LEAN)), math.cos(math.radians(LEAN)), math.sin(math.radians(LEAN))


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
hull = BVHTree.FromPolygons(hv, hp)
fin = BVHTree.FromPolygons(fv, fp)
cup = BVHTree.FromPolygons(cv, cpl)
z_flat = min(v.z for v in cv)
ZB = z_flat-BULB_GAP                                       # base top
Z_BED = ZB-BASE_T
BULB_NOSE_X = max(v.x for v in cv)
BULB_TAIL_X = min(v.x for v in cv)
FIN_TE_X = min(v.x for v in fv if v.z > -30.0)


# ---------------- nose chock (saddle); it sets the lift-off height ----------------
def bulb_bottom(x):
    zz = []
    for y in np.linspace(-CHOCK_HW, CHOCK_HW, 9):
        h = cup.ray_cast(Vector((x, y, -80.0)), Vector((0, 0, 1)))
        if h[0] is not None:
            zz.append(h[0].z)
    return min(zz) if zz else None


Z_CHOCK = z_flat+CHOCK_LOCK
XC0 = None
for x in np.arange(-10.0, BULB_NOSE_X, 0.1):
    zb = bulb_bottom(x)
    if zb is not None and zb >= Z_CHOCK+CHOCK_CLEAR:
        XC0 = float(x)
        break
XC1 = XC0+CHOCK_LEN
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


# ---------------- fin slot near the stop: swept fin section + clearance ----------------
GX0, GX1, GDX = -30.0, 12.0, 0.1
GZ0, GDZ = -20.0, 0.1
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
pre = np.maximum.accumulate(hb, axis=1)                    # everything aft passes x on the way out (boat slides fwd)
nl = int(round(LIFT/GDZ))
nc = int(round(SLOT_CLEAR/GDZ))                            # vertical clearance under downward steps of the fin
lw = np.array([pre[max(0, j-nl):j+nc+1].max(axis=0) for j in range(len(gz))])   # carried LIFT higher while sliding
lw[:, :-1] = np.maximum(lw[:, :-1], lw[:, 1:])            # one grid cell for the TE falling between samples
nk = int(round(SLOT_CLEAR/GDX))
hw_fin = np.zeros_like(lw)
for d in range(-nk, nk+1):
    r = math.sqrt(max(0.0, SLOT_CLEAR**2-(d*GDX)**2))
    sh = np.roll(lw, -d, axis=1)
    if d > 0:
        sh[:, -d:] = 0
    elif d < 0:
        sh[:, :-d] = 0
    hw_fin = np.maximum(hw_fin, np.where(sh > 0, sh+r, 0.0))

# ---------------- flare: plan footprint of fin + bulb (all z below the root), displaced forward by SLIDE ----------------
FX0, FX1, FDX = -54.0, 22.0, 0.1
fxs = np.arange(FX0, FX1+1e-9, FDX)
fpw = np.zeros(len(fxs))
for i, x in enumerate(fxs):
    m = 0.0
    for z in np.arange(-56.0, Z_ROOT+1e-9, 0.25):
        for s in (1, -1):
            h = fin.ray_cast(Vector((x, s*20.0, z)), Vector((0, -s, 0)))
            if h[0] is not None:
                m = max(m, abs(h[0].y))
    fpw[i] = m
nf = int(round(LIFT_CLEAR/FDX))
fpd = np.zeros_like(fpw)
for d in range(-nf, nf+1):
    r = math.sqrt(max(0.0, LIFT_CLEAR**2-(d*FDX)**2))
    sh = np.roll(fpw, -d)
    if d > 0:
        sh[-d:] = 0
    elif d < 0:
        sh[:-d] = 0
    fpd = np.maximum(fpd, np.where(sh > 0, sh+r, 0.0))


def flare_hw(x):
    return float(np.interp(x-SLIDE, fxs, fpd, left=0.0, right=0.0))


def row(z):
    return min(len(gz)-1, max(0, int(round((z-GZ0)/GDZ))))


def slot_hw(z, x):
    return max(float(np.interp(x, gx, hw_fin[row(z)])), flare_hw(x))


def slot_start(z):
    r = hw_fin[row(z)]
    return float(gx[np.nonzero(r > 0)[0].min()])


X_STOP = min(slot_start(z) for z in gz)
XE = X_TIP+3.0                                             # slot cutter runs out beyond the prong tips
# head plan half-width: cheeks CHEEK_T outside the widest slot at any head level, monotone forward
hx = np.arange(-40.0, X_TIP+1e-9, 0.05)
s_top = np.array([max(slot_hw(z, x) for z in gz[::5]) for x in hx])
hh_arr = np.maximum(W_BRIDGE, np.maximum.accumulate(np.where(hx >= X_STOP, s_top+CHEEK_T, 0.0)))


def hh(x):
    return float(np.interp(x, hx, hh_arr))


HH_MAX = float(hh_arr.max())


# ---------------- neck profile (side view) ----------------
a_f = XF0+R_F*(1-CL)-TL*(ZA_F+R_F*SL)                      # front (lower, overhanging) face line: x = a_f + tan * z
a_r = a_f-T_L/CL                                           # rear face line
ZA_R = (XR0+R_R*(1-CL)-a_r)/TL-R_R*SL                       # rear face: vertical below, arc, then the line


def face(z, x0, za, r, a):
    if z <= za:
        return x0
    if z <= za+r*SL:
        return x0+r*(1-math.cos(math.asin((z-za)/r)))
    return a+TL*z


def x_rear(z):
    return face(z, XR0, ZA_R, R_R, a_r)


def x_front(z):
    return face(z, XF0, ZA_F, R_F, a_f)


# hull-only height field over the head (fin and socket excluded) -> zero-gap pads
HX0, HX1, HY = x_rear(Z_ROOT)-3.0, X_TIP+4.0, HH_MAX+2.0
hxs = np.arange(HX0, HX1+1e-9, 0.2)
hys = np.arange(-HY, HY+1e-9, 0.2)
H = np.full((len(hxs), len(hys)), np.nan)
for i, x in enumerate(hxs):
    for j, y in enumerate(hys):
        h = hull.ray_cast(Vector((x, y, -30.0)), Vector((0, 0, 1)))
        if h[0] is not None and -14.0 < h[0].z < -8.0:
            H[i, j] = h[0].z
for i in range(len(hxs)):
    ok = ~np.isnan(H[i])
    if ok.any():
        k = np.nonzero(ok)[0]
        for j in np.nonzero(~ok)[0]:                       # inside the fin socket: nearest valid |y| (slot cuts it)
            H[i, j] = H[i, k[np.argmin(np.abs(k-j))]]
rows_ok = [i for i in range(len(hxs)) if not np.isnan(H[i]).any()]
for i in range(len(hxs)):
    if np.isnan(H[i]).any():
        H[i] = H[min(rows_ok, key=lambda k: abs(k-i))]
in_head = [(i, j) for i in range(len(hxs)) for j in range(len(hys))
           if X_STOP <= hxs[i] <= X_TIP and abs(hys[j]) <= hh(hxs[i])]
Z_HB = round(float(min(H[i, j] for i, j in in_head))-3.0, 2)  # flat head underside, 3 mm below the lowest pad
if Z_HB-1.5 < GZ0:
    raise RuntimeError("slot grid too shallow for head bottom %.2f" % Z_HB)


def width(z):
    z0, z1 = Z_HB-WIDEN, Z_HB
    if z >= z1:
        return W_BRIDGE
    if z <= z0:
        return NECK_HW
    t = (z-z0)/(z1-z0)
    return NECK_HW+(W_BRIDGE-NECK_HW)*t*t*(3-2*t)


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


# neck: horizontal plan sections stacked in z, root fillet at the base, capped just inside the head
zs, z = [], ZB-0.6
while z < Z_HB-0.05-1e-6:
    zs.append(z)
    z += 0.1 if z < ZB+ROOT_R+0.5 else 0.25
zs += [Z_HB-0.05, Z_HB+0.05, Z_HB+0.5]


def neck_ring(z):
    d = flare(z)-(0.05 if z > Z_HB else 0.0)              # inside the head: 0.05 inset, no coplanar faces to union
    return [(x, y, z) for x, y in rrect(x_rear(z)-d, x_front(z)+d, -width(z)-d, width(z)+d, HEAD_R+d)]


neck = rings_solid("Stand", [neck_ring(z) for z in zs])
v_neck = volume(neck)


# head: plan from the neck's rear face to the prong tips, half-width hh(x), rounded rear (= neck corner) and tips
NH = 160


def head_ring(z):
    xa, xb = x_rear(z), X_TIP
    pts = []
    for k in range(NH+1):
        x = xa+(xb-xa)*(1-math.cos(math.pi*k/NH))/2
        w = hh(x)
        if x < xa+HEAD_R:
            w = (w-HEAD_R)+math.sqrt(max(0.0, HEAD_R**2-(xa+HEAD_R-x)**2))
        elif x > xb-TIP_R:
            w = (w-TIP_R)+math.sqrt(max(0.0, TIP_R**2-(x-xb+TIP_R)**2))
        pts.append((x, w))
    return [(x, y, z) for x, y in pts]+[(x, -y, z) for x, y in reversed(pts)]


head = rings_solid("Head", [head_ring(z) for z in np.arange(Z_HB, Z_TOP+1e-9, 0.25)])
boolean(neck, head, "UNION")
hcut = heightfield_cutter("HullCut", hxs, hys, H, Z_TOP+3.0)
boolean(neck, hcut, "DIFFERENCE")

# fin slot cutter: closed rounded end at the stop, open past the prong tips
NS = 200
slot_rings = []
for z in list(np.arange(Z_HB-1.5, Z_ROOT+1e-9, 0.2))+[Z_ROOT+0.3, Z_TOP+3.0]:
    zz = min(z, Z_ROOT)
    xs0 = slot_start(zz)
    side = []
    for k in range(1, NS+1):
        x = xs0+(XE-xs0)*(1-math.cos(0.5*math.pi*k/NS))
        side.append((x, max(slot_hw(zz, x), 0.02)))
    slot_rings.append([(xs0-0.01, 0.0, z)]+[(x, y, z) for x, y in side]+[(x, -y, z) for x, y in reversed(side)])
boolean(neck, rings_solid("Slot", slot_rings), "DIFFERENCE")
v_head = volume(neck)-v_neck

# base: bevelled egg, widest ahead of centre (under G), narrow aft under the neck root
x_lo = XR0-ROOT_R-BASE_MARGIN
x_hi = BASE_X_HI
XC, A = (x_lo+x_hi)/2, (x_hi-x_lo)/2


def egg(a, b, z, n=200):
    return [(XC+a*math.cos(2*math.pi*k/n), b*math.sin(2*math.pi*k/n)*(1+BASE_K*math.cos(2*math.pi*k/n)), z)
            for k in range(n)]


def egg_hw(x, a=A, b=BASE_B):
    c = (x-XC)/a
    return b*math.sqrt(max(0.0, 1-c*c))*(1+BASE_K*c) if abs(c) <= 1 else 0.0


root_margin = egg_hw(XR0-ROOT_R)-(NECK_HW+ROOT_R)
chock_margin = min(egg_hw(XC0), egg_hw(XC1))-CHOCK_HW
if root_margin < 2.5 or chock_margin < 2.5:
    raise RuntimeError("base too small: root %.2f chock %.2f" % (root_margin, chock_margin))
base = rings_solid("Base", [egg(A-BASE_FOOT, BASE_B-BASE_FOOT, Z_BED), egg(A, BASE_B, Z_BED+BASE_FOOT),
                            egg(A, BASE_B, ZB-BASE_BEVEL), egg(A-BASE_BEVEL, BASE_B-BASE_BEVEL, ZB)])
chock = rings_solid("Chock", [[(x, y, z) for x, y in rrect(XC0, XC1, -CHOCK_HW, CHOCK_HW, 1.6)] for z in (ZB-0.6, CHOCK_TOP+1.0)])
boolean(chock, heightfield_cutter("ChockCut", cxs, cys, CH, -30.0), "DIFFERENCE")
v_base, v_chock = volume(base), volume(chock)
boolean(neck, base, "UNION")
boolean(neck, chock, "UNION")
stand = neck

bm = bmesh.new(); bm.from_mesh(stand.data)
bmesh.ops.triangulate(bm, faces=list(bm.faces))
nm_at = [[round(c, 2) for c in (e.verts[0].co+e.verts[1].co)/2] for e in bm.edges if not e.is_manifold]
nonman = len(nm_at)
vol = bm.calc_volume(signed=False)
lo = Vector([min(v.co[i] for v in bm.verts) for i in range(3)])
hi = Vector([max(v.co[i] for v in bm.verts) for i in range(3)])
tris = [tuple(v.co.copy() for v in f.verts) for f in bm.faces]
# printability: downward faces above the bed; the head underside (z >= Z_HB) is tree-supported, the rest must not be
over_area, over_max, down_area, sup_area = 0.0, 0.0, 0.0, 0.0
for f in bm.faces:
    n = f.normal
    c = f.calc_center_median()
    if n.z < -1e-6 and c.z > Z_BED+0.05:
        ang = math.degrees(math.asin(min(1.0, -n.z)))
        a = f.calc_area()
        down_area += a
        if c.z >= Z_HB-0.05:
            if ang > OVERHANG_MAX:
                sup_area += a
            continue
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


fin_pts = [v for v in fv if Z_HB-0.5 < v.z < Z_ROOT+0.2]
bulb_pts = [v for v in fv if v.z < -40.0]
chock_pts = [v for v in cv if v.x > XC0-3.0 and v.z < Z_CHOCK+3.0]
gaps = {"fin_to_slot_mm": min_gap(fin_pts), "bulb_to_neck_mm": min_gap([v for v in bulb_pts if v.x < -20.0]),
        "bulb_to_chock_mm": min_gap(chock_pts), "bulb_to_base_mm": round(z_flat-ZB, 3),
        "rudder_to_stand_mm": min_gap(rv), "fin_te_to_stop_mm": round(FIN_TE_X-X_STOP, 3)}
if gaps["fin_to_slot_mm"][0] < SLOT_CLEAR-0.06 or gaps["bulb_to_neck_mm"][0] < 2.5 or \
        gaps["bulb_to_chock_mm"][0] < CHOCK_CLEAR-0.06:
    raise RuntimeError("clearance %s" % gaps)
# contact pads: height-field cells where the stand top meets the hull bottom
pad = []
for i, x in enumerate(hxs):
    for j, y in enumerate(hys):
        h = st_tree.ray_cast(Vector((x, y, H[i, j]+0.05)), Vector((0, 0, -1)))
        if h[0] is not None and h[0].z > H[i, j]-0.05 and hull.ray_cast(Vector((x, y, -30.0)), Vector((0, 0, 1)))[0]:
            pad.append((float(x), float(y)))
PAD_X = (min(p[0] for p in pad), max(p[0] for p in pad))

# ---------------- lift-off path: up LIFT, forward SLIDE, up 50 ----------------
P = np.array([[v.x, v.y, v.z] for v in hv+fv+rv])
path = [(0.0, 0.0, t) for t in np.arange(0.25, LIFT+1e-9, 0.25)]
path += [(s, 0.0, LIFT) for s in np.arange(0.5, SLIDE+1e-9, 0.5)]
path += [(SLIDE, 0.0, LIFT+t) for t in np.arange(2.0, 50.1, 2.0)]
PAR_D = Vector((0.123, 0.981, 0.149)).normalized()


def inside(p):
    o, k = Vector(p), 0
    while True:
        h = st_tree.ray_cast(o, PAR_D)
        if h[0] is None:
            return k % 2 == 1
        k += 1; o = h[0]+PAR_D*1e-4


bb_lo, bb_hi = np.array(lo)-0.01, np.array(hi)+0.01
hits, checked, closest = {}, 0, (99.0, None)
for o in path:
    Q = P+np.array(o)
    m = np.all((Q >= bb_lo) & (Q <= bb_hi), axis=1)
    cnt = 0
    for q in Q[m]:
        checked += 1
        if inside(q):
            cnt += 1
    if cnt:
        hits["%.2f,%.2f" % (o[0], o[2])] = cnt
# closest approach of the rudder to the neck on the slide (the binding constraint on SLIDE)
R_ = np.array([[v.x, v.y, v.z] for v in rv])
for s in np.arange(0.0, SLIDE+1e-9, 0.5):
    for q in R_+np.array((s, 0.0, LIFT)):
        n = st_tree.find_nearest(Vector(q))
        if n[0] is not None and n[3] < closest[0]:
            closest = (round(n[3], 3), round(float(s), 1))
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
print_g = None
for sub, src in (("slice", None), ("slice-nosupport", "BambuStudio slice without supports (supports removed)")):
    tt = os.path.join(SOUT, sub, "times.txt")
    mg = re.search(r"total filament weight \[g\] : ([\d.]+)", open(tt).read()) if os.path.exists(tt) else None
    if mg and src:
        stand_g, stand_g_src = float(mg.group(1)), src
    elif mg:
        print_g = float(mg.group(1))
hj = json.load(open(os.path.join(OUT, "hydro_check.json")))
M, Lm, Lc, G = hj["mass_g"]["total"], hj["mass_g"]["lead"], Vector(hj["lead_centroid"]), Vector(hj["G"])
cases = {"sailing trim (full lead, paper sail)": (M, G), "no lead": (M-Lm, (G*M-Lc*Lm)/(M-Lm))}
ds = os.environ.get("DISPLAY_SAIL_JSON")
if ds and os.path.exists(ds):
    dj = json.load(open(ds))
    dm = dj["mass_g"]-dj["replaces_paper_g"]
    cases["full lead, printed display sail"] = (M+dm, (G*M+Vector(dj["centroid"])*dm)/(M+dm))
FOOT = [(p[0], p[1]) for p in egg(A-BASE_FOOT, BASE_B-BASE_FOOT, Z_BED, 720)]


def tip_deg(p, H_, ux, uy):
    hsup = max(ux*x+uy*y for x, y in FOOT)
    return math.degrees(math.atan2(hsup-(ux*p.x+uy*p.y), H_))


stab = {"stand_mass_g": round(stand_g, 1), "stand_mass_source": stand_g_src,
        "print_mass_incl_supports_g": print_g, "stand_cg": [round(v, 2) for v in stand_cg],
        "cases": {}}
for k, (m, g) in cases.items():
    tot = (g*m+stand_cg*stand_g)/(m+stand_g)
    H_ = tot.z-Z_BED
    dirs = [(math.cos(math.radians(a)), math.sin(math.radians(a))) for a in range(0, 360, 2)]
    stab["cases"][k] = {
        "boat_mass_g": round(m, 2), "G": [round(v, 2) for v in g],
        "G_margin_to_pads_aft_mm": round(g.x-PAD_X[0], 2), "G_margin_to_pads_fore_mm": round(PAD_X[1]-g.x, 2),
        "roll": "held by the fin in the slot (%.1f mm per side at the stop)" % SLOT_CLEAR,
        "assembly_tip_deg": {"sideways": round(tip_deg(tot, H_, 0, 1), 1), "forward": round(tip_deg(tot, H_, 1, 0), 1),
                             "aft": round(tip_deg(tot, H_, -1, 0), 1),
                             "any_direction_min": round(min(tip_deg(tot, H_, ux, uy) for ux, uy in dirs), 1)}}
    if not (PAD_X[0]+5.0 < g.x < PAD_X[1]-5.0) and not EXPLORE:
        raise RuntimeError("G %.2f not over the pads %s with 5 mm margin" % (g.x, PAD_X))
report = {
    "type": "swan-neck from aft",
    "base": {"shape": "egg", "length_mm": round(2*A, 1), "width_mm": round(2*max(abs(p[1]) for p in egg(A, BASE_B, 0, 720)), 1),
             "thickness_mm": BASE_T, "x_range": [round(x_lo, 2), round(x_hi, 2)], "top_z": round(ZB, 2),
             "top_bevel_mm": BASE_BEVEL, "margin_root_mm": round(root_margin, 2), "margin_chock_mm": round(chock_margin, 2),
             "volume_cm3": round(v_base/1000, 2)},
    "neck": {"root_x": [XR0, XF0], "section_at_root_mm": [round(XF0-XR0, 2), 2*NECK_HW],
             "section_at_lean_mm": [T_L, 2*NECK_HW], "lean_deg": LEAN, "lean_direction": "forward",
             "gap_to_bulb_tail_mm": gaps["bulb_to_neck_mm"][0], "gap_to_rudder_mm": gaps["rudder_to_stand_mm"][0],
             "root_fillet_mm": ROOT_R, "front_arc_r": R_F, "rear_arc_r": R_R, "front_vertical_to_z": ZA_F,
             "rear_vertical_to_z": round(ZA_R, 2)},
    "fork": {"pads_x": [round(v, 2) for v in PAD_X], "head_x": [round(x_rear(Z_HB), 2), X_TIP],
             "head_bottom_z": Z_HB, "head_half_width_mm": [W_BRIDGE, round(HH_MAX, 2)],
             "slot_stop_x": round(X_STOP, 2), "slot_half_width_at_stop_region_mm": round(float(hw_fin.max()), 2),
             "slot_half_width_at_tips_mm": round(slot_hw(Z_ROOT, X_TIP), 2), "cheek_mm": CHEEK_T,
             "slot_clearance_mm": SLOT_CLEAR, "lift_clearance_mm": LIFT_CLEAR, "pad_cells": len(pad),
             "contact": "zero gap: pads follow the hull bottom", "supports": "tree, under the head only"},
    "chock": {"x": [round(XC0, 2), round(XC1, 2)], "front_top_z": round(Z_CHOCK, 2), "max_top_z": round(CHOCK_TOP, 2),
              "half_width_mm": CHOCK_HW, "shape": "saddle following the bulb nose underside",
              "lock_height_over_bulb_flat_mm": [CHOCK_LOCK, round(CHOCK_TOP-z_flat, 2)], "clearance_mm": CHOCK_CLEAR,
              "lift_to_remove_mm": LIFT},
    "clearances": gaps,
    "lift_off": {"path": "lift %.1f mm, slide forward %.0f mm, lift off" % (LIFT, SLIDE), "steps": len(path),
                 "vertex_checks": checked, "hits": hits,
                 "rudder_closest_to_stand_on_slide_mm": {"gap": closest[0], "at_slide_mm": closest[1]}},
    "printability": {"downward_area_mm2": round(down_area, 1), "area_over_%d_deg_mm2" % OVERHANG_MAX: round(over_area, 2),
                     "max_overhang_from_vertical_deg_faces_over_0.05mm2": round(over_max, 1),
                     "head_underside_supported_mm2": round(sup_area, 1),
                     "supports": "tree supports under the fork head only; base, fillet and neck support-free"},
    "stability": stab,
    "nonmanifold_edges": nonman, "nonmanifold_at": nm_at[:12], "volume_cm3": round(vol/1000, 2),
    "volume_parts_cm3": {"base": round(v_base/1000, 2), "neck": round(v_neck/1000, 2), "head": round(v_head/1000, 2),
                         "chock": round(v_chock/1000, 3)},
    "size_mm": [round(hi[i]-lo[i], 1) for i in range(3)],
    "assembled_bbox": [[round(v, 2) for v in lo], [round(v, 2) for v in hi]]}
json.dump(report, open(os.path.join(SOUT, "stand.json"), "w"), indent=1)
print("STAND", json.dumps(report))
if nonman:
    raise RuntimeError("stand non-manifold")
if over_area > 0.5 and not EXPLORE:
    raise RuntimeError("unsupported overhang %.2f mm2 over %d deg" % (over_area, OVERHANG_MAX))
