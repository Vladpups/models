# Stage 4: bake HP -> LP (base color, roughness, metallic via emission; tangent normals; AO)
import bpy, sys, json, os, numpy as np
src, out, texdir = sys.argv[1], sys.argv[2], sys.argv[3]
P = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
RES = P.get('res', 2048); SS = P.get('ss', 2)   # supersample factor
BR = RES * SS
os.makedirs(texdir, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=src)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.cycles.samples = P.get('samples', 1); sc.cycles.use_denoising = False
hp = bpy.data.objects['HP_Medic']; lp = bpy.data.objects['LP_Medic']
hp.hide_render = False; hp.hide_set(False); lp.hide_render = False
bk = sc.render.bake
bk.use_selected_to_active = True; bk.cage_extrusion = P.get('extrusion', 0.015); bk.max_ray_distance = P.get('ray', 0.035)
bk.margin = P.get('margin', 16) * SS; bk.margin_type = 'EXTEND'; bk.use_clear = True
# LP bake material
mat = bpy.data.materials.new('M_Medic'); mat.use_nodes = True
lp.data.materials.clear(); lp.data.materials.append(mat)
tex = mat.node_tree.nodes.new('ShaderNodeTexImage'); mat.node_tree.nodes.active = tex
# HP material hooks
hm = hp.data.materials[0]; hn = hm.node_tree
bsdf = hn.nodes['Principled BSDF']; mout = hn.nodes['Material Output']
col_sock = bsdf.inputs['Base Color'].links[0].from_socket
rough_sock = bsdf.inputs['Roughness'].links[0].from_socket
metal_sock = bsdf.inputs['Metallic'].links[0].from_socket
emis = hn.nodes.new('ShaderNodeEmission')
def select():
    for o in sc.objects: o.select_set(False)
    hp.select_set(True); lp.select_set(True); bpy.context.view_layer.objects.active = lp
def new_img(name, noncolor, float_buf=False, res=BR):
    im = bpy.data.images.new(name, res, res, alpha=False, float_buffer=float_buf)
    if noncolor: im.colorspace_settings.name = 'Non-Color'
    return im
def bake_emit(sock, name, noncolor):
    hn.links.new(sock, emis.inputs['Color']); hn.links.new(emis.outputs[0], mout.inputs['Surface'])
    im = new_img(name, noncolor, float_buf=True); tex.image = im; select()
    bpy.ops.object.bake(type='EMIT')
    return im
def to_np(im):
    a = np.empty(im.size[0] * im.size[1] * 4, np.float32); im.pixels.foreach_get(a)
    return a.reshape(im.size[1], im.size[0], 4)
def down(a):
    if SS == 1: return a
    h, w, c = a.shape
    return a.reshape(h // SS, SS, w // SS, SS, c).mean((1, 3))
import time
t = time.time()
base = down(to_np(bake_emit(col_sock, 'bk_base', False))); print('base', round(time.time() - t, 1)); t = time.time()
rough = down(to_np(bake_emit(rough_sock, 'bk_rough', True))); print('rough', round(time.time() - t, 1)); t = time.time()
metal = down(to_np(bake_emit(metal_sock, 'bk_metal', True))); print('metal', round(time.time() - t, 1)); t = time.time()
# normals: restore BSDF
hn.links.new(bsdf.outputs[0], mout.inputs['Surface'])
im = new_img('bk_normal', True, float_buf=True); tex.image = im; select()
bpy.ops.object.bake(type='NORMAL', normal_space='TANGENT')
nrm = down(to_np(im)); print('normal', round(time.time() - t, 1)); t = time.time()
# renormalize normal after downsampling
v = nrm[..., :3] * 2 - 1; v /= np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-6); nrm[..., :3] = v * 0.5 + 0.5
# AO from HP geometry, LP invisible to rays
ao = None
if P.get('ao', True):
    for attr in ('visible_camera', 'visible_diffuse', 'visible_glossy', 'visible_transmission', 'visible_volume_scatter', 'visible_shadow'):
        setattr(lp, attr, False)
    sc.cycles.samples = P.get('ao_samples', 48)
    sc.world = sc.world or bpy.data.worlds.new('W')
    sc.world.light_settings.distance = P.get('ao_dist', 0.12)
    aor = P.get('ao_res', 1024)
    im = new_img('bk_ao', True, float_buf=True, res=aor); tex.image = im; select()
    bk.margin = P.get('margin', 16) * aor // RES
    bpy.ops.object.bake(type='AO')
    ao_small = to_np(im)[..., 0]
    if aor != RES:
        from PIL import Image
        ao = np.asarray(Image.fromarray(ao_small.astype(np.float32), 'F').resize((RES, RES), Image.BICUBIC), np.float32)
    else:
        ao = ao_small
    print('ao', round(time.time() - t, 1))
    for attr in ('visible_camera', 'visible_diffuse', 'visible_glossy', 'visible_transmission', 'visible_volume_scatter', 'visible_shadow'):
        setattr(lp, attr, True)
def save(name, arr, noncolor):
    h, w = arr.shape[:2]
    im = bpy.data.images.new(name, w, h, alpha=arr.shape[2] == 4 and name.endswith('Smoothness'), float_buffer=False)
    if noncolor: im.colorspace_settings.name = 'Non-Color'
    rgba = np.ones((h, w, 4), np.float32); rgba[..., :arr.shape[2]] = arr
    im.pixels.foreach_set(rgba.ravel())
    im.filepath_raw = os.path.join(texdir, name + '.png'); im.file_format = 'PNG'
    im.save()
    return im
# base color: emission bake values are linear -> convert to sRGB for 8-bit storage
def lin2srgb(c):
    c = np.clip(c, 0, 1); return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)
save('T_Medic_BaseColor', lin2srgb(base[..., :3]), True)
save('T_Medic_Normal', nrm[..., :3], True)
ndx = nrm[..., :3].copy(); ndx[..., 1] = 1 - ndx[..., 1]
save('T_Medic_Normal_DirectX', ndx, True)
R = np.clip(rough[..., 0], 0, 1); M = np.clip(metal[..., 0], 0, 1)
O = np.clip(ao, 0, 1) if ao is not None else np.ones_like(R)
O = 1 - P.get('ao_strength', 0.7) * (1 - O)
save('T_Medic_ORM', np.stack([O, R, M], -1), True)
save('T_Medic_MetallicSmoothness', np.stack([M, M, M, 1 - R], -1), True)
bpy.ops.wm.save_as_mainfile(filepath=out)
print('DONE')
