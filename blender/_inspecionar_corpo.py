"""Imprime as matrizes da armadura e os ossos do tronco, bracos, cabeca e pernas (espaco da armadura e mundo), mais a caixa da malha."""
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import usuario_neo as U

arm = U.armadura()
print("matriz_mundo da armadura:\n", arm.matrix_world)
for pb in arm.pose.bones:
    n = U._norm(pb.name)
    if any(k in n for k in ("indicador", "medio", "anelar", "mindinho", "polegar")):
        continue
    b = pb.bone
    hm, tm = arm.matrix_world @ b.head_local, arm.matrix_world @ b.tail_local
    print("%-48r pai=%-28r h_loc=(%6.3f %6.3f %6.3f) t_loc=(%6.3f %6.3f %6.3f) h_mundo=(%6.3f %6.3f %6.3f) len=%5.3f inherit_scale=%s conecta=%s" % (
        pb.name, pb.parent.name if pb.parent else None, *b.head_local, *b.tail_local, *hm, b.length, b.inherit_scale, b.use_connect))
mn, mx = U.caixa_mundo()
print("caixa mundo (corpo+capa visivel):", mn, mx, "altura", mx[2] - mn[2])
mn, mx = U.caixa_mundo(["NeoMetal"])
print("caixa mundo NeoMetal:", mn, mx)
