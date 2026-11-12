"""Centroides dos grupos de ilhas em varios quadros (parado, soco) e residuo do ajuste rigido (Kabsch) em relacao ao quadro parado."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import golpes_ref as G

q, sup = G.ler()
rot = {i: G.componentes(sup[i]["pos"].shape[1], sup[i]["tris"]) for i in (0, 27, 31, 32, 1)}
GRUPOS = {
    "cabeca": [(0, [10])],
    "tronco": [(0, [96, 97, 98, 99])],
    "luva_P": [(0, [44, 47, 48, 49, 50, 52, 53, 54])],
    "punho_P": [(0, [34, 35, 36, 37])],
    "haste_P": [(31, [14, 17, 18])],
    "luva_Q": [(27, [16, 17, 20, 21, 22, 24, 25, 26])],
    "punho_Q": [(27, [8, 9, 10, 11])],
    "haste_Q": [(32, [1, 3, 4])],
    "tenis_X": [(0, [26, 27, 92, 93, 94])],
    "tenis_Y": [(27, [0, 1, 27, 28, 29])],
    "canela_X": [(0, [38, 39, 40, 41])],
    "canela_Y": [(27, [12, 13, 14, 15])],
}


def idx(grupo):
    out = []
    for s, ilhas in grupo:
        m = np.isin(rot[s], ilhas)
        out.append((s, np.where(m)[0]))
    return out


def pontos(grupo, f):
    return np.concatenate([sup[s]["pos"][f][ix] for s, ix in idx(grupo)])


def kabsch(a, b):
    ca, cb = a.mean(0), b.mean(0)
    h = (a - ca).T @ (b - cb)
    u, _, vt = np.linalg.svd(h)
    d = np.sign(np.linalg.det(vt.T @ u.T))
    r = vt.T @ np.diag([1, 1, d]) @ u.T
    res = np.sqrt((((a - ca) @ r.T + cb - b) ** 2).sum(1).mean())
    return r, ca, cb, res


for ref in (5, 219):
    print("\n=== parado %d (%s)" % (ref, q[ref]))
    todos = np.concatenate([sup[i]["pos"][ref][G.mascara_visivel(sup, ref)[i]] for i in range(len(sup))])
    print("caixa visivel min", todos.min(0).round(2), "max", todos.max(0).round(2), "altura", round(todos[:, 2].max() - todos[:, 2].min(), 2))
    for nome, g in GRUPOS.items():
        p = pontos(g, ref)
        print("%-9s n=%3d c=(%6.2f %6.2f %6.2f) ext=(%5.2f %5.2f %5.2f)" % (nome, len(p), *p.mean(0), *(p.max(0) - p.min(0))))
    for f in ([277, 278, 279, 280] if ref == 219 else [141, 142, 143, 144]):
        lin = []
        for nome in ("cabeca", "tronco", "luva_P", "luva_Q", "tenis_X", "tenis_Y"):
            p0, p1 = pontos(GRUPOS[nome], ref), pontos(GRUPOS[nome], f)
            r, ca, cb, res = kabsch(p0, p1)
            lin.append("%s res=%.2f" % (nome, res))
        print(f, " | ".join(lin))
