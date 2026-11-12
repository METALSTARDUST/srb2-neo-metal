"""Fotografa as poses da biblioteca mao_poses (mao isolada, sem o braco na frente).
Uso: blender -b <modelo.blend> --python _poses_mao.py -- <saida_dir> [lado] [tam] [pose1,pose2,...] [t]
Com 't' (0 a 1) a pose e aplicada pela metade do caminho; o arquivo sai como <pose>_t<NN>_<vista>.png."""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corrigir_pesos
import mao_poses as MP
import punho_fechado as PF
import usuario_neo as U

arg = sys.argv[sys.argv.index("--") + 1:]
saida = os.path.abspath(arg[0])
lado = arg[1] if len(arg) > 1 else "esquerdo"
tam = int(arg[2]) if len(arg) > 2 else 480
nomes = arg[3].split(",") if len(arg) > 3 and arg[3] else list(MP.POSES)
ts = [float(x) for x in arg[4].split(",")] if len(arg) > 4 else [1.0]
os.makedirs(saida, exist_ok=True)

U.preparar(tecido=False)
bpy.data.objects["capa"].hide_render = True
corrigir_pesos.corrigir(verbose=False)
U.repouso()
sinal = -1 if lado == "esquerdo" else 1
pulso = U.armadura().matrix_world @ PF._palma(lado).head
U.mascarar_ossos({pb.name for pb in MP.ossos_da_mao(lado)})
cam, cd = U.camera_render(tam, tam, exposicao=1.0)
alvo = (pulso.x + sinal * 0.42, pulso.y - 0.03, pulso.z + 0.10)
vistas = {"perfil": (0, 1, 0.0), "baixo": (0, -0.03, -1), "ponta_baixo": (sinal * 0.6, -0.1, -0.8)}
for nome in nomes:
    for t in ts:
        MP.aplicar(lado, MP.POSES[nome], t)
        sufixo = "" if len(ts) == 1 and t == 1.0 else "_t%02d" % round(t * 100)
        for vista, d in vistas.items():
            U.foto(cam, cd, os.path.join(saida, "%s%s_%s.png" % (nome, sufixo, vista)), alvo, d, 1.1)
print("ok", len(nomes) * len(ts))
