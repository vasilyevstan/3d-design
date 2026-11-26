import math, re, sys, struct, numpy as np
# Usage: python3 wall_fill.py v7j  (run from the build folder; compares Hull_lower G-code fill with the STL section)
ver = sys.argv[1]
A = math.pi*(1.75/2)**2
def stl(p):
    b=open(p,"rb").read(); n=struct.unpack("<I",b[80:84])[0]
    a=np.frombuffer(b[84:84+n*50],dtype=np.dtype([("n","<3f4"),("v","<9f4"),("a","<u2")]))
    return a["v"].reshape(-1,3,3).astype(float)
T=np.concatenate([stl(f"yacht-build/{ver}/{n}.stl") for n in ("Lower_blue","Lower_white","Lower_ink")])
N=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0])
def area(z):
    d=T[:,:,2]-z; tot=0.0
    m=(d.min(1)<0)&(d.max(1)>0)
    for t,dd,n in zip(T[m],d[m],N[m]):
        pts=[]
        for i in range(3):
            j=(i+1)%3
            if (dd[i]<0)!=(dd[j]<0):
                u=dd[i]/(dd[i]-dd[j]); pts.append(t[i]+(t[j]-t[i])*u)
        if len(pts)!=2: continue
        p,q=pts
        dx,dy=q[0]-p[0],q[1]-p[1]
        if dy*n[0]-dx*n[1]<0: p,q=q,p
        tot+=0.5*(p[0]*q[1]-q[0]*p[1])
    return tot
obj=None; feat=None; z=None; h=None; first=None
lay={}
er=re.compile(r"E(-?[\d.]+)")
for line in open(f"yacht-build/{ver}/plate/x/Metadata/plate_1.gcode"):
    if line.startswith("; Z_HEIGHT:"): z=float(line.split(":")[1]); continue
    if line.startswith("; LAYER_HEIGHT:"): h=float(line.split(":")[1]); continue
    if line.startswith("; start printing object, unique label id:"):
        obj=int(line.split(":")[1]); first=obj if first is None else min(first,obj); continue
    if line.startswith("; stop printing object"): obj=None; continue
    if line.startswith("; FEATURE:"): feat=line.split(":",1)[1].strip(); continue
    if obj is not None and line[:3] in ("G1 ","G2 ","G3 ") and "E" in line:
        cmd=line.split(";")[0]; m=er.search(cmd)
        if not m or not re.search(r"[XYIJ]-?[\d.]",cmd): continue
        e=float(m.group(1))
        if e<=0 or feat.startswith("Support"): continue
        lay.setdefault((obj,round(z,3),h),{}); d=lay[(obj,round(z,3),h)]; d[feat]=d.get(feat,0)+e*A
rows=[]
for (o,zz,hh),d in sorted(lay.items()):
    if o!=first: continue
    zm=2.5-(zz-hh/2)
    if zm>-0.2 or zm<-12: continue
    a=area(zm); v=sum(d.values())
    rows.append((zz,zm,a,v/hh/a if a>0 else 0,{k:round(x/hh,1) for k,x in d.items()}))
for r in [r for i, r in enumerate(rows) if i % 3 == 0 or r[3] < 0.85]:
    print(f"print z {r[0]:5.2f}  model z {r[1]:6.2f}  section {r[2]:7.1f} mm2  deposited/section {r[3]:.2f}  ", r[4])
print("median ratio", round(float(np.median([r[3] for r in rows])),3), "min", round(min(r[3] for r in rows),3))
