"""Close-up de um objeto da cena (ex.: NeoPose_279): argumentos -- <objeto> <cx,cy,cz> <escala> <saida_prefixo> [<tam>]"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import usuario_neo as U
arg = sys.argv[sys.argv.index("--") + 1:]
nome = arg[0]
cx, cy, cz = [float(x) for x in arg[1].split(",")]
esc = float(arg[2]); pref = arg[3]; tam = int(arg[4]) if len(arg) > 4 else 900
cam, cd = U.camera_render(tam, tam, 1.0)
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.type == "MESH":
        o.hide_render = (o.name != nome)
sc.display.shading.color_type = "TEXTURE"
for v, d in {"lado": (-1, 0, 0), "34": (-0.62, -0.78, 0.18), "frente": (0, -1, 0), "topo": (0, -0.05, 1)}.items():
    U.foto(cam, cd, pref + "_" + v + ".png", (cx, cy, cz), d, esc)
print("ok")
