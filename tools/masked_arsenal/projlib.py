# Helpers for projecting the reference sheet onto the low poly: rasterizer, sampling, flow alignment.
import numpy as np, cv2


def raster(P2, Z, tris, W, H, depth_test=True):
    """Rasterize triangles given per-vertex screen coords P2 (n,2; pixel centers at integers) and depth Z (n,).
    Returns zbuf (H,W), fid (H,W) int (-1 empty), bary (H,W,3)."""
    zbuf = np.full((H, W), np.inf, np.float32)
    fid = np.full((H, W), -1, np.int32)
    bary = np.zeros((H, W, 3), np.float32)
    T = P2[tris]  # (F,3,2)
    lo = np.floor(T.min(1)).astype(int); hi = np.ceil(T.max(1)).astype(int)
    for f in range(len(tris)):
        x0, y0 = max(lo[f, 0], 0), max(lo[f, 1], 0)
        x1, y1 = min(hi[f, 0], W - 1), min(hi[f, 1], H - 1)
        if x1 < x0 or y1 < y0: continue
        (ax, ay), (bx, by), (cx, cy) = T[f]
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-12: continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        w0 = ((by - cy) * (xs - cx) + (cx - bx) * (ys - cy)) / den
        w1 = ((cy - ay) * (xs - cx) + (ax - cx) * (ys - cy)) / den
        w2 = 1 - w0 - w1
        e = -1e-4
        inside = (w0 >= e) & (w1 >= e) & (w2 >= e)
        if not inside.any(): continue
        a, b, c = tris[f]
        z = w0 * Z[a] + w1 * Z[b] + w2 * Z[c]
        sub = zbuf[y0:y1 + 1, x0:x1 + 1]
        upd = inside & (z < sub) if depth_test else inside
        sub[upd] = z[upd]
        fid[y0:y1 + 1, x0:x1 + 1][upd] = f
        bb = bary[y0:y1 + 1, x0:x1 + 1]
        bb[upd] = np.stack([w0[upd], w1[upd], w2[upd]], -1)
    return zbuf, fid, bary


def sample(img, x, y, border=cv2.BORDER_REPLICATE):
    """Bilinear sample img (H,W[,C] float32) at float pixel coords x,y (any shape)."""
    shp = x.shape; n = x.size; cols = 4096
    rows = max(1, -(-n // cols)); pad = rows * cols - n
    mx = np.concatenate([x.ravel(), np.zeros(pad)]).astype(np.float32).reshape(rows, cols)
    my = np.concatenate([y.ravel(), np.zeros(pad)]).astype(np.float32).reshape(rows, cols)
    out = cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=border)
    c = img.shape[2] if img.ndim == 3 else None
    out = out.reshape(-1, c) if c else out.ravel()
    return out[:n].reshape(shp + ((c,) if c else ()))


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)


def flow(src_gray, dst_gray, preset=cv2.DISOPTICAL_FLOW_PRESET_MEDIUM, smooth=0):
    """Dense flow so that dst(p + f(p)) ~ src(p). Inputs uint8."""
    dis = cv2.DISOpticalFlow_create(preset)
    dis.setFinestScale(0)
    dis.setVariationalRefinementIterations(10)
    f = dis.calc(src_gray, dst_gray, None)
    if smooth: f = cv2.GaussianBlur(f, (0, 0), smooth)
    return f


def lin2srgb(c):
    c = np.clip(c, 0, 1); return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def srgb2lin(c):
    c = np.clip(c, 0, 1); return np.where(c <= 0.04045, c / 12.92, np.power((c + 0.055) / 1.055, 2.4))


def dilate_fill(img, valid, iters=24):
    """Extend valid pixels into invalid ones (texture padding)."""
    img = img.copy(); valid = valid.copy()
    for _ in range(iters):
        acc = np.zeros_like(img); cnt = np.zeros(valid.shape, np.float32)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            v = np.roll(np.roll(valid, dy, 0), dx, 1)
            acc += np.roll(np.roll(img, dy, 0), dx, 1) * v[..., None]
            cnt += v
        new = (~valid) & (cnt > 0)
        if not new.any(): break
        img[new] = acc[new] / cnt[new][:, None]
        valid = valid | new
    return img
