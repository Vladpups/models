# Stage 3: body-part segmentation -> seams -> min-stretch unwrap -> pack with texel density priorities
import bpy, sys, json, math, heapq, numpy as np, bmesh
from mathutils import Vector
src, out = sys.argv[1], sys.argv[2]
P = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
bpy.ops.wm.open_mainfile(filepath=src)
lp = bpy.data.objects['LP_Medic']; me = lp.data
bm = bmesh.new(); bm.from_mesh(me)
bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table()
for e in bm.edges: e.seam = False

# rough skeleton (grounded coords, -Y forward)
J = {
 'hip': (0, 0.02, 0.93), 'chest': (0, 0.02, 1.35), 'neck': (0, 0.01, 1.64), 'headb': (0, -0.03, 1.72), 'headt': (0, -0.03, 1.97),
}
SEG = [('torso', J['hip'], J['chest']), ('torso', J['chest'], J['neck']), ('head', J['headb'], J['headt'])]
for s, sx in (('L', 1), ('R', -1)):
    sh = (sx*0.21, 0.04, 1.56); el = (sx*0.465, 0.07, 1.545); wr = (sx*0.735, 0.06, 1.535); ft = (sx*0.95, 0.04, 1.49)
    hp = (sx*0.095, 0.02, 0.92)
    kn = (0.155 if sx > 0 else -0.20, 0.04, 0.53); an = (0.205 if sx > 0 else -0.25, 0.08, 0.10); toe = (0.30 if sx > 0 else -0.315, -0.19, 0.03)
    SEG += [('arm'+s, sh, el), ('arm'+s, el, wr), ('hand'+s, wr, ft),
            ('thigh'+s, hp, kn), ('shin'+s, kn, an), ('foot'+s, an, toe)]
def seg_dist(p, a, b):
    a = np.array(a); b = np.array(b); ab = b - a
    t = np.clip(((p - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(p - (a + np.outer(t, ab)), axis=1)
C = np.array([f.calc_center_median()[:] for f in bm.faces])
D = np.stack([seg_dist(C, a, b) for _, a, b in SEG], 1)
names = [n for n, _, _ in SEG]
lab = [names[i] for i in D.argmin(1)]
# rules: torso vs arm boundary by |x|, head vs torso at the collar, torso vs thigh at the belt
for i, f in enumerate(bm.faces):
    x, y, z = C[i]
    if lab[i].startswith('arm') and abs(x) < 0.25: lab[i] = 'torso'
    if lab[i] == 'torso' and abs(x) > 0.29 and z > 1.45: lab[i] = 'armL' if x > 0 else 'armR'
    if lab[i] == 'head' and z < 1.675: lab[i] = 'torso'
    if lab[i] == 'torso' and z > 1.70 and abs(x) < 0.12: lab[i] = 'head'
    if lab[i].startswith('thigh') and z > 0.98: lab[i] = 'torso'
    if lab[i] == 'torso' and z < 0.86: lab[i] = 'thighL' if x > 0 else 'thighR'
def neighbors(f):
    return [e.link_faces[0] if e.link_faces[1] == f else e.link_faces[1] for e in f.edges if len(e.link_faces) == 2]
NB = [[g.index for g in neighbors(f)] for f in bm.faces]
def smooth(lab, iters=4):
    for _ in range(iters):
        new = lab[:]
        for i in range(len(lab)):
            cnt = {}
            for j in NB[i]: cnt[lab[j]] = cnt.get(lab[j], 0) + 1
            best = max(cnt, key=cnt.get)
            if cnt[best] >= 2 and best != lab[i]: new[i] = best
        lab = new
    return lab
def components(lab):
    comp = [-1]*len(lab); comps = []
    for i in range(len(lab)):
        if comp[i] >= 0: continue
        st = [i]; comp[i] = len(comps); mem = []
        while st:
            k = st.pop(); mem.append(k)
            for j in NB[k]:
                if comp[j] < 0 and lab[j] == lab[i]: comp[j] = comp[i]; st.append(j)
        comps.append(mem)
    return comp, comps
def absorb_small(lab, minsize):
    # keep only largest component per label (and any component >= minsize); merge others into neighbor label
    for _ in range(6):
        comp, comps = components(lab)
        biggest = {}
        for ci, mem in enumerate(comps):
            l = lab[mem[0]]
            if l not in biggest or len(mem) > len(comps[biggest[l]]): biggest[l] = ci
        changed = False
        for ci, mem in enumerate(comps):
            l = lab[mem[0]]
            if ci == biggest[l] or len(mem) >= minsize: continue
            cnt = {}
            for k in mem:
                for j in NB[k]:
                    if lab[j] != l: cnt[lab[j]] = cnt.get(lab[j], 0) + 1
            if cnt:
                nl = max(cnt, key=cnt.get)
                for k in mem: lab[k] = nl
                changed = True
        if not changed: break
    return lab
lab = smooth(lab, 3); lab = absorb_small(lab, 10**9)

# sub-split by smoothed normal direction for closed blobs
FN = np.array([f.normal[:] for f in bm.faces])
def split_dir(part, axis, center, posname, negname, iters=6):
    idx = [i for i in range(len(lab)) if lab[i] == part]
    s = {i: (FN[i] @ axis) for i in idx}
    # combine normal with position relative to center for stability
    for i in idx:
        s[i] = 0.6 * s[i] + 0.4 * np.sign((C[i] - center) @ axis)
    for _ in range(iters):
        ns = {}
        for i in idx:
            vals = [s[j] for j in NB[i] if j in s] + [s[i]]
            ns[i] = sum(vals) / len(vals)
        s = ns
    for i in idx: lab[i] = posname if s[i] >= 0 else negname
Y = np.array([0, 1.0, 0]); Z = np.array([0, 0, 1.0])
split_dir('head', -Y, np.array([0, -0.03, 1.84]), 'head_front', 'head_back')
split_dir('torso', -Y, np.array([0, 0.02, 1.25]), 'torso_front', 'torso_back')
for s, sx in (('L', 1), ('R', -1)):
    split_dir('hand'+s, Z, np.array([sx*0.86, 0.05, 1.51]), 'hand'+s+'_top', 'hand'+s+'_bot')
    split_dir('foot'+s, Z, np.array([0, 0, 0.04]), 'foot'+s+'_top', 'foot'+s+'_bot')
lab = smooth(lab, 2); lab = absorb_small(lab, 10**9)

# seams between charts
for e in bm.edges:
    lf = e.link_faces
    if len(lf) == 2 and lab[lf[0].index] != lab[lf[1].index]: e.seam = True

# longitudinal seam on cylindrical parts (Dijkstra between boundary loops along preferred side)
def cyl_seam(part, side_fn, split_fn):
    fset = set(i for i in range(len(lab)) if lab[i] == part)
    if not fset: return
    verts = set(v.index for i in fset for v in bm.faces[i].verts)
    bverts = set()
    for e in bm.edges:
        lf = [f.index for f in e.link_faces]
        inside = [f in fset for f in lf]
        if any(inside) and not all(inside): bverts.update(v.index for v in e.verts)
    bl = list(bverts)
    A = [v for v in bl if split_fn(np.array(bm.verts[v].co[:])) < 0]; B = [v for v in bl if split_fn(np.array(bm.verts[v].co[:])) > 0]
    if not A or not B: return
    sc = {v: side_fn(np.array(bm.verts[v].co[:])) for v in verts}
    lo_, hi_ = min(sc.values()), max(sc.values())
    nsc = {v: (sc[v] - lo_) / (hi_ - lo_ + 1e-9) for v in verts}
    src_v = min(A, key=lambda v: nsc[v]); dst = set(B)
    dist = {src_v: 0.0}; prev = {}; pq = [(0.0, src_v)]; end = None
    while pq:
        d, v = heapq.heappop(pq)
        if d > dist.get(v, 1e9): continue
        if v in dst and v != src_v: end = v; break
        for e in bm.verts[v].link_edges:
            if not any(f.index in fset for f in e.link_faces): continue
            w = e.other_vert(bm.verts[v]).index
            if w not in verts: continue
            c = e.calc_length() * (1 + 25 * (nsc[w] ** 2))
            if d + c < dist.get(w, 1e9): dist[w] = d + c; prev[w] = (v, e); heapq.heappush(pq, (d + c, w))
    if end is None: return
    v = end; n = 0
    while v in prev:
        pv, e = prev[v]; e.seam = True; v = pv; n += 1
    print('cyl seam', part, n, 'edges')
for s, sx in (('L', 1), ('R', -1)):
    cyl_seam('arm'+s, lambda p: p[2] - 0.3 * p[1], lambda p: -1 if abs(p[0]) < 0.33 else (1 if abs(p[0]) > 0.62 else 0))
    cyl_seam('thigh'+s, lambda p: sx * p[0] + 0.3 * p[1], lambda p: -1 if p[2] > 0.78 else (1 if p[2] < 0.62 else 0))
    cyl_seam('shin'+s, lambda p: sx * p[0] - 0.5 * p[1], lambda p: -1 if p[2] > 0.42 else (1 if p[2] < 0.22 else 0))
from collections import Counter, defaultdict
cylseams = set(e.index for e in bm.edges if e.seam and len(e.link_faces) == 2 and lab[e.link_faces[0].index] == lab[e.link_faces[1].index])
print('CHARTS0', len(set(lab)))
bm.to_mesh(me); bm.free()
while me.uv_layers: me.uv_layers.remove(me.uv_layers[0])
me.uv_layers.new(name='UVMap')
for o in bpy.context.scene.objects: o.select_set(False)
lp.select_set(True); bpy.context.view_layer.objects.active = lp
METHOD = P.get('method', 'ANGLE_BASED')

def apply_seams_and_unwrap(lab):
    for e in me.edges: e.use_seam = e.index in cylseams
    # edge->faces map
    for e in EF:
        fs = EF[e]
        if len(fs) == 2 and lab[fs[0]] != lab[fs[1]]: me.edges[e].use_seam = True
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    kw = {'iterations': P.get('iters', 20)} if METHOD == 'MINIMUM_STRETCH' else {}
    bpy.ops.uv.unwrap(method=METHOD, fill_holes=True, correct_aspect=True, margin=0.002, **kw)
    bpy.ops.object.mode_set(mode='OBJECT')
EF = defaultdict(list)
for p in me.polygons:
    for ek in p.edge_keys: pass
for p in me.polygons:
    for li in p.loop_indices: EF[me.loops[li].edge_index].append(p.index)
FA = np.array([p.area for p in me.polygons])
def island_quality(lab):
    uvl = me.uv_layers.active.data
    groups = defaultdict(list)
    for i, l in enumerate(lab): groups[l].append(i)
    res = {}
    for l, fs in groups.items():
        sg = []
        for i in fs:
            p = me.polygons[i]; pts = [uvl[li].uv.copy() for li in p.loop_indices]
            a = sum(((pts[k]-pts[0]).cross(pts[k+1]-pts[0]))/2 for k in range(1, len(pts)-1)); sg.append(a)
        sg = np.array(sg); a3 = FA[fs]
        maj = np.sign(sg.sum()); flips = int(((np.sign(sg) != maj) & (np.abs(sg) > 1e-12)).sum())
        ratio = (np.abs(sg) / np.maximum(a3, 1e-12)) / (np.abs(sg).sum() / a3.sum())
        badarea = a3[(ratio < 0.4) | (ratio > 2.5)].sum() / a3.sum()
        res[l] = (len(fs), flips, badarea)
    return res
def split_label(lab, l, tag):
    fs = [i for i, x in enumerate(lab) if x == l]
    if P.get('split', 'plane') == 'plane':
        Pc = C[fs]; mu = Pc.mean(0); ax = np.linalg.svd(Pc - mu)[2][0]
        proj = (Pc - mu) @ ax; med = np.median(proj)
        for n, f in enumerate(fs): lab[f] = f'{l}.{tag}{int(proj[n] > med)}'
        return lab
    N = FN[fs]
    # 2-means on normals, init with farthest pair along principal direction
    u, sv, vt = np.linalg.svd(N - N.mean(0)); ax = vt[0]
    proj = (N - N.mean(0)) @ ax
    c = [N[proj.argmin()], N[proj.argmax()]]
    for _ in range(10):
        d0 = N @ c[0]; d1 = N @ c[1]; asg = (d1 > d0).astype(int)
        for k in (0, 1):
            m = N[asg == k]
            if len(m): v = m.sum(0); c[k] = v / (np.linalg.norm(v) + 1e-9)
    loc = {f: asg[n] for n, f in enumerate(fs)}
    for _ in range(3):
        new = {}
        for f in fs:
            cnt = Counter(loc[j] for j in NB[f] if j in loc); cnt[loc[f]] += 0.5
            new[f] = max(cnt, key=cnt.get)
        loc = new
    for f in fs: lab[f] = f'{l}.{tag}{loc[f]}'
    return lab
def relabel_components(lab):
    comp, comps = components(lab)
    for ci, mem in enumerate(comps):
        for k in mem: lab[k] = f'{lab[k]}#{ci}' if len(comps) else lab[k]
    # normalize names
    m = {}; out = []
    for l in lab:
        if l not in m: m[l] = f'c{len(m)}'
        out.append(m[l])
    return out
# absorb tiny components before starting
lab = relabel_components(lab)
for it in range(P.get('max_iter', 8)):
    apply_seams_and_unwrap(lab)
    q = island_quality(lab)
    bad = [l for l, (n, fl, ba) in q.items() if n >= P.get('min_faces', 10) and (fl > max(1, 0.01 * n) or ba > P.get('bad_frac', 0.12))]
    tot_fl = sum(v[1] for v in q.values()); tot_ba = sum(v[2] * FA[[i for i, x in enumerate(lab) if x == l]].sum() for l, v in q.items()) / FA.sum()
    print(f'iter {it}: islands {len(q)} bad {len(bad)} flips {tot_fl} badarea {tot_ba:.3f}')
    if not bad: break
    for l in bad: lab = split_label(lab, l, f'i{it}')
    lab = relabel_components(lab)
    # merge tiny islands (<4 faces) into neighbour
    lab = absorb_small(lab, 4)
    lab = relabel_components(lab)
apply_seams_and_unwrap(lab)
q = island_quality(lab)
print('FINAL islands', len(q), 'flips', sum(v[1] for v in q.values()))
bpy.ops.wm.save_as_mainfile(filepath=out)
