"""Lista as ilhas (pecas conectadas) do corpo do usuario com a distribuicao de pesos por osso.
Serve para achar pecas rigidas que vazaram peso para ossos vizinhos. So le.
Uso: blender -b <modelo.blend> --python analisar_ilhas_usuario.py -- <saida.txt> [min_verts]"""
import sys

import bpy
import numpy as np

arg = sys.argv[sys.argv.index("--") + 1:]
saida = arg[0]
min_v = int(arg[1]) if len(arg) > 1 else 12
L = []


def p(*a):
    L.append(" ".join(str(x) for x in a))


corpo = bpy.data.objects["NeoMetal"]
me = corpo.data
nv = len(me.vertices)
mw = corpo.matrix_world
co = np.array([(mw @ v.co)[:] for v in me.vertices])
nomes = [vg.name.strip() for vg in corpo.vertex_groups]

W = np.zeros((nv, len(nomes)))
for v in me.vertices:
    for ge in v.groups:
        W[v.index, ge.group] = ge.weight

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
ids = np.unique(ilha)
dados = []
for i in ids:
    m = ilha == i
    n = int(m.sum())
    if n < min_v:
        continue
    soma = W[m].sum(axis=0)
    tot = soma.sum()
    ordem = np.argsort(-soma)[:4]
    pureza = soma[ordem[0]] / tot if tot > 0 else 0
    pts = co[m]
    dados.append((n, pts.min(axis=0), pts.max(axis=0), pureza, [(nomes[k], round(float(soma[k] / n), 2)) for k in ordem if soma[k] > 0]))
dados.sort(key=lambda t: (-t[0]))
p("ilhas com >= %d verts: %d (de %d)" % (min_v, len(dados), len(ids)))
for n, lo, hi, pur, top in dados:
    p("n=%4d pureza=%.2f bbox x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f  %s" % (n, pur, lo[0], hi[0], lo[1], hi[1], lo[2], hi[2], top))
open(saida, "w", encoding="utf-8").write("\n".join(L))
