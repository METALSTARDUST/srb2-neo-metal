"""Perfil radial dos bracos do Neo em repouso: raio maximo por faixa ao longo do eixo do braco (acha a haste fina entre as juntas)."""
import os, sys
import bpy
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import usuario_neo as U
import perna_poses as PP

U.preparar()
U.repouso()
corpo = bpy.data.objects["NeoMetal"]
arm = U.armadura()
mw = corpo.matrix_world
co = np.array([(mw @ v.co)[:] for v in corpo.data.vertices])
nome_g = {vg.index: PP._sem_acento(vg.name) for vg in corpo.vertex_groups}
for lado, chave in (("direito", "direit"), ("esquerdo", "esquerd")):
    pesos = np.zeros(len(co))
    for v in corpo.data.vertices:
        for g in v.groups:
            n = nome_g[g.group]
            if chave in n and any(k in n for k in ("braco", "cotovelo", "cutovelo", "punho", "indicador", "medio", "anelar", "mindinho", "polegar")):
                pesos[v.index] += g.weight
    arm_pb = [pb for pb in arm.pose.bones if PP._sem_acento(pb.name).startswith("braco") and chave in PP._sem_acento(pb.name)][0]
    s = np.array((arm.matrix_world @ arm_pb.bone.head_local)[:])
    e = np.array((arm.matrix_world @ arm_pb.bone.tail_local)[:])
    u = (e - s) / np.linalg.norm(e - s)
    sel = pesos >= 0.5
    t = (co[sel] - s) @ u
    perp = co[sel] - s - np.outer(t, u)
    r = np.linalg.norm(perp, axis=1)
    print("\n%s: ombro(braco head) %s tail %s u %s; vertices do braco para fora %d" % (lado, s.round(3), e.round(3), u.round(3), sel.sum()))
    for a in np.arange(-0.1, 0.62, 0.02):
        m = (t >= a) & (t < a + 0.02)
        if m.any():
            print("t %.2f..%.2f  n=%3d  r_max=%.3f  r_med=%.3f  verts so de 'braco' (peso braco>=.9): %d" % (a, a + 0.02, m.sum(), r[m].max(), r[m].mean(), 0))
