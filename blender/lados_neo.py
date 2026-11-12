"""Imprime de que lado (X do Blender) fica cada perna do Neo parado e para onde o Neo olha.
Uso: blender -b neo_base_pose.blend --python lados_neo.py"""
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, r"C:\tmp\srb2-metal-homing\neo\fontes\blender")
import braco_poses as BP
import perna_poses as PP

ob = bpy.data.objects["NeoMetal"]
co = BP._coords(ob)
print("ARMATURE:", [o.name for o in bpy.data.objects if o.type == "ARMATURE"])
for lado in ("direito", "esquerdo"):
    o = PP.ossos_perna(lado)
    print("== lado", lado, "ossos:", {k: v.name for k, v in o.items()})
    quadril = np.array(BP.p_mundo(o["coxa"].head)[:])
    joelho = np.array(BP.p_mundo(o["canela"].head)[:])
    tornozelo = np.array(BP.p_mundo(o["pe_frente"].head)[:])
    ponta = co[BP.indice_ponta_pe(lado)]
    print("  quadril", quadril.round(3), "joelho", joelho.round(3), "tornozelo", tornozelo.round(3), "ponta", np.array(ponta).round(3))
    print("  frente do pe (ponta - tornozelo):", (np.array(ponta) - tornozelo).round(3))
for lado in ("direito", "esquerdo"):
    try:
        b = BP.ossos_braco(lado)
        print("braco", lado, {k: (v.name, np.array(BP.p_mundo(v.head)[:]).round(3).tolist()) for k, v in b.items() if hasattr(v, "head")})
    except Exception as e:
        print("braco", lado, "erro", e)
