"""Monta o Neo Metal Sonic com esqueleto no Blender a partir de neo_repouso.json (exportar_neo_blender.py).
Uso: blender -b --python montar_neo_blend.py -- <pasta com neo_repouso.json e NEO_METAL.png> <saida.blend>
Eixos: o JSON esta nas coordenadas do MD3 do jogo; aqui viram (y, -x, z) * 0,1, com o personagem de frente na vista Front (Numpad 1), como o padrao do Blender."""
import json
import math
import os
import sys

import bpy
from mathutils import Vector

ESC = 0.1
pasta, saida = sys.argv[sys.argv.index("--") + 1:][:2]
D = json.load(open(os.path.join(pasta, "neo_repouso.json")))
bpy.ops.wm.read_factory_settings(use_empty=True)


def B(p):
    return Vector((p[1] * ESC, -p[0] * ESC, p[2] * ESC))


V = [B(p) for p in D["vertices"]]
J = {k: B(v) for k, v in D["juntas"].items()}
malha = bpy.data.meshes.new("NeoMetal")
malha.from_pydata(V, [], [tuple(t) for t in D["tris"]])
malha.update()
uv = malha.uv_layers.new(name="UV")
for lp in malha.loops:
    s, t = D["st"][lp.vertex_index]
    uv.data[lp.index].uv = (s, 1.0 - t)
for p in malha.polygons:
    p.use_smooth = True
obj = bpy.data.objects.new("NeoMetal", malha)
bpy.context.scene.collection.objects.link(obj)
mat = bpy.data.materials.new("NeoMetal")
mat.use_nodes = True
img = bpy.data.images.load(os.path.abspath(os.path.join(pasta, "NEO_METAL.png")))
img.pack()
no = mat.node_tree.nodes.new("ShaderNodeTexImage")
no.image = img
no.interpolation = "Closest"
mat.node_tree.links.new(no.outputs["Color"], mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
malha.materials.append(mat)

# --- esqueleto ---
parte, lado = D["parte"], D["lado"]
foot_idx = {s: [i for i in range(len(V)) if parte[i] == "foot" and lado[i] == s] for s in (1.0, -1.0)}
cape_idx = [i for i in range(len(V)) if parte[i] == "cape"]
z_topo = max(V[i].z for i in cape_idx)
z_base = min(V[i].z for i in cape_idx)
arm_data = bpy.data.armatures.new("NeoMetal_rig")
arm = bpy.data.objects.new("NeoMetal_rig", arm_data)
bpy.context.scene.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="EDIT")
eb = arm_data.edit_bones
ossos = {}


def osso(nome, cab, cau, pai=None):
    b = eb.new(nome)
    b.head, b.tail = cab, cau
    if pai:
        b.parent = ossos[pai]
    ossos[nome] = b
    return b


up = Vector((0, 0, 0.2))
osso("corpo", J["CINTURA"], J["CINTURA"] + Vector((0, 0, 0.35)))
osso("peito", J["CINTURA"] + Vector((0, 0, 0.35)), J["HEAD"], "corpo")
osso("cabeca", J["HEAD"], J["HEAD"] + Vector((0, 0, 0.55)), "peito")
for s, suf in ((1.0, ".R"), (-1.0, ".L")):
    S, E, W, H, K, A = (J["%s%s" % (n, suf)] for n in "SEWHKA")
    osso("braco_sup" + suf, S, E, "peito")
    osso("antebraco" + suf, E, W, "braco_sup" + suf)
    osso("mao" + suf, W, W + (W - E).normalized() * 0.5, "antebraco" + suf)
    osso("coxa" + suf, H, K, "corpo")
    osso("canela" + suf, K, A, "coxa" + suf)
    pf = foot_idx[s]
    ponta = min(V[i].y for i in pf)                  # a frente do personagem e -Y
    osso("pe" + suf, A, Vector((A.x, ponta, A.z * 0.55)), "canela" + suf)
NB = 3
alturas = [z_topo - (z_topo - z_base) * k / NB for k in range(NB + 1)]
xc = sum(V[i].y for i in cape_idx) / len(cape_idx)
for k in range(NB):
    osso("capa%d" % (k + 1), Vector((0, xc, alturas[k])), Vector((0, xc, alturas[k + 1])), "corpo" if k == 0 else "capa%d" % k)
bpy.ops.object.mode_set(mode="OBJECT")

# --- pesos: cada peca e rigida em um osso (a capa tem degrade em 3 ossos) ---
OSSO_DA_PARTE = {"head": "cabeca", "torso": "peito", "belt": "corpo", "sleeve": "braco_sup", "uarm": "braco_sup", "farm": "antebraco", "hand": "mao",
                 "thigh": "coxa", "shin": "canela", "foot": "pe"}
grupos = {n: obj.vertex_groups.new(name=n) for n in ossos}
for i in range(len(V)):
    p, s = parte[i], lado[i]
    if p == "cape":
        t = (z_topo - V[i].z) / max(1e-6, z_topo - z_base) * NB
        pes = [max(0.0, 1.0 - abs(t - (k + 0.5))) for k in range(NB)]
        tot = sum(pes) or 1.0
        for k in range(NB):
            if pes[k] > 0:
                grupos["capa%d" % (k + 1)].add([i], pes[k] / tot, "REPLACE")
        continue
    nome = OSSO_DA_PARTE.get(p, "peito")
    if nome in ("braco_sup", "antebraco", "mao", "coxa", "canela", "pe"):
        if s == 0.0:
            nome = "peito"
        else:
            nome += ".R" if s > 0 else ".L"
    grupos[nome].add([i], 1.0, "REPLACE")
mod = obj.modifiers.new("Armature", "ARMATURE")
mod.object = arm
obj.parent = arm
arm.show_in_front = True
arm_data.display_type = "OCTAHEDRAL"
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, 24
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(saida))
print("ok:", len(ossos), "ossos,", len(V), "vertices")
