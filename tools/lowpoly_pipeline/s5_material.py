# Stage 5: final PBR material on LP from baked textures (glTF/FBX friendly)
import bpy, sys, os
src, out, texdir = sys.argv[1], sys.argv[2], sys.argv[3]
bpy.ops.wm.open_mainfile(filepath=src)
lp = bpy.data.objects['LP_Scavenger']
hp = bpy.data.objects.get('HP_Scavenger')
for attr in ('visible_camera', 'visible_diffuse', 'visible_glossy', 'visible_transmission', 'visible_volume_scatter', 'visible_shadow'):
    setattr(lp, attr, True)
for m in list(bpy.data.materials):
    if m.name.startswith('M_Scavenger'): bpy.data.materials.remove(m)
mat = bpy.data.materials.new('M_Scavenger'); mat.use_nodes = True
lp.data.materials.clear(); lp.data.materials.append(mat)
nt = mat.node_tree; N = nt.nodes; L = nt.links
bsdf = N['Principled BSDF']
def img(name, noncolor):
    path = os.path.join(texdir, name + '.png')
    im = bpy.data.images.load(path, check_existing=False); im.name = name
    if noncolor: im.colorspace_settings.name = 'Non-Color'
    n = N.new('ShaderNodeTexImage'); n.image = im; n.label = name; return n
bc = img('T_Scavenger_BaseColor', False); bc.location = (-700, 300)
orm = img('T_Scavenger_ORM', True); orm.location = (-700, 0)
nm = img('T_Scavenger_Normal', True); nm.location = (-700, -300)
sep = N.new('ShaderNodeSeparateColor'); sep.location = (-400, 0)
nmap = N.new('ShaderNodeNormalMap'); nmap.location = (-400, -300)
L.new(bc.outputs['Color'], bsdf.inputs['Base Color'])
L.new(orm.outputs['Color'], sep.inputs['Color'])
L.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
L.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
L.new(nm.outputs['Color'], nmap.inputs['Color'])
L.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
# glTF occlusion hookup (custom group recognised by the glTF exporter)
g = bpy.data.node_groups.get('glTF Material Output') or bpy.data.node_groups.new('glTF Material Output', 'ShaderNodeTree')
if not g.interface.items_tree:
    g.interface.new_socket('Occlusion', in_out='INPUT', socket_type='NodeSocketFloat')
gn = N.new('ShaderNodeGroup'); gn.node_tree = g; gn.location = (-100, -500)
L.new(sep.outputs['Red'], gn.inputs['Occlusion'])
if hp: bpy.data.objects.remove(hp)  # HP no longer needed in the deliverable scene
for im in list(bpy.data.images):
    if im.users == 0: bpy.data.images.remove(im)
bpy.ops.wm.save_as_mainfile(filepath=out)
