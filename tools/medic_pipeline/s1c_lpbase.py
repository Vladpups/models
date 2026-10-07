# Stage 1c: rebuild the LP base as a clean voxel surface (marching cubes) of the HP volume.
# Morphological closing fills slits (sunglasses lenses, fringe undercut, pouch gaps); on the head an extra
# opening removes thin parts (sunglasses temples). The HP stays untouched as the bake source.
import bpy, sys, json, time, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from scipy import ndimage
from skimage import measure
src, out = sys.argv[1], sys.argv[2]
P = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
bpy.ops.wm.open_mainfile(filepath=src)
hp = bpy.data.objects['HP_Medic']; lp = bpy.data.objects['LP_Medic']
h = P.get('h', 0.0025)
co = np.array([v.co[:] for v in lp.data.vertices])
lo = co.min(0) - 4 * h; hi = co.max(0) + 4 * h
n = np.ceil((hi - lo) / h).astype(int) + 1
xs, ys, zs = (lo[k] + np.arange(n[k]) * h for k in range(3))
tree = BVHTree.FromObject(lp, bpy.context.evaluated_depsgraph_get())
t = time.time()
occ = np.zeros(n, bool)
for i, x in enumerate(xs):
    for j, y in enumerate(ys):
        hits = []; o = Vector((x, y, hi[2] + 0.5)); d = Vector((0, 0, -1))
        while len(hits) < 80:
            loc = tree.ray_cast(o, d)[0]
            if loc is None: break
            hits.append(-loc.z); o = loc + d * 1e-6
        if hits: occ[i, j] = (np.searchsorted(np.array(hits), -zs) % 2) == 1
print('voxelized', n, round(time.time() - t, 1), 's')
def closing(a, r):
    dil = ndimage.distance_transform_edt(~a) * h <= r
    return ndimage.distance_transform_edt(dil) * h > r
def opening(a, r):
    ero = ndimage.distance_transform_edt(a) * h > r
    return ndimage.distance_transform_edt(~ero) * h <= r
if P.get('close_all', 0.003): occ = closing(occ, P.get('close_all', 0.003))
if P.get('open_all', 0.0025): occ = opening(occ, P.get('open_all', 0.0025))   # rings, loops, thin flaps -> texture only
# head box: stronger closing + opening
hb0 = np.floor((np.array(P.get('head_lo', [-0.19, -0.27, 1.66])) - lo) / h).astype(int)
hb1 = np.ceil((np.array(P.get('head_hi', [0.19, 0.18, 2.02])) - lo) / h).astype(int)
sl = tuple(slice(max(a, 0), b) for a, b in zip(hb0, hb1))
sub = occ[sl]
sub2 = sub.copy()
# local fills: sockets behind the sunglasses lenses, the groove under the fringe. Glasses and fringe sit flush.
FILLS = P.get('fills', [
    {'lo': [-0.10, -0.24, 1.785], 'hi': [0.10, -0.06, 1.895], 'r': 0.015},   # sunglasses
    {'lo': [-0.115, -0.26, 1.815], 'hi': [0.115, -0.07, 1.975], 'r': 0.04, 'yz': True},  # forehead under the fringe (profile)
    {'lo': [0.022, -0.26, 1.785], 'hi': [0.115, -0.07, 1.86], 'r': 0.03, 'yz': True},    # under the lenses (cheeks)
    {'lo': [-0.115, -0.26, 1.785], 'hi': [-0.022, -0.07, 1.86], 'r': 0.03, 'yz': True},
])
for f in FILLS:
    e0 = np.floor((np.array(f['lo']) - lo) / h).astype(int) - hb0
    e1 = np.ceil((np.array(f['hi']) - lo) / h).astype(int) - hb0
    esl = tuple(slice(max(a, 0), b) for a, b in zip(e0, e1))
    pad = int(np.ceil(f['r'] / h)) + 2
    psl = tuple(slice(max(a.start - pad, 0), a.stop + pad) for a in esl)
    if f.get('yz'):   # 2D closing of each side-profile slice: fills wide shallow undercuts
        cl = np.stack([closing(a, f['r']) for a in sub2[psl]])
    else:
        cl = closing(sub2[psl], f['r'])
    inner = tuple(slice(a.start - b.start, a.stop - b.start) for a, b in zip(esl, psl))
    sub2[esl] |= cl[inner]
sub2 = opening(closing(sub2, P.get('head_close', 0.008)), P.get('head_open', 0.0025))
zz = zs[sl[2]]
wz = np.clip((zz - P.get('head_z0', 1.69)) / 0.02, 0, 1)   # blend in above the neck
occf = occ.astype(np.float32)
occf[sl] = sub * (1 - wz) + sub2 * wz
occf = ndimage.gaussian_filter(occf, P.get('blur', 0.8))
verts, faces, _, _ = measure.marching_cubes(occf, 0.5, spacing=(h, h, h))
verts += lo
# keep the largest connected piece only (drops voxel crumbs)
me = bpy.data.meshes.new('LP_Medic')
me.from_pydata(verts.tolist(), [], faces[:, ::-1].tolist())
me.update()
import bmesh
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
seen = set(); comps = []
for v in bm.verts:
    if v.index in seen: continue
    st = [v]; seen.add(v.index); mem = []
    while st:
        a = st.pop(); mem.append(a)
        for e in a.link_edges:
            b = e.other_vert(a)
            if b.index not in seen: seen.add(b.index); st.append(b)
    comps.append(mem)
comps.sort(key=len, reverse=True)
for c in comps[1:]: bmesh.ops.delete(bm, geom=c, context='VERTS')
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
bm.to_mesh(me); bm.free()
old = lp.data; lp.data = me; bpy.data.meshes.remove(old)
for p in me.polygons: p.use_smooth = True
# uniform pre-decimation: the voxel surface is far denser than needed for the weighted pass
for o in bpy.context.scene.objects: o.select_set(False)
lp.select_set(True); bpy.context.view_layer.objects.active = lp
m = lp.modifiers.new('pre', 'DECIMATE'); m.ratio = P.get('pre_tris', 200000) / len(me.polygons); m.use_collapse_triangulate = True
bpy.ops.object.modifier_apply(modifier='pre')
me = lp.data
print('LP base tris', len(me.polygons), 'pieces dropped', len(comps) - 1, 'total', round(time.time() - t, 1), 's')
bpy.ops.wm.save_as_mainfile(filepath=out)
