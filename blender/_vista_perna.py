"""Renderiza a perna direita do Neo em repouso (quadril, coxa, joelho) de frente e de lado: -- <saida_prefixo>"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import usuario_neo as U
pref = sys.argv[sys.argv.index("--") + 1]
U.preparar()
U.repouso()
cam, cd = U.camera_render(900, 900, 1.0)
for o in bpy.data.objects:
    if o.type == "MESH":
        o.hide_render = (o.name != "NeoMetal")
for v, d in {"frente": (0, -1, 0), "lado": (1, 0, 0), "34": (0.62, -0.78, 0.18)}.items():
    U.foto(cam, cd, pref + "_" + v + ".png", (0.05, 0.0, 1.25), d, 0.95)
print("ok")
