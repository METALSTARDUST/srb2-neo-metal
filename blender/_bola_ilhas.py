"""Mostra, em cores diferentes, as pecas pequenas (ilhas) em volta da bola do tornozelo esquerdo, para saber o que e o que.
Uso: blender -b <modelo.blend> --python _bola_ilhas.py -- <saida_dir>"""
import colorsys
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corrigir_pesos
import perna_poses as PP
import usuario_neo as U

saida = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
os.makedirs(saida, exist_ok=True)
U.preparar(tecido=False)
bpy.data.objects["capa"].hide_render = True
U.repouso()
corpo = bpy.data.objects["NeoMetal"]
me = corpo.data
raiz, co = corrigir_pesos._componentes(corpo)
bola = np.array(PP.bola_tornozelo("esquerdo")[:])
cores = np.full((len(me.vertices), 3), 0.78)
legenda = []
k = 0
for r in np.unique(raiz):
    idx = np.where(raiz == r)[0]
    c = co[idx].mean(axis=0)
    if len(idx) < 8 or len(idx) > 60 or np.linalg.norm(c - bola) > 0.2:
        continue
    h = (k * 0.618034) % 1.0
    rgb = colorsys.hsv_to_rgb(h, 0.9, 0.95)
    cores[idx] = rgb
    legenda.append((k, len(idx), tuple(round(float(x), 3) for x in c), tuple(round(float(x), 2) for x in rgb)))
    k += 1
for item in legenda:
    print("ILHA", item)
attr = me.color_attributes.new(name="ilhas_bola", type="FLOAT_COLOR", domain="POINT")
attr.data.foreach_set("color", np.hstack([cores, np.ones((len(cores), 1))]).ravel().tolist())
me.color_attributes.active_color = attr
try:
    me.color_attributes.default_color_name = "ilhas_bola"
except (AttributeError, TypeError):
    pass
cam, cd = U.camera_render(700, 700, exposicao=0.2)
bpy.context.scene.display.shading.color_type = "VERTEX"
alvo = (bola[0], bola[1], bola[2] - 0.05)
for nome, d in {"lado": (-1, 0, 0.0), "frente": (0, -1, 0.0), "baixo": (0, -0.03, -1), "tres_quartos": (-0.62, -0.78, 0.30)}.items():
    U.foto(cam, cd, os.path.join(saida, "bola_%s.png" % nome), alvo, d, 0.55)
print("ok")
