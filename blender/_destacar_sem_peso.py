"""Debug: pinta de cores diferentes as ilhas sem peso do corpo do usuario e fotografa (frente, 3/4, costas, lado).
Uso: blender -b <modelo.blend> --python _destacar_sem_peso.py -- <saida_dir>"""
import colorsys
import os
import sys

import bmesh
import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import usuario_neo as U

saida = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
os.makedirs(saida, exist_ok=True)
U.preparar(tecido=False)
bpy.data.objects["capa"].hide_render = True
U.repouso()

corpo = bpy.data.objects["NeoMetal"]
me = corpo.data
nv = len(me.vertices)
sem = np.array([not any(ge.weight > 1e-4 for ge in v.groups) for v in me.vertices])
pai = list(range(nv))


def achar(a):
    while pai[a] != a:
        pai[a] = pai[pai[a]]
        a = pai[a]
    return a


for e in me.edges:
    a, b = achar(e.vertices[0]), achar(e.vertices[1])
    if a != b:
        pai[a] = b
ilha = np.array([achar(i) for i in range(nv)])
ids = [i for i in np.unique(ilha) if sem[ilha == i].all()]
print("ilhas sem peso:", len(ids))

# copia do corpo so com as ilhas sem peso, cada uma com um material de cor diferente
bm = bmesh.new()
bm.from_mesh(me)
bm.verts.ensure_lookup_table()
bm.faces.ensure_lookup_table()
cores = {}
for k, i in enumerate(ids):
    h = (k * 0.618034) % 1.0
    cores[i] = colorsys.hsv_to_rgb(h, 0.95, 1.0)
mats = []
for k, i in enumerate(ids):
    m = bpy.data.materials.new("sem_%d" % k)
    m.use_nodes = False
    m.diffuse_color = (*cores[i], 1.0)
    mats.append(m)
idx_mat = {i: k for k, i in enumerate(ids)}
manter = []
for f in bm.faces:
    v0 = f.verts[0].index
    if sem[v0] and ilha[v0] in idx_mat and all(sem[v.index] for v in f.verts):
        f.material_index = idx_mat[ilha[v0]]
        manter.append(f)
apagar = [f for f in bm.faces if f not in manter]
bmesh.ops.delete(bm, geom=apagar, context="FACES")
nm = bpy.data.meshes.new("so_sem_peso")
bm.to_mesh(nm)
bm.free()
for m in mats:
    nm.materials.append(m)
obj = bpy.data.objects.new("so_sem_peso", nm)
obj.matrix_world = corpo.matrix_world
bpy.context.scene.collection.objects.link(obj)
corpo.hide_render = True  # o corpo original aparece como fantasma pela copia abaixo
fant = corpo.copy()
fant.data = corpo.data.copy()
bpy.context.scene.collection.objects.link(fant)
fant.hide_render = False
fant.hide_viewport = False
for m in list(fant.modifiers):
    fant.modifiers.remove(m)
mat_f = bpy.data.materials.new("fantasma")
mat_f.use_nodes = False
mat_f.diffuse_color = (0.8, 0.8, 0.85, 1.0)
fant.data.materials.clear()
fant.data.materials.append(mat_f)
for pg in fant.data.polygons:
    pg.material_index = 0

lo, hi = U.caixa_mundo(("NeoMetal",)) if False else (np.array([-1.9, -1, 0]), np.array([1.8, 1.6, 3.6]))
cen = (lo + hi) / 2
escala = 4.2
cam, cd = U.camera_render(900, 900, exposicao=0.0)
bpy.context.scene.display.shading.color_type = "MATERIAL"
alvo = (float(cen[0]), float(cen[1]), float(cen[2]))
for nome, d in {"frente": (0, -1, 0.12), "tres_quartos": (-0.62, -0.78, 0.30), "costas": (0, 1, 0.12), "lado": (-1, 0, 0.12)}.items():
    U.foto(cam, cd, os.path.join(saida, "sem_peso_%s.png" % nome), alvo, d, escala)
print("ok")
