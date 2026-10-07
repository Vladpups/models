# Re-import exported files and check Mixamo compatibility
import bpy, sys, os, math
args=sys.argv[sys.argv.index('--')+1:]
OUTDIR, WALK = args[0], args[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=os.path.join(OUTDIR,'Zealot.fbx'))
A=[o for o in bpy.context.selected_objects if o.type=='ARMATURE'][0]
M=[o for o in bpy.context.selected_objects if o.type=='MESH'][0]
dg=bpy.context.evaluated_depsgraph_get()
import numpy as np
co=np.array([(M.matrix_world@v.co)[:] for v in M.data.vertices])
print('FBX mesh: tris',sum(len(p.vertices)-2 for p in M.data.polygons),'height %.3f'%(co[:,2].max()-co[:,2].min()),
      'materials',[m.name for m in M.data.materials],'images',[i.name for i in bpy.data.images])
print('FBX armature bones',len(A.data.bones),'vertex groups',len(M.vertex_groups),'max influences',max(len(v.groups) for v in M.data.vertices))
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.import_scene.fbx(filepath=WALK)
B=[o for o in bpy.context.selected_objects if o.type=='ARMATURE'][0]
worst=0; names_missing=[]
for b in B.data.bones:
    a=A.data.bones.get(b.name)
    if a is None: names_missing.append(b.name); continue
    ra=(A.matrix_world@a.matrix_local).to_3x3().normalized().to_quaternion()
    rb=(B.matrix_world@b.matrix_local).to_3x3().normalized().to_quaternion()
    ang=math.degrees(ra.rotation_difference(rb).angle); ang=min(ang,360-ang)
    worst=max(worst,ang)
print('bones missing vs Mixamo:',names_missing)
print('max rest-orientation difference vs Mixamo skeleton: %.4f deg'%worst)
pa=[b.name for b in A.data.bones]; pb=[b.name for b in B.data.bones]
print('same hierarchy:', all((A.data.bones[n].parent.name if A.data.bones[n].parent else None)==(B.data.bones[n].parent.name if B.data.bones[n].parent else None) for n in pb))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(OUTDIR,'Zealot.glb'))
print('GLB objects',[(o.name,o.type) for o in bpy.data.objects],'actions',[(a.name,a.frame_range[:]) for a in bpy.data.actions])
