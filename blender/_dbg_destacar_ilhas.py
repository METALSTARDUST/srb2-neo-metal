"""Destaca em cor as ilhas sem peso do corpo do Neo (no arquivo base antes da correcao) e renderiza o ombro: -- <saida_prefixo>"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np, bmesh
from mathutils import Vector
import usuario_neo as U
pref = sys.argv[sys.argv.index("--") + 1]
U.preparar()
corpo = bpy.data.objects["NeoMetal"]
me = corpo.data
n = len(me.vertices)
pai = list(range(n))
def achar(a):
    while pai[a] != a:
        pai[a] = pai[pai[a]]
        a = pai[a]
    return a
for p in me.polygons:
    vs = list(p.vertices)
    r0 = achar(vs[0])
    for x in vs[1:]:
        pai[achar(x)] = r0
raiz = np.array([achar(i) for i in range(n)])
nomes = {vg.index: vg.name for vg in corpo.vertex_groups}
ossos = {b.name for b in U.armadura().data.bones}
tot = np.array([sum(g.weight for g in v.groups if nomes[g.group] in ossos) for v in me.vertices])
sem = np.zeros(n, bool)
for r in set(raiz):
    idx = np.where(raiz == r)[0]
    if (tot[idx] < 0.5).mean() > 0.5:
        sem[idx] = True
# material por face: 0 = cinza, 1 = vermelho (sem peso)
def mat(nome, cor):
    m = bpy.data.materials.new(nome)
    m.use_nodes = False
    m.diffuse_color = cor
    return m
me2 = me.copy()
me2.materials.clear()
me2.materials.append(mat("cinza", (0.55, 0.55, 0.6, 1)))
me2.materials.append(mat("vermelho", (1.0, 0.1, 0.1, 1)))
for p in me2.polygons:
    p.material_index = 1 if sem[p.vertices[0]] else 0
o2 = bpy.data.objects.new("destaque", me2)
o2.matrix_world = corpo.matrix_world.copy()
bpy.context.scene.collection.objects.link(o2)
for o in bpy.data.objects:
    if o.type == "MESH":
        o.hide_render = o.name != "destaque"
cam, cd = U.camera_render(900, 900, 1.0)
bpy.context.scene.display.shading.color_type = "MATERIAL"
alvo = (0.0, 0.0, 1.85)
for v, d in {"frente": (0, -1, 0), "topo": (0, -0.05, 1), "34": (-0.62, -0.78, 0.3)}.items():
    U.foto(cam, cd, pref + "_" + v + ".png", alvo, d, 1.6)
print("ok", int(sem.sum()))
