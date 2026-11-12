"""Poses da mao do Neo (modelo do usuario). Como a mao funciona (aprendido em 31/10, com o punho aprovado):
- cada dedo tem o osso 1 (toco com a bola da junta, nunca gira) e os ossos 2, 3 e 4 (falange, falange e garra);
- cada junta dobra num plano vertical (eixo = lateral da mao) e as dobras se somam ao longo do dedo;
- o repouso e um leque: 'alinhar' (0 a 1) fecha o leque ate o dedo ficar paralelo ao eixo da mao e
  'abrir' abre o dedo para o lado (positivo = rumo ao polegar), girando o dedo inteiro em torno da junta da base;
- o polegar sai do pulso (nao do cubo dos dedos), tem 3 ossos longos e e posto por direcao-alvo de cada osso.
Uso dentro do Blender: import mao_poses as MP; MP.aplicar("esquerdo", MP.POSES["paz"])"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import punho_fechado as PF
import usuario_neo as U

Z = Vector((0.0, 0.0, 1.0))
LADO_POLEGAR = Vector((0.0, -1.0, 0.0))
DEDOS = PF.DEDOS

RETO = (0.0, 0.0, 0.0)
FECHADO = (90.0, 90.0, 60.0)
POLEGAR_PUNHO = PF.POLEGAR
POLEGAR_CIMA = ((0.0, 0.80, -0.60), (0.10, 0.30, -0.95), (0.35, 0.10, -0.93))


def ossos_da_mao(lado):
    ossos = [PF._palma(lado)]
    for nome in DEDOS + ("polegar",):
        ossos += U.cadeia(lado, nome)
    return ossos


def soltar(lado):
    for pb in ossos_da_mao(lado):
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1, 0, 0, 0)
    bpy.context.view_layer.update()


def dobrar_dedo(lado, nome, juntas=RETO, alinhar=1.0, abrir=0.0):
    """juntas: dobra RELATIVA (graus) das falanges 2, 3 e 4; alinhar: 0 = leque do repouso, 1 = paralelo ao eixo da mao;
    abrir: graus de abertura lateral, positivo rumo ao polegar."""
    palma = PF._palma(lado)
    d = PF._horizontal(palma.bone.tail_local - palma.bone.head_local)
    eixo = Z.cross(d).normalized()
    sinal = 1.0 if eixo.dot(LADO_POLEGAR) > 0 else -1.0
    cad = U.cadeia(lado, nome)
    assert len(cad) == len(juntas) + 1, (lado, nome, [pb.name for pb in cad])
    n_pai = Matrix.Identity(3)
    acum = 0.0
    for pb, j in zip(cad[1:], juntas):
        acum += j
        r_rep = PF._rot_osso(pb)
        rh = PF._horizontal(pb.bone.tail_local - pb.bone.head_local)
        psi = math.atan2(rh.cross(d).z, rh.dot(d))
        alfa = -(1.0 - alinhar) * psi + math.radians(abrir) * sinal
        n_i = Matrix.Rotation(alfa, 3, Z) @ Matrix.Rotation(math.radians(acum), 3, eixo) @ Matrix.Rotation(psi, 3, Z)
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (r_rep.inverted() @ n_pai.inverted() @ n_i @ r_rep).to_quaternion()
        n_pai = n_i
    bpy.context.view_layer.update()


def dobrar_polegar(lado, dirs, t=1.0):
    """dirs: (fora, frente, baixo) por osso; t interpola da direcao de repouso (0) ate a direcao-alvo (1)."""
    fora = Vector((-1.0, 0.0, 0.0)) if lado == "esquerdo" else Vector((1.0, 0.0, 0.0))
    pol = U.cadeia(lado, "polegar")
    assert len(pol) == len(dirs) == 3, [pb.name for pb in pol]
    for pb, (f, fr, b) in zip(pol, dirs):
        alvo = (fora * f + PF.FRENTE * fr + PF.BAIXO * b).normalized()
        repouso = (pb.bone.tail_local - pb.bone.head_local).normalized()
        PF.orientar(pb, repouso.slerp(alvo, t))


def aplicar(lado, pose, t=1.0):
    """pose: {"dedos": {nome: (juntas, alinhar, abrir)}, "polegar": dirs ou None}; t (0 a 1) vai do repouso ate a pose."""
    soltar(lado)
    for nome in DEDOS:
        juntas, alinhar, abrir = pose["dedos"].get(nome, (RETO, 0.0, 0.0))
        dobrar_dedo(lado, nome, tuple(j * t for j in juntas), alinhar * t, abrir * t)
    if pose.get("polegar"):
        dobrar_polegar(lado, pose["polegar"], t)


def _todos(juntas, alinhar=1.0, abrir=0.0):
    return {nome: (juntas, alinhar, abrir) for nome in DEDOS}


def _com(base, **mudancas):
    d = dict(base)
    d.update(mudancas)
    return d


_FECHADOS = _todos(FECHADO)
POSES = {
    "aberta": {"dedos": _todos(RETO, 0.0), "polegar": None},
    "espalmada": {"dedos": _todos(RETO, 1.0), "polegar": None},
    "punho": {"dedos": _FECHADOS, "polegar": POLEGAR_PUNHO},
    "relaxada": {"dedos": {"indicador": ((20, 25, 15), 0.5, 0), "medio": ((25, 30, 20), 0.5, 0),
                           "anelar": ((30, 35, 25), 0.5, 0), "mindinho": ((35, 40, 25), 0.5, 0)}, "polegar": None},
    "garra": {"dedos": _todos((35, 55, 40), 0.2), "polegar": None},
    "apontar": {"dedos": _com(_FECHADOS, indicador=(RETO, 1.0, 0.0)), "polegar": POLEGAR_PUNHO},
    "paz": {"dedos": _com(_FECHADOS, indicador=(RETO, 1.0, 10.0), medio=(RETO, 1.0, -8.0)), "polegar": POLEGAR_PUNHO},
    "rock": {"dedos": _com(_FECHADOS, indicador=(RETO, 1.0, 8.0), mindinho=(RETO, 1.0, -8.0)), "polegar": POLEGAR_PUNHO},
    "joinha": {"dedos": _FECHADOS, "polegar": POLEGAR_CIMA},
}
