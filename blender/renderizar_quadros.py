"""Renderiza TODOS os quadros de um .blend criado por importar_md3.py (vista de lado, fundo transparente) em PNGs numerados.
Uso: blender -b <modelo.blend> --python renderizar_quadros.py -- <pasta_saida> [tamanho=160] [azimute_graus=0] [escala_fixa]"""
import bpy, sys, os, math, json, mathutils
a = sys.argv[sys.argv.index("--") + 1:]
saida = os.path.abspath(a[0]); os.makedirs(saida, exist_ok=True)
tam = int(a[1]) if len(a) > 1 else 160
az = math.radians(float(a[2])) if len(a) > 2 else 0.0
sc = bpy.context.scene
obj = [o for o in bpy.data.objects if o.type == "MESH" and o.data.shape_keys][0]
chaves = obj.data.shape_keys.key_blocks
nomes = [kb.name for kb in chaves][1:]
n = len(nomes)
# enquadramento: uniao dos volumes de todos os quadros
mn = mathutils.Vector((1e9,) * 3); mx = mathutils.Vector((-1e9,) * 3)
for f in range(1, n + 1):
    sc.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    for c in obj.evaluated_get(dg).bound_box:
        for k in range(3):
            mn[k] = min(mn[k], c[k]); mx[k] = max(mx[k], c[k])
centro = (mn + mx) / 2
alt = max(mx.z - mn.z, max(mx.x - mn.x, mx.y - mn.y))
fixo = float(a[3]) if len(a) > 3 else 0.0
if fixo:
    centro.z = fixo * 0.40
    alt = fixo / 1.08
cd = bpy.data.cameras.new("cam"); cd.type = "ORTHO"; cd.ortho_scale = alt * 1.08
cam = bpy.data.objects.new("cam", cd); sc.collection.objects.link(cam); sc.camera = cam
dist = alt * 4
cam.location = centro + mathutils.Vector((-math.cos(az) * dist, -math.sin(az) * dist, 0))
cam.rotation_euler = (centro - cam.location).to_track_quat("-Z", "Y").to_euler()
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "TEXTURE"; sc.display.shading.show_cavity = False
sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = tam
sc.render.image_settings.color_mode = "RGBA"
for f in range(1, n + 1):
    sc.frame_set(f)
    sc.render.filepath = os.path.join(saida, "q%03d.png" % f)
    bpy.ops.render.render(write_still=True)
json.dump(nomes, open(os.path.join(saida, "nomes.json"), "w"))
print("renderizados", n)
