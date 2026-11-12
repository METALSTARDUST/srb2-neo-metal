"""Utilidades para o modelo do usuario (NeoMetal rigado no Blender): preparar a cena, voltar ao repouso,
fechar o punho e fotografar. Importado pelos outros scripts (sys.path) dentro do Blender.

Convencao do modelo do usuario: o personagem olha para -Y, os ossos "esquerdo" ficam em -X (esquerda de quem
ve o personagem de frente) e os "direito" em +X."""
import math
import os
import re

import bpy
import numpy as np
from mathutils import Matrix, Vector

TEXTURA = r"C:\tmp\srb2-metal-homing\neo\pacote-blender\neo-metal\NEO_METAL.png"
LADOS = ("esquerdo", "direito")
DEDOS = ("indicador", "medio", "anelar", "mindinho", "polegar")


def preparar(tecido=False):
    """Arruma o caminho da textura, mostra a capa e liga/desliga a simulacao de tecido."""
    img = bpy.data.images.get("NEO_METAL.png")
    if img is not None and os.path.exists(TEXTURA):
        img.filepath = TEXTURA
        img.reload()
    capa = bpy.data.objects["capa"]
    capa.hide_set(False)
    capa.hide_viewport = False
    capa.hide_render = False
    for m in capa.modifiers:
        if m.type == "CLOTH":
            m.show_viewport = tecido
            m.show_render = tecido


def armadura():
    return bpy.data.objects["Armação"]


def repouso():
    for pb in armadura().pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)
    bpy.context.view_layer.update()


def _norm(nome):
    return nome.strip().lower()


def _numero(nome):
    m = re.search(r"(\d+)\s*$", _norm(nome))
    return int(m.group(1)) if m else 1


def cadeia(lado, dedo):
    """Ossos de um dedo, do mais proximo da palma ate a ponta."""
    osso = [pb for pb in armadura().pose.bones if dedo in _norm(pb.name) and lado in _norm(pb.name)]
    return sorted(osso, key=lambda pb: _numero(pb.name))


def _rot3(m4):
    return m4.to_3x3().normalized()


def curvar(cadeia_ossos, angulos_graus, eixo_arm):
    """Gira cada osso da cadeia em torno de um unico eixo (no espaco da armadura) pelo angulo dado.
    A rotacao local de cada osso e a conjugada da rotacao de mundo pelo repouso do osso, entao as
    articulacoes dobram na mesma direcao e o filho herda a dobra do pai."""
    eixo = Vector(eixo_arm).normalized()
    for pb, ang in zip(cadeia_ossos, angulos_graus):
        r_rep = _rot3(pb.bone.matrix_local)
        r_mundo = Matrix.Rotation(math.radians(ang), 3, eixo)
        local = r_rep.inverted() @ r_mundo @ r_rep
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = local.to_quaternion()
    bpy.context.view_layer.update()


def eixo_curva(cadeia_ossos, para_baixo=True):
    """Eixo horizontal, perpendicular ao dedo, em torno do qual um giro positivo leva a ponta para -Z."""
    base = cadeia_ossos[0].bone.head_local
    ponta = cadeia_ossos[-1].bone.tail_local
    d = Vector((ponta.x - base.x, ponta.y - base.y, 0.0))
    d.normalize()
    eixo = Vector((0, 0, 1)).cross(d)
    eixo.normalize()
    return eixo if para_baixo else -eixo


def ponta_mundo(pb):
    """Posicao de mundo da ponta (cauda) do osso na pose atual."""
    arm = armadura()
    return arm.matrix_world @ pb.tail


def mascarar_ossos(nomes, limiar=0.5):
    """So para fotografar: some com tudo que nao pesa pelo menos 'limiar' nos ossos dados (modificador Mask em memoria)."""
    obj = bpy.data.objects["NeoMetal"]
    idx = {g.index for g in obj.vertex_groups if g.name in nomes}
    vg = obj.vertex_groups.new(name="_mascara")
    vg.add([v.index for v in obj.data.vertices if sum(g.weight for g in v.groups if g.group in idx) >= limiar], 1.0, "REPLACE")
    mod = obj.modifiers.new("_mascara", "MASK")
    mod.vertex_group = "_mascara"


def camera_render(tam_x, tam_y, exposicao=1.0):
    sc = bpy.context.scene
    cd = bpy.data.cameras.new("cam_u")
    cd.type = "ORTHO"
    cd.clip_start = 0.1
    cd.clip_end = 500
    cam = bpy.data.objects.new("cam_u", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "STUDIO"
    sc.display.shading.color_type = "TEXTURE"
    sc.display.shading.show_cavity = False
    sc.display.render_aa = "8"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.exposure = exposicao
    sc.render.film_transparent = True
    sc.render.resolution_x = tam_x
    sc.render.resolution_y = tam_y
    sc.render.image_settings.color_mode = "RGBA"
    return cam, cd


def foto(cam, cd, caminho, alvo, direcao, escala):
    """Camera ortografica em 'alvo + direcao*60' olhando para o alvo."""
    alvo = Vector(alvo)
    d = Vector(direcao).normalized()
    cam.location = alvo + d * 60
    cam.rotation_euler = (alvo - cam.location).to_track_quat("-Z", "Y").to_euler()
    cd.ortho_scale = escala
    bpy.context.scene.render.filepath = caminho
    bpy.ops.render.render(write_still=True)


def caixa_mundo(objs=None):
    """Caixa envolvente (min, max) em mundo da malha avaliada com a pose atual."""
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for nome in objs or ("NeoMetal", "capa"):
        o = bpy.data.objects[nome]
        if o.hide_render:
            continue
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        pts.append(np.array([(o.matrix_world @ v.co)[:] for v in me.vertices]))
        ev.to_mesh_clear()
    a = np.vstack(pts)
    return a.min(axis=0), a.max(axis=0)
