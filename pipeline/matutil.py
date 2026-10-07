import bpy, os

def setup_material(obj, texdir, name='Zealot_MAT'):
    """Principled material wired to the final baked textures (glTF-compatible layout)."""
    mat=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes=True
    mat.use_backface_culling=True
    nt=mat.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out=nt.nodes.new('ShaderNodeOutputMaterial'); out.location=(600,0)
    b=nt.nodes.new('ShaderNodeBsdfPrincipled'); b.location=(250,0)
    nt.links.new(b.outputs[0], out.inputs['Surface'])
    def tex(fname, noncolor, loc):
        img=bpy.data.images.load(os.path.join(texdir,fname), check_existing=True)
        img.colorspace_settings.name='Non-Color' if noncolor else 'sRGB'
        n=nt.nodes.new('ShaderNodeTexImage'); n.image=img; n.location=loc
        return n
    bc=tex('Zealot_BaseColor.png', False, (-500,300))
    nt.links.new(bc.outputs['Color'], b.inputs['Base Color'])
    orm=tex('Zealot_ORM.png', True, (-500,0))
    sep=nt.nodes.new('ShaderNodeSeparateColor'); sep.location=(-200,0)
    nt.links.new(orm.outputs['Color'], sep.inputs[0])
    nt.links.new(sep.outputs['Green'], b.inputs['Roughness'])
    nt.links.new(sep.outputs['Blue'], b.inputs['Metallic'])
    nm=tex('Zealot_Normal_OpenGL.png', True, (-500,-300))
    nmap=nt.nodes.new('ShaderNodeNormalMap'); nmap.location=(-200,-300)
    nt.links.new(nm.outputs['Color'], nmap.inputs['Color'])
    nt.links.new(nmap.outputs['Normal'], b.inputs['Normal'])
    # occlusion slot read by the glTF exporter
    grp=bpy.data.node_groups.get('glTF Material Output')
    if grp is None:
        grp=bpy.data.node_groups.new('glTF Material Output','ShaderNodeTree')
        grp.interface.new_socket('Occlusion', in_out='INPUT', socket_type='NodeSocketFloat')
    g=nt.nodes.new('ShaderNodeGroup'); g.node_tree=grp; g.location=(250,-400)
    nt.links.new(sep.outputs['Red'], g.inputs['Occlusion'])
    obj.data.materials.clear(); obj.data.materials.append(mat)
    return mat
