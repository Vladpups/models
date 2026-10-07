import numpy as np, math, time
from mathutils import Vector
from mathutils.bvhtree import BVHTree
def fib_dirs(n):
    i=np.arange(n)+0.5
    phi=np.arccos(1-2*i/n); th=math.pi*(1+5**0.5)*i
    return np.stack([np.cos(th)*np.sin(phi),np.sin(th)*np.sin(phi),np.cos(phi)],1)
def vertex_visibility(me, ndirs=96, eps=1e-3, far=10.0):
    """fraction of hemisphere directions (around vertex normal) along which a ray escapes the mesh"""
    t=time.time()
    verts=[v.co.copy() for v in me.vertices]
    polys=[p.vertices[:] for p in me.polygons]
    tree=BVHTree.FromPolygons(verts, polys, all_triangles=False, epsilon=0.0)
    D=fib_dirs(ndirs); Dv=[Vector(d) for d in D]
    vis=np.zeros(len(verts))
    for i,v in enumerate(me.vertices):
        n=v.normal
        o=v.co+n*eps
        cnt=0; tot=0
        for d in Dv:
            if d.dot(n)<0.05: continue
            tot+=1
            hit=tree.ray_cast(o,d,far)
            if hit[0] is None: cnt+=1
        vis[i]=cnt/max(tot,1)
    print('visibility computed in',round(time.time()-t,1),'s',flush=True)
    return vis

def face_side_visibility(bm, ndirs=128, far=10.0):
    """for each face: (#directions it is seen from in front, #directions seen from behind) by viewers at infinity"""
    from mathutils.bvhtree import BVHTree
    bm.faces.ensure_lookup_table()
    tree=BVHTree.FromBMesh(bm)
    D=[Vector(d) for d in fib_dirs(ndirs)]
    res=[]
    for f in bm.faces:
        c=f.calc_center_median(); n=f.normal
        fr=bk=0
        for u in D:
            s=u.dot(n)
            if abs(s)<0.05: continue
            o=c+n*(1e-4 if s>0 else -1e-4)
            hit=tree.ray_cast(o,u,far)
            if hit[0] is None:
                if s>0: fr+=1
                else: bk+=1
        res.append((fr,bk))
    return res
