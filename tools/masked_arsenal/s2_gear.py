# Stage 2a: add back gear (LP + HP versions), delete LP faces hidden inside the pack
import bpy, sys, os, bmesh, math
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gear import PANEL, MEDKIT, BEDROLL, HIDE
src, out = sys.argv[1], sys.argv[2]
bpy.ops.wm.open_mainfile(filepath=src)
sc = bpy.context.scene
lp = bpy.data.objects['LP']; hp = bpy.data.objects['HP']

def box(bm, d, segs, part):
    (x0, x1), (z0, z1) = d['x'], d['z']; y0, y1 = d['y_in'], d['y_out']
    r = bmesh.ops.create_cube(bm, size=1.0)
    vs = r['verts']
    for v in vs:
        v.co = Vector(((x0 + x1) / 2 + v.co.x * (x1 - x0), (y0 + y1) / 2 + v.co.y * (y1 - y0), (z0 + z1) / 2 + v.co.z * (z1 - z0)))
    for v in vs:  # taper: outer face leans in toward the top
        if v.co.y > y0 + 1e-6 and v.co.z > (z0 + z1) / 2: v.co.y = d.get('y_out_top', y1)
    faces = list({f for v in vs for f in v.link_faces})
    edges = [e for e in {e for f in faces for e in f.edges} if any(v.co.y > y0 + 1e-6 for v in e.verts)]
    bmesh.ops.bevel(bm, geom=edges, offset=d['bevel'], segments=segs, profile=0.5, affect='EDGES', clamp_overlap=True)
    inner = [f for f in bm.faces if f.calc_center_median().y < y0 + 1e-5 and abs(f.normal.y) > 0.9 and f[part_layer] == 0 and f.is_valid]
    bmesh.ops.delete(bm, geom=inner, context='FACES')

def cyl(bm, d, segs):
    x0, x1 = d['x']; r = d['r']
    m = Matrix.Translation((((x0 + x1) / 2), d['yc'], d['zc'])) @ Matrix.Rotation(math.pi / 2, 4, 'Y')
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs, radius1=r, radius2=r, depth=x1 - x0, matrix=m)

def build(name, segs_box, segs_cyl):
    me = bpy.data.meshes.new(name); ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    bm = bmesh.new()
    global part_layer
    part_layer = bm.faces.layers.int.new('gear')
    for pid, (fn, d, s) in enumerate([(box, PANEL, segs_box), (box, MEDKIT, segs_box), (cyl, BEDROLL, segs_cyl)], start=1):
        before = set(bm.faces)
        if fn is box: fn(bm, d, s, part_layer)
        else: fn(bm, d, s)
        for f in bm.faces:
            if f not in before: f[part_layer] = pid
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    return ob
g_lp = build('GEAR', 2, 12)
g_hp = build('HP_GEAR', 3, 48)
# flat placeholder material for the HP gear (real colour comes from the reference projection later)
m = bpy.data.materials.new('M_GearHP'); m.use_nodes = True
b = m.node_tree.nodes['Principled BSDF']
b.inputs['Base Color'].default_value = (0.16, 0.14, 0.09, 1); b.inputs['Roughness'].default_value = 0.85; b.inputs['Metallic'].default_value = 0.0
g_hp.data.materials.append(m)
g_hp.hide_render = True
# sharp edges for LP gear: auto smooth by angle via edge sharpness
for e in g_lp.data.edges:
    pass
# delete body faces hidden inside the panel (LP to save triangles, HP so the bake never hits the old pouches)
(hx0, hx1), (hz0, hz1), ymin = HIDE['x'], HIDE['z'], HIDE['y_min']
def inside(v): return hx0 < v.co.x < hx1 and hz0 < v.co.z < hz1 and v.co.y > ymin
def carve(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    dead = [f for f in bm.faces if all(inside(v) for v in f.verts)]
    bmesh.ops.delete(bm, geom=dead, context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(ob.data); bm.free()
    return dead
dead = carve(lp); dead_hp = carve(hp)
print('HP faces carved', len(dead_hp))
print('deleted hidden faces', len(dead), 'LP tris now', len(lp.data.polygons), 'GEAR tris', len(g_lp.data.polygons), 'HP_GEAR tris', len(g_hp.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=out)
