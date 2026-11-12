"""Fotografa poses da perna inteira (quadril, joelho e as metades do pe), de lado, com uma barra de chao em z = 0.
Uso: blender -b <modelo.blend> --python _poses_perna.py -- <saida_dir> [tam]
Cada pose = {lado: dict(argumentos de pose_perna)}."""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corrigir_pesos
import perna_poses as PP
import usuario_neo as U

arg = sys.argv[sys.argv.index("--") + 1:]
saida = os.path.abspath(arg[0])
tam = int(arg[1]) if len(arg) > 1 else 640
os.makedirs(saida, exist_ok=True)

POSES = {
    "parado": {"esquerdo": {}, "direito": {}},
    "passo": {"esquerdo": dict(quadril=-25.0, joelho=10.0),
              "direito": dict(quadril=20.0, joelho=35.0, calcanhar_reto=False)},
    "agachado": {"esquerdo": dict(quadril=-45.0, joelho=85.0), "direito": dict(quadril=-45.0, joelho=85.0)},
    "chute": {"esquerdo": dict(quadril=-70.0, joelho=5.0, ponta_reta=False, calcanhar_reto=False), "direito": {}},
}

U.preparar(tecido=False)
bpy.data.objects["capa"].hide_render = True
corrigir_pesos.corrigir(verbose=False)
U.repouso()
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, -0.006))
chao = bpy.context.active_object
chao.scale = (4.0, 4.0, 0.012)
mat = bpy.data.materials.new("chao")
mat.use_nodes = False
mat.diffuse_color = (0.18, 0.18, 0.24, 1.0)
chao.data.materials.append(mat)
cam, cd = U.camera_render(tam, tam, exposicao=1.0)
for nome, lados in POSES.items():
    for lado in U.LADOS:
        PP.soltar_perna(lado)
        PP.pose_perna(lado, **lados[lado])
    U.foto(cam, cd, os.path.join(saida, "%s_lado.png" % nome), (-0.05, 0.0, 0.80), (-1, 0, 0.0), 1.9)
    U.foto(cam, cd, os.path.join(saida, "%s_frente.png" % nome), (-0.05, 0.0, 0.80), (0, -1, 0.0), 1.9)
print("ok", len(POSES))
