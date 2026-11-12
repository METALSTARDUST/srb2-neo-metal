"""Estudo da perna e do pe: pinta o corpo pelos pesos dos ossos da perna (cada osso uma cor, pesos mistos viram mistura),
fotografa vistas da perna e do pe e grava as linhas dos ossos em pixels (para desenhar por cima depois).
Uso: blender -b <modelo.blend> --python _pes_estudo.py -- <saida_dir> [tam]"""
import json
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corrigir_pesos
import perna_poses as PP
import usuario_neo as U

arg = sys.argv[sys.argv.index("--") + 1:]
saida = os.path.abspath(arg[0])
tam = int(arg[1]) if len(arg) > 1 else 800
os.makedirs(saida, exist_ok=True)

U.preparar(tecido=False)
bpy.data.objects["capa"].hide_render = True
corrigir_pesos.corrigir(verbose=False)
U.repouso()

CORES = {"quadril": (0.62, 0.30, 0.90), "coxa": (1.0, 0.82, 0.10), "canela": (0.15, 0.45, 1.0),
         "pe_frente": (1.0, 0.15, 0.10), "pe_tras": (0.10, 0.80, 0.20)}
CINZA = (0.74, 0.74, 0.76)
corpo = bpy.data.objects["NeoMetal"]
me = corpo.data
cor_do_grupo = {}
papel_do_osso = {}
for lado in U.LADOS:
    for papel, pb in PP.ossos_perna(lado).items():
        cor_do_grupo[pb.name] = CORES[papel]
        papel_do_osso[pb.name] = (lado, papel)
indice = {vg.index: cor_do_grupo.get(vg.name) for vg in corpo.vertex_groups}
attr = me.color_attributes.new(name="pesos_perna", type="FLOAT_COLOR", domain="POINT")
dados = []
for v in me.vertices:
    r = g = b = resto = 0.0
    for ge in v.groups:
        c = indice.get(ge.group)
        if c is None:
            continue
        r += c[0] * ge.weight
        g += c[1] * ge.weight
        b += c[2] * ge.weight
        resto += ge.weight
    f = max(0.0, 1.0 - resto)
    dados += [r + CINZA[0] * f, g + CINZA[1] * f, b + CINZA[2] * f, 1.0]
attr.data.foreach_set("color", dados)
me.color_attributes.active_color = attr
try:
    me.color_attributes.default_color_name = "pesos_perna"
except (AttributeError, TypeError):
    pass

cam, cd = U.camera_render(tam, tam, exposicao=0.2)
bpy.context.scene.display.shading.color_type = "VERTEX"
arm = U.armadura()
bola = {lado: PP.bola_tornozelo(lado) for lado in U.LADOS}
linhas = {}


def projetar(p, escala):
    c = cam.matrix_world.inverted() @ p
    return [(c.x / escala + 0.5) * tam, (0.5 - c.y / escala) * tam]


def fotografar(nome, alvo, direcao, escala):
    U.foto(cam, cd, os.path.join(saida, nome + ".png"), alvo, direcao, escala)
    bpy.context.view_layer.update()
    osso = []
    for lado in U.LADOS:
        for papel, pb in PP.ossos_perna(lado).items():
            osso.append({"nome": pb.name.strip(), "lado": lado, "papel": papel,
                         "a": projetar(arm.matrix_world @ pb.head, escala), "b": projetar(arm.matrix_world @ pb.tail, escala)})
    linhas[nome] = osso


perna = (-0.05, 0.0, 0.80)
fotografar("perna_frente", perna, (0, -1, 0.0), 1.9)
fotografar("perna_lado_esq", perna, (-1, 0, 0.0), 1.9)
fotografar("perna_tres_quartos", perna, (-0.62, -0.78, 0.30), 1.9)
fotografar("perna_costas", perna, (0, 1, 0.0), 1.9)
for lado, sinal in (("esquerdo", -1), ("direito", 1)):
    b = bola[lado]
    alvo = (b.x, b.y, 0.17)
    fotografar("pe_%s_lado" % lado, alvo, (sinal, 0, 0.0), 0.8)
    fotografar("pe_%s_frente" % lado, alvo, (0, -1, 0.0), 0.8)
    fotografar("pe_%s_cima" % lado, alvo, (0, -0.03, 1), 0.8)
    fotografar("pe_%s_tres_quartos" % lado, alvo, (sinal * 0.62, -0.78, 0.30), 0.8)
json.dump(linhas, open(os.path.join(saida, "ossos.json"), "w", encoding="utf-8"), ensure_ascii=False)
print("BOLAS", {k: [round(c, 4) for c in v] for k, v in bola.items()})
print("ok")
