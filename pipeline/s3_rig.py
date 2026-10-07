# Stage 3: fit the Mixamo skeleton (from the walk FBX) to the LP and skin it
import bpy, sys, os, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
args=sys.argv[sys.argv.index('--')+1:]
BLEND, FBX, OUT = args[0], args[1], args[2]
bpy.ops.wm.open_mainfile(filepath=BLEND)
lp=bpy.data.objects['Zealot']; hp=bpy.data.objects['Zealot_HP']
P='mixamorig:'

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.import_scene.fbx(filepath=FBX)
arm=[o for o in bpy.context.selected_objects if o.type=='ARMATURE'][0]
arm.name='Armature'; arm.data.name='Armature'
act=arm.animation_data.action
act.name='Walk'

def action_fcurves(a):
    out=[]
    for layer in a.layers:
        for strip in layer.strips:
            for cb in strip.channelbags: out+=list(cb.fcurves)
    return out

# bake the FBX object transform (rot X 90, scale 0.01) into the bones -> meters, Z up
bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); bpy.context.view_layer.objects.active=arm
UNIT=arm.scale[0]
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# ---- target joint positions (meters, character faces -Y, Left = +X) ----
hv=np.array([v.co[:] for v in hp.data.vertices])
def toe_x(side):
    m=(hv[:,2]<0.08)&(hv[:,1]<-0.12)&(hv[:,0]*side>0)
    return hv[m,0].mean()
def toe_y(side):
    m=(hv[:,2]<0.10)&(hv[:,0]*side>0)
    return hv[m,1].min()
J={}
J['Hips']=(0,0.0,0.979)
J['Spine']=(0,0.0,1.083)
J['Spine1']=(0,0.010,1.184)
J['Spine2']=(0,0.020,1.278)
J['Neck']=(0,0.030,1.430)
J['Head']=(0,0.005,1.495)
J['HeadTop_End']=(0,-0.030,1.700)
for side,S in ((1,'Left'),(-1,'Right')):
    J[S+'Shoulder']=(0.045*side,0.040,1.392)
    J[S+'Arm']=(0.165*side,0.070,1.392)
    J[S+'ForeArm']=(0.385*side,0.085,1.368)
    J[S+'Hand']=(0.605*side,0.075,1.345)
    J[S+'UpLeg']=(0.100*side,0.010,0.910)
    J[S+'Leg']=(0.168*side,-0.005,0.507)
    J[S+'Foot']=(0.236*side,0.020,0.105)
    tx=toe_x(side); ty=toe_y(side)
    J[S+'ToeBase']=(0.5*(0.236*side)+0.5*tx,-0.115,0.035)
    J[S+'Toe_End']=(tx,ty+0.015,0.035)
J={P+k:Vector(v) for k,v in J.items()}

bpy.ops.object.mode_set(mode='EDIT')
eb=arm.data.edit_bones
orig={b.name:(b.head.copy(), b.matrix.copy(), b.length) for b in eb}
for b in eb: b.use_connect=False
# fingers: keep Mixamo hand proportions, rotate down with the glove's droop
DROOP=math.radians(float(os.environ.get('HAND_DROOP','9')))
FS=float(os.environ.get('FINGER_SCALE','0.97'))
for b in eb:
    n=b.name[len(P):]
    if any(f in n for f in ('Thumb','Index','Middle','Ring','Pinky')):
        S='Left' if n.startswith('Left') else 'Right'; side=1 if S=='Left' else -1
        R=Matrix.Rotation(DROOP*side, 3, 'Y')
        off=orig[b.name][0]-orig[P+S+'Hand'][0]
        J[b.name]=J[P+S+'Hand']+R@(off*FS)
# thumb: chain from its Mixamo base toward the glove's thumb tip (lowest point of the glove)
for side,S in ((1,'Left'),(-1,'Right')):
    m=(hv[:,0]*side>0.60)&(hv[:,0]*side<0.78)&(hv[:,2]>1.15)
    g=hv[m]; tip=Vector(g[np.argmin(g[:,2])])
    base=J[P+S+'HandThumb1']
    names=[P+S+f'HandThumb{i}' for i in (1,2,3,4)]
    seg=[(orig[names[i+1]][0]-orig[names[i]][0]).length for i in range(3)]
    tot=sum(seg); d=(tip-base)
    # end joint sits ~1.2 cm inside the tip
    d=d*((d.length-0.012)/d.length)
    acc=0
    for i in range(1,4):
        acc+=seg[i-1]; J[names[i]]=base+d*(acc/tot)
    print(S,'thumb tip',tuple(round(x,3) for x in tip),'base',tuple(round(x,3) for x in base))
missing=[b.name for b in eb if b.name not in J]
assert not missing, missing
# move heads, keep every bone's rest orientation and roll identical to Mixamo
for b in eb:
    M=orig[b.name][1].to_3x3().to_4x4(); M.translation=J[b.name]
    b.matrix=M
for b in eb:
    kids=[c for c in b.children]
    if len(kids)==1 or (kids and b.name.endswith('Hand')):
        c=[k for k in kids if 'Middle1' in k.name] or kids
        L=(J[c[0].name]-J[b.name]).length
    elif kids:
        L=orig[b.name][2]*UNIT
    else:
        L=orig[b.name][2]*UNIT*0.95
    b.length=max(L,0.01)
bpy.ops.object.mode_set(mode='OBJECT')

# joints must sit inside the mesh for bone-heat weighting
dg=bpy.context.evaluated_depsgraph_get()
tree=BVHTree.FromObject(lp,dg)
outside=[]
for b in arm.data.bones:
    loc,nrm,fi,d=tree.find_nearest(b.head_local)
    if (b.head_local-loc).dot(nrm)>0: outside.append((b.name,round(d,3)))
print('joints outside LP:',outside)

# end bones never deform (Mixamo convention)
for b in arm.data.bones:
    if b.name.endswith(('4','_End')): b.use_deform=False

# scale the walk's location keys: FBX cm -> m and Y Bot hip height -> ours
k_hip=(J[P+'LeftUpLeg'].z-0.0)/(orig[P+'LeftUpLeg'][0].z)
for fc in action_fcurves(act):
    if fc.data_path.endswith('location'):
        k=UNIT*(k_hip if 'Hips' in fc.data_path else 1.0)
        for kp in fc.keyframe_points:
            kp.co[1]*=k; kp.handle_left[1]*=k; kp.handle_right[1]*=k
print('hip scale',k_hip)

# ---- close the last see-through spots: double-side thin folds seen from behind, pay for them with hidden tris ----
import bmesh
sys.path.insert(0, os.path.dirname(__file__))
from vis import face_side_visibility
bm=bmesh.new(); bm.from_mesh(lp.data); bm.faces.ensure_lookup_table()
sv=face_side_visibility(bm, ndirs=400)
dup=[bm.faces[i] for i,(fr,bk) in enumerate(sv) if bk>=3]
hidden=set(bm.faces[i] for i,(fr,bk) in enumerate(sv) if fr==0 and bk==0)
budget=int(os.environ.get('TRI_BUDGET','5000'))
need=len(bm.faces)+len(dup)-budget
removed=0
while need>0:
    cand=[e for e in bm.edges if e.is_valid and len(e.link_faces)==2 and all(f in hidden for f in e.link_faces)
          and all(f in hidden for v in e.verts for f in v.link_faces)]
    if not cand: break
    e=min(cand,key=lambda e:e.calc_length())
    n0=len(bm.faces); bmesh.ops.collapse(bm, edges=[e], uvs=True)
    d=n0-len(bm.faces); need-=d; removed+=d
    hidden=set(f for f in hidden if f.is_valid)
bm.to_mesh(lp.data); bm.free()
print('hidden tris removed',removed)

# ---- skinning ----
arm.animation_data.action=None
for pb in arm.pose.bones:
    pb.location=(0,0,0); pb.rotation_quaternion=(1,0,0,0); pb.scale=(1,1,1)
bpy.ops.object.select_all(action='DESELECT')
lp.select_set(True); arm.select_set(True); bpy.context.view_layer.objects.active=arm
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
me=lp.data
nz=sum(1 for v in me.vertices if not any(g.weight>1e-4 for g in v.groups))
print('verts without weights after auto:',nz)

# ---- weight post-process ----
vgs={g.name:g for g in lp.vertex_groups}
gname={g.index:g.name for g in lp.vertex_groups}
def get_w(v): return {gname[g.group]:g.weight for g in v.groups if g.weight>0}
def set_w(v, w):
    for g in list(v.groups): vgs[gname[g.group]].remove([v.index])
    tot=sum(w.values())
    for n,x in w.items():
        if x>1e-4:
            if n not in vgs: vgs[n]=lp.vertex_groups.new(name=n); gname[vgs[n].index]=n
            vgs[n].add([v.index], x/tot, 'REPLACE')
def seg_dist(p,a,b):
    ab=b-a; t=max(0,min(1,(p-a).dot(ab)/ab.length_squared)); return (p-(a+ab*t)).length
def smoothstep(a,b,x):
    t=max(0,min(1,(x-a)/(b-a))); return t*t*(3-2*t)
HIP_Z=J[P+'Hips'].z; HEM_Z=float(os.environ.get('HEM_Z','0.42'))
SKIRT_MAX=float(os.environ.get('SKIRT_LEG','0.8'))
ARMB=('Shoulder','Arm','ForeArm','Hand','Thumb','Index','Middle','Ring','Pinky')
nskirt=ngear=nhood=0
for v in me.vertices:
    p=v.co; w=get_w(v)
    shinL=seg_dist(p,J[P+'LeftLeg'],J[P+'LeftFoot']); shinR=seg_dist(p,J[P+'RightLeg'],J[P+'RightFoot'])
    is_leg = p.z<0.60 and min(shinL,shinR)<float(os.environ.get('LEG_R','0.095'))
    # hood cone and head: rigid with the head
    if p.z>J[P+'Head'].z+0.12 and abs(p.x)<0.12:
        set_w(v,{P+'Head':1.0}); nhood+=1; continue
    # torso, belt gear and skirt never follow the arms
    if abs(p.x)<0.36 and p.z<1.25:
        w={k:x for k,x in w.items() if not any(a in k for a in ARMB)} or {P+'Hips':1.0}
    # robe skirt: Hips + thighs only, leg share grows from hips to hem, split left/right by x
    if not is_leg and HEM_Z-0.1<p.z<HIP_Z-0.02 and abs(p.x)<0.40:
        t=smoothstep(HIP_Z-0.05, HEM_Z, p.z)
        legs=SKIRT_MAX*t
        sL=smoothstep(-0.10,0.10,p.x)
        sw={P+'Hips':1-legs, P+'LeftUpLeg':legs*sL, P+'RightUpLeg':legs*(1-sL)}
        # keep a bit of the auto weights near the waist for the gear/belt
        keep=1-t
        w={k:sw.get(k,0)*(1-keep*0.5)+w.get(k,0)*keep*0.5 for k in set(sw)|set(w)}
        nskirt+=1
    set_w(v,w)
print('hood verts',nhood,'skirt verts',nskirt)
# smooth then limit to 4 influences and normalize
bpy.ops.object.select_all(action='DESELECT'); lp.select_set(True); bpy.context.view_layer.objects.active=lp
bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
bpy.ops.object.vertex_group_smooth(group_select_mode='ALL', factor=0.5, repeat=int(os.environ.get('WSMOOTH','2')), expand=0.0)
bpy.ops.object.vertex_group_clean(group_select_mode='ALL', limit=0.01, keep_single=True)
bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL', lock_active=False)
bpy.ops.object.mode_set(mode='OBJECT')
mx=max(len([g for g in v.groups if g.weight>0]) for v in me.vertices)
nz=sum(1 for v in me.vertices if not any(g.weight>1e-4 for g in v.groups))
print('max influences',mx,'unweighted',nz)
# drop empty groups
for g in list(lp.vertex_groups):
    if not any(any(x.group==g.index and x.weight>0 for x in v.groups) for v in me.vertices):
        lp.vertex_groups.remove(g)
print('groups',len(lp.vertex_groups))
# double-side the thin folds seen from behind (copies keep UVs and weights)
bm=bmesh.new(); bm.from_mesh(lp.data); bm.faces.ensure_lookup_table()
sv=face_side_visibility(bm, ndirs=400)
dup=[bm.faces[i] for i,(fr,bk) in enumerate(sv) if bk>=3]
ret=bmesh.ops.duplicate(bm, geom=dup)
newf=[g for g in ret['geom'] if isinstance(g,bmesh.types.BMFace)]
bmesh.ops.reverse_faces(bm, faces=newf)
bm.to_mesh(lp.data); bm.free()
for p in lp.data.polygons: p.use_smooth=True
print('double-sided faces',len(newf),'final tris',sum(len(p.vertices)-2 for p in lp.data.polygons),'verts',len(lp.data.vertices))

arm.animation_data.action=act
bpy.ops.wm.save_as_mainfile(filepath=OUT)
