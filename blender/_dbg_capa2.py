"""Pesos por ilha da capa/cinto (somente leitura) no arquivo original do usuario."""
import bpy, numpy as np
capa = bpy.data.objects["capa"]
me = capa.data
n = len(me.vertices)
pai = list(range(n))
def achar(a):
    while pai[a] != a:
        pai[a] = pai[pai[a]]; a = pai[a]
    return a
for p in me.polygons:
    vs = list(p.vertices)
    r0 = achar(vs[0])
    for x in vs[1:]:
        pai[achar(x)] = r0
raiz = np.array([achar(i) for i in range(n)])
co = np.empty(n * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
m = np.array(capa.matrix_world); wco = co @ m[:3, :3].T + m[:3, 3]
nomes = {vg.index: vg.name for vg in capa.vertex_groups}
def pesos(i):
    return {nomes[g.group]: g.weight for g in me.vertices[i].groups if g.weight > 1e-4}
ilhas = {}
for r in set(raiz):
    ilhas[r] = np.where(raiz == r)[0]
for r, idx in sorted(ilhas.items(), key=lambda kv: wco[kv[1]][:, 2].max(), reverse=True):
    ps = [pesos(i) for i in idx]
    sem = sum(1 for p in ps if not p)
    tot = {}
    for p in ps:
        for k, v in p.items():
            tot.setdefault(k, []).append(v)
    soma = [sum(p.values()) for p in ps]
    fix = sum(1 for p in ps if "capa_fixacao" in p)
    print("ilha %5d n=%4d zmax %.2f  sem_peso=%3d  na_fixacao=%3d  soma_media=%.2f  grupos %s" % (r, len(idx), wco[idx][:, 2].max(), sem, fix, np.mean(soma),
          {k: (len(v), round(float(np.mean(v)), 2)) for k, v in tot.items() if k != "capa_fixacao"}))
