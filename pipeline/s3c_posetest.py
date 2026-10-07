# Stress poses beyond the walk: arms up, squat, torso twist, high kick
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
import rutil, matutil
from mathutils import Matrix, Vector
a=sys.argv[sys.argv.index('--')+1:]
BLEND, TEXDIR, OUT = a[0], a[1], a[2]
bpy.ops.wm.open_mainfile(filepath=BLEND)
for o in bpy.data.objects:
    if o.type=='MESH' and o.name!='Zealot': o.hide_render=True
lp=bpy.data.objects['Zealot']; arm=bpy.data.objects['Armature']
matutil.setup_material(lp, TEXDIR)
arm.animation_data.action=None
arm.data.pose_position='POSE'
P='mixamorig:'
vl=bpy.context.view_layer
def reset():
    for pb in arm.pose.bones:
        pb.location=(0,0,0); pb.rotation_quaternion=(1,0,0,0); pb.rotation_euler=(0,0,0); pb.scale=(1,1,1)
    vl.update()
def rot(bone, axis, deg):
    pb=arm.pose.bones[P+bone]; M=pb.matrix.copy(); h=M.translation.copy()
    pb.matrix=Matrix.Translation(h)@Matrix.Rotation(math.radians(deg),4,axis)@Matrix.Translation(-h)@M
    vl.update()
def move(bone, d):
    pb=arm.pose.bones[P+bone]; M=pb.matrix.copy(); M.translation+=Vector(d); pb.matrix=M; vl.update()
POSES={
 'armsup':  lambda:(rot('LeftArm','Y',-70),rot('RightArm','Y',70),rot('LeftForeArm','Z',40),rot('RightForeArm','Z',-40)),
 'armsdown':lambda:(rot('LeftArm','Y',75),rot('RightArm','Y',-75),rot('LeftForeArm','X',-30),rot('RightForeArm','X',-30)),
 'squat':   lambda:(move('Hips',(0,0.06,-0.32)),rot('LeftUpLeg','X',-85),rot('RightUpLeg','X',-85),rot('LeftLeg','X',105),rot('RightLeg','X',105),
                    rot('LeftFoot','X',-20),rot('RightFoot','X',-20),rot('Spine','X',-25),rot('LeftArm','Y',60),rot('RightArm','Y',-60)),
 'twist':   lambda:(rot('Spine1','Z',20),rot('Spine2','Z',20),rot('Head','Z',40),rot('Neck','X',-10),rot('LeftArm','Y',60),rot('RightArm','Z',-60)),
 'kick':    lambda:(rot('RightUpLeg','X',-75),rot('RightLeg','X',20),rot('LeftArm','Y',40),rot('RightArm','Y',-40)),
}
rutil.setup_render(int(os.environ.get('RES','600')), int(os.environ.get('SPP','12')))
for name,fn in POSES.items():
    reset(); fn()
    for az in (35,-110):
        rutil.cam_shot(f'{OUT}_{name}_{az}.png',(0,0,0.85),4,az,8,2.2)
