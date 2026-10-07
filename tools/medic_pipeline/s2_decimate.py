# Stage 2: weighted collapse decimation of LP
import bpy, sys, bmesh, json, math
src, out, target = sys.argv[1], sys.argv[2], int(sys.argv[3])
params = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
bpy.ops.wm.open_mainfile(filepath=src)
lp = bpy.data.objects['LP_Medic']; me = lp.data

def smoothstep(e0, e1, x):
    t = min(max((x - e0) / (e1 - e0), 0.0), 1.0); return t * t * (3 - 2 * t)
def band(x, a, b, f):  # 1 inside [a,b], falloff f outside
    if x < a: return 1 - smoothstep(0, f, a - x)
    if x > b: return 1 - smoothstep(0, f, x - b)
    return 1.0
REG = {
 'head':     lambda x,y,z: band(z,1.72,2.0,0.04)*band(abs(x),0,0.2,0.03),
 'face':     lambda x,y,z: band(z,1.70,1.89,0.02)*band(y,-0.3,-0.09,0.03)*band(abs(x),0,0.075,0.02),
 'ears':     lambda x,y,z: band(z,1.76,1.85,0.01)*band(abs(x),0.085,0.14,0.01)*band(y,-0.05,0.03,0.01),
 'neck':     lambda x,y,z: band(z,1.64,1.72,0.03)*band(abs(x),0,0.12,0.03),
 'hands':    lambda x,y,z: band(abs(x),0.75,1.0,0.03)*band(z,1.38,1.62,0.02),
 'wrists':   lambda x,y,z: band(abs(x),0.69,0.76,0.02)*band(z,1.38,1.62,0.02),
 'elbows':   lambda x,y,z: band(abs(x),0.41,0.52,0.03)*band(z,1.45,1.65,0.02),
 'shoulders':lambda x,y,z: band(abs(x),0.17,0.32,0.03)*band(z,1.45,1.70,0.03),
 'knees':    lambda x,y,z: band(z,0.45,0.62,0.04)*band(abs(x),0.03,0.4,0.02),
 'shins':    lambda x,y,z: band(z,0.15,0.45,0.02)*band(abs(x),0.03,0.4,0.02),
 'feet':     lambda x,y,z: band(z,0.0,0.15,0.02),
 'hips':     lambda x,y,z: band(z,0.85,1.02,0.04)*band(abs(x),0,0.3,0.02),
 'torso':    lambda x,y,z: band(z,1.02,1.45,0.03)*band(abs(x),0,0.33,0.02),
}
boost = params.get('boost', {})
g = lp.vertex_groups.new(name='dec_w')
for v in me.vertices:
    x, y, z = v.co
    w = 1.0 - params.get('base', 0.0)
    for k, b in boost.items():
        w -= b * REG[k](x, y, z)
    g.add([v.index], min(max(w, 0.02), 1.0), 'REPLACE')
m = lp.modifiers.new('dec', 'DECIMATE'); m.use_collapse_triangulate = True
m.vertex_group = 'dec_w'; m.vertex_group_factor = params.get('factor', 1.0)
# binary search ratio to hit target exactly-ish
lo, hi = 0.002, 0.2
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
