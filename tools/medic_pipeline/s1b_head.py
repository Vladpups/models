# Stage 1b: morph the Meshy head toward the reference face sheet (3D RBF warp driven by MediaPipe landmarks
# + side-profile points), then rescale the whole model back to the target height.
# args: in.blend out.blend lm_3d.json lm_ref.json '{"center":[0,-0.05,1.84],"size":0.36,"res":1000}'
import bpy, sys, os, json, numpy as np
from scipy import ndimage
from mathutils.kdtree import KDTree
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from head_landmarks import *
src, out, f3d, fref = sys.argv[1:5]
R = json.loads(sys.argv[5]); P = json.loads(sys.argv[6]) if len(sys.argv) > 6 else {}
bpy.ops.wm.open_mainfile(filepath=src)
hp = bpy.data.objects['HP_Medic']; lp = bpy.data.objects['LP_Medic']
L3 = np.array(json.load(open(f3d)))[:, :2]; LR = np.array(json.load(open(fref)))[:, :2]
cx, cy, cz = R['center']; sz = R['size']; res = R['res']
bvh = BVHTree.FromObject(lp, bpy.context.evaluated_depsgraph_get())
# HP has split verts (UV seams); LP is the same surface welded. Edit LP, copy back to HP through this map.
kd = KDTree(len(lp.data.vertices))
for v in lp.data.vertices: kd.insert(v.co, v.index)
kd.balance()
HP2LP = np.array([kd.find(v.co)[1] for v in hp.data.vertices])
def hit_front(x, z):
    loc, nrm, idx, d = bvh.ray_cast(Vector((x, -1.0, z)), Vector((0, 1, 0)))
    return (loc, nrm) if loc else (None, None)
# --- source landmark positions on the mesh
src_pts = {}
for i, (u, v) in enumerate(L3):
    x = cx + (u / res - 0.5) * sz; z = cz - (v / res - 0.5) * sz
    loc, nrm = hit_front(x, z)
    if loc is None or loc.y > -0.02 or nrm.y > -0.25: continue   # missed or grazing (face outline)
    src_pts[i] = np.array(loc[:])
# face outline: rays just inside the silhouette, point slid back out to the outline x
for i in OVAL:
    u, v = L3[i]; x = cx + (u / res - 0.5) * sz; z = cz - (v / res - 0.5) * sz
    loc, nrm = hit_front(x * 0.96, z)
    if loc is not None and loc.y < 0.0: src_pts[i] = np.array((x, loc.y, z))
print('front landmarks on mesh', len(src_pts))
# --- front tile -> model mapping: chin fixed, chin..crown span preserved
z_chin = src_pts[152][2]
s = (CROWN_3D - z_chin) / (LR[152][1] - CROWN_PX_FRONT)
x_mid3 = np.mean([src_pts[i][0] for i in MIDLINE if i in src_pts]); x_midr = np.mean([LR[i][0] for i in MIDLINE])
def front_xz(i): return x_mid3 + (LR[i][0] - x_midr) * s, z_chin + (LR[152][1] - LR[i][1]) * s
# --- side tile mapping (y forward = -Y), y anchored at the ear centre of the mesh
ss = (CROWN_3D - z_chin) / (SIDE['chin_bottom'][1] - CROWN_PX_SIDE)
EAR_Y = P.get('ear_y', -0.008)
def side_yz(k):
    px, py = SIDE[k]; return EAR_Y + (px - SIDE['ear_center'][0]) * ss, z_chin + (SIDE['chin_bottom'][1] - py) * ss
dy_mid = {}
for k, i in SIDE_MP.items():
    if i in src_pts and k != 'chin_bottom': dy_mid[i] = side_yz(k)[0] - src_pts[i][1]
off = np.mean(list(dy_mid.values()))   # the side tile is a slight 3/4 view: trust relative depths only
dy_mid = {i: d - off for i, d in dy_mid.items()}
print('scale front', round(s * 1000, 4), 'mm/px side', round(ss * 1000, 4), 'profile dy (mm)', {k: round(v * 1000, 1) for k, v in dy_mid.items()})
mz = sorted((src_pts[i][2], d) for i, d in dy_mid.items())
def dy_at(z, x):
    zz = [a for a, _ in mz]; dd = [b for _, b in mz]
    return float(np.interp(z, zz, dd)) * max(0.0, 1 - abs(x) / P.get('dy_falloff', 0.09))
SRC, DST = [], []
for i, p in src_pts.items():
    X, Z = front_xz(i)
    Y = p[1] + (dy_mid[i] if i in dy_mid else dy_at(p[2], p[0]))
    SRC.append(p); DST.append((X, Y, Z))
for side in EARS.values():
    for k, m in side['mesh'].items():
        px, py = side['px'][k]
        SRC.append(np.array(m)); DST.append((x_mid3 + (px - x_midr) * s, m[1], z_chin + (LR[152][1] - py) * s))
SRC = np.array(SRC); DST = np.array(DST)
DL = np.linalg.norm(DST - SRC, axis=1)
print('z_chin', round(z_chin, 4), 'chin px', LR[152], 'disp mm mean/max', round(DL.mean() * 1000, 1), round(DL.max() * 1000, 1))
# --- fixed anchors: neck base, back and top of the skull
co = np.array([v.co[:] for v in hp.data.vertices])
rng = np.random.default_rng(0)
def sample(mask, n):
    idx = np.nonzero(mask)[0]; return co[rng.choice(idx, min(n, len(idx)), replace=False)]
neck = sample((co[:, 2] > 1.60) & (co[:, 2] < 1.665) & (np.abs(co[:, 0]) < 0.2), 60)
back = sample((co[:, 2] > 1.70) & (co[:, 1] > P.get('back_y', 0.035)), 60)
top = sample((co[:, 2] > P.get('top_z', 1.93)), 40)
A = np.concatenate([neck, back, top])
SRC = np.concatenate([SRC, A]); DST = np.concatenate([DST, A])
keep = []   # drop duplicates / near-duplicates (split UV verts, dense lip landmarks): >= 5 mm spacing
for i in range(len(SRC)):
    if not keep or np.linalg.norm(SRC[keep] - SRC[i], axis=1).min() > P.get('min_spacing', 0.005): keep.append(i)
nlm = sum(1 for i in keep if i < len(src_pts)); SRC = SRC[keep]; DST = DST[keep]
# --- polyharmonic RBF (phi=r) with linear term; phi=r is conditionally negative definite -> smoothing term is -lam
def rbf_fit(Xs, D, lam):
    n = len(Xs); K = np.linalg.norm(Xs[:, None] - Xs[None], axis=2) + lam * np.eye(n)
    Pm = np.hstack([np.ones((n, 1)), Xs])
    M = np.zeros((n + 4, n + 4)); M[:n, :n] = K; M[:n, n:] = Pm; M[n:, :n] = Pm.T
    rhs = np.zeros((n + 4, 3)); rhs[:n] = D
    sol = np.linalg.solve(M, rhs); return sol[:n], sol[n:]
def rbf_eval(Xs, w, a, Q, chunk=20000):
    out = np.empty((len(Q), 3))
    for k in range(0, len(Q), chunk):
        q = Q[k:k + chunk]; K = np.linalg.norm(q[:, None] - Xs[None], axis=2)
        out[k:k + chunk] = K @ w + np.hstack([np.ones((len(q), 1)), q]) @ a
    return out
w, a = rbf_fit(SRC, DST - SRC, -P.get('lam', 0.001))
def smoothstep(e0, e1, x): t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
def warp(ob):
    c = np.array([v.co[:] for v in ob.data.vertices])
    m = smoothstep(1.645, 1.69, c[:, 2]) * (1 - smoothstep(0.17, 0.22, np.abs(c[:, 0])))
    sel = m > 0
    d = np.zeros_like(c); d[sel] = rbf_eval(SRC, w, a, c[sel]) * m[sel, None]
    c += d
    ob.data.vertices.foreach_set('co', c.ravel()); ob.data.update()
    return np.linalg.norm(d, axis=1)
dl = warp(lp); dh = dl
res_err = np.linalg.norm(rbf_eval(SRC, w, a, SRC[:nlm]) + SRC[:nlm] - DST[:nlm], axis=1)
print('max displacement mm', round(dh.max() * 1000, 1), 'landmark fit err mm mean/max', round(res_err.mean() * 1000, 2), round(res_err.max() * 1000, 2))
# --- hair top: morphological opening of the volume (radius r) pulls thin curls/flaps into the hair mass
def open_hair(ob, h=0.0015, r=0.004, rc=0.0, sigma=0.0, lo=(-0.17, -0.24, 1.84), hi=(0.17, 0.15, 2.01), z0=1.88, z1=1.90, yf0=-1.0, yf1=-0.99):
    lo = np.array(lo); hi = np.array(hi)
    me = ob.data; co = np.array([v.co[:] for v in me.vertices])
    tree = BVHTree.FromObject(ob, bpy.context.evaluated_depsgraph_get())
    n = np.ceil((hi - lo) / h).astype(int) + 1
    xs, ys, zs = (lo[k] + np.arange(n[k]) * h for k in range(3))
    inside = np.zeros(n, bool)
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            hits = []; o = Vector((x, y, hi[2] + 0.3)); d = Vector((0, 0, -1))   # from above: start is outside
            while len(hits) < 60:
                loc = tree.ray_cast(o, d)[0]
                if loc is None: break
                hits.append(-loc.z); o = loc + d * 1e-5
            if hits: inside[i, j] = (np.searchsorted(np.array(hits), -zs) % 2) == 1
    eroded = ndimage.distance_transform_edt(inside) * h > r
    opened = ndimage.distance_transform_edt(~eroded) * h <= r
    if rc:      # closing fills slits and notches cut into the hair mass
        dil = ndimage.distance_transform_edt(~opened) * h <= rc
        opened = ndimage.distance_transform_edt(dil) * h > rc
    if sigma:   # blur the occupancy: rounds tufts
        opened = ndimage.gaussian_filter(opened.astype(np.float32), sigma / h) > 0.5
    d2, ind = ndimage.distance_transform_edt(~opened, return_indices=True)
    if sigma or rc:   # verts inside the processed volume (slit walls) are pushed out to its surface
        din2, ind_in = ndimage.distance_transform_edt(opened, return_indices=True)
        inner = opened
    gi = np.round((co - lo) / h).astype(int); ok = np.all((gi >= 0) & (gi < n), axis=1)
    m = smoothstep(z0, z1, co[:, 2]) * smoothstep(yf0, yf1, co[:, 1]) * ok   # spare the fringe over the forehead
    idx = np.nonzero(m > 0)[0]; g = gi[idx]
    dv = np.zeros(len(co)); tgt = co.copy()
    dv[idx] = d2[g[:, 0], g[:, 1], g[:, 2]] * h
    tgt[idx] = lo + np.stack([ind[k][g[:, 0], g[:, 1], g[:, 2]] for k in range(3)], 1) * h
    if sigma or rc:
        gin = inner[g[:, 0], g[:, 1], g[:, 2]]; ii = idx[gin]; gg = g[gin]
        dv[ii] = din2[gg[:, 0], gg[:, 1], gg[:, 2]] * h
        tgt[ii] = lo + np.stack([ind_in[k][gg[:, 0], gg[:, 1], gg[:, 2]] for k in range(3)], 1) * h
    wv = m * smoothstep(0.002, 0.0035, dv)
    new = co + wv[:, None] * (tgt - co)
    E = np.array([e.vertices[:] for e in me.edges]); deg = np.zeros(len(co))
    np.add.at(deg, E[:, 0], 1); np.add.at(deg, E[:, 1], 1)
    mm = np.clip(wv * 3, 0, 1)
    for _ in range(6):   # relax the collapsed curls
        acc = np.zeros_like(new); np.add.at(acc, E[:, 0], new[E[:, 1]]); np.add.at(acc, E[:, 1], new[E[:, 0]])
        new += 0.5 * mm[:, None] * (acc / deg[:, None] - new)
    me.vertices.foreach_set('co', new.ravel()); me.update()
    print('hair opening: moved verts', int((wv > 0.01).sum()), 'max mm', round(dv.max() * 1000, 1))
# --- sunglasses: Meshy put the lenses ~2.5 cm in front of the eyes; move the lens shells back toward the face
def push_glasses(ob, centers, r0=0.032, r1=0.042, y0=-0.145, y1=-0.152, dy=0.010):
    c = np.array([v.co[:] for v in ob.data.vertices])
    r = np.min([np.hypot(c[:, 0] - cx_, c[:, 2] - cz_) for cx_, cz_ in centers], axis=0)
    w = (1 - smoothstep(r0, r1, r)) * smoothstep(y0, y1, c[:, 1])
    c[:, 1] += dy * w
    ob.data.vertices.foreach_set('co', c.ravel()); ob.data.update()
    print('glasses pushed back: verts', int((w > 0.01).sum()))
if P.get('push_glasses', 0.010):
    LENS = [front_xz(i) for i in (468, 473)]   # MediaPipe iris centres sit behind the lens centres
    push_glasses(lp, LENS, dy=P.get('push_glasses', 0.010))
if P.get('open_hair', True): open_hair(lp, r=P.get('open_r', 0.004), rc=P.get('close_r', 0.0), sigma=P.get('hair_sigma', 0.0), z0=P.get('hair_z0', 1.88), z1=P.get('hair_z1', 1.90), yf0=P.get('hair_yf0', -1.0), yf1=P.get('hair_yf1', -0.99))
c = np.array([v.co[:] for v in lp.data.vertices])
hp.data.vertices.foreach_set('co', c[HP2LP].ravel()); hp.data.update()
# --- rescale to target height
H = P.get('height', 2.0)
zmax = c[:, 2].max()
for ob in (hp, lp):
    c = np.array([v.co[:] for v in ob.data.vertices]).reshape(-1, 3) * (H / zmax)
    ob.data.vertices.foreach_set('co', c.ravel()); ob.data.update()
print('height before rescale', round(zmax, 4))
# photo->model mapping after the rescale, used by the face projection stage
k = H / zmax
MAP = {'s': s * k, 'ss': ss * k, 'x_mid3': float(x_mid3) * k, 'x_midr': float(x_midr), 'z_chin': float(z_chin) * k,
       'chin_py': float(LR[152][1]), 'ear_y': EAR_Y * k, 'side_ear_px': SIDE['ear_center'][0], 'side_chin_py': SIDE['chin_bottom'][1]}
json.dump(MAP, open(os.path.splitext(out)[0] + '_map.json', 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=out)
