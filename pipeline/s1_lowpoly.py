# Stage 1: import HP, normalize transform, build 5000-tri LP, UV unwrap
import bpy, sys, os, bmesh, math
import numpy as np
from mathutils import Vector, Matrix
args=sys.argv[sys.argv.index('--')+1:]
GLB, OUT = args[0], args[1]
TARGET_TRIS=int(os.environ.get('TARGET','5000'))
HEIGHT=1.90
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
hp=[o for o in bpy.data.objects if o.type=='MESH'][0]
hp.name='Zealot_HP'; hp.data.name='Zealot_HP'
# normalize: feet on ground, exact height, centered between feet
co=np.zeros(len(hp.data.vertices)*3); hp.data.vertices.foreach_get('co',co); co=co.reshape(-1,3)
zmin,zmax=co[:,2].min(),co[:,2].max()
s=HEIGHT/(zmax-zmin)
low=co[co[:,2]<zmin+0.12]
xl=low[low[:,0]<0][:,0].mean(); xr=low[low[:,0]>0][:,0].mean()
off=Vector((-(xl+xr)/2, 0, -zmin))
M=Matrix.Diagonal((s,s,s,1))@Matrix.Translation(off)
hp.data.transform(M)
hp.data.update()
print('scale',s,'offset',off[:])
# LP copy with welded seams
lp=hp.copy(); lp.data=hp.data.copy(); lp.name='Zealot'; lp.data.name='Zealot'
bpy.context.scene.collection.objects.link(lp)
bm=bmesh.new(); bm.from_mesh(lp.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bm.to_mesh(lp.data); bm.free()
lp.data.materials.clear()
# remove the hidden interior shell (inner walls of robe/hood/sleeves never seen from outside)
sys.path.insert(0, os.path.dirname(__file__))
from vis import vertex_visibility
if os.environ.get('CULL','1')=='1':
    vis=vertex_visibility(lp.data, ndirs=int(os.environ.get('VISDIRS','64')))
    bm=bmesh.new(); bm.from_mesh(lp.data); bm.verts.ensure_lookup_table()
    # keep a band of inner surface around everything visible (geodesic distance), so slits and openings stay closed
    import heapq
    GROW=float(os.environ.get('GROW','0.02'))
    nv=len(bm.verts); dist=np.full(nv,np.inf); hq=[]
    for i in np.nonzero(vis>0)[0]: dist[i]=0.0; hq.append((0.0,int(i)))
    heapq.heapify(hq)
    while hq:
        d,i=heapq.heappop(hq)
        if d>dist[i] or d>GROW: continue
        vi=bm.verts[i]
        for e in vi.link_edges:
            j=e.other_vert(vi).index; nd=d+e.calc_length()
            if nd<dist[j] and nd<=GROW: dist[j]=nd; heapq.heappush(hq,(nd,j))
    keep_v=set(np.nonzero(dist<=GROW)[0].tolist())
    keep_f=set(f.index for f in bm.faces if any(v.index in keep_v for v in f.verts))
    dead=[f for f in bm.faces if f.index not in keep_f]
    print('interior faces removed',len(dead),'of',len(bm.faces))
    bmesh.ops.delete(bm, geom=dead, context='FACES')
    # drop small floating leftovers
    bm.faces.ensure_lookup_table(); seen=set(); comps=[]
    for f in bm.faces:
        if f in seen: continue
        st=[f]; seen.add(f); comp=[]
        while st:
            a=st.pop(); comp.append(a)
            for e in a.edges:
                for g in e.link_faces:
                    if g not in seen: seen.add(g); st.append(g)
        comps.append(comp)
    comps.sort(key=len, reverse=True)
    small=[f for c in comps[1:] if len(c)<200 for f in c]
    print('components',[len(c) for c in comps[:8]],'removed small faces',len(small))
    bmesh.ops.delete(bm, geom=small, context='FACES')
    bm.to_mesh(lp.data); bm.free()
# Taubin smoothing (no shrink) to remove cloth micro-wrinkles before decimation; detail goes to normal map
TAUBIN=int(os.environ.get('TAUBIN','30'))
if TAUBIN>0:
    me=lp.data
    P=np.zeros(len(me.vertices)*3); me.vertices.foreach_get('co',P); P=P.reshape(-1,3)
    E=np.zeros(len(me.edges)*2,dtype=np.int64); me.edges.foreach_get('vertices',E); E=E.reshape(-1,2)
    deg=np.bincount(E.ravel(),minlength=len(P)).astype(float)
    mask=np.ones(len(P))
    mask[np.abs(P[:,0])>0.60]=float(os.environ.get('HANDSMOOTH','0.3'))
    mask[(P[:,2]>1.45)&(P[:,2]<1.68)&(np.abs(P[:,0])<0.2)&(P[:,1]<0)]=0.5
    bnd=np.zeros(len(P),dtype=bool)
    ec=np.bincount(np.array([k for p in me.polygons for k in p.edge_keys]).view([('a',np.int64),('b',np.int64)]).ravel().view(np.int64).reshape(-1,2)[:,0]*0,minlength=1) if False else None
    import bmesh as _bm
    _b=_bm.new(); _b.from_mesh(me)
    for e in _b.edges:
        if e.is_boundary: bnd[e.verts[0].index]=True; bnd[e.verts[1].index]=True
    _b.free()
    mask[bnd]=0.0
    def lap(P):
        acc=np.zeros_like(P)
        np.add.at(acc,E[:,0],P[E[:,1]]); np.add.at(acc,E[:,1],P[E[:,0]])
        return acc/deg[:,None]-P
    for i in range(TAUBIN):
        P=P+0.5*mask[:,None]*lap(P)
        P=P-0.53*mask[:,None]*lap(P)
    me.vertices.foreach_set('co',P.ravel()); me.update()
# importance weights: lower = more detail kept
vg=lp.vertex_groups.new(name='decimate_w')
cl=np.zeros(len(lp.data.vertices)*3); lp.data.vertices.foreach_get('co',cl); cl=cl.reshape(-1,3)
w=np.ones(len(cl))
W_HAND,W_FACE,W_FEET=[float(x) for x in os.environ.get('WTS','0.5,0.85,0.9').split(',')]
w[np.abs(cl[:,0])>0.60]=W_HAND
face=(cl[:,2]>1.45)&(cl[:,2]<1.68)&(np.abs(cl[:,0])<0.2)&(cl[:,1]<0)
w[face]=W_FACE
w[cl[:,2]<0.15]=W_FEET
for val in np.unique(w):
    vg.add([int(i) for i in np.nonzero(w==val)[0]], float(val), 'REPLACE')
bpy.context.view_layer.objects.active=lp
for o in bpy.context.selected_objects: o.select_set(False)
lp.select_set(True)
d=lp.modifiers.new('dec','DECIMATE'); d.decimate_type='COLLAPSE'
d.ratio=TARGET_TRIS/len(lp.data.polygons); d.use_collapse_triangulate=True
d.vertex_group='decimate_w'; d.vertex_group_factor=1.0
bpy.ops.object.modifier_apply(modifier='dec')
lp.vertex_groups.clear()
# cleanup: remove degenerate, beautify near-flat edges
bm=bmesh.new(); bm.from_mesh(lp.data)
bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges[:])
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts)>3])
flat=[e for e in bm.edges if len(e.link_faces)==2 and e.calc_face_angle(0)<math.radians(8)]
bmesh.ops.beautify_fill(bm, faces=bm.faces[:], edges=flat, method='ANGLE')
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
nm=sum(1 for e in bm.edges if not e.is_manifold)
bm.to_mesh(lp.data); bm.free()
# fix faces folded inside-out by the decimation: flip faces that viewers outside see mostly from behind
from vis import face_side_visibility
bm=bmesh.new(); bm.from_mesh(lp.data); bm.faces.ensure_lookup_table()
sv=face_side_visibility(bm)
flip=[bm.faces[i] for i,(fr,bk) in enumerate(sv) if bk>fr and bk>=3]
bmesh.ops.reverse_faces(bm, faces=flip)
bm.to_mesh(lp.data); bm.free()
print('flipped faces fixed',len(flip))
for p in lp.data.polygons: p.use_smooth=True
tris=sum(len(p.vertices)-2 for p in lp.data.polygons)
print('LP tris',tris,'verts',len(lp.data.vertices),'nonmanifold edges',nm)
print('boundary edges', sum(1 for e in lp.data.edges if False))
import collections
reg=collections.Counter()
for p in lp.data.polygons:
    c=p.center
    reg["hands" if abs(c.x)>0.60 else "feet" if c.z<0.15 else "head" if c.z>1.45 else "body"]+=1
print('regions',dict(reg))
bm=bmesh.new(); bm.from_mesh(lp.data)
ang=np.degrees(np.array([e.calc_face_angle(0) for e in bm.edges])); bm.free()
print('dihedral >60',(ang>60).sum(),'>90',(ang>90).sum(),'>150',(ang>150).sum())
# UV unwrap
while lp.data.uv_layers: lp.data.uv_layers.remove(lp.data.uv_layers[0])
uvlay=lp.data.uv_layers.new(name='UVMap')
import xatlas
me=lp.data
V=np.zeros(len(me.vertices)*3,dtype=np.float32); me.vertices.foreach_get('co',V); V=V.reshape(-1,3)
F=np.array([p.vertices[:] for p in me.polygons],dtype=np.uint32)
# texel-density boost for hands and face: inflate those regions only for parametrization
DETAIL=float(os.environ.get('DETAIL_UV','1.35'))
Vp=V.copy()
for side in (-1,1):
    c=np.array([0.70*side,0.07,1.33],dtype=np.float32)
    m=V[:,0]*side>0.56
    Vp[m]=c+(V[m]-c)*DETAIL
fc=np.array([0.0,-0.08,1.57],dtype=np.float32)
m=(V[:,2]>1.47)&(V[:,2]<1.68)&(V[:,1]<-0.02)&(np.abs(V[:,0])<0.13)
Vp[m]=fc+(V[m]-fc)*DETAIL
RES=2048
co=xatlas.ChartOptions(); co.max_iterations=4
def run(tpu):
    at=xatlas.Atlas(); at.add_mesh(Vp,F)
    po=xatlas.PackOptions(); po.resolution=RES; po.texels_per_unit=tpu; po.padding=5; po.bilinear=True; po.rotate_charts=True; po.bruteForce=True
    at.generate(co,po); return at
# estimate, then binary search the largest texel density that fits one square atlas
at0=xatlas.Atlas(); at0.add_mesh(Vp,F); po0=xatlas.PackOptions(); po0.resolution=RES; po0.padding=5; po0.bilinear=True
at0.generate(co,po0)
lo,hi=0.0,None; t=at0.texels_per_unit if hasattr(at0,'texels_per_unit') else 500.0
print('estimate tpu',t)
best=None
for it in range(10):
    at=run(t)
    ok=(at.atlas_count==1)
    if ok: lo=t; best=at
    else: hi=t
    t = (lo*1.15 if hi is None else (lo+hi)/2) if ok else (lo+hi)/2 if lo>0 else t*0.8
print('tpu',lo,'atlases',best.atlas_count,'size',best.width,best.height,'util',best.utilization,'charts',best.chart_count)
vmap,ind,uvs=best[0]
assert len(ind)==len(F)
L=np.zeros(len(me.loops)*2,dtype=np.float32)
for fi,p in enumerate(me.polygons):
    for k,li in enumerate(p.loop_indices):
        L[li*2:li*2+2]=uvs[ind[fi]][k]
# stretch the packed layout to fill the whole 0..1 square (textures are baked fresh, padding grows proportionally)
L=L.reshape(-1,2); e=2.0/RES
mn=L.min(0); mx=L.max(0)
L=(L-mn)/(mx-mn)*(1-2*e)+e
print('uv bbox before stretch',mn,mx)
uvlay.data.foreach_set('uv',L.ravel())
# report UV usage
me=lp.data
uv=np.zeros(len(me.loops)*2); me.uv_layers[0].data.foreach_get('uv',uv); uv=uv.reshape(-1,2)
area=0
for p in me.polygons:
    a=uv[p.loop_start:p.loop_start+p.loop_total]
    u=a[1]-a[0]; v=a[2]-a[0]; area+=0.5*abs(u[0]*v[1]-u[1]*v[0])
print('uv coverage',round(area,3))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
