"""Renderiza o Neo posado de um quadro com algumas ilhas da malha em destaque (magenta; o resto em cinza) na mesma camera do render do quadro (so le; nao grava a cena).
Serve para ver que peca e cada ilha. Uso: blender -b <pasta>/cena_<quadros>.blend --python destacar_ilhas_pose.py -- <metricas.json> <saida_dir> <quadros q,q> <raiz,raiz,...> [<tam_px>]
Saida: <saida_dir>/dest_q<quadro>_lado.png e dest_q<quadro>_34.png."""
import json
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import usuario_neo as U

arg = sys.argv[sys.argv.index("--") + 1:]
met = json.load(open(arg[0]))
SAIDA = os.path.abspath(arg[1])
QUADROS = arg[2].split(",")
RAIZES = {int(x) for x in arg[3].split(",")}
TAM = int(arg[4]) if len(arg) > 4 else 560
VISTAS = {"lado": Vector((-1.0, 0.0, 0.0)), "34": Vector((-0.62, -0.78, 0.18))}
os.makedirs(SAIDA, exist_ok=True)

base = bpy.data.objects["NeoMetal"]
n = len(base.data.vertices)
pai = list(range(n))


def achar(a):
    while pai[a] != a:
        pai[a] = pai[pai[a]]
        a = pai[a]
    return a


for p in base.data.polygons:
    vs = list(p.vertices)
    for v in vs[1:]:
        ra, rb = achar(vs[0]), achar(v)
        if ra != rb:
            pai[rb] = ra
raiz = np.array([achar(i) for i in range(n)])
destaque = np.isin(raiz, list(RAIZES))

sc = bpy.context.scene
cam = bpy.data.objects["cam_u"]
cd = cam.data
sc.render.resolution_x = sc.render.resolution_y = TAM
sc.display.shading.color_type = "MATERIAL"


def material(nome, cor):
    m = bpy.data.materials.new(nome)
    m.diffuse_color = cor
    return m


cinza, magenta = material("_cinza", (0.72, 0.74, 0.80, 1.0)), material("_destaque", (1.0, 0.0, 0.9, 1.0))
for o in bpy.data.objects:
    if o.type in {"MESH", "CURVE"}:
        o.hide_render = True
for q in QUADROS:
    obj = bpy.data.objects["NeoPose_%s" % q]
    copia = obj.copy()
    copia.data = obj.data.copy()
    copia.name = "dest_%s" % q
    sc.collection.objects.link(copia)
    copia.data.materials.clear()
    copia.data.materials.append(cinza)
    copia.data.materials.append(magenta)
    for p in copia.data.polygons:
        p.material_index = 1 if destaque[list(p.vertices)].all() else 0
    copia.hide_render = False
    centro = Vector(met["centros"][q])
    for nome, direcao in VISTAS.items():
        U.foto(cam, cd, os.path.join(SAIDA, "dest_q%s_%s.png" % (q, nome)), centro, direcao, met["escala_render"])
    copia.hide_render = True
print("fim destaque", sorted(RAIZES), QUADROS)
