import bpy, numpy as np
def ilhas(me):
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
    return np.array([achar(i) for i in range(n)])
def mundo(o):
    me = o.data
    n = len(me.vertices)
    co = np.empty(n * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    m = np.array(o.matrix_world)
    return co @ m[:3, :3].T + m[:3, 3]
base = bpy.data.objects["NeoMetal"]
raiz = ilhas(base.data)
for nome in ("NeoMetal", "NeoPose_219", "NeoPose_279"):
    o = bpy.data.objects.get(nome)
    if o is None:
        continue
    p = mundo(o)
    print("==", nome)
    for r in set(raiz):
        idx = np.where(raiz == r)[0]
        if len(idx) > 60:
            continue
        resto = np.ones(len(p), bool); resto[idx] = False
        c = p[idx].mean(axis=0)
        d = np.linalg.norm(p[resto] - c, axis=1).min()
        if d > 0.25:
            print("  flutuante: %d vertices centro %s distancia minima ao resto %.2f" % (len(idx), c.round(2), d))
