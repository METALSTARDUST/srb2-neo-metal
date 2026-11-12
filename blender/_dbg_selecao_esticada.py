import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
import braco_poses as BP
import usuario_neo as U
U.preparar()
BP.zerar()
for lado in U.LADOS:
    BP.fechar_mao(lado)
BP.zerar()
BP.preparar_esticar()
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
co = BP._coords(corpo)
nomes = {vg.index: vg.name for vg in corpo.vertex_groups}
for lado in U.LADOS:
    sel, h = BP.ESTICA[lado]
    print("=== lado", lado, "selecionados", len(sel))
    por_ilha = {}
    for i, hh in zip(sel, h):
        por_ilha.setdefault(raiz[i], []).append((i, hh))
    for r, lst in sorted(por_ilha.items(), key=lambda kv: -len(kv[1])):
        idx = np.array([i for i, _ in lst])
        tam = int((raiz == r).sum())
        grp = {}
        for i in idx[:50]:
            v = me.vertices[i]
            for g in v.groups:
                if g.weight > 0.3:
                    grp[nomes[g.group]] = grp.get(nomes[g.group], 0) + 1
        top = sorted(grp.items(), key=lambda kv: -kv[1])[:3]
        print("ilha de %4d vertices (selecionados %4d), caixa min %s max %s, grupos %s" % (tam, len(idx), co[idx].min(axis=0).round(2), co[idx].max(axis=0).round(2), top))
