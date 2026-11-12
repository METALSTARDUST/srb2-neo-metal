"""Soco do Dark Sonic (TAL1) com o Neo Metal: poe o Neo nos quadros do XSonic.md3 por cima de um fantasma do XSonic na escala do Neo.
Mapa referencia -> Neo: p_neo = K (p_ref - H_parado) + pelve_neo, com K = altura do Neo / altura do Sonic X parado e H_parado = meio dos quadris do
Sonic X parado (Super, quadro 219). O tronco gira em torno da pelve pela mesma rotacao do tronco do XSonic; a cabeca, a mao e os pes usam a rotacao
absoluta da peca rigida correspondente; bracos e pernas vao por alvo (IK), com a haste do braco esticando quando a mao esta alem do alcance.
Quadros: 277-280 (Super), 141-144 (forma normal: corpo igual, so a cabeca muda) e 219 (parado, so para conferir o encaixe da mao).
Pernas: a PONTA DO PE do Neo cai na ponta do tenis do XSonic (vertice mais a frente do fundo da sola); a canela e o pe crescem escala_perna vezes por igual
em torno do joelho e a haste da coxa estica (ou encolhe um pouco) para o joelho ficar onde a ponta pede. O Neo fica maior que o fantasma atras da ponta.
Corpo: com a ponta do pe presa e a canela maior, o joelho vai para tras e para cima; se a pelve ficasse na pelve do XSonic, a coxa sairia quase horizontal para
tras do corpo. Por isso o corpo todo (e as maos com ele, para o braco ficar como esta) anda por um vetor "desloca" por quadro: o necessario para cada coxa ficar
com escala_coxa x o comprimento natural e a direcao da coxa do XSonic (do joelho ao quadril), com os joelhos e as pontas dos pes onde ja estavam.
Tamanho: o Neo inteiro (corpo, cabeca, bracos, pernas e capa) fica escala_corpo vezes maior que o XSonic da cena, e as pontas dos pes continuam nas do tenis dele. A pose
e feita no tamanho natural do Neo; so as pontas dos pes pedem o XSonic encolhido 1/escala_corpo em torno da ancora de cada quadro (o meio das duas pontas de tenis do
XSonic: assim as pontas quase nao saem do lugar e o resto cresce em volta delas); pelve, maos e faixa seguem os mesmos alvos de antes, por isso o corpo fica proporcional.
No fim o Neo, a capa e a faixa sao ampliados escala_corpo vezes em torno da ancora (matrix_world) e o XSonic fica como estava. As medidas de pose (erros, joelho
atras/abaixo, graus) ficam no tamanho natural; as que comparam posicao com o XSonic (joelho ate a manopla, tornozelo ate o tenis, desloca_cena) saem nas unidades da cena.
Capa e cinto: alem do tamanho do corpo, o tecido da capa e o cinto (aro com tachas e a tira que pende) ficam escala_capa e escala_cinto vezes maiores, em torno do centro do aro do cinto
(onde a capa prende); o objeto 'capa' e dividido por componentes ligados da malha (o maior e o tecido; os pequenos e baixos sao o aro e as tachas; os compridos, a tira).
Closes do cinto, centrados no centro do aro: q<quadro>_neo_cinto / cinto34 (corpo so com o cinto) e cintocapa / cintocapa34 (com a capa inteira); o log e o JSON trazem a folga do aro ate o corpo.
Uso: blender -b golpes-neo/neo_base_pose.blend --python golpes_soco.py -- <saida_dir> <quadros q,q,q> <tam_px> [<mao_soco|-> [<escala_perna> [<escala_coxa|-> [<alinhar 1|0> [<escala_corpo|-> [<escala_capa|-> [<escala_cinto|->]]]]]]]
mao_soco (opcional, "-" = padrao): quantas vezes a mao e a manopla do Neo crescem no quadro do soco; sem ele vale o que a luva do XSonic cresce (1,73).
escala_perna (opcional): quantas vezes a canela e o pe do Neo crescem (padrao ESCALA_PERNA_PADRAO).
escala_coxa (opcional, "-" = igual a escala_perna): comprimento da coxa, em vezes o natural, que o corpo procura ao andar (a haste da coxa estica o que faltar).
alinhar (opcional, padrao 1): 0 deixa a pelve do Neo na pelve do XSonic (como na v6).
escala_corpo (opcional, "-" = padrao ESCALA_CORPO_PADRAO): quantas vezes o Neo inteiro fica maior que o XSonic na cena (1 = como a v7).
escala_capa (opcional, "-" = padrao ESCALA_CAPA_PADRAO): quantas vezes o tecido da capa fica maior alem do corpo (1 = como a v8).
escala_cinto (opcional, "-" = padrao ESCALA_CINTO_PADRAO = 1): o mesmo para o cinto (1 = o cinto fica do tamanho do corpo; so a capa cresce alem dele).
Ambiente: NEO_CAMERA_JSON = metricas_*.json de outra rodada (com "centros" e "escala_render"): usa a mesma camera dela, para comparar versoes pixel a pixel.
Saida: renders (fantasma com textura, fantasma liso, Neo com e sem capa, closes da mao, do braco e das pernas) por quadro e vista, metricas_<quadros>.json e cena_<quadros>.blend"""
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import braco_poses as BP
import golpes_ref as G
import perna_poses as PP
import usuario_neo as U

PASTA = r"C:\tmp\srb2-metal-homing\neo\golpes-neo"
TEXTURA_XSONIC = r"C:\tmp\srb2-metal-homing\habilidades-metal\modelos-celular\xsonic\XSONIC.png"
ALTURA_NEO = 2.71
PARADO_SUPER = 219
# quadros em que o braco que soca vira a faixa branca (luva + punho + haste esticados ao longo de -Y): a faixa entra copiada do XSonic e o braco do Neo some
QUADROS_RASTRO = {278, 142}
RASTRO_ILHAS = {0: [34, 35, 36, 37, 44, 47, 48, 49, 50, 52, 53, 54], 31: [14, 17, 18]}
# luva de cada lado no XSonic (superficie, ilhas): o tamanho dela no quadro, contra o do parado, diz quanto a mao do Neo cresce (no soco ela fica 1,73x)
LUVAS_REF = {"direito": (0, [44, 47, 48, 49, 50, 52, 53, 54]), "esquerdo": (27, [16, 17, 20, 21, 22, 24, 25, 26])}
# tenis de cada lado no XSonic (superficie, ilhas): a ponta dele e onde a ponta do pe do Neo tem que cair
TENIS_REF = {"direito": (0, [26, 27, 92, 93, 94]), "esquerdo": (27, [0, 1, 27, 28, 29])}
ESCALA_PERNA_PADRAO = 1.4
ESCALA_CORPO_PADRAO = 1.45
ESCALA_CAPA_PADRAO = 1.4
# o cinto (aro, tachas e tira) fica do tamanho que tinha com o corpo; so o tecido da capa cresce alem dele (pedido de 11/11: "o cinto e o cinto, fica do mesmo jeito, a capa aumenta")
ESCALA_CINTO_PADRAO = 1.0
# quanto a haste da coxa pode encurtar (m) quando o joelho pedido fica mais perto do quadril que a coxa natural
COMPRIME_COXA_MAX = 0.10
VISTAS = {"lado": Vector((-1.0, 0.0, 0.0)), "34": Vector((-0.62, -0.78, 0.18))}
COR_FANTASMA = (0.50, 0.58, 0.95)
I3 = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]

arg = sys.argv[sys.argv.index("--") + 1:]
SAIDA = os.path.abspath(arg[0])
QUADROS = [int(x) for x in arg[1].split(",")]
TAM = int(arg[2]) if len(arg) > 2 else 560
MAO_SOCO = float(arg[3]) if len(arg) > 3 and arg[3] != "-" else None
ESCALA_PERNA = float(arg[4]) if len(arg) > 4 else ESCALA_PERNA_PADRAO
ESCALA_COXA = float(arg[5]) if len(arg) > 5 and arg[5] != "-" else ESCALA_PERNA
ALINHAR = (arg[6] != "0") if len(arg) > 6 else True
ESCALA_CORPO = float(arg[7]) if len(arg) > 7 and arg[7] != "-" else ESCALA_CORPO_PADRAO
ESCALA_CAPA = float(arg[8]) if len(arg) > 8 and arg[8] != "-" else ESCALA_CAPA_PADRAO
ESCALA_CINTO = float(arg[9]) if len(arg) > 9 and arg[9] != "-" else ESCALA_CINTO_PADRAO
CAMERA = json.load(open(os.environ["NEO_CAMERA_JSON"])) if os.environ.get("NEO_CAMERA_JSON") else None
os.makedirs(SAIDA, exist_ok=True)

M = json.load(open(os.path.join(PASTA, "medidas", "soco_ref.json")))
K = ALTURA_NEO / M["altura"]
H_S = (np.array(M["quadril_parado"]["X"]) + np.array(M["quadril_parado"]["Y"])) / 2
CTP = np.array(M["tronco_parado_c"])
q_nomes, SUP = G.ler()


def dados_quadro(q):
    """Dados do quadro q: Super (277-280) vem do json; normal (141-144) e o mesmo corpo com a cabeca do quadro normal; 219 e o parado."""
    if q == PARADO_SUPER:
        p = M["parado"]
        return {"R_tronco": I3, "c_tronco": M["tronco_parado_c"], "R_cabeca": I3, "luva_P_c": p["luva_P"], "luva_Q_c": p["luva_Q"],
                "luva_P_ponta": p["luva_P"], "R_punho_P": I3, "R_luva_Q": I3, "quadril_X": M["quadril_parado"]["X"],
                "quadril_Y": M["quadril_parado"]["Y"], "c_canela_X": p["canela_X"], "c_canela_Y": p["canela_Y"], "c_tenis_X": p["tenis_X"],
                "c_tenis_Y": p["tenis_Y"], "R_tenis_X": I3, "R_tenis_Y": I3}
    if q < 200:
        d = dict(M["quadros"][str(q + 136)])
        d["R_cabeca"] = M["cabeca_normal"][str(q)]["R_cabeca"]
        return d
    return M["quadros"][str(q)]


# ------------------------------------------------------------------ cena
U.preparar()
BP.zerar()
for lado in U.LADOS:
    BP.fechar_mao(lado)
C_MAO = {lado: BP.medir_centro_mao(lado) for lado in U.LADOS}
NATURAL_NEO = {}
for lado in U.LADOS:
    o = BP.ossos_braco(lado)
    pulso = BP.p_mundo(o["palma"].bone.head_local)
    NATURAL_NEO[lado] = float((pulso + BP.v_mundo(C_MAO[lado]) - BP.p_mundo(o["braco"].bone.head_local)).length)
BP.zerar()
BP.preparar_esticar()
P_NEO = np.array(BP.pelve_mundo()[:])
print("K %.4f  pelve do Neo %s  alcance natural da mao fechada %s" % (K, P_NEO.round(3), {k: round(v, 3) for k, v in NATURAL_NEO.items()}))


def T(p):
    """Ponto do espaco do XSonic para o espaco do Neo."""
    return K * (np.asarray(p) - H_S) + P_NEO


ANCORA = np.zeros(3)


def fixar_ancora(q):
    """A ancora do quadro q (o ponto que nao se mexe quando o Neo cresce) e o meio das duas pontas de tenis do XSonic: assim as pontas dos pes mal saem do lugar com o
    corpo ampliado e o resto cresce em volta delas. (Uma ancora fixa no chao, sob a pelve, tirava as coxas do alinhamento do XSonic nos quadros de voo.)
    Muda ANCORA no lugar: T_pe, D e m_corpo leem o valor do quadro corrente."""
    ANCORA[:] = 0.5 * (T(ponta_tenis(q, "direito")) + T(ponta_tenis(q, "esquerdo")))


def m_corpo():
    """Matriz de mundo que amplia o Neo ESCALA_CORPO vezes em torno da ancora do quadro corrente."""
    return Matrix.Translation(Vector(ANCORA[:])) @ Matrix.Scale(ESCALA_CORPO, 4) @ Matrix.Translation(-Vector(ANCORA[:]))


def T_pe(p):
    """Como T, mas com o XSonic encolhido 1/ESCALA_CORPO em torno da ancora: onde a ponta do pe do Neo (no tamanho natural) tem que cair para, depois de o Neo ser
    ampliado ESCALA_CORPO vezes, coincidir com a ponta do tenis."""
    return ANCORA + (T(p) - ANCORA) / ESCALA_CORPO


def D(p):
    """Do espaco da pose (Neo no tamanho natural) para o da cena (Neo ESCALA_CORPO vezes maior em torno da ancora; o XSonic ja esta no espaco da cena)."""
    return ANCORA + ESCALA_CORPO * (np.asarray(p) - ANCORA)


# ------------------------------------------------------------------ fantasma (XSonic na escala do Neo)
def fantasma(q):
    """Objeto 'fantasma' com o quadro q do XSonic (so o que aparece) na escala do Neo; devolve (obj, pontos visiveis em mundo)."""
    vis = G.mascara_visivel(SUP, q)
    verts, faces, uvs, base, visiveis = [], [], [], 0, []
    for s, mv in zip(SUP, vis):
        p = T(s["pos"][q].reshape(-1, 3)).reshape(-1, 3)
        verts.append(p)
        visiveis.append(p[mv])
        ok = mv[s["tris"]].all(axis=1)
        for a, b, c in s["tris"][ok].tolist():
            faces.append((base + a, base + c, base + b))
        uvs.append(s["st"])
        base += len(p)
    verts, uvs = np.vstack(verts), np.vstack(uvs)
    me = bpy.data.meshes.new("fantasma")
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    uv = me.uv_layers.new(name="UV")
    for lp in me.loops:
        s_, t_ = uvs[lp.vertex_index]
        uv.data[lp.index].uv = (s_, 1.0 - t_)
    for p in me.polygons:
        p.use_smooth = True
    mat = bpy.data.materials.get("fantasma_mat")
    if mat is None:
        mat = bpy.data.materials.new("fantasma_mat")
        mat.use_nodes = True
        nos = mat.node_tree.nodes
        nos.clear()
        saida_no = nos.new("ShaderNodeOutputMaterial")
        principled = nos.new("ShaderNodeBsdfPrincipled")
        tex = nos.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(TEXTURA_XSONIC)
        tex.interpolation = "Closest"
        mat.node_tree.links.new(tex.outputs["Color"], principled.inputs["Base Color"])
        mat.node_tree.links.new(principled.outputs["BSDF"], saida_no.inputs["Surface"])
    me.materials.append(mat)
    obj = bpy.data.objects.new("fantasma", me)
    bpy.context.scene.collection.objects.link(obj)
    return obj, np.vstack(visiveis)


ILHAS_SUP = {s: G.componentes(SUP[s]["pos"].shape[1], SUP[s]["tris"]) for s in RASTRO_ILHAS}
ILHAS_LUVA = {s: G.componentes(SUP[s]["pos"].shape[1], SUP[s]["tris"]) for s, _ in LUVAS_REF.values()}


def indice_ponta_tenis(lado):
    """Indice (na superficie) do vertice da ponta do tenis do XSonic: o mais a frente (-Y) do fundo da sola no parado Super (mesma definicao da ponta do pe do Neo)."""
    s, ilhas = TENIS_REF[lado]
    idx = np.where(np.isin(ILHAS_LUVA[s], ilhas))[0]
    p = T(SUP[s]["pos"][PARADO_SUPER][idx])
    fundo = np.where(p[:, 2] < p[:, 2].min() + BP.BANDA_SOLA)[0]
    return int(idx[fundo[np.argmin(p[fundo, 1])]])


PONTA_TENIS = {lado: indice_ponta_tenis(lado) for lado in U.LADOS}


def ponta_tenis(q, lado):
    """Ponta do tenis do XSonic desse lado no quadro q (espaco do XSonic)."""
    return SUP[TENIS_REF[lado][0]]["pos"][q][PONTA_TENIS[lado]]


def pontos_tenis(q, lado):
    """Vertices do tenis do XSonic desse lado no quadro q, no espaco do Neo."""
    s, ilhas = TENIS_REF[lado]
    return T(SUP[s]["pos"][q][np.isin(ILHAS_LUVA[s], ilhas)])


def extensoes(pontos, R):
    """Largura, comprimento e altura (m) de um conjunto de pontos nos eixos de um pe de rotacao R (x lateral, y para a frente, z para cima)."""
    local = np.asarray(pontos) @ np.asarray(R)
    return (local.max(axis=0) - local.min(axis=0)).tolist()


def escala_luva(q, lado):
    """Quanto a luva do XSonic do lado dado cresce no quadro q em relacao ao parado Super (raio medio dos vertices em torno do centro; 1,0 = igual)."""
    s, ilhas = LUVAS_REF[lado]
    sel = np.isin(ILHAS_LUVA[s], ilhas)

    def raio(f):
        p = SUP[s]["pos"][f][sel]
        return float(np.sqrt(((p - p.mean(axis=0)) ** 2).sum(axis=1).mean()))
    return raio(q) / raio(PARADO_SUPER)


def escala_mao(q, lado):
    """Quanto a mao do Neo desse lado cresce no quadro q: o que a luva do XSonic cresce ou, na mao que soca, o valor de MAO_SOCO (se dado).
    O braco P vira a faixa nos quadros de rastro, entao la fica 1,0."""
    fator = escala_luva(q, lado)
    if lado == "direito" and q in QUADROS_RASTRO:
        return 1.0
    if MAO_SOCO is not None and lado == "direito" and fator > 1.001:
        return MAO_SOCO
    return fator


def rastro(q, desloca=(0.0, 0.0, 0.0)):
    """Objeto com a faixa branca do quadro q: so as ilhas de RASTRO_ILHAS (triangulos visiveis), na escala do Neo e com a textura do XSonic,
    andando junto com o corpo do Neo (desloca)."""
    desloca = np.asarray(desloca, dtype=float)
    vis = G.mascara_visivel(SUP, q)
    verts, faces, uvs, base = [], [], [], 0
    for s, ilhas in RASTRO_ILHAS.items():
        sf = SUP[s]
        no_grupo = np.isin(ILHAS_SUP[s], ilhas) & vis[s]
        tris = sf["tris"][no_grupo[sf["tris"]].all(axis=1)]
        usados, inv = np.unique(tris, return_inverse=True)
        verts.append(T(sf["pos"][q][usados]).reshape(-1, 3) + desloca)
        uvs.append(sf["st"][usados])
        for a, b, c in (inv.reshape(-1, 3) + base).tolist():
            faces.append((a, c, b))
        base += len(usados)
    verts, uvs = np.vstack(verts), np.vstack(uvs)
    me = bpy.data.meshes.new("rastro")
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    uv = me.uv_layers.new(name="UV")
    for lp in me.loops:
        s_, t_ = uvs[lp.vertex_index]
        uv.data[lp.index].uv = (s_, 1.0 - t_)
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(bpy.data.materials["fantasma_mat"])
    obj = bpy.data.objects.new("rastro", me)
    bpy.context.scene.collection.objects.link(obj)
    return obj, verts


# ------------------------------------------------------------------ pose do Neo
def rot_y(graus):
    return Matrix.Rotation(math.radians(graus), 3, Vector((0, 1, 0)))


def angulos(r):
    """Mesmas definicoes de golpes_medidas.angulos_tronco: inclinacao para a frente (-Y), para o lado (+X), total e giro da frente em torno da vertical."""
    cima, frente = np.asarray(r) @ np.array([0, 0, 1.0]), np.asarray(r) @ np.array([0, -1.0, 0])
    return {"frente": math.degrees(math.atan2(-cima[1], cima[2])), "lado": math.degrees(math.atan2(cima[0], cima[2])),
            "total": math.degrees(math.acos(max(-1.0, min(1.0, cima[2])))), "giro": math.degrees(math.atan2(frente[0], -frente[1]))}


def _posar_em(q, d, escala_mao, escala_perna, desloca):
    """Uma passada da pose: o corpo todo na pelve do XSonic mais 'desloca' (vetor de mundo); as maos vao para o alvo do XSonic mais 'desloca' (o braco fica como estava);
    os pes ficam presos nas pontas dos tenis do XSonic (nao andam com o corpo) e a haste da coxa estica ou encolhe o que o joelho pedir."""
    BP.zerar()
    for lado in U.LADOS:
        BP.fechar_mao(lado)
    R = np.array(d["R_tronco"])
    hips_f = R @ (H_S - CTP) + np.array(d["c_tronco"])
    BP.pose_corpo(R, K * (hips_f - H_S) + desloca)
    BP.pose_cabeca(np.array(d["R_cabeca"]))
    info = {"R": R, "esticar": {}, "alvo_mao": {}, "perna": {}, "desloca": np.asarray(desloca, dtype=float)}
    cima = Vector((R @ np.array([0, 0, 1.0]))[:])
    for lado, suf, rot_ref, sinal in (("direito", "P", "R_punho_P", +90), ("esquerdo", "Q", "R_luva_Q", -90)):
        alvo = T(d["luva_%s_c" % suf]) + desloca
        n_h = Matrix(d[rot_ref]) @ rot_y(sinal)
        polo = -cima + Vector((0, 0.5, 0))
        folga, cotovelo, pulso = BP.pose_braco_alvo(lado, Vector(alvo[:]), n_h, polo, C_MAO[lado], escala_mao[lado])
        info["esticar"][("braco", lado)] = folga
        info["alvo_mao"][lado] = alvo
    pelve = T(hips_f)
    info["pelve_ref"] = pelve
    for lado, suf in (("direito", "X"), ("esquerdo", "Y")):
        quadril, joelho_ref, tenis, ponta = T(d["quadril_" + suf]), T(d["c_canela_" + suf]), T(d["c_tenis_" + suf]), T_pe(ponta_tenis(q, lado))
        esticada, u, joelho, falta = BP.pose_perna_ponta(lado, Vector(ponta[:]), Vector((tenis - joelho_ref)[:]), np.array(d["R_tenis_" + suf]),
                                                         Vector((quadril - pelve)[:]), escala_perna[lado], COMPRIME_COXA_MAX)
        info["esticar"][("perna", lado)] = esticada
        info["perna"][lado] = {"quadril": quadril, "joelho": np.array(joelho[:]), "joelho_ref": joelho_ref, "tenis": tenis, "ponta": ponta,
                               "ponta_ref": T(ponta_tenis(q, lado)), "u_coxa": np.array(u[:]), "falta": falta,
                               "quadril_neo": np.array(BP.p_mundo(PP.ossos_perna(lado)["coxa"].head)[:])}
    return info


def deslocamento_do_corpo(info, escala_coxa):
    """Vetor de mundo (m) que leva o corpo do Neo (e a bola do quadril de cada lado com ele) para onde as duas coxas ficam com escala_coxa x o comprimento natural,
    apontando como a coxa do XSonic (do joelho ao quadril), a partir dos joelhos pedidos, que nao dependem de onde esta a pelve. Media dos dois lados."""
    passos = []
    for lado in U.LADOS:
        p = info["perna"][lado]
        u = p["quadril"] - p["joelho_ref"]
        u = u / np.linalg.norm(u)
        quadril_pedido = p["joelho"] + escala_coxa * PP.ossos_perna(lado)["coxa"].bone.length * u
        passos.append(quadril_pedido - p["quadril_neo"])
    return np.mean(passos, axis=0)


def posar(q, d, escala_mao, escala_perna, escala_coxa, alinhar=True):
    """Poe o Neo na pose do quadro q (dados d). escala_mao: quanto o antebraco de cada lado cresce, com manopla e mao; o cotovelo recua para o centro da mao crescida chegar no alvo.
    escala_perna: quanto a canela e o pe de cada lado crescem; a ponta do pe cai na ponta do tenis do XSonic e o joelho vai para onde isso pede.
    alinhar: depois da primeira passada (corpo na pelve do XSonic) o corpo anda o necessario para as coxas ficarem como a do XSonic (ver deslocamento_do_corpo) e a pose
    e refeita; os joelhos e as pontas dos pes nao mudam, so o resto do corpo e as maos.
    Devolve o que foi pedido: esticar por lado, alvos, comprimentos, direcoes das pernas e o deslocamento do corpo (desloca)."""
    info = _posar_em(q, d, escala_mao, escala_perna, np.zeros(3))
    if alinhar:
        info = _posar_em(q, d, escala_mao, escala_perna, deslocamento_do_corpo(info, escala_coxa))
    return info


def medir_neo(q, info, d):
    """Medidas do Neo na pose do quadro q (mesmas definicoes das medidas do XSonic) e o erro em relacao ao alvo. Devolve (malha em mundo, dict)."""
    co = BP.malha_posada(info["esticar"], info.get("escala_mao"), info.get("escala_perna"))
    a3 = np.array(BP._a3())
    liq_mundo = lambda pb: a3 @ np.array(BP.rot_liquida(pb)) @ a3.T
    Rt, Rc = liq_mundo(BP.tronco()), liq_mundo(BP.cabeca())
    out = {"tronco": angulos(Rt), "cabeca_rel": angulos(Rt.T @ Rc), "bracos": {}, "pernas": {}, "desloca": info["desloca"].tolist()}
    frente_t, cima_t = info["R"] @ np.array([0, -1.0, 0]), info["R"] @ np.array([0, 0, 1.0])

    def atras_abaixo(de, para):
        """Quanto 'para' fica atras e abaixo de 'de' (m), nos eixos do tronco."""
        v = np.asarray(para) - np.asarray(de)
        return [float(-(v @ frente_t)), float(-(v @ cima_t))]
    for lado, suf in (("direito", "P"), ("esquerdo", "Q")):
        mao = co[BP._pesos(lado, BP.GRUPOS_MAO, True) >= 0.5]
        centro = mao.mean(axis=0)
        ombro = np.array(BP.p_mundo(BP.ossos_braco(lado)["braco"].head)[:])
        ponta = mao[np.argmax(np.linalg.norm(mao - ombro, axis=1))]
        b = {"alcance": float(np.linalg.norm(centro - ombro)), "natural": NATURAL_NEO[lado], "centro": centro.tolist(), "ponta": ponta.tolist(),
             "ombro": ombro.tolist(), "alvo": info["alvo_mao"][lado].tolist(), "erro_centro": float(np.linalg.norm(centro - info["alvo_mao"][lado])),
             "esticou": info["esticar"][("braco", lado)], "luva_local": (Rt.T @ (centro - ombro)).tolist()}
        if suf == "P":
            b["erro_ponta"] = float(np.linalg.norm(ponta - (T(d["luva_P_ponta"]) + info["desloca"])))
        out["bracos"][suf] = b
    for lado, suf in (("direito", "X"), ("esquerdo", "Y")):
        o = PP.ossos_perna(lado)
        alvo, esticada = info["perna"][lado], info["esticar"][("perna", lado)]
        fator = (info.get("escala_perna") or {}).get(lado, 1.0)
        haste = alvo["u_coxa"] * esticada
        quadril = np.array(BP.p_mundo(o["coxa"].head)[:])
        joelho_sem = np.array(BP.p_mundo(o["canela"].head)[:])
        joelho = joelho_sem + haste
        tornozelo = joelho + fator * (np.array(BP.p_mundo(o["pe_frente"].head)[:]) - joelho_sem)
        eixo_neo, eixo_ref = tornozelo - joelho, alvo["tenis"] - alvo["joelho_ref"]
        cos = float(eixo_neo @ eixo_ref / np.linalg.norm(eixo_neo) / np.linalg.norm(eixo_ref))
        R_pe = np.array(d["R_tenis_" + suf])
        ponta = co[BP.indice_ponta_pe(lado)]
        pe_neo = co[BP._pesos_nomes([o["pe_frente"].name, o["pe_tras"].name]) >= 0.5]
        pe_ref = pontos_tenis(q, lado)
        eixo_pe_neo, eixo_pe_ref = ponta - pe_neo.mean(axis=0), alvo["ponta_ref"] - pe_ref.mean(axis=0)
        cos_pe = float(eixo_pe_neo @ eixo_pe_ref / np.linalg.norm(eixo_pe_neo) / np.linalg.norm(eixo_pe_ref))
        u_neo, u_ref = quadril - joelho, alvo["quadril"] - alvo["joelho_ref"]
        angulo_coxa = math.degrees(math.acos(max(-1.0, min(1.0, float(u_neo @ u_ref / np.linalg.norm(u_neo) / np.linalg.norm(u_ref))))))
        out["pernas"][suf] = {"quadril": quadril.tolist(), "quadril_ref": alvo["quadril"].tolist(),
                              "erro_quadril": float(np.linalg.norm(quadril - (alvo["quadril"] + info["desloca"]))),
                              "atras_abaixo_neo": atras_abaixo(quadril, joelho), "atras_abaixo_ref": atras_abaixo(alvo["quadril"], alvo["joelho_ref"]),
                              "angulo_coxa": angulo_coxa,
                              "joelho": joelho.tolist(), "erro_joelho": float(np.linalg.norm(joelho - alvo["joelho"])),
                              "joelho_ate_manopla": float(np.linalg.norm(D(joelho) - alvo["joelho_ref"])),
                              "ponta": ponta.tolist(), "ponta_alvo": alvo["ponta"].tolist(), "erro_ponta": float(np.linalg.norm(ponta - alvo["ponta"])),
                              "coxa_natural": float(o["coxa"].bone.length), "coxa_esticada": float(o["coxa"].bone.length + esticada),
                              "esticou": esticada, "falta": float(alvo["falta"]), "tornozelo": tornozelo.tolist(),
                              "tornozelo_ao_tenis": float(np.linalg.norm(D(tornozelo) - alvo["tenis"])),
                              "angulo_canela": math.degrees(math.acos(max(-1.0, min(1.0, cos)))),
                              "pe_neo": extensoes(pe_neo, R_pe), "pe_ref": extensoes(pe_ref, R_pe),
                              "inclinacao_pe_neo": math.degrees(math.asin(max(-1.0, min(1.0, eixo_pe_neo[2] / np.linalg.norm(eixo_pe_neo))))),
                              "inclinacao_pe_ref": math.degrees(math.asin(max(-1.0, min(1.0, eixo_pe_ref[2] / np.linalg.norm(eixo_pe_ref))))),
                              "angulo_pe": math.degrees(math.acos(max(-1.0, min(1.0, cos_pe))))}
    return co, out


# ------------------------------------------------------------------ renders
sc = bpy.context.scene
cam, cd = U.camera_render(TAM, TAM, 1.0)
corpo, capa = bpy.data.objects["NeoMetal"], bpy.data.objects["capa"]


def partes_da_capa():
    """Indices de vertice do objeto 'capa' por parte, pelos componentes ligados da malha em repouso: tecido (o maior), aro do cinto (aro e tachas: baixos) e tira que pende
    (alta e fina, na frente). Devolve (tecido, aro, tira)."""
    me = capa.data
    n = len(me.vertices)
    pai = list(range(n))

    def achar(a):
        while pai[a] != a:
            pai[a] = pai[pai[a]]
            a = pai[a]
        return a
    for p in me.polygons:
        vs = list(p.vertices)
        for v in vs[1:]:
            ra, rb = achar(vs[0]), achar(v)
            if ra != rb:
                pai[rb] = ra
    raiz = np.array([achar(i) for i in range(n)])
    mw = np.array(capa.matrix_world)
    co = np.empty(n * 3)
    me.vertices.foreach_get("co", co)
    z = (co.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3])[:, 2]
    componentes = [np.flatnonzero(raiz == r) for r in np.unique(raiz)]
    tecido = max(componentes, key=len)
    aro, tira = [], []
    for c in componentes:
        if c is not tecido:
            (aro if np.ptp(z[c]) < 0.25 * np.ptp(z[tecido]) else tira).extend(c.tolist())
    return tecido, np.array(sorted(aro)), np.array(sorted(tira))


TECIDO_CAPA, ARO_CAPA, TIRA_CAPA = partes_da_capa()
print("capa: tecido %d vertices, aro e tachas do cinto %d, tira do cinto %d; capa x%.2f, cinto x%.2f alem do corpo x%.2f" % (
    len(TECIDO_CAPA), len(ARO_CAPA), len(TIRA_CAPA), ESCALA_CAPA, ESCALA_CINTO, ESCALA_CORPO))


def ampliar_capa(obj):
    """Poe a capa posada (obj, no tamanho natural) na cena: o corpo ampliado ESCALA_CORPO em torno da ancora (D) e, em cima disso, o tecido ESCALA_CAPA vezes e o cinto
    ESCALA_CINTO vezes maiores em torno do centro do aro do cinto (onde a capa prende). Grava os vertices (obj.matrix_world nao muda).
    Devolve (vertices em mundo na cena, centro do aro na cena)."""
    me = obj.data
    mw = np.array(obj.matrix_world)
    local = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", local)
    pose = local.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]
    pivo = D(pose[ARO_CAPA].mean(axis=0))
    fator = np.full(len(pose), ESCALA_CAPA)
    fator[ARO_CAPA] = fator[TIRA_CAPA] = ESCALA_CINTO
    cena = pivo + fator[:, None] * (D(pose) - pivo)
    inv = np.array(obj.matrix_world.inverted())
    me.vertices.foreach_set("co", (cena @ inv[:3, :3].T + inv[:3, 3]).ravel())
    me.update()
    return cena, pivo


def separar_cinto(capa_pose, nome):
    """Copia o cinto (aro, tachas e tira) da capa ja ampliada para um objeto proprio, sem o tecido: serve para ver o cinto sozinho contra o corpo."""
    copia = capa_pose.copy()
    copia.data = capa_pose.data.copy()
    copia.name = nome
    bpy.context.scene.collection.objects.link(copia)
    bm = bmesh.new()
    bm.from_mesh(copia.data)
    bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in TECIDO_CAPA], context="VERTS")
    bm.to_mesh(copia.data)
    bm.free()
    return copia


def folga_do_cinto(aro_cena, corpo_cena):
    """Distancia (m, na cena) de cada vertice do aro do cinto ao vertice mais proximo do corpo: mostra se o cinto continua justo na cintura ou virou um arco solto."""
    menores = np.empty(len(aro_cena))
    for i in range(0, len(aro_cena), 32):
        bloco = aro_cena[i:i + 32]
        menores[i:i + 32] = np.sqrt(((bloco[:, None, :] - corpo_cena[None, :, :]) ** 2).sum(axis=2)).min(axis=1)
    return menores


def render(caminho, centro, escala, direcao, modo):
    sc.display.shading.color_type = modo
    if modo == "SINGLE":
        sc.display.shading.single_color = COR_FANTASMA
    U.foto(cam, cd, caminho, centro, direcao, escala)


def limpar(nome):
    o = bpy.data.objects.get(nome)
    if o is not None:
        me = o.data
        bpy.data.objects.remove(o)
        bpy.data.meshes.remove(me)


resultado = {"K": K, "H_S": H_S.tolist(), "pelve_neo": P_NEO.tolist(), "altura_neo": ALTURA_NEO, "natural_neo": NATURAL_NEO, "escala_corpo": ESCALA_CORPO, "quadros": {}}
print("escala do corpo x%.2f: o Neo fica com %.2f m de altura em repouso na cena, o XSonic com %.2f m; ancora de cada quadro = meio das pontas dos tenis do XSonic" % (
    ESCALA_CORPO, ALTURA_NEO * ESCALA_CORPO, ALTURA_NEO))
caixas = {}
for q in QUADROS:
    fixar_ancora(q)
    d = dados_quadro(q)
    escala = {lado: escala_mao(q, lado) for lado in U.LADOS}
    escala_pe = {lado: ESCALA_PERNA for lado in U.LADOS}
    info = posar(q, d, escala, escala_pe, ESCALA_COXA, ALINHAR)
    info["escala_mao"] = escala
    info["escala_perna"] = escala_pe
    co, med = medir_neo(q, info, d)
    ghost, pts_f = fantasma(q)
    ghost.name = "fantasma_%d" % q
    if q in QUADROS_RASTRO:
        co = co.copy()
        ombro_p = np.array(BP.p_mundo(BP.ossos_braco("direito")["braco"].head)[:])
        co[BP._pesos("direito", BP.GRUPOS_BRACO, True) >= 0.5] = ombro_p
        faixa, verts_faixa = rastro(q, info["desloca"])
        faixa.name = "rastro_%d" % q
        faixa.matrix_world = m_corpo() @ faixa.matrix_world
        med["bracos"]["P"]["erro_ponta"] = med["bracos"]["P"]["erro_centro"] = None
    neo_pose = BP.materializar("NeoPose_%d" % q, co)
    neo_pose.matrix_world = m_corpo() @ neo_pose.matrix_world
    capa_pose = BP.materializar("CapaPose_%d" % q, None, de="capa")
    capa_cena, pivo_capa = ampliar_capa(capa_pose)
    separar_cinto(capa_pose, "CintoPose_%d" % q)
    folga = folga_do_cinto(capa_cena[ARO_CAPA], D(co))
    todos = np.vstack([D(co), pts_f, capa_cena] + ([D(verts_faixa)] if q in QUADROS_RASTRO else []))
    caixas[q] = (todos.min(axis=0), todos.max(axis=0))
    desloca_cena = (ESCALA_CORPO - 1.0) * (info["pelve_ref"] - ANCORA) + ESCALA_CORPO * info["desloca"]
    resultado["quadros"][q] = {"medidas_neo": med, "esticar": {"%s_%s" % chave: v for chave, v in info["esticar"].items()}, "escala_mao": info["escala_mao"],
                               "escala_perna": info["escala_perna"], "escala_coxa": ESCALA_COXA, "alinhar": ALINHAR, "desloca": info["desloca"].tolist(),
                               "desloca_cena": desloca_cena.tolist(), "ancora": ANCORA.tolist(), "escala_capa": ESCALA_CAPA, "escala_cinto": ESCALA_CINTO,
                               "pivo_capa": pivo_capa.tolist(), "caixa_capa": [capa_cena.min(axis=0).tolist(), capa_cena.max(axis=0).tolist()],
                               "folga_cinto": {"minima": float(folga.min()), "mediana": float(np.median(folga)), "maxima": float(folga.max())},
                               "caixa_tecido": [capa_cena[TECIDO_CAPA].min(axis=0).tolist(), capa_cena[TECIDO_CAPA].max(axis=0).tolist()]}

ESC = CAMERA["escala_render"] if CAMERA else max(float((mx - mn).max()) for mn, mx in caixas.values()) * 1.12
ESC_MAO = 1.8  # largura (m) do close da mao que soca, centrado no alvo da mao
ESC_CINTO = 1.9  # largura (m, tamanho natural) do close do cinto, centrado no centro do aro
corpo.hide_render = capa.hide_render = True
resultado["centros"] = {}
for q in QUADROS:
    fixar_ancora(q)
    mn, mx = caixas[q]
    centro = Vector(CAMERA["centros"][str(q)]) if CAMERA else Vector(((mn + mx) / 2)[:])
    resultado["centros"][q] = list(centro)
    for o in bpy.data.objects:
        if o.name.startswith(("fantasma_", "NeoPose_", "CapaPose_", "CintoPose_", "rastro_")):
            o.hide_render = True
    faixa = bpy.data.objects.get("rastro_%d" % q)
    bpy.data.objects["fantasma_%d" % q].hide_render = False
    for nome, direcao in VISTAS.items():
        render(os.path.join(SAIDA, "q%03d_ref_%s.png" % (q, nome)), centro, ESC, direcao, "TEXTURE")
        render(os.path.join(SAIDA, "q%03d_fantasma_%s.png" % (q, nome)), centro, ESC, direcao, "SINGLE")
    bpy.data.objects["fantasma_%d" % q].hide_render = True
    bpy.data.objects["NeoPose_%d" % q].hide_render = False
    bpy.data.objects["CapaPose_%d" % q].hide_render = False
    if faixa is not None:
        faixa.hide_render = False
    for nome, direcao in VISTAS.items():
        render(os.path.join(SAIDA, "q%03d_neo_%s.png" % (q, nome)), centro, ESC, direcao, "TEXTURE")
    bpy.data.objects["CapaPose_%d" % q].hide_render = True
    for nome, direcao in VISTAS.items():
        render(os.path.join(SAIDA, "q%03d_neosocapa_%s.png" % (q, nome)), centro, ESC, direcao, "TEXTURE")
    # close do cinto: o corpo com so o cinto (cinto, cinto34) e com a capa inteira (cintocapa, cintocapa34), centrado no centro do aro; a mesma camera para todos os fatores
    pivo_v = Vector(resultado["quadros"][q]["pivo_capa"])
    for objeto, sufixos in (("CintoPose_%d" % q, {"lado": "cinto", "34": "cinto34"}), ("CapaPose_%d" % q, {"lado": "cintocapa", "34": "cintocapa34"})):
        bpy.data.objects[objeto].hide_render = False
        for nome, direcao in VISTAS.items():
            render(os.path.join(SAIDA, "q%03d_neo_%s.png" % (q, sufixos[nome])), pivo_v, ESC_CINTO * ESCALA_CORPO, direcao, "TEXTURE")
        bpy.data.objects[objeto].hide_render = True
    alvo_p = Vector(resultado["quadros"][q]["medidas_neo"]["bracos"]["P"]["alvo"])
    desloca_v = Vector(resultado["quadros"][q]["desloca"])
    sufixo_mao = {"lado": "mao", "34": "mao34"}
    esc_mao = ESC_MAO * ESCALA_CORPO
    for nome, direcao in VISTAS.items():
        render(os.path.join(SAIDA, "q%03d_neo_%s.png" % (q, sufixo_mao[nome])), Vector(D(np.array(alvo_p[:]))[:]), esc_mao, direcao, "TEXTURE")
    bpy.data.objects["NeoPose_%d" % q].hide_render = True
    if faixa is not None:
        faixa.hide_render = True
    bpy.data.objects["fantasma_%d" % q].hide_render = False
    for nome, direcao in VISTAS.items():
        render(os.path.join(SAIDA, "q%03d_ref_%s.png" % (q, sufixo_mao[nome])), alvo_p - desloca_v, esc_mao, direcao, "TEXTURE")
    # close do braco que soca inteiro (do ombro ate a mao), de lado: confere a haste, o cotovelo e a manopla contra a referencia
    ombro_p = Vector(resultado["quadros"][q]["medidas_neo"]["bracos"]["P"]["ombro"])
    esc_braco = max((alvo_p - ombro_p).length * 1.3 * ESCALA_CORPO, 1.6)
    render(os.path.join(SAIDA, "q%03d_ref_braco.png" % q), (alvo_p + ombro_p) / 2 - desloca_v, esc_braco, VISTAS["lado"], "TEXTURE")
    bpy.data.objects["fantasma_%d" % q].hide_render = True
    bpy.data.objects["NeoPose_%d" % q].hide_render = False
    if faixa is not None:
        faixa.hide_render = False
    render(os.path.join(SAIDA, "q%03d_neo_braco.png" % q), Vector(D(np.array(((alvo_p + ombro_p) / 2)[:]))[:]), esc_braco, VISTAS["lado"], "TEXTURE")
    # close das pernas (do quadril aos pes, de lado e 3/4): o Neo contra o fantasma
    m = resultado["quadros"][q]["medidas_neo"]
    pontos_pernas = np.array([p for suf in ("X", "Y") for p in (D(m["pernas"][suf]["quadril"]), m["pernas"][suf]["quadril_ref"],
                                                                 D(m["pernas"][suf]["ponta_alvo"]), D(m["pernas"][suf]["ponta"]))])
    centro_pernas = Vector(((pontos_pernas.min(axis=0) + pontos_pernas.max(axis=0)) / 2)[:])
    esc_pernas = max(float((pontos_pernas.max(axis=0) - pontos_pernas.min(axis=0)).max()) * 1.5, 2.4)
    if CAMERA and "pernas_cam" in CAMERA:
        centro_pernas, esc_pernas = Vector(CAMERA["pernas_cam"][str(q)]["centro"]), CAMERA["pernas_cam"][str(q)]["escala"]
    resultado.setdefault("pernas_cam", {})[q] = {"centro": list(centro_pernas), "escala": esc_pernas}
    sufixo_pernas = {"lado": "pernas", "34": "pernas34"}
    bpy.data.objects["NeoPose_%d" % q].hide_render = True
    if faixa is not None:
        faixa.hide_render = True
    bpy.data.objects["fantasma_%d" % q].hide_render = False
    for nome, direcao in VISTAS.items():
        render(os.path.join(SAIDA, "q%03d_ref_%s.png" % (q, sufixo_pernas[nome])), centro_pernas, esc_pernas, direcao, "TEXTURE")
    bpy.data.objects["fantasma_%d" % q].hide_render = True
    bpy.data.objects["NeoPose_%d" % q].hide_render = False
    if faixa is not None:
        faixa.hide_render = False
    for nome, direcao in VISTAS.items():
        render(os.path.join(SAIDA, "q%03d_neo_%s.png" % (q, sufixo_pernas[nome])), centro_pernas, esc_pernas, direcao, "TEXTURE")
    fmt = lambda v: "-" if v is None else "%.3f" % v
    print("quadro %d  esticou %s  mao cresce %s  erro centro P %s Q %s  erro ponta P %s%s" % (
        q, {k: round(v, 2) for k, v in resultado["quadros"][q]["esticar"].items()}, {k: round(v, 2) for k, v in resultado["quadros"][q]["escala_mao"].items()},
        fmt(m["bracos"]["P"]["erro_centro"]), fmt(m["bracos"]["Q"]["erro_centro"]),
        fmt(m["bracos"]["P"]["erro_ponta"]), "  (braco P trocado pela faixa)" if q in QUADROS_RASTRO else ""))
    print("   corpo anda (tamanho natural, mundo) %s = %.2f m; na cena (Neo x%.2f) a pelve do Neo fica %s = %.2f m da pelve do XSonic" % (
        np.round(m["desloca"], 3), np.linalg.norm(m["desloca"]), ESCALA_CORPO, np.round(resultado["quadros"][q]["desloca_cena"], 3),
        np.linalg.norm(resultado["quadros"][q]["desloca_cena"])))
    caixa_t = resultado["quadros"][q]["caixa_tecido"]
    print("   capa x%.2f e cinto x%.2f (alem do corpo): tecido na cena x %.2f..%.2f  y %.2f..%.2f  z %.2f..%.2f; centro do aro %s" % (
        ESCALA_CAPA, ESCALA_CINTO, caixa_t[0][0], caixa_t[1][0], caixa_t[0][1], caixa_t[1][1], caixa_t[0][2], caixa_t[1][2],
        np.round(resultado["quadros"][q]["pivo_capa"], 3)))
    fg = resultado["quadros"][q]["folga_cinto"]
    print("   folga do aro do cinto ate o corpo (m, na cena): minima %.3f mediana %.3f maxima %.3f" % (fg["minima"], fg["mediana"], fg["maxima"]))
    for suf in ("X", "Y"):
        pn = m["pernas"][suf]
        print("   perna %s (pe x%.2f): ponta do pe %.3f quadril %.3f joelho %.3f (ate a manopla %.2f) coxa %.2f -> %.2f falta %.3f canela %.1f graus" % (
            suf, ESCALA_PERNA, pn["erro_ponta"], pn["erro_quadril"], pn["erro_joelho"], pn["joelho_ate_manopla"], pn["coxa_natural"], pn["coxa_esticada"],
            pn["falta"], pn["angulo_canela"]))
        print("      joelho atras/abaixo do quadril (m): Neo %s  XSonic %s  coxa do Neo difere %.0f graus da do XSonic" % (
            np.round(pn["atras_abaixo_neo"], 2), np.round(pn["atras_abaixo_ref"], 2), pn["angulo_coxa"]))
        print("      pe do Neo (largo x comprido x alto) %s  tenis do XSonic %s  eixo do pe (calcanhar -> ponta) sobe %.0f graus no Neo e %.0f no XSonic, diferenca %.0f graus" % (
            np.round(pn["pe_neo"], 2), np.round(pn["pe_ref"], 2), pn["inclinacao_pe_neo"], pn["inclinacao_pe_ref"], pn["angulo_pe"]))

resultado["escala_render"] = ESC
etiqueta = "_".join(str(q) for q in QUADROS)
json.dump(resultado, open(os.path.join(SAIDA, "metricas_%s.json" % etiqueta), "w"), indent=1, default=float)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(SAIDA, "cena_%s.blend" % etiqueta))
print("ok", SAIDA, "escala", round(ESC, 2))
