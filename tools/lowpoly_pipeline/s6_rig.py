# Stage 6: Mixamo-compatible rig. Fit -> auto weights -> straighten to Mixamo bind pose -> ground, scale -> final Mixamo-oriented armature.
import bpy, sys, os, json, math, numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_cfg
C = load_cfg()
src, walk, out = sys.argv[1], sys.argv[2], sys.argv[3]
P = {**getattr(C, 'RIG_PARAMS', {}), **(json.loads(sys.argv[4]) if len(sys.argv) > 4 else {})}
bpy.ops.wm.open_mainfile(filepath=src)
sc = bpy.context.scene
lp = bpy.data.objects[f'LP_{C.NAME}']
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
H = {}; LSCALE = {}   # LSCALE: length scale for leaf bones
for n in ORDER:
    s = short(n)
    if s in C.J: H[n] = Vector(C.J[s])
def fit_hand_template(side, sx):
    # no measured fingers: Mixamo hand scaled by HAND_SCALE, drooped by HAND_DROOP, thumb aimed at THUMB_TIP
    hand = f'mixamorig:{side}Hand'
    rot = Matrix.Rotation(sx * C.HAND_DROOP, 3, 'Y')
    for n in ORDER:
        if n.startswith(hand) and n != hand:
            H[n] = H[hand] + rot @ ((REF[n][0] - REF[hand][0]) * C.HAND_SCALE)
            if n[-1] == '4': LSCALE[n] = C.HAND_SCALE
    t = [f'{hand}Thumb{i}' for i in (1, 2, 3, 4)]
    tip = Vector(C.THUMB_TIP[side]); base = H[t[0]]
    cur = H[t[3]] - base; tgt = tip - base; tgt = tgt - tgt.normalized() * 0.012
    Rt = cur.rotation_difference(tgt).to_matrix(); st = tgt.length / cur.length
    for n in t[1:]: H[n] = base + Rt @ ((H[n] - base) * st)
for side, sx in (('Left', 1), ('Right', -1)):
    if not hasattr(C, 'FINGERS'):
        fit_hand_template(side, sx); continue
    for fn, (base, tip) in C.FINGERS.items():
        chain = [f'mixamorig:{side}Hand{fn}{i}' for i in (1, 2, 3, 4)]
        base = Vector((sx * base[0], base[1], base[2])); tip = Vector((sx * tip[0], tip[1], tip[2]))
        tmpl = [REF[n][0] for n in chain]
        cur = tmpl[3] - tmpl[0]; tgt = tip - base; tgt = tgt - tgt.normalized() * C.TIP_INSET
        R = cur.rotation_difference(tgt).to_matrix(); s = tgt.length / cur.length
        for n, t in zip(chain, tmpl): H[n] = base + R @ ((t - tmpl[0]) * s)
        LSCALE[chain[3]] = s
missing = [n for n in ORDER if n not in H]
assert not missing, missing
CHILD = {}
for n in ORDER:
    p = REF[n][3]
    if p and p not in CHILD: CHILD[p] = n
CHILD.update({'mixamorig:Spine2': 'mixamorig:Neck', 'mixamorig:Hips': 'mixamorig:Spine',
              'mixamorig:LeftHand': 'mixamorig:LeftHandMiddle1', 'mixamorig:RightHand': 'mixamorig:RightHandMiddle1'})
def our_dir_len(n):
    if n in CHILD:
        d = H[CHILD[n]] - H[n]; return d.normalized(), d.length
    # leaf: mixamo direction rotated like the parent, scaled length
    p = REF[n][3]
    pd, _ = our_dir_len(p)
    rp = (REF[p][1] @ Vector((0, 1, 0))).rotation_difference(pd).to_matrix()
    d = rp @ (REF[n][1] @ Vector((0, 1, 0)))
    return d.normalized(), REF[n][2] * LSCALE.get(n, 1.0)
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
# --- armature A: bones along our limbs, roll from the Mixamo frame
FA = {}
for n in ORDER:
    d, l = our_dir_len(n)
    Rm = REF[n][1]
    delta = (Rm @ Vector((0, 1, 0))).rotation_difference(d).to_matrix()
    FA[n] = (H[n], delta @ Rm, l)
A = build_arm('RigFit', FA)
# --- auto weights (bone heat)
def select_only(o):
    for x in sc.objects: x.select_set(False)
    o.select_set(True); bpy.context.view_layer.objects.active = o
for o in sc.objects: o.select_set(False)
lp.select_set(True); A.select_set(True); bpy.context.view_layer.objects.active = A
lp.vertex_groups.clear()
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
unweighted = sum(1 for v in lp.data.vertices if sum(x.weight for x in v.groups) < 1e-4)
print('WEIGHTS groups', len(lp.vertex_groups), 'unweighted verts', unweighted)
# --- weight cleanup: fill unweighted, rigid overrides, smooth, max 4 influences, normalized
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
def smooth_W(W, f, it, mask=None):
    n = len(W)
    for _ in range(it):
        acc = np.zeros_like(W); cnt = np.zeros((n, 1), np.float32)
        np.add.at(acc, EDGES[:, 0], W[EDGES[:, 1]]); np.add.at(acc, EDGES[:, 1], W[EDGES[:, 0]])
        np.add.at(cnt, EDGES[:, 0], 1); np.add.at(cnt, EDGES[:, 1], 1)
        Wn = (1 - f) * W + f * acc / np.maximum(cnt, 1)
        W = Wn if mask is None else np.where(mask[:, None], Wn, W)
    return W
GI = {g.name: g.index for g in lp.vertex_groups}
CO = np.array([v.co[:] for v in lp.data.vertices])
W = get_W(lp)
# unweighted verts: take weights from the nearest weighted vertex
empty = W.sum(1) < 1e-4
if empty.any():
    ok = np.nonzero(~empty)[0]
    for i in np.nonzero(empty)[0]:
        j = ok[np.argmin(np.linalg.norm(CO[ok] - CO[i], axis=1))]; W[i] = W[j]
W = smooth_W(W, P.get('smooth_factor', 0.5), P.get('smooth_repeat', 1))
rigid = np.zeros(len(W), bool)
for pred, bone in getattr(C, 'WEIGHT_OVERRIDES', []):
    m = np.array([pred(*c) for c in CO])
    W[m] = 0; W[m, GI[bone]] = 1; rigid |= m
    print('override', bone, int(m.sum()), 'verts')
W = cleanup_W(W)
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
        pb.matrix = Matrix.Translation(head) @ REF[n][1].to_4x4()
    elif n in KEEP_WORLD:
        pb.matrix = Matrix.Translation(head) @ FA[n][1].to_4x4()
bpy.context.view_layer.update()
bpy.ops.object.mode_set(mode='OBJECT')
POSED = {n: (A.matrix_world @ A.pose.bones[n].head).copy() for n in ORDER}
select_only(lp)
mod = [m for m in lp.modifiers if m.type == 'ARMATURE'][0]
bpy.ops.object.modifier_apply(modifier=mod.name)
lp.parent = None
bpy.data.objects.remove(A)
# --- ground both feet (straightening lowers each foot by a different amount), then scale to the target height
me = lp.data
CO = np.array([v.co[:] for v in me.vertices])
W = get_W(lp)
def wsum(names): return sum(W[:, GI[n]] for n in names if n in GI)
low = {}
for side in ('Left', 'Right'):
    foot = wsum([f'mixamorig:{side}Foot', f'mixamorig:{side}ToeBase'])
    low[side] = CO[foot > 0.5, 2].min()
lift = -max(low.values())
print('feet bottoms after straightening', {k: round(v, 4) for k, v in low.items()}, 'global lift', round(lift, 4))
CO[:, 2] += lift
for n in POSED: POSED[n] = POSED[n] + Vector((0, 0, lift))
for side in ('Left', 'Right'):
    d = -(low[side] + lift)   # remaining gap below ground for this foot (>= 0)
    if d < 1e-5: continue
    lower = wsum([f'mixamorig:{side}Leg', f'mixamorig:{side}Foot', f'mixamorig:{side}ToeBase'])
    CO[:, 2] += d * np.clip(lower, 0, 1)
    for n in ORDER:
        s = short(n)
        if s.startswith(side) and any(k in s for k in ('Foot', 'Toe')): POSED[n] = POSED[n] + Vector((0, 0, d))
        if s == f'{side}Leg': POSED[n] = POSED[n] + Vector((0, 0, d * 0.5))
    print('shortened', side, 'lower leg by', round(d, 4))
H0 = CO[:, 2].max() - CO[:, 2].min()
k = C.HEIGHT / H0 if getattr(C, 'HEIGHT', None) else 1.0
CO *= k
for n in POSED: POSED[n] = POSED[n] * k
me.vertices.foreach_set('co', CO.ravel()); me.update()
print('height before scale', round(H0, 4), 'scale', round(k, 5), 'final height', round(CO[:, 2].max() - CO[:, 2].min(), 4))
# --- final armature: Mixamo names, hierarchy and rest orientations; joints at the character's positions
FB = {}
for n in ORDER:
    R = REF[n][1]
    if n in CHILD:
        d = POSED[CHILD[n]] - POSED[n]; l = max(d.dot(R @ Vector((0, 1, 0))), 0.25 * d.length, 0.01)
    else:
        l = REF[n][2] * LSCALE.get(n, 1.0) * k
    FB[n] = (POSED[n], R, l)
B = build_arm('Armature', FB)
B.data.name = 'Armature'
B.data.display_type = 'STICK'
lp.parent = B
m = lp.modifiers.new('Armature', 'ARMATURE'); m.object = B
lp.name = C.NAME; lp.data.name = C.NAME
# --- walk animation from the Mixamo file: cm -> m, hips translation scaled to this character's hips height
act = action.copy(); act.name = 'Walk'
def fcurves(a):
    out = []
    for layer in a.layers:
        for strip in layer.strips:
            for cb in strip.channelbags: out += list(cb.fcurves)
    return out
unit = MW.to_scale()[0]
hips_ratio = POSED['mixamorig:Hips'].z / REF['mixamorig:Hips'][0].z
print('hips height ours', round(POSED['mixamorig:Hips'].z, 4), 'mixamo', round(REF['mixamorig:Hips'][0].z, 4), 'ratio', round(hips_ratio, 4))
f0 = act.frame_range[0]
for fc in fcurves(act):
    for kp in fc.keyframe_points:   # clip starts at frame 0 (time 0 in exported files)
        kp.co.x -= f0; kp.handle_left.x -= f0; kp.handle_right.x -= f0
    if fc.data_path.endswith('.location'):
        f = unit * (hips_ratio if 'mixamorig:Hips' in fc.data_path else 1.0)
        for kp in fc.keyframe_points:
            kp.co.y *= f; kp.handle_left.y *= f; kp.handle_right.y *= f
B.animation_data_create(); B.animation_data.action = act
if act.slots: B.animation_data.action_slot = act.slots[0]
for pb in B.pose.bones: pb.rotation_mode = mx.pose.bones[pb.name].rotation_mode
sc.frame_start, sc.frame_end = 0, int(round(max(kp.co.x for fc in fcurves(act) for kp in fc.keyframe_points)))
act.use_frame_range = True; act.frame_start, act.frame_end = sc.frame_start, sc.frame_end
sc.render.fps = 30
bpy.data.objects.remove(mx)
for a in list(bpy.data.actions):
    if a is not act: bpy.data.actions.remove(a)
act.use_fake_user = True
B['hips_ratio'] = hips_ratio
print('RIG done; deform bones', sum(1 for b in B.data.bones if b.use_deform), 'action', act.name, act.frame_range[:])
bpy.ops.wm.save_as_mainfile(filepath=out)
