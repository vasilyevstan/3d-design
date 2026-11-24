# Margaret revision 2: fair hull generator.
# Runs in Blender MCP safe mode (bpy/bmesh/mathutils/stdlib only, no closures, no file IO)
# and headless (model.py exec()s this file). Units mm, bow +X, port +Y, DWL z = 0.
import bpy, bmesh, math, bisect
from mathutils import Vector


def spl(pts):
    xs = [float(p[0]) for p in pts]; ys = [float(p[1]) for p in pts]; n = len(xs)
    h = [xs[i+1]-xs[i] for i in range(n-1)]
    a = [0.0]*n; b = [1.0]*n; c = [0.0]*n; d = [0.0]*n
    for i in range(1, n-1):
        a[i], b[i], c[i] = h[i-1], 2*(h[i-1]+h[i]), h[i]
        d[i] = 6*((ys[i+1]-ys[i])/h[i]-(ys[i]-ys[i-1])/h[i-1])
    for i in range(1, n):
        m = a[i]/b[i-1]; b[i] -= m*c[i-1]; d[i] -= m*d[i-1]
    M = [0.0]*n
    M[-1] = d[-1]/b[-1]
    for i in range(n-2, -1, -1):
        M[i] = (d[i]-c[i]*M[i+1])/b[i]
    return (xs, ys, M, h)


def ev(S, x):
    xs, ys, M, h = S
    if x <= xs[0]:
        s = (ys[1]-ys[0])/h[0]-h[0]*(2*M[0]+M[1])/6
        return ys[0]+s*(x-xs[0])
    if x >= xs[-1]:
        s = (ys[-1]-ys[-2])/h[-1]+h[-1]*(2*M[-1]+M[-2])/6
        return ys[-1]+s*(x-xs[-1])
    i = min(max(bisect.bisect_right(xs, x)-1, 0), len(xs)-2)
    t = x-xs[i]; u = xs[i+1]-x
    return (M[i]*u**3+M[i+1]*t**3)/(6*h[i])+(ys[i]/h[i]-M[i]*h[i]/6)*u+(ys[i+1]/h[i]-M[i+1]*h[i]/6)*t


def prof(pts):
    s = [0.0]
    for p, q in zip(pts, pts[1:]):
        s.append(s[-1]+math.dist(p, q))
    fx = spl(list(zip(s, [p[0] for p in pts])))
    fz = spl(list(zip(s, [p[1] for p in pts])))
    T = [(ev(fx, s[-1]*i/3000), ev(fz, s[-1]*i/3000)) for i in range(3001)]
    return ([p[0] for p in T], [p[1] for p in T])


def pev(T, x):
    xs, zs = T
    if x <= xs[0]:
        return zs[0]
    if x >= xs[-1]:
        return zs[-1]
    i = min(max(bisect.bisect_right(xs, x)-1, 0), len(xs)-2)
    return zs[i]+(zs[i+1]-zs[i])*(x-xs[i])/max(xs[i+1]-xs[i], 1e-12)


def hull_tables(P):
    return {"zs": spl(P["sheer"]), "bs": spl(P["half_beam"]), "zk": prof(P["keel"]),
            "be": spl(P["deadrise"]), "th": spl(P["flare"]), "ka": spl(P["bilge_low"]),
            "kb": spl(P["bilge_high"]), "rd": spl(P["round"]), "x_stem": P["x_stem"]}


def bez(c, t):
    u = 1-t
    return (u**3*c[0][0]+3*u*u*t*c[1][0]+3*u*t*t*c[2][0]+t**3*c[3][0],
            u**3*c[0][1]+3*u*u*t*c[1][1]+3*u*t*t*c[2][1]+t**3*c[3][1])


def half_section(H, x, n, inset_base=0.0, inset_bump=0.0, bump_x=None, bump_z=None, bumps=None):
    """Half-section from centreline keel to sheer as n (y, z) points, equal arc length.
    Outer surface = Bezier of reduced half-beam plus a quarter-round keel/stem radius.
    inset > 0 offsets along the true inward normal; points crossing the centreline are clipped."""
    zs = ev(H["zs"], x); zk = pev(H["zk"], x)
    rd = max(ev(H["rd"], x), 0.05)
    B = max(ev(H["bs"], x)-rd, 1e-4)
    Hh = max(zs-zk, 1e-4)
    be = math.radians(ev(H["be"], x)); th = math.radians(ev(H["th"], x))
    a = ev(H["ka"], x)*B; b = ev(H["kb"], x)*Hh
    c = [(0.0, zk), (a*math.cos(be), zk+a*math.sin(be)), (B-b*math.sin(th), zs-b*math.cos(th)), (B, zs)]
    m = 900
    dense = [bez(c, (i/m)**2) for i in range(m+1)]
    s = [0.0]
    for p, q in zip(dense, dense[1:]):
        s.append(s[-1]+math.dist(p, q))
    dzk = (pev(H["zk"], x+0.25)-pev(H["zk"], x-0.25))/0.5
    bz = rd*math.sqrt(1+dzk*dzk)
    rounded = []
    for (y, z), si in zip(dense, s):
        f = min(1.0, si/bz)
        rounded.append((y+rd*math.sqrt(max(0.0, 1-(1-f)**2)), z))
    if inset_base > 0:
        off = []
        for i in range(m+1):
            p0 = rounded[max(i-1, 0)]; p1 = rounded[min(i+1, m)]
            dy, dz = p1[0]-p0[0], p1[1]-p0[1]
            L = math.hypot(dy, dz) or 1.0
            y, z = rounded[i]
            t = inset_base
            if inset_bump and bump_x is not None:
                wx = ev_window(bump_x, x)
                wz = ev_window(bump_z, z)
                t += inset_bump*wx*wz
            for amp, bx, bzw in (bumps or ()):
                t += amp*ev_window(bx, x)*ev_window(bzw, z)
            off.append((y-dz/L*t, z+dy/L*t))
        k = 0
        while k < m and off[k][0] < 0:
            k += 1
        if k > 0:
            (y0, z0), (y1, z1) = off[k-1], off[k]
            z_c = z0+(z1-z0)*(0-y0)/((y1-y0) or 1e-9)
            off = [(0.0, z_c)]+off[k:]
        else:
            off[0] = (0.0, off[0][1])
        rounded = off
    s = [0.0]
    for p, q in zip(rounded, rounded[1:]):
        s.append(s[-1]+math.dist(p, q))
    out = []
    j = 0
    N = len(rounded)-1
    for i in range(n):
        u = i/(n-1)
        target = s[-1]*(u-0.75*math.sin(math.pi*u)/math.pi)
        while j < N-1 and s[j+1] < target:
            j += 1
        t = (target-s[j])/max(s[j+1]-s[j], 1e-12)
        out.append((rounded[j][0]+(rounded[j+1][0]-rounded[j][0])*t, rounded[j][1]+(rounded[j+1][1]-rounded[j][1])*t))
    out[0] = (0.0, out[0][1])
    return out, zs


def ev_window(W, v):
    """Smooth 0..1 window: W = (lo, hi, ramp)."""
    lo, hi, r = W
    if v <= lo-r or v >= hi+r:
        return 0.0
    if lo <= v <= hi:
        return 1.0
    u = (lo-v)/r if v < lo else (v-hi)/r
    return 0.5+0.5*math.cos(math.pi*u)


def station_list(x0, x1, x_fine, d_coarse, d_fine):
    xs = []
    x = x0
    while x < x_fine:
        xs.append(x); x += d_coarse
    x = x_fine
    while x < x1-1e-6:
        xs.append(x); x += d_fine
    xs.append(x1)
    return xs


def loft_solid(name, H, xs, n, inset=0.0, top_extra=0.0, k_top=9, bump=None):
    """Closed solid from station rings. Top closes flat at sheer (+top_extra for cutters)."""
    bm = bmesh.new()
    rings = []
    for x in xs:
        if bump is None:
            hs, zs = half_section(H, x, n, inset)
        else:
            hs, zs = half_section(H, x, n, inset, bump[0], bump[1], bump[2])
        if top_extra > 0:
            hs = hs+[(hs[-1][0], zs+top_extra)]
        ztop = hs[-1][1]
        B = hs[-1][0]
        ring = [(-y, z) for (y, z) in reversed(hs)]+[(y, z) for (y, z) in hs[1:]]
        ring += [(B-2*B*j/(k_top+1), ztop) for j in range(1, k_top+1)]
        rings.append([bm.verts.new((x, y, z)) for (y, z) in ring])
    for r0, r1 in zip(rings, rings[1:]):
        L = len(r0)
        for j in range(L):
            bm.faces.new((r0[j], r0[(j+1) % L], r1[(j+1) % L], r1[j]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def cut_plane(ob, co, no):
    """Remove everything on the +no side of the plane and cap the cut."""
    bm = bmesh.new(); bm.from_mesh(ob.data)
    geom = list(bm.verts)+list(bm.edges)+list(bm.faces)
    bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=co, plane_no=no, clear_outer=True)
    edges = [e for e in bm.edges if e.is_boundary]
    bmesh.ops.holes_fill(bm, edges=edges)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data); bm.free()


def box(name, x0, x1, y0, y1, z0, z1):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x = x0 if v.co.x < 0 else x1
        v.co.y = y0 if v.co.y < 0 else y1
        v.co.z = z0 if v.co.z < 0 else z1
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    return ob


def boolean(a, b, op, remove_b=True):
    mod = a.modifiers.new("bool", "BOOLEAN")
    mod.operation = op; mod.solver = "EXACT"; mod.object = b
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(a.evaluated_get(dg))
    a.modifiers.remove(mod)
    old = a.data; a.data = me; bpy.data.meshes.remove(old)
    if remove_b:
        bpy.data.meshes.remove(b.data)
    return a


def transom_plane(P, shift=0.0):
    (x0, z0), (x1, z1) = P["transom"]["knuckle"], P["transom"]["top"]
    dx, dz = x1-x0, z1-z0
    L = math.hypot(dx, dz)
    no = Vector((-dz/L, 0, dx/L))
    co = Vector((x0, 0, z0))-no*shift
    return co, no


def mesh_stats(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    nm = sum(1 for e in bm.edges if not e.is_manifold)
    vol = bm.calc_volume(signed=False)
    bm.free()
    return {"verts": len(ob.data.vertices), "faces": len(ob.data.polygons), "nonmanifold": nm, "vol_cm3": round(vol/1000, 3)}
