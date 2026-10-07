# Stage 3b: texel-density priorities + packing (xatlas packer, square 2048 atlas)
import bpy, sys, json, numpy as np, xatlas, bmesh
from collections import defaultdict
src, out = sys.argv[1], sys.argv[2]
P = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
bpy.ops.wm.open_mainfile(filepath=src)
lp = bpy.data.objects['LP']; me = lp.data
GEAR = [0] * len(me.polygons)
if 'gear' in me.attributes: me.attributes['gear'].data.foreach_get('value', GEAR)
bm = bmesh.new(); bm.from_mesh(me); uv = bm.loops.layers.uv.active
bm.faces.ensure_lookup_table()
# islands by seams
parent = list(range(len(bm.faces)))
def find(a):
    while parent[a] != a: parent[a] = parent[parent[a]]; a = parent[a]
    return a
for e in bm.edges:
    if e.seam or len(e.link_faces) != 2: continue
    parent[find(e.link_faces[0].index)] = find(e.link_faces[1].index)
isl = defaultdict(list)
for f in bm.faces: isl[find(f.index)].append(f)
def prio(c, g):
    x, y, z = c
    if g in (1, 2): return P.get('gear', 1.3)       # NATO panel + med pouch: the most visible logo
    if g == 3: return P.get('bedroll', 1.1)
    if z > 1.52 and abs(x) < 0.17: return P.get('head', 1.4)
    if abs(x) > 0.6 and z > 1.2: return P.get('hands', 1.15)
    if z < 0.11: return P.get('feet', 0.8)
    if 0.95 < z < 1.5 and abs(x) < 0.25 and y < 0: return P.get('chest', 1.15)
    return 1.0
for k, fs in isl.items():
    a3 = sum(f.calc_area() for f in fs)
    auv = 0
    for f in fs:
        p = [l[uv].uv for l in f.loops]
        auv += abs(sum(((p[i]-p[0]).cross(p[i+1]-p[0]))/2 for i in range(1, len(p)-1)))
    cen = sum((f.calc_center_median() * f.calc_area() for f in fs), start=fs[0].calc_center_median()*0) / a3
    s = np.sqrt(a3 / max(auv, 1e-12)) * prio(cen, GEAR[fs[0].index])   # uv units == meters * prio
    piv = sum((l[uv].uv for f in fs for l in f.loops), start=fs[0].loops[0][uv].uv*0) / sum(len(f.loops) for f in fs)
    for f in fs:
        for l in f.loops: l[uv].uv = (l[uv].uv - piv) * s
bm.to_mesh(me)
# weld loops into shared uv verts for xatlas
key = {}; uvs = []; idx = []
uvl = me.uv_layers.active.data
for p in me.polygons:
    tri = []
    for li in p.loop_indices:
        k = (me.loops[li].vertex_index, round(uvl[li].uv.x, 6), round(uvl[li].uv.y, 6))
        if k not in key: key[k] = len(uvs); uvs.append(uvl[li].uv[:])
        tri.append(key[k])
    idx.append(tri)
uvs = np.array(uvs, np.float32); idx = np.array(idx, np.uint32)
uvs -= uvs.min(0)
RES = P.get('res', 2048); PAD = P.get('pad', 8)
def pack(tpu):
    a = xatlas.Atlas(); a.add_uv_mesh(uvs, idx)
    po = xatlas.PackOptions(); po.resolution = RES; po.texels_per_unit = tpu; po.padding = PAD
    po.bruteForce = P.get('brute', True); po.rotate_charts = True; po.bilinear = True
    a.generate(pack_options=po)
    return a
lo, hi = 100.0, 4000.0; best = None
brute = P.get('brute', True); P['brute'] = False
for i in range(P.get('steps', 10)):
    mid = (lo + hi) / 2; a = pack(mid)
    n = a.atlas_count
    print('tpu', round(mid, 1), 'atlases', n, 'util', round(a.utilization, 3) if n == 1 else '-')
    if n == 1: lo = mid; best = a
    else: hi = mid
if brute:  # refine upward with the slow, tighter packer
    P['brute'] = True; t = lo
    while True:
        t *= 1.012; a = pack(t)
        print('brute tpu', round(t, 1), 'atlases', a.atlas_count)
        if a.atlas_count != 1: break
        lo = t; best = a
a = best
vmap, ind, out_uv = a[0]
# out_uv normalized by width/height; atlas is RES x RES
assert a.width == RES and a.height == RES, (a.width, a.height)
uvl = me.uv_layers.active.data
for pi, p in enumerate(me.polygons):
    for j, li in enumerate(p.loop_indices): uvl[li].uv = out_uv[ind[pi][j]]
print('PACKED tpu', round(lo, 1), 'texel/m', round(lo, 1), 'util', round(a.utilization, 3))
lp['texels_per_meter'] = lo
bpy.ops.wm.save_as_mainfile(filepath=out)
