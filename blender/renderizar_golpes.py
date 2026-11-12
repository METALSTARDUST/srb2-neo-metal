"""Renderiza quadros escolhidos de um .blend criado por importar_md3.py (XSONIC.md3) em duas vistas com enquadramento fixo.
Cada PNG sai com o personagem centrado na caixa do proprio quadro; a escala e a mesma dentro de cada grupo de quadros (um golpe),
entao as poses do golpe se comparam sem o personagem ficar minusculo.
O MD3 estaciona as pecas que nao aparecem num quadro em pontos quaisquer (muitas vezes longe do corpo) e centenas de vertices
ficam empilhados no mesmo ponto: a caixa ignora toda posicao repetida 20 vezes ou mais. Quadro sem nada visivel e pulado.
Uso: blender -b xsonic.blend --python renderizar_golpes.py -- <saida_dir> <tam> <modelo.md3> <q,q,q;q,q;...>   (grupos separados por ;)
O quadro N do MD3 e o quadro N + 1 da linha do tempo do Blender. Saida: q<N>_lado.png (camera em -X: a frente do personagem
fica a direita da imagem) e q<N>_34.png (de tres quartos, frente e esquerda)."""
import collections
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importar_md3

arg = sys.argv[sys.argv.index("--") + 1:]
saida = os.path.abspath(arg[0])
tam = int(arg[1])
md3 = os.path.abspath(arg[2])
grupos = [[int(x) for x in g.split(",")] for g in arg[3].split(";")]
os.makedirs(saida, exist_ok=True)

sc = bpy.context.scene
_, superficies = importar_md3.ler_md3(md3)
ESC = importar_md3.ESCALA


def caixa(q):
    """Caixa (em unidades do Blender) dos vertices visiveis do quadro q, ou None se nao houver nada visivel."""
    pts = [p for s in superficies for p in s["frames"][q]]
    contagem = collections.Counter(pts)
    vis = [p for p in pts if contagem[p] < 20]
    if len(vis) < 50:
        return None
    mp = [Vector((y * ESC, -x * ESC, z * ESC)) for x, y, z in vis]
    mn = Vector([min(p[i] for p in mp) for i in range(3)])
    mx = Vector([max(p[i] for p in mp) for i in range(3)])
    return mn, mx


cd = bpy.data.cameras.new("cam")
cd.type = "ORTHO"
cam = bpy.data.objects.new("cam", cd)
sc.collection.objects.link(cam)
sc.camera = cam
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.light = "STUDIO"
sc.display.shading.color_type = "TEXTURE"
sc.display.shading.show_cavity = False
sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = tam
sc.render.image_settings.color_mode = "RGBA"

VISTAS = {"lado": Vector((-1.0, 0.0, 0.0)), "34": Vector((-0.62, -0.78, 0.18))}
vazios = []
for quadros in grupos:
    caixas = {q: caixa(q) for q in quadros}
    vazios += [q for q, c in caixas.items() if c is None]
    visiveis = [q for q in quadros if caixas[q] is not None]
    if not visiveis:
        continue
    maior = max(max((mx - mn)[i] for i in range(3)) for mn, mx in (caixas[q] for q in visiveis))
    cd.ortho_scale = maior * 1.12
    for q in visiveis:
        sc.frame_set(q + 1)
        bpy.context.view_layer.update()
        mn, mx = caixas[q]
        centro = (mn + mx) / 2
        for nome, d in VISTAS.items():
            cam.location = centro + d.normalized() * 60
            cam.rotation_euler = (centro - cam.location).to_track_quat("-Z", "Y").to_euler()
            sc.render.filepath = os.path.join(saida, "q%03d_%s.png" % (q, nome))
            bpy.ops.render.render(write_still=True)
    print("grupo", quadros[0], "..", quadros[-1], "escala", round(cd.ortho_scale, 2))
print("ok, vazios:", vazios)
