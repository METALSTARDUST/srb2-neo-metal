"""Mede um espinho da cabeca do Neo (so le; nao grava nada): acha as ilhas da malha que aparecem numa caixa do render, diz a que ossos elas estao pesadas e compara o formato
em repouso com o da pose do quadro.
Uso: blender -b <pasta>/cena_<quadros>.blend --python analisar_espinho.py -- <metricas.json> <quadro> <u0,v0,u1,v1 caixa no render> [<vista lado|34>]
A caixa esta em pixels do render (TAM x TAM, origem no canto superior esquerdo). Projecao ortografica igual a de usuario_neo.foto."""
import json
import sys

import bpy
import numpy as np
from mathutils import Vector

arg = sys.argv[sys.argv.index("--") + 1:]
met = json.load(open(arg[0]))
q = arg[1]
u0, v0, u1, v1 = [float(x) for x in arg[2].split(",")]
vista = arg[3] if len(arg) > 3 else "lado"
VISTAS = {"lado": np.array([-1.0, 0.0, 0.0]), "34": np.array([-0.62, -0.78, 0.18])}
TAM = 560

centro = np.array(met["centros"][q])
esc = met["escala_render"]
d = VISTAS[vista] / np.linalg.norm(VISTAS[vista])
frente = -d
direita = np.cross(frente, [0.0, 0.0, 1.0])
direita /= np.linalg.norm(direita)
cima = np.cross(direita, frente)
cima /= np.linalg.norm(cima)


def projetar(p):
    r = p - centro
    return np.stack([TAM / 2 + (r @ direita) / esc * TAM, TAM / 2 - (r @ cima) / esc * TAM, r @ d], axis=1)


def mundo(obj):
    me = obj.data
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    mw = np.array(obj.matrix_world)
    return co.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]


pose = bpy.data.objects["NeoPose_%s" % q]
base = bpy.data.objects["NeoMetal"]
n = len(base.data.vertices)
assert len(pose.data.vertices) == n, (len(pose.data.vertices), n)
P_pose = mundo(pose)
P_rep = mundo(base)

nomes = {g.index: g.name for g in base.vertex_groups}
pesos = [[(nomes[g.group], g.weight) for g in v.groups] for v in base.data.vertices]

# ilhas da malha do corpo
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
ilhas = {r: np.flatnonzero(raiz == r) for r in np.unique(raiz)}

uv = projetar(P_pose)
dentro = (uv[:, 0] >= u0) & (uv[:, 0] <= u1) & (uv[:, 1] >= v0) & (uv[:, 1] <= v1)
print("quadro %s vista %s: %d vertices na caixa (%.0f,%.0f)-(%.0f,%.0f); %d ilhas no corpo" % (q, vista, dentro.sum(), u0, v0, u1, v1, len(ilhas)))


def dominante(idx):
    soma = {}
    for i in idx:
        for nome, w in pesos[i]:
            soma[nome] = soma.get(nome, 0.0) + w
    tot = sum(soma.values()) or 1.0
    return sorted(((k, v / tot) for k, v in soma.items()), key=lambda t: -t[1])[:4]


vistas_ilha = {}
for i in np.flatnonzero(dentro):
    vistas_ilha.setdefault(raiz[i], []).append(i)
print("ilhas tocadas pela caixa (vertices na caixa / total da ilha):")
for r, dentro_idx in sorted(vistas_ilha.items(), key=lambda t: -len(t[1])):
    ilha = ilhas[r]
    caixa_rep = (P_rep[ilha].min(axis=0).round(3), P_rep[ilha].max(axis=0).round(3))
    print("  ilha %d: %d na caixa / %d; profundidade na vista %.2f..%.2f; pesos %s" % (
        r, len(dentro_idx), len(ilha), uv[ilha, 2].min(), uv[ilha, 2].max(), [(k, round(v, 2)) for k, v in dominante(ilha)]))
    print("     caixa em repouso (mundo) %s .. %s" % (caixa_rep[0], caixa_rep[1]))
    print("     projecao na pose: u %.0f..%.0f  v %.0f..%.0f" % (uv[ilha, 0].min(), uv[ilha, 0].max(), uv[ilha, 1].min(), uv[ilha, 1].max()))
