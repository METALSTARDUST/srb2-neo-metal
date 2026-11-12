"""Mede o chute (TAL2) do Dark Sonic no XSONIC.md3: forma Super (quadros 273-276) e normal (137-140), sem bpy (Python do Blender: so numpy).
Mesmo formato de golpes_medidas.py (soco): tudo em unidades do modelo (Blender = MD3 * 0,1) e em fracao da altura do personagem parado.
Pecas rigidas (tronco, cabeca, punhos, luva Q, canelas) seguem o ajuste rigido (Kabsch) a partir do quadro parado. O TENIS e a CANELA (o anel cinza do tornozelo)
CRESCEM no chute (o tenis fica enorme), entao seguem o ajuste de semelhanca (Umeyama: rotacao + escala + residuo) e as razoes por eixo do pe parado.
Alem do formato do soco, cada quadro traz esc_tenis_X/Y e esc_canela_X/Y (quanto a peca cresce), a haste da coxa (tubo) e as extensoes por eixo.
Uso: python golpes_medidas_chute.py <saida.json> <saida.txt>"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

import golpes_ref as G

PARADO_SUPER, PARADO_NORMAL = 219, 5
SUPER = [273, 274, 275, 276]
NORMAL = [137, 138, 139, 140]
NOMES = "ABCD"
QUADRO_OMBRO = 279  # quadro do soco com o braco P esticado: de la saem os ombros (nao existem no modelo), como em golpes_medidas.py

RIGIDOS = {
    "cabeca": [(0, [10])],
    "tronco": [(0, [96, 97, 98, 99])],
    "punho_P": [(0, [34, 35, 36, 37])],
    "punho_Q": [(27, [8, 9, 10, 11])],
    "luva_Q": [(27, [16, 17, 20, 21, 22, 24, 25, 26])],
    "tenis_X": [(0, [26, 27, 92, 93, 94])],
    "tenis_Y": [(27, [0, 1, 27, 28, 29])],
    "canela_X": [(0, [38, 39, 40, 41])],
    "canela_Y": [(27, [12, 13, 14, 15])],
}
LUVA_P = [(0, [44, 47, 48, 49, 50, 52, 53, 54])]
TUBOS = {"haste_P": [(31, [14, 17, 18])], "haste_Q": [(32, [1, 3, 4])], "tubo_X": [(0, [101, 104, 105])], "tubo_Y": [(27, [31, 33, 34])]}
# pecas que crescem no chute: ajuste de semelhanca
CRESCEM = ("tenis_X", "tenis_Y", "canela_X", "canela_Y")
# pecas pequenas do anel da canela que tambem se esticam no quadro C (ilhas 103, 106, 107 do s00; 32, 35, 36 do s27): so para a tabela
ANEL_EXTRA = {"X": [(0, [102, 103, 106, 107])], "Y": [(27, [30, 32, 35, 36])]}

q_nomes, sup = G.ler()
ilha = {i: G.componentes(sup[i]["pos"].shape[1], sup[i]["tris"]) for i in (0, 27, 31, 32)}


def pts(grupo, f):
    return np.concatenate([sup[s]["pos"][f][np.isin(ilha[s], il)] for s, il in grupo])


def kabsch(a, b):
    """R, ca, cb, residuo tais que b - cb = R (a - ca)."""
    ca, cb = a.mean(0), b.mean(0)
    u, _, vt = np.linalg.svd((a - ca).T @ (b - cb))
    d = np.sign(np.linalg.det(vt.T @ u.T))
    r = vt.T @ np.diag([1, 1, d]) @ u.T
    return r, ca, cb, float(np.sqrt((((a - ca) @ r.T + cb - b) ** 2).sum(1).mean()))


def umeyama(a, b):
    """R, s, ca, cb, residuo tais que b - cb = s R (a - ca): rotacao e UMA escala uniforme (a peca cresce por igual)."""
    ca, cb = a.mean(0), b.mean(0)
    aa, bb = a - ca, b - cb
    u, d, vt = np.linalg.svd(bb.T @ aa / len(a))
    sinal = np.eye(3)
    sinal[2, 2] = np.sign(np.linalg.det(u) * np.linalg.det(vt))
    r = u @ sinal @ vt
    s = float((d * np.diag(sinal)).sum() / (aa ** 2).sum(1).mean())
    return r, s, ca, cb, float(np.sqrt((((s * aa @ r.T) - bb) ** 2).sum(1).mean()))


def graus(rad):
    return math.degrees(rad)


def angulos_tronco(r):
    """Inclinacao do eixo 'para cima' do tronco: para a frente (-Y), para o lado (+X) e total; giro da frente do tronco em torno da vertical."""
    cima, frente = r @ np.array([0, 0, 1.0]), r @ np.array([0, -1.0, 0])
    return {"frente": graus(math.atan2(-cima[1], cima[2])), "lado": graus(math.atan2(cima[0], cima[2])),
            "total": graus(math.acos(max(-1, min(1, cima[2])))), "giro": graus(math.atan2(frente[0], -frente[1]))}


def haste(p):
    """Tubo (3 tiras): eixo principal, extremos, comprimento, largura e espessura (extensoes nos outros dois eixos)."""
    c = p.mean(0)
    _, _, vt = np.linalg.svd(p - c)
    eixo = vt[0]
    t = (p - c) @ vt.T
    ext = t.max(0) - t.min(0)
    return {"eixo": eixo, "p0": c + eixo * t[:, 0].min(), "p1": c + eixo * t[:, 0].max(), "comprimento": float(ext[0]),
            "largura": float(ext[1]), "espessura": float(ext[2]), "centro": c}


def vet(v):
    return [round(float(x), 5) for x in v]


def extensoes_no_pe_parado(p_parado, p_quadro, r, ca, cb):
    """Extensoes (x, y, z do pe parado) de uma peca no quadro, desfazendo a rotacao r: (p - cb) @ r leva ao sistema da peca parada. Devolve [razoes por eixo] e as extensoes."""
    loc_p = (p_parado - ca)
    loc_q = (p_quadro - cb) @ r
    e_p, e_q = loc_p.max(0) - loc_p.min(0), loc_q.max(0) - loc_q.min(0)
    return (e_q / e_p).tolist(), e_p.tolist(), e_q.tolist()


# ---------------------------------------------------------------- altura e quadro parado
estado = {}
for nome, parado in (("normal", PARADO_NORMAL), ("super", PARADO_SUPER)):
    cab = pts(RIGIDOS["cabeca"], parado)
    mv = G.mascara_visivel(sup, parado)
    todos = np.concatenate([sup[i]["pos"][parado][mv[i]] for i in range(len(sup))])
    topo_cabeca = cab[:, 2].max()
    estado[nome] = {"quadro": parado, "chao": float(todos[:, 2].min()), "topo_cabeca": float(topo_cabeca),
                    "altura": float(topo_cabeca - todos[:, 2].min()), "altura_com_cabelo": float(todos[:, 2].max() - todos[:, 2].min())}
ALTURA = estado["normal"]["altura"]
P0 = PARADO_SUPER
base = {n: pts(g, P0) for n, g in list(RIGIDOS.items()) + [("luva_P", LUVA_P)]}
base_anel = {k: pts(g, P0) for k, g in ANEL_EXTRA.items()}
ctp = base["tronco"].mean(0)


def rigido(f):
    return kabsch(base["tronco"], pts(RIGIDOS["tronco"], f))


def para_parado(p, f):
    r, ca, cb, _ = rigido(f)
    return r.T @ (np.asarray(p) - cb) + ca


# ---------------------------------------------------------------- ombros e quadris (como em golpes_medidas.py)
C = QUADRO_OMBRO
hP = haste(pts(TUBOS["haste_P"], C))
prox = hP["p0"] if np.linalg.norm(hP["p0"] - pts(RIGIDOS["tronco"], C).mean(0)) < np.linalg.norm(hP["p1"] - pts(RIGIDOS["tronco"], C).mean(0)) else hP["p1"]
ombro_P_parado = para_parado(prox, C)
ombro_Q_parado = np.array([-(ombro_P_parado[0] - ctp[0]) + ctp[0], ombro_P_parado[1], ombro_P_parado[2]])
quadril = {}
tubo_parado = {}
for nome in ("tubo_X", "tubo_Y"):
    h = haste(pts(TUBOS[nome], P0))
    tenis = pts(RIGIDOS["tenis_" + nome[-1]], P0).mean(0)
    quadril[nome[-1]] = h["p0"] if np.linalg.norm(h["p0"] - tenis) > np.linalg.norm(h["p1"] - tenis) else h["p1"]
    tubo_parado[nome[-1]] = h

res = {"altura": ALTURA, "estado": estado, "ombro_P_parado": vet(ombro_P_parado), "ombro_Q_parado": vet(ombro_Q_parado),
       "quadril_parado": {k: vet(v) for k, v in quadril.items()}, "tronco_parado_c": vet(ctp), "quadros": {}}

linhas = []
w = linhas.append
w("MEDIDAS DO CHUTE DO DARK SONIC (XSONIC.md3) - unidades do modelo; entre parenteses, fracao da altura (%.2f, sola ate o topo da cabeca)" % ALTURA)
w("quadro parado normal %d: chao z=%.2f topo da cabeca z=%.2f altura %.2f (com os espetos %.2f); parado Super %d (flutua): altura %.2f"
  % (PARADO_NORMAL, estado["normal"]["chao"], estado["normal"]["topo_cabeca"], ALTURA, estado["normal"]["altura_com_cabelo"], PARADO_SUPER, estado["super"]["altura"]))
w("quadril X (+X): (%.2f %.2f %.2f) quadril Y (-X): (%.2f %.2f %.2f); haste da coxa parada: X %.2f Y %.2f (comprimento), canela parada (quadril->centro do anel): X %.2f Y %.2f" % (
    *quadril["X"], *quadril["Y"], tubo_parado["X"]["comprimento"], tubo_parado["Y"]["comprimento"],
    np.linalg.norm(base["canela_X"].mean(0) - quadril["X"]), np.linalg.norm(base["canela_Y"].mean(0) - quadril["Y"])))
w("tenis parado (extensao no sistema do pe parado, largura x comprimento x altura; x lateral, y para a frente, z para cima): X %s Y %s" % (
    np.round(base["tenis_X"].max(0) - base["tenis_X"].min(0), 2), np.round(base["tenis_Y"].max(0) - base["tenis_Y"].min(0), 2)))

pernas_quadros = {}
for f, letra in zip(SUPER, NOMES):
    r, ca, ct, rr = rigido(f)
    ang = angulos_tronco(r)
    cab_r, _, cab_c, cab_res = kabsch(base["cabeca"], pts(RIGIDOS["cabeca"], f))
    cab_rel = r.T @ cab_r
    ang_cab_rel = angulos_tronco(cab_rel)
    ombroP = r @ (ombro_P_parado - ca) + ct
    ombroQ = r @ (ombro_Q_parado - ca) + ct
    luva = pts(LUVA_P, f)
    luva_c = luva.mean(0)
    ponta = luva[np.argmax(np.linalg.norm(luva - ombroP, axis=1))]
    punhoP = pts(RIGIDOS["punho_P"], f).mean(0)
    punhoQ = pts(RIGIDOS["punho_Q"], f).mean(0)
    luvaQ = pts(RIGIDOS["luva_Q"], f).mean(0)
    hP_f, hQ_f = haste(pts(TUBOS["haste_P"], f)), haste(pts(TUBOS["haste_Q"], f))
    d = {"c_tronco": vet(ct), "R_tronco": [vet(l) for l in r], "angulos_tronco": {k: round(v, 2) for k, v in ang.items()},
         "c_cabeca": vet(cab_c), "R_cabeca": [vet(l) for l in cab_r], "cabeca_rel_tronco": {k: round(v, 2) for k, v in ang_cab_rel.items()},
         "ombro_P": vet(ombroP), "ombro_Q": vet(ombroQ), "punho_P": vet(punhoP), "luva_P_c": vet(luva_c), "luva_P_ponta": vet(ponta),
         "punho_Q": vet(punhoQ), "luva_Q_c": vet(luvaQ),
         "haste_P": {k: (vet(v) if isinstance(v, np.ndarray) else round(v, 4)) for k, v in hP_f.items()},
         "haste_Q": {k: (vet(v) if isinstance(v, np.ndarray) else round(v, 4)) for k, v in hQ_f.items()}}
    for nome in ("punho_P", "punho_Q", "luva_Q"):
        rr_, _, cc_, rs_ = kabsch(base[nome], pts(RIGIDOS[nome], f))
        d["R_" + nome] = [vet(l) for l in rr_]
        d["c_" + nome] = vet(cc_)
        d["res_" + nome] = round(rs_, 3)
    for nome in CRESCEM:
        r_, s_, ca_, cb_, rs_ = umeyama(base[nome], pts(RIGIDOS[nome], f))
        razoes, e_p, e_q = extensoes_no_pe_parado(base[nome], pts(RIGIDOS[nome], f), r_, ca_, cb_)
        d["R_" + nome] = [vet(l) for l in r_]
        d["c_" + nome] = vet(cb_)
        d["esc_" + nome] = round(s_, 4)
        d["res_" + nome] = round(rs_, 3)
        d["razoes_" + nome] = vet(razoes)
    d["quadril_X"] = vet(r @ (quadril["X"] - ca) + ct)
    d["quadril_Y"] = vet(r @ (quadril["Y"] - ca) + ct)
    for lado in ("X", "Y"):
        h_f = haste(pts(TUBOS["tubo_" + lado], f))
        d["tubo_" + lado] = {k: (vet(v) if isinstance(v, np.ndarray) else round(v, 4)) for k, v in h_f.items()}
    res["quadros"][str(f)] = d

    w("\n== quadro %s (MD3 %d, %s) ==" % (letra, f, q_nomes[f]))
    w("tronco: inclinacao para a frente %.1f graus, para o lado(+X) %.1f, total %.1f, giro da frente para +X %.1f; centro (%.2f %.2f %.2f)" % (
        ang["frente"], ang["lado"], ang["total"], ang["giro"], *ct))
    h_loc = r.T @ (cab_c - ct)
    w("cabeca: centro relativo ao tronco, no sistema do tronco (%.2f %.2f %.2f) = (%.0f%% %.0f%% %.0f%% da altura); giro relativo ao tronco: frente %.1f lado %.1f giro %.1f" % (
        *h_loc, *(100 * h_loc / ALTURA), ang_cab_rel["frente"], ang_cab_rel["lado"], ang_cab_rel["giro"]))
    for lado in ("X", "Y"):
        hip = np.array(d["quadril_" + lado])
        cuff = np.array(d["c_canela_" + lado]) if "c_canela_" + lado in d else None
        cuff_c = pts(RIGIDOS["canela_" + lado], f).mean(0)
        shoe_c = np.array(d["c_tenis_" + lado])
        tubo = d["tubo_" + lado]
        v_c, v_s = cuff_c - hip, shoe_c - hip
        loc_c, loc_s = r.T @ v_c, r.T @ v_s
        w("perna %s: quadril->centro do anel (%.2f %.2f %.2f) no sistema do tronco, comprimento %.2f (%.0f%% da altura; parado %.2f); quadril->centro do tenis (%.2f %.2f %.2f) = %.2f" % (
            lado, *loc_c, np.linalg.norm(v_c), 100 * np.linalg.norm(v_c) / ALTURA, np.linalg.norm(base["canela_" + lado].mean(0) - quadril[lado]), *loc_s, np.linalg.norm(v_s)))
        w("   haste da coxa (tubo): comprimento %.2f (parado %.2f, x%.2f) largura %.2f espessura %.2f" % (
            tubo["comprimento"], tubo_parado[lado]["comprimento"], tubo["comprimento"] / tubo_parado[lado]["comprimento"], tubo["largura"], tubo["espessura"]))
        w("   tenis cresce x%.2f (semelhanca; residuo %.2f); por eixo do pe parado (largura, comprimento, altura): x%.2f x%.2f x%.2f" % (
            d["esc_tenis_" + lado], d["res_tenis_" + lado], *d["razoes_tenis_" + lado]))
        w("   anel da canela cresce x%.2f (residuo %.2f); por eixo: x%.2f x%.2f x%.2f" % (d["esc_canela_" + lado], d["res_canela_" + lado], *d["razoes_canela_" + lado]))
        pernas_quadros[(f, lado)] = (np.linalg.norm(v_c), tubo["comprimento"], d["esc_tenis_" + lado])
    v2 = r.T @ (luva_c - ombroP)
    w("braco P: ombro->centro da luva %.2f (%.0f%%); luva no sistema do tronco (%.2f %.2f %.2f); haste P comprimento %.2f largura %.2f" % (
        np.linalg.norm(luva_c - ombroP), 100 * np.linalg.norm(luva_c - ombroP) / ALTURA, *v2, hP_f["comprimento"], hP_f["largura"]))
    v2 = r.T @ (luvaQ - ombroQ)
    w("braco Q (o outro): ombro->centro da luva %.2f (%.0f%%); luva no sistema do tronco (%.2f %.2f %.2f); haste Q comprimento %.2f largura %.2f" % (
        np.linalg.norm(luvaQ - ombroQ), 100 * np.linalg.norm(luvaQ - ombroQ) / ALTURA, *v2, hQ_f["comprimento"], hQ_f["largura"]))
    lp = pts(LUVA_P, P0)
    raio = lambda p: float(np.sqrt(((p - p.mean(0)) ** 2).sum(1).mean()))
    w("luvas: a P cresce x%.2f e a Q x%.2f em relacao ao parado (raio medio dos vertices em torno do centro)" % (
        raio(luva) / raio(lp), raio(pts(RIGIDOS["luva_Q"], f)) / raio(base["luva_Q"])))

# ---------------------------------------------------------------- o que muda de um quadro para o outro (residuo do ajuste rigido entre quadros seguidos)
w("\n== pecas que deformam entre quadros seguidos (residuo do ajuste rigido; 0 = so se mexeu como bloco) ==")
todos_grupos = dict(RIGIDOS)
todos_grupos["luva_P"] = LUVA_P
todos_grupos.update(TUBOS)
for a, b in zip(SUPER[:-1], SUPER[1:]):
    lin = []
    for nome, g in todos_grupos.items():
        _, _, _, rs = kabsch(pts(g, a), pts(g, b))
        lin.append("%s %.2f" % (nome, rs))
    w("%s->%s: %s" % (NOMES[SUPER.index(a)], NOMES[SUPER.index(b)], "; ".join(lin)))

# ---------------------------------------------------------------- a forma normal e igual?
w("\n== forma normal (137-140) contra a Super (273-276): deslocamento do centro e giro de cada peca rigida ==")
dif_max = 0.0
for n_, s_ in zip(NORMAL, SUPER):
    for nome in ("tronco", "punho_P", "punho_Q", "luva_Q", "tenis_X", "tenis_Y", "canela_X", "canela_Y"):
        a, b = pts(RIGIDOS[nome], n_), pts(RIGIDOS[nome], s_)
        dif_max = max(dif_max, float(np.linalg.norm(a.mean(0) - b.mean(0))))
    a, b = pts(RIGIDOS["cabeca"], n_), pts(RIGIDOS["cabeca"], s_)
    r_, _, _, _ = kabsch(a, b)
    ang = graus(math.acos(max(-1, min(1, (np.trace(r_) - 1) / 2))))
    w("%s (%d x %d): maior desvio das pecas rigidas (sem a cabeca) acumulado %.3f; cabeca: desloca %.2f e gira %.1f graus" % (
        NOMES[NORMAL.index(n_)], n_, s_, dif_max, np.linalg.norm(a.mean(0) - b.mean(0)), ang))

# ---------------------------------------------------------------- cabeca da forma normal (o resto do corpo e igual ao Super)
res["cabeca_normal"] = {}
for n_ in NORMAL:
    cab_r_n, _, cab_c_n, _ = kabsch(base["cabeca"], pts(RIGIDOS["cabeca"], n_))
    res["cabeca_normal"][str(n_)] = {"R_cabeca": [vet(l) for l in cab_r_n], "c_cabeca": vet(cab_c_n)}

# ---------------------------------------------------------------- alcance natural (pose parada Super)
res["parado"] = {n: vet(base[n].mean(0)) for n in ("cabeca", "tronco", "punho_P", "punho_Q", "luva_P", "luva_Q", "canela_X", "canela_Y", "tenis_X", "tenis_Y")}
res["natural"] = {
    "braco_P": float(np.linalg.norm(base["luva_P"].mean(0) - ombro_P_parado)),
    "braco_Q": float(np.linalg.norm(base["luva_Q"].mean(0) - ombro_Q_parado)),
    "perna_X": float(np.linalg.norm(base["canela_X"].mean(0) - quadril["X"])),
    "perna_Y": float(np.linalg.norm(base["canela_Y"].mean(0) - quadril["Y"])),
}
res["natural"] = {k: round(v, 4) for k, v in res["natural"].items()}
res["tubo_parado"] = {k: {"comprimento": round(v["comprimento"], 4), "largura": round(v["largura"], 4), "espessura": round(v["espessura"], 4)} for k, v in tubo_parado.items()}
w("\n== resumo por quadro: quadril->anel, haste da coxa e quanto o tenis cresce (o que a perna do Neo precisa seguir) ==")
for lado in ("X", "Y"):
    for f, letra in zip(SUPER, NOMES):
        anel, tubo, esc = pernas_quadros[(f, lado)]
        w("perna %s quadro %s: quadril->anel %.2f (x%.2f do parado %.2f), haste %.2f (x%.2f), tenis x%.2f" % (
            lado, letra, anel, anel / res["natural"]["perna_" + lado], res["natural"]["perna_" + lado], tubo, tubo / tubo_parado[lado]["comprimento"], esc))

json.dump(res, open(sys.argv[1], "w"), indent=1)
open(sys.argv[2], "w", encoding="utf-8").write("\n".join(linhas) + "\n")
print("\n".join(linhas))
