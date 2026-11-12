"""Lista os pesos de osso de cada vertice de algumas ilhas do corpo do Neo e procura espinhos da cabeca contaminados por outros ossos (so le; nao grava nada).
Uso: blender -b <arquivo>.blend --python analisar_espinho_pesos.py -- [<raiz da ilha>,<raiz>,... para listar vertice a vertice]
Sem argumento lista so o resumo. 'raiz' e o indice de vertice que o union-find da malha devolve para a ilha (o mesmo de analisar_espinho.py)."""
import sys

import bpy
import numpy as np

arg = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
detalhar = [int(x) for x in arg[0].split(",")] if arg else []
CABECA = "head (cabeça)"

obj = bpy.data.objects["NeoMetal"]
me = obj.data
n = len(me.vertices)
nomes = {vg.index: vg.name for vg in obj.vertex_groups}
pai = list(range(n))


def achar(a):
    while pai[a] != a:
        pai[a] = pai[pai[a]]
        a = pai[a]
    return a


for p in me.polygons:
    vs = list(p.vertices)
    for v in vs[1:]:
        ra, rb = achar(vs[0]), achar(v)
        if ra != rb:
            pai[rb] = ra
raiz = np.array([achar(i) for i in range(n)])
co = np.empty(n * 3)
me.vertices.foreach_get("co", co)
mw = np.array(obj.matrix_world)
mundo = co.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]
pesos = [{nomes[g.group]: g.weight for g in v.groups if g.weight > 1e-4} for v in me.vertices]

print("malha %s: %d vertices, %d grupos" % (obj.name, n, len(nomes)))
print("ilhas de ate 40 vertices com peso na cabeca e algum vertice com peso (>0,01) em outro osso:")
for r in np.unique(raiz):
    idx = np.flatnonzero(raiz == r)
    if len(idx) > 40:
        continue
    soma_cabeca = sum(pesos[i].get(CABECA, 0.0) for i in idx)
    if soma_cabeca < 0.5 * len(idx):
        continue
    sujos = [(int(i), {k: round(v, 3) for k, v in pesos[i].items() if k != CABECA and v > 0.01}) for i in idx]
    sujos = [(i, w) for i, w in sujos if w]
    if sujos:
        print("  ilha %d (%d vertices, centro %s): %d vertices com outros ossos: %s" % (
            r, len(idx), mundo[idx].mean(axis=0).round(2), len(sujos), sujos[:6]))
for r in detalhar:
    idx = np.flatnonzero(raiz == r)
    print("ilha %d: %d vertices" % (r, len(idx)))
    for i in idx:
        print("   v%-5d %s  %s" % (i, mundo[i].round(3), {k: round(v, 3) for k, v in sorted(pesos[i].items(), key=lambda t: -t[1])}))
