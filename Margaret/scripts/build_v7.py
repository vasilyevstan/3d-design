# Margaret v7: fuller-shouldered planform, filleted fin that fades into the hull, round-tailed
# bulb, open-transom stern (helm seats + centre passage + tread + swim platform with ladder),
# teak side decks/foredeck with sprung caulking, bow roller, taller mast.
# Headless:  Blender -b --factory-startup --python-exit-code 1 -P build_v7.py
import sys, os, json, math, bisect, time, bpy, bmesh
from mathutils import Vector
D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import importlib, hullgen as G
importlib.reload(G)

P = json.load(open(os.path.join(D, "hull_params_v7.json")))
OUT = os.environ.get("MARGARET_OUT", os.path.join(D, "yacht-build", "v7"))
os.makedirs(OUT, exist_ok=True)
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
H = G.hull_tables(P)
T0 = time.time()

SEAM = P["seam"]; WALL = 0.85; DECK = 0.8
LAND = 1.8
X_MAST, X_FIN, X_RUD = 26.0, -1.0, -72.0
T6 = math.tan(math.radians(10.0))
FONT = "/System/Library/Fonts/Supplemental/Verdana Bold.ttf"


def log(*a):
    print("[%5.1fs]" % (time.time()-T0), *a, flush=True)


# ---------------------------------------------------------------- helpers
def pchip(pts):
    xs = [float(p[0]) for p in pts]; ys = [float(p[1]) for p in pts]; n = len(xs)
    h = [xs[i+1]-xs[i] for i in range(n-1)]
    dl = [(ys[i+1]-ys[i])/h[i] for i in range(n-1)]
    m = [0.0]*n; m[0] = dl[0]; m[-1] = dl[-1]
    for i in range(1, n-1):
        if dl[i-1]*dl[i] <= 0:
            m[i] = 0.0
        else:
            w1 = 2*h[i]+h[i-1]; w2 = h[i]+2*h[i-1]
            m[i] = (w1+w2)/(w1/dl[i-1]+w2/dl[i])
    return (xs, ys, m, h)


def pc(S, x):
    xs, ys, m, h = S
    if x <= xs[0]:
        return ys[0]+m[0]*(x-xs[0])
    if x >= xs[-1]:
        return ys[-1]+m[-1]*(x-xs[-1])
    i = min(max(bisect.bisect_right(xs, x)-1, 0), len(xs)-2)
    t = (x-xs[i])/h[i]
    return ((2*t**3-3*t*t+1)*ys[i]+(t**3-2*t*t+t)*h[i]*m[i]+(-2*t**3+3*t*t)*ys[i+1]+(t**3-t*t)*h[i]*m[i+1])


def link(name, bm):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    return ob


def rings_solid(name, rings, cap=True):
    bm = bmesh.new()
    R = [[bm.verts.new(p) for p in r] for r in rings]
    for r0, r1 in zip(R, R[1:]):
        L = len(r0)
        for j in range(L):
            bm.faces.new((r0[j], r0[(j+1) % L], r1[(j+1) % L], r1[j]))
    if cap:
        bm.faces.new(list(reversed(R[0]))); bm.faces.new(R[-1])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return link(name, bm)


def prism(name, poly, axis, a0, a1):
    """poly: 2D points; axis 'z' -> poly is (x,y); 'y' -> poly is (x,z)."""
    def P3(p, a):
        return (p[0], p[1], a) if axis == "z" else (p[0], a, p[1])
    return rings_solid(name, [[P3(p, a0) for p in poly], [P3(p, a1) for p in poly]])


def rrect(x0, x1, y0, y1, r, seg=8):
    r = min(r, (x1-x0)/2-1e-3, (y1-y0)/2-1e-3)
    pts = []
    for cx, cy, a0 in ((x1-r, y0+r, -90), (x1-r, y1-r, 0), (x0+r, y1-r, 90), (x0+r, y0+r, 180)):
        for k in range(seg+1):
            a = math.radians(a0+90*k/seg)
            pts.append((cx+r*math.cos(a), cy+r*math.sin(a)))
    return pts


def rbox(name, x0, x1, y0, y1, z0, z1, r, seg=8):
    return prism(name, rrect(x0, x1, y0, y1, r, seg), "z", z0, z1)


def stadium(cx, cy, lx, ly, seg=12):
    return rrect(cx-lx/2, cx+lx/2, cy-ly/2, cy+ly/2, min(lx, ly)/2-1e-3, seg)


def lathe(name, cx, cy, prof, seg=40):
    rings = [[(cx+r*math.cos(2*math.pi*k/seg), cy+r*math.sin(2*math.pi*k/seg), z) for k in range(seg)] for r, z in prof]
    return rings_solid(name, rings)


def torus_z(name, cx, cy, cz, major, minor, n_major=32, n_minor=10):
    bm = bmesh.new()
    grid = []
    for i in range(n_major):
        t = 2*math.pi*i/n_major
        row = []
        for j in range(n_minor):
            a = 2*math.pi*j/n_minor
            r = major+minor*math.cos(a)
            row.append(bm.verts.new((cx+r*math.cos(t), cy+r*math.sin(t), cz+minor*math.sin(a))))
        grid.append(row)
    for i in range(n_major):
        for j in range(n_minor):
            bm.faces.new((grid[i][j], grid[(i+1) % n_major][j],
                          grid[(i+1) % n_major][(j+1) % n_minor], grid[i][(j+1) % n_minor]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return link(name, bm)


def torus_y(name, cx, cy, cz, major, minor, n_major=32, n_minor=10):
    bm = bmesh.new()
    grid = []
    for i in range(n_major):
        t = 2*math.pi*i/n_major
        row = []
        for j in range(n_minor):
            a = 2*math.pi*j/n_minor
            r = major+minor*math.cos(a)
            row.append(bm.verts.new((cx+r*math.cos(t), cy+minor*math.sin(a), cz+r*math.sin(t))))
        grid.append(row)
    for i in range(n_major):
        for j in range(n_minor):
            bm.faces.new((grid[i][j], grid[(i+1) % n_major][j],
                          grid[(i+1) % n_major][(j+1) % n_minor], grid[i][(j+1) % n_minor]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return link(name, bm)


def rod_x(name, x0, x1, y, z, radius, n=20):
    rings = []
    for x in (x0, x1):
        rings.append([(x, y+radius*math.cos(2*math.pi*k/n),
                       z+radius*math.sin(2*math.pi*k/n)) for k in range(n)])
    return rings_solid(name, rings)


def rod_y(name, x, y0, y1, z, radius, n=20):
    rings = []
    for y in (y0, y1):
        rings.append([(x+radius*math.cos(2*math.pi*k/n), y,
                       z+radius*math.sin(2*math.pi*k/n)) for k in range(n)])
    return rings_solid(name, rings)


def rod_between(name, p0, p1, radius=0.1, n=8):
    a = Vector(p0); b = Vector(p1); axis = (b-a).normalized()
    ref = Vector((0, 0, 1))
    if abs(axis.dot(ref)) > 0.9:
        ref = Vector((0, 1, 0))
    u = axis.cross(ref).normalized(); v = axis.cross(u).normalized()
    rings = []
    for center in (a, b):
        rings.append([tuple(center+radius*(u*math.cos(2*math.pi*k/n)+
                                           v*math.sin(2*math.pi*k/n))) for k in range(n)])
    return rings_solid(name, rings)


def pad(name, x0, x1, y0, y1, z0, z1, r, ch):
    """Rounded-plan block whose top edge is softened by `ch`."""
    rings = []
    for z, d in ((z0, 0.0), (z1-ch, 0.0), (z1-0.3*ch, 0.3*ch), (z1, ch)):
        rings.append([(px, py, z) for px, py in rrect(x0+d, x1-d, y0+d, y1-d, max(r-d, 0.2), 8)])
    return rings_solid(name, rings)


def bool_many(a, objs, op):
    for o in objs:
        G.boolean(a, o, op)
    return a


def dup(ob, name):
    o = ob.copy(); o.data = ob.data.copy(); o.name = name
    bpy.context.scene.collection.objects.link(o)
    return o


def half_space(name, z0, z1):
    return G.box(name, -250, 250, -120, 120, z0, z1)


from mathutils.bvhtree import BVHTree


def selfx(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.triangulate(bm, faces=bm.faces)
    t = BVHTree.FromBMesh(bm); bm.faces.ensure_lookup_table()
    bad = [a for a, b in t.overlap(t) if a < b and not (set(v.index for v in bm.faces[a].verts) & set(v.index for v in bm.faces[b].verts))]
    bm.free()
    return bad


def stats(ob):
    s = G.mesh_stats(ob)
    log(ob.name, s)
    return s


def zs(x):
    return G.ev(H["zs"], x)


def hb(x):
    return G.ev(H["bs"], x)


def camber(x):
    return 0.042*max(hb(x), 0.0)


def deck_z(x, y):
    B = max(hb(x), 1.0)
    return zs(x)+camber(x)*(1-(y/B)**2)


def box_xy(name, x0, x1, y0, y1, z0, z1):
    y0, y1 = min(y0, y1), max(y0, y1)
    return prism(name, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "z", z0, z1)


def stations(x0, x1, N, a=0.72):
    L = x1-x0
    return [x0+L*(t-a*math.sin(2*math.pi*t)/(2*math.pi)) for t in [i/(N-1) for i in range(N)]]


def y_at_z(x, z, inset=0.0):
    hs, _ = G.half_section(H, x, 400, inset)
    for (y0, z0), (y1, z1) in zip(hs, hs[1:]):
        if z0 <= z <= z1 and z1 > z0:
            return y0+(y1-y0)*(z-z0)/(z1-z0)
    return None


def plan_poly(x0, x1, hw0, hw1, r, seg=8):
    """Rounded, linearly tapered plan outline with matched ring vertex counts."""
    r0 = min(r, (x1-x0)/2-1e-3, hw0-1e-3)
    r1 = min(r, (x1-x0)/2-1e-3, hw1-1e-3)
    pts = []
    corners = [
        (x1-r1, -hw1+r1, -90), (x1-r1, hw1-r1, 0),
        (x0+r0, hw0-r0, 90), (x0+r0, -hw0+r0, 180)
    ]
    for cx, cy, a0 in corners:
        rr = r1 if cx > (x0+x1)/2 else r0
        for k in range(seg+1):
            a = math.radians(a0+90*k/seg)
            pts.append((cx+rr*math.cos(a), cy+rr*math.sin(a)))
    return pts


def pocket(name, x0, x1, hw0, hw1, r, z0, z1, floor_r=0.8, top_r=1.0, end_r=0.0):
    """Lofted rounded cockpit void with printable floor and rim transitions."""
    rings = []
    for z, off in [(z0, -floor_r)]:
        rings.append([(x, y, z) for x, y in plan_poly(
            x0-off, x1+off, hw0+off, hw1+off, max(0.1, r+off))])
    for k in range(1, 6):
        a = math.pi*k/10
        off = -floor_r+floor_r*math.sin(a)
        z = z0+floor_r*(1-math.cos(a))
        rings.append([(x, y, z) for x, y in plan_poly(
            x0-off, x1+off, hw0+off, hw1+off, max(0.1, r+off))])
    zt = z1-top_r
    rings.append([(x, y, zt) for x, y in plan_poly(x0, x1, hw0, hw1, r)])
    for k in range(1, 6):
        a = math.pi*k/10
        off = top_r*(1-math.cos(a))
        z = zt+top_r*math.sin(a)
        rings.append([(x, y, z) for x, y in plan_poly(
            x0-off, x1+off, hw0+off, hw1+off, r+off)])
    return rings_solid(name, rings)


def smin(a, b, k):
    h = max(k-abs(a-b), 0.0)/k
    return min(a, b)-h*h*k*0.25


def coaming_solid(side):
    rings = []
    for i in range(62):
        x = -65.5+0.5*i
        if x < -58.5:
            t = (x+65.5)/7.0
            ztop = 16.0+2.5*t*t*(3.0-2.0*t)
        elif x <= -42.0:
            ztop = 18.5
        else:
            t = (x+42.0)/7.0
            ztop = 18.5-2.5*t*t*(3.0-2.0*t)
        prof = [(17.4, 13.4), (22.4, 13.4), (22.4, ztop-0.8),
                (22.0, ztop-0.2), (21.4, ztop), (18.6, ztop),
                (18.0, ztop-0.5)]
        if side < 0:
            prof.reverse()
        rings.append([(x, side*y, z) for y, z in prof])
    return rings_solid("Coaming%d" % side, rings)


FIN_FILLET_H, FIN_FILLET_K = 2.5, 0.6


def bulb_crown(x):
    return BULB_ZC+BULB_HH*bulb_factor((X_BULB+BULB_L/2-x)/BULB_L)


def naca_fin(name, xfin, zroot=-12.3, ztip=-44.0, zend=None, ztop=None, hull=None):
    """NACA fin; chord/LE taper defined root→ztip and extrapolated to zend. With zend set, the fin is buried in the
    bulb down to just above the glue plane and gets a concave fairing fillet that follows the bulb crown."""
    rings = []
    u_samples = [0.5*(1.0-math.cos(math.pi*i/32)) for i in range(33)]
    zend = ztip if zend is None else zend
    zf = zend+FIN_FILLET_H+3.6
    z0 = zroot if ztop is None else ztop
    zs_ = [z0+(zf-z0)*i/20 for i in range(20)]+[zf+(zend-zf)*i/24 for i in range(25)] if zend != ztip else \
        [z0+(ztip-z0)*i/24 for i in range(25)]
    for z in zs_:
        t = (z-zroot)/(ztip-zroot)
        chord = 27.0+(19.5-27.0)*t
        xle = xfin+9.0+(xfin+2.5-(xfin+9.0))*t

        def yt(u):
            f = 5*0.13*(0.2969*math.sqrt(max(u, 0.0))-0.1260*u-0.3516*u*u+
                        0.2843*u**3-0.1015*u**4)
            y = max(chord*f, 0.25*u**8)
            if zend != ztip:
                h = z-bulb_crown(xle-u*chord)
                s = min(max(1.0-h/FIN_FILLET_H, 0.0), 1.0)
                fade = min(max(chord*(1.0-u)/2.0, 0.0), 1.0)
                y *= 1.0+FIN_FILLET_K*s*s*fade
            return y
        section = [(xle-u*chord, yt(u)) for u in u_samples]
        section += [(xle-u*chord, -yt(u)) for u in reversed(u_samples[1:])]
        rings.append([(x, y, z) for x, y in section])
    foil = rings_solid(name, rings)
    if hull is not None:
        G.boolean(foil, dup(hull, "FinRootTrim"), "DIFFERENCE")
    tenon = rbox("FinTenon", xfin-9.0, xfin+9.0, -1.6, 1.6, -12.6, -7.3, 0.8)
    G.boolean(foil, tenon, "UNION")
    return foil


RUD_STOCK_R, RUD_STOCK_TOP = 1.0, 10.05
RUD_GAP = 0.7
_HULL_BVH = []


def hull_bottom_z(x):
    """Lowest outer-hull z on the centreline at x (ray cast up through HYDRO_HULL)."""
    if not _HULL_BVH:
        bm = bmesh.new(); bm.from_mesh(HYDRO_HULL.data)
        _HULL_BVH.append(BVHTree.FromBMesh(bm)); bm.free()
    hit = _HULL_BVH[0].ray_cast(Vector((x, 0.0, -80.0)), Vector((0, 0, 1)), 200)
    if hit[0] is None:
        raise RuntimeError("no hull above rudder at x=%.2f" % x)
    return hit[0].z


RUD_C_ROOT, RUD_C_TIP, RUD_Z_HULL, RUD_TC = 12.0, 7.5, -5.0, 0.16
RUD_HALF_T = 0.6               # blade is a 1.2 mm plate with faired NACA edges
RUD_Y_OFF = RUD_HALF_T-RUD_STOCK_R  # blade face flush with the stock's print face


def naca_rudder(name, xrud):
    """Tapered spade: 7 deg swept LE, near-vertical TE, rounded tip, stock at 27% root chord."""
    rings = []
    u_samples = [0.5*(1.0-math.cos(math.pi*i/32)) for i in range(33)]
    zroot, ztip = 3.0, -25.0
    sweep = math.tan(math.radians(7.0))
    for iz in range(29):
        t = iz/28
        z = zroot+(ztip-zroot)*t
        f = (RUD_Z_HULL-z)/(RUD_Z_HULL-ztip)
        chord = RUD_C_ROOT+(RUD_C_TIP-RUD_C_ROOT)*f
        xle = xrud+0.27*RUD_C_ROOT-sweep*(RUD_Z_HULL-z)
        dz = z-ztip
        if dz < 3.0:
            chord -= 3.0-math.sqrt(max(9.0-(3.0-dz)**2, 0.0))
        section = []
        for u in u_samples:
            yt = chord*5*RUD_TC*(0.2969*math.sqrt(max(u, 0.0))-0.1260*u-
                                 0.3516*u*u+0.2843*u**3-0.1015*u**4)
            section.append((xle-u*chord, yt))
        for u in reversed(u_samples[1:]):
            yt = chord*5*RUD_TC*(0.2969*math.sqrt(max(u, 0.0))-0.1260*u-
                                 0.3516*u*u+0.2843*u**3-0.1015*u**4)
            section.append((xle-u*chord, -yt))
        rings.append([(x, y, z) for x, y in section])
    blade = rings_solid(name, rings)
    xs_ = [xle_ for xle_ in (xrud+8.5-0.25*k for k in range(77))]
    top = [(x, hull_bottom_z(x)-RUD_GAP) for x in xs_]
    G.boolean(blade, prism("RudderCrown", top+[(xs_[-1], 40.0), (xs_[0], 40.0)], "y", -4.0, 4.0), "DIFFERENCE")
    G.boolean(blade, rbox("RudderFlats", xrud-14.0, xrud+8.0, -RUD_HALF_T, RUD_HALF_T, -30.0, 20.0, 0.05), "INTERSECT")
    for v in blade.data.vertices:
        v.co.y += RUD_Y_OFF
    zc = hull_bottom_z(xrud)-RUD_GAP
    G.boolean(blade, lathe("RudderStock", xrud, 0, [(0.35, zc-3.2), (RUD_STOCK_R, zc-1.8), (RUD_STOCK_R, RUD_STOCK_TOP-0.25),
                                                    (RUD_STOCK_R-0.25, RUD_STOCK_TOP)], 32), "UNION")
    G.boolean(blade, rbox("TrimSlot", xrud-1.5, xrud+1.5, -0.25, 0.25, RUD_STOCK_TOP-0.55, RUD_STOCK_TOP+1, 0.05), "DIFFERENCE")
    return blade


def cylinder_y(name, cx, cy, cz, radius, depth, n=24):
    rings = []
    for y in (cy-depth/2, cy+depth/2):
        rings.append([(cx+radius*math.cos(2*math.pi*k/n), y,
                       cz+radius*math.sin(2*math.pi*k/n)) for k in range(n)])
    return rings_solid(name, rings)


def prism_x(name, poly_yz, x0, x1):
    return rings_solid(name, [[(x0, y, z) for y, z in poly_yz],
                              [(x1, y, z) for y, z in poly_yz]])


def revolve_x(name, cx, cy, cz, major, prof, n_major=56):
    """Closed (dr, dx) section swept around an axis parallel to X."""
    bm = bmesh.new()
    grid = []
    for i in range(n_major):
        t = 2*math.pi*i/n_major
        grid.append([bm.verts.new((cx+dx, cy+(major+dr)*math.cos(t), cz+(major+dr)*math.sin(t)))
                     for dr, dx in prof])
    m = len(prof)
    for i in range(n_major):
        for j in range(m):
            bm.faces.new((grid[i][j], grid[(i+1) % n_major][j],
                          grid[(i+1) % n_major][(j+1) % m], grid[i][(j+1) % m]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return link(name, bm)


WHEEL_X, WHEEL_Y, WHEEL_Z = -68.25, 13.0, 22.5
WHEEL_T, WHEEL_R = 1.12, 7.25
BINNACLE_AFT = -67.3
STUB_R, STUB_L, AXLE_BORE_R = 0.8, 2.3, 0.95


def helm_wheel(name, cx, cy, cz):
    """Navy rim + white six-spoke hub (axle along X); flat aft face prints face-down."""
    h = WHEEL_T/2
    rim_prof = [(-0.48, -h), (0.48, -h), (0.48, 0.15), (0.32, 0.45), (0.0, h),
                (-0.32, 0.45), (-0.48, 0.15)]
    rim = revolve_x(name, cx, cy, cz, WHEEL_R-0.48, rim_prof, 64)
    hub = rod_x(name+"Hub", cx-h, cx+h, cy, cz, 1.25, 28)
    for i in range(6):
        a = math.pi/2+2*math.pi*i/6
        dy, dz = math.cos(a), math.sin(a)
        py, pz = -dz*0.4, dy*0.4
        poly = [(cy+0.9*dy+py, cz+0.9*dz+pz), (cy+(WHEEL_R-0.75)*dy+py, cz+(WHEEL_R-0.75)*dz+pz),
                (cy+(WHEEL_R-0.75)*dy-py, cz+(WHEEL_R-0.75)*dz-pz), (cy+0.9*dy-py, cz+0.9*dz-pz)]
        G.boolean(hub, prism_x(name+"Spoke", poly, cx-h, cx+0.3), "UNION")
    G.boolean(hub, rod_x(name+"Axle", cx+h-0.05, cx+h+STUB_L, cy, cz, STUB_R, 24), "UNION")
    G.boolean(hub, dup(rim, name+"RimCut"), "DIFFERENCE")
    return rim, hub


def binnacle(name, x_aft, y, z_sole):
    rings = []
    for z, dx, dy in ((z_sole-1.2, 3.4, 3.6), (z_sole+0.5, 3.0, 3.0), (z_sole+1.4, 2.4, 2.4), (19.6, 2.4, 2.4),
                      (20.7, 3.4, 3.6), (WHEEL_Z+1.9, 3.4, 3.8), (WHEEL_Z+2.5, 3.0, 3.4)):
        rings.append([(px, py, z) for px, py in rrect(x_aft, x_aft+dx, y-dy/2, y+dy/2, 0.9, 6)])
    return rings_solid(name, rings)


def teardrop(cx, cz, r, n=20):
    """Hole outline in a vertical plane: round with a 45-degree peak so it prints unsupported."""
    pts = []
    for k in range(n+1):
        a = math.radians(45-270*k/n)
        pts.append((cx+r*math.cos(a), cz+r*math.sin(a)))
    pts.append((cx, cz+r*math.sqrt(2)))
    return pts


def padeye(name, x, y, z, along="x", hole_r=0.55):
    """Upright tab with a threadable teardrop hole; `along` is the tab's long axis."""
    zb, zc = z-0.5, z+1.45
    tab = [(-1.35, zb), (1.35, zb)]+[(1.35*math.cos(math.pi*k/12), zc+1.35*math.sin(math.pi*k/12)) for k in range(13)]
    tab[-1] = (-1.35, zc)
    if along == "x":
        ob = prism(name, [(x+s, zz) for s, zz in tab], "y", y-0.5, y+0.5)
        hole = prism(name+"H", [(x+s, zz) for s, zz in teardrop(0.0, zc, hole_r)], "y", y-1.5, y+1.5)
    else:
        ob = prism_x(name, [(y+s, zz) for s, zz in tab], x-0.5, x+0.5)
        hole = prism_x(name+"H", [(y+s, zz) for s, zz in teardrop(0.0, zc, hole_r)], x-1.5, x+1.5)
    G.boolean(ob, rbox(name+"Pad", x-1.8, x+1.8, y-1.25, y+1.25, z-0.5, z+0.3, 0.6)
              if along == "x" else rbox(name+"Pad", x-1.25, x+1.25, y-1.8, y+1.8, z-0.5, z+0.3, 0.6), "UNION")
    G.boolean(ob, hole, "DIFFERENCE")
    return ob


CLEAT_FLANGE = (1.5, 0.8, 0.32, 0.4)             # half-length, half-width, height above deck, plan radius


def cleat(name, x, y, z, g=0.0):
    """Fore-aft horn cleat (rev 11): 4.2 long, 1.2 wide, top 2.72 above the deck (17 layers); a straight pedestal of
    +-0.75 up to 0.88 (a visible waist) and horns whose undersides rise at 45 deg to 0.3-0.5 mm tips, so there is
    daylight under each horn and no
    supports when the upper hull prints deck-up. Sits on a 3.0 x 1.6 x 0.32 flange buried 0.25 mm. `g` grows the
    whole fitting (the navy ink tool copy, as for the anchor)."""
    prof = [(-0.75, -0.25), (0.75, -0.25), (0.75, 0.88), (1.95, 2.08), (2.1, 2.20), (2.1, 2.50), (1.8, 2.68),
            (0.6, 2.72), (-0.6, 2.72), (-1.8, 2.68), (-2.1, 2.50), (-2.1, 2.20), (-1.95, 2.08), (-0.75, 0.88)]
    if g:
        n = len(prof); grown = []
        for i, (px, pz) in enumerate(prof):                 # mitred outward offset of the CCW profile
            ax, az = prof[i-1]; bx, bz = prof[(i+1) % n]
            n1 = (pz-az, -(px-ax)); n2 = (bz-pz, -(bx-px))
            n1 = [c/math.hypot(*n1) for c in n1]; n2 = [c/math.hypot(*n2) for c in n2]
            m = (n1[0]+n2[0], n1[1]+n2[1]); L = math.hypot(*m); m = (m[0]/L, m[1]/L)
            k = g/max(0.3, m[0]*n1[0]+m[1]*n1[1])
            grown.append((px+m[0]*k, pz+m[1]*k))
        prof = grown
    ob = prism(name, [(x+s, z+zz) for s, zz in prof], "y", y-0.6-g, y+0.6+g)
    fl, fw, fh, fr = CLEAT_FLANGE
    G.boolean(ob, pad(name+"Flange", x-fl-g, x+fl+g, y-fw-g, y+fw+g, z-0.25-g, z+fh+g, fr+g, 0.12), "UNION")
    return ob


def winch(name, x, y, z):
    return lathe(name, x, y, [(1.45, z-0.3), (1.45, z+0.35), (1.15, z+0.55), (1.05, z+1.25),
                              (1.32, z+1.35), (1.32, z+1.6), (1.0, z+1.8), (0.45, z+1.95)], 32)


def hatch(name, x, y, lx, ly, zfun, frame=0.85, rise=0.48, r=1.2):
    """Raised locally-level hatch frame with a recessed lens; returns (frame, recess, lens)."""
    zs_ = [zfun(x+dx*lx/2, y+dy*ly/2) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
    top = max(zs_)+rise
    fr = rbox(name, x-lx/2, x+lx/2, y-ly/2, y+ly/2, min(zs_)-0.8, top, r)
    rec = rbox(name+"Rec", x-lx/2+frame, x+lx/2-frame, y-ly/2+frame, y+ly/2-frame,
               top-0.16, top+3.0, max(r-frame, 0.3))
    lens = rbox(name+"Lens", x-lx/2+frame, x+lx/2-frame, y-ly/2+frame, y+ly/2-frame,
                top-0.16-0.48, top-0.16+0.02, max(r-frame, 0.3))
    return fr, rec, lens


BULB_TAIL_T, BULB_TAIL_C = 0.90, 0.0275   # NACA truncated at 90 % chord, elliptical round tail cap


def _naca24(w):
    return 5*0.24*(0.2969*math.sqrt(w)-0.1260*w-0.3516*w*w+0.2843*w**3-0.1036*w**4)


def bulb_factor(u):
    u = min(max(u, 0.0), 1.0)
    w = u*(BULB_TAIL_T+BULB_TAIL_C)
    fmax = _naca24(0.30)
    if w <= BULB_TAIL_T:
        f = _naca24(w)/fmax
    else:
        f = _naca24(BULB_TAIL_T)/fmax*math.sqrt(max(0.0, 1.0-((w-BULB_TAIL_T)/BULB_TAIL_C)**2))
    return max(0.02, f)


BULB_L, BULB_HW, BULB_HH, BULB_ZC = 64.0, 8.6, 8.0, -48.75
BULB_SPLIT, BULB_WALL = -45.0, 0.9
BULB_FLAT = BULB_ZC-BULB_HH+1.3
BULB_FLOOR = BULB_FLAT+0.9


def bulb_rings(xc, inset=0.0, n_u=72, n_a=64, u_lim=None):
    """Torpedo with the blunt NACA nose forward and both ends closing on the section centreline."""
    xb = xc+BULB_L/2
    out = []
    for i in range(n_u+1):
        u = 0.5*(1.0-math.cos(math.pi*i/n_u))
        if u_lim:
            u = u_lim[0]+(u_lim[1]-u_lim[0])*i/n_u
        f = bulb_factor(u)
        hw, hh = BULB_HW*f-inset, BULB_HH*f-inset
        out.append((xb-BULB_L*u, f, hw, hh))
    return out


def bulb_outer(name, xc):
    rings = []
    for x, f, hw, hh in bulb_rings(xc):
        rings.append([(x, hw*math.sin(2*math.pi*k/64), BULB_ZC+hh*math.cos(2*math.pi*k/64)) for k in range(64)])
    return rings_solid(name, rings)


def bulb_cavity_range():
    us = [k/400 for k in range(401)]
    ok = [u for u in us if BULB_HH*bulb_factor(u)-BULB_WALL >= (BULB_SPLIT-BULB_ZC)+0.55]
    return min(ok), max(ok)


def bulb_cavity(name, xc):
    """Open-topped shot well: the inset torpedo clipped just above the glue plane."""
    zt = BULB_SPLIT+0.8
    rings = []
    for x, f, a, b in bulb_rings(xc, BULB_WALL, 60, 40, bulb_cavity_range()):
        sec = []
        for k in range(49):
            t = 2*math.pi*k/48
            y, z = a*math.sin(t), BULB_ZC-b*math.cos(t)
            sec.append((y, max(min(z, zt), BULB_FLOOR)))
        pts = []
        for p in sec:
            if not pts or abs(p[0]-pts[-1][0]) > 1e-4 or abs(p[1]-pts[-1][1]) > 1e-4:
                pts.append(p)
        if abs(pts[0][0]-pts[-1][0]) < 1e-4 and abs(pts[0][1]-pts[-1][1]) < 1e-4:
            pts.pop()
        rings.append([(x, y, z) for y, z in pts])
    n = min(len(r) for r in rings)
    if any(len(r) != n for r in rings):
        raise RuntimeError("cavity ring sizes differ")
    return rings_solid(name, rings)


# ---------------------------------------------------------------- hull lofts with cambered deck
def loft_deck(name, xs, n, inset, drop, k=41, bumps=None):
    rings = []
    for x in xs:
        hs, _ = G.half_section(H, x, n, inset, bumps=bumps)
        f = (lambda y: deck_z(x, y)-drop)
        out = [hs[0]]
        for p, q in zip(hs, hs[1:]):
            if q[1] < f(q[0]):
                out.append(q); continue
            g0 = p[1]-f(p[0]); g1 = q[1]-f(q[0])
            t = g0/(g0-g1) if g0 != g1 else 1.0
            out.append((p[0]+(q[0]-p[0])*t, p[1]+(q[1]-p[1])*t))
            break
        if len(out) != n:
            s = [0.0]
            for p, q in zip(out, out[1:]):
                s.append(s[-1]+math.dist(p, q))
            rs = []; j = 0
            for i in range(n):
                u = i/(n-1)
                tg = s[-1]*(u-0.75*math.sin(math.pi*u)/math.pi)
                while j < len(out)-2 and s[j+1] < tg:
                    j += 1
                t = (tg-s[j])/max(s[j+1]-s[j], 1e-12)
                rs.append((out[j][0]+(out[j+1][0]-out[j][0])*t, out[j][1]+(out[j+1][1]-out[j][1])*t))
            rs[0] = (0.0, rs[0][1]); out = rs
        Be = out[-1][0]
        ring = [(-y, z) for (y, z) in reversed(out)]+[(y, z) for (y, z) in out[1:]]
        for j in range(1, k+1):
            y = Be-2*Be*j/(k+1)
            ring.append((y, f(y)))
        rings.append([(x, y, z) for y, z in ring])
    return rings_solid(name, rings)


# ---------------------------------------------------------------- coachroof
CR_XA, CR_XF, CR_RC, CRC = -38.5, 45.2, 4.0, 1.1
CR_RAKE = 1.356
CR_ZA = deck_z(CR_XA, 0)
WP = pchip([(-38.5, 18.5), (-34.0, 18.5), (-15, 18.4), (5, 18.0), (15, 16.8), (26, 14.5), (36, 11.8)])
CR_NOSE_X, CR_NOSE_A, CR_NOSE_B = 33.0, 12.5, 12.15   # elliptical plan nose ahead of x 36
RT = pchip([(-36.0, 23.0), (-15, 22.9), (5, 22.7), (26, 22.4), (36, 21.9), (40.5, 21.1), (43.5, 19.9),
            (CR_XF, deck_z(CR_XF, 0)+0.3)])


def cr_w(x):
    if x < CR_XA+CR_RC:
        dx = x-(CR_XA+CR_RC)
        return 20.5-CR_RC+math.sqrt(max(CR_RC**2-dx*dx, 0.0))
    if x > 36.0:
        return CR_NOSE_B*math.sqrt(max(1.0-((x-CR_NOSE_X)/CR_NOSE_A)**2, 0.0))
    return pc(WP, x)


def cr_profile(x, d, zb_drop):
    w0 = cr_w(x); w = w0-d
    zde = deck_z(x, w0)
    raked = CR_ZA+(x-CR_XA)*CR_RAKE
    rtd = smin(pc(RT, x)-d, raked-d*math.sqrt(1+CR_RAKE**2), 1.4)
    W = max(w, 0.5)
    z = rtd-CRC
    for _ in range(50):
        y = w-(z-zde)*T6
        z = rtd-CRC*(y/W)**2
    yc, zc = y, z
    zb = deck_z(x, 0)-zb_drop
    r = max(0.05, min(1.4, 0.45*(zc-zb), 0.35*yc))
    yA = yc-r
    roof = [(yA*i/10, rtd-CRC*(yA*i/10/W)**2) for i in range(11)]
    sl = math.hypot(T6, 1.0)
    Bp = (yc+r*T6/sl, zc-r/sl)
    A = roof[-1]
    fil = []
    for i in range(1, 8):
        t = i/8
        fil.append(((1-t)**2*A[0]+2*(1-t)*t*yc+t*t*Bp[0], (1-t)**2*A[1]+2*(1-t)*t*zc+t*t*Bp[1]))
    side = [Bp]+[(w-(zz-zde)*T6, zz) for zz in [Bp[1]-(Bp[1]-zb)*i/6 for i in range(1, 7)]]
    half = roof+fil+side
    return [(-y, z) for (y, z) in reversed(half)]+[(y, z) for (y, z) in half[1:]], (yc, zc, zde)


def cr_stations(x0, x1):
    xs = [CR_XA+CR_RC-CR_RC*math.cos(math.radians(90*i/18)) for i in range(19)]
    xs = [x for x in xs if x >= x0]
    if xs[0] > x0:
        xs.insert(0, x0)
    x = xs[-1]+1.0
    while x < x1-0.6:
        xs.append(x); x += 1.0 if x < 34 else 0.5
    xs.append(x1)
    return xs


def coachroof(name, d, zb_drop, x0=None, x1=None):
    x0 = CR_XA if x0 is None else x0
    x1 = CR_XF if x1 is None else x1
    rings = []
    for x in cr_stations(x0, x1):
        prof, _ = cr_profile(x, d, zb_drop)
        rings.append([(x, y, z) for y, z in prof])
    return rings_solid(name, rings)


def cr_band(name, d_out, d_in):
    b = coachroof(name, d_out, 2.5)
    G.boolean(b, coachroof(name+"i", d_in, 8.0), "DIFFERENCE")
    return b


def window_band(x):
    _, (yc, zc, zde) = cr_profile(x, 0.0, 3.0)
    h = zc-zde
    hw = 4.0+(2.2-4.0)*(x+34)/60.0
    zm = zde+0.56*h
    return zm-hw/2, zm+hw/2


def window_poly(x0, x1, round_a, round_f, g=0.0):
    def band(x):
        lo, hi = window_band(min(max(x, x0), x1))
        return lo-g, hi+g
    ra = (band(x0)[1]-band(x0)[0])/2 if round_a else 0.0
    rf = (band(x1)[1]-band(x1)[0])/2 if round_f else 0.0
    xa = x0+ra if round_a else x0-g
    xb = x1-rf if round_f else x1+g
    xs = [xa+(xb-xa)*i/30 for i in range(31)]
    pts = [(x, band(x)[0]) for x in xs]
    if round_f:
        zl, zh = band(xb); zm = (zl+zh)/2; r = (zh-zl)/2
        pts += [(xb+r*math.sin(math.pi*k/12), zm-r*math.cos(math.pi*k/12)) for k in range(1, 12)]
    pts += [(x, band(x)[1]) for x in reversed(xs)]
    if round_a:
        zl, zh = band(xa); zm = (zl+zh)/2; r = (zh-zl)/2
        pts += [(xa-r*math.sin(math.pi*k/12), zm+r*math.cos(math.pi*k/12)) for k in range(1, 12)]
    return pts


WINDEF = [(-34.0, -14.35, True, False), (-13.65, 5.65, False, False), (6.35, 26.0, False, True)]


def roof_z(x, y):
    w0 = cr_w(x)
    raked = CR_ZA+(x-CR_XA)*CR_RAKE
    rtd = smin(pc(RT, x), raked, 1.4)
    return rtd-CRC*(y/max(w0, 0.5))**2


# ---------------------------------------------------------------- rig
MAST_HEEL, MAST_TOP = -3.0, 240.0
MAST_XA = X_MAST-1.9          # flat aft face = print face; D-shaped heel keys the socket
GOOSE_Z = 43.0                # top of the gooseneck saddle; boom sits on it


MAST_D0, MAST_W0, MAST_D1, MAST_W1 = 3.6, 2.6, 2.2, 1.7


def mast_dw(z):
    t = min(max((z-30.0)/(MAST_TOP-30.0), 0.0), 1.0)
    return MAST_D0+(MAST_D1-MAST_D0)*t, MAST_W0+(MAST_W1-MAST_W0)*t


def mast_section(d, w, off=0.0, nf=16, nc=5):
    a = w/2+off; rc = 0.45+0.5*off; xa = MAST_XA-off; xc = MAST_XA+d-w/2
    pts = []
    for k in range(nc+1):
        t = math.radians(180+90*k/nc)
        pts.append((xa+rc+rc*math.cos(t), -a+rc+rc*math.sin(t)))
    for k in range(nf+1):
        t = math.radians(-90+180*k/nf)
        pts.append((xc+a*math.cos(t), a*math.sin(t)))
    for k in range(nc+1):
        t = math.radians(90+90*k/nc)
        pts.append((xa+rc+rc*math.cos(t), a-rc+rc*math.sin(t)))
    return pts


def mast_prism(name, off, z0, z1):
    d, w = mast_dw(z0)
    return prism(name, mast_section(d, w, off), "z", z0, z1)


def window_solids(prefix, d_out, d_in, g=0.0):
    out = []
    for i, (a, b, ra, rf) in enumerate(WINDEF):
        t = prism(prefix+str(i), window_poly(a, b, ra, rf, g), "y", -40, 40)
        G.boolean(t, cr_band(prefix+"b%d" % i, d_out, d_in), "INTERSECT")
        out.append(t)
    return out


# ================================================================== build
log("outer loft")
xs_out = stations(P["x_aft"], P["x_stem"]-0.2, 180)
outer = loft_deck("Outer", xs_out, 96, 0.0, 0.0)
G.cut_plane(outer, *G.transom_plane(P, 0.0))
HULL_X0 = min(v.co.x for v in outer.data.vertices)
HULL_X1 = max(v.co.x for v in outer.data.vertices)
stats(outer)

probe = dup(outer, "probe")
G.boolean(probe, half_space("uw", -80, 0.0), "INTERSECT")
bm = bmesh.new(); bm.from_mesh(probe.data)
bmesh.ops.triangulate(bm, faces=bm.faces)
vol = 0.0; mx = 0.0
for f in bm.faces:
    a, b, c = (v.co for v in f.verts)
    v6 = a.dot(b.cross(c))
    vol += v6/6; mx += v6*(a.x+b.x+c.x)/24
bm.free()
LCB = mx/vol if vol else 0
log("canoe displaced cm3 %.3f  LCB x %.2f" % (vol/1000, LCB))
bpy.data.objects.remove(probe)

DISPLACEMENT_CURVE = {}
for wl in (0.0, 1.0, 2.0, 3.0, 4.0, 5.0):
    p = dup(outer, "DWL_%s" % str(wl).replace(".", "_"))
    G.boolean(p, half_space("DWLClip", -80.0, wl), "INTERSECT")
    DISPLACEMENT_CURVE[wl] = G.mesh_stats(p)["vol_cm3"]
    bpy.data.objects.remove(p, do_unlink=True)
log("hull displacement curve cm3 before final LOA scale", DISPLACEMENT_CURVE)

# open stern: full-width bathing platform at z 4.5 below a plumb upper transom at x -86
PLAT_Z, PLAT_XF = 4.5, -86.0
PLAT_XA = P["transom"]["knuckle"][0]+(PLAT_Z-P["transom"]["knuckle"][1])*(
    (P["transom"]["top"][0]-P["transom"]["knuckle"][0])/(P["transom"]["top"][1]-P["transom"]["knuckle"][1]))
TREAD_Z, TREAD_XF, PASS_HW = 7.4, -82.5, 8.0
HELM_Z = 14.0
add = []
for side in (1, -1):
    rings = []
    for x in stations(-86.5, 94.0, 170, 0.3):
        B = hb(x); z = zs(x)
        yo = B-0.05; yi = max(B-0.85, 0.0)
        taper = min(1.0, max(0.0, (x+86.5)/3.0), max(0.0, (94.0-x)/3.0))
        z0, z1 = z-0.6, z+0.48*taper
        prof = [(yi, z0), (yo, z0), (yo, z1-0.18), (yo-0.05, z1-0.05),
                (yo-0.18, z1), (yi+0.12, z1), (yi, z1-0.12)]
        rings.append([(x, side*y, zz) for y, zz in (prof if side > 0 else list(reversed(prof)))])
    add.append(rings_solid("Toe%d" % side, rings))
for side in (1, -1):
    add.append(coaming_solid(side))
add.append(coachroof("CR_outer", 0.0, 2.5))
roof_mast = pc(RT, X_MAST)
add.append(prism("MastCollar", stadium(X_MAST, 0, 7.4, 6.0), "z", roof_mast-1.5, roof_mast+0.8))
ZB = deck_z(94.0, 0.0)
# printed rig (rev 10): no thread padeyes. Chainplate blocks with funnel pockets take the feet of the printed
# mast + shroud frame; a stemhead block with a pocket on the stay axis takes the foot tab of the printed furler.
CHAIN_Y, CHAIN_X = 26.0, MAST_XA+0.6           # rev 11: outboard, 2.2 mm inside the toe rail (was 17.6, by the coachroof)
TAB_W, TAB_L = 1.2, 2.4                        # frame-foot tab section (x and y) and length
CHAIN_H, CHAIN_BOSS = 1.4, 1.4                 # block height above the deck; solid boss below the deck
CHAIN_SEAT = (TAB_W+0.4, TAB_W+0.6)            # pocket seat x, y: 0.2 / 0.3 clearance per side (rev10 r2)
CHAIN_DEPTH = TAB_L+0.1                        # pocket depth below the block top (tab bottom 0.5 above the floor)
CHAINPLATES = []
for s in (1, -1):
    _y = s*CHAIN_Y
    _z = deck_z(CHAIN_X, _y)
    add.append(pad("Chainplate%d" % s, CHAIN_X-1.8, CHAIN_X+1.8, _y-1.6, _y+1.6, _z-0.5, _z+CHAIN_H, 0.9, 0.35))
    CHAINPLATES.append((CHAIN_X, _y, _z, _z+CHAIN_H))
SH_X, SH_TOP = 90.0, ZB+1.5                    # stemhead block: the furler axis meets its top at (SH_X, SH_TOP)
add.append(pad("Stemhead", SH_X-1.6, SH_X+1.8, -1.7, 1.7, deck_z(SH_X, 0.0)-0.5, SH_TOP, 0.8, 0.3))
_dt, _wt = mast_dw(MAST_TOP)
CAP_TOP, CAP_XA, CAP_XF = MAST_TOP+0.6, MAST_XA, MAST_XA+_dt+0.45
HOOK_STOCK, HOOK_CLR, HOOK_LEG = 1.0, 0.375, 1.2  # rev10 r2: measured min ~0.35 (reviewers: >=0.25, <=0.45)
HOOK_B = (CAP_XF+HOOK_CLR+HOOK_STOCK/2, CAP_TOP-1.6)  # the furler's straight run ends here, in front of the cap
FURL_A = (SH_X, SH_TOP)
_d = (HOOK_B[0]-FURL_A[0], HOOK_B[1]-FURL_A[1])
FURL_L = math.hypot(*_d)
FURL_T = (_d[0]/FURL_L, _d[1]/FURL_L)          # unit axis, stemhead -> masthead
FURL_N = (FURL_T[1], -FURL_T[0])               # in-plane normal (points forward)
FURL_Y0 = -0.6                                 # flat (print-bed) face of the furler, y = const
FTAB_A, FTAB_H, FURL_DRUM_S = 0.55, 1.1, 1.0   # foot tab half-width / thickness; drum bottom 1 mm above the block
FPOCKET = (FTAB_A+0.2, FURL_Y0-0.2, FURL_Y0+FTAB_H+0.2, 4.0)   # seat half-width, y0, y1, depth along the axis


def funnel(name, cx, cy, seat, mouth, z_floor, z_top, flare=0.6):
    """Vertical pocket: seat (x, y) from the floor to z_top-flare, opening to `mouth` just above z_top."""
    rings = []
    for z_, (lx, ly) in ((z_floor, seat), (z_top-flare, seat), (z_top+0.3, mouth)):
        rings.append([(px, py, z_) for px, py in rrect(cx-lx/2, cx+lx/2, cy-ly/2, cy+ly/2, 0.2, 4)])
    return rings_solid(name, rings)


def axis_solid(name, segs, A=FURL_A, t=FURL_T, n=FURL_N):
    """Rectangular sections (s, half-width along n, y0, y1) swept along an inclined axis in the x-z plane."""
    rings = []
    for s_, a_, y0_, y1_ in segs:
        cx, cz = A[0]+t[0]*s_, A[1]+t[1]*s_
        rings.append([(cx+n[0]*u_, yy, cz+n[1]*u_) for u_, yy in ((-a_, y0_), (a_, y0_), (a_, y1_), (-a_, y1_))])
    return rings_solid(name, rings)


BOW_TIP = 99.6
CHEEK_X1 = 98.3                                # cheeks stop ~1.5 mm aft of the anchor crown
ROLLER = (97.4, ZB+0.9, 0.72)                  # x, z, r
# fitting: plank + chin web (|y| <= 1.2), open slot under the roller, white cheeks at |y| 1.15-1.8
bow = prism("BowFitting", [(88.5, ZB-0.7), (95.6, ZB-0.7), (95.6, ZB-3.2), (96.3, ZB-3.2), (CHEEK_X1, ZB-1.2),
                           (CHEEK_X1, ZB-0.35), (96.95, ZB-0.35), (96.65, ZB+0.55), (88.5, ZB+0.55)], "y", -1.2, 1.2)
G.boolean(bow, pad("BowFittingPad", 88.5, 95.0, -1.2, 1.2, ZB-0.7, ZB+0.55, 0.6, 0.3), "UNION")
_cheek = [(94.0, ZB-0.7), (95.6, ZB-0.7), (95.6, ZB-3.2), (96.3, ZB-3.2), (CHEEK_X1, ZB-1.2)]
_cheek += [(CHEEK_X1-0.6+0.6*math.cos(math.radians(a_)), ZB+1.0+0.6*math.sin(math.radians(a_))) for a_ in range(0, 91, 15)]
_cheek += [(94.8, ZB+1.6), (94.0, ZB+0.8)]
for s_ in (1, -1):
    G.boolean(bow, prism("RollerCheek", _cheek, "y", *sorted((s_*1.15, s_*1.8))), "UNION")
G.boolean(bow, rod_y("BowRoller", ROLLER[0], -1.3, 1.3, ROLLER[1], ROLLER[2], 28), "UNION")
G.boolean(bow, pad("AnchorChock", 92.75, 93.85, -0.4, 0.4, ZB+0.3, ZB+0.75, 0.2, 0.1), "UNION")
add.append(bow)

# stowed delta anchor, a separate-looking navy object: 1.0 mm shank over the roller between the cheeks (0.65 mm
# daylight each side), resting only on the roller (saddle) and, via its D-ring shackle, on a white deck chock;
# 0.9 mm air under the shank. The fluke hangs ahead of the 45-degree chin with a shadow gap and touches the stem
# only with its toe pad (which starts its print); the navy crown stands ~1.5 mm proud of the cheeks.
from mathutils.bvhtree import BVHTree
_bvh = BVHTree.FromPolygons([v.co.copy() for v in outer.data.vertices], [tuple(p.vertices) for p in outer.data.polygons])


def stem_x(z):
    hit = _bvh.ray_cast(Vector((130.0, 0.0, z)), Vector((-1.0, 0.0, 0.0)))
    return hit[0].x if hit[0] is not None else None


R2 = math.sqrt(0.5)
FL_OT, FL_OB, FL_RIDGE, FL_W, FL_DIH, FL_U1 = 0.75, 1.55, 0.45, 2.5, 0.3, 2.4
ANCH_X1 = 99.82
SHACKLE = (93.3, ZB+1.6, 0.7, 0.3)             # centre x, z, major and minor radius: OD 2.0, hole 0.8


def fluke_pt(u, o, y):
    return (96.3+u+o*R2, y, ZB-3.2+u-o*R2)


ANCHOR_U0 = 0.0
while ANCHOR_U0 > -6.0:
    bx, _, bz = fluke_pt(ANCHOR_U0, FL_OT, 0.0)
    sx = stem_x(bz)
    if sx is not None and bx < sx-0.45:
        break
    ANCHOR_U0 -= 0.05
log("anchor toe u", round(ANCHOR_U0, 2), "stem x at toe", round(stem_x(fluke_pt(ANCHOR_U0, FL_OT, 0)[2]) or -1, 2),
    "stem x at fitting chin", round(stem_x(ZB-3.2) or -1, 2), "fluke length mm", round((FL_U1-ANCHOR_U0)*math.sqrt(2), 2))


def anchor(name, g=0.0):
    p_in, p_out = fluke_pt(FL_U1-0.4, FL_OT+0.15, 0.0), fluke_pt(FL_U1-0.4, FL_OB+0.1, 0.0)
    sh = prism(name+"Shank", [(93.95-g, ZB+1.45-g), (98.5, ZB+1.45-g), (98.8-g, ZB+1.15), (p_in[0]-g, p_in[2]),
                              (p_out[0], p_out[2]-g), (ANCH_X1+g, ZB+1.5), (99.6+g, ZB+2.1+g), (99.15, ZB+2.4+g),
                              (96.0, ZB+2.3+g), (94.4, ZB+2.1+g), (93.95-g, ZB+1.8)], "y", -0.5-g, 0.5+g)
    G.boolean(sh, torus_y(name+"Shackle", SHACKLE[0], 0.0, SHACKLE[1], SHACKLE[2], SHACKLE[3]+g, 32, 12), "UNION")
    rings = []
    NR = 30
    uM = FL_U1-0.8
    for k in range(NR+1):
        u = ANCHOR_U0+(FL_U1-ANCHOR_U0)*k/NR
        w = 0.5+(FL_W-0.5)*(u-ANCHOR_U0)/(uM-ANCHOR_U0) if u <= uM else FL_W-(FL_W-1.6)*((u-uM)/(FL_U1-uM))**2
        w += g
        t = (u-ANCHOR_U0)/(FL_U1-ANCHOR_U0)
        rh = max(0.0, FL_RIDGE*min(1.0, t/0.3, (1.0-t)/0.25))
        rw = min(0.55, 0.8*w)
        dd = FL_DIH*w/FL_W
        ot, ob = FL_OT-g, FL_OB+g
        prof = [(-w, ot-dd), (0.0, ot), (w, ot-dd), (w, ob-dd), (rw, ob-dd*rw/w), (0.55*rw, ob+rh),
                (-0.55*rw, ob+rh), (-rw, ob-dd*rw/w), (-w, ob-dd)]
        # grow the end caps too, or the ink tool's caps are coplanar with the anchor's and leave a white skin
        uu = u-g if k == 0 else (u+g if k == NR else u)
        rings.append([fluke_pt(uu, o, y) for y, o in prof])
    G.boolean(sh, rings_solid(name+"Fluke", rings), "UNION")
    sh.name = name
    return sh


add.append(anchor("Anchor"))
CLEATS = [(79.0, 9.0), (79.0, -9.0), (-30.0, 25.0), (-30.0, -25.0), (-78.6, 23.5), (-78.6, -23.5)]
for i, (x, y) in enumerate(CLEATS):
    add.append(cleat("Cleat%d" % i, x, y, deck_z(x, y)))
WINCHES = [(-46.0, 20.0, 18.5), (-46.0, -20.0, 18.5),
           (-30.5, 12.0, roof_z(-30.5, 12.0)), (-30.5, -12.0, roof_z(-30.5, -12.0))]
for i, (x, y, z) in enumerate(WINCHES):
    add.append(winch("Winch%d" % i, x, y, z))
CLUTCHES = []
for s in (1, -1):
    z = roof_z(-25.5, s*12.0)
    CLUTCHES.append((-25.5, s*12.0, z+0.75))
    add.append(pad("Clutch%d" % s, -27.0, -24.0, s*12.0-1.6, s*12.0+1.6, z-0.5, z+0.75, 0.4, 0.2))
# companionway: smoked slider between rails, garage forward, washboards below
SLIDER = (-33.8, -26.6, -4.8, 4.8)
slider_top = max(roof_z(x, y) for x in (-33.8, -30.0, -26.6) for y in (-4.8, 0.0, 4.8))+0.45
add.append(pad("Slider", *SLIDER, slider_top-1.2, slider_top, 1.0, 0.2))
for s in (1, -1):
    y0, y1 = (4.6, 5.4) if s > 0 else (-5.4, -4.6)
    add.append(pad("SliderRail%d" % s, -34.2, -21.0, y0, y1, slider_top-1.4, slider_top+0.25, 0.35, 0.15))
GARAGE_TOP = max(roof_z(x, y) for x in (-26.6, -21.0) for y in (-6.4, 0.0, 6.4))+1.05
add.append(pad("Garage", -26.6, -20.6, -6.4, 6.4, GARAGE_TOP-2.0, GARAGE_TOP, 1.4, 0.55))
TRAV_X = -17.0
trav_z = max(roof_z(TRAV_X, y) for y in (-8.5, 0.0, 8.5))
TRAV_TOP = trav_z+0.7
add.append(pad("Traveller", TRAV_X-0.8, TRAV_X+0.8, -8.5, 8.5, trav_z-0.9, TRAV_TOP, 0.6, 0.2))
add.append(pad("TravCar", TRAV_X-1.3, TRAV_X+1.3, -1.3, 1.3, TRAV_TOP-0.3, TRAV_TOP+0.45, 0.5, 0.15))
add.append(padeye("SheetEye", TRAV_X, 0.0, TRAV_TOP+0.45, "x", 0.5))
SHEET_EYE = (TRAV_X, 0.0, TRAV_TOP+0.45+1.45)
HATCHES = [("HatchSaloon", -10.5, 0.0, 9.0, 8.0, roof_z), ("HatchCabP", 7.0, 5.6, 6.0, 5.0, roof_z),
           ("HatchCabS", 7.0, -5.6, 6.0, 5.0, roof_z), ("HatchFwdRoof", 34.5, 0.0, 6.5, 6.0, roof_z),
           ("HatchForedeck", 63.5, 0.0, 10.0, 9.0, deck_z)]
HATCH_RECESS, HATCH_LENS = [], []
for nm, x, y, lx, ly, fn in HATCHES:
    fr, rec, lens = hatch(nm, x, y, lx, ly, fn)
    add.append(fr); HATCH_RECESS.append(rec); HATCH_LENS.append(lens)
NONSKID_H, NS_MARGIN = 0.2, 1.5


def deck_panel(name, side, x0, x1, y_in, y_out, n=90):
    rings = []
    for x in stations(x0, x1, n, 0.0):
        yi, yo = y_in(x), y_out(x)
        ys = [yi+(yo-yi)*k/10 for k in range(11)]
        prof = [(y, deck_z(x, y)+NONSKID_H) for y in ys]+[(y, deck_z(x, y)-0.35) for y in reversed(ys)]
        rings.append([(x, side*y, z) for y, z in (prof if side > 0 else list(reversed(prof)))])
    return rings_solid(name, rings)


def toe_in(x):
    return hb(x)-0.85-NS_MARGIN


HATCH_FD = (63.5, 0.0, 10.0, 9.0)


def handrail_y(x):
    return cr_profile(x, 0.0, 3.0)[1][0]-1.7


HANDRAIL_X = (-21.0, 14.0)


def handrail(name, side, grow=0.0, zlo=-0.4, top=0.8, n=60):
    rings = []
    for x in stations(HANDRAIL_X[0]-grow, HANDRAIL_X[1]+grow, n, 0.0):
        y = handrail_y(x)
        end = min(1.0, (x-HANDRAIL_X[0]+grow)/1.2+0.25, (HANDRAIL_X[1]+grow-x)/1.2+0.25)
        prof = []
        for yy, zz in ((y-0.4-grow, zlo), (y+0.4+grow, zlo), (y+0.4+grow, top*end), (y-0.4-grow, top*end)):
            prof.append((yy, roof_z(x, yy)+zz))
        rings.append([(x, side*yy, zz) for yy, zz in (prof if side > 0 else list(reversed(prof)))])
    return rings_solid(name, rings)


for side in (1, -1):
    add.append(handrail("Handrail%d" % side, side))
for addition in add:
    addition_name = addition.name
    stats(addition)
    log("addition selfx", addition_name, len(selfx(addition)))
    G.boolean(outer, addition, "UNION")
    union_stats = G.mesh_stats(outer)
    log("union result", addition_name, union_stats)
    if union_stats["nonmanifold"]:
        bm = bmesh.new(); bm.from_mesh(outer.data)
        bad = [e for e in bm.edges if not e.is_manifold]
        for edge in bad[:3]:
            log("bad edge", addition_name, tuple(tuple(round(c, 4) for c in v.co) for v in edge.verts),
                "faces", len(edge.link_faces))
        bm.free()
stats(outer)

VOIDS = [
    (-77.0, -63.5, 21.0, 10.25, 3.0),
    (-66.0, -38.6, 10.0, 10.3, 2.0),
    (-83.0, -70.0, PASS_HW, 10.3, 1.5),
    (-100.0, -75.5, 21.0, HELM_Z, 2.0),
    (-100.0, TREAD_XF, PASS_HW, TREAD_Z, 1.0),
]
cockpit_tools = [
    pocket("Pocket", -77.0, -63.5, 21.0, 21.0, 3.0, 10.25, 60.0, 1.0, 1.2),
    pocket("WellFwd", -66.0, -38.6, 10.0, 10.0, 2.0, 10.3, 60.0, 0.8, 1.5),
    pocket("HelmSeats", -100.0, -75.5, 21.0, 21.0, 2.0, HELM_Z, 60.0, 0.6, 1.0),
    pocket("WellAft", -83.0, -70.0, PASS_HW, PASS_HW, 1.5, 10.3, HELM_Z+0.05, 0.8, 0.8),
    pocket("Passage", -100.0, TREAD_XF, PASS_HW, PASS_HW, 1.0, TREAD_Z, HELM_Z+0.05, 0.6, 0.8),
]
bool_many(outer, cockpit_tools, "DIFFERENCE")
# platform cut with a chamfered nose, plus plan-rounded transom corners
CH = 0.4
stern_cut = prism("SternCut", [(PLAT_XF, 60.0), (PLAT_XF, PLAT_Z), (PLAT_XA+CH, PLAT_Z),
                               (PLAT_XA-0.2, PLAT_Z-CH-0.15), (-110.0, PLAT_Z-CH-0.15), (-110.0, 60.0)], "y", -45.0, 45.0)
CORNER_R = 2.5
Yc = hb(PLAT_XF+CORNER_R)+0.02
for s_ in (1, -1):
    arc = [(PLAT_XF+CORNER_R+CORNER_R*math.cos(math.radians(a)), Yc-CORNER_R+CORNER_R*math.sin(math.radians(a)))
           for a in range(180, 89, -10)]
    poly = [(PLAT_XF-1.0, Yc-CORNER_R)]+arc+[(PLAT_XF+CORNER_R, Yc+6.0), (PLAT_XF-1.0, Yc+6.0)]
    if s_ < 0:
        poly = [(x, -y) for x, y in reversed(poly)]
    G.boolean(stern_cut, prism("TransomCorner", poly, "z", PLAT_Z, 60.0), "UNION")
RAKE_K = 1.6/11.5


def rake(ob):
    for v in ob.data.vertices:
        if v.co.z > PLAT_Z:
            v.co.x += RAKE_K*(v.co.z-PLAT_Z)
    ob.data.update()


rake(stern_cut)
G.boolean(outer, stern_cut, "DIFFERENCE")
LADDER = [(PLAT_XA+0.5, PLAT_XA+5.7, s_*2.3, s_*2.8) for s_ in (1, -1)]
LADDER += [(PLAT_XA+x_-0.25, PLAT_XA+x_+0.25, -2.3, 2.3) for x_ in (1.9, 3.4, 4.9)]
LADDER += [(PLAT_XA+0.45, PLAT_XA+1.15, s_*1.9, s_*3.2) for s_ in (1, -1)]
for i, (x0_, x1_, y0_, y1_) in enumerate(LADDER):
    G.boolean(outer, box_xy("Ladder%d" % i, x0_, x1_, y0_, y1_, PLAT_Z-0.3, PLAT_Z+0.3), "UNION")
log("platform aft x", round(PLAT_XA, 2), "corner y", round(Yc, 2))
BENCH_Z = 15.9
bool_many(outer, [rbox("BenchSeat%d" % s, -63.6, -39.0, *((9.6, 17.9) if s > 0 else (-17.9, -9.6)),
                       BENCH_Z, 60.0, 0.9) for s in (1, -1)], "DIFFERENCE")
bool_many(outer, HATCH_RECESS, "DIFFERENCE")
LID = (78.5, 86.0, -3.6, 3.6)
lid = prism("LidGroove", rrect(*LID, 1.2), "z", deck_z(LID[0], LID[3])-0.3, 40.0)
G.boolean(lid, prism("LidIn", rrect(LID[0]+0.45, LID[1]-0.45, LID[2]+0.45, LID[3]-0.45, 0.8), "z", 0.0, 41.0), "DIFFERENCE")
G.boolean(outer, lid, "DIFFERENCE")
SOLE_Z = 10.3
G.boolean(outer, lathe("RudCounterbore", X_RUD, 0, [(1.6, SOLE_Z-0.7), (1.6, 30.0)], 32), "DIFFERENCE")
for s in (1, -1):
    G.boolean(outer, binnacle("Binnacle%d" % s, BINNACLE_AFT, s*WHEEL_Y, 10.25), "UNION")

# rev 11 railings: two flat-printed navy fences (pulpit + stanchions + lifelines + pushpit side) and two flat
# transom returns. Each post ends in a tab that drops into a pocket in a navy base pad just inside the toe rail.
# Pads are added after the cockpit cuts (the return's inner leg stands on the helm seat).
RAIL_POSTS = [90.0, 82.0, 72.0, 46.0, 18.0, -10.0, -38.0, -64.0, -82.0]
RAIL_IN, RAIL_T = 1.45, 0.68                   # fence centreline inboard of the hull edge; strip thickness (0.2+3x0.16)
RAIL_PAD = (2.45, 0.85, 2.4, 0.35)             # pad: inboard / outboard offset from hb, length along the edge, height
RAIL_POCKET = (0.98, 1.0, 0.004, 1.2)          # width, base length, length growth per mm from the middle post, depth
RAIL_TAB = (0.7, 1.2)                          # tab length, depth: it bottoms on the pocket floor with the post foot
                                               # flush on the pad (the 1.0 post is not wider than the pocket)
SX_EST = 1.0346                                # final x scale, asserted after scaling: pockets are sized in final mm
RET_LEGS = (10.1,)                             # transom-return tabbed leg on the helm seat (rev 11 r2: the outer end
                                               # is a tab-less post glued to the corner post's aft face, one corner)
_bm = bmesh.new(); _bm.from_mesh(outer.data); _bvh = BVHTree.FromBMesh(_bm); _bm.free()


def surf_z(x, y):
    hit = _bvh.ray_cast(Vector((x, y, 80.0)), Vector((0.0, 0.0, -1.0)))
    assert hit[0] is not None, ("no deck under", x, y)
    return hit[0].z


def rail_y(x):
    return hb(x)-RAIL_IN


def rail_t(x):
    d = (rail_y(x+0.05)-rail_y(x-0.05))/0.1; L = math.hypot(1.0, d)
    return (1.0/L, d/L)


_RX = [95.0-0.05*k for k in range(3701)]
_RS = [0.0]
for _a, _b in zip(_RX, _RX[1:]):
    _RS.append(_RS[-1]+math.hypot(SX_EST*(_b-_a), rail_y(_b)-rail_y(_a)))


def rail_s(x):
    i = min(max(int((95.0-x)/0.05), 0), len(_RX)-2)
    return _RS[i]+(_RS[i+1]-_RS[i])*((95.0-x)/0.05-i)


def edge_pad(name, xc, side, half_x, y_in, y_out, z0, z1, n=8):
    rings = []
    for k in range(n+1):
        x = xc-half_x+2*half_x*k/n
        B = hb(x)
        prof = [(B-y_in, z0), (B-y_out, z0), (B-y_out, z1), (B-y_in, z1)]
        rings.append([(x, side*y, z) for y, z in (prof if side > 0 else list(reversed(prof)))])
    return rings_solid(name, rings)


RAIL_INFO, RAIL_BORES, RAIL_KEEP, RAIL_INK, RAIL_CUT = {}, [], [], [], []
_s_mid = rail_s(-10.0)
for xp in RAIL_POSTS:
    tx, ty = rail_t(xp)
    k_ = math.hypot(SX_EST*tx, ty)             # final mm per pre-scale mm along the fence line
    hx = RAIL_PAD[2]/2*tx/k_
    zs_ = [surf_z(x_, y_) for x_ in (xp-hx, xp, xp+hx) for y_ in [hb(x_)-o_ for o_ in (RAIL_PAD[0]-0.1, RAIL_IN, RAIL_PAD[1]+0.1)]]
    zc_ = surf_z(xp, rail_y(xp))
    top = max(zc_+RAIL_PAD[3], max(zs_)+0.15); bot = min(zs_)-0.5
    plen = RAIL_POCKET[1]+RAIL_POCKET[2]*abs(rail_s(xp)-_s_mid)
    a_, b_ = plen/2/k_, RAIL_POCKET[0]/2
    RAIL_INFO[xp] = {"pad_top": top, "deck": zc_, "pocket_len": round(plen, 3), "deck_spread": round(max(zs_)-min(zs_), 3)}
    for s in (1, -1):
        G.boolean(outer, edge_pad("RailPad", xp, s, hx, RAIL_PAD[0], RAIL_PAD[1], bot, top), "UNION")
        RAIL_INK.append(edge_pad("RailPadInk", xp, s, hx+0.03, RAIL_PAD[0]+0.03, RAIL_PAD[1]-0.03, bot-0.03, top+0.03))
        RAIL_CUT.append(edge_pad("RailPadTeak", xp, s, hx+0.1, RAIL_PAD[0]+0.1, RAIL_PAD[1]-0.1, -10.0, 60.0))
        cx_, cy_ = xp, rail_y(xp)
        pts = [(cx_+tx*u+(-ty)*v, cy_+ty*u+tx*v) for u, v in ((-a_, -b_), (a_, -b_), (a_, b_), (-a_, b_))]
        if s < 0:
            pts = [(x_, -y_) for x_, y_ in reversed(pts)]
        RAIL_BORES.append(prism("RailPocket", pts, "z", top-RAIL_POCKET[3], top+0.6))
        ex, ey = a_*abs(tx)+b_*abs(ty)+0.9, a_*abs(ty)+b_*abs(tx)+0.9
        RAIL_KEEP.append(rbox("RailBoss", cx_-ex, cx_+ex, s*cy_-ey, s*cy_+ey, top-RAIL_POCKET[3]-0.9, 80, 0.6))
# transom returns: a flat panel whose forward face touches the aft face of the corner post
_tx, _ty = rail_t(RAIL_POSTS[-1])
RET_X = RAIL_POSTS[-1]-0.5*_tx/math.hypot(SX_EST*_tx, _ty)-RAIL_T/2/SX_EST
RET_INFO = {}
_hx = 0.65/SX_EST
for j, yl in enumerate(RET_LEGS):
    y0_, y1_ = yl-1.0, yl+1.0
    zs_ = [surf_z(x_, y_) for x_ in (RET_X-_hx, RET_X, RET_X+_hx) for y_ in (y0_+0.1, yl, yl+0.9)]
    top = max(surf_z(RET_X, yl)+RAIL_PAD[3], max(zs_)+0.15); bot = min(zs_)-0.5
    RET_INFO[j] = {"y": yl, "pad_top": top, "deck": surf_z(RET_X, yl), "deck_spread": round(max(zs_)-min(zs_), 3)}
    for s in (1, -1):
        Y0, Y1 = sorted((s*y0_, s*y1_))
        G.boolean(outer, rbox("RetPad", RET_X-_hx, RET_X+_hx, Y0, Y1, bot, top, 0.4), "UNION")
        RAIL_INK.append(rbox("RetPadInk", RET_X-_hx-0.03, RET_X+_hx+0.03, Y0-0.03, Y1+0.03, bot-0.03, top+0.03, 0.43))
        RAIL_CUT.append(rbox("RetPadTeak", RET_X-_hx-0.1, RET_X+_hx+0.1, Y0-0.1, Y1+0.1, -10.0, 60.0, 0.5))
        RAIL_BORES.append(rbox("RetPocket", RET_X-RAIL_POCKET[0]/2/SX_EST, RET_X+RAIL_POCKET[0]/2/SX_EST,
                               s*yl-RAIL_POCKET[1]/2, s*yl+RAIL_POCKET[1]/2, top-RAIL_POCKET[3], top+0.6, 0.05))
        RAIL_KEEP.append(rbox("RetBoss", RET_X-1.5, RET_X+1.5, s*yl-1.4, s*yl+1.4, top-RAIL_POCKET[3]-0.9, 80, 0.6))
log("rail pads", {k: (round(v["pad_top"], 2), v["pocket_len"], v["deck_spread"]) for k, v in RAIL_INFO.items()},
    "returns x", round(RET_X, 3), {k: (round(v["pad_top"], 2), v["deck_spread"]) for k, v in RET_INFO.items()})
TABLE = (-58.5, -45.0, -4.0, 4.0, 16.6)
TABLE_BASE = (-56.0, -47.5, -1.2, 1.2)
table_rings = []
for z, rect, r in ((SOLE_Z-0.5, TABLE_BASE, 0.8), (TABLE[4]-4.2, TABLE_BASE, 0.8), (TABLE[4]-1.0, TABLE[:4], 1.2),
                   (TABLE[4]-0.3, TABLE[:4], 1.2), (TABLE[4], (TABLE[0]+0.3, TABLE[1]-0.3, TABLE[2]+0.3, TABLE[3]-0.3), 0.9)):
    table_rings.append([(px, py, z) for px, py in rrect(*rect, r, 8)])
G.boolean(outer, rings_solid("Table", table_rings), "UNION")
stats(outer)
hs_mast, _ = G.half_section(H, X_MAST-1.9, 400, 0.0)
hs_mast2, _ = G.half_section(H, X_MAST+1.9, 400, 0.0)
log("hull bottom at mast heel", round(hs_mast[0][1], 2), round(hs_mast2[0][1], 2), "socket floor", MAST_HEEL-0.3)
HYDRO_HULL = dup(outer, "HydroHull")

log("cavity loft")
BUMPS = [(LAND-0.95, (-300, 300, 1.0), (SEAM-1.2, SEAM+1.2, 0.9)),
         (0.6, (-15.0, 17.0, 2.0), (9.1, 12.1, 0.8)),
         (0.6, (55.0, 86.0, 2.0), (7.0, 12.4, 0.8))]
cav = loft_deck("Cavity", stations(P["x_aft"], 80.0, 150), 80, WALL, DECK, bumps=BUMPS)
G.cut_plane(cav, *G.transom_plane(P, WALL))
stats(cav); log("cav selfx", len(selfx(cav)))
bool_many(cav, [coachroof("CR_cav", 0.9, 7.0, -42.0, 39.0)], "UNION")
keep = [rbox("dV%d" % i, x0-0.9, x1+0.9, -hw-0.9, hw+0.9, z0-0.9, 80, r+0.9) for i, (x0, x1, hw, z0, r) in enumerate(VOIDS)]
keep.append(rbox("PlatformKeep", -110.0, PLAT_XF+0.9, -45.0, 45.0, PLAT_Z-1.0, 80, 1.0)); rake(keep[-1])
for s in (1, -1):
    keep.append(rbox("BenchKeep%d" % s, -64.5, -38.9, *((8.7, 18.8) if s > 0 else (-18.8, -8.7)),
                     BENCH_Z-0.9, 80, 1.2))
keep.append(prism("MastTube", mast_section(MAST_D0, MAST_W0, 1.15), "z", -30, 40))
for cx_, cy_, cz_, ctop_ in CHAINPLATES:           # solid bosses under the chainplate pockets
    keep.append(rbox("ChainBoss", cx_-1.8, cx_+1.8, cy_-1.8, cy_+1.8, ctop_-CHAIN_DEPTH-0.9, 80, 0.8))
keep.append(rbox("KeelBox", X_FIN-10.4, X_FIN+10.4, -3.0, 3.0, -30, -5.6, 1.0))
keep.append(lathe("RudTube", X_RUD, 0, [(1.925, -30), (1.925, 9.5)]))
keep += RAIL_KEEP
LUGS = []
for lx in (52.0, -46.0):
    yi = y_at_z(lx, SEAM, WALL+0.85)
    zz = [SEAM-3.5+0.25*k for k in range(29)]
    yh = min(yi-1.9, min(y_at_z(lx, z) for z in zz)-1.075-0.9)
    marg = min(y_at_z(lx, z)-(yh+1.075) for z in zz)
    log("lug x", lx, "inner y", round(yi, 2), "hole y", round(yh, 2), "min outer margin", round(marg, 2))
    for s in (1, -1):
        LUGS.append((lx, s*yh))
        keep.append(rbox("Lug", lx-1.9, lx+1.9, min(s*(yh-2.1), s*(yi+0.6)), max(s*(yh-2.1), s*(yi+0.6)), SEAM-3.8, SEAM+3.8, 0.8))
keep += window_solids("WinThick", -0.3, 1.6, 0.8)
bool_many(cav, keep, "DIFFERENCE")
stats(cav); log("cav selfx", len(selfx(cav)))

log("hollow")
shell = outer
G.boolean(shell, cav, "DIFFERENCE")
stats(shell)

bores = [prism("MastBore", mast_section(MAST_D0, MAST_W0, 0.15), "z", MAST_HEEL-0.3, 40),
         rbox("FinSlot", X_FIN-9.2, X_FIN+9.2, -1.8, 1.8, -30, -6.8, 0.3),
         lathe("RudBore", X_RUD, 0, [(1.05, -30), (1.05, 11.0)])]
for s in (1, -1):
    bores.append(prism_x("AxleBore%d" % s, [(s*WHEEL_Y+a, WHEEL_Z+b) for a, b in teardrop(0.0, 0.0, 1.0, 24)],
                         BINNACLE_AFT-0.5, BINNACLE_AFT+2.7))
for lx, ly in LUGS:
    bores.append(lathe("LugHole", lx, ly, [(1.075, SEAM-3.5), (1.075, SEAM-0.4), (1.475, SEAM), (1.075, SEAM+0.4), (1.075, SEAM+3.5)], 32))
bores += window_solids("WinCut", -0.8, 0.95)
for cx_, cy_, cz_, ctop_ in CHAINPLATES:
    bores.append(funnel("ChainPocket", cx_, cy_, CHAIN_SEAT, (2.2, 2.4), ctop_-CHAIN_DEPTH, ctop_))
_fa, _fy0, _fy1, _fd = FPOCKET
bores += RAIL_BORES
bores.append(axis_solid("FurlerPocket", [(-_fd, _fa, _fy0, _fy1), (-0.5, _fa, _fy0, _fy1),
                                         (0.3, _fa+0.3, _fy0-0.2, _fy1+0.2)]))
bool_many(shell, bores, "DIFFERENCE")
stats(shell)

lower = dup(shell, "Lower")
G.boolean(lower, half_space("hs", -100, SEAM), "INTERSECT")
upper = shell; upper.name = "Upper"
G.boolean(upper, half_space("hs", SEAM, 100), "INTERSECT")
stats(lower); stats(upper)

parts = {}
lb = dup(lower, "Lower_blue"); G.boolean(lb, half_space("c", -100, 0.8), "INTERSECT")
lw = dup(lower, "Lower_white"); G.boolean(lw, half_space("cw", 0.8, 1.7), "INTERSECT")
li = lower; li.name = "Lower_ink"; G.boolean(li, half_space("c", 1.7, 50), "INTERSECT")
parts.update({"Lower_blue": lb, "Lower_white": lw, "Lower_ink": li})

log("ink zones")
NAME_X, NAME_Z, NAME_SIZE = 70.0, 8.5, 4.2
PORTS_X, PORT_Z = (-9.5, 1.0, 11.5), 10.6
skin_in = loft_deck("Skin04", stations(-15.0, 90.0, 80, 0.0), 96, 0.4, 0.4)
tool = prism("Port0", stadium(PORTS_X[0], PORT_Z, 7.0, 1.7, 10), "y", -40, 40)
for i, px in enumerate(PORTS_X[1:]):
    G.boolean(tool, prism("Port%d" % (i+1), stadium(px, PORT_Z, 7.0, 1.7, 10), "y", -40, 40), "UNION")
fnt = bpy.data.fonts.load(FONT)
for side in (1, -1):
    cu = bpy.data.curves.new("NameCurve", "FONT")
    cu.body = "Margaret"; cu.font = fnt; cu.size = NAME_SIZE; cu.extrude = 17.5; cu.align_x = "CENTER"
    cu.resolution_u = 6
    tob = bpy.data.objects.new("NameTmp", cu); bpy.context.scene.collection.objects.link(tob)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tob.evaluated_get(dg))
    bpy.data.objects.remove(tob); bpy.data.curves.remove(cu)
    bm = bmesh.new(); bm.from_mesh(me); bpy.data.meshes.remove(me)
    for v in bm.verts:
        X, Y, Z = v.co
        v.co = Vector((NAME_X-side*X, side*(22.5+Z), NAME_Z+Y))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = link("NamePrism%d" % side, bm)
    xs_ = [v.co.x for v in ob.data.vertices]; zz_ = [v.co.z for v in ob.data.vertices]
    log("name side", side, "x", round(min(xs_), 2), round(max(xs_), 2), "z", round(min(zz_), 2), round(max(zz_), 2),
        "sheer above name", round(min(zs(x) for x in xs_)-max(zz_), 2))
    G.boolean(tool, ob, "UNION")
G.boolean(tool, skin_in, "DIFFERENCE")
for side in (1, -1):
    rings = []
    for x in stations(-89.6, 95.8, 170, 0.3):
        B = hb(x); z = zs(x)
        prof = [(max(B-0.95, 0.0), z+0.12), (B+0.6, z+0.12),
                (B+0.6, z+0.55), (max(B-0.95, 0.0), z+0.55)]
        rings.append([(x, side*y, zz) for y, zz in (prof if side > 0 else list(reversed(prof)))])
    rz = rings_solid("RailZone", rings)
    G.boolean(rz, rbox("RailBowClear", 88.2, 101.5, -1.45, 1.45, 0.0, 40.0, 0.3), "DIFFERENCE")
    G.boolean(tool, rz, "UNION")
bool_many(tool, HATCH_LENS, "UNION")


def x_face(z):
    return CR_XA+(z-CR_ZA)/CR_RAKE


WB_TOP = 21.7
wash = prism("WashboardRake", [(x_face(CR_ZA-0.05)-1.2, CR_ZA-0.05), (x_face(CR_ZA-0.05)+0.55, CR_ZA-0.05),
                               (x_face(WB_TOP)+0.55, WB_TOP), (x_face(WB_TOP)-1.2, WB_TOP)], "y", -4.1, 4.1)
G.boolean(wash, rbox("WashboardLow", -39.8, -38.15, -4.1, 4.1, 11.4, CR_ZA+0.05, 0.4), "UNION")
G.boolean(wash, prism("WashboardBar", [(x_face(18.6)-2.0, 18.6), (x_face(18.6)+2.0, 18.6),
                                        (x_face(19.1)+2.0, 19.1), (x_face(19.1)-2.0, 19.1)], "y", -4.3, 4.3), "DIFFERENCE")
G.boolean(tool, wash, "UNION")
G.boolean(tool, rbox("SliderSmoke", SLIDER[0]+0.5, SLIDER[1]-0.5, SLIDER[2]+0.5, SLIDER[3]-0.5,
                     slider_top-0.35, slider_top+0.2, 0.6), "UNION")
for i, (x0_, x1_, y0_, y1_) in enumerate(LADDER):
    G.boolean(tool, box_xy("LadderInk%d" % i, x0_, x1_, y0_, y1_, PLAT_Z-0.46, PLAT_Z+0.5), "UNION")
G.boolean(tool, lathe("DeckPlate", X_RUD, 0, [(2.3, SOLE_Z-0.45), (2.3, SOLE_Z+0.02)], 40), "UNION")
for s_ in (1, -1):
    G.boolean(tool, rbox("Instrument%d" % s_, BINNACLE_AFT-0.3, BINNACLE_AFT+3.7, s_*WHEEL_Y-2.2, s_*WHEEL_Y+2.2,
                         WHEEL_Z+1.7, WHEEL_Z+4.0, 0.3), "UNION")
G.boolean(tool, anchor("AnchorInk", 0.03), "UNION")
for i, (x, y) in enumerate(CLEATS):              # rev 11: navy cleats read against the white deck and teak
    G.boolean(tool, cleat("CleatInk%d" % i, x, y, deck_z(x, y), 0.03), "UNION")
bool_many(tool, RAIL_INK, "UNION")
# repeat the name on the port (+y) upper transom face, reading left-to-right from astern, inlaid 0.8 mm.
# Slicer coupons (coupon/): a 0.6 mm inlay of these 0.5-0.6 mm strokes is near-square in every layer, so Arachne's
# medial axis collapses and most strokes vanish; 0.8 mm prints every layer. A white pad behind the name keeps a
# continuous two-bead white skin, so no navy/white seam runs through this wall (it can wet when heeled).
TN_Y0, TN_Y1 = PASS_HW+0.9, Yc-CORNER_R-0.6
TN_ZC = 0.5*(PLAT_Z+HELM_Z)+0.3
cu = bpy.data.curves.new("TNameCurve", "FONT")
cu.body = "Margaret"; cu.font = fnt; cu.size = 1.0; cu.extrude = 1.0; cu.align_x = "CENTER"; cu.resolution_u = 6
tob = bpy.data.objects.new("TNameTmp", cu); bpy.context.scene.collection.objects.link(tob)
me = bpy.data.meshes.new_from_object(tob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
bpy.data.objects.remove(tob); bpy.data.curves.remove(cu)
bm = bmesh.new(); bm.from_mesh(me); bpy.data.meshes.remove(me)
_X = [v.co.x for v in bm.verts]; _Y = [v.co.y for v in bm.verts]
TN_S = min(3.9, (TN_Y1-TN_Y0)/(max(_X)-min(_X)))
_xc, _yc = 0.5*(max(_X)+min(_X)), 0.5*(max(_Y)+min(_Y))
for v in bm.verts:
    X, Y, Z = v.co
    z = TN_ZC+TN_S*(Y-_yc)
    v.co = Vector((PLAT_XF+RAKE_K*(z-PLAT_Z)+1.05*Z-0.25, 0.5*(TN_Y0+TN_Y1)-TN_S*(X-_xc), z))
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
tname = link("TransomName", bm)
_ty = [v.co.y for v in tname.data.vertices]; _tz = [v.co.z for v in tname.data.vertices]
log("transom name size", round(TN_S, 2), "y", round(min(_ty), 2), round(max(_ty), 2), "z", round(min(_tz), 2),
    round(max(_tz), 2), "face y", round(PASS_HW, 2), round(Yc-CORNER_R, 2), "face z", PLAT_Z, HELM_Z)
build_stats_extra = {"transom_name": {"size": round(TN_S, 2), "y": [round(min(_ty), 2), round(max(_ty), 2)],
                                      "z": [round(min(_tz), 2), round(max(_tz), 2)]}}
G.boolean(tool, tname, "UNION")
_xf = lambda z: PLAT_XF+RAKE_K*(z-PLAT_Z)
_zb, _zt = min(_tz)-0.5, max(_tz)+0.5
G.boolean(upper, prism("TransomNamePad", [(_xf(_zb-1.0)+0.9, _zb-1.0), (_xf(_zb)+1.62, _zb), (_xf(_zt)+1.62, _zt),
                                          (_xf(_zt)+0.9, _zt)], "y", TN_Y0-0.2, TN_Y1+0.2), "UNION")
stats(upper)
stats(tool)

log("teak with caulked seams")
PLAT_POLY = []
for k in range(13):
    x_ = PLAT_XA+CH+0.25+(PLAT_XF-0.05-(PLAT_XA+CH+0.25))*k/12
    PLAT_POLY.append((x_, y_at_z(x_, PLAT_Z)-0.6))
PLAT_POLY += [(x_, -y_) for x_, y_ in reversed(PLAT_POLY)]
TEAK_ZONES = [
    prism("TeakSole", rrect(TREAD_XF+0.4, -39.6, -9.0, 9.0, 1.2), "z", SOLE_Z-0.5, SOLE_Z+0.02),
    prism("TeakWheelWell", rrect(-76.1, -64.4, -20.1, 20.1, 1.0), "z", SOLE_Z-0.5, SOLE_Z+0.02),
    prism("TeakBenchP", rrect(-62.9, -39.7, 10.6, 16.9, 1.0), "z", BENCH_Z-0.45, BENCH_Z+0.02),
    prism("TeakBenchS", rrect(-62.9, -39.7, -16.9, -10.6, 1.0), "z", BENCH_Z-0.45, BENCH_Z+0.02),
    prism("TeakHelmP", rrect(PLAT_XF+RAKE_K*(HELM_Z-PLAT_Z)+0.35, -77.4, 9.3, 20.3, 1.0), "z", HELM_Z-0.45, HELM_Z+0.02),
    prism("TeakHelmS", rrect(PLAT_XF+RAKE_K*(HELM_Z-PLAT_Z)+0.35, -77.4, -20.3, -9.3, 1.0), "z", HELM_Z-0.45, HELM_Z+0.02),
    prism("TeakPlatform", PLAT_POLY, "z", PLAT_Z-0.45, PLAT_Z+0.02),
    prism("TeakTread", rrect(PLAT_XF-0.05, TREAD_XF-0.25, -PASS_HW+0.5, PASS_HW-0.5, 0.6), "z",
          TREAD_Z-0.45, TREAD_Z+0.02),
    prism("TeakTable", rrect(TABLE[0]+0.55, TABLE[1]-0.55, TABLE[2]+0.55, TABLE[3]-0.55, 0.6), "z",
          TABLE[4]-0.4, TABLE[4]+0.02),
    handrail("TeakRailP", 1, grow=0.25, zlo=0.14, top=1.6),
    handrail("TeakRailS", -1, grow=0.25, zlo=0.14, top=1.6),
]
TD_X0, TD_X1, TD_EDGE, TD_PITCH = PLAT_XF+RAKE_K*(16.0-PLAT_Z)+0.6, 88.0, 2.05, 2.5
TD_KING, TD_MARGIN, TD_COCKPIT = 1.5, 1.5, 22.6


def td_out(x):
    return hb(x)-TD_EDGE


band_rings = []
for x in stations(TD_X0, TD_X1, 160, 0.0):
    yo = td_out(x)
    ys = [yo*(2*k/40-1) for k in range(41)]
    prof = [(y, deck_z(x, y)+0.05) for y in ys]+[(y, deck_z(x, y)-0.45) for y in reversed(ys)]
    band_rings.append([(x, y, z) for y, z in prof])
deck_teak = rings_solid("TeakDeck", band_rings)
cr_xs = [CR_XA+(CR_XF-CR_XA)*k/300 for k in range(301)]
cr_poly = [(x, cr_w(x)+0.05) for x in cr_xs]
cr_poly = [(CR_XA-0.6, 0.0)]+cr_poly+[(CR_XF+0.05, 0.0)]
cr_poly += [(x, -y) for x, y in reversed(cr_poly[1:-1])]
excl = [prism("TeakExclCR", cr_poly, "z", -10.0, 60.0),
        rbox("TeakExclCockpit", -110.0, -35.0, -TD_COCKPIT, TD_COCKPIT, -10.0, 60.0, 1.0),
        rbox("TeakExclHatch", HATCH_FD[0]-HATCH_FD[2]/2-0.6, HATCH_FD[0]+HATCH_FD[2]/2+0.6,
             -HATCH_FD[3]/2-0.6, HATCH_FD[3]/2+0.6, -10.0, 60.0, 1.8),
        rbox("TeakExclLid", LID[0]-0.6, LID[1]+0.6, LID[2]-0.6, LID[3]+0.6, -10.0, 60.0, 1.6)]
for cx_, cy_, cz_, ctop_ in CHAINPLATES:
    excl.append(rbox("TeakExclChain", cx_-1.9, cx_+1.9, cy_-1.7, cy_+1.7, -10.0, 60.0, 1.0))
for x, y in CLEATS:
    excl.append(rbox("TeakExclCleat", x-CLEAT_FLANGE[0]-0.1, x+CLEAT_FLANGE[0]+0.1, y-CLEAT_FLANGE[1]-0.1,
                      y+CLEAT_FLANGE[1]+0.1, -10.0, 60.0, CLEAT_FLANGE[3]+0.1))
bool_many(deck_teak, excl, "DIFFERENCE")
TEAK_ZONES.append(deck_teak)
ttool = TEAK_ZONES[0]; bool_many(ttool, TEAK_ZONES[1:], "UNION")
cut_fp = [rbox("BinnacleFoot%d" % s, BINNACLE_AFT-0.5, BINNACLE_AFT+3.9, s*WHEEL_Y-2.3, s*WHEEL_Y+2.3,
               SOLE_Z-1.0, SOLE_Z+0.5, 1.0) for s in (1, -1)]
cut_fp.append(rbox("TableFoot", TABLE_BASE[0]-0.5, TABLE_BASE[1]+0.5, TABLE_BASE[2]-0.5, TABLE_BASE[3]+0.5,
                   SOLE_Z-1.0, SOLE_Z+0.5, 1.2))
cut_fp.append(lathe("DeckPlateFoot", X_RUD, 0, [(2.95, SOLE_Z-1.0), (2.95, SOLE_Z+0.5)], 40))
cut_fp += RAIL_CUT
for i, (x0_, x1_, y0_, y1_) in enumerate(LADDER):
    cut_fp.append(box_xy("LadderFoot%d" % i, x0_, x1_, y0_, y1_, PLAT_Z-0.6, PLAT_Z+0.6))
bool_many(ttool, cut_fp, "DIFFERENCE")
SEAM_W = 0.5
strips = [rbox("SoleSeam", -84.0, -39.0, (k+0.5)*2.25-SEAM_W/2, (k+0.5)*2.25+SEAM_W/2, SOLE_Z-0.8, SOLE_Z+0.3, 0.05)
          for k in range(-9, 9)]
for s in (1, -1):
    strips += [rbox("BenchSeam", -63.5, -39.0, s*y-SEAM_W/2, s*y+SEAM_W/2, BENCH_Z-0.8, BENCH_Z+0.3, 0.05)
               for y in (12.7, 14.8)]
    strips += [rbox("HelmSeam", PLAT_XF-0.5, -76.8, s*y-SEAM_W/2, s*y+SEAM_W/2, HELM_Z-0.8, HELM_Z+0.3, 0.05)
               for y in (11.5, 13.75, 16.0, 18.25)]
strips += [rbox("PlatSeam", x-SEAM_W/2, x+SEAM_W/2, -30.0, 30.0, PLAT_Z-0.8, PLAT_Z+0.3, 0.05)
           for x in (PLAT_XA+2.3, PLAT_XA+4.4)]
strips += [rbox("TreadSeam", -84.25-SEAM_W/2, -84.25+SEAM_W/2, -PASS_HW, PASS_HW, TREAD_Z-0.8, TREAD_Z+0.3, 0.05)]


def seam_band(name, pts, hw=SEAM_W/2, lo=-0.8, hi=0.3):
    rings = []
    for i, (x, y) in enumerate(pts):
        xa, ya = pts[max(i-1, 0)]; xb, yb = pts[min(i+1, len(pts)-1)]
        tx, ty = xb-xa, yb-ya; L = math.hypot(tx, ty) or 1.0
        nx, ny = -ty/L, tx/L
        z = deck_z(x, y)
        rings.append([(x-nx*hw, y-ny*hw, z+lo), (x+nx*hw, y+ny*hw, z+lo),
                      (x+nx*hw, y+ny*hw, z+hi), (x-nx*hw, y-ny*hw, z+hi)])
    return rings_solid(name, rings)


# centreline of the coachroof margin seam: the coachroof edge offset along its normal by TD_MARGIN
MPTS = []
for k in range(201):
    x = -34.3+(36.0+34.3)*k/200
    dw = (cr_w(x+0.05)-cr_w(x-0.05))/0.1
    L = math.hypot(1.0, dw)
    MPTS.append((x-dw/L*TD_MARGIN, cr_w(x)+TD_MARGIN/L))
th0 = math.acos((36.0-CR_NOSE_X)/CR_NOSE_A)
for k in range(1, 61):
    th = th0*(1-k/60)
    nx, ny = math.cos(th)/CR_NOSE_A, math.sin(th)/CR_NOSE_B
    L = math.hypot(nx, ny)
    p = (CR_NOSE_X+CR_NOSE_A*math.cos(th)+nx/L*TD_MARGIN, CR_NOSE_B*math.sin(th)+ny/L*TD_MARGIN)
    if p[1] < TD_KING:
        break
    MPTS.append(p)


def margin_y(x):
    """y of the margin-seam centreline at x (it is monotonic in x), None outside its span."""
    if not MPTS[0][0] <= x <= MPTS[-1][0]:
        return None
    for (xa, ya), (xb, yb) in zip(MPTS, MPTS[1:]):
        if xa <= x <= xb:
            return ya+(yb-ya)*(x-xa)/((xb-xa) or 1.0)


def td_lim(x):
    """Inner limit for sprung seams: cockpit margin aft, coachroof margin seam, king plank forward."""
    if x < -35.0:
        return TD_COCKPIT+TD_MARGIN
    ym = margin_y(x)
    if ym is not None:
        return max(ym, TD_KING)
    if x <= CR_XF+TD_MARGIN:
        return max(cr_w(min(x, CR_XF))+TD_MARGIN, TD_KING)
    return TD_KING


def runs(pts, ok):
    out, cur = [], []
    for p in pts:
        if ok(p):
            cur.append(p)
        elif cur:
            out.append(cur); cur = []
    if cur:
        out.append(cur)
    return [r for r in out if len(r) >= 4 and math.dist(r[0], r[-1]) > 4.0]


edge_x = [TD_X0+(TD_X1-TD_X0)*k/700 for k in range(701)]
SEAM_RUNS = 0
NIB, NIBS = 1.2, 0
for s in (1, -1):
    for k in range(1, 16):
        d = TD_PITCH*k
        pts = []
        for x in edge_x:
            dy = (td_out(x+0.05)-td_out(x-0.05))/0.1
            L = math.hypot(1.0, dy)
            pts.append((x+d*dy/L, td_out(x)-d/L))
        ok = lambda p: TD_X0+0.4 <= p[0] <= TD_X1-0.4 and p[1] >= td_lim(p[0])+SEAM_W+NIB
        for r in runs(pts, ok):
            strips.append(seam_band("DeckSeam", [(x, s*y) for x, y in r])); SEAM_RUNS += 1
            for xe, ye in (r[0], r[-1]):
                if -30.0 < xe < TD_X1-1.0:
                    yl = td_lim(xe)
                    # ends sit inside the neighbouring seams (no coplanar faces for the exact solver);
                    # yl is the margin-seam centreline, so a 0.24 mm half-width nib never pokes past it
                    y0n, y1n = ye+0.2*SEAM_W, yl-0.05
                    strips.append(seam_band("Nib", [(xe, s*(y0n+(y1n-y0n)*j/6)) for j in range(7)],
                                            0.48*SEAM_W, -0.73, 0.37))
                    NIBS += 1
    strips.append(seam_band("CockpitMargin", [(x, s*(TD_COCKPIT+TD_MARGIN)) for x in
                                              [TD_X0+0.4+(-35.5-TD_X0-0.4)*k/40 for k in range(41)]]))
    mpts = MPTS
    strips.append(seam_band("CRMargin", [(x, s*y) for x, y in mpts]))
    strips.append(seam_band("KingSeam", [(x, s*TD_KING) for x in [mpts[-1][0]+(TD_X1-0.4-mpts[-1][0])*k/40
                                                                   for k in range(41)]]))
log("deck seam runs", SEAM_RUNS, "nibs", NIBS)
seam_tool = strips[0]; bool_many(seam_tool, strips[1:], "UNION")
# white is cut with the seam-free tools only: re-subtracting curved seam walls that a previous boolean has
# float-rounded leaves near-coincident slanted faces, which breaks the exact solver.
seams = dup(seam_tool, "CaulkSeams"); G.boolean(seams, dup(ttool, "tz"), "INTERSECT")
seam_keep = dup(seam_tool, "SeamKeep")
ttool_c = dup(ttool, "TeakCaulked"); G.boolean(ttool_c, seam_tool, "DIFFERENCE")
tool_c = dup(tool, "InkWithSeams"); G.boolean(tool_c, seams, "UNION")
stats(ttool_c); stats(tool_c)

ink_up = dup(upper, "Upper_ink"); G.boolean(ink_up, tool_c, "INTERSECT")
# clip to the deck first, then cut the seams: upper ^ (teak - seams) can come back empty from the exact
# solver when a seam wall grazes a deck-moulding face; the two-step order is equivalent and robust.
teak = dup(upper, "Upper_teak"); G.boolean(teak, dup(ttool, "tq"), "INTERSECT")
G.boolean(teak, seam_keep, "DIFFERENCE")
assert G.mesh_stats(teak)["vol_cm3"] > 1.5, "teak boolean failed"
white = upper; white.name = "Upper_white"
# teak first: in v7g the tool-then-teak order came back as a 2.9 cm3 sliver from the exact solver
G.boolean(white, ttool, "DIFFERENCE"); G.boolean(white, tool, "DIFFERENCE")
assert G.mesh_stats(white)["vol_cm3"] > 15.0, "white boolean failed"
panes = window_solids("Pane", 0.35, 0.95)
ink_win = panes[0]; bool_many(ink_win, panes[1:], "UNION"); ink_win.name = "Window_ink"
for o in (ink_up, teak, white, ink_win):
    stats(o)
parts.update({"Upper_white": white, "Upper_ink": ink_up, "Upper_teak": teak, "Window_ink": ink_win})

log("keel fin and detachable bulb")
X_BULB = float(os.environ.get("MARGARET_XBULB", "-13.0"))   # aft so a level lead pour trims level
bulb = bulb_outer("BulbOuter", X_BULB)
G.boolean(bulb, half_space("BulbFlat", BULB_FLAT, 100.0), "INTERSECT")
cap = dup(bulb, "BulbCap")
G.boolean(cap, half_space("BulbCapHalf", BULB_SPLIT, 100.0), "INTERSECT")
cup = dup(bulb, "BulbCup")
G.boolean(cup, half_space("BulbCupHalf", -100.0, BULB_SPLIT), "INTERSECT")
fin = naca_fin("Fin", X_FIN, zend=BULB_SPLIT+0.05, ztop=-9.5, hull=HYDRO_HULL)
hydro_probe = dup(HYDRO_HULL, "HydroAssembly")
keel_probe = dup(bulb, "HydroKeel")
G.boolean(keel_probe, naca_fin("HydroFin", X_FIN, zend=BULB_SPLIT+0.05, ztop=-9.5), "UNION")
G.boolean(hydro_probe, keel_probe, "UNION")
G.boolean(hydro_probe, naca_rudder("HydroRudder", X_RUD), "UNION")
ASSEMBLY_DISPLACEMENT_CURVE = {}
for wl in (-1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0):
    p_ = dup(hydro_probe, "AssemblyDWL_%s" % str(wl).replace(".", "_").replace("-", "m"))
    G.boolean(p_, half_space("AssemblyDWLClip", -80.0, wl), "INTERSECT")
    ASSEMBLY_DISPLACEMENT_CURVE[wl] = G.mesh_stats(p_)["vol_cm3"]
    bpy.data.objects.remove(p_, do_unlink=True)
hydro_probe.name = "HydroEnvelope"
log("assembled displacement curve cm3 before final LOA scale", ASSEMBLY_DISPLACEMENT_CURVE)
G.boolean(cap, fin, "UNION")
cavity_tool = bulb_cavity("BulbCavity", X_BULB)
CAV_U = bulb_cavity_range()
CAV_X = (X_BULB+BULB_L/2-BULB_L*CAV_U[1], X_BULB+BULB_L/2-BULB_L*CAV_U[0])
cavity_probe = dup(cavity_tool, "BulbCavityMeasure")
G.boolean(cavity_probe, half_space("BulbCavityBelowSplit", -100.0, BULB_SPLIT), "INTERSECT")
CAVITY_CM3 = G.mesh_stats(cavity_probe)["vol_cm3"]
bpy.data.objects.remove(cavity_probe, do_unlink=True)
G.boolean(cup, cavity_tool, "DIFFERENCE")
POSTS = [CAV_X[1]-8.0, X_BULB+1.5]
POST_R, POST_TOP = 1.0, BULB_SPLIT+1.0
POST_IN_CAVITY = 0.0
for px in POSTS:
    f = bulb_factor((X_BULB+BULB_L/2-px)/BULB_L)
    z_floor = max(BULB_ZC-(BULB_HH*f-BULB_WALL), BULB_FLOOR)
    hole_top = POST_TOP+0.3+0.9
    log("post x", round(px, 2), "cavity floor", round(z_floor, 2), "cap wall above hole", round(BULB_ZC+BULB_HH*f-hole_top, 2))
    POST_IN_CAVITY += math.pi*POST_R**2*(BULB_SPLIT-z_floor)/1000
    G.boolean(cup, lathe("CupPost", px, 0, [(POST_R, z_floor-0.5), (POST_R, POST_TOP-0.25), (POST_R-0.25, POST_TOP)], 32), "UNION")
    G.boolean(cap, lathe("CapPostHole", px, 0, [(POST_R+0.2, BULB_SPLIT-1.0), (POST_R+0.2, POST_TOP+0.3),
                                                 (0.3, hole_top)], 32), "DIFFERENCE")
CAVITY_CM3 -= POST_IN_CAVITY
log("bulb x", round(X_BULB, 2), "cavity x", [round(v, 2) for v in CAV_X], "usable cavity cm3", round(CAVITY_CM3, 3),
    "posts", [round(v, 2) for v in POSTS])
cap.name = "Fin_cap"
cup.name = "Ballast_cup"
parts.update({"Fin_cap": cap, "Ballast_cup": cup})
stats(cap); stats(cup)

log("mast, boom, rudder and helm wheels")
d43, w43 = mast_dw(GOOSE_Z)
MZ = [MAST_HEEL, MAST_HEEL+0.35]+[30.0+(MAST_TOP-30.0)*k/14 for k in range(15)]
mast_rings = [[(x, y, MAST_HEEL) for x, y in mast_section(*mast_dw(MAST_HEEL), -0.3)]]
mast_rings += [[(x, y, z) for x, y in mast_section(*mast_dw(z))] for z in MZ[1:]]
mast = rings_solid("MastSpar", mast_rings)
dt, wt = mast_dw(MAST_TOP)
G.boolean(mast, pad("MastCap", MAST_XA, MAST_XA+dt+0.45, -(wt/2+0.35), wt/2+0.35, MAST_TOP-5.0, MAST_TOP+0.6, 0.45, 0.35), "UNION")
G.boolean(mast, rbox("Gooseneck", MAST_XA, MAST_XA+d43+0.8, -(w43/2+1.2), w43/2+1.2, GOOSE_Z-1.4, GOOSE_Z, 0.6), "UNION")
spar_only = dup(mast, "SparOnly")
# printed shroud frame (navy, part "Shrouds"): cap shrouds hounds -> spreader tips -> chainplate, lowers from below
# the lower spreader root; a flat 0.6 mm frame on the mast's aft print face. Tabs at the feet drop into the
# chainplate pockets; the mast heel bottoms in its socket while the tabs and feet keep clearance.
SHR_T, SHR_W, FOOT_R, TIP_R = 0.6, 1.0, 1.0, 0.8
SPREADERS = [(95.0, 24.0), (155.0, 14.5)]          # rev 11: swept out to the outboard chainplates
SPREADER_SEC = [(1.6, 1.3, 0.9), (1.25, 1.1, 0.8)]  # fore-aft depth, root and tip heights (tapered aerofoil-ish)
HOUNDS = (MAST_XA+0.9, MAST_TOP-8.5)
SHROUD_FEET, SHROUD_PATHS = [], {}


def strip_x(name, pts, w=SHR_W, x0=MAST_XA, x1=MAST_XA+SHR_T, e0=0.0, e1=0.0):
    """One mitred flat strip along a y-z polyline (a single prism, no internal booleans). e0/e1 extend (+) or
    shorten (-) the open ends so that strips meeting at a node never share an end face."""
    P = [list(p) for p in pts]
    for i_, j_, e_ in ((0, 1, e0), (-1, -2, e1)):  # move the end point outward along its own segment by e_
        L = math.hypot(P[i_][0]-P[j_][0], P[i_][1]-P[j_][1])
        P[i_] = [P[i_][0]+(P[i_][0]-P[j_][0])/L*e_, P[i_][1]+(P[i_][1]-P[j_][1])/L*e_]
    nrm = []
    for (y0, z0), (y1, z1) in zip(P, P[1:]):
        L = math.hypot(y1-y0, z1-z0); nrm.append((-(z1-z0)/L, (y1-y0)/L))
    left, right = [], []
    for k, p in enumerate(P):
        if k == 0 or k == len(P)-1:
            n_ = nrm[0] if k == 0 else nrm[-1]
            m_ = 1.0
        else:
            n_ = (nrm[k-1][0]+nrm[k][0], nrm[k-1][1]+nrm[k][1]); L = math.hypot(*n_); n_ = (n_[0]/L, n_[1]/L)
            m_ = 1.0/max(0.3, n_[0]*nrm[k][0]+n_[1]*nrm[k][1])
        left.append((p[0]+n_[0]*w/2*m_, p[1]+n_[1]*w/2*m_))
        right.append((p[0]-n_[0]*w/2*m_, p[1]-n_[1]*w/2*m_))
    return prism_x(name, left+list(reversed(right)), x0, x1)


shrouds = None
for s in (1, -1):
    cx_, cy_, cz_, ctop_ = [c for c in CHAINPLATES if c[1]*s > 0][0]
    foot = (cy_, ctop_+0.3+FOOT_R)
    SHROUD_FEET.append((MAST_XA+0.6, cy_, foot[1]))
    cap_ = [(s*0.3, HOUNDS[1]), (s*(SPREADERS[1][1]-0.2), SPREADERS[1][0]),
            (s*(SPREADERS[0][1]-0.2), SPREADERS[0][0]), foot]
    low_ = [(s*0.6, SPREADERS[0][0]-1.6), foot]
    SHROUD_PATHS["port" if s > 0 else "starboard"] = {"cap": cap_, "lower": low_}
    side = strip_x("CapShroud", cap_, e1=0.3)
    G.boolean(side, rod_x("ShroudFoot", MAST_XA, MAST_XA+SHR_T, foot[0], foot[1], FOOT_R, 28), "UNION")
    for (y_, z_) in cap_[1:3]:
        G.boolean(side, rod_x("SpreaderTipNode", MAST_XA, MAST_XA+SHR_T, y_, z_, TIP_R, 28), "UNION")
    G.boolean(side, strip_x("LowerShroud", low_, e1=-0.3), "UNION")
    G.boolean(side, rbox("ShroudTab", MAST_XA, MAST_XA+TAB_W, cy_-TAB_W/2, cy_+TAB_W/2,
                         ctop_-CHAIN_DEPTH+0.5, foot[1], 0.25, 4), "UNION")
    if shrouds is None:
        shrouds = side
    else:
        G.boolean(shrouds, side, "UNION")
G.boolean(shrouds, spar_only, "DIFFERENCE")
for i, (zsp, half) in enumerate(SPREADERS):
    dep, h0, h1 = SPREADER_SEC[i]
    poly = [(-half, zsp-h1/2), (0.0, zsp-h0/2), (half, zsp-h1/2), (half, zsp+h1/2), (0.0, zsp+h0/2), (-half, zsp+h1/2)]
    G.boolean(mast, prism_x("Spreader%d" % i, poly, MAST_XA, MAST_XA+dep), "UNION")
MASTHEAD_HOLE_Z = MAST_TOP-2.2
G.boolean(mast, rod_x("StayHole", MAST_XA-1, MAST_XA+5, 0, MASTHEAD_HOLE_Z, 0.42, 16), "DIFFERENCE")
_cut = dup(shrouds, "ShroudCut")
for v in _cut.data.vertices:                    # drop the cutter's print face below the mast's to avoid coplanar faces
    if abs(v.co.x-MAST_XA) < 1e-4:
        v.co.x -= 0.3
G.boolean(mast, _cut, "DIFFERENCE")
mast.name = "Mast"; shrouds.name = "Shrouds"
log("shroud feet", [(round(y, 2), round(z, 2)) for _, y, z in SHROUD_FEET], "chainplates", CHAINPLATES)

# printed furled genoa on a furler (display only): white D-section body on the stay axis, navy drum + foot tab
# that drops into the stemhead pocket, and an inverted-U hook that hangs over the masthead cap.


def furl_ring(s, a, c, n=20):
    """Truncated ellipse section at axis station s: in-plane half-width a, y semi-axis c, flat face at FURL_Y0."""
    yc = FURL_Y0+0.75*c
    cx, cz = FURL_A[0]+FURL_T[0]*s, FURL_A[1]+FURL_T[1]*s
    ring = []
    for k in range(n):
        ph = 2*math.pi*k/n
        u, yy = a*math.cos(ph), max(FURL_Y0, yc+c*math.sin(ph))
        ring.append((cx+FURL_N[0]*u, yy, cz+FURL_N[1]*u))
    return ring


DRUM_S0, DRUM_S1, BODY_A = FURL_DRUM_S, FURL_DRUM_S+1.6, 1.1
drum = rings_solid("FurlerDrum", [furl_ring(DRUM_S0, 1.0, 0.8), furl_ring(DRUM_S0+0.25, 1.3, 1.0),
                                  furl_ring(DRUM_S1-0.25, 1.3, 1.0), furl_ring(DRUM_S1, 1.0, 0.8)])
G.boolean(drum, axis_solid("FurlerTab", [(DRUM_S0-3.4, FTAB_A, FURL_Y0, FURL_Y0+FTAB_H),
                                          (DRUM_S0+0.3, FTAB_A, FURL_Y0, FURL_Y0+FTAB_H)]), "UNION")
body_rings = []
NS = 60
for k in range(NS+1):
    s_ = DRUM_S1+(FURL_L-DRUM_S1)*k/NS
    if s_ < 12.0:
        a_ = 0.55+(BODY_A-0.55)*math.sin(0.5*math.pi*(s_-DRUM_S1)/(12.0-DRUM_S1))
    else:
        a_ = BODY_A-(BODY_A-0.55)*((s_-12.0)/(FURL_L-12.0))**1.3
    body_rings.append(furl_ring(s_, a_, 0.55+0.37*a_/BODY_A))
furler = rings_solid("FurlerBody", body_rings)
hx0, hx1 = CAP_XA-HOOK_CLR-HOOK_STOCK, CAP_XF+HOOK_CLR+HOOK_STOCK
hz1 = CAP_TOP+HOOK_CLR+HOOK_STOCK
hook = [(hx1, HOOK_B[1]-0.4), (hx1, hz1-0.5)]
hook += [(hx1-0.5+0.5*math.cos(math.radians(a_)), hz1-0.5+0.5*math.sin(math.radians(a_))) for a_ in range(15, 91, 15)]
hook += [(hx0+0.5+0.5*math.cos(math.radians(a_)), hz1-0.5+0.5*math.sin(math.radians(a_))) for a_ in range(90, 181, 15)]
hook += [(hx0, CAP_TOP-HOOK_LEG), (hx0+HOOK_STOCK, CAP_TOP-HOOK_LEG), (hx0+HOOK_STOCK, CAP_TOP+HOOK_CLR),
         (hx1-HOOK_STOCK, CAP_TOP+HOOK_CLR), (hx1-HOOK_STOCK, HOOK_B[1]-0.4)]
G.boolean(furler, prism("FurlerHook", hook, "y", FURL_Y0, FURL_Y0+HOOK_STOCK), "UNION")
furler.name = "Furler"; drum.name = "Furler_ink"
log("furler length", round(FURL_L, 2), "axis", [round(v, 4) for v in FURL_T], "hook x", (round(hx0, 2), round(hx1, 2)),
    "hook top", round(hz1, 2), "cap", (round(CAP_XA, 2), round(CAP_XF, 2), round(CAP_TOP, 2)))
log("mast section heel", mast_dw(0.0), "gooseneck", (round(d43, 2), round(w43, 2)), "top", (round(dt, 2), round(wt, 2)))

BOOM_Z0, BOOM_H, BOOM_W = GOOSE_Z+0.05, 2.6, 1.9
BOOM_AFT = -45.5
BOOM_FWD = MAST_XA-0.35
boom = prism_x("BoomSpar", rrect(-BOOM_W/2, BOOM_W/2, BOOM_Z0, BOOM_Z0+BOOM_H, 0.65), BOOM_AFT+1.0, BOOM_FWD-1.0)
G.boolean(boom, rbox("BoomEnd", BOOM_AFT, BOOM_AFT+5.0, -1.25, 1.25, BOOM_Z0, BOOM_Z0+BOOM_H, 1.2), "UNION")
G.boolean(boom, rbox("BoomTongue", BOOM_FWD-4.0, BOOM_FWD, -1.2, 1.2, BOOM_Z0, BOOM_Z0+BOOM_H, 1.15), "UNION")
BOOM_HOLES = {"gooseneck loop": BOOM_FWD-1.3, "mainsheet": TRAV_X, "clew start": TRAV_X-3.6,
              "clew medium": -32.5, "clew": BOOM_AFT+1.25}
for k_, (x0_, x1_) in {"sheet": (TRAV_X-5.3, TRAV_X+1.7), "medium": (-34.2, -30.8)}.items():
    G.boolean(boom, rbox("BoomBoss", x0_, x1_, -1.2, 1.2, BOOM_Z0, BOOM_Z0+BOOM_H, 0.35), "UNION")
for k, hx in BOOM_HOLES.items():
    G.boolean(boom, lathe("BoomHole", hx, 0, [(0.42, BOOM_Z0-1), (0.42, BOOM_Z0+BOOM_H+1)], 16), "DIFFERENCE")
boom.name = "Boom"
rudder = naca_rudder("RudderBlade", X_RUD)
RUD_INK_Z = 9.0
rudder_ink = dup(rudder, "Rudder_ink")
G.boolean(rudder_ink, half_space("RudInkZone", RUD_INK_Z, 100.0), "INTERSECT")
G.boolean(rudder, half_space("RudBlueZone", -100.0, RUD_INK_Z), "INTERSECT")
rudder.name = "Rudder"; rudder_ink.name = "Rudder_ink"
wheel_p, spokes_p = helm_wheel("Wheel_Port", WHEEL_X, WHEEL_Y, WHEEL_Z)
wheel_s, spokes_s = helm_wheel("Wheel_Starboard", WHEEL_X, -WHEEL_Y, WHEEL_Z)
wheel_p.name, wheel_s.name = "Wheel_Port", "Wheel_Starboard"
spokes_p.name, spokes_s.name = "WheelSpokes_Port", "WheelSpokes_Starboard"
parts.update({"Mast": mast, "Shrouds": shrouds, "Furler": furler, "Furler_ink": drum,
              "Boom": boom, "Rudder": rudder, "Rudder_ink": rudder_ink,
              "Wheel_Port": wheel_p, "Wheel_Starboard": wheel_s,
              "WheelSpokes_Port": spokes_p, "WheelSpokes_Starboard": spokes_s})

aux = {"HydroEnvelope": hydro_probe}
for o in list(bpy.data.objects):
    if o.name not in parts and o.name not in aux:
        bpy.data.objects.remove(o)
all_x = [v.co.x for ob in parts.values() for v in ob.data.vertices]
X_MIN, X_MAX = min(all_x), max(all_x)
X_CENTER = 0.5*(X_MIN+X_MAX)
SX = 200.0/(X_MAX-X_MIN)
for ob in list(parts.values())+list(aux.values()):
    for v in ob.data.vertices:
        v.co.x = (v.co.x-X_CENTER)*SX


def fx(x):
    return (x-X_CENTER)*SX
log("x scale", round(SX, 6), "hull length", round((HULL_X1-HULL_X0)*SX, 3),
    "overall", round((X_MAX-X_MIN)*SX, 3))

log("railings: flat strips, bent to the deck edge")
assert abs(SX-SX_EST) < 0.003, ("rail pockets were sized for SX", SX_EST, SX)
_CX = [fx(x) for x in _RX]; _CY = [rail_y(x) for x in _RX]
_CS = [0.0]
for i in range(1, len(_RX)):
    _CS.append(_CS[-1]+math.hypot(_CX[i]-_CX[i-1], _CY[i]-_CY[i-1]))


def _interp(s, arr):
    i = min(max(bisect.bisect_right(_CS, s)-1, 0), len(_CS)-2)
    u = (s-_CS[i])/(_CS[i+1]-_CS[i])
    return arr[i]+(arr[i+1]-arr[i])*u


def c_at(s):
    """final (x, y) of the port fence centreline, outward unit normal, and pre-scale x at arc length s."""
    x0, y0 = _interp(s-0.05, _CX), _interp(s-0.05, _CY)
    x1, y1 = _interp(s+0.05, _CX), _interp(s+0.05, _CY)
    L = math.hypot(x1-x0, y1-y0); tx_, ty_ = (x1-x0)/L, (y1-y0)/L
    return (_interp(s, _CX), _interp(s, _CY)), (ty_, -tx_), _interp(s, _RX)


def s_post(x):
    i = min(max(int((95.0-x)/0.05), 0), len(_RX)-2)
    return _CS[i]+(_CS[i+1]-_CS[i])*((95.0-x)/0.05-i)


def deck_s(s):
    x = c_at(s)[2]
    return deck_z(x, rail_y(x))


RAIL_H = [(RAIL_POSTS[0], RAIL_POSTS[2], 10.5), (RAIL_POSTS[2], RAIL_POSTS[-2], 9.2),
          (RAIL_POSTS[-2], RAIL_POSTS[-1], 10.0)]          # pulpit, lifelines, pushpit: top above the deck
RAIL_TOP_W, RAIL_MID_W, RAIL_MID_Z, RAIL_POST_W = 0.85, 0.8, 4.7, 1.0


def flat_box(name, s0, s1, z0, z1):
    return rings_solid(name, [[(s0, z0, 0.0), (s0, z0, RAIL_T), (s0, z1, RAIL_T), (s0, z1, 0.0)],
                              [(s1, z0, 0.0), (s1, z0, RAIL_T), (s1, z1, RAIL_T), (s1, z1, 0.0)]])


def flat_band(name, s0, s1, zc_fun, h):
    n = max(2, int((s1-s0)/0.8)+1)
    rings = []
    for k in range(n+1):
        s = s0+(s1-s0)*k/n; zc = zc_fun(s)
        rings.append([(s, zc-h/2, 0.0), (s, zc-h/2, RAIL_T), (s, zc+h/2, RAIL_T), (s, zc+h/2, 0.0)])
    return rings_solid(name, rings)


def fine_s(ob, max_len=0.9):
    """split long strip-wise edges so the strip bends smoothly when mapped onto the deck-edge curve."""
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    for _ in range(8):
        long_ = [e for e in bm.edges if abs(e.verts[0].co.x-e.verts[1].co.x) > max_len]
        if not long_:
            break
        bmesh.ops.subdivide_edges(bm, edges=long_, cuts=1, use_grid_fill=False)
        bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(ob.data); bm.free()
    return ob


SP = {xp: s_post(xp) for xp in RAIL_POSTS}
strip = None
for xa, xb, h in RAIL_H:
    sa, sb = SP[xa]-0.45, SP[xb]+0.45
    b_ = flat_band("RailTop", sa, sb, lambda s, h=h: deck_s(s)+h-RAIL_TOP_W/2, RAIL_TOP_W)
    strip = b_ if strip is None else G.boolean(strip, b_, "UNION")
G.boolean(strip, flat_band("RailMid", SP[RAIL_POSTS[0]]-0.45, SP[RAIL_POSTS[-1]]+0.45,
                           lambda s: deck_s(s)+RAIL_MID_Z, RAIL_MID_W), "UNION")
RAIL_POST_TOPS = {}
for xp in RAIL_POSTS:
    h = max(h_ for xa, xb, h_ in RAIL_H if xb <= xp <= xa)
    top_ = deck_s(SP[xp])+h-0.05; ptop = RAIL_INFO[xp]["pad_top"]
    RAIL_POST_TOPS[xp] = round(top_-ptop, 2)
    G.boolean(strip, flat_box("RailPost", SP[xp]-RAIL_POST_W/2, SP[xp]+RAIL_POST_W/2, ptop, top_), "UNION")
    G.boolean(strip, flat_box("RailTab", SP[xp]-RAIL_TAB[0]/2, SP[xp]+RAIL_TAB[0]/2, ptop-RAIL_TAB[1], ptop+0.05), "UNION")
fine_s(strip)
log("rail strip", G.mesh_stats(strip), "post heights above pads", RAIL_POST_TOPS)
# transom return (flat coords: s = y, z, t), top and mid rails level with the side fence at the corner post
s_c = SP[RAIL_POSTS[-1]]
RET_TOP = deck_s(s_c)+RAIL_H[-1][2]
RET_MIDZ = deck_s(s_c)+RAIL_MID_Z
RET_YEND = rail_y(RAIL_POSTS[-1])+RAIL_T/2
RET_YC = RET_YEND-RAIL_POST_W/2                 # corner post of the return, flush with the fence's outer face
RET_CTOP = RAIL_INFO[RAIL_POSTS[-1]]["pad_top"]   # it stands on the side fence's corner pad, no tab, glued
ret = flat_box("RetTop", RET_LEGS[0]-0.45, RET_YEND, RET_TOP-RAIL_TOP_W, RET_TOP)
G.boolean(ret, flat_box("RetMid", RET_LEGS[0]-0.45, RET_YEND, RET_MIDZ-RAIL_MID_W/2, RET_MIDZ+RAIL_MID_W/2), "UNION")
G.boolean(ret, flat_box("RetCorner", RET_YC-RAIL_POST_W/2, RET_YC+RAIL_POST_W/2, RET_CTOP, RET_TOP-0.05), "UNION")
for j, yl in enumerate(RET_LEGS):
    ptop = RET_INFO[j]["pad_top"]
    G.boolean(ret, flat_box("RetPost", yl-RAIL_POST_W/2, yl+RAIL_POST_W/2, ptop, RET_TOP-0.05), "UNION")
    G.boolean(ret, flat_box("RetTab", yl-RAIL_TAB[0]/2, yl+RAIL_TAB[0]/2, ptop-RAIL_TAB[1], ptop+0.05), "UNION")
RET_XF = fx(RET_X)
_post_aft = c_at(s_c+RAIL_POST_W/2)[0][0]
log("transom return", G.mesh_stats(ret), "front face x", round(RET_XF+RAIL_T/2, 3), "corner post aft face x",
    round(_post_aft, 3), "top z", round(RET_TOP, 2), "mid z", round(RET_MIDZ, 2))


def _flip(o):
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.reverse_faces(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()


def map_strip(name, src, side):
    o = dup(src, name)
    for v in o.data.vertices:
        s, z, t = v.co
        (cx_, cy_), (nx_, ny_), _ = c_at(s)
        v.co = Vector((cx_+nx_*(t-RAIL_T/2), side*(cy_+ny_*(t-RAIL_T/2)), z))
    if side < 0:
        _flip(o)
    return o


def map_ret(name, src, side):
    o = dup(src, name)
    for v in o.data.vertices:
        s, z, t = v.co
        v.co = Vector((RET_XF+t-RAIL_T/2, side*s, z))
    if side < 0:
        _flip(o)
    return o


rails = {"Rail_Port": map_strip("Rail_Port", strip, 1), "Rail_Starboard": map_strip("Rail_Starboard", strip, -1),
         "RailAft_Port": map_ret("RailAft_Port", ret, 1), "RailAft_Starboard": map_ret("RailAft_Starboard", ret, -1)}
# flat print layout: two identical strips nested along their sheer, the two (identical) returns stacked after them
_zs = [v.co.y for v in strip.data.vertices]; _ss = [v.co.x for v in strip.data.vertices]
_lo = [deck_s(s) for s in _ss]
NEST_DZ = max(z-d for z, d in zip(_zs, _lo))-min(z-d for z, d in zip(_zs, _lo))+1.2
_rz = [v.co.y for v in ret.data.vertices]; _ry = [v.co.x for v in ret.data.vertices]
pr = []
for k in range(2):
    o = dup(strip, "RailPrint%d" % k)
    for v in o.data.vertices:
        v.co = Vector((v.co.x-min(_ss), v.co.y-min(_zs)+k*NEST_DZ, v.co.z))
    pr.append(o)
for k in range(2):
    o = dup(ret, "RetPrint%d" % k)
    for v in o.data.vertices:
        v.co = Vector((max(_ss)-min(_ss)+2.0+v.co.x-min(_ry), v.co.y-min(_rz)+k*(max(_rz)-min(_rz)+1.5), v.co.z))
    pr.append(o)
rails_print = pr[0]
for o in pr[1:]:
    G.boolean(rails_print, o, "UNION")
_bad = G.mesh_stats(rails_print)["nonmanifold"]
assert _bad == 0, ("rail print sheet non-manifold", _bad)
os.makedirs(os.path.join(OUT, "print"), exist_ok=True)
for o in bpy.data.objects:
    o.select_set(o is rails_print)
bpy.ops.wm.stl_export(filepath=os.path.join(OUT, "print", "Rails_print.stl"), export_selected_objects=True)
_pb = [max(v.co[i] for v in rails_print.data.vertices)-min(v.co[i] for v in rails_print.data.vertices) for i in range(3)]
RAIL_STATS = {"posts_x_prescale": RAIL_POSTS, "posts_x": [round(fx(x), 2) for x in RAIL_POSTS],
              "heights_above_deck": {"pulpit": 10.5, "lifelines": 9.2, "pushpit": 10.0}, "mid_rail": RAIL_MID_Z,
              "strip_t": RAIL_T, "top_rail_w": RAIL_TOP_W, "mid_rail_w": RAIL_MID_W, "post_w": RAIL_POST_W,
              "tab": RAIL_TAB, "pocket": RAIL_POCKET, "pad": RAIL_PAD, "fence_inboard_of_edge": RAIL_IN,
              "strip_length": round(max(_ss)-min(_ss), 2), "nest_dz": round(NEST_DZ, 2),
              "print_sheet_mm": [round(v, 2) for v in _pb], "post_heights_above_pads": RAIL_POST_TOPS,
              "pads": {str(k): {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in v.items()}
                       for k, v in RAIL_INFO.items()},
              "returns": {"x": round(RET_XF, 3), "legs_y": [round(RET_YC, 3)]+list(RET_LEGS), "top_z": round(RET_TOP, 2),
                          "pad_tops": [round(RET_CTOP, 4)]+[round(RET_INFO[j]["pad_top"], 4) for j in range(len(RET_LEGS))],
                          "corner_post": "tab-less, stands on the corner pad, glued to the corner post's aft face",
                          "mid_z": round(RET_MIDZ, 2), "y_end": round(RET_YEND, 2),
                          "front_face_to_corner_post": round(_post_aft-(RET_XF+RAIL_T/2), 3)}}
log("rail print sheet", [round(v, 1) for v in _pb], "nest dz", round(NEST_DZ, 2))
for o in [strip, ret, rails_print]:
    bpy.data.objects.remove(o, do_unlink=True)
parts.update(rails)
BALLAST_CAVITY_CM3 = CAVITY_CM3*SX
PELLET_VOL_CM3 = 4*math.pi*(0.15**3)/3
PELLET_COUNT = int(BALLAST_CAVITY_CM3*0.64/PELLET_VOL_CM3)
log("ballast usable cm3", round(BALLAST_CAVITY_CM3, 3),
    "3mm lead balls at 64% packing", PELLET_COUNT, "mass g", round(PELLET_COUNT*0.160, 2))
tot = {}
for nmn, ob in parts.items():
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-3, edges=bm.edges[:])   # sub-micron keyhole bridges from EXACT
    bmesh.ops.delete(bm, geom=[e for e in bm.edges if not e.link_faces], context="EDGES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bmesh.ops.triangulate(bm, faces=bm.faces)
    by_key = {}
    for f in bm.faces:
        by_key.setdefault(frozenset(v.index for v in f.verts), []).append(f)
    folds = [f for fs in by_key.values() if len(fs) == 2 for f in fs]   # zero-volume membranes (keyhole folds)
    if folds:
        bmesh.ops.delete(bm, geom=folds, context="FACES_ONLY")
        bmesh.ops.delete(bm, geom=[e for e in bm.edges if not e.link_faces], context="EDGES")
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
        log("removed fold face pairs", nmn, len(folds)//2)
    crumbs = []                                    # boolean needles thinner than 0.05 mm: unprintable
    seen = set()
    for f0 in bm.faces:
        if f0 in seen:
            continue
        comp, stack = [], [f0]; seen.add(f0)
        while stack:
            f = stack.pop(); comp.append(f)
            for e in f.edges:
                for g in e.link_faces:
                    if g not in seen:
                        seen.add(g); stack.append(g)
        co = [v.co for f in comp for v in f.verts]
        ext = sorted(max(c[k] for c in co)-min(c[k] for c in co) for k in range(3))
        if ext[0] < 0.05 and ext[1] < 0.1:
            crumbs += comp
    if crumbs:
        bmesh.ops.delete(bm, geom=crumbs, context="FACES")
        log("removed sub-0.05 mm boolean crumbs", nmn, len(crumbs))
    tri_bad = sum(1 for e in bm.edges if not e.is_manifold)
    log("triangulated topology", nmn, "nonmanifold", tri_bad)
    if tri_bad:
        for edge in [e for e in bm.edges if not e.is_manifold][:5]:
            log("triangulated bad edge", nmn,
                tuple(tuple(round(c, 6) for c in v.co) for v in edge.verts),
                "faces", len(edge.link_faces))
            for face in edge.link_faces:
                log("triangulated bad face", tuple(tuple(round(c, 6) for c in v.co) for v in face.verts),
                    tuple(round(c, 6) for c in face.normal))
    if tri_bad:
        bm.free()
        raise RuntimeError("non-manifold after STL triangulation: %s (%d edges)" % (nmn, tri_bad))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(nmn+"_tri")
    bm.to_mesh(me); bm.free()
    old = ob.data; ob.data = me; bpy.data.meshes.remove(old)
    s = G.mesh_stats(ob); tot[nmn] = s
    log("triangulated part stats", nmn, s)
    for o in bpy.data.objects:
        o.select_set(o is ob)
    bpy.ops.wm.stl_export(filepath=os.path.join(OUT, nmn+".stl"), export_selected_objects=True)
for o in bpy.data.objects:
    o.select_set(o is aux["HydroEnvelope"])
bpy.ops.wm.stl_export(filepath=os.path.join(OUT, "_HydroEnvelope.stl"), export_selected_objects=True)
bpy.data.objects.remove(aux["HydroEnvelope"], do_unlink=True)
json.dump({"parts": tot, "canoe_cm3": vol*SX/1000, "LCB": (LCB-X_CENTER)*SX,
           "x_scale": SX, "hull_length_mm": (HULL_X1-HULL_X0)*SX,
           "overall_length_mm": (X_MAX-X_MIN)*SX,
           "displacement_curve_cm3_at_z_mm": {
               wl: round(cm3*SX, 3) for wl, cm3 in DISPLACEMENT_CURVE.items()},
           "assembled_displacement_curve_cm3_at_z_mm": {
               wl: round(cm3*SX, 3) for wl, cm3 in ASSEMBLY_DISPLACEMENT_CURVE.items()},
           "ballast_cavity_cm3": BALLAST_CAVITY_CM3,
           "lead_3mm_balls_64pct": PELLET_COUNT,
           "lead_mass_g_64pct": round(PELLET_COUNT*0.160, 2),
           "total_parts_cm3": round(sum(v["vol_cm3"] for v in tot.values()), 3),
           "lugs": [((x-X_CENTER)*SX, y) for x, y in LUGS],
           "bulb": {"x_center": fx(X_BULB), "cavity_x": [fx(v) for v in CAV_X], "posts_x": [fx(v) for v in POSTS],
                    "split_z": BULB_SPLIT, "post_r": POST_R, "post_top_z": POST_TOP, "length": BULB_L*SX,
                    "half_width": BULB_HW, "half_height": BULB_HH, "z_centre": BULB_ZC, "wall": BULB_WALL,
                    "flat_z": BULB_FLAT, "floor_z": BULB_FLOOR},
           "rig": {"mast_aft_x": fx(MAST_XA), "mast_heel_z": MAST_HEEL, "mast_top_z": MAST_TOP,
                   "gooseneck_z": GOOSE_Z, "boom_top_z": BOOM_Z0+BOOM_H, "boom_holes_x": {k: fx(v) for k, v in BOOM_HOLES.items()},
                   "masthead_hole_z": MASTHEAD_HOLE_Z, "hounds_z": HOUNDS[1], "spreaders": SPREADERS,
                   "shroud_strip_mm": [SHR_T, SHR_W], "shroud_paths_yz": SHROUD_PATHS,
                   "shroud_feet": [(fx(x), y, z) for x, y, z in SHROUD_FEET],
                   "chainplates": [{"x": fx(x), "y": y, "deck_z": round(z, 2), "top_z": round(t, 2),
                                    "pocket_seat": CHAIN_SEAT, "pocket_depth": CHAIN_DEPTH} for x, y, z, t in CHAINPLATES],
                   "tab_mm": [TAB_W, TAB_W, TAB_L], "sheet_eye": (fx(SHEET_EYE[0]), 0.0, SHEET_EYE[2])},
           "furler": {"display_only": True, "axis_foot": (fx(FURL_A[0]), 0.0, FURL_A[1]),
                      "axis_head": (fx(HOOK_B[0]), 0.0, HOOK_B[1]), "length_mm": round(FURL_L*1.0, 2),
                      "body_max_width_mm": 2*BODY_A, "flat_face_y": FURL_Y0, "drum_s": [DRUM_S0, DRUM_S1],
                      "foot_tab": [2*FTAB_A, FTAB_H, 3.4], "stemhead_pocket": FPOCKET,
                      "hook_x": (fx(hx0), fx(hx1)), "hook_top_z": hz1, "hook_clearance": HOOK_CLR},
           "display_only_parts": ["Furler", "Furler_ink"],
           "wheel": {"x": fx(WHEEL_X), "y": WHEEL_Y, "z": WHEEL_Z, "r": WHEEL_R},
           "rudder_x": fx(X_RUD)}, open(os.path.join(OUT, "stats.json"), "w"), indent=1)

def material(name, color, roughness=0.4):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    if shader:
        shader.inputs["Base Color"].default_value = color
        shader.inputs["Roughness"].default_value = roughness
    return mat


def srgb(hexs):
    c = [int(hexs[i:i+2], 16)/255.0 for i in (1, 3, 5)]
    return tuple((v/12.92 if v <= 0.04045 else ((v+0.055)/1.055)**2.4) for v in c)+(1.0,)


PRINT_COLOURS = {"white": "#F6F5EE", "blue": "#15499D", "ink": "#173347", "teak": "#BF8A54"}
PART_COLOUR = {"Lower_blue": "blue", "Lower_white": "white", "Lower_ink": "ink", "Upper_white": "white",
               "Upper_ink": "ink", "Upper_teak": "teak", "Window_ink": "ink", "Fin_cap": "blue",
               "Ballast_cup": "blue", "Mast": "white", "Shrouds": "ink", "Furler": "white", "Furler_ink": "ink",
               "Boom": "white", "Rudder": "blue", "Rudder_ink": "ink",
               "Wheel_Port": "ink", "Wheel_Starboard": "ink", "WheelSpokes_Port": "white",
               "WheelSpokes_Starboard": "white", "Rail_Port": "ink", "Rail_Starboard": "ink",
               "RailAft_Port": "ink", "RailAft_Starboard": "ink"}
PRINT_MATS = {k: material("PLA %s %s" % (k, v), srgb(v), 0.55) for k, v in PRINT_COLOURS.items()}
for name, ob in parts.items():
    ob["printable"] = True
    ob["print_colour"] = PART_COLOUR[name]
    ob.data.materials.append(PRINT_MATS[PART_COLOUR[name]])

LUFF_X = MAST_XA-0.2
SAIL_TACK_Z = BOOM_Z0+BOOM_H+0.4
SAIL_HEAD_Z = MAST_TOP-5.6
sail_xz = [(LUFF_X, SAIL_TACK_Z), (LUFF_X, SAIL_HEAD_Z), (BOOM_HOLES["clew"], SAIL_TACK_Z)]
sail_area = 0.0
for i, (x0, z0) in enumerate(sail_xz):
    x1, z1 = sail_xz[(i+1) % len(sail_xz)]
    sail_area += x0*z1-x1*z0
sail_area = abs(sail_area)*0.5*SX/100.0
with open(os.path.join(OUT, "stats.json"), "r") as f:
    build_stats = json.load(f)
build_stats["paper_sail_area_cm2"] = round(sail_area, 2)
build_stats["sail"] = {"luff_x": fx(LUFF_X), "tack_z": SAIL_TACK_Z, "head_z": SAIL_HEAD_Z,
                       "clew_x": fx(BOOM_HOLES["clew"]), "luff_mm": SAIL_HEAD_Z-SAIL_TACK_Z,
                       "foot_mm": (LUFF_X-BOOM_HOLES["clew"])*SX}
REEF_HEAD_Z = SPREADERS[1][0]+1.8
build_stats["sails"] = {}
for nm_, (hz_, cx_) in {"full": (SAIL_HEAD_Z, BOOM_HOLES["clew"]),
                        "medium": (REEF_HEAD_Z, BOOM_HOLES["clew medium"]),
                        "start": (REEF_HEAD_Z, BOOM_HOLES["clew start"])}.items():
    luff_, foot_ = hz_-SAIL_TACK_Z, (LUFF_X-cx_)*SX
    build_stats["sails"][nm_] = {"luff_mm": round(luff_, 2), "foot_mm": round(foot_, 2),
                                 "area_cm2": round(luff_*foot_/200.0, 2), "head_z": round(hz_, 2),
                                 "clew_hole_x": round(fx(cx_), 2)}
build_stats["luff_tie_z_avoid"] = [[z_-1.3, z_+1.3] for z_, _ in SPREADERS]
json.dump(build_stats, open(os.path.join(OUT, "stats.json"), "w"), indent=1)
sail = prism("Preview_PaperSail", [(fx(x), z) for x, z in sail_xz], "y", -0.12, 0.12)
sail["printable"] = False
sail.data.materials.append(material("Paper sail preview", (0.96, 0.94, 0.84, 1)))

stay_paths = {"Preview_Mainsheet": [(fx(TRAV_X), 0.0, BOOM_Z0), (fx(SHEET_EYE[0]), 0.0, SHEET_EYE[2])]}
build_stats.update(build_stats_extra)
build_stats["anchor"] = {"toe_u": round(ANCHOR_U0, 2), "crown_front_x_prescale": ANCH_X1, "cheek_end_x_prescale": CHEEK_X1,
                         "roller": ROLLER, "shackle": SHACKLE, "fluke_shadow_gap_mm": FL_OT,
                         "shank_daylight_to_cheeks_mm": round(1.15-0.5, 2), "shank_air_over_plank_mm": 0.9}
build_stats["railings"] = RAIL_STATS
build_stats["cleats"] = {"xy_prescale": CLEATS, "flange": CLEAT_FLANGE, "top_above_deck": 2.72, "length": 4.2,
                         "width": 1.2, "colour": "ink"}
build_stats["spreaders_section"] = SPREADER_SEC
json.dump(build_stats, open(os.path.join(OUT, "stats.json"), "w"), indent=1)
rig_mat = material("Mainsheet thread preview", (0.04, 0.055, 0.07, 1))
for name, path in stay_paths.items():
    for i, (p0, p1) in enumerate(zip(path, path[1:])):
        segment = rod_between("%s_%d" % (name, i), p0, p1, 0.12)
        segment["printable"] = False
        segment.data.materials.append(rig_mat)

scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 0.001
scene.unit_settings.length_unit = "MILLIMETERS"
world = scene.world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.22, 0.25, 0.29, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.75
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1200
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.view_settings.view_transform = "AgX"
camera_data = bpy.data.cameras.new("Margaret presentation camera")
camera = bpy.data.objects.new("Margaret presentation camera", camera_data)
scene.collection.objects.link(camera)
camera.location = (380.0, -700.0, 380.0)
camera.rotation_euler = (Vector((0.0, 0.0, 85.0))-camera.location).to_track_quat("-Z", "Y").to_euler()
camera.data.lens = 60.0
scene.camera = camera
for name, loc, power, size in (
    ("Key", (170.0, -240.0, 300.0), 180.0, 220.0),
    ("Fill", (-240.0, -120.0, 160.0), 100.0, 260.0),
    ("Rim", (0.0, 220.0, 260.0), 160.0, 220.0),
):
    light_data = bpy.data.lights.new(name, "AREA")
    light_data.energy = power
    light_data.shape = "DISK"
    light_data.size = size
    light = bpy.data.objects.new(name, light_data)
    scene.collection.objects.link(light)
    light.location = loc
    light.rotation_euler = (Vector((0.0, 0.0, 70.0))-light.location).to_track_quat("-Z", "Y").to_euler()

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "Margaret.blend"))
log("DONE", {k: (v["vol_cm3"], v["nonmanifold"]) for k, v in tot.items()})
