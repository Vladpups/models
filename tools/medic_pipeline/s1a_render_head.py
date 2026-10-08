# Stage 1a: render the Meshy head from the front (ortho, transparent) for MediaPipe landmark detection
# args: s1.blend out.png ; camera must match the HEADCAM json passed to s1b_head.py
import bpy, sys, mathutils
bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
sc = bpy.context.scene
hp = bpy.data.objects['HP_Medic']; hp.hide_render = False; bpy.data.objects['LP_Medic'].hide_render = True
sc.render.engine = 'CYCLES'; sc.cycles.samples = 16; sc.cycles.use_denoising = False; sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = 1000
sc.world = bpy.data.worlds.new('W'); sc.world.use_nodes = True; sc.world.node_tree.nodes['Background'].inputs[0].default_value = (1, 1, 1, 1)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 0.36
cam.location = (0, -10.05, 1.84); cam.rotation_euler = mathutils.Vector((0, 1, 0)).to_track_quat('-Z', 'Y').to_euler()
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 2.0
sun.rotation_euler = (-mathutils.Vector((0.3, -1, 0.6))).to_track_quat('-Z', 'Y').to_euler()
sc.render.filepath = sys.argv[2]; bpy.ops.render.render(write_still=True)
