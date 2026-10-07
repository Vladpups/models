# Stage 2: bake HP -> LP (base color, tangent normal, roughness/metallic, AO)
import bpy, sys, os, time
args=sys.argv[sys.argv.index('--')+1:]
BLEND, TEXDIR, OUT = args[0], args[1], args[2]
BR=int(os.environ.get('BAKERES','2048'))
PASSES=os.environ.get('PASSES','color,normal,rm,ao').split(',')
os.makedirs(TEXDIR, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=BLEND)
sc=bpy.context.scene
sc.render.engine='CYCLES'; sc.cycles.device='CPU'
# no light transport needed: every pass reads material data or emission
sc.cycles.max_bounces=0; sc.cycles.diffuse_bounces=0; sc.cycles.glossy_bounces=0
sc.cycles.transmission_bounces=0; sc.cycles.transparent_max_bounces=0; sc.cycles.volume_bounces=0
sc.cycles.use_denoising=False
for l in [o for o in bpy.data.objects if o.type=='LIGHT']: bpy.data.objects.remove(l)
w=bpy.data.worlds.new('BakeW'); sc.world=w; w.use_nodes=True; w.node_tree.nodes['Background'].inputs[1].default_value=0.0
bk=sc.render.bake
bk.use_selected_to_active=True
bk.cage_extrusion=float(os.environ.get('CAGE','0.012'))
bk.max_ray_distance=float(os.environ.get('MAXRAY','0.03'))
bk.margin=int(BR/2048*16); bk.margin_type='EXTEND'
bk.use_clear=True
hp=bpy.data.objects['Zealot_HP']; lp=bpy.data.objects['Zealot']
hp.hide_render=False; hp.hide_set(False); lp.hide_set(False)
mat=bpy.data.materials.get('Zealot_MAT') or bpy.data.materials.new('Zealot_MAT')
mat.use_nodes=True; nt=mat.node_tree
lp.data.materials.clear(); lp.data.materials.append(mat)

def target(name, noncolor, flt=False):
    img=bpy.data.images.new(name, BR, BR, alpha=False, float_buffer=flt)
    img.colorspace_settings.name='Non-Color' if noncolor else 'sRGB'
    n=nt.nodes.new('ShaderNodeTexImage'); n.image=img; n.name=name
    return n

def bake(kind, node, spp, **kw):
    t=time.time()
    sc.cycles.samples=spp
    for n in nt.nodes: n.select=False
    node.select=True; nt.nodes.active=node
    bpy.ops.object.select_all(action='DESELECT')
    hp.select_set(True); lp.select_set(True); bpy.context.view_layer.objects.active=lp
    bpy.ops.object.bake(type=kind, **kw)
    print('baked',kind,node.name,round(time.time()-t,1),'s', flush=True)

def save_png(img, path):
    img.filepath_raw=path; img.file_format='PNG'; img.save()

hnt=hp.data.materials[0].node_tree
outn=[n for n in hnt.nodes if n.type=='OUTPUT_MATERIAL'][0]
orig_from=[l for l in hnt.links if l.to_socket==outn.inputs['Surface']][0].from_socket
sep=[n for n in hnt.nodes if n.type=='SEPARATE_COLOR'][0]
SPP=int(os.environ.get('SPP','16'))

if 'color' in PASSES:
    n=target('bake_basecolor', False)
    bake('DIFFUSE', n, SPP, pass_filter={'COLOR'})
    save_png(n.image, f'{TEXDIR}/raw_basecolor.png')

if 'normal' in PASSES:
    # Normal pass uses the shading normal, so the HP normal map detail is included
    n=target('bake_normal', True, flt=True)
    bake('NORMAL', n, SPP, normal_space='TANGENT')
    n.image.filepath_raw=f'{TEXDIR}/raw_normal.exr'; n.image.file_format='OPEN_EXR'; n.image.save()

if 'rm' in PASSES:
    # roughness -> G, metallic -> B (glTF channel layout), via emission
    em=hnt.nodes.new('ShaderNodeEmission'); comb=hnt.nodes.new('ShaderNodeCombineColor')
    hnt.links.new(sep.outputs['Green'], comb.inputs['Green']); hnt.links.new(sep.outputs['Blue'], comb.inputs['Blue'])
    comb.inputs['Red'].default_value=1.0
    hnt.links.new(comb.outputs[0], em.inputs['Color'])
    hnt.links.new(em.outputs[0], outn.inputs['Surface'])
    n=target('bake_rm', True)
    bake('EMIT', n, max(4,SPP//4))
    save_png(n.image, f'{TEXDIR}/raw_rm.png')
    hnt.links.new(orig_from, outn.inputs['Surface'])

if 'ao' in PASSES:
    # only_local: occlusion from HP geometry only (the LP would otherwise shadow it)
    ao=hnt.nodes.new('ShaderNodeAmbientOcclusion'); ao.only_local=True; ao.samples=16
    ao.inputs['Distance'].default_value=float(os.environ.get('AODIST','0.15'))
    em2=hnt.nodes.new('ShaderNodeEmission'); hnt.links.new(ao.outputs['AO'], em2.inputs['Color'])
    hnt.links.new(em2.outputs[0], outn.inputs['Surface'])
    n=target('bake_ao', True)
    bake('EMIT', n, int(os.environ.get('SPP_AO','8')))
    save_png(n.image, f'{TEXDIR}/raw_ao.png')
    hnt.links.new(orig_from, outn.inputs['Surface'])

bpy.ops.wm.save_as_mainfile(filepath=OUT)
