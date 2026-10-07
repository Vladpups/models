import bpy, sys, math
def load(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    a = [o for o in bpy.data.objects if o not in before and o.type == 'ARMATURE'][0]
    return a
bpy.ops.wm.read_factory_settings(use_empty=True)
ours = load(sys.argv[1]); ref = load(sys.argv[2])
print('ours obj rot/scale', tuple(round(math.degrees(x),1) for x in ours.rotation_euler), tuple(round(x,3) for x in ours.scale))
print('ref  obj rot/scale', tuple(round(math.degrees(x),1) for x in ref.rotation_euler), tuple(round(x,3) for x in ref.scale))
worst = 0; worst_n = None; pdiff = []
for b in ref.data.bones:
    rq = (ref.matrix_world @ b.matrix_local).to_quaternion()
    oq = (ours.matrix_world @ ours.data.bones[b.name].matrix_local).to_quaternion()
    ang = math.degrees(rq.rotation_difference(oq).angle)
    ang = min(ang, 360 - ang)
    if ang > worst: worst, worst_n = ang, b.name
    # local (parent-relative) rest rotation, which is what animation curves are relative to
    if b.parent:
        rl = (b.parent.matrix_local.inverted() @ b.matrix_local).to_quaternion()
        ob = ours.data.bones[b.name]
        ol = (ob.parent.matrix_local.inverted() @ ob.matrix_local).to_quaternion()
        d = math.degrees(rl.rotation_difference(ol).angle); pdiff.append(min(d, 360 - d))
print(f'max world rest-orientation difference vs Mixamo: {worst:.3f} deg ({worst_n})')
print(f'max parent-relative rest-rotation difference: {max(pdiff):.3f} deg')
# hips height / leg lengths
for n in ('mixamorig:Hips', 'mixamorig:LeftUpLeg', 'mixamorig:LeftLeg', 'mixamorig:LeftFoot', 'mixamorig:LeftArm', 'mixamorig:LeftHand', 'mixamorig:Head'):
    print(n, 'ours', tuple(round(x, 3) for x in ours.matrix_world @ ours.data.bones[n].head_local), 'mixamo', tuple(round(x, 3) for x in ref.matrix_world @ ref.data.bones[n].head_local))
