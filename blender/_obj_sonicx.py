import bpy, os
obj = [o for o in bpy.data.objects if o.type == "MESH"][0]
bpy.context.view_layer.objects.active = obj; obj.select_set(True)
for f, nome in ((6, "parado"), (17, "andando_1"), (33, "correndo_1"), (41, "dash_1"), (75, "voando_1"), (69, "caindo_1")):
    bpy.context.scene.frame_set(f)
    bpy.context.view_layer.update()
    bpy.ops.wm.obj_export(filepath=os.path.abspath("sonic-x-3d/SONIC_X_%s.obj" % nome), export_selected_objects=True, apply_modifiers=True, export_materials=False)
