"""Laboratorio do punho: renderiza a mao em varias vistas para cada variante.
Uso: blender -b <modelo.blend> --python _lab_punho.py -- <saida_dir> <arquivo_variantes.json> [lado]
Cada variante: {"curva": [a1, a2, a3], "polegar": [[f, fr, b] x3]} (ambos opcionais)."""
import json
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corrigir_pesos
import punho_fechado as PF
import usuario_neo as U

arg = sys.argv[sys.argv.index("--") + 1:]
saida = os.path.abspath(arg[0])
variantes = json.load(open(arg[1], encoding="utf-8"))
lado = arg[2] if len(arg) > 2 else "esquerdo"
os.makedirs(saida, exist_ok=True)

U.preparar(tecido=False)
bpy.data.objects["capa"].hide_render = True
corrigir_pesos.corrigir(verbose=False)
tam = int(os.environ.get("TAM", "600"))
cam, cd = U.camera_render(tam, tam, exposicao=1.0)
sinal = -1 if lado == "esquerdo" else 1
so_mao = os.environ.get("SO_MAO") == "1"
escala = float(os.environ.get("ESCALA", "0.95"))


def mascarar_mao():
    """Esconde tudo que nao e da mao (palma, dedos e polegar) para ver o perfil dos dedos sem o braco na frente."""
    obj = bpy.data.objects["NeoMetal"]
    nomes = {PF._palma(lado).name}
    for d in PF.DEDOS + ("polegar",):
        nomes |= {pb.name for pb in U.cadeia(lado, d)}
    idx = {g.index for g in obj.vertex_groups if g.name in nomes}
    vg = obj.vertex_groups.new(name="_mao")
    vg.add([v.index for v in obj.data.vertices if sum(g.weight for g in v.groups if g.group in idx) >= 0.5], 1.0, "REPLACE")
    mod = obj.modifiers.new("_mascara", "MASK")
    mod.vertex_group = "_mao"


if so_mao:
    mascarar_mao()
U.repouso()
palma = PF._palma(lado)
meio = (U.ponta_mundo(palma) + (U.armadura().matrix_world @ palma.head)) / 2
alvo = (meio.x - float(os.environ.get("DESLOC", "0.12")) * sinal, meio.y, meio.z - 0.1)
for nome, v in variantes.items():
    U.repouso()
    curva = tuple(v["curva"]) if v.get("curva") else None
    polegar = tuple(tuple(t) for t in v["polegar"]) if v.get("polegar") else None
    PF.fechar_mao(lado, curva=curva, polegar=polegar)
    dire = {"perfil": (0, 1, 0.0), "frente": (0, -1, 0.0), "baixo": (0, -0.03, -1), "ponta": (sinal, 0, 0.0), "ponta_baixo": (sinal * 0.6, -0.1, -0.8), "topo": (0, -0.03, 1)}
    for vista, d in dire.items():
        U.foto(cam, cd, os.path.join(saida, "%s_%s.png" % (nome, vista)), alvo, d, escala)
print("ok")
