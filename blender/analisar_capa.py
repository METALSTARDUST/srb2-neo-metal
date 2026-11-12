"""Mede a capa (tecido + cinto) do neo_base_pose.blend: componentes ligados, caixa, centro, raio em torno do eixo vertical, pesos. So leitura."""
import bpy
import numpy as np

capa, corpo = bpy.data.objects["capa"], bpy.data.objects["NeoMetal"]
print("capa: vertices", len(capa.data.vertices), "poligonos", len(capa.data.polygons), "modificadores", [(m.type, m.name) for m in capa.modifiers])
print("capa matrix_world\n", np.array(capa.matrix_world).round(3))
print("grupos de vertices da capa:", [g.name for g in capa.vertex_groups])
mw = np.array(capa.matrix_world)
co = np.empty(len(capa.data.vertices) * 3)
capa.data.vertices.foreach_get("co", co)
co = co.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]

# componentes ligados por aresta
n = len(co)
pai = list(range(n))


def achar(a):
    while pai[a] != a:
        pai[a] = pai[pai[a]]
        a = pai[a]
    return a


for p in capa.data.polygons:
    vs = list(p.vertices)
    for v in vs[1:]:
        ra, rb = achar(vs[0]), achar(v)
        if ra != rb:
            pai[rb] = ra
raiz = np.array([achar(i) for i in range(n)])
comps = {}
for i, r in enumerate(raiz):
    comps.setdefault(r, []).append(i)
tri_por_comp = {}
for p in capa.data.polygons:
    tri_por_comp[achar(p.vertices[0])] = tri_por_comp.get(achar(p.vertices[0]), 0) + len(p.vertices) - 2
ordem = sorted(comps.items(), key=lambda kv: -len(kv[1]))
print("componentes:", len(ordem))
for k, (r, vs) in enumerate(ordem[:30]):
    c = co[vs]
    print("  #%d vertices %d triangulos %d  caixa min %s max %s  centro %s" % (k, len(vs), tri_por_comp.get(r, 0), c.min(axis=0).round(3), c.max(axis=0).round(3), c.mean(axis=0).round(3)))

pano = ordem[0][1]
cinto = [i for r, vs in ordem[1:] for i in vs]
cp, cc = co[pano], co[cinto]
eixo = np.array([cc[:, 0].mean(), cc[:, 1].mean()])
print("tecido: vertices", len(pano), "z %.3f..%.3f" % (cp[:, 2].min(), cp[:, 2].max()))
print("cinto: vertices", len(cinto), "z %.3f..%.3f  centro xy %s" % (cc[:, 2].min(), cc[:, 2].max(), eixo.round(3)))
rt = np.linalg.norm(cp[:, :2] - eixo, axis=1)
rc = np.linalg.norm(cc[:, :2] - eixo, axis=1)
print("raio do tecido em torno do eixo do cinto: min %.3f max %.3f; no topo (z>max-0.05): %.3f" % (rt.min(), rt.max(), rt[cp[:, 2] > cp[:, 2].max() - 0.05].mean()))
print("raio do cinto: min %.3f max %.3f media %.3f" % (rc.min(), rc.max(), rc.mean()))
for z0 in np.linspace(cp[:, 2].min(), cp[:, 2].max(), 7):
    sel = np.abs(cp[:, 2] - z0) < 0.05
    if sel.any():
        print("   tecido z %.2f: raio medio %.3f (n=%d)" % (z0, rt[sel].mean(), sel.sum()))

# largura do corpo na altura do cinto
mwc = np.array(corpo.matrix_world)
cb = np.empty(len(corpo.data.vertices) * 3)
corpo.data.vertices.foreach_get("co", cb)
cb = cb.reshape(-1, 3) @ mwc[:3, :3].T + mwc[:3, 3]
zc = cc[:, 2]
sel = (cb[:, 2] > zc.min() - 0.05) & (cb[:, 2] < zc.max() + 0.05)
print("corpo na altura do cinto (z %.2f..%.2f): vertices %d  x %.3f..%.3f  y %.3f..%.3f" % (zc.min(), zc.max(), sel.sum(), cb[sel, 0].min(), cb[sel, 0].max(), cb[sel, 1].min(), cb[sel, 1].max()))
rb = np.linalg.norm(cb[sel][:, :2] - eixo, axis=1)
print("   raio do corpo nessa altura: media %.3f max %.3f" % (rb.mean(), rb.max()))
# pesos
gnomes = {g.index: g.name for g in capa.vertex_groups}
tot = {}
for v in capa.data.vertices:
    for g in v.groups:
        tot[gnomes[g.group]] = tot.get(gnomes[g.group], 0.0) + g.weight
print("peso total por grupo (capa):", sorted(((round(w, 1), n_) for n_, w in tot.items()), reverse=True)[:8])
