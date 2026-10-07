# Stage 4: export game-ready files
import bpy, sys, os, shutil
sys.path.insert(0, os.path.dirname(__file__))
import matutil
args=sys.argv[sys.argv.index('--')+1:]
BLEND, TEXDIR, OUTDIR = args[0], args[1], args[2]
os.makedirs(OUTDIR, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=BLEND)
sc=bpy.context.scene
# drop everything but the game asset
for o in list(bpy.data.objects):
    if o.name not in ('Zealot','Armature'): bpy.data.objects.remove(o, do_unlink=True)
for m in list(bpy.data.meshes):
    if m.users==0: bpy.data.meshes.remove(m)
lp=bpy.data.objects['Zealot']; arm=bpy.data.objects['Armature']
# clean material: remove bake-target images, wire final textures
for img in list(bpy.data.images):
    if img.name.startswith('bake_') or img.users==0: bpy.data.images.remove(img)
tex_out=os.path.join(OUTDIR,'textures'); os.makedirs(tex_out, exist_ok=True)
for f in os.listdir(TEXDIR):
    if f.endswith('.png'): shutil.copy(os.path.join(TEXDIR,f), tex_out)
matutil.setup_material(lp, tex_out)
for m in list(bpy.data.materials):
    if m.users==0: bpy.data.materials.remove(m)
for img in list(bpy.data.images):
    if img.users==0: bpy.data.images.remove(img)
lp.data.name='Zealot'
act=bpy.data.actions['Walk']
fr=act.frame_range
sc.frame_start=int(fr[0]); sc.frame_end=int(fr[1]); sc.render.fps=30
tris=sum(len(p.vertices)-2 for p in lp.data.polygons)
print('final tris',tris,'verts',len(lp.data.vertices),'bones',len(arm.data.bones))

def select_asset():
    bpy.ops.object.select_all(action='DESELECT')
    lp.select_set(True); arm.select_set(True); bpy.context.view_layer.objects.active=arm

FBX_COMMON=dict(use_selection=True, object_types={'ARMATURE','MESH'},
    apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL',
    axis_forward='-Z', axis_up='Y', use_mesh_modifiers=True,
    mesh_smooth_type='FACE', use_tspace=True, use_triangles=True,
    add_leaf_bones=False, primary_bone_axis='Y', secondary_bone_axis='X',
    armature_nodetype='NULL', use_armature_deform_only=False)

# 1) model in T-pose, no animation, textures embedded
arm.animation_data.action=None
for pb in arm.pose.bones:
    pb.location=(0,0,0); pb.rotation_quaternion=(1,0,0,0); pb.scale=(1,1,1)
sc.frame_set(sc.frame_start)
select_asset()
bpy.ops.export_scene.fbx(filepath=os.path.join(OUTDIR,'Zealot.fbx'), bake_anim=False,
    path_mode='COPY', embed_textures=True, **FBX_COMMON)
# 2) same model with the walk cycle (textures referenced from ./textures)
arm.animation_data.action=act
if hasattr(arm.animation_data,'action_slot') and arm.animation_data.action_slot is None and act.slots:
    arm.animation_data.action_slot=act.slots[0]
select_asset()
bpy.ops.export_scene.fbx(filepath=os.path.join(OUTDIR,'Zealot_Walk.fbx'), bake_anim=True,
    bake_anim_use_all_bones=True, bake_anim_use_nla_strips=False, bake_anim_use_all_actions=False,
    bake_anim_force_startend_keying=True, bake_anim_simplify_factor=0.0,
    path_mode='RELATIVE', embed_textures=False, **FBX_COMMON)
# 3) glTF binary with PBR textures and the walk
select_asset()
bpy.ops.export_scene.gltf(filepath=os.path.join(OUTDIR,'Zealot.glb'), export_format='GLB',
    use_selection=True, export_skins=True, export_animations=True, export_animation_mode='ACTIONS',
    export_yup=True, export_normals=True, export_tangents=False, export_apply=False,
    export_image_format='AUTO')
# 4) Blender source (textures packed)
arm.animation_data.action=act
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUTDIR,'Zealot.blend'), compress=True)
for f in sorted(os.listdir(OUTDIR)):
    p=os.path.join(OUTDIR,f)
    if os.path.isfile(p): print(f, round(os.path.getsize(p)/1e6,2),'MB')
