"""Tabela por superficie do XSONIC.md3 nos quadros do soco (Super 277-280, normal 141-144)."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import golpes_ref as G

q, sup = G.ler()
print("quadros", len(q), "superficies", len(sup))
for i, s in enumerate(sup):
    print("s%02d nv=%4d nt=%4d nome=%s" % (i, s["pos"].shape[1], len(s["tris"]), s["nome"]))
for grupo in ([277, 278, 279, 280], [141, 142, 143, 144]):
    for f in grupo:
        mv = G.mascara_visivel(sup, f)
        print("\nquadro", f, q[f])
        lin = []
        for i, (s, m) in enumerate(zip(sup, mv)):
            n = int(m.sum())
            if n:
                p = s["pos"][f][m]
                c = p.mean(axis=0)
                mn, mx = p.min(axis=0), p.max(axis=0)
                lin.append("s%02d vis=%4d c=(%6.2f %6.2f %6.2f) ext=(%5.2f %5.2f %5.2f)" % (i, n, c[0], c[1], c[2], *(mx - mn)))
        print("\n".join(lin))
