"""Perna e pe do Neo (modelo do usuario). Como a perna funciona:
- quadril (osso solto, raiz) -> coxa -> canela (joelho ate o pe, 0,8 de comprimento) -> dois ossos do pe;
- os dois ossos do pe nascem no MESMO ponto, a bola do tornozelo (cauda da canela), e abrem em "A" para a frente e para tras:
  um e a metade da frente (ponta do pe) e o outro e a metade de tras (calcanhar). Cada metade gira livremente em torno da bola
  (o pe do robo e articulado); a bola em si nao se mexe, fica presa a canela.
- o 1o/2o "vertice" do nome troca de lado entre as pernas, entao frente e calcanhar saem pela posicao (cauda em -Y = frente).
Uso dentro do Blender: import perna_poses as PP; PP.pe_elevacao("esquerdo", frente=0, tras=-42)"""
import math
import os
import sys
import unicodedata

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import usuario_neo as U

X = Vector((1.0, 0.0, 0.0))
Y = Vector((0.0, 1.0, 0.0))
Z = Vector((0.0, 0.0, 1.0))
CHAVE_LADO = {"esquerdo": "esquerd", "direito": "direit"}


def _sem_acento(nome):
    return "".join(c for c in unicodedata.normalize("NFD", nome) if unicodedata.category(c) != "Mn").strip().lower()


def ossos_perna(lado):
    """Dict com quadril, coxa, canela, pe_frente e pe_tras (PoseBone) do lado dado."""
    chave = CHAVE_LADO[lado]
    pes = [pb for pb in U.armadura().pose.bones if _sem_acento(pb.name).startswith("pe (") and chave in _sem_acento(pb.name)]
    assert len(pes) == 2, [pb.name for pb in pes]
    pes.sort(key=lambda pb: pb.bone.tail_local.y)
    frente, tras = pes
    canela = frente.parent
    coxa = canela.parent
    return {"quadril": coxa.parent, "coxa": coxa, "canela": canela, "pe_frente": frente, "pe_tras": tras}


def bola_tornozelo(lado):
    """Posicao de mundo da bola do tornozelo (onde nascem os dois ossos do pe) na pose atual."""
    return U.armadura().matrix_world @ ossos_perna(lado)["pe_frente"].head


def _rot_osso(pb):
    return U._rot3(pb.bone.matrix_local)


def girar(pb, eixo, graus):
    """Gira o osso em torno da sua propria cabeca, em torno de 'eixo' (eixos da armadura, acompanhando o pai):
    rotacao liquida N_i = N_pai . R(eixo, graus), entao as rotacoes em torno do mesmo eixo se somam pela cadeia."""
    r_rep = _rot_osso(pb)
    r = Matrix.Rotation(math.radians(graus), 3, Vector(eixo).normalized())
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = (r_rep.inverted() @ r @ r_rep).to_quaternion()
    bpy.context.view_layer.update()


CORES_PAPEL = {"quadril": (0.62, 0.30, 0.90), "coxa": (1.0, 0.82, 0.10), "canela": (0.15, 0.45, 1.0),
               "pe_frente": (1.0, 0.15, 0.10), "pe_tras": (0.10, 0.80, 0.20)}
CINZA = (0.74, 0.74, 0.76)


def pintar_pesos():
    """Diagnostico: cria a cor por vertice 'pesos_perna' (cada osso da perna uma cor, pesos mistos viram mistura, o resto cinza)
    e liga a vista por vertice do Workbench. So em memoria."""
    corpo = bpy.data.objects["NeoMetal"]
    me = corpo.data
    cor_do_grupo = {}
    for lado in U.LADOS:
        for papel, pb in ossos_perna(lado).items():
            cor_do_grupo[pb.name] = CORES_PAPEL[papel]
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
    bpy.context.scene.display.shading.color_type = "VERTEX"


def soltar_perna(lado):
    for pb in ossos_perna(lado).values():
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1, 0, 0, 0)
    bpy.context.view_layer.update()


def elevacao(pb, frente_e_menos_y):
    """Angulo (graus) do osso em relacao a horizontal no plano YZ: positivo = ponta acima da base.
    frente_e_menos_y: True para a metade da frente (a ponta aponta para -Y), False para o calcanhar (+Y)."""
    v = pb.tail - pb.head
    avanco = -v.y if frente_e_menos_y else v.y
    return math.degrees(math.atan2(v.z, avanco))


def inclinar_pe(lado, ponta=0.0, calcanhar=0.0, tornozelo=0.0):
    """Inclina as metades do pe em relacao a sola reta do repouso (graus). As solas ficam retas no repouso mesmo com os ossos
    em A (-42 graus), entao e a inclinacao da sola que importa: ponta/calcanhar positivos levantam aquela metade;
    'tornozelo' gira as duas metades juntas, como um pe rigido (positivo = bico para cima)."""
    o = ossos_perna(lado)
    girar(o["pe_frente"], X, -(ponta + tornozelo))
    girar(o["pe_tras"], X, calcanhar - tornozelo)


def girar_metade(lado, metade, eixo, graus):
    """Giro livre de uma metade do pe em torno da bola (metade: 'ponta' ou 'calcanhar'; eixo da armadura: X = inclinar,
    Z = abrir/fechar a ponta para o lado, Y = rolar sobre o eixo do pe). Positivo em Z leva a ponta (-Y) para +X."""
    o = ossos_perna(lado)
    girar(o["pe_frente" if metade == "ponta" else "pe_tras"], eixo, graus)


def pose_perna(lado, quadril=0.0, joelho=0.0, ponta=0.0, calcanhar=0.0, ponta_reta=True, calcanhar_reto=True):
    """Pose da perna toda. quadril: balanco da coxa (negativo = para a frente); joelho: dobra (positivo = canela para tras);
    ponta/calcanhar: inclinacao extra de cada metade do pe. Com ponta_reta/calcanhar_reto a metade compensa o giro da perna
    e fica com a sola na horizontal (pe plano no chao); desligado, ela acompanha a canela."""
    o = ossos_perna(lado)
    girar(o["coxa"], X, quadril)
    girar(o["canela"], X, joelho)
    giro = quadril + joelho
    girar(o["pe_frente"], X, -(ponta + (giro if ponta_reta else 0.0)))
    girar(o["pe_tras"], X, calcanhar - (giro if calcanhar_reto else 0.0))


def pe_elevacao(lado, frente=None, tras=None):
    """Poe cada metade do pe numa elevacao em relacao a horizontal (graus; negativo = ponta para baixo). None = nao mexe.
    No repouso as duas metades estao a uns -42 graus (um "A" simetrico sobre a bola)."""
    o = ossos_perna(lado)
    for chave, alvo, e_frente in (("pe_frente", frente, True), ("pe_tras", tras, False)):
        if alvo is None:
            continue
        pb = o[chave]
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1, 0, 0, 0)
        bpy.context.view_layer.update()
        atual = elevacao(pb, e_frente)
        delta = alvo - atual
        girar(pb, X, delta if not e_frente else -delta)
        # girar() usa o pai como referencia (a canela esta em repouso aqui); conferir depois com elevacao()
