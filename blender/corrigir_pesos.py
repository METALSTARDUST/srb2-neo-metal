"""Corrige no modelo do usuario as pecas que ficaram sem nenhum peso (12 ilhas): elas nao acompanhavam o esqueleto.
Cada ilha vai para o osso do lugar onde ela esta encaixada; as ilhas que cruzam o joelho recebem um degrade
coxa -> canela para dobrarem junto com a perna. Nao mexe em nenhum peso que ja existia."""
import numpy as np

import bpy


def _grupo(corpo, trecho_a, trecho_b=None):
    """Grupo de vertices cujo nome (sem espacos nas pontas, minusculo) contem os trechos dados."""
    for vg in corpo.vertex_groups:
        n = vg.name.strip().lower()
        if trecho_a in n and (trecho_b is None or trecho_b in n):
            return vg
    raise KeyError((trecho_a, trecho_b))


def ilhas_sem_peso(corpo):
    me = corpo.data
    nv = len(me.vertices)
    sem = np.array([not any(ge.weight > 1e-4 for ge in v.groups) for v in me.vertices])
    pai = list(range(nv))

    def achar(a):
        while pai[a] != a:
            pai[a] = pai[pai[a]]
            a = pai[a]
        return a

    for e in me.edges:
        a, b = achar(e.vertices[0]), achar(e.vertices[1])
        if a != b:
            pai[a] = b
    raiz = np.array([achar(i) for i in range(nv)])
    mw = corpo.matrix_world
    co = np.array([(mw @ v.co)[:] for v in me.vertices])
    saida = []
    for r in np.unique(raiz):
        m = raiz == r
        if sem[m].all():
            idx = np.where(m)[0]
            saida.append((idx, co[idx]))
    return saida


def _componentes(corpo):
    """Raiz da ilha (peca conectada) de cada vertice e posicao de mundo dos vertices."""
    me = corpo.data
    nv = len(me.vertices)
    pai = list(range(nv))

    def achar(a):
        while pai[a] != a:
            pai[a] = pai[pai[a]]
            a = pai[a]
        return a

    for e in me.edges:
        a, b = achar(e.vertices[0]), achar(e.vertices[1])
        if a != b:
            pai[a] = b
    mw = corpo.matrix_world
    return np.array([achar(i) for i in range(nv)]), np.array([(mw @ v.co)[:] for v in me.vertices])


def fixar_bola_tornozelo(corpo=None, verbose=True):
    """A bola do tornozelo nao se mexe (so as duas metades do pe giram em torno dela, palavra do usuario). Ela e o eixo do
    tornozelo: um cone de cada lado, cada cone partido em duas metades (cima e baixo), 4 ilhas de 47 vertices por pe. Nos pesos
    dele as metades de fora estao 100% na ponta do pe e as de dentro misturam ponta, calcanhar e canela, entao a inclinacao
    parte o cone ao meio e o giro lateral ou a rolagem o arrastam; aqui as quatro passam a ser 100% da canela. As arruelas
    (placas e disco 50/50 ponta e calcanhar entre os cones) ficam como ele fez: seguem a media das duas metades."""
    corpo = corpo or bpy.data.objects["NeoMetal"]
    me = corpo.data
    arm = bpy.data.objects["Armação"]
    raiz, co = _componentes(corpo)
    feitos = []
    for lado, trecho in (("esquerdo", "joelho esquerdo ate"), ("direito", "joelho direito até")):
        canela = _grupo(corpo, trecho)
        bola = arm.matrix_world @ arm.data.bones[canela.name].tail_local
        for r in np.unique(raiz):
            idx = np.where(raiz == r)[0]
            if len(idx) != 47:
                continue
            c = co[idx].mean(axis=0)
            if abs(c[1] - bola.y) < 0.05 and abs(c[2] - bola.z) < 0.12 and 0.08 < abs(c[0] - bola.x) < 0.18:
                for i in idx:
                    for ge in list(me.vertices[int(i)].groups):
                        corpo.vertex_groups[ge.group].remove([int(i)])
                canela.add([int(i) for i in idx], 1.0, "REPLACE")
                feitos.append((lado, len(idx), tuple(round(float(x), 3) for x in c)))
    if verbose:
        for f in feitos:
            print("BOLA", f)
    return feitos


def corrigir(corpo=None, verbose=True):
    corpo = corpo or bpy.data.objects["NeoMetal"]
    grupos = {
        "head": _grupo(corpo, "head"),
        "spine": _grupo(corpo, "spine"),
        "braco_e": _grupo(corpo, "braço esquerdo"),
        "braco_d": _grupo(corpo, "braço direito"),
        "ind4_e": _grupo(corpo, "indicador esquerdo 4"),
        "coxa_e": _grupo(corpo, "perna esquerda"),
        "canela_e": _grupo(corpo, "joelho esquerdo ate"),
        "coxa_d": _grupo(corpo, "perna até o joelho direito"),
        "canela_d": _grupo(corpo, "joelho direito até"),
    }
    # altura do joelho em mundo: cabeca do osso da canela
    arm = bpy.data.objects["Armação"]
    z_joelho = {
        "e": (arm.matrix_world @ arm.data.bones[grupos["canela_e"].name].head_local).z,
        "d": (arm.matrix_world @ arm.data.bones[grupos["canela_d"].name].head_local).z,
    }
    feitos = []
    for idx, pts in ilhas_sem_peso(corpo):
        n = len(idx)
        c = pts.mean(axis=0)
        z = pts[:, 2]
        if c[2] < 1.3 and n <= 9:
            lado = "e" if c[0] < -0.05 else "d"
            zj = z_joelho[lado]
            for i, zi in zip(idx, z):
                t = float(np.clip((zj + 0.15 - zi) / 0.30, 0.0, 1.0))
                t = t * t * (3 - 2 * t)
                grupos["coxa_" + lado].add([int(i)], 1.0 - t, "REPLACE")
                grupos["canela_" + lado].add([int(i)], t, "REPLACE")
            destino = "coxa->canela " + lado
        elif n == 8 and c[0] < -1.5:
            grupos["ind4_e"].add([int(i) for i in idx], 1.0, "REPLACE")
            destino = "indicador esquerdo 4"
        elif n == 47 and c[0] < 0:
            grupos["braco_e"].add([int(i) for i in idx], 1.0, "REPLACE")
            destino = "braço esquerdo"
        elif n in (81, 33) and c[2] > 1.9:
            grupos["head"].add([int(i) for i in idx], 1.0, "REPLACE")
            destino = "head"
        elif n == 56:
            grupos["spine"].add([int(i) for i in idx], 1.0, "REPLACE")
            destino = "spine"
        else:
            raise RuntimeError("ilha sem regra: n=%d centro=%s" % (n, c))
        feitos.append((n, tuple(round(float(x), 2) for x in c), destino))
    if verbose:
        for f in feitos:
            print("PESO", f)
    fixar_bola_tornozelo(corpo, verbose)
    return feitos
