"""Estudo da faixa (rastro) do quadro B do soco: lista as ilhas visiveis do quadro 278 e marca as que formam a faixa. Uso: python _estudo_rastro.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

import golpes_ref as G

q_nomes, sup = G.ler()
Q = 278
vis = G.mascara_visivel(sup, Q)
PUNHO_P = (0, [34, 35, 36, 37])
LUVA_P = (0, [44, 47, 48, 49, 50, 52, 53, 54])
HASTE_P = (31, [14, 17, 18])
linhas = []
for s, (sf, mv) in enumerate(zip(sup, vis)):
    if not mv.any():
        continue
    rot = G.componentes(sf["pos"].shape[1], sf["tris"])
    for il in np.unique(rot):
        m = (rot == il) & mv
        if not m.any():
            continue
        p = sf["pos"][Q][m]
        ext = p.max(0) - p.min(0)
        c = p.mean(0)
        marca = ""
        for nome, (ss, ils) in (("punho_P", PUNHO_P), ("luva_P", LUVA_P), ("haste_P", HASTE_P)):
            if ss == s and il in ils:
                marca = nome
        linhas.append((s, il, int(m.sum()), c, ext, marca))
print("quadro", Q, "ilhas visiveis:", len(linhas))
for s, il, n, c, e, marca in sorted(linhas, key=lambda x: -x[4][1]):
    if e[1] > 1.2 or marca:
        print("s%02d i%3d nv=%4d c=(%5.2f %5.2f %5.2f) ext=(%5.2f %5.2f %5.2f) %s" % (s, il, n, c[0], c[1], c[2], e[0], e[1], e[2], marca))
