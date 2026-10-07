# Stage 4b: project the reference head photos (front, both sides, back) onto the head texels of the baked maps.
# args: in.blend texdir ref.png map.json [json params]
import bpy, sys, os, json, shutil, numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage
src, texdir, refp, mapp = sys.argv[1:5]
P = json.loads(sys.argv[5]) if len(sys.argv) > 5 else {}
M = json.load(open(mapp))
bpy.ops.wm.open_mainfile(filepath=src)
me = bpy.data.objects['LP_Medic'].data
def tex(name):
    p = os.path.join(texdir, name + '.png'); b = os.path.join(texdir, name + '_bake.png')
    if not os.path.exists(b): shutil.copy2(p, b)   # keep the pure bake, re-runs start from it
    return np.asarray(Image.open(b).convert('RGB'), np.float32) / 255, p
base, base_p = tex('T_Medic_BaseColor'); nrm, nrm_p = tex('T_Medic_Normal'); orm, orm_p = tex('T_Medic_ORM')
RES = base.shape[0]
# ---------- rasterize LP in UV space: per-texel 3D position, smooth normal, coverage
co = np.array([v.co[:] for v in me.vertices]); vn = np.array([v.normal[:] for v in me.vertices])
uvl = me.uv_layers.active.data
cover = np.zeros((RES, RES), bool); head = np.zeros((RES, RES), bool)
POS = np.zeros((RES, RES, 3), np.float32); NRM = np.zeros((RES, RES, 3), np.float32)
for p in me.polygons:
    vi = list(p.vertices); li = list(p.loop_indices)
    uv = np.array([uvl[l].uv[:] for l in li]) * RES - 0.5
    uv[:, 1] = RES - 1 - uv[:, 1]
    x0, y0 = np.floor(uv.min(0)).astype(int); x1, y1 = np.ceil(uv.max(0)).astype(int)
    xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1, RES - 1) + 1), np.arange(max(y0, 0), min(y1, RES - 1) + 1))
    a, b, c = uv; v0 = b - a; v1 = c - a; den = v0[0] * v1[1] - v1[0] * v0[1]
    if abs(den) < 1e-12: continue
    px = xs - a[0]; py = ys - a[1]
    l1 = (px * v1[1] - v1[0] * py) / den; l2 = (v0[0] * py - px * v0[1]) / den; l0 = 1 - l1 - l2
    m = (l0 >= -1e-4) & (l1 >= -1e-4) & (l2 >= -1e-4)
    if not m.any(): continue
    X, Y = xs[m], ys[m]; L = np.stack([l0[m], l1[m], l2[m]], 1)
    cover[Y, X] = True
    if co[vi, 2].max() < P.get('z_min', 1.63): continue
    head[Y, X] = True
    POS[Y, X] = L @ co[vi]; n = L @ vn[vi]; NRM[Y, X] = n / np.linalg.norm(n, axis=1, keepdims=True)
print('head texels', int(head.sum()))
# ---------- reference tiles: foreground masks, background inpainted with the nearest head colour
ref = Image.open(refp).convert('RGB')
UP = P.get('up', 4)
TILES = {'front': (5, 690, 184, 1010), 'left': (186, 690, 353, 1010), 'back': (356, 690, 518, 1010), 'right': (521, 690, 700, 1010)}
T = {}
for k, (x0, y0, x1, y1) in TILES.items():
    im = ref.crop((x0, y0, x1, y1)).resize(((x1 - x0) * UP, (y1 - y0) * UP), Image.LANCZOS)
    im = im.filter(ImageFilter.UnsharpMask(radius=2 * UP / 4, percent=P.get('sharpen', 60), threshold=2))
    a = np.asarray(im, np.float32) / 255
    # background = bright and colourless; wispy hair over the white backdrop counts as background too
    bgl = (a.min(2) > P.get('bg_val', 0.78)) & ((a.max(2) - a.min(2)) < P.get('bg_sat', 0.10))
    fg = ndimage.binary_opening(~bgl, iterations=2 * UP)
    lab_, nl = ndimage.label(fg); sizes = ndimage.sum(fg, lab_, range(1, nl + 1))
    fg = lab_ == (1 + int(np.argmax(sizes)))   # the head itself, not crumbs or neighbouring tiles
    fg = ndimage.binary_erosion(fg, iterations=int(UP * P.get('erode_px', 2)))   # drop wispy hair edges blended with the white background
    d = ndimage.distance_transform_edt(~fg)
    # background -> smooth extension of the nearby head colours (normalized convolution, coarse to fine)
    fill = a.copy(); todo = ~fg
    for sg in (2, 5, 12, 30):
        wsm = ndimage.gaussian_filter(fg.astype(np.float32), sg * UP)
        num = np.stack([ndimage.gaussian_filter(a[..., c] * fg, sg * UP) for c in range(3)], -1)
        okk = todo & (wsm > 0.02)
        fill[okk] = num[okk] / wsm[okk, None]; todo &= ~okk
    fill[todo] = a[fg].mean(0)
    T[k] = (fill, d / UP, (x0, y0))
def sample(k, px, py):
    a, d, (x0, y0) = T[k]
    u = (px - x0) * UP - 0.5; v = (py - y0) * UP - 0.5
    H, W = d.shape
    ok = (u >= 0) & (v >= 0) & (u < W - 1) & (v < H - 1)
    u = np.clip(u, 0, W - 1.001); v = np.clip(v, 0, H - 1.001)
    i0 = np.floor(v).astype(int); j0 = np.floor(u).astype(int); fv = (v - i0)[:, None]; fu = (u - j0)[:, None]
    c = (a[i0, j0] * (1 - fu) * (1 - fv) + a[i0, j0 + 1] * fu * (1 - fv) + a[i0 + 1, j0] * (1 - fu) * fv + a[i0 + 1, j0 + 1] * fu * fv)
    dist = d[i0, j0]
    valid = ok * np.maximum(np.clip(1 - dist / P.get('out_px', 4.0), 0, 1), 0.02)   # outside the silhouette: smooth fill, low weight
    return c, valid
# ---------- projections (model -> sheet pixels)
Yi, Xi = np.nonzero(head); p = POS[Yi, Xi].astype(np.float64); n = NRM[Yi, Xi].astype(np.float64)
x, y, z = p.T
s, ss = M['s'], M['ss']
VIEWS = {
    'front': ((M['x_midr'] + (x - M['x_mid3']) / s, M['chin_py'] - (z - M['z_chin']) / s), -n[:, 1]),
    'left':  ((M['side_ear_px'] + (y - M['ear_y']) / ss, M['side_chin_py'] - (z - M['z_chin']) / ss), n[:, 0]),
    'right': ((P.get('right_ear_px', 610.5) - (y - M['ear_y']) / ss, M['side_chin_py'] - (z - M['z_chin']) / ss), -n[:, 0]),
    'back':  ((P.get('back_cx', 434.0) - (x - M['x_mid3']) / s, M['side_chin_py'] - (z - M['z_chin']) / ss), n[:, 1]),
}
def smoothstep(e0, e1, t): t = np.clip((t - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
# crown (seen by no photo): hair strands from the back tile, laid front-to-back over rows of its upper hair
ty0, ty1 = P.get('crown_y', (-0.12, 0.09)); tr0, tr1 = P.get('crown_rows', (742.0, 800.0))
VIEWS['top'] = ((P.get('back_cx', 434.0) - (x - M['x_mid3']) / s, tr0 + np.clip((y - ty0) / (ty1 - ty0), 0, 1) * (tr1 - tr0)), n[:, 2])
TOP_TILE = 'back'
K = P.get('k', 6.0); FLOOR = P.get('floor', 0.04)
acc = np.zeros((len(x), 3)); wsum = np.zeros(len(x))
for k, ((px, py), facing) in VIEWS.items():
    c, valid = sample(TOP_TILE if k == 'top' else k, px, py)
    w = (np.clip(facing, 0, 1) + FLOOR) ** K * valid * P.get('view_w', {}).get(k, 1.0)
    if k in ('left', 'right'):   # side tiles are slight 3/4 views: keep them off the front of the face
        hz = smoothstep(1.86, 1.89, z)   # temples and hair above the brow may take the side tiles further forward
        w *= smoothstep(P.get('side_y0', -0.14) - 0.05 * hz, P.get('side_y1', -0.09) - 0.06 * hz, y)
    acc += c * w[:, None]; wsum += w
photo = acc / np.maximum(wsum, 1e-9)[:, None]
# collar line: low V at the front, higher at the sides and back
fb = smoothstep(-0.09, -0.03, y)
alpha = smoothstep(P.get('neck0', 1.665) + 0.04 * fb, P.get('neck1', 1.70) + 0.03 * fb, z) * (wsum > 0)
# match the photo's skin tone to the baked skin in the blend band so the neck and arms stay consistent
band = (z > 1.75) & (z < 1.80) & (np.abs(x) > 0.035) & (np.abs(x) < 0.07) & (n[:, 1] < -0.5)   # cheeks
gain = np.ones(3)
if band.sum() > 50:
    bk = base[Yi[band], Xi[band]]; ph = photo[band]
    gain = np.clip(np.median(bk, 0) / np.maximum(np.median(ph, 0), 1e-3), 0.8, 1.25) ** P.get('tone_match', 0.3)
print('tone gain', np.round(gain, 3))
photo = np.clip(photo * gain, 0, 1)
# where no photo sees the surface well (top of the head), borrow fine strand detail from the bake
vis = np.zeros(len(x))
for k, ((px, py), facing) in VIEWS.items():
    if k != 'top': vis = np.maximum(vis, (sample(k, px, py)[1] > 0.5) * np.clip(facing, 0, 1))
lum = base.mean(2); hpass = lum - ndimage.gaussian_filter(lum, P.get('detail_sigma', 3))
photo = np.clip(photo + (hpass[Yi, Xi] * P.get('detail_gain', 1.0) * (1 - np.clip(vis / 0.5, 0, 1)))[:, None], 0, 1)
out = base.copy(); out[Yi, Xi] = base[Yi, Xi] * (1 - alpha[:, None]) + photo * alpha[:, None]
# soften the baked normal/AO detail under the photo (Meshy's face details no longer match the new face)
A = np.zeros((RES, RES), np.float32); A[Yi, Xi] = alpha
face = smoothstep(1.70, 1.73, z) * (n[:, 1] < 0.2)
FL = np.zeros((RES, RES), np.float32); FL[Yi, Xi] = alpha * (P.get('flat_face', 0.75) * face + P.get('flat_hair', 0.4) * (1 - face))
# bleed the edited texels into the gutter (texels outside every island)
edit = np.zeros((RES, RES), bool); edit[Yi, Xi] = True
d, ind = ndimage.distance_transform_edt(~edit, return_indices=True)
gut = (~cover) & (d <= P.get('bleed', 12))
out[gut] = out[ind[0][gut], ind[1][gut]]; A[gut] = A[ind[0][gut], ind[1][gut]]; FL[gut] = FL[ind[0][gut], ind[1][gut]]
flat = np.array([0.5, 0.5, 1.0], np.float32)
nrm2 = nrm * (1 - FL[..., None]) + flat * FL[..., None]
v = nrm2 * 2 - 1; v /= np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-6); nrm2 = v * 0.5 + 0.5
orm2 = orm.copy(); orm2[..., 0] = orm[..., 0] * (1 - FL) + FL * np.maximum(orm[..., 0], 0.85)   # lighter AO where the photo carries shading
def save(arr, path):
    Image.fromarray((np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path)
save(out, base_p); save(nrm2, nrm_p)
ndx = nrm2.copy(); ndx[..., 1] = 1 - ndx[..., 1]; save(ndx, os.path.join(texdir, 'T_Medic_Normal_DirectX.png'))
save(orm2, orm_p)
ms = os.path.join(texdir, 'T_Medic_MetallicSmoothness.png')
if os.path.exists(ms):
    msa = np.asarray(Image.open(ms).convert('RGBA'), np.float32) / 255
    msa[..., 3] = 1 - orm2[..., 1]; Image.fromarray((msa * 255 + 0.5).astype(np.uint8), 'RGBA').save(ms)
print('face projection done')
