import bpy, numpy as np
o = bpy.data.objects["NeoMetal"]
me = o.data
n = len(me.vertices)
nomes = {vg.index: vg.name for vg in o.vertex_groups}
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
co = np.empty(n * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
m = np.array(o.matrix_world)
mundo = co @ m[:3, :3].T + m[:3, 3]
osso = set(b.name for b in bpy.data.objects["Armação"].data.bones)
tot = np.zeros(n)
for i, v in enumerate(me.vertices):
    tot[i] = sum(g.weight for g in v.groups if nomes[g.group] in osso)
print("vertices com peso de osso < 0.5:", int((tot < 0.5).sum()))
for r in set(raiz):
    idx = np.where(raiz == r)[0]
    fr = float((tot[idx] < 0.5).mean())
    if fr > 0.2:
        print("ilha %d vertices, %.0f%% sem peso, centro %s, caixa min %s max %s" % (len(idx), fr * 100, mundo[idx].mean(axis=0).round(3), mundo[idx].min(axis=0).round(3), mundo[idx].max(axis=0).round(3)))
