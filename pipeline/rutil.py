import bpy, math
from mathutils import Vector
def setup_render(res=600, samples=16):
    sc=bpy.context.scene
    sc.render.engine='CYCLES'
    sc.cycles.device='CPU'
    sc.cycles.samples=samples
    sc.cycles.use_denoising=False
    sc.render.resolution_x=res; sc.render.resolution_y=res
    sc.render.film_transparent=False
    w=bpy.data.worlds.new('W') if not sc.world else sc.world
    sc.world=w; w.use_nodes=True
    bg=w.node_tree.nodes.get('Background'); bg.inputs[0].default_value=(0.8,0.8,0.82,1); bg.inputs[1].default_value=0.6
    if 'KeyL' not in bpy.data.objects:
        l=bpy.data.lights.new('KeyL','SUN'); l.energy=3.5
        o=bpy.data.objects.new('KeyL',l); sc.collection.objects.link(o); o.rotation_euler=(math.radians(50),0,math.radians(-30))
def cam_shot(path, center, dist, az_deg, el_deg=5, ortho=2.1, res=None):
    sc=bpy.context.scene
    cam=bpy.data.objects.get('Cam')
    if not cam:
        cd=bpy.data.cameras.new('Cam'); cam=bpy.data.objects.new('Cam',cd); sc.collection.objects.link(cam)
    cam.data.type='ORTHO'; cam.data.ortho_scale=ortho
    az=math.radians(az_deg); el=math.radians(el_deg)
    c=Vector(center)
    pos=c+Vector((math.sin(az)*math.cos(el)*-1*-1, -math.cos(az)*math.cos(el), math.sin(el)))*dist
    cam.location=pos
    d=(c-pos).normalized()
    cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
    sc.camera=cam
    if res: sc.render.resolution_x=sc.render.resolution_y=res
    sc.render.filepath=path
    bpy.ops.render.render(write_still=True)
