# Stage 3: body-part segmentation -> seams -> min-stretch unwrap (split while stretched); parts outside cfg.UV_KEEP are charted by xatlas
import bpy, sys, os, json, math, heapq, numpy as np, bmesh
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_cfg
C = load_cfg()
from mathutils import Vector
src, out = sys.argv[1], sys.argv[2]
P = {**getattr(C, 'UV_PARAMS', {}), **(json.loads(sys.argv[3]) if len(sys.argv) > 3 else {})}
bpy.ops.wm.open_mainfile(filepath=src)
lp = bpy.data.objects[f'LP_{C.NAME}']; me = lp.data
bm = bmesh.new(); bm.from_mesh(me)
bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table()
for e in bm.edges: e.seam = False

SEG = C.uv_segments()
def seg_dist(p, a, b):
    a = np.array(a); b = np.array(b); ab = b - a
    t = np.clip(((p - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(p - (a + np.outer(t, ab)), axis=1)
C_ = np.array([f.calc_center_median()[:] for f in bm.faces])
D = np.stack([seg_dist(C_, a, b) for _, a, b in SEG], 1)
names = [n for n, _, _ in SEG]
lab = [names[i] for i in D.argmin(1)]
for i in range(len(lab)):
    lab[i] = C.uv_rule(lab[i], *C_[i])
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
        s[i] = 0.6 * s[i] + 0.4 * np.sign((C_[i] - center) @ axis)
    for _ in range(iters):
        ns = {}
        for i in idx:
            vals = [s[j] for j in NB[i] if j in s] + [s[i]]
            ns[i] = sum(vals) / len(vals)
        s = ns
    for i in idx: lab[i] = posname if s[i] >= 0 else negname
for part, axis, center, pn, nn in C.UV_SPLITS: split_dir(part, np.array(axis, float), np.array(center, float), pn, nn)
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
for part, side_fn, split_fn in C.UV_CYL: cyl_seam(part, side_fn, split_fn)
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
TRI = np.array([p.vertices[:] for p in me.polygons]); VCO = np.array([v.co[:] for v in me.vertices])
LI = np.array([p.loop_indices[:] for p in me.polygons])
_p0, _p1, _p2 = VCO[TRI[:, 0]], VCO[TRI[:, 1]], VCO[TRI[:, 2]]
_e1 = _p1 - _p0; _e2 = _p2 - _p0; _l1 = np.linalg.norm(_e1, axis=1); _ex = _e1 / np.maximum(_l1, 1e-12)[:, None]
_n = np.cross(_e1, _e2); _ey = np.cross(_n / np.maximum(np.linalg.norm(_n, axis=1), 1e-12)[:, None], _ex)
_Q = np.stack([np.stack([_l1, np.zeros_like(_l1)], 1), np.stack([(_e2 * _ex).sum(1), (_e2 * _ey).sum(1)], 1)], 2)
_Qi = np.linalg.pinv(_Q)
def face_metrics():
    uv = np.empty(len(me.loops) * 2, np.float32); me.uv_layers.active.data.foreach_get('uv', uv); uv = uv.reshape(-1, 2).astype(np.float64)
    u0, u1, u2 = uv[LI[:, 0]], uv[LI[:, 1]], uv[LI[:, 2]]
    sg = ((u1 - u0)[:, 0] * (u2 - u0)[:, 1] - (u1 - u0)[:, 1] * (u2 - u0)[:, 0]) / 2
    Jm = np.stack([u1 - u0, u2 - u0], 2) @ _Qi
    sv = np.linalg.svd(Jm, compute_uv=False)
    an = sv[:, 0] / np.maximum(sv[:, 1], 1e-12)
    return sg, an
def island_quality(lab):
    sg_all, an_all = face_metrics()
    groups = defaultdict(list)
    for i, l in enumerate(lab): groups[l].append(i)
    res = {}
    for l, fs in groups.items():
        sg = sg_all[fs]; a3 = FA[fs]; an = an_all[fs]
        if np.abs(sg).sum() < 1e-9 or not np.isfinite(sg).all():   # unsolved island (closed shell, no seam)
            res[l] = (len(fs), len(fs), 1.0, 1.0); continue
        maj = np.sign(sg.sum()); flips = int(((np.sign(sg) != maj) & (np.abs(sg) > 1e-12)).sum())
        ratio = (np.abs(sg) / np.maximum(a3, 1e-12)) / (np.abs(sg).sum() / a3.sum())
        badarea = a3[(ratio < 0.4) | (ratio > 2.5)].sum() / a3.sum()
        anarea = a3[an > P.get('aniso', 1.7)].sum() / a3.sum()
        res[l] = (len(fs), flips, badarea, anarea)
    return res
def split_label(lab, l, tag):
    fs = [i for i, x in enumerate(lab) if x == l]
    if P.get('split', 'plane') == 'plane':
        Pc = C_[fs]; mu = Pc.mean(0); ax = np.linalg.svd(Pc - mu)[2][0]
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
# body parts unwrapped by our seams (clean, semantic islands); the rest (gear-heavy) is charted by xatlas
PART = lab[:]
KEEP_PREFIX = tuple(C.UV_KEEP) if hasattr(C, 'UV_KEEP') and P.get('hybrid', True) else None
def is_keep(i): return KEEP_PREFIX is None or PART[i].startswith(KEEP_PREFIX)
KEEPF = np.array([is_keep(i) for i in range(len(PART))])
# absorb tiny components before starting
lab = relabel_components(lab)
for it in range(P.get('max_iter', 8)):
    apply_seams_and_unwrap(lab)
    q = island_quality(lab)
    keep_l = defaultdict(int)
    for i, l in enumerate(lab): keep_l[l] += 1 if KEEPF[i] else -1
    bad = [l for l, (n, fl, ba, aa) in q.items() if keep_l[l] > 0 and n >= P.get('min_faces', 10) and (fl > max(1, 0.01 * n) or ba > P.get('bad_frac', 0.12) or aa > P.get('aniso_frac', 1.0))]
    tot_fl = sum(v[1] for v in q.values()); tot_ba = sum(v[2] * FA[[i for i, x in enumerate(lab) if x == l]].sum() for l, v in q.items()) / FA.sum()
    tot_aa = sum(v[3] * FA[[i for i, x in enumerate(lab) if x == l]].sum() for l, v in q.items()) / FA.sum()
    print(f'iter {it}: islands {len(q)} bad {len(bad)} flips {tot_fl} badarea {tot_ba:.3f} aniso_area {tot_aa:.3f}')
    if not bad: break
    for l in bad: lab = split_label(lab, l, f'i{it}')
    lab = relabel_components(lab)
    # merge tiny islands (<4 faces) into neighbour
    lab = absorb_small(lab, 4)
    lab = relabel_components(lab)
apply_seams_and_unwrap(lab)
if not KEEPF.all():
    import xatlas
    sub = np.nonzero(~KEEPF)[0]
    vids = np.unique(TRI[sub]); remap = -np.ones(len(VCO), np.int64); remap[vids] = np.arange(len(vids))
    xa = xatlas.Atlas(); xa.add_mesh(VCO[vids].astype(np.float32), remap[TRI[sub]].astype(np.uint32))
    co = xatlas.ChartOptions()
    for k, v in P.get('xatlas', {'normal_deviation_weight': 0.2, 'max_cost': 16, 'straightness_weight': 1, 'roundness_weight': 0.2, 'normal_seam_weight': 1}).items(): setattr(co, k, v)
    xa.generate(co, xatlas.PackOptions())
    vmap, ind, xuv = xa[0]
    par = list(range(len(vmap)))
    def fnd(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    for t in ind:
        for k in (1, 2): par[fnd(int(t[k]))] = fnd(int(t[0]))
    uvl = me.uv_layers.active.data
    for n_, fi in enumerate(sub):
        t = ind[n_]
        # xatlas keeps triangle corner order; match corners by original vertex index
        corner = {int(vids[vmap[t[k]]]): xuv[t[k]] for k in range(3)}
        for li in me.polygons[fi].loop_indices: uvl[li].uv = corner[me.loops[li].vertex_index]
        lab[fi] = f'xa{fnd(int(t[0]))}'
    for e in EF:
        fs = EF[e]
        if len(fs) == 2 and (not KEEPF[fs[0]] or not KEEPF[fs[1]]): me.edges[e].use_seam = lab[fs[0]] != lab[fs[1]]
    print('xatlas charts', len(set(lab[i] for i in sub)), 'for', len(sub), 'faces')
q = island_quality(lab)
sg_all, an_all = face_metrics()
for pref in sorted(set(p_.rstrip('LR').split('_')[0] for p_ in PART)):
    m = np.array([p_.startswith(pref) for p_ in PART])
    print(f'  part {pref}: faces {m.sum()} islands {len(set(np.array(lab)[m]))} aniso_mean {np.average(np.minimum(an_all[m], 10), weights=FA[m]):.3f} >1.5 {FA[m][an_all[m] > 1.5].sum() / FA[m].sum():.3f}')
print('FINAL islands', len(q), 'flips', sum(v[1] for v in q.values()), 'aniso_mean', round(float(np.average(np.minimum(an_all, 10), weights=FA)), 3), 'area aniso>1.5', round(float(FA[an_all > 1.5].sum() / FA.sum()), 3), 'aniso>2', round(float(FA[an_all > 2].sum() / FA.sum()), 3))
bpy.ops.wm.save_as_mainfile(filepath=out)
