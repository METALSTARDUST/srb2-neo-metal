"""(Python do Blender, numpy) Tabela das ilhas visiveis do XSONIC.md3 em varios quadros: por superficie e ilha, quantos vertices aparecem, o centro e a extensao (x y z) em cada quadro.
Serve para achar, num golpe novo, quais pecas formam o pe que chuta, a perna e os rastros (as pecas extras so aparecem em alguns quadros).
Uso: python tabela_ilhas.py <saida.txt> <quadro> [<quadro> ...]"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

import golpes_ref as G

saida = sys.argv[1]
quadros = [int(x) for x in sys.argv[2:]]
q_nomes, sup = G.ler()
vis = {f: G.mascara_visivel(sup, f) for f in quadros}
linhas = []
for i, s in enumerate(sup):
    rot = G.componentes(s["pos"].shape[1], s["tris"])
    ilhas = np.unique(rot)
    linhas.append("")
    linhas.append("superficie s%02d: %d vertices, %d ilhas topologicas" % (i, s["pos"].shape[1], len(ilhas)))
    for k in ilhas:
        m = rot == k
        partes = []
        for f in quadros:
            mv = m & vis[f][i]
            if mv.sum() == 0:
                continue
            p = s["pos"][f][mv]
            c, e = p.mean(0), p.max(0) - p.min(0)
            partes.append("%d vis=%3d c=(%5.2f %5.2f %5.2f) e=(%4.2f %4.2f %4.2f)" % (f, mv.sum(), *c, *e))
        if partes:
            linhas.append("ilha %3d nv=%4d | %s" % (k, m.sum(), " | ".join(partes)))
open(saida, "w", encoding="utf-8").write("\n".join(linhas) + "\n")
print("ok", saida, len(linhas), "linhas")
