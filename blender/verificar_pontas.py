"""Confere, na cena salva de uma rodada do golpes_soco.py, se o Neo ampliado (matrix_world) tem um vertice onde D() manda a ponta do pe e se a ponta do tenis do XSonic
(fantasma) esta onde o alvo pede. Uso: blender -b <cena.blend> --python verificar_pontas.py -- <metricas.json>"""
import json
import sys

import bpy
import numpy as np

m = json.load(open(sys.argv[sys.argv.index("--") + 1]))
S = m["escala_corpo"]


def D(p, A):
    return A + S * (np.asarray(p) - A)


def mundo(obj):
    mw = np.array(obj.matrix_world)
    co = np.empty(len(obj.data.vertices) * 3)
    obj.data.vertices.foreach_get("co", co)
    return co.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]


print("escala do corpo", S)
for q, d in m["quadros"].items():
    A = np.array(d["ancora"])
    print("quadro", q, "ancora", A.round(3))
    neo, gh = bpy.data.objects["NeoPose_%s" % q], bpy.data.objects["fantasma_%s" % q]
    vn, vg = mundo(neo), mundo(gh)
    capa = mundo(bpy.data.objects["CapaPose_%s" % q])
    print("quadro", q, "Neo z %.2f..%.2f  y %.2f..%.2f | capa z %.2f..%.2f | fantasma z %.2f..%.2f" % (
        vn[:, 2].min(), vn[:, 2].max(), vn[:, 1].min(), vn[:, 1].max(), capa[:, 2].min(), capa[:, 2].max(), vg[:, 2].min(), vg[:, 2].max()))
    for suf in ("X", "Y"):
        p = d["medidas_neo"]["pernas"][suf]
        ponta_neo, alvo = D(p["ponta"], A), D(p["ponta_alvo"], A)
        print("   perna %s: vertice do Neo em D(ponta) a %.5f m; vertice do fantasma na ponta do tenis a %.5f m; ponta do Neo - ponta do tenis = %.4f m" % (
            suf, np.linalg.norm(vn - ponta_neo, axis=1).min(), np.linalg.norm(vg - alvo, axis=1).min(), np.linalg.norm(ponta_neo - alvo)))
