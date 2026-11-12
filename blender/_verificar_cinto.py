"""Fotos do cinto/capa em repouso e em duas poses de corpo inteiro (tronco inclinado e girado), para conferir que o cinto acompanha o corpo.
Uso: blender -b <arquivo>.blend --python _verificar_cinto.py -- <saida_dir> <rotulo>"""
import math, os, sys
import bpy, numpy as np
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import usuario_neo as U, braco_poses as BP

arg = sys.argv[sys.argv.index("--") + 1:]
saida, rotulo = os.path.abspath(arg[0]), arg[1]
os.makedirs(saida, exist_ok=True)
U.preparar()
cam, cd = U.camera_render(560, 560, 1.0)
VISTAS = {"lado": Vector((1, 0, 0.0)), "frente": Vector((0, -1, 0.1)), "tres_quartos": Vector((0.62, -0.78, 0.25))}

def fotos(nome, escala=4.2, alvo=Vector((0, 0.3, 1.4))):
    for v, d in VISTAS.items():
        U.foto(cam, cd, os.path.join(saida, "%s_%s_%s.png" % (rotulo, nome, v)), alvo, d, escala)

BP.zerar()
fotos("repouso")
R1 = Matrix.Rotation(math.radians(40), 3, "X")          # inclina o corpo todo 40 graus para a frente (em torno da pelve)
BP.pose_corpo(R1, (0, -0.3, -0.2))
fotos("inclinado", alvo=Vector((0, 0.0, 1.2)))
R2 = Matrix.Rotation(math.radians(70), 3, "Z") @ Matrix.Rotation(math.radians(25), 3, "X")
BP.pose_corpo(R2, (0.2, 0.0, 0.0))
fotos("girado", alvo=Vector((0, 0.0, 1.3)))
# pesos: quantos vertices do cinto seguem algum osso
capa = bpy.data.objects["capa"]
sem = [v.index for v in capa.data.vertices if not any(g.weight > 1e-4 and capa.vertex_groups[g.group].name != "capa_fixacao" for g in v.groups)]
print("vertices da capa sem peso de osso:", len(sem))
