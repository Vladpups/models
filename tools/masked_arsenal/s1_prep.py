# Stage 1: import Meshy GLB, scale to target height, ground, center; HP (bake source) + LP base (merged, no UV)
import bpy, sys, bmesh, json
from mathutils import Vector
src, out = sys.argv[1], sys.argv[2]
P = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
H = P.get('height', 1.80)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
hp = [o for o in bpy.data.objects if o.type == 'MESH'][0]; hp.name = 'HP'
me = hp.data
co = [v.co.copy() for v in me.vertices]
zmin = min(c.z for c in co); zmax = max(c.z for c in co)
s = H / (zmax - zmin)
# center x on the legs/pelvis, y on the feet
low = [c for c in co if c.z - zmin < 0.5 * (zmax - zmin)]
cx = (min(c.x for c in low) + max(c.x for c in low)) / 2
feet = [c for c in co if c.z - zmin < 0.05 * (zmax - zmin)]
cy = (min(c.y for c in feet) + max(c.y for c in feet)) / 2
for v in me.vertices:
    v.co = Vector(((v.co.x - cx) * s, (v.co.y - cy) * s, (v.co.z - zmin) * s))
me.update()
lp = hp.copy(); lp.data = me.copy(); lp.name = 'LP'; lp.data.name = 'LP'
bpy.context.scene.collection.objects.link(lp)
bm = bmesh.new(); bm.from_mesh(lp.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bm.to_mesh(lp.data); bm.free()
while lp.data.uv_layers: lp.data.uv_layers.remove(lp.data.uv_layers[0])
lp.data.materials.clear()
hp.hide_render = True
for p in lp.data.polygons: p.use_smooth = True
bpy.ops.wm.save_as_mainfile(filepath=out)
print('scale', round(s, 5), 'center', round(cx, 4), round(cy, 4), 'LP verts', len(lp.data.vertices), 'tris', len(lp.data.polygons))
