# Stage 1: import, ground the model, create HP (bake source) and LP base (merged, no UV)
import bpy, sys, bmesh
src, out = sys.argv[1], sys.argv[2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
hp = bpy.data.objects['Mesh_0']; hp.name = 'HP_Scavenger'
me = hp.data
zmin = min(v.co.z for v in me.vertices)
for v in me.vertices: v.co.z -= zmin
me.update()
lp = hp.copy(); lp.data = me.copy(); lp.name = 'LP_Scavenger'; lp.data.name = 'LP_Scavenger'
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
