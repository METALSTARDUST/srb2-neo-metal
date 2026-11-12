"""Punho fechado do Neo (modelo do usuario). As maos ficam com a palma para baixo (-Z) no repouso, entao
dobrar os dedos para baixo fecha a mao.

Dedos (v2): os quatro ficam PARALELOS, retos, com dobras bem marcadas no mesmo plano (o desenho do usuario):
o osso 1 de cada dedo e so o toco/bola do nocaute e nao gira; as tres falanges (ossos 2, 3 e 4) primeiro se
alinham com o eixo da mao (fecham o leque do repouso) e depois dobram por angulos acumulados em torno do eixo
lateral da mao: 90 (desce reta), 180 (volta rumo ao pulso, paralela a palma) e 240 (a garra sobe para a palma).

O polegar e posto por direcoes-alvo (fora = rumo dos dedos, frente = -Y, baixo = -Z), uma por osso, e foi
aprovado pelo usuario na v1."""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import usuario_neo as U

Z = Vector((0.0, 0.0, 1.0))
FRENTE = Vector((0.0, -1.0, 0.0))
BAIXO = Vector((0.0, 0.0, -1.0))

DEDOS = ("indicador", "medio", "anelar", "mindinho")
# angulo acumulado (graus, a partir da direcao da mao) das falanges 1, 2 e 3 (garra)
CURVA = (90.0, 180.0, 240.0)
# (fora, frente, baixo) por osso do polegar: sai da base para a frente e para baixo, cruza a frente do punho
POLEGAR = ((0.0, 0.857, 0.514), (0.987, 0.0, 0.158), (0.97, -0.24, 0.0))


def _horizontal(v):
    h = Vector((v.x, v.y, 0.0))
    h.normalize()
    return h


def _rot_osso(pb):
    return U._rot3(pb.bone.matrix_local)


def orientar(pb, direcao):
    """Aponta o osso para 'direcao' (espaco da armadura) pela menor rotacao a partir da pose herdada do pai."""
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = (1, 0, 0, 0)
    bpy.context.view_layer.update()
    p0 = pb.matrix.to_3x3().normalized()
    atual = (p0 @ Vector((0, 1, 0))).normalized()
    rw = atual.rotation_difference(Vector(direcao).normalized()).to_matrix()
    pb.rotation_quaternion = (p0.inverted() @ rw @ p0).to_quaternion()
    bpy.context.view_layer.update()


def _palma(lado):
    for pb in U.armadura().pose.bones:
        n = U._norm(pb.name)
        if n.startswith("punho") and lado in n:
            return pb
    raise KeyError(lado)


def fechar_dedos(lado, curva=None):
    """Alinha cada falange com o eixo da mao e dobra pelos angulos acumulados em 'curva' (um por falange)."""
    curva = curva or CURVA
    palma = _palma(lado)
    d = _horizontal(palma.bone.tail_local - palma.bone.head_local)
    eixo = Z.cross(d).normalized()
    for nome in DEDOS:
        cad = U.cadeia(lado, nome)
        assert len(cad) == len(curva) + 1, (lado, nome, [pb.name for pb in cad])
        n_pai = Matrix.Identity(3)
        for pb, phi in zip(cad[1:], curva):
            r_rep = _rot_osso(pb)
            rh = _horizontal(pb.bone.tail_local - pb.bone.head_local)
            psi = math.atan2(rh.cross(d).z, rh.dot(d))
            n_i = Matrix.Rotation(math.radians(phi), 3, eixo) @ Matrix.Rotation(psi, 3, Z)
            pb.rotation_mode = "QUATERNION"
            pb.rotation_quaternion = (r_rep.inverted() @ n_pai.inverted() @ n_i @ r_rep).to_quaternion()
            n_pai = n_i
    bpy.context.view_layer.update()


def fechar_polegar(lado, polegar=None):
    polegar = polegar or POLEGAR
    fora = Vector((-1.0, 0.0, 0.0)) if lado == "esquerdo" else Vector((1.0, 0.0, 0.0))
    pol = U.cadeia(lado, "polegar")
    assert len(pol) == len(polegar) == 3, [pb.name for pb in pol]
    for pb, (f, fr, b) in zip(pol, polegar):
        orientar(pb, fora * f + FRENTE * fr + BAIXO * b)


def fechar_mao(lado, curva=None, polegar=None):
    fechar_dedos(lado, curva)
    fechar_polegar(lado, polegar)


def aplicar(**kw):
    for lado in U.LADOS:
        fechar_mao(lado, **kw)
