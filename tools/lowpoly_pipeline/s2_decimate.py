# Stage 2: weighted collapse decimation of LP (zones from cfg.DEC_REG, boosts from cfg.DEC_BOOST)
import bpy, sys, os, bmesh, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_cfg
C = load_cfg()
src, out = sys.argv[1], sys.argv[2]
target = int(os.environ.get('TRIS', C.TRIS))
bpy.ops.wm.open_mainfile(filepath=src)
lp = bpy.data.objects[f'LP_{C.NAME}']; me = lp.data
REG = C.DEC_REG; boost = C.DEC_BOOST
g = lp.vertex_groups.new(name='dec_w')
for v in me.vertices:
    x, y, z = v.co
    w = 1.0 - C.DEC_BASE
    for k, b in boost.items():
        w -= b * REG[k](x, y, z)
    g.add([v.index], min(max(w, 0.02), 1.0), 'REPLACE')
m = lp.modifiers.new('dec', 'DECIMATE'); m.use_collapse_triangulate = True
m.vertex_group = 'dec_w'; m.vertex_group_factor = getattr(C, 'DEC_FACTOR', 1.0)
# binary search ratio to land just under the target
lo, hi = 0.005, 0.2
dg = bpy.context.evaluated_depsgraph_get()
for i in range(18):
    m.ratio = (lo + hi) / 2
    dg.update(); n = len(lp.evaluated_get(dg).data.polygons)
    if n > target: hi = m.ratio
    else: lo = m.ratio
    if target - 30 <= n <= target: break
m.ratio = lo if n > target else m.ratio
dg.update()
bpy.context.view_layer.objects.active = lp
bpy.ops.object.modifier_apply(modifier='dec')
lp.vertex_groups.clear()
me = lp.data
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges[:])
ng = [f for f in bm.faces if len(f.verts) > 3]
if ng: bmesh.ops.triangulate(bm, faces=ng)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
print('CLEAN nonmanifold edges', sum(1 for e in bm.edges if not e.is_manifold), 'zero-area', sum(1 for f in bm.faces if f.calc_area() < 1e-9))
bm.to_mesh(me); bm.free()
counts = {k: 0 for k in REG}
for p in me.polygons:
    x, y, z = p.center
    for k, f in REG.items():
        if f(x, y, z) > 0.5: counts[k] += 1
print('RESULT tris', len(me.polygons), 'verts', len(me.vertices), json.dumps(counts))
bpy.ops.wm.save_as_mainfile(filepath=out)
