# Put Mixamo animations (FBX, any character, with or without skin) onto a character built by this pipeline.
# Rotations copy 1:1 (rest orientations are identical to Mixamo), hips translation is scaled to the character's hips height.
# Usage: python -I retarget_mixamo.py Character.blend outdir anim1.fbx [anim2.fbx ...] [--skin]
#   --skin: export the mesh too (one self-contained FBX per animation); default is skeleton + animation only.
import bpy, sys, os, math
args = [a for a in sys.argv[1:] if not a.startswith('--')]
skin = '--skin' in sys.argv
src, outdir, anims = args[0], os.path.abspath(args[1]), args[2:]
os.makedirs(outdir, exist_ok=True)
FBX = dict(use_mesh_modifiers=False, mesh_smooth_type='FACE', use_tspace=True, add_leaf_bones=False,
           primary_bone_axis='Y', secondary_bone_axis='X', use_armature_deform_only=False, armature_nodetype='NULL',
           apply_scale_options='FBX_SCALE_ALL', axis_forward='-Z', axis_up='Y', path_mode='COPY', embed_textures=True,
           bake_anim=True, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=False, bake_anim_use_all_actions=False,
           bake_anim_force_startend_keying=True, bake_anim_simplify_factor=0.0)
def fcurves(a):
    out = []
    for layer in a.layers:
        for strip in layer.strips:
            for cb in strip.channelbags: out += list(cb.fcurves)
    return out
for path in anims:
    bpy.ops.wm.open_mainfile(filepath=src)
    sc = bpy.context.scene
    arm = [o for o in sc.objects if o.type == 'ARMATURE'][0]
    for a in list(bpy.data.actions): bpy.data.actions.remove(a)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    mx = [o for o in new if o.type == 'ARMATURE'][0]
    if not (mx.animation_data and mx.animation_data.action):
        print('SKIP (no animation):', path); continue
    src_act = mx.animation_data.action
    MW = mx.matrix_world
    # rest orientation check: animation curves are only valid 1:1 when rest frames match
    worst = 0
    for b in arm.data.bones:
        rb = mx.data.bones.get(b.name)
        if rb is None: continue
        d = math.degrees((MW @ rb.matrix_local).to_quaternion().rotation_difference((arm.matrix_world @ b.matrix_local).to_quaternion()).angle)
        worst = max(worst, min(d, 360 - d))
    if worst > 1.0: print(f'WARNING {os.path.basename(path)}: rest orientations differ from the character by {worst:.1f} deg')
    unit = MW.to_scale()[0]
    ratio = arm.data.bones['mixamorig:Hips'].head_local.z / (MW @ mx.data.bones['mixamorig:Hips'].head_local).z
    act = src_act.copy(); act.name = os.path.splitext(os.path.basename(path))[0]
    f0 = act.frame_range[0]
    for fc in fcurves(act):
        for k in fc.keyframe_points:
            k.co.x -= f0; k.handle_left.x -= f0; k.handle_right.x -= f0
        if fc.data_path.endswith('.location'):
            f = unit * (ratio if 'mixamorig:Hips' in fc.data_path else 1.0)
            for k in fc.keyframe_points:
                k.co.y *= f; k.handle_left.y *= f; k.handle_right.y *= f
    for o in new: bpy.data.objects.remove(o)
    arm.animation_data_create(); arm.animation_data.action = act
    if act.slots: arm.animation_data.action_slot = act.slots[0]
    for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'
    end = int(round(max(k.co.x for fc in fcurves(act) for k in fc.keyframe_points)))
    sc.frame_start, sc.frame_end = 0, end
    for o in sc.objects: o.select_set(o.type == 'ARMATURE' or (skin and o.type == 'MESH'))
    out = os.path.join(outdir, act.name + '.fbx')
    bpy.ops.export_scene.fbx(filepath=out, use_selection=True, object_types={'ARMATURE', 'MESH'} if skin else {'ARMATURE'}, **FBX)
    print(f'OK {act.name}: frames 0-{end}, hips scale {ratio:.3f} -> {out}')
