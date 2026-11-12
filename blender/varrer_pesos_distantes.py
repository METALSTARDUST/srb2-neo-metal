"""Varre o corpo do Neo atras de vertices com peso (> limite) num osso que fica LONGE dele em repouso (so le; nao grava nada): o peso que prende uma peca a um osso distante a faz
esticar ou entortar quando esse osso se mexe. Agrupa por ilha da malha e por osso.
Uso: blender -b <arquivo>.blend --python varrer_pesos_distantes.py -- [<peso minimo, padrao 0.02>] [<distancia minima ao osso em m, padrao 0.6>]"""
import sys

import bpy
import numpy as np

arg = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
PESO_MIN = float(arg[0]) if arg else 0.02
DIST_MIN = float(arg[1]) if len(arg) > 1 else 0.6

obj = bpy.data.objects["NeoMetal"]
arm = bpy.data.objects["Armação"]
me = obj.data
n = len(me.vertices)
nomes = {vg.index: vg.name for vg in obj.vertex_groups}
ossos = {}
M = np.array(arm.matrix_world)
for b in arm.data.bones:
    cab = M[:3, :3] @ np.array(b.head_local) + M[:3, 3]
    cau = M[:3, :3] @ np.array(b.tail_local) + M[:3, 3]
    ossos[b.name] = (cab, cau)

co = np.empty(n * 3)
me.vertices.foreach_get("co", co)
mw = np.array(obj.matrix_world)
mundo = co.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]

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


def dist_segmento(p, a, b):
    ab = b - a
    t = np.clip(((p - a) @ ab) / max(ab @ ab, 1e-12), 0.0, 1.0)
    return np.linalg.norm(p - (a + t * ab))


achados = {}
for i, v in enumerate(me.vertices):
    for g in v.groups:
        nome = nomes[g.group]
        if g.weight < PESO_MIN or nome not in ossos:
            continue
        d = dist_segmento(mundo[i], *ossos[nome])
        if d >= DIST_MIN:
            achados.setdefault((int(raiz[i]), nome), []).append((i, g.weight, d))

print("vertices com peso >= %.2f num osso a >= %.2f m (repouso): %d pares ilha/osso" % (PESO_MIN, DIST_MIN, len(achados)))
for (r, nome), lista in sorted(achados.items(), key=lambda t: -max(w * d for _, w, d in t[1])):
    idx = np.flatnonzero(raiz == r)
    pesos = [w for _, w, _ in lista]
    dist = [d for _, _, d in lista]
    print("  ilha %5d (%4d vertices, centro %s) osso '%s': %d vertices, peso %.3f..%.3f, distancia ao osso %.2f..%.2f m" % (
        r, len(idx), mundo[idx].mean(axis=0).round(2), nome, len(lista), min(pesos), max(pesos), min(dist), max(dist)))
