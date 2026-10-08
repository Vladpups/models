# Stage 1: import Meshy GLB, scale to target height, ground, create HP (bake source) and LP base (merged, no UV)
import bpy, sys, bmesh
src, out = sys.argv[1], sys.argv[2]
HEIGHT = float(sys.argv[3]) if len(sys.argv) > 3 else 2.0
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
hp = [o for o in bpy.data.objects if o.type == 'MESH'][0]; hp.name = 'HP_Medic'
me = hp.data
zs = [v.co.z for v in me.vertices]; zmin, zmax = min(zs), max(zs)
xs = [v.co.x for v in me.vertices]; xc = (min(xs) + max(xs)) / 2
s = HEIGHT / (zmax - zmin)
for v in me.vertices:
    v.co.x = (v.co.x - xc) * s; v.co.y *= s; v.co.z = (v.co.z - zmin) * s
me.update()
lp = hp.copy(); lp.data = me.copy(); lp.name = 'LP_Medic'; lp.data.name = 'LP_Medic'
bpy.context.scene.collection.objects.link(lp)
bm = bmesh.new(); bm.from_mesh(lp.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bm.to_mesh(lp.data); bm.free()
while lp.data.uv_layers: lp.data.uv_layers.remove(lp.data.uv_layers[0])
lp.data.materials.clear()
hp.hide_render = True
for p in lp.data.polygons: p.use_smooth = True
bpy.ops.wm.save_as_mainfile(filepath=out)
print('scale', s, 'LP verts', len(lp.data.vertices), 'tris', len(lp.data.polygons))
