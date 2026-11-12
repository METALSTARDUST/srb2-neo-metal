"""(Python do Blender, numpy) Projeta um quadro do XSONIC.md3 em 2D e grava JSON com triangulos por ilha e rotulos.
Uso: python _mapa_ilhas_dados.py <quadro> <saida.json> [lado|frente|cima]   (lado: camera em -X, frente do personagem a direita; cima: frente do personagem para cima da imagem)"""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import golpes_ref as G

q, sup = G.ler()
f = int(sys.argv[1])
vista = sys.argv[3] if len(sys.argv) > 3 else "lado"
mv = G.mascara_visivel(sup, f)


def proj(p):
    if vista == "lado":
        return (-p[:, 1], p[:, 2], -p[:, 0])
    if vista == "cima":
        return (p[:, 0], -p[:, 1], p[:, 2])
    return (p[:, 0], p[:, 2], p[:, 1])


tris, rot_txt = [], []
for i, s in enumerate(sup):
    if not mv[i].any():
        continue
    rot = G.componentes(s["pos"].shape[1], s["tris"])
    pos = s["pos"][f]
    u, v, d = proj(pos)
    for t in s["tris"]:
        if mv[i][t].all():
            tris.append([[float(u[a]), float(v[a])] for a in t] + [i, int(rot[t[0]]), float(d[t].mean())])
    for k in np.unique(rot[mv[i]]):
        m = (rot == k) & mv[i]
        if m.sum() >= 5:
            rot_txt.append([float(u[m].mean()), float(v[m].mean()), "%d.%d" % (i, k), int(m.sum())])
json.dump(dict(tris=tris, rotulos=rot_txt), open(sys.argv[2], "w"))
print("ok", len(tris), "triangulos", len(rot_txt), "rotulos")
