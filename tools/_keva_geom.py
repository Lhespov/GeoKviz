# -*- coding: utf-8 -*-
"""Extract GEO geometry (rivers as lines, islands as polys) for keva features."""
import json, math

NE="C:/Users/andra/claude/_ne/"

def rdp(pts, eps):
    """Douglas-Peucker on list of [x,y]; returns simplified list."""
    if len(pts)<3: return pts[:]
    dmax=0.0; idx=0
    a=pts[0]; b=pts[-1]
    for i in range(1,len(pts)-1):
        d=perp(pts[i],a,b)
        if d>dmax: dmax=d; idx=i
    if dmax>eps:
        l=rdp(pts[:idx+1],eps); r=rdp(pts[idx:],eps)
        return l[:-1]+r
    return [a,b]

def perp(p,a,b):
    ax,ay=a; bx,by=b; px,py=p
    dx=bx-ax; dy=by-ay
    if dx==0 and dy==0: return math.hypot(px-ax,py-ay)
    t=((px-ax)*dx+(py-ay)*dy)/(dx*dx+dy*dy)
    t=max(0,min(1,t))
    cx=ax+t*dx; cy=ay+t*dy
    return math.hypot(px-cx,py-cy)

def pip(pt, ring):
    """ring = list of [lng,lat]; pt=(lng,lat)."""
    x,y=pt; inside=False; n=len(ring); j=n-1
    for i in range(n):
        xi,yi=ring[i][0],ring[i][1]; xj,yj=ring[j][0],ring[j][1]
        if ((yi>y)!=(yj>y)) and (x < (xj-xi)*(y-yi)/((yj-yi) or 1e-15)+xi):
            inside=not inside
        j=i
    return inside

def ring_area(ring):
    s=0.0; n=len(ring)
    for i in range(n):
        x1,y1=ring[i][0],ring[i][1]; x2,y2=ring[(i+1)%n][0],ring[(i+1)%n][1]
        s+=x1*y2-x2*y1
    return abs(s)/2

# ---------- ISLANDS ----------
land=json.load(open(NE+"ne_10m_land.geojson",encoding="utf-8"))
polys=[]  # list of exterior rings [[lng,lat],...]
for f in land["features"]:
    g=f["geometry"]
    if g["type"]=="Polygon":
        polys.append(g["coordinates"][0])
    else:
        for poly in g["coordinates"]:
            polys.append(poly[0])

islands={
 198:("britanija",54.0,-2.0), 199:("irska",53.0,-8.0), 200:("island",65.0,-18.0),
 201:("sicilija",37.5,14.0), 202:("sardinija",40.0,9.0), 203:("rodos",36.17,27.92),
 204:("lezbos",39.21,26.28), 205:("krit",35.21,24.91), 206:("madagaskar",-20.0,47.0),
 207:("papua",-6.0,142.0),
}

GEO={}
for fid,(name,lat,lng) in islands.items():
    cand=[r for r in polys if pip((lng,lat),r)]
    if not cand:
        # ellipse fallback ~0.4deg
        ring=[[lng+0.4*math.cos(t),lat+0.4*math.sin(t)] for t in [k*math.pi/8 for k in range(16)]]
        chosen=ring; note="ELLIPSE-FALLBACK"
    else:
        chosen=min(cand,key=ring_area); note=""
    # simplify; pick eps by bbox size
    xs=[p[0] for p in chosen]; ys=[p[1] for p in chosen]
    span=max(max(xs)-min(xs),max(ys)-min(ys))
    eps=max(0.01,span/120.0)
    s=rdp(chosen,eps)
    # to [lat,lng] rounded
    c=[[round(p[1],3),round(p[0],3)] for p in s]
    GEO[fid]={"m":"poly","c":[c]}
    print(f"{fid} {name}: pts {len(chosen)}->{len(c)} span {span:.1f} {note}")

# ---------- RIVERS ----------
riv=json.load(open(NE+"ne_10m_rivers_lake_centerlines.geojson",encoding="utf-8"))
rivers={
 208:("volga",["Volga"]), 209:("neva",["Neva"]), 210:("visla",["Vistula"]),
 211:("zapadna_dvina",["Daugava"]), 212:("temza",["Thames"]), 213:("loara",["Loire"]),
 214:("gvadalkivir",["Guadalquivir"]), 215:("arkanzas",["Arkansas"]), 216:("tenesi",["Tennessee"]),
}
def collect_lines(names):
    out=[]
    nl=[n.lower() for n in names]
    for f in riv["features"]:
        p=f["properties"]
        nm=(p.get("name") or "").lower(); ne_=(p.get("name_en") or "").lower()
        if nm in nl or ne_ in nl:
            g=f["geometry"]
            if g["type"]=="LineString": out.append(g["coordinates"])
            else:
                for ln in g["coordinates"]: out.append(ln)
    return out

for fid,(name,names) in rivers.items():
    lines=collect_lines(names)
    paths=[]
    total=0
    for ln in lines:
        total+=len(ln)
        eps=0.02
        s=rdp(ln,eps)
        paths.append([[round(p[1],3),round(p[0],3)] for p in s])
    GEO[fid]={"m":"line","c":paths}
    # midpoint of longest path for fallback point
    longest=max(paths,key=len) if paths else []
    mid=longest[len(longest)//2] if longest else None
    print(f"{fid} {name}: {len(lines)} segs, {total} pts -> {sum(len(p) for p in paths)} pts; mid {mid}")

# emit JS
with open("C:/Users/andra/claude/_keva_geo.js","w",encoding="utf-8") as fo:
    parts=[]
    for fid in sorted(GEO):
        parts.append(f"{fid}:"+json.dumps(GEO[fid],separators=(',',':')))
    fo.write(",\n".join(parts))
print("WROTE _keva_geo.js")
