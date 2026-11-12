import bpy, numpy as np
for nome in ("NeoMetal", "capa"):
    o = bpy.data.objects[nome]
    me = o.data
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
    co = np.empty(n * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    m = np.array(o.matrix_world)
    mundo = co @ m[:3, :3].T + m[:3, 3]
    usados = set()
    for p in me.polygons:
        usados.update(p.vertices)
    soltos = [i for i in range(n) if i not in usados]
    print(nome, "vertices", n, "soltos (sem face):", len(soltos))
    for i in soltos[:10]:
        print("  solto", i, mundo[i].round(3))
    for r in sorted(set(raiz), key=lambda r: (raiz == r).sum()):
        idx = np.where(raiz == r)[0]
        if len(idx) < 40 and len(idx) > 0:
            print("  ilha pequena: %d vertices, centro %s" % (len(idx), mundo[idx].mean(axis=0).round(3)))
