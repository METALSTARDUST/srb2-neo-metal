"""Imprime a geometria (mundo) dos ossos de cada dedo depois de fechar a mao: cabeca, cauda, comprimento e angulo no plano XZ.
Uso: blender -b <modelo.blend> --python _diag_dedos.py -- [lado] [a1,a2,a3]"""
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import punho_fechado as PF
import usuario_neo as U

arg = sys.argv[sys.argv.index("--") + 1:]
lado = arg[0] if arg else "esquerdo"
curva = tuple(float(x) for x in arg[1].split(",")) if len(arg) > 1 else None
sinal = -1 if lado == "esquerdo" else 1

U.preparar(tecido=False)
U.repouso()
arm = U.armadura()
mw = arm.matrix_world
PF.fechar_mao(lado, curva=curva)
bpy.context.view_layer.update()

for nome in PF.DEDOS + ("polegar",):
    print("==", nome)
    for pb in U.cadeia(lado, nome):
        h = mw @ pb.head
        t = mw @ pb.tail
        v = t - h
        ang = math.degrees(math.atan2(-v.z, v.x * sinal))
        print("%-26s h=(%.3f,%.3f,%.3f) t=(%.3f,%.3f,%.3f) len=%.3f ang_xz=%6.1f  dy=%.3f" % (pb.name, h.x, h.y, h.z, t.x, t.y, t.z, v.length, ang, v.y))
print("ok")
