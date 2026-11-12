"""Analisa os vertices sem peso do corpo do usuario: ilhas conectadas, onde ficam e quem sao os vizinhos ponderados.
So le. Uso: blender -b <modelo.blend> --python analisar_pesos_usuario.py -- <saida.txt>"""
import sys

import bpy
import numpy as np

saida = sys.argv[sys.argv.index("--") + 1]
L = []


def p(*a):
    L.append(" ".join(str(x) for x in a))


corpo = bpy.data.objects["NeoMetal"]
me = corpo.data
nv = len(me.vertices)
mw = corpo.matrix_world
co = np.array([(mw @ v.co)[:] for v in me.vertices])

peso_total = np.zeros(nv)
dom = [None] * nv
for v in me.vertices:
    s = 0.0
    melhor = (0.0, None)
    for ge in v.groups:
        if ge.weight > 1e-4:
            s += ge.weight
            if ge.weight > melhor[0]:
                melhor = (ge.weight, corpo.vertex_groups[ge.group].name)
    peso_total[v.index] = s
    dom[v.index] = melhor[1]

# ilhas por arestas
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
p("ilhas:", len(ids), "verts:", nv)
sem = peso_total < 1e-4
p("sem peso:", int(sem.sum()))
linhas = []
for i in ids:
    m = ilha == i
    n = int(m.sum())
    ns = int((m & sem).sum())
    if ns == 0:
        continue
    pts = co[m]
    doms = {}
    for k in np.where(m & ~sem)[0]:
        doms[dom[k]] = doms.get(dom[k], 0) + 1
    top = sorted(doms.items(), key=lambda kv: -kv[1])[:3]
    linhas.append((ns, n, pts.min(axis=0), pts.max(axis=0), top))
linhas.sort(key=lambda t: -t[0])
p("ilhas com vertices sem peso:", len(linhas))
for ns, n, lo, hi, top in linhas[:60]:
    p("  sem=%4d/%4d  bbox x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f  dominantes %s" % (ns, n, lo[0], hi[0], lo[1], hi[1], lo[2], hi[2], top))

soma_baixa = (peso_total > 1e-4) & (peso_total < 0.99)
p("pesos com soma<0.99 (mas >0):", int(soma_baixa.sum()), "min soma", float(peso_total[soma_baixa].min()) if soma_baixa.any() else None)

# vertices dos dedos esquerdos/direitos com influencia de ossos que nao sao da mao
p("")
p("== vertices cujo grupo dominante e um dedo mas que ficam longe do centro do dedo (possivel vazamento) ==")
nomes = [vg.name for vg in corpo.vertex_groups]
open(saida, "w", encoding="utf-8").write("\n".join(L))
print("\n".join(L))
