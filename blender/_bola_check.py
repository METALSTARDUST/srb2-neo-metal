"""Diagnostico da bola do tornozelo: quais pecas (ilhas) ficam em volta da bola, com que pesos, e quanto cada uma se desloca
quando a ponta ou o calcanhar giram 35 graus. Uso: blender -b <modelo.blend> --python _bola_check.py -- [lado]"""
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corrigir_pesos
import perna_poses as PP
import usuario_neo as U

arg = sys.argv[sys.argv.index("--") + 1:]
lado = arg[0] if arg else "esquerdo"
U.preparar(tecido=False)
corrigir_pesos.corrigir(verbose=False)
U.repouso()
corpo = bpy.data.objects["NeoMetal"]
me = corpo.data
nv = len(me.vertices)
nomes = [vg.name.strip() for vg in corpo.vertex_groups]
W = np.zeros((nv, len(nomes)))
for v in me.vertices:
    for ge in v.groups:
        W[v.index, ge.group] = ge.weight
pai = list(range(nv))


def achar(a):
    while pai[a] != a:
        pai[a] = pai[pai[a]]
        a = pai[a]
    return a


for e in me.edges:
    a, b = achar(e.vertices[0]), achar(e.vertices[1])
    if a != b:
        pai[a] = b
ilha = np.array([achar(i) for i in range(nv)])


def posicoes():
    dg = bpy.context.evaluated_depsgraph_get()
    ev = corpo.evaluated_get(dg)
    m = ev.to_mesh()
    p = np.array([(corpo.matrix_world @ v.co)[:] for v in m.vertices])
    ev.to_mesh_clear()
    return p


o = PP.ossos_perna(lado)
bola = np.array(PP.bola_tornozelo(lado)[:])
repouso = posicoes()
cenarios = {}
for nome, args in (("ponta+35", dict(ponta=35.0)), ("calcanhar+35", dict(calcanhar=35.0))):
    PP.soltar_perna(lado)
    PP.inclinar_pe(lado, **args)
    cenarios[nome] = posicoes()
PP.soltar_perna(lado)

idx_ponta = nomes.index(o["pe_frente"].name.strip())
idx_calc = nomes.index(o["pe_tras"].name.strip())
idx_canela = nomes.index(o["canela"].name.strip())
print("BOLA", bola.round(4))
linhas = []
for i in np.unique(ilha):
    m = ilha == i
    pts = repouso[m]
    cen = pts.mean(axis=0)
    if np.linalg.norm(cen - bola) > 0.16 or m.sum() < 8:
        continue
    w = W[m].mean(axis=0)
    desloc = {k: float(np.linalg.norm((c[m] - repouso[m]).mean(axis=0)) * 1000) for k, c in cenarios.items()}
    esticou = {k: float(np.linalg.norm((c[m] - c[m].mean(axis=0)) - (repouso[m] - cen), axis=1).max() * 1000) for k, c in cenarios.items()}
    linhas.append((np.linalg.norm(cen - bola), int(m.sum()), cen, pts.min(axis=0), pts.max(axis=0), w[idx_ponta], w[idx_calc], w[idx_canela], desloc, esticou))
linhas.sort(key=lambda t: t[0])
for d, n, cen, lo, hi, wp, wc, wk, desloc, esticou in linhas:
    print("dist %.3f n=%3d centro=(%.3f,%.3f,%.3f) tamanho=(%.2f,%.2f,%.2f) pesos ponta %.2f calc %.2f canela %.2f | centroide mexe (mm) %s | deforma (mm) %s" % (
        d, n, cen[0], cen[1], cen[2], hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2], wp, wc, wk,
        {k: round(v, 1) for k, v in desloc.items()}, {k: round(v, 1) for k, v in esticou.items()}))
print("ok")
