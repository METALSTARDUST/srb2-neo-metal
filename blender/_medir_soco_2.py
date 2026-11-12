"""Ilhas topologicas de cada superficie do XSONIC.md3 e como cada ilha aparece nos quadros do soco."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import golpes_ref as G


def componentes(nv, tris):
    pai = np.arange(nv)

    def achar(a):
        while pai[a] != a:
            pai[a] = pai[pai[a]]
            a = pai[a]
        return a
    for a, b, c in tris:
        ra, rb, rc = achar(a), achar(b), achar(c)
        pai[rb] = ra
        pai[achar(rc)] = ra
    raiz = np.array([achar(i) for i in range(nv)])
    _, rot = np.unique(raiz, return_inverse=True)
    return rot


q, sup = G.ler()
quadros = [277, 278, 279, 280]
mv = {f: G.mascara_visivel(sup, f) for f in quadros}
for i in (0, 27, 31, 32, 1):
    s = sup[i]
    rot = componentes(s["pos"].shape[1], s["tris"])
    n = rot.max() + 1
    print("\nsuperficie s%02d: %d ilhas topologicas" % (i, n))
    for k in range(n):
        idx = np.where(rot == k)[0]
        lin = ["ilha %3d nv=%4d" % (k, len(idx))]
        vis_algum = False
        for f in quadros:
            m = mv[f][i][idx]
            if m.sum() >= 5:
                p = s["pos"][f][idx][m]
                c = p.mean(axis=0)
                e = p.max(axis=0) - p.min(axis=0)
                lin.append("| %d vis=%4d c=(%5.2f %5.2f %5.2f) e=(%4.2f %4.2f %4.2f)" % (f, m.sum(), c[0], c[1], c[2], *e))
                vis_algum = True
        if vis_algum:
            print(" ".join(lin))
