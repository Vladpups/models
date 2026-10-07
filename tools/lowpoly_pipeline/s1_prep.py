# Stage 1: import, ground (and optionally scale to cfg.HEIGHT), create HP (bake source) and LP base (merged, no UV)
import bpy, sys, os, bmesh
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_cfg
C = load_cfg()
src, out = sys.argv[1], sys.argv[2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
hp = [o for o in bpy.data.objects if o.type == 'MESH'][0]; hp.name = f'HP_{C.NAME}'
me = hp.data
zmin = min(v.co.z for v in me.vertices); zmax = max(v.co.z for v in me.vertices)
s = C.HEIGHT / (zmax - zmin) if getattr(C, 'HEIGHT', None) else 1.0
for v in me.vertices: v.co.z -= zmin; v.co *= s
me.update()
print('scale', round(s, 5), 'height', round((zmax - zmin) * s, 4))
lp = hp.copy(); lp.data = me.copy(); lp.name = f'LP_{C.NAME}'; lp.data.name = f'LP_{C.NAME}'
bpy.context.scene.collection.objects.link(lp)
bm = bmesh.new(); bm.from_mesh(lp.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bm.to_mesh(lp.data); bm.free()
while lp.data.uv_layers: lp.data.uv_layers.remove(lp.data.uv_layers[0])
lp.data.materials.clear()
hp.hide_render = True
for p in lp.data.polygons: p.use_smooth = True
bpy.ops.wm.save_as_mainfile(filepath=out)
print('LP verts', len(lp.data.vertices), 'tris', len(lp.data.polygons))
