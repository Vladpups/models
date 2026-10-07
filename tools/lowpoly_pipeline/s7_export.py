# Stage 7: deliverables (FBX T-pose, FBX + walk, GLB + walk, .blend with relative textures)
import bpy, sys, os, shutil
src, texsrc, outdir = sys.argv[1], sys.argv[2], os.path.abspath(sys.argv[3])
os.makedirs(os.path.join(outdir, 'textures'), exist_ok=True)
for f in os.listdir(texsrc):
    if f.endswith('.png'): shutil.copy2(os.path.join(texsrc, f), os.path.join(outdir, 'textures', f))
bpy.ops.wm.open_mainfile(filepath=src)
sc = bpy.context.scene
arm = bpy.data.objects['Armature']; mesh = bpy.data.objects['Scavenger']
for im in bpy.data.images:
    if im.filepath:
        im.filepath = os.path.join(outdir, 'textures', os.path.basename(im.filepath)); im.reload()
act = arm.animation_data.action
FBX = dict(object_types={'ARMATURE', 'MESH'}, use_mesh_modifiers=False, mesh_smooth_type='FACE', use_tspace=True,
           add_leaf_bones=False, primary_bone_axis='Y', secondary_bone_axis='X', use_armature_deform_only=False,
           armature_nodetype='NULL', apply_scale_options='FBX_SCALE_ALL', axis_forward='-Z', axis_up='Y',
           path_mode='COPY', embed_textures=True)
# 1) T-pose model for Mixamo / engines
arm.animation_data.action = None; arm.data.pose_position = 'REST'
for pb in arm.pose.bones: pb.matrix_basis.identity()
sc.frame_set(1)
bpy.ops.export_scene.fbx(filepath=os.path.join(outdir, 'Scavenger_LowPoly.fbx'), bake_anim=False, **FBX)
# 2) model + walk
sc.name = 'Walk'
arm.data.pose_position = 'POSE'; arm.animation_data.action = act
if act.slots: arm.animation_data.action_slot = act.slots[0]
bpy.ops.export_scene.fbx(filepath=os.path.join(outdir, 'Scavenger_Walk.fbx'), bake_anim=True, bake_anim_use_all_bones=True,
                         bake_anim_use_nla_strips=False, bake_anim_use_all_actions=False, bake_anim_force_startend_keying=True,
                         bake_anim_simplify_factor=0.0, **FBX)
# 3) glTF binary with walk
sc.name = 'Scene'
bpy.ops.export_scene.gltf(filepath=os.path.join(outdir, 'Scavenger.glb'), export_format='GLB', export_yup=True,
                          export_texcoords=True, export_normals=True, export_tangents=True, export_skins=True,
                          export_animations=True, export_image_format='AUTO')
# 4) blend with relative texture paths
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(outdir, 'Scavenger.blend'), relative_remap=True)
bpy.ops.file.make_paths_relative()
bpy.ops.wm.save_mainfile()
import glob
for f in glob.glob(os.path.join(outdir, '*.blend1')): os.remove(f)
print('EXPORT done')
