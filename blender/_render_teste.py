import bpy, sys, math, mathutils
a = sys.argv[sys.argv.index("--")+1:]
frames = [int(x) for x in a[1].split(",")]
import os
out = os.path.abspath(a[0])
sc = bpy.context.scene
obj = [o for o in bpy.data.objects if o.type == "MESH"][0]
print("shape keys:", len(obj.data.shape_keys.key_blocks), "frame0 blk:", obj.data.shape_keys.key_blocks[1].frame, obj.data.shape_keys.key_blocks[2].frame)
print("markers:", [(m.name, m.frame) for m in sc.timeline_markers][:40])
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
sc.frame_set(frames[0]); bpy.context.view_layer.update()
bb = [obj.matrix_world @ mathutils.Vector(c) for c in obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).bound_box]
alt = max(v.z for v in bb)
cam.location = (alt*0.3, -alt*3.2, alt*0.7)
d = mathutils.Vector((0, 0, alt*0.5)) - cam.location
cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
cam.data.lens = 50
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "TEXTURE"
sc.render.resolution_x = 480; sc.render.resolution_y = 480
sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.2, 0.22, 0.28)
for f in frames:
    sc.frame_set(f)
    sc.render.filepath = "%s_%03d.png" % (out, f)
    bpy.ops.render.render(write_still=True)
    print("render", f, obj.data.shape_keys.eval_time)
