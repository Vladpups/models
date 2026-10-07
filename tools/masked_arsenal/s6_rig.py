# Stage 6: Mixamo-compatible rig. Fit -> auto weights -> straighten to Mixamo bind pose -> final Mixamo-oriented armature.
import bpy, sys, os, json, math, numpy as np
from mathutils import Vector, Matrix, Quaternion
src, walk, out = sys.argv[1], sys.argv[2], sys.argv[3]
P = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from joints import J, HAND_SCALE, HAND_DROOP, THUMB_TIP, LEG_SPLAY
bpy.ops.wm.open_mainfile(filepath=src)
sc = bpy.context.scene
lp = bpy.data.objects['LP']
# --- Mixamo reference skeleton
before = set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=walk)
mx = [o for o in bpy.data.objects if o not in before and o.type == 'ARMATURE'][0]
mx.name = 'MixamoRef'
action = mx.animation_data.action
MW = mx.matrix_world
REF = {}   # name -> (head_world, rot3 world (orthonormal), length_world, parent)
for b in mx.data.bones:
    m = MW @ b.matrix_local
    loc, rot, scl = m.decompose()
    REF[b.name] = (loc.copy(), rot.to_matrix(), b.length * MW.to_scale()[0], b.parent.name if b.parent else None)
ORDER = [b.name for b in mx.data.bones]  # parents before children
short = lambda n: n.split(':', 1)[1]
# --- fitted joint positions for all bones
H = {}
for n in ORDER:
    s = short(n)
    if s in J: H[n] = Vector(J[s])
for side in ('Left', 'Right'):
    hand = f'mixamorig:{side}Hand'; sx = 1 if side == 'Left' else -1
    rot = Matrix.Rotation(-sx * HAND_DROOP, 3, 'Y') if True else Matrix()
    # rotate about Y: for +x pointing hand, positive droop lowers fingertips
    rot = Matrix.Rotation(sx * HAND_DROOP, 3, 'Y')
    for n in ORDER:
        if n.startswith(f'mixamorig:{side}Hand') and n != hand:
            off = (REF[n][0] - REF[hand][0]) * HAND_SCALE
            H[n] = H[hand] + rot @ off
    # fit thumb chain onto the mesh thumb: rotate/scale about Thumb1 so Thumb4 head lands near the thumb tip
    t = [f'mixamorig:{side}HandThumb{i}' for i in (1, 2, 3, 4)]
    tip = Vector(THUMB_TIP[side]); base = H[t[0]]
    cur = H[t[3]] - base; tgt = (tip - base); tgt = tgt - tgt.normalized() * 0.012
    Rt = cur.rotation_difference(tgt).to_matrix(); st = tgt.length / cur.length
    for n in t[1:]: H[n] = base + Rt @ ((H[n] - base) * st)
missing = [n for n in ORDER if n not in H]
assert not missing, missing
CHILD = {}
for n in ORDER:
    p = REF[n][3]
    if p and p not in CHILD: CHILD[p] = n
# main child preference (for tails)
PREF = {'mixamorig:Spine2': 'mixamorig:Neck', 'mixamorig:Hips': 'mixamorig:Spine', 'mixamorig:LeftHand': 'mixamorig:LeftHandMiddle1', 'mixamorig:RightHand': 'mixamorig:RightHandMiddle1'}
CHILD.update(PREF)
def our_dir_len(n):
    if n in CHILD:
        d = H[CHILD[n]] - H[n]; return d.normalized(), d.length
    # leaf: mixamo direction rotated like parent delta, scaled length
    p = REF[n][3]
    pd, _ = our_dir_len(p)
    rp = (REF[p][1] @ Vector((0, 1, 0))).rotation_difference(pd).to_matrix()
    d = rp @ (REF[n][1] @ Vector((0, 1, 0)))
    scale = HAND_SCALE if 'Hand' in n else 1.0
    return d.normalized(), REF[n][2] * scale
# --- armature A (fitted, bones along our limbs, roll from mixamo frame)
def build_arm(name, frames):
    ad = bpy.data.armatures.new(name); ob = bpy.data.objects.new(name, ad); sc.collection.objects.link(ob)
    for o in sc.objects: o.select_set(False)
    ob.select_set(True); bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    for n in ORDER:
        head, R, length = frames[n]
        eb = ad.edit_bones.new(n)
        eb.head = head; eb.tail = head + R @ Vector((0, length, 0))
        eb.align_roll(R @ Vector((0, 0, 1)))
    for n in ORDER:
        p = REF[n][3]
        if p: ad.edit_bones[n].parent = ad.edit_bones[p]
    bpy.ops.object.mode_set(mode='OBJECT')
    for n in ORDER:
        s = short(n)
        ad.bones[n].use_deform = not (s.endswith('_End') or s[-1] == '4' and 'Hand' in s)
    return ob
FA = {}
for n in ORDER:
    d, l = our_dir_len(n)
    Rm = REF[n][1]
    delta = (Rm @ Vector((0, 1, 0))).rotation_difference(d).to_matrix()
    FA[n] = (H[n], delta @ Rm, l)
A = build_arm('RigFit', FA)
# --- auto weights
for o in sc.objects: o.select_set(False)
lp.select_set(True); A.select_set(True); bpy.context.view_layer.objects.active = A
lp.vertex_groups.clear()
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
vg_names = [g.name for g in lp.vertex_groups]
empty = [g.name for g in lp.vertex_groups if not any(g.index in [x.group for x in v.groups] for v in lp.data.vertices)]
print('WEIGHTS groups', len(vg_names), 'empty', empty)
unweighted = sum(1 for v in lp.data.vertices if sum(x.weight for x in v.groups) < 1e-4)
print('WEIGHTS unweighted verts', unweighted)

def select_only(o):
    for x in sc.objects: x.select_set(False)
    o.select_set(True); bpy.context.view_layer.objects.active = o
# --- weight cleanup: smooth lightly, max 4 influences, normalized
def get_W(ob):
    W = np.zeros((len(ob.data.vertices), len(ob.vertex_groups)), np.float32)
    for v in ob.data.vertices:
        for g in v.groups: W[v.index, g.group] = g.weight
    return W
def set_W(ob, W):
    for gi, g in enumerate(ob.vertex_groups):
        g.remove(list(range(len(ob.data.vertices))))
        idx = np.nonzero(W[:, gi] > 0)[0]
        for i in idx: g.add([int(i)], float(W[i, gi]), 'REPLACE')
def cleanup_W(W, maxinf=4, minw=0.01):
    W = W.copy()
    if W.shape[1] > maxinf:
        part = np.argpartition(-W, maxinf, axis=1)[:, maxinf:]
        np.put_along_axis(W, part, 0, axis=1)
    W[W < minw] = 0
    s = W.sum(1, keepdims=True); s[s == 0] = 1
    return W / s
EDGES = np.array([e.vertices[:] for e in lp.data.edges])
def smooth_W(W, f, it):
    n = len(W)
    for _ in range(it):
        acc = np.zeros_like(W); cnt = np.zeros((n, 1), np.float32)
        np.add.at(acc, EDGES[:, 0], W[EDGES[:, 1]]); np.add.at(acc, EDGES[:, 1], W[EDGES[:, 0]])
        np.add.at(cnt, EDGES[:, 0], 1); np.add.at(cnt, EDGES[:, 1], 1)
        W = (1 - f) * W + f * acc / np.maximum(cnt, 1)
    return W
W = get_W(lp)
# verts the heat solver could not reach (small detached bits) take the weights of the nearest weighted vertex
CO = np.array([v.co[:] for v in lp.data.vertices])
tot = W.sum(1); bad = np.nonzero(tot < 1e-6)[0]
if len(bad):
    from scipy.spatial import cKDTree
    good = np.nonzero(tot >= 1e-6)[0]
    _, j = cKDTree(CO[good]).query(CO[bad]); W[bad] = W[good[j]]
    print('WEIGHTS filled from nearest', len(bad), 'at', np.round(CO[bad].mean(0), 3))
W = smooth_W(W, P.get('smooth_factor', 0.5), P.get('smooth_repeat', 1))
W = cleanup_W(W)
# back gear is rigid: pack/med pouch ride the upper spine, the bedroll the lower spine
GEAR = [0] * len(lp.data.polygons)
if 'gear' in lp.data.attributes: lp.data.attributes['gear'].data.foreach_get('value', GEAR)
gv = {}
for p in lp.data.polygons:
    if GEAR[p.index]:
        for vi in p.vertices: gv[vi] = GEAR[p.index]
GI = {g.name: g.index for g in lp.vertex_groups}
def vg(n):
    if n not in GI:
        GI[n] = lp.vertex_groups.new(name=n).index
        global W
        W = np.concatenate([W, np.zeros((len(W), 1), np.float32)], 1)
    return GI[n]
s1, s2, s0 = vg('mixamorig:Spine1'), vg('mixamorig:Spine2'), vg('mixamorig:Spine')
for vi, g in gv.items():
    z = lp.data.vertices[vi].co.z
    W[vi] = 0
    if g == 3: W[vi, s0] = 0.6; W[vi, s1] = 0.4
    else:
        t = min(max((z - 1.05) / (1.30 - 1.05), 0), 1)
        W[vi, s1] = 1 - t; W[vi, s2] = t
print('gear verts reweighted', len(gv))
set_W(lp, W)
# --- straighten limbs into the exact Mixamo bind pose
ALIGN = set()
for side in ('Left', 'Right'):
    ALIGN |= {f'mixamorig:{side}{b}' for b in ('Arm', 'ForeArm', 'Hand', 'UpLeg', 'Leg')}
    ALIGN |= {n for n in ORDER if n.startswith(f'mixamorig:{side}Hand') and 'Thumb' not in n}
KEEP_WORLD = {'mixamorig:LeftFoot', 'mixamorig:RightFoot'}
select_only(A); bpy.ops.object.mode_set(mode='POSE')
for n in ORDER:
    pb = A.pose.bones[n]
    bpy.context.view_layer.update()
    head = pb.matrix.translation.copy()
    if n in ALIGN:
        R = REF[n][1]
        if n.endswith('UpLeg') or n.endswith('Leg'):
            R = Matrix.Rotation(-LEG_SPLAY if 'Left' in n else LEG_SPLAY, 3, 'Y') @ R
        pb.matrix = Matrix.Translation(head) @ R.to_4x4()
    elif n in KEEP_WORLD:
        pb.matrix = Matrix.Translation(head) @ FA[n][1].to_4x4()
bpy.context.view_layer.update()
bpy.ops.object.mode_set(mode='OBJECT')
POSED = {n: (A.matrix_world @ A.pose.bones[n].head).copy() for n in ORDER}
select_only(lp)
mod = [m for m in lp.modifiers if m.type == 'ARMATURE'][0]
bpy.ops.object.modifier_apply(modifier=mod.name)
lp.parent = None
# straightened legs reach a few mm lower than the source pose: put the soles back on z=0 and keep the target height
H_TARGET = P.get('height', 1.80)
zs = [v.co.z for v in lp.data.vertices]; z0, z1 = min(zs), max(zs)
k = H_TARGET / (z1 - z0)
for v in lp.data.vertices: v.co = Vector((v.co.x * k, v.co.y * k, (v.co.z - z0) * k))
lp.data.update()
POSED = {n: Vector((p.x * k, p.y * k, (p.z - z0) * k)) for n, p in POSED.items()}
print('NORMALIZE sole', round(z0, 4), 'top', round(z1, 4), 'scale', round(k, 5), 'hips', tuple(round(x, 4) for x in POSED['mixamorig:Hips']))
bpy.data.objects.remove(A)
# --- final armature: Mixamo names, hierarchy and rest orientations; joints at the character's positions
FB = {}
for n in ORDER:
    R = REF[n][1]
    if n in CHILD:
        d = POSED[CHILD[n]] - POSED[n]; l = max(d.dot(R @ Vector((0, 1, 0))), 0.25 * d.length, 0.01)
    else:
        l = REF[n][2] * (HAND_SCALE if 'Hand' in n else 1.0)
    FB[n] = (POSED[n], R, l)
B = build_arm('Armature', FB)
B.data.name = 'Armature'
B.data.display_type = 'STICK'
lp.parent = B
m = lp.modifiers.new('Armature', 'ARMATURE'); m.object = B
lp.name = 'MaskedArsenal'; lp.data.name = 'MaskedArsenal'
# --- walk animation from the Mixamo file, retimed to meters
act = action.copy(); act.name = 'Walk'
def fcurves(a):
    out = []
    for layer in a.layers:
        for strip in layer.strips:
            for cb in strip.channelbags: out += list(cb.fcurves)
    return out
unit = MW.to_scale()[0]
f0 = act.frame_range[0]
for fc in fcurves(act):
    for k in fc.keyframe_points:   # clip starts at frame 0 (time 0 in exported files)
        k.co.x -= f0; k.handle_left.x -= f0; k.handle_right.x -= f0
    if fc.data_path.endswith('.location'):
        for k in fc.keyframe_points:
            k.co.y *= unit; k.handle_left.y *= unit; k.handle_right.y *= unit
B.animation_data_create(); B.animation_data.action = act
if act.slots: B.animation_data.action_slot = act.slots[0]
for pb in B.pose.bones: pb.rotation_mode = mx.pose.bones[pb.name].rotation_mode
act.frame_range = (0, act.frame_range[1] - f0) if act.use_frame_range else act.frame_range
sc.frame_start, sc.frame_end = 0, int(round(max(k.co.x for fc in fcurves(act) for k in fc.keyframe_points)))
sc.render.fps = 30
bpy.data.objects.remove(mx)
for a in list(bpy.data.actions):
    if a is not act: bpy.data.actions.remove(a)
act.use_fake_user = True
print('RIG done; deform bones', sum(1 for b in B.data.bones if b.use_deform), 'action', act.name, act.frame_range[:])
bpy.ops.wm.save_as_mainfile(filepath=out)
