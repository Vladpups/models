# Stage 2b: turn raw bakes into final game textures
import bpy, sys, os
import numpy as np
from PIL import Image, ImageDraw
args=sys.argv[sys.argv.index('--')+1:]
BLEND, RAW, OUTDIR = args[0], args[1], args[2]
os.makedirs(OUTDIR, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=BLEND)
me=bpy.data.objects['Zealot'].data

def load(path):
    img=bpy.data.images.load(path)
    img.colorspace_settings.name='Non-Color'   # raw values, no transform
    W,H=img.size
    a=np.array(img.pixels[:],dtype=np.float32).reshape(H,W,4)[::-1]
    return a

bc=load(f'{RAW}/raw_basecolor.png')[...,:3]
nr=load(f'{RAW}/raw_normal.exr')[...,:3]
rm=load(f'{RAW}/raw_rm.png')[...,:3]
ao=load(f'{RAW}/raw_ao.png')[...,0]
R=bc.shape[0]

# coverage mask: rasterized UV triangles, grown by a few px (bake margin already filled these)
uv=np.zeros(len(me.loops)*2); me.uv_layers[0].data.foreach_get('uv',uv); uv=uv.reshape(-1,2)
m=Image.new('L',(R,R),0); d=ImageDraw.Draw(m)
for p in me.polygons:
    pts=[(uv[l,0]*R,(1-uv[l,1])*R) for l in range(p.loop_start,p.loop_start+p.loop_total)]
    d.polygon(pts,fill=255,outline=255)
from PIL import ImageFilter
m=m.filter(ImageFilter.MaxFilter(9))
mask=np.array(m)>0
print('texel coverage incl. margin', mask.mean())

def push_pull(img, mask):
    """fill unmasked pixels from masked ones (mip pyramid), keeps mip-mapping clean at UV seams"""
    if mask.all(): return img
    lv=[(img*mask[...,None], mask.astype(np.float32))]
    while lv[-1][1].shape[0]>1:
        c,w=lv[-1]; h=c.shape[0]//2
        c2=c.reshape(h,2,h,2,-1).sum((1,3)); w2=w.reshape(h,2,h,2).sum((1,3))
        lv.append((c2,w2))
    col=lv[-1][0]/np.maximum(lv[-1][1][...,None],1e-8)
    for c,w in reversed(lv[:-1]):
        up=np.repeat(np.repeat(col,2,0),2,1)
        own=c/np.maximum(w[...,None],1e-8)
        col=np.where((w>0)[...,None], own, up)
    return np.where(mask[...,None], img, col)

def save(arr, name, mode='RGB', bits=8):
    a=np.clip(arr,0,1)
    if bits==16 and mode=='L':
        Image.fromarray((a*65535+0.5).astype(np.uint16)).save(f'{OUTDIR}/{name}')
    else:
        Image.fromarray((a*255+0.5).astype(np.uint8), mode).save(f'{OUTDIR}/{name}', optimize=True)
    print('saved',name)

# base color: baked raw values are display-referred sRGB already
bc=push_pull(bc, mask); save(bc,'Zealot_BaseColor.png')
# normal: renormalize, fill gaps with flat normal, OpenGL (+Y) and DirectX (-Y)
v=nr*2-1; v/=np.maximum(np.linalg.norm(v,axis=2,keepdims=True),1e-6)
v[~mask]=(0,0,1)
v=push_pull(v, mask); v/=np.maximum(np.linalg.norm(v,axis=2,keepdims=True),1e-6)
ngl=v*0.5+0.5
save(ngl,'Zealot_Normal_OpenGL.png')
ndx=ngl.copy(); ndx[...,1]=1-ndx[...,1]
save(ndx,'Zealot_Normal_DirectX.png')
rough=push_pull(rm[...,1:2], mask)[...,0]; metal=push_pull(rm[...,2:3], mask)[...,0]
aof=push_pull(ao[...,None], mask)[...,0]
print('roughness mean',rough[mask].mean(),'metal mean',metal[mask].mean(),'metal>0.5 frac',(metal[mask]>0.5).mean(),'ao mean',aof[mask].mean())
save(np.stack([aof,rough,metal],2),'Zealot_ORM.png')                         # glTF / Unreal: R=AO G=Rough B=Metal
ms=np.concatenate([np.stack([metal,metal,metal],2),(1-rough)[...,None]],2)  # Unity Standard/URP: RGB=Metallic A=Smoothness
save(ms,'Zealot_MetallicSmoothness.png','RGBA')
save(aof,'Zealot_AO.png','L')
