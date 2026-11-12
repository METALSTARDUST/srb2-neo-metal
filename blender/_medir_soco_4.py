"""Compara os grupos rigidos do soco normal (141-144) com os do Super (277-280): mesma pose?"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import golpes_ref as G
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_medir_soco_3.py")).read().split("for ref in")[0])
print("grupo      quadro  centro normal            centro Super             dif   rot(graus entre os dois)")
for n_, s_ in zip((141, 142, 143, 144), (277, 278, 279, 280)):
    for nome in ("cabeca", "tronco", "luva_P", "luva_Q", "punho_P", "punho_Q", "tenis_X", "tenis_Y", "canela_X", "canela_Y"):
        a, b = pontos(GRUPOS[nome], n_), pontos(GRUPOS[nome], s_)
        ca, cb = a.mean(0), b.mean(0)
        r, _, _, res = kabsch(a, b)
        ang = np.degrees(np.arccos(np.clip((np.trace(r) - 1) / 2, -1, 1)))
        print("%-9s %d/%d (%5.2f %5.2f %5.2f)  (%5.2f %5.2f %5.2f)  d=%.3f rot=%.1f res=%.3f" % (nome, n_, s_, *ca, *cb, np.linalg.norm(ca - cb), ang, res))
