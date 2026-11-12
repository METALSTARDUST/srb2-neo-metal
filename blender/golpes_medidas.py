"""Mede o soco (TAL1) do Dark Sonic no XSONIC.md3: forma Super (quadros 277-280) e normal (141-144), sem bpy (Python do Blender: so numpy).
Tudo sai em unidades do modelo (Blender = MD3 * 0,1) e em fracao da altura do personagem parado (sola ate o topo da cabeca).
Pecas rigidas (tronco, cabeca, punhos, tenis, canelas) sao seguidas pelo ajuste rigido (Kabsch) a partir do quadro parado;
ombros e quadris nao existem no modelo (cada membro e um tubo solto), entao saem das pontas dos tubos e viajam com o tronco.
Uso: python golpes_medidas.py <saida.json> <saida.txt>"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

import golpes_ref as G

PARADO_SUPER, PARADO_NORMAL = 219, 5
SUPER = [277, 278, 279, 280]
NORMAL = [141, 142, 143, 144]
NOMES = "ABCD"

# grupos de ilhas (superficie, [ilhas]); a ilha e o componente conexo da superficie (ver _ilhas_xsonic.txt)
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


def medir(frames, parado, rotulo):
    base = {n: pts(g, parado) for n, g in RIGIDOS.items()}
    base["luva_P"] = pts(LUVA_P, parado)
    ctp = base["tronco"].mean(0)
    out = {"parado": parado, "quadros": {}}
    for f in frames:
        rt, _, ct, _ = kabsch(base["tronco"], pts(RIGIDOS["tronco"], f))
        out["quadros"][f] = {"R_tronco": rt, "c_tronco": ct}
    return out


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
ctp = base["tronco"].mean(0)


def rigido(f):
    return kabsch(base["tronco"], pts(RIGIDOS["tronco"], f))


def para_parado(p, f):
    """Ponto de um quadro f levado ao sistema do quadro parado, seguindo o tronco."""
    r, ca, cb, _ = rigido(f)
    return r.T @ (np.asarray(p) - cb) + ca


def do_parado(p, f):
    r, ca, cb, _ = rigido(f)
    return r @ (np.asarray(p) - ca) + cb


# ---------------------------------------------------------------- ombros e quadris (pontas dos tubos no quadro estendido C)
C = 279
hP = haste(pts(TUBOS["haste_P"], C))
prox = hP["p0"] if np.linalg.norm(hP["p0"] - pts(RIGIDOS["tronco"], C).mean(0)) < np.linalg.norm(hP["p1"] - pts(RIGIDOS["tronco"], C).mean(0)) else hP["p1"]
ombro_P_parado = para_parado(prox, C)
ombro_Q_parado = np.array([-(ombro_P_parado[0] - ctp[0]) + ctp[0], ombro_P_parado[1], ombro_P_parado[2]])
quadril = {}
for nome in ("tubo_X", "tubo_Y"):
    h = haste(pts(TUBOS[nome], P0))
    tenis = pts(RIGIDOS["tenis_" + nome[-1]], P0).mean(0)
    quadril[nome[-1]] = h["p0"] if np.linalg.norm(h["p0"] - tenis) > np.linalg.norm(h["p1"] - tenis) else h["p1"]

res = {"altura": ALTURA, "estado": estado, "ombro_P_parado": vet(ombro_P_parado), "ombro_Q_parado": vet(ombro_Q_parado),
       "quadril_parado": {k: vet(v) for k, v in quadril.items()}, "tronco_parado_c": vet(ctp), "quadros": {}}

linhas = []
w = linhas.append
w("MEDIDAS DO SOCO DO DARK SONIC (XSONIC.md3) - unidades do modelo; entre parenteses, fracao da altura (%.2f, sola ate o topo da cabeca)" % ALTURA)
w("quadro parado normal %d: chao z=%.2f topo da cabeca z=%.2f altura %.2f (com os espetos %.2f); parado Super %d (flutua): altura %.2f"
  % (PARADO_NORMAL, estado["normal"]["chao"], estado["normal"]["topo_cabeca"], ALTURA, estado["normal"]["altura_com_cabelo"], PARADO_SUPER, estado["super"]["altura"]))
w("ombro P (braco que soca) no sistema parado: (%.2f %.2f %.2f); quadril X: (%.2f %.2f %.2f) quadril Y: (%.2f %.2f %.2f)" % (
    *ombro_P_parado, *quadril["X"], *quadril["Y"]))

longitudes = {}
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
    for nome in ("punho_P", "punho_Q", "luva_Q", "tenis_X", "tenis_Y", "canela_X", "canela_Y"):
        rr_, _, cc_, rs_ = kabsch(base[nome], pts(RIGIDOS[nome], f))
        d["R_" + nome] = [vet(l) for l in rr_]
        d["c_" + nome] = vet(cc_)
        d["res_" + nome] = round(rs_, 3)
    d["quadril_X"] = vet(r @ (quadril["X"] - ca) + ct)
    d["quadril_Y"] = vet(r @ (quadril["Y"] - ca) + ct)
    res["quadros"][str(f)] = d

    w("\n== quadro %s (MD3 %d, %s) ==" % (letra, f, q_nomes[f]))
    w("tronco: inclinacao para a frente %.1f graus, para o lado(+X) %.1f, total %.1f, giro da frente para +X %.1f; centro (%.2f %.2f %.2f)" % (
        ang["frente"], ang["lado"], ang["total"], ang["giro"], *ct))
    h_loc = r.T @ (cab_c - ct)
    w("cabeca: centro relativo ao tronco, no sistema do tronco (%.2f %.2f %.2f) = (%.0f%% %.0f%% %.0f%% da altura); giro relativo ao tronco: frente %.1f lado %.1f giro %.1f" % (
        *h_loc, *(100 * h_loc / ALTURA), ang_cab_rel["frente"], ang_cab_rel["lado"], ang_cab_rel["giro"]))
    for lado, tub, cc in (("X(+X)", "canela_X", "quadril_X"), ("Y(-X)", "canela_Y", "quadril_Y")):
        hip = np.array(d[cc])
        tor = np.array(d["c_" + tub])
        tn = np.array(d["c_tenis_" + tub[-1]])
        v = tor - hip
        loc = r.T @ v
        baixo = r.T @ (tn - tor)
        w("perna %s: quadril->punho da canela (%.2f %.2f %.2f) no sistema do tronco, comprimento %.2f (%.0f%% da altura), angulo com o eixo do tronco %.1f graus; tenis em relacao a canela (%.2f %.2f %.2f)" % (
            lado, *loc, np.linalg.norm(v), 100 * np.linalg.norm(v) / ALTURA, math.degrees(math.acos(max(-1, min(1, -loc[2] / np.linalg.norm(loc))))), *baixo))
    v = punhoP - ombroP
    vl = r.T @ (luva_c - ombroP)
    vt_ = r.T @ (ponta - ombroP)
    w("braco P: ombro->punho (manga) %.2f (%.0f%%), ombro->centro da luva %.2f (%.0f%%), ombro->ponta da luva %.2f (%.0f%%); luva no sistema do tronco (%.2f %.2f %.2f)" % (
        np.linalg.norm(v), 100 * np.linalg.norm(v) / ALTURA, np.linalg.norm(luva_c - ombroP), 100 * np.linalg.norm(luva_c - ombroP) / ALTURA,
        np.linalg.norm(ponta - ombroP), 100 * np.linalg.norm(ponta - ombroP) / ALTURA, *vl))
    w("haste P (tubo de 3 tiras): comprimento %.2f largura %.2f espessura %.2f; luva P: extensao %.2f x %.2f x %.2f" % (
        hP_f["comprimento"], hP_f["largura"], hP_f["espessura"], *(luva.max(0) - luva.min(0))))
    v2 = r.T @ (luvaQ - ombroQ)
    w("braco Q (o outro): ombro->centro da luva %.2f (%.0f%%); luva no sistema do tronco (%.2f %.2f %.2f); haste Q comprimento %.2f largura %.2f" % (
        np.linalg.norm(luvaQ - ombroQ), 100 * np.linalg.norm(luvaQ - ombroQ) / ALTURA, *v2, hQ_f["comprimento"], hQ_f["largura"]))
    longitudes[f] = np.linalg.norm(luva_c - ombroP)

w("\n== razao do comprimento do braco P (ombro->centro da luva) em relacao ao quadro A ==")
for f, letra in zip(SUPER, NOMES):
    w("%s: %.2f vs A %.2f = x%.2f" % (letra, longitudes[f], longitudes[SUPER[0]], longitudes[f] / longitudes[SUPER[0]]))

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
w("\n== forma normal (141-144) contra a Super (277-280): deslocamento do centro e giro de cada peca rigida ==")
dif_max = 0.0
for n_, s_ in zip(NORMAL, SUPER):
    lin = []
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

# ---------------------------------------------------------------- alcance natural (pose parada Super): referencia do esticamento
res["parado"] = {n: vet(base[n].mean(0)) for n in ("cabeca", "tronco", "punho_P", "punho_Q", "luva_P", "luva_Q", "canela_X", "canela_Y", "tenis_X", "tenis_Y")}
natural = {
    "braco_P": float(np.linalg.norm(base["luva_P"].mean(0) - ombro_P_parado)),
    "braco_Q": float(np.linalg.norm(base["luva_Q"].mean(0) - ombro_Q_parado)),
    "perna_X": float(np.linalg.norm(base["canela_X"].mean(0) - quadril["X"])),
    "perna_Y": float(np.linalg.norm(base["canela_Y"].mean(0) - quadril["Y"])),
}
res["natural"] = {k: round(v, 4) for k, v in natural.items()}
w("\n== alcance natural na pose parada Super (219): braco P (ombro->centro da luva) %.2f, braco Q %.2f, perna X (quadril->punho da canela) %.2f, perna Y %.2f ==" % (
    natural["braco_P"], natural["braco_Q"], natural["perna_X"], natural["perna_Y"]))
w("razao ao natural no quadro C: braco P x%.2f, braco Q x%.2f, perna X x%.2f, perna Y x%.2f" % (
    longitudes[279] / natural["braco_P"], res["quadros"]["279"]["luva_Q_c"] and float(np.linalg.norm(np.array(res["quadros"]["279"]["luva_Q_c"]) - np.array(res["quadros"]["279"]["ombro_Q"]))) / natural["braco_Q"],
    float(np.linalg.norm(np.array(res["quadros"]["279"]["c_canela_X"]) - np.array(res["quadros"]["279"]["quadril_X"]))) / natural["perna_X"],
    float(np.linalg.norm(np.array(res["quadros"]["279"]["c_canela_Y"]) - np.array(res["quadros"]["279"]["quadril_Y"]))) / natural["perna_Y"]))

json.dump(res, open(sys.argv[1], "w"), indent=1)
open(sys.argv[2], "w", encoding="utf-8").write("\n".join(linhas) + "\n")
print("\n".join(linhas))
