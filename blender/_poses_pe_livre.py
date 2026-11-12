"""Testa os outros graus de liberdade das metades do pe (abrir para o lado e rolar), alem da inclinacao.
Uso: blender -b <modelo.blend> --python _poses_pe_livre.py -- <saida_dir> [tam]"""
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
    "repouso": [],
    "ponta_para_dentro": [("ponta", PP.Z, 25.0)],
    "ponta_para_fora": [("ponta", PP.Z, -25.0)],
    "calcanhar_para_fora": [("calcanhar", PP.Z, 25.0)],
    "ponta_rolando": [("ponta", PP.Y, 20.0)],
    "as_duas_abertas": [("ponta", PP.Z, -20.0), ("calcanhar", PP.Z, 20.0)],
}

U.preparar(tecido=False)
bpy.data.objects["capa"].hide_render = True
corrigir_pesos.corrigir(verbose=False)
U.repouso()
cam, cd = U.camera_render(tam, tam, exposicao=1.0)
bola = PP.bola_tornozelo("esquerdo")
alvo = (bola.x, bola.y, 0.17)
for nome, giros in POSES.items():
    PP.soltar_perna("esquerdo")
    for metade, eixo, graus in giros:
        PP.girar_metade("esquerdo", metade, eixo, graus)
    U.foto(cam, cd, os.path.join(saida, "%s_baixo.png" % nome), alvo, (0, -0.03, -1), 0.8)
    U.foto(cam, cd, os.path.join(saida, "%s_frente.png" % nome), alvo, (0, -1, 0.0), 0.8)
    U.foto(cam, cd, os.path.join(saida, "%s_tres_quartos.png" % nome), alvo, (-0.62, -0.78, 0.30), 0.8)
print("ok", len(POSES))
