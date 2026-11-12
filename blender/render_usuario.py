"""Fotografa o modelo do usuario. Uso:
blender -b <modelo.blend> --python render_usuario.py -- <pose> <saida_dir> [tamanho]
pose: usuario (como foi salva) | repouso (todos os ossos zerados) | punho (repouso + punhos fechados, ver PUNHO)
Gera vistas do corpo inteiro e fotos de perto das duas maos."""
import json
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import usuario_neo as U

arg = sys.argv[sys.argv.index("--") + 1:]
pose = arg[0]
saida = os.path.abspath(arg[1])
tam = int(arg[2]) if len(arg) > 2 else 900
os.makedirs(saida, exist_ok=True)

import corrigir_pesos

U.preparar(tecido=False)
if os.environ.get("CORRIGIR", "1") == "1":
    corrigir_pesos.corrigir(verbose=False)
if os.environ.get("CAPA", "0") != "1":
    bpy.data.objects["capa"].hide_render = True
if pose in ("repouso", "punho"):
    U.repouso()


def alvo_mao(lado, sinal):
    medio = U.cadeia(lado, "medio")
    pts = [U.ponta_mundo(pb) for pb in medio]
    c = sum((p for p in pts), pts[0] * 0) / len(pts)
    return (c.x - 0.12 * sinal, c.y, c.z - 0.05)


# o enquadramento das maos sai da pose aberta, para o antes e o depois ficarem alinhados
alvos_maos = {lado: alvo_mao(lado, sinal) for lado, sinal in (("esquerdo", -1), ("direito", 1))}
if pose == "punho":
    import punho_fechado as PF
    PF.aplicar()

lo, hi = U.caixa_mundo()
print("CAIXA", [round(float(x), 3) for x in lo], [round(float(x), 3) for x in hi])
cen = (lo + hi) / 2
altura = float(hi[2] - lo[2])
largura = float(hi[0] - lo[0])
escala = max(altura, largura) * 1.08

cam, cd = U.camera_render(tam, tam, exposicao=1.0)
alvo = (float(cen[0]), float(cen[1]), float(cen[2]))
vistas = {
    "frente": (0, -1, 0.12),
    "lado_dir": (-1, 0, 0.12),
    "costas": (0, 1, 0.12),
    "tres_quartos": (-0.62, -0.78, 0.30),
    "topo": (0, -0.04, 1),
}
for nome, d in vistas.items():
    U.foto(cam, cd, os.path.join(saida, "%s_%s.png" % (pose, nome)), alvo, d, escala)

for lado, sinal in (("esquerdo", -1), ("direito", 1)):
    alvo_m = alvos_maos[lado]
    dire = {"topo": (0, -0.03, 1), "frente": (0, -1, 0.15), "ponta": (sinal, 0, 0.15), "baixo": (0, -0.03, -1)}
    for nome, d in dire.items():
        U.foto(cam, cd, os.path.join(saida, "%s_mao_%s_%s.png" % (pose, lado, nome)), alvo_m, d, 1.5)
print("FOTOS em", saida)
