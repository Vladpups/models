# Stage 5b: paint the reference sheet onto the LP base colour (LP still in the source pose, which matches the sheet).
# Body: ortho front/back views + mask close-ups, aligned by silhouette fit and dense optical flow.
# Back gear (pack, med pouch, bedroll): explicit rect mapping from the sheet, side walls mirrored from the edges.
import bpy, sys, os, json, numpy as np, cv2
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from projlib import raster, sample, smoothstep, flow, dilate_fill
from gear import PANEL, MEDKIT, BEDROLL, REF_RECTS
src, texdir, refp, out, dbg = sys.argv[1:6]
P = json.loads(sys.argv[6]) if len(sys.argv) > 6 else {}
os.makedirs(dbg, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=src)
ob = bpy.data.objects['LP']; me = ob.data
M = np.array(ob.matrix_world)
n = len(me.vertices)
V = np.empty(n * 3, np.float32); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
NV = np.empty(n * 3, np.float32); me.vertices.foreach_get('normal', NV); NV = NV.reshape(-1, 3) @ M[:3, :3].T
NV /= np.linalg.norm(NV, axis=1, keepdims=True) + 1e-9
assert all(len(p.vertices) == 3 for p in me.polygons)
F = len(me.polygons)
TRI = np.empty(F * 3, np.int32); me.polygons.foreach_get('vertices', TRI); TRI = TRI.reshape(-1, 3)
UV = np.empty(len(me.loops) * 2, np.float32); me.uv_layers.active.data.foreach_get('uv', UV); UV = UV.reshape(-1, 3, 2)
GEAR = np.zeros(F, np.int32)
if 'gear' in me.attributes: me.attributes['gear'].data.foreach_get('value', GEAR)
FN = np.cross(V[TRI[:, 1]] - V[TRI[:, 0]], V[TRI[:, 2]] - V[TRI[:, 0]]); FN /= np.linalg.norm(FN, axis=1, keepdims=True) + 1e-12

# ---------- texel -> surface point
bc_path = os.path.join(texdir, 'T_MaskedArsenal_BaseColor.png')
meshy_path = os.path.join(texdir, 'T_MaskedArsenal_BaseColor_meshy.png')
if not os.path.exists(meshy_path): Image.open(bc_path).save(meshy_path)   # keep the pure bake, re-runs start from it
base = np.asarray(Image.open(meshy_path).convert('RGB'), np.float32) / 255
RES = base.shape[0]
uvpx = np.stack([UV[..., 0] * RES - 0.5, (1 - UV[..., 1]) * RES - 0.5], -1).reshape(-1, 2)
_, TF, TB = raster(uvpx, np.zeros(len(uvpx), np.float32), np.arange(F * 3).reshape(F, 3), RES, RES, depth_test=False)
cov = TF >= 0
tf = TF[cov]; tb = TB[cov]
TP = (V[TRI[tf]] * tb[..., None]).sum(1)                      # (K,3) texel positions
TN = (NV[TRI[tf]] * tb[..., None]).sum(1); TN /= np.linalg.norm(TN, axis=1, keepdims=True) + 1e-9
TG = GEAR[tf]
K = len(tf)
print('texels covered', K)

ref = np.asarray(Image.open(refp).convert('RGB'), np.float32) / 255
refg = cv2.cvtColor((ref * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
ref_sil = (ref.min(2) < 0.92).astype(np.uint8)
ref_sil = cv2.morphologyEx(ref_sil, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))

def basis(theta):
    c, s = np.cos(theta), np.sin(theta)
    d = np.array([-s, c, 0.0]); r = np.array([c, s, 0.0]); u = np.array([0, 0, 1.0])
    return d, r, u

class View:
    def __init__(s, name, rect, theta, scale, cx, cy, pivot, weight=1.0):
        s.name, s.rect, s.theta, s.scale, s.cx, s.cy, s.pivot, s.weight = name, rect, theta, scale, cx, cy, np.array(pivot), weight
    def proj(s, X):  # world -> (px, py, depth) in full sheet pixels
        d, r, u = basis(s.theta); Q = X - s.pivot
        return s.cx + s.scale * (Q @ r), s.cy - s.scale * (Q @ u), Q @ d
    def dir(s): return basis(s.theta)[0]
    def render(s):
        x0, y0, x1, y1 = s.rect
        px, py, dz = s.proj(V)
        zb, fid, bar = raster(np.stack([px - x0, py - y0], 1), dz.astype(np.float32), TRI, x1 - x0, y1 - y0)
        return zb, fid, bar

def albedo(fid, bar):
    img = np.ones(fid.shape + (3,), np.float32)
    m = fid >= 0
    uvp = (uvpx.reshape(F, 3, 2)[fid[m]] * bar[m][..., None]).sum(1)
    img[m] = sample(base, uvp[:, 0], uvp[:, 1])
    return img

def iou(a, b): return (a & b).sum() / max((a | b).sum(), 1)

def fit(v, rows=None, steps=((6, 3), (3, 1)), sc_steps=(0.03, 0.01), th_steps=None):
    x0, y0, x1, y1 = v.rect
    R = ref_sil[y0:y1, x0:x1].astype(bool)
    if rows is not None: R = R.copy(); R[rows:] = False
    def score():
        _, fid, _ = v.render(); S = fid >= 0
        if rows is not None: S[rows:] = False
        return iou(S, R)
    best = score()
    for (dp, _), ds in zip(steps, sc_steps):
        improved = True
        while improved:
            improved = False
            cands = [('cx', dp), ('cx', -dp), ('cy', dp), ('cy', -dp), ('scale', v.scale * ds), ('scale', -v.scale * ds)]
            if th_steps: cands += [('theta', th_steps), ('theta', -th_steps)]
            for k, dv in cands:
                old = getattr(v, k); setattr(v, k, old + dv); sc = score()
                if sc > best + 1e-4: best = sc; improved = True
                else: setattr(v, k, old)
    print(f'fit {v.name}: iou {best:.3f} scale {v.scale:.1f} cx {v.cx:.1f} cy {v.cy:.1f} theta {np.degrees(v.theta):.1f}')
    return best

# ---------- back gear: reference rects on the pack / pouch / bedroll at a uniform scale (patch keeps its aspect).
# The pack face runs past the rect into the belts beside it in the sheet; the pack walls get camo fabric made from
# the pack's palette; the med pouch walls unfold into the pack fabric around it in the sheet.
def rect_sample(name, u, v):
    x0, y0, x1, y1 = REF_RECTS[name]
    return sample(ref, x0 + u * (x1 - x0), y0 + np.clip(v, 0, 1) * (y1 - y0))
# camo palette of the pack in the sheet (k-means over the pack fabric, NATO patch and med pouch excluded)
_px = np.concatenate([ref[158:245, 1008:1021].reshape(-1, 3), ref[160:228, 1078:1098].reshape(-1, 3), ref[229:247, 1010:1098].reshape(-1, 3)])
_crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 1e-4)
_, _lab, PAL = cv2.kmeans(_px.astype(np.float32), 4, None, _crit, 5, cv2.KMEANS_PP_CENTERS)
_cnt = np.bincount(_lab.ravel(), minlength=4); PAL = PAL[np.argsort(-_cnt)]   # most common colour first = base
print('camo palette', np.round(PAL, 3).tolist(), 'shares', np.round(np.sort(_cnt)[::-1] / _cnt.sum(), 2).tolist())
def noise_img(rng, h, w, scale):
    small = rng.random((max(2, int(h / scale)) + 3, max(2, int(w / scale)) + 3)).astype(np.float32)
    big = cv2.resize(small, (w + int(3 * scale), h + int(3 * scale)), interpolation=cv2.INTER_CUBIC)
    return big[:h, :w]
def camo(su, sv, seed=0, res=0.002):
    """Woodland-style camo in wall coords (meters) from the pack palette: base + three blob layers + fabric grain."""
    rng = np.random.default_rng(77 + seed)
    W_, H_ = int(0.8 / res), int(1.2 / res)
    out_ = np.broadcast_to(PAL[0], (H_, W_, 3)).copy()
    for li, (scale, thr) in enumerate(((0.045, 0.56), (0.03, 0.62), (0.02, 0.66))):
        nz_ = 0.65 * noise_img(rng, H_, W_, scale / res) + 0.35 * noise_img(rng, H_, W_, scale / res / 2.5)
        mk = smoothstep(thr - 0.02, thr + 0.02, nz_)[..., None]
        out_ = out_ * (1 - mk) + PAL[1 + li] * mk
    out_ = cv2.GaussianBlur(out_, (0, 0), 0.6)
    grain = (noise_img(rng, H_, W_, 0.0015 / res) - 0.5) * 0.06
    out_ = np.clip(out_ * (1 + grain[..., None]), 0, 1).astype(np.float32)
    return sample(out_, np.mod(su / res + 37 * seed, W_ - 2), np.mod(sv / res + 53 * seed, H_ - 2))
gcol = np.zeros((K, 3), np.float32); gw = np.zeros(K, np.float32)
for gid, name, d in ((1, 'panel', PANEL), (2, 'medkit', MEDKIT)):
    m = TG == gid
    X = TP[m]
    (bx0, bx1), (bz0, bz1) = d['x'], d['z']
    rx0, ry0, rx1, ry1 = REF_RECTS[name]
    sc = (bz1 - bz0) / (ry1 - ry0)           # meters per reference px, set by the height
    cw, ch = (rx1 - rx0) * sc, (bz1 - bz0)
    t = np.clip((X[:, 2] - (bz0 + bz1) / 2) / (ch / 2), 0, 1)
    yout = d['y_out'] + (d.get('y_out_top', d['y_out']) - d['y_out']) * t
    depth = np.clip(yout - X[:, 1], 0, None)
    nx, nz = TN[m][:, 0], TN[m][:, 2]
    side_w = smoothstep(0.35, 0.75, np.abs(nx)); top_w = smoothstep(0.35, 0.75, np.abs(nz))
    u = 0.5 + ((bx0 + bx1) / 2 - X[:, 0]) / cw    # image left = +x
    vf = (bz1 - X[:, 2]) / ch
    if name == 'panel':
        col_face = sample(ref, rx0 + u * (rx1 - rx0), ry0 + vf * (ry1 - ry0))
        # walls: plain pack fabric synthesised from the sheet's pack camo (no belts / shirt / mirrored prints)
        wid = np.where(side_w >= top_w, np.where(nx > 0, 1, 2), np.where(nz > 0, 3, 4))
        wt_ = np.where(side_w >= top_w, X[:, 2], X[:, 0])
        col_wall = np.zeros((len(X), 3), np.float32)
        for k_ in (1, 2, 3, 4):
            mk = wid == k_
            if mk.any(): col_wall[mk] = camo(depth[mk], wt_[mk], seed=k_)
        wall = np.maximum(side_w, top_w)[:, None]
        gcol[m] = col_face * (1 - wall) + col_wall * wall; gw[m] = 1
        continue
    u = u + side_w * np.where(nx > 0, -depth, depth) / cw
    v = vf + top_w * np.where(nz > 0, -depth, depth) / ch
    gcol[m] = sample(ref, rx0 + u * (rx1 - rx0), ry0 + v * (ry1 - ry0)); gw[m] = 1
m = TG == 3
X = TP[m]; bx0, bx1 = BEDROLL['x']; r = BEDROLL['r']
u = (bx1 - X[:, 0]) / (bx1 - bx0)
ang = np.arctan2(X[:, 2] - BEDROLL['zc'], X[:, 1] - BEDROLL['yc'])      # 0 = facing back (+y), +90 = up
ang = np.where(ang > np.pi / 2, np.pi - ang, np.where(ang < -np.pi / 2, -np.pi - ang, ang))  # mirror the hidden half
v = 0.5 - 0.5 * np.sin(ang)
cap = np.abs(TN[m][:, 0]) > 0.7
rad = np.hypot(X[:, 1] - BEDROLL['yc'], X[:, 2] - BEDROLL['zc']) / r
u = np.where(cap, np.where(u < 0.5, 0.01 + 0.07 * rad, 0.99 - 0.07 * rad), u)   # rolled end: rings from the end columns
v = np.where(cap, 0.35 + 0.3 * rad, v)
gcol[m] = rect_sample('bedroll', u, v) * np.where(cap, 0.82, 1.0)[:, None]; gw[m] = 1   # roll ends a bit darker
base2 = base.copy(); tmp = base2[cov]; tmp[gw > 0] = gcol[gw > 0]; base2[cov] = tmp

# ---------- body views (sheet figures + mask close-ups), aligned by silhouette fit + smoothed optical flow
def box_dist(X, d):
    lo = np.array([d['x'][0], d['y_in'], d['z'][0]]); hi = np.array([d['x'][1], d['y_out'], d['z'][1]])
    return np.linalg.norm(np.maximum(np.maximum(lo - X, X - hi), 0), axis=1)
def cyl_dist(X, d):
    r = np.hypot(X[:, 1] - d['yc'], X[:, 2] - d['zc']) - d['r']
    ex = np.maximum(np.maximum(d['x'][0] - X[:, 0], X[:, 0] - d['x'][1]), 0)
    return np.hypot(np.maximum(r, 0), ex)
GD = np.minimum(np.minimum(box_dist(TP, PANEL), box_dist(TP, MEDKIT)), cyl_dist(TP, BEDROLL))
GEARFAR = smoothstep(0.01, 0.035, GD)   # body right at the gear edge keeps the bake (contact shading, no shirt halo)
HEAD = np.array([0.015, -0.02, 1.68])
VIEWS = {
    'front': View('front', (0, 0, 640, 705), 0.0, 375.0, 303.0, 688.0, (0, 0, 0)),
    'back': View('back', (760, 0, 1350, 705), np.pi, 375.0, 1050.0, 690.0, (0, 0, 0)),
    'head_front': View('head_front', (8, 715, 182, 995), 0.0, 1050.0, 87.0, 850.0, HEAD),
    'head_back': View('head_back', (358, 715, 528, 995), np.pi, 900.0, 443.0, 830.0, HEAD),
    'head_left': View('head_left', (178, 715, 362, 995), np.radians(90), 950.0, 265.0, 830.0, HEAD),
    'head_right': View('head_right', (525, 715, 708, 995), np.radians(-45), 950.0, 615.0, 830.0, HEAD),
}
USE = P.get('views', {'back': 1.0, 'head_front': 1.0, 'head_back': 1.0, 'head_left': 1.0, 'head_right': 1.0})
z, ax = TP[:, 2], np.abs(TP[:, 0])
body = (TG == 0).astype(np.float32)
REGION = {
    'front': body,
    'back': body * smoothstep(0.84, 0.88, z) * (1 - smoothstep(1.49, 1.53, z)) * (1 - smoothstep(0.24, 0.28, ax)) * GEARFAR,
}
HZ = P.get('head_z', (1.52, 1.58))
for k in ('head_front', 'head_back', 'head_left', 'head_right'): REGION[k] = body * smoothstep(*HZ, z) * (1 - smoothstep(0.17, 0.2, np.abs(TP[:, 0] - 0.015)))
# the face (holes, burns) comes from the front close-up only; side close-ups would duplicate the holes elsewhere
for k in ('head_left', 'head_right'): REGION[k] = REGION[k] * (1 - smoothstep(0.2, 0.5, -TN[:, 1]))
FACE = {'front': (0.3, 0.75), 'back': (0.3, 0.75)}
for k in ('head_front', 'head_back', 'head_left', 'head_right'): FACE[k] = tuple(P.get('head_face', (0.25, 0.75)))
SMOOTH = {'front': 2.0, 'back': 3.0, 'head_front': -1, 'head_back': -1, 'head_left': -1, 'head_right': -1}
SMOOTH.update(P.get('smooth', {}))
acc = np.zeros((K, 3), np.float32); wsum = np.zeros(K, np.float32)
base_keep = base; base = base2   # renders for the flow see the gear already painted
for name, strength in USE.items():
    v = VIEWS[name]
    if name.startswith('head'):
        x0, y0, x1, y1 = v.rect
        R = ref_sil[y0:y1, x0:x1].astype(bool).copy(); rows = int((y1 - y0) * 0.55); R[rows:] = False
        ys, xs = np.nonzero(R); top = ys.min(); cxr = xs[ys < top + 60].mean()
        px, py, _ = v.proj(V[V[:, 2] > 1.55])
        v.cy += top - (py.min() - y0); v.cx += cxr - (px[py < py.min() + 60 * 1.0].mean() - x0)
        fit(v, rows=rows, steps=((4, 2), (2, 1)), sc_steps=(0.03, 0.01))
    else:
        fit(v)
    x0, y0, x1, y1 = v.rect
    zb, fid, bar = v.render()
    alb = albedo(fid, bar)
    sil = (fid >= 0).astype(np.uint8)
    a8 = cv2.cvtColor((np.clip(alb, 0, 1) * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
    r8 = refg[y0:y1, x0:x1].copy()
    r8[cv2.dilate(sil, np.ones((9, 9), np.uint8)) == 0] = 255   # ignore other figures on the sheet
    fl = flow(a8, r8, smooth=SMOOTH[name]) if SMOOTH[name] >= 0 else np.zeros(a8.shape + (2,), np.float32)
    refc = ref[y0:y1, x0:x1]
    gx, gy = np.meshgrid(np.arange(x1 - x0, dtype=np.float32), np.arange(y1 - y0, dtype=np.float32))
    warped = sample(refc, gx + fl[..., 0], gy + fl[..., 1])
    Image.fromarray((np.concatenate([alb, refc, warped], 1) * 255).clip(0, 255).astype(np.uint8)).save(os.path.join(dbg, f'{name}_alb_ref_warp.png'))
    px, py, dz = v.proj(TP)
    px -= x0; py -= y0
    inb = (px >= 1) & (py >= 1) & (px < x1 - x0 - 2) & (py < y1 - y0 - 2)
    pxi = np.clip(np.round(px).astype(int), 0, x1 - x0 - 1); pyi = np.clip(np.round(py).astype(int), 0, y1 - y0 - 1)
    zmin = cv2.erode(np.where(np.isfinite(zb), zb, 1e3).astype(np.float32), np.ones((3, 3), np.uint8))
    vis = inb & (dz <= zmin[pyi, pxi] + P.get('zeps', 0.012))
    edge = cv2.distanceTransform(sil, cv2.DIST_L2, 3)
    ew = smoothstep(1.0, 4.0, edge[pyi, pxi])
    facing = -(TN @ v.dir())
    w = smoothstep(*FACE[name], facing) * vis * ew * REGION[name] * strength
    fx = sample(np.ascontiguousarray(fl[..., 0]), px, py)
    fy = sample(np.ascontiguousarray(fl[..., 1]), px, py)
    col = sample(refc, px + fx, py + fy)
    if name.startswith('head'):   # never pull shirt / background into the mask
        lum = col @ np.array([0.3, 0.59, 0.11], np.float32)
        w = w * (1 - smoothstep(0.62, 0.75, lum))
    acc += col * w[:, None]; wsum += w
    print(f'view {name}: texels used {(w > 0.01).sum()}')
base = base_keep

# ---------- combine
old = base[cov]
wb = np.clip(wsum, 0, None)
refmix = acc / np.maximum(wb, 1e-6)[:, None]
alpha = np.clip(wb, 0, 1)
new = old * (1 - alpha[:, None]) + refmix * alpha[:, None]
new = np.where(gw[:, None] > 0, gcol, new)
outimg = base.copy(); outimg[cov] = new
outimg = dilate_fill(outimg, cov, 24)
Image.fromarray((np.clip(outimg, 0, 1) * 255 + 0.5).astype(np.uint8)).save(bc_path)
amap = np.zeros((RES, RES), np.float32); amap[cov] = np.maximum(alpha, gw)
Image.fromarray((amap * 255).astype(np.uint8)).save(os.path.join(dbg, 'ref_weight.png'))

# ---------- detail normals + brass from the painted areas (holes recess, cartridges / straps / patch edges stand out)
def keep(name):
    pth = os.path.join(texdir, name + '.png'); bak = os.path.join(texdir, name + '_bake.png')
    if not os.path.exists(bak): Image.open(pth).save(bak)
    return pth, np.asarray(Image.open(bak), np.float32) / 255
covf = cov.astype(np.float32)
lum = outimg @ np.array([0.3, 0.59, 0.11], np.float32)
lum = dilate_fill(lum[..., None], cov, 24)[..., 0]
lum = cv2.GaussianBlur(lum, (0, 0), P.get('nd_blur', 0.8))
h = lum - cv2.GaussianBlur(lum, (0, 0), P.get('nd_sigma', 6.0))
gx = cv2.Sobel(h, cv2.CV_32F, 1, 0, ksize=3) / 8; gy = cv2.Sobel(h, cv2.CV_32F, 0, 1, ksize=3) / 8
k = P.get('nd_strength', 7.0)
dmask = np.zeros((RES, RES), np.float32)
tmp = np.zeros(K, np.float32)
tmp += gw * 1.0
tmp = np.maximum(tmp, np.clip(alpha, 0, 1) * P.get('nd_body', 0.7))
dmask[cov] = tmp
dmask = cv2.GaussianBlur(dmask, (0, 0), 1.0) * covf
nd = np.stack([-k * gx * dmask, k * gy * dmask, np.ones_like(gx)], -1)   # OpenGL: +v is image up
nd /= np.linalg.norm(nd, axis=-1, keepdims=True)
npth, nb = keep('T_MaskedArsenal_Normal')
n1 = nb[..., :3] * 2 - 1
t = n1 + np.array([0, 0, 1.0], np.float32); u_ = nd * np.array([-1, -1, 1.0], np.float32)
rn = t * (np.sum(t * u_, -1, keepdims=True) / np.maximum(t[..., 2:3], 1e-4)) - u_
rn /= np.linalg.norm(rn, axis=-1, keepdims=True)
rn = dilate_fill(np.where(cov[..., None], rn, n1), cov, 24)
rn /= np.linalg.norm(rn, axis=-1, keepdims=True)
nimg = rn * 0.5 + 0.5
Image.fromarray((np.clip(nimg, 0, 1) * 255 + 0.5).astype(np.uint8)).save(npth)
ndx = nimg.copy(); ndx[..., 1] = 1 - ndx[..., 1]
Image.fromarray((np.clip(ndx, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(texdir, 'T_MaskedArsenal_Normal_DirectX.png'))
# brass cartridges in the painted areas: metallic, smoother
opth, orm = keep('T_MaskedArsenal_ORM')
hsv = cv2.cvtColor((np.clip(outimg, 0, 1) * 255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
hue, sat, val = hsv[..., 0] * 2, hsv[..., 1] / 255, hsv[..., 2] / 255
brass = smoothstep(0.3, 0.45, sat) * smoothstep(0.35, 0.5, val) * smoothstep(18, 26, hue) * (1 - smoothstep(48, 58, hue))
brass *= cv2.GaussianBlur(amap, (0, 0), 1.0) * covf
orm = orm.copy()
orm[..., 2] = np.maximum(orm[..., 2], 0.75 * brass)
orm[..., 1] = orm[..., 1] * (1 - brass) + 0.38 * brass
Image.fromarray((np.clip(orm, 0, 1) * 255 + 0.5).astype(np.uint8)).save(opth)
ms = np.stack([orm[..., 2]] * 3 + [1 - orm[..., 1]], -1)
Image.fromarray((np.clip(ms, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGBA').save(os.path.join(texdir, 'T_MaskedArsenal_MetallicSmoothness.png'))
print('brass texels', int((brass > 0.5).sum()))
for im in bpy.data.images:
    if im.filepath: im.reload()
bpy.ops.wm.save_as_mainfile(filepath=out)
print('PROJECT done')
