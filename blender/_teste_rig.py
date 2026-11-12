import bpy, sys, os, math, mathutils
out = os.path.abspath(sys.argv[sys.argv.index("--")+1])
sc = bpy.context.scene
arm = bpy.data.objects["NeoMetal_rig"]; obj = bpy.data.objects["NeoMetal"]
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "TEXTURE"
sc.render.resolution_x = 500; sc.render.resolution_y = 500
sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.25, 0.27, 0.33)
def shot(nome, loc, alvo=(0,0,1.35)):
    cam.location = loc
    cam.rotation_euler = (mathutils.Vector(alvo) - mathutils.Vector(loc)).to_track_quat("-Z","Y").to_euler()
    sc.render.filepath = out + nome; bpy.ops.render.render(write_still=True)
shot("_a_frente.png", (0,-9,1.6))
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="POSE")
pb = arm.pose.bones
def rot(n, eul):
    pb[n].rotation_mode = "XYZ"; pb[n].rotation_euler = [math.radians(a) for a in eul]
rot("braco_sup.R", (0,0,-70)); rot("antebraco.R", (-60,0,0))
rot("braco_sup.L", (0,0,70)); rot("antebraco.L", (60,0,0))
rot("coxa.R", (-40,0,0)); rot("canela.R", (60,0,0)); rot("coxa.L", (30,0,0))
rot("corpo", (35,0,0)); rot("cabeca", (-25,0,0)); rot("capa1", (-20,0,0))
bpy.context.view_layer.update()
shot("_b_pose_lado.png", (9,0,1.6)); shot("_b_pose_frente.png", (0,-9,1.6))
