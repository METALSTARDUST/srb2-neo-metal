"""Fotografa poses do pe articulado (as duas metades giram em torno da bola do tornozelo) nos dois pes.
Uso: blender -b <modelo.blend> --python _poses_pe.py -- <saida_dir> [tam]      (env PESOS=1 pinta pelos pesos da perna)
Cada pose = (ponta, calcanhar, tornozelo): inclinacao da sola de cada metade e giro do pe inteiro, em graus (0 = sola reta, o repouso)."""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corrigir_pesos
import perna_poses as PP
import usuario_neo as U

arg = sys.argv[sys.argv.index("--") + 1:]
saida = os.path.abspath(arg[0])
tam = int(arg[1]) if len(arg) > 1 else 560
os.makedirs(saida, exist_ok=True)

POSES = {
    "repouso": (0.0, 0.0, 0.0),
    "ponta_cima": (35.0, 0.0, 0.0),
    "ponta_baixo": (-35.0, 0.0, 0.0),
    "calcanhar_cima": (0.0, 35.0, 0.0),
    "calcanhar_baixo": (0.0, -35.0, 0.0),
    "bico_cima_rigido": (0.0, 0.0, 30.0),
    "desenho": (42.0, 12.0, 0.0),
}

U.preparar(tecido=False)
bpy.data.objects["capa"].hide_render = True
corrigir_pesos.corrigir(verbose=False)
U.repouso()
pesos = os.environ.get("PESOS") == "1"
if pesos:
    PP.pintar_pesos()
cam, cd = U.camera_render(tam, tam, exposicao=0.2 if pesos else 1.0)
if pesos:
    bpy.context.scene.display.shading.color_type = "VERTEX"
bola = {lado: PP.bola_tornozelo(lado) for lado in U.LADOS}
alvo = {lado: (bola[lado].x, bola[lado].y, 0.17) for lado in U.LADOS}
for nome, (ponta, calcanhar, tornozelo) in POSES.items():
    for lado in U.LADOS:
        PP.soltar_perna(lado)
        PP.inclinar_pe(lado, ponta, calcanhar, tornozelo)
    U.foto(cam, cd, os.path.join(saida, "%s_lado.png" % nome), alvo["esquerdo"], (-1, 0, 0.0), 0.8)
    U.foto(cam, cd, os.path.join(saida, "%s_tres_quartos.png" % nome), alvo["esquerdo"], (-0.62, -0.78, 0.30), 0.8)
    U.foto(cam, cd, os.path.join(saida, "%s_lado_dir.png" % nome), alvo["direito"], (1, 0, 0.0), 0.8)
print("ok", len(POSES))
