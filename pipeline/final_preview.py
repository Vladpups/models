# Clean-room check: exported Zealot.fbx + the ORIGINAL Mixamo Standard_Walk.fbx, as an engine would combine them
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
import rutil, matutil
a=sys.argv[sys.argv.index('--')+1:]
OUT, WALK, FR = a[0], a[1], a[2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=os.path.join(OUT,'Zealot.fbx'))
A=[o for o in bpy.context.selected_objects if o.type=='ARMATURE'][0]
M=[o for o in bpy.context.selected_objects if o.type=='MESH'][0]
matutil.setup_material(M, os.path.join(OUT,'textures'))
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.import_scene.fbx(filepath=WALK)
B=[o for o in bpy.context.selected_objects if o.type=='ARMATURE'][0]
act=B.animation_data.action
# Mixamo file is in cm on a 0.01-scaled object; our rig is meters at scale 1 -> only the root translation needs units
k=B.scale[0]/A.scale[0]*0.933
for layer in act.layers:
    for strip in layer.strips:
        for cb in strip.channelbags:
            for fc in cb.fcurves:
                if fc.data_path.endswith('location'):
                    for kp in fc.keyframe_points:
                        kp.co[1]*=k; kp.handle_left[1]*=k; kp.handle_right[1]*=k
A.animation_data_create(); A.animation_data.action=act
if A.animation_data.action_slot is None and act.slots: A.animation_data.action_slot=act.slots[0]
bpy.data.objects.remove(B)
sc=bpy.context.scene
rutil.setup_render(int(os.environ.get('RES','480')), int(os.environ.get('SPP','10')))
mode=os.environ.get('MODE','gif')
if mode=='gif':
    for f in range(1,37):
        sc.frame_set(f)
        h=A.matrix_world@A.pose.bones['mixamorig:Hips'].head
        rutil.cam_shot(f'{FR}/walk_{f:03d}.png',(h.x,h.y,0.95),4,35,8,2.15)
else:
    for f,az in [(8,35),(26,35),(8,95),(26,-60)]:
        sc.frame_set(f)
        h=A.matrix_world@A.pose.bones['mixamorig:Hips'].head
        rutil.cam_shot(f'{FR}/still_{f}_{az}.png',(h.x,h.y,0.95),4,az,8,2.15)
