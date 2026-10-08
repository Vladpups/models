# Re-import deliverables in a clean scene and report what an engine would see
import os as _os; N = _os.environ.get("NAME", "Scavenger")
import bpy, sys, os
d = sys.argv[1]
def report(path, kind):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if kind == 'fbx': bpy.ops.import_scene.fbx(filepath=path)
    else: bpy.ops.import_scene.gltf(filepath=path)
    arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']; meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    m = max(meshes, key=lambda o: len(o.data.polygons)); me = m.data
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    maxinf = max(len([g for g in v.groups if g.weight > 0]) for v in me.vertices)
    bones = arms[0].data.bones
    imgs = [(i.name, i.size[:]) for i in bpy.data.images]
    acts = [(a.name, tuple(a.frame_range)) for a in bpy.data.actions]
    import mathutils
    bb = [m.matrix_world @ mathutils.Vector(c) for c in m.bound_box]
    h = max(v.z for v in bb) - min(v.z for v in bb)
    print(f'{os.path.basename(path)}: tris={tris} verts={len(me.vertices)} uv={len(me.uv_layers)} bones={len(bones)} '
          f'root={[b.name for b in bones if not b.parent]} max_influences={maxinf} height={h:.3f}m mats={[s.material.name for s in m.material_slots]} images={imgs} actions={acts}')
    names = sorted(b.name for b in bones)
    return names
n1 = report(os.path.join(d, f'{N}_LowPoly.fbx'), 'fbx')
n2 = report(os.path.join(d, f'{N}_Walk.fbx'), 'fbx')
n3 = report(os.path.join(d, f'{N}.glb'), 'glb')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=sys.argv[2])
ref = sorted(b.name for b in [o for o in bpy.data.objects if o.type == 'ARMATURE'][0].data.bones)
print('bone names identical to Mixamo walk.fbx:', n1 == ref, n2 == ref, n3 == ref)
