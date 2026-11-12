"""Perfil radial da perna do Neo ao longo do eixo da coxa (repouso): onde ficam a bola do quadril, a haste da coxa, a bola do joelho e o cone da canela."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
import usuario_neo as U
import perna_poses as PP
U.preparar()
U.repouso()
corpo = bpy.data.objects["NeoMetal"]
me = corpo.data
n = len(me.vertices)
M = np.array(corpo.matrix_world)
co = np.empty(n * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
nomes = {vg.index: vg.name for vg in corpo.vertex_groups}
def w_osso(nome):
    w = np.zeros(n)
    idx = [i for i, nm in nomes.items() if nm == nome]
    for v in me.vertices:
        for g in v.groups:
            if g.group in idx:
                w[v.index] += g.weight
    return w
A = U.armadura().matrix_world
for lado in ("direito",):
    o = PP.ossos_perna(lado)
    for papel in ("quadril", "coxa", "canela"):
        pb = o[papel]
        s = np.array((A @ pb.bone.head_local)[:]); e = np.array((A @ pb.bone.tail_local)[:])
        u = (e - s) / np.linalg.norm(e - s)
        w = w_osso(pb.name)
        sel = np.where(w >= 0.5)[0]
        t = (co[sel] - s) @ u
        r = np.linalg.norm(co[sel] - s - np.outer(t, u), axis=1)
        print("== %s (%s): %d vertices com peso>=0.5; comprimento do osso %.3f" % (papel, pb.name, len(sel), np.linalg.norm(e - s)))
        for a in np.arange(-0.1, np.linalg.norm(e - s) + 0.2, 0.04):
            m = (t >= a) & (t < a + 0.04)
            if m.any():
                print("   t %5.2f-%5.2f  n=%3d  raio %.3f-%.3f" % (a, a + 0.04, m.sum(), r[m].min(), r[m].max()))
