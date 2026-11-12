"""Tronco, cabeca, bracos e pernas do Neo (modelo do usuario) por orientacao absoluta e alvo de mao/tornozelo, no estilo de perna_poses.py.
Como funciona:
- cada osso tem uma rotacao LIQUIDA N (eixos da armadura, relativa ao repouso): N_i = N_pai . Rest_i . B_i . Rest_i^-1, entao
  definir_liquida() poe a rotacao local B = Rest^-1 . N_pai^-1 . N_alvo . Rest e o osso fica com a orientacao pedida, seja qual for o pai;
- espinha e os dois quadris sao tres raizes com a cabeca no mesmo ponto (a pelve): girar as tres do mesmo jeito gira o corpo todo em torno
  da pelve, e a translacao da raiz (pose_corpo) leva o corpo inteiro;
- os dedos (mao_poses) ficam guardados relativos a palma e viajam com ela: fechar a mao ANTES de orientar o braco;
- o braco e ombro -> braco (haste fina de 0,3) -> antebraco (bola do cotovelo + manopla, 0,5) -> palma. No soco a HASTE FINA estica DEPOIS
  da pele (malha_posada): os vertices da haste alongam e tudo o que vem depois (bola do cotovelo, manopla, mao) so desliza junto pela
  direcao do osso do braco; as bolas das juntas nao viram elipsoide e vale com o braco reto ou dobrado.
Uso dentro do Blender: import braco_poses as BP; BP.preparar_esticar(); BP.pose_corpo(R, t); BP.pose_braco_alvo(...); co = BP.malha_posada({'direito': 0.9})"""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mao_poses as MP
import perna_poses as PP
import usuario_neo as U

CHAVE_LADO = PP.CHAVE_LADO
GRUPOS_BRACO = ("braco", "tovelo", "punho", "indicador", "medio", "anelar", "mindinho", "polegar")
GRUPOS_MAO = GRUPOS_BRACO[2:]
# faixa da haste fina do braco, em metros a partir da cabeca do osso do braco: antes fica a bola do ombro, depois a bola do cotovelo
HASTE_T0, HASTE_T1, HASTE_RAIO = 0.07, 0.235, 0.12
# a mesma coisa na coxa (quadril ate o joelho): antes fica a bola do quadril, depois a ponteira do joelho
COXA_T0, COXA_T1, COXA_RAIO = 0.07, 0.24, 0.07
# quanto da proporcao que a canela e o pe crescem a haste da coxa engrossa junto (1 = engrossa igual, 0 = fica fina como o tubo da perna do Sonic X)
ENGROSSAR_COXA = 0.5
# (parte, lado) -> (indices dos vertices, fator h de cada um); so a haste fina e o que vem depois dela se mexem, ombreira e espinhos da cabeca ficam como estao
ESTICA = {}


# ------------------------------------------------------------------ ossos
def osso(inicio=None, lado=None, contem=None):
    """Primeiro osso cujo nome sem acento comeca com 'inicio' (ou contem 'contem') e, se dado, e do lado (esquerdo/direito)."""
    for pb in U.armadura().pose.bones:
        n = PP._sem_acento(pb.name)
        if lado is not None and CHAVE_LADO[lado] not in n:
            continue
        if (inicio and n.startswith(inicio)) or (contem and contem in n):
            return pb
    raise KeyError((inicio, lado, contem))


def ossos_braco(lado):
    return {"ombro": osso("ombro", lado), "braco": osso("braco", lado), "antebraco": osso(None, lado, "tovelo"), "palma": osso("punho", lado)}


def raizes():
    return [osso("spine"), osso("quadril", "esquerdo"), osso("quadril", "direito")]


def tronco():
    return osso("spine")


def cabeca():
    return osso("head")


# ------------------------------------------------------------------ espacos e rotacoes
def _a3():
    return U.armadura().matrix_world.to_3x3()


def v_arm(v):
    """Vetor (direcao) de mundo para eixos da armadura."""
    return _a3().inverted() @ Vector(v)


def v_mundo(v):
    return _a3() @ Vector(v)


def p_arm(p):
    return U.armadura().matrix_world.inverted() @ Vector(p)


def p_mundo(p):
    return U.armadura().matrix_world @ Vector(p)


def r_arm(r):
    """Rotacao de mundo (3x3) para eixos da armadura."""
    a = _a3()
    return a.inverted() @ Matrix([[float(x) for x in linha] for linha in r]) @ a


def rot_rep(pb):
    return U._rot3(pb.bone.matrix_local)


def rot_liquida(pb):
    """Rotacao liquida atual do osso (eixos da armadura, relativa ao repouso)."""
    return U._rot3(pb.matrix) @ rot_rep(pb).inverted()


def definir_liquida(pb, n_alvo):
    n_pai = rot_liquida(pb.parent) if pb.parent else Matrix.Identity(3)
    r = rot_rep(pb)
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = (r.inverted() @ n_pai.inverted() @ Matrix([[float(x) for x in linha] for linha in n_alvo]) @ r).to_quaternion()
    bpy.context.view_layer.update()


def eixo_repouso(pb):
    """Direcao (cabeca -> cauda) do osso em repouso, eixos da armadura."""
    return (pb.bone.tail_local - pb.bone.head_local).normalized()


def menor_giro(de, para):
    return Vector(de).normalized().rotation_difference(Vector(para).normalized()).to_matrix()


# ------------------------------------------------------------------ corpo e cabeca
def zerar():
    U.repouso()


def pelve_mundo():
    """Ponto de mundo da pelve no repouso (cabeca da espinha e dos quadris)."""
    return p_mundo(tronco().bone.head_local)


def pose_corpo(r_mundo, t_mundo=(0, 0, 0)):
    """Gira o corpo todo (tres raizes) em torno da pelve pela rotacao de mundo r_mundo e depois translada por t_mundo."""
    r = r_arm(r_mundo)
    t = v_arm(t_mundo)
    for pb in raizes():
        definir_liquida(pb, r)
        pb.location = rot_rep(pb).inverted() @ t
    bpy.context.view_layer.update()


def pose_cabeca(r_mundo):
    definir_liquida(cabeca(), r_arm(r_mundo))


# ------------------------------------------------------------------ mao e haste esticavel
_PESOS = {}


def _pesos(lado, grupos, inicio=False):
    """Soma por vertice dos pesos nos grupos do lado cujo nome (sem acento) tem alguma das palavras dadas (guardada em cache).
    Com inicio=True a palavra tem que abrir o nome: o grupo do antebraco se chama '... ate o punho' e nao e da mao."""
    chave_cache = (lado, grupos, inicio)
    if chave_cache not in _PESOS:
        corpo = bpy.data.objects["NeoMetal"]
        chave = CHAVE_LADO[lado]
        casa = (lambda n, k: n.startswith(k)) if inicio else (lambda n, k: k in n)
        idx = {vg.index for vg in corpo.vertex_groups if chave in PP._sem_acento(vg.name) and any(casa(PP._sem_acento(vg.name), k) for k in grupos)}
        w = np.zeros(len(corpo.data.vertices))
        for v in corpo.data.vertices:
            for g in v.groups:
                if g.group in idx:
                    w[v.index] += g.weight
        _PESOS[chave_cache] = w
    return _PESOS[chave_cache]


_PESOS_NOMES = {}


def _pesos_nomes(nomes):
    """Soma por vertice dos pesos dos grupos com exatamente esses nomes (em cache)."""
    chave = tuple(nomes)
    if chave not in _PESOS_NOMES:
        corpo = bpy.data.objects["NeoMetal"]
        idx = {vg.index for vg in corpo.vertex_groups if vg.name in chave}
        w = np.zeros(len(corpo.data.vertices))
        for v in corpo.data.vertices:
            for g in v.groups:
                if g.group in idx:
                    w[v.index] += g.weight
        _PESOS_NOMES[chave] = w
    return _PESOS_NOMES[chave]


def _coords(obj):
    """Coordenadas de mundo da malha avaliada (pose atual, sem a haste esticada)."""
    ev = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = ev.to_mesh()
    a = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", a)
    ev.to_mesh_clear()
    m = np.array(obj.matrix_world)
    return a.reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]


def _selecao_haste(co, osso_haste, peso_haste, peso_depois, t0, t1, raio, peso_rigido=None):
    """Vertices que esticam ao longo do osso 'osso_haste' (em repouso): os da haste fina (peso_haste >= 0,5, entre t0 e t1 do eixo, perto dele)
    entram numa rampa de 0 a 1; os que vem depois (t >= t1 e peso_depois >= 0,5) so deslizam inteiros (h = 1).
    peso_rigido: pesos do que e rigido com tudo o que vem depois da haste; esses vertices deslizam inteiros mesmo com t < t1
    (a placa da canela passa do joelho para cima: sem isso a metade de cima fica na pelve e a placa vira uma lamina de 1 m)."""
    s = np.array(p_mundo(osso_haste.bone.head_local)[:])
    e = np.array(p_mundo(osso_haste.bone.tail_local)[:])
    u = (e - s) / np.linalg.norm(e - s)
    t = (co - s) @ u
    r = np.linalg.norm(co - s - np.outer(t, u), axis=1)
    rampa = np.clip((t - t0) / (t1 - t0), 0.0, 1.0)
    na_haste = (t > t0) & (t < t1) & (r < raio) & (peso_haste >= 0.5)
    depois = (t >= t1) & (peso_depois >= 0.5)
    if peso_rigido is not None:
        depois |= peso_rigido >= 0.5
        na_haste &= ~(peso_rigido >= 0.5)
    sel = np.where(na_haste | depois)[0]
    return (sel, np.where(depois[sel], 1.0, rampa[sel])), int(na_haste.sum()), int(depois.sum())


def preparar_esticar():
    """Com o corpo em repouso: acha, por parte (braco: haste do braco; perna: haste da coxa) e lado, os vertices da haste fina
    e os que ficam depois dela, com o fator h (0 a 1) de cada um. So eles esticam: ombreira, bolas das juntas e espinhos da cabeca nao."""
    corpo = bpy.data.objects["NeoMetal"]
    co = _coords(corpo)
    for lado in U.LADOS:
        peso = _pesos(lado, GRUPOS_BRACO)
        ESTICA[("braco", lado)], na_haste, depois = _selecao_haste(co, ossos_braco(lado)["braco"], peso, peso, HASTE_T0, HASTE_T1, HASTE_RAIO)
        print("haste do braco %s: %d vertices na rampa, %d depois dela" % (lado, na_haste, depois))
        o = PP.ossos_perna(lado)
        w_coxa = _pesos_nomes([o["coxa"].name])
        w_baixo = w_coxa + _pesos_nomes([o["canela"].name, o["pe_frente"].name, o["pe_tras"].name])
        w_rigido = _pesos_nomes([o["canela"].name, o["pe_frente"].name, o["pe_tras"].name])
        ESTICA[("perna", lado)], na_haste, depois = _selecao_haste(co, o["coxa"], w_coxa, w_baixo, COXA_T0, COXA_T1, COXA_RAIO, w_rigido)
        print("haste da coxa %s: %d vertices na rampa, %d depois dela" % (lado, na_haste, depois))
        indice_ponta_pe(lado)


def _osso_da_haste(parte, lado):
    return ossos_braco(lado)["braco"] if parte == "braco" else PP.ossos_perna(lado)["coxa"]


def _junta_depois_da_haste(parte, lado):
    """Osso logo depois da haste: o antebraco (cotovelo) no braco, a canela (joelho) na perna."""
    return ossos_braco(lado)["antebraco"] if parte == "braco" else PP.ossos_perna(lado)["canela"]


def _crescer_depois(co, parte, lado, fator, metros):
    """Tudo o que vem depois da haste (braco: bola do cotovelo, manopla e mao; perna: ponteira do joelho, canela e pe) cresce 'fator' por igual em torno
    da articulacao (cotovelo ou joelho): a manopla continua um cone com a mesma forma e a boca acompanha a mao, sem esticar para os lados.
    Chamar depois da haste esticada (metros = esticada dessa parte). O ponto que importa (centro da mao, ponta do pe) so cai no alvo se o membro foi
    posado levando 'fator' em conta: pose_braco_alvo(..., escala=fator) ou pose_perna_ponta(..., escala=fator)."""
    pb = _osso_da_haste(parte, lado)
    u = np.array((p_mundo(pb.tail) - p_mundo(pb.head)).normalized()[:])
    junta = np.array(p_mundo(_junta_depois_da_haste(parte, lado).head)[:]) + u * metros
    sel, h = ESTICA[(parte, lado)]
    depois = sel[h >= 1.0]
    co[depois] = junta + fator * (co[depois] - junta)
    return co


def _crescer_pe(co, lado, extra, fator_perna, metros):
    """O pe (calcanhar e ponta) cresce 'extra' vezes ALEM do que a perna ja cresceu, em torno do tornozelo (cabeca do osso da frente do pe): no chute o tenis do Dark Sonic
    fica muito maior que o anel da canela, que continua do tamanho de antes. O tornozelo esta onde _crescer_depois o deixou: joelho (esticado 'metros') + fator_perna * (tornozelo - joelho).
    Chamar depois de _crescer_depois. A ponta do pe so cai no alvo se o membro foi posado com pose_perna_ponta(..., extra_pe=extra)."""
    o = PP.ossos_perna(lado)
    u = np.array((p_mundo(o["coxa"].tail) - p_mundo(o["coxa"].head)).normalized()[:])
    joelho_sem = np.array(p_mundo(o["canela"].head)[:])
    tornozelo = joelho_sem + u * metros + fator_perna * (np.array(p_mundo(o["pe_frente"].head)[:]) - joelho_sem)
    pe = _pesos_nomes([o["pe_frente"].name, o["pe_tras"].name]) >= 0.5
    co[pe] = tornozelo + extra * (co[pe] - tornozelo)
    return co


def _engrossar_haste(co, parte, lado, fator):
    """A haste fina (do braco ou da coxa) engrossa em volta do proprio eixo, de 1 na origem ate 'fator' na articulacao (curva suave), para acompanhar
    o que vem depois dela e cresceu."""
    pb = _osso_da_haste(parte, lado)
    s = np.array(p_mundo(pb.head)[:])
    u = np.array((p_mundo(pb.tail) - p_mundo(pb.head)).normalized()[:])
    sel, h = ESTICA[(parte, lado)]
    na_haste = h < 1.0
    rel = co[sel[na_haste]] - s
    perp = rel - np.outer(rel @ u, u)
    suave = h[na_haste] ** 2 * (3.0 - 2.0 * h[na_haste])
    co[sel[na_haste]] += (fator - 1.0) * suave[:, None] * perp
    return co


def malha_posada(esticar=None, escala_mao=None, escala_perna=None, extra_pe=None):
    """Coordenadas de mundo da malha NeoMetal na pose atual, com as hastes esticadas: esticar = {(parte, lado): metros}, parte 'braco' ou 'perna'.
    escala_mao = {lado: fator}: o antebraco desse lado (bola do cotovelo, manopla e mao) cresce 'fator' por igual (_crescer_depois) e a haste
    do braco engrossa junto (_engrossar_haste). escala_perna = {lado: fator}: o mesmo para a perna (ponteira do joelho, canela e pe; haste da coxa).
    extra_pe = {lado: fator} (opcional): so o pe cresce mais 'fator' vezes em torno do tornozelo (_crescer_pe), alem de escala_perna (o chute)."""
    co = _coords(bpy.data.objects["NeoMetal"])
    for (parte, lado), metros in (esticar or {}).items():
        if abs(metros) < 1e-9:
            continue
        pb = _osso_da_haste(parte, lado)
        u = (p_mundo(pb.tail) - p_mundo(pb.head)).normalized()
        sel, h = ESTICA[(parte, lado)]
        co[sel] += np.outer(h, np.array(u[:])) * metros
    for parte, escalas, engrosso in (("braco", escala_mao, 1.0), ("perna", escala_perna, ENGROSSAR_COXA)):
        for lado, fator in (escalas or {}).items():
            if abs(fator - 1.0) > 1e-6:
                _engrossar_haste(co, parte, lado, 1.0 + (fator - 1.0) * engrosso)
                _crescer_depois(co, parte, lado, fator, (esticar or {}).get((parte, lado), 0.0))
    for lado, extra in (extra_pe or {}).items():
        if abs(extra - 1.0) > 1e-6:
            _crescer_pe(co, lado, extra, (escala_perna or {}).get(lado, 1.0), (esticar or {}).get(("perna", lado), 0.0))
    return co


def materializar(nome, coords_mundo=None, de="NeoMetal"):
    """Cria um objeto estatico (malha ja com a pose e, se dadas, as coordenadas de mundo com a haste esticada) para renderizar; devolve o objeto.
    'de' fornece UV e material; sem coords_mundo fica como a malha avaliada (pose atual)."""
    origem = bpy.data.objects[de]
    me = bpy.data.meshes.new_from_object(origem.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    if coords_mundo is not None:
        m = np.array(origem.matrix_world.inverted())
        loc = coords_mundo @ m[:3, :3].T + m[:3, 3]
        me.vertices.foreach_set("co", loc.ravel())
        me.update()
    obj = bpy.data.objects.new(nome, me)
    obj.matrix_world = origem.matrix_world.copy()
    bpy.context.scene.collection.objects.link(obj)
    return obj


def fechar_mao(lado, pose="punho"):
    """Poe a mao na pose da biblioteca mao_poses (padrao: o punho aprovado). Chamar ANTES de orientar o braco."""
    MP.aplicar(lado, MP.POSES[pose])


def centro_da_mao(lado):
    """Centroide de mundo dos vertices da mao (palma e dedos) na pose atual, sem a haste esticada."""
    corpo = bpy.data.objects["NeoMetal"]
    sel = _pesos(lado, GRUPOS_MAO, True) >= 0.5
    return Vector(_coords(corpo)[sel].mean(axis=0))


def medir_centro_mao(lado):
    """Vetor (eixos da armadura) do pulso (cabeca da palma) ate o centro da mao fechada, com o braco em repouso."""
    return v_arm(centro_da_mao(lado) - p_mundo(ossos_braco(lado)["palma"].bone.head_local))


# ------------------------------------------------------------------ IK
def ik_dois_ossos(s, w, a, b, polo, comprime_max=0.0):
    """Joelho/cotovelo E da cadeia s -> E (a) -> w (b), dobrando para o lado de 'polo'. Alem do alcance: cadeia reta, e devolve a folga.
    comprime_max (m, padrao 0 = como antes): ate essa distancia por DENTRO do alcance a cadeia tambem fica reta e o primeiro osso encolhe (folga negativa), em vez de dobrar o cotovelo."""
    d = w - s
    dist = d.length
    u = d / dist if dist > 1e-9 else Vector((0, 0, -1))
    if dist >= a + b - comprime_max - 1e-6:
        folga = dist - (a + b)
        return s + u * (a + min(folga, 0.0)), folga
    x = (dist * dist + a * a - b * b) / (2 * dist)
    h = math.sqrt(max(a * a - x * x, 0.0))
    p = Vector(polo) - Vector(polo).dot(u) * u
    p = p.normalized() if p.length > 1e-6 else u.orthogonal().normalized()
    return s + u * x + p * h, 0.0


def pose_braco_alvo(lado, alvo_mundo, n_mao_mundo, polo_mundo, c_mao, escala=1.0, comprime_max=0.0):
    """Poe o braco para o centro da mao fechada ficar em alvo_mundo, com a mao orientada por n_mao_mundo (rotacao liquida de mundo da palma).
    c_mao: vetor pulso->centro da mao (medir_centro_mao). polo_mundo: para onde o cotovelo aponta quando o braco dobra.
    escala: quanto malha_posada vai crescer o antebraco (bola do cotovelo, manopla e mao); o comprimento do osso e o vetor pulso->centro da mao entram
    multiplicados por ela, e assim o centro da mao cai no alvo e a haste do braco estica so o que sobra.
    comprime_max (m, padrao 0): a haste tambem pode ENCOLHER ate esse tanto para o braco ficar reto quando o punho pedido esta um pouco aquem do alcance (ver ik_dois_ossos).
    Retorna (quanto estica em metros, negativo se encolheu; cotovelo de mundo; pulso de mundo ja esticado)."""
    o = ossos_braco(lado)
    n_h = r_arm(n_mao_mundo)
    s = Vector(o["braco"].head)
    a, b = o["braco"].bone.length, o["antebraco"].bone.length * escala
    w = p_arm(alvo_mundo) - n_h @ (c_mao * escala)
    e, folga = ik_dois_ossos(s, w, a, b, v_arm(polo_mundo), comprime_max)
    u1 = (e - s).normalized()
    u2 = (e - s).normalized() if folga > 0 else (w - e).normalized()
    n_f = menor_giro(n_h @ eixo_repouso(o["antebraco"]), u2) @ n_h
    n_u = menor_giro(n_f @ eixo_repouso(o["braco"]), u1) @ n_f
    definir_liquida(o["braco"], n_u)
    definir_liquida(o["antebraco"], n_f)
    definir_liquida(o["palma"], n_h)
    return folga, p_mundo(e), p_mundo(w)


def pose_perna_cadeia(lado, joelho_mundo, dir_canela_mundo, n_pe_mundo, dir_quadril_mundo):
    """Perna em tres partes, como no Sonic X (o corpo ja precisa estar na pose):
    1) o quadril (osso solto da pelve) vira para dir_quadril_mundo, o que poe a bola do quadril no lado da pelve, no alto, e nao la embaixo;
    2) a haste da coxa (quadril ate o joelho) aponta para joelho_mundo e ESTICA se ele estiver mais longe que o comprimento natural;
    3) da ponteira do joelho para baixo (canela, placa e pe) tudo e rigido: a canela segue dir_canela_mundo e as duas metades do pe ficam com n_pe_mundo.
    Retorna (esticada da coxa em metros, direcao da coxa de mundo); o joelho so chega em joelho_mundo depois de malha_posada()."""
    o = PP.ossos_perna(lado)
    n_q0 = rot_liquida(o["quadril"])
    n_q = menor_giro(n_q0 @ eixo_repouso(o["quadril"]), v_arm(dir_quadril_mundo)) @ n_q0
    definir_liquida(o["quadril"], n_q)
    alvo = p_arm(joelho_mundo) - Vector(o["coxa"].head)
    u1 = alvo.normalized()
    n_c = menor_giro(n_q @ eixo_repouso(o["coxa"]), u1) @ n_q
    definir_liquida(o["coxa"], n_c)
    n_s = menor_giro(n_c @ eixo_repouso(o["canela"]), v_arm(dir_canela_mundo)) @ n_c
    definir_liquida(o["canela"], n_s)
    n_p = r_arm(n_pe_mundo)
    definir_liquida(o["pe_frente"], n_p)
    definir_liquida(o["pe_tras"], n_p)
    return max(0.0, alvo.length - o["coxa"].bone.length), v_mundo(u1)


_PONTA_PE = {}
# faixa (m) acima do ponto mais baixo do pe que conta como sola: a ponta do pe e o vertice mais a frente (-Y) dessa faixa, e nao o bico mais alto do cabedal
BANDA_SOLA = 0.06


def indice_ponta_pe(lado):
    """Indice do vertice da ponta do pe do Neo: o mais a frente (-Y) entre os do fundo da sola (BANDA_SOLA m acima do ponto mais baixo dos que pesam nos
    ossos do pe), achado com o corpo em repouso (em cache)."""
    if lado not in _PONTA_PE:
        o = PP.ossos_perna(lado)
        pe = np.where(_pesos_nomes([o["pe_frente"].name, o["pe_tras"].name]) >= 0.5)[0]
        p = _coords(bpy.data.objects["NeoMetal"])[pe]
        fundo = np.where(p[:, 2] < p[:, 2].min() + BANDA_SOLA)[0]
        _PONTA_PE[lado] = int(pe[fundo[np.argmin(p[fundo, 1])]])
    return _PONTA_PE[lado]


def pose_perna_ponta(lado, ponta_mundo, dir_canela_mundo, n_pe_mundo, dir_quadril_mundo, escala=1.0, comprime_max=0.0, extra_pe=1.0):
    """Como pose_perna_cadeia, mas em vez de levar o joelho a um ponto leva a PONTA DO PE do Neo (indice_ponta_pe) a ponta_mundo, com a canela e o pe
    crescidos 'escala' vezes por malha_posada(..., escala_perna): o joelho sai de ponta_mundo - escala * (joelho -> ponta com a canela e o pe ja na pose)
    e a haste da coxa estica o que for preciso para chegar la. Se o joelho cair mais perto do quadril que o comprimento natural da coxa, a haste encurta
    ate comprime_max metros (sem isso a coxa nao encolhe e o pe afunda alem da ponta pedida).
    extra_pe: o pe cresce mais essas vezes em torno do tornozelo (malha_posada(..., extra_pe)); o vetor tornozelo -> ponta entra multiplicado por ele (1 = como antes).
    Retorna (esticada da coxa em metros, negativa se encolheu; direcao da coxa de mundo; joelho de mundo pedido; falta, o que ainda faltou encolher alem de comprime_max)."""
    o = PP.ossos_perna(lado)
    joelho = Vector(p_mundo(o["canela"].head))
    for _ in range(3):
        pose_perna_cadeia(lado, joelho, dir_canela_mundo, n_pe_mundo, dir_quadril_mundo)
        joelho_pos = np.array(p_mundo(o["canela"].head)[:])
        tornozelo_pos = np.array(p_mundo(o["pe_frente"].head)[:])
        ponta_pos = _coords(bpy.data.objects["NeoMetal"])[indice_ponta_pe(lado)]
        joelho_ate_ponta = (tornozelo_pos - joelho_pos) + extra_pe * (ponta_pos - tornozelo_pos)
        joelho = Vector(np.array(Vector(ponta_mundo)[:]) - escala * joelho_ate_ponta)
    _, u = pose_perna_cadeia(lado, joelho, dir_canela_mundo, n_pe_mundo, dir_quadril_mundo)
    distancia = (p_arm(joelho) - Vector(o["coxa"].head)).length
    natural = o["coxa"].bone.length
    esticada = max(distancia - natural, -comprime_max)
    return esticada, u, joelho, max(0.0, natural - comprime_max - distancia)


def tornozelo_pedido(lado, ponta_mundo, escala=1.0, extra_pe=1.0):
    """Com a perna ja posada por pose_perna_ponta (o pe com a rotacao pedida): devolve (bola do quadril de mundo, tornozelo de mundo que leva a ponta do pe a ponta_mundo com o pe
    crescido escala x extra_pe, comprimento da canela crescida escala vezes). Serve para achar o joelho de uma perna reta: ele cai na reta quadril -> tornozelo, a canela antes do tornozelo."""
    o = PP.ossos_perna(lado)
    quadril = np.array(p_mundo(o["coxa"].head)[:])
    joelho_pos = np.array(p_mundo(o["canela"].head)[:])
    tornozelo_pos = np.array(p_mundo(o["pe_frente"].head)[:])
    ponta_pos = _coords(bpy.data.objects["NeoMetal"])[indice_ponta_pe(lado)]
    tornozelo = np.array(Vector(ponta_mundo)[:]) - escala * extra_pe * (ponta_pos - tornozelo_pos)
    return quadril, tornozelo, escala * float(np.linalg.norm(tornozelo_pos - joelho_pos))


def pose_perna_alvo(lado, alvo_mundo, n_pe_mundo, polo_mundo):
    """Perna com a bola do tornozelo o mais perto possivel de alvo_mundo (sem esticar; alem do alcance fica reta), pe rigido com
    n_pe_mundo (rotacao liquida de mundo das duas metades). O corpo ja precisa estar na pose. Retorna (joelho de mundo, tornozelo de mundo)."""
    o = PP.ossos_perna(lado)
    s = Vector(o["coxa"].head)
    a, b = o["coxa"].bone.length, o["canela"].bone.length
    alvo = p_arm(alvo_mundo)
    dist = (alvo - s).length
    minimo = abs(a - b) + 0.02
    if dist > a + b:
        alvo = s + (alvo - s).normalized() * (a + b)
    elif dist < minimo:
        alvo = s + (alvo - s).normalized() * minimo
    e, _ = ik_dois_ossos(s, alvo, a, b, v_arm(polo_mundo))
    u1 = (e - s).normalized()
    u2 = (alvo - e).normalized()
    n_q = rot_liquida(o["quadril"])
    n_c = menor_giro(n_q @ eixo_repouso(o["canela"]), u2) @ n_q
    n_t = menor_giro(n_c @ eixo_repouso(o["coxa"]), u1) @ n_c
    definir_liquida(o["coxa"], n_t)
    definir_liquida(o["canela"], n_c)
    n_p = r_arm(n_pe_mundo)
    definir_liquida(o["pe_frente"], n_p)
    definir_liquida(o["pe_tras"], n_p)
    return p_mundo(e), p_mundo(alvo)
