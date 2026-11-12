"""Monta (PIL) as folhas e os mapas numerados das partes do Neo a partir de partes.json e das fotos do Blender (separar_partes.py).
Uso: python -I montar_folhas_partes.py <pasta partes-corpo>"""
import json
import math
import os
import sys

sys.path.append(os.path.join(os.path.expanduser("~"), "AppData/Local/Packages/PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0/LocalCache/local-packages/Python312/site-packages"))
from PIL import Image, ImageDraw, ImageFilter, ImageFont

PASTA = os.path.abspath(sys.argv[1])
dados = json.load(open(os.path.join(PASTA, "partes.json"), encoding="utf-8"))
P = {p["id"]: p for p in dados["partes"]}
BG = (24, 26, 33)
TEXTO = (232, 234, 240)
SUAVE = (150, 156, 170)
ALERTA = (255, 196, 70)


def fonte(tam, negrito=False):
    return ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf" if negrito else "C:/Windows/Fonts/segoeui.ttf", tam)


def rgb(p):
    return tuple(int(c * 255) for c in p.get("cor", (0.4, 0.42, 0.47, 1.0))[:3])


def rotulo(p):
    return str(p["n"]) if p["n"] else p["id"].upper()


def quebrar(d, texto, f, largura, max_linhas=2):
    linhas, atual = [], ""
    for pal in texto.split():
        t = (atual + " " + pal).strip()
        if d.textlength(t, font=f) <= largura or not atual:
            atual = t
        else:
            linhas.append(atual)
            atual = pal
    linhas.append(atual)
    if len(linhas) > max_linhas:
        resto = " ".join(linhas[max_linhas - 1:])
        while d.textlength(resto + "...", font=f) > largura and len(resto) > 3:
            resto = resto[:-1]
        linhas = linhas[:max_linhas - 1] + [resto + "..."]
    return linhas


def selo(d, x, y, txt, cor, r=15, f=None):
    d.ellipse([x - r, y - r, x + r, y + r], fill=cor, outline=(255, 255, 255), width=2)
    d.text((x, y), txt, font=f or fonte(17, True), fill=(255, 255, 255), anchor="mm", stroke_width=2, stroke_fill=(0, 0, 0))


def miniatura(p, lado):
    a = Image.open(os.path.join(PASTA, "miniaturas", "%s_A.png" % p["id"])).convert("RGBA")
    b = Image.open(os.path.join(PASTA, "miniaturas", "%s_B.png" % p["id"])).convert("RGBA")
    base = Image.new("RGBA", a.size, BG + (255,))
    base.alpha_composite(a)
    halo = b.getchannel("A").filter(ImageFilter.MaxFilter(9)).point(lambda v: 235 if v > 8 else 0)
    brilho = Image.new("RGBA", a.size, (255, 255, 255, 255))
    brilho.putalpha(halo)
    base.alpha_composite(brilho)
    base.alpha_composite(b)
    return base.convert("RGB").resize((lado, lado), Image.LANCZOS)


def tile(im, p, x, y, lado, cap):
    d = ImageDraw.Draw(im)
    if "objeto" in p:
        im.paste(miniatura(p, lado), (x, y))
    else:
        d.rectangle([x, y, x + lado - 1, y + lado - 1], fill=(36, 38, 48))
        d.text((x + lado // 2, y + lado // 2 - 14), "sem malha", font=fonte(26, True), fill=SUAVE, anchor="mm")
        d.text((x + lado // 2, y + lado // 2 + 18), "osso de comprimento %.1f" % p["comprimento"], font=fonte(18), fill=SUAVE, anchor="mm")
    d.rectangle([x, y, x + lado - 1, y + lado - 1], outline=(70, 74, 88), width=2)
    selo(d, x + 26, y + 26, rotulo(p), rgb(p), r=21, f=fonte(22, True))     # o numero tambem na foto: um recorte so da imagem continua identificavel
    cy = y + lado + 8
    selo(d, x + 24, cy + 20, rotulo(p), rgb(p), r=20, f=fonte(21, True))
    f = fonte(18)
    for k, linha in enumerate(quebrar(d, p["osso"], f, lado - 62)):
        d.text((x + 52, cy + k * 22), linha, font=f, fill=TEXTO)
    if "objeto" in p:
        extra = "%d tri, %d ilhas, pureza %.2f" % (p["triangulos"], p.get("ilhas", 0), p["pureza"])
        if p["origem"] == "capa":
            extra = "objeto 'capa': " + extra
        d.text((x + 6, cy + 48), extra, font=fonte(15), fill=SUAVE)
        if p["ajustado"]:
            d.text((x + 6, cy + 67), "* peso ajustado por mim (%d tri)" % p["ajustado"], font=fonte(15), fill=ALERTA)


def folha(titulo, sub, ids, colunas, lado, saida):
    M, TOPO, CAP = 14, 118, 94
    linhas = math.ceil(len(ids) / colunas)
    W = colunas * (lado + M) + M
    H = TOPO + linhas * (lado + CAP + M) + M
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.text((M + 4, 14), titulo, font=fonte(34, True), fill=TEXTO)
    d.text((M + 4, 62), sub, font=fonte(19), fill=SUAVE)
    d.text((M + 4, 88), "Laranja = a parte deste osso, cinza = o resto do corpo. 'esquerdo' = lado esquerdo da imagem (como você nomeou). * = peso que eu mexi na cópia.",
           font=fonte(17), fill=SUAVE)
    for i, pid in enumerate(ids):
        if pid is None:
            continue
        tile(im, P[pid], M + (i % colunas) * (lado + M), TOPO + (i // colunas) * (lado + CAP + M), lado, CAP)
    im.save(os.path.join(PASTA, saida), optimize=True)
    print(saida, im.size)


def n(i):
    return "p%02d" % i


corpo_ids = [n(1), n(48), "c1", "c2", n(49), n(55),
             n(2), n(25), n(3), n(26), n(4), n(27),
             n(8), n(28), n(50), n(56), n(51), n(52),
             n(57), n(53), n(54), n(58), n(59), None]
folha("Neo - partes por osso (1/3): corpo", "Corpo, cabeça, capa, cinto, braços e pernas (as mãos têm folhas próprias: 2/3 e 3/3).", corpo_ids, 6, 330, "folha_1_corpo.png")


def dedos(esq):
    if esq:
        return [n(5), n(6), n(7), None, n(9), n(10), n(11), n(12), n(13), n(14), n(15), n(16), n(17), n(18), n(19), n(20), n(21), n(22), n(23), n(24)]
    return [n(45), n(46), n(47), None, n(41), n(42), n(43), n(44), n(37), n(38), n(39), n(40), n(33), n(34), n(35), n(36), n(29), n(30), n(31), n(32)]


folha("Neo - partes por osso (2/3): mão esquerda", "Uma linha por dedo, da palma (1) até a ponta. Linhas: polegar, indicador, médio, anelar, mindinho. A palma é o 8 (folha 1).",
      dedos(True), 4, 290, "folha_2_mao_esquerda.png")
folha("Neo - partes por osso (3/3): mão direita", "Uma linha por dedo, da palma (1) até a ponta. Linhas: polegar, indicador, médio, anelar, mindinho. A palma é o 28 (folha 1).",
      dedos(False), 4, 290, "folha_3_mao_direita.png")


# ------------------------------------------------------------------ mapas numerados
def painel(nome, lado, so_tipos=None, escondidos=()):
    cru = Image.open(os.path.join(PASTA, "mapa_%s_cru.png" % nome)).convert("RGBA")
    base = Image.new("RGBA", cru.size, BG + (255,))
    base.alpha_composite(cru)
    m = dados["mapas"][nome]
    k = lado / cru.size[0]
    base = base.convert("RGB").resize((lado, int(cru.size[1] * k)), Image.LANCZOS)
    d = ImageDraw.Draw(base)
    usados = []
    for pid, (x, y) in m["ancoras"].items():
        p = P[pid]
        if pid in escondidos or (so_tipos and p["tipo"] not in so_tipos):
            continue
        selo(d, x * k, y * k, rotulo(p), rgb(p), r=15)
        usados.append(pid)
    return base, usados


def legenda(d, ids, x0, y0, colunas, larg_col, f=None):
    f = f or fonte(17)
    linhas = math.ceil(len(ids) / colunas)
    for i, pid in enumerate(ids):
        p = P[pid]
        c, r = divmod(i, linhas)
        x, y = x0 + c * larg_col, y0 + r * 32
        selo(d, x + 15, y + 15, rotulo(p), rgb(p), r=13, f=fonte(14, True))
        d.text((x + 36, y + 15), p["osso"], font=f, fill=TEXTO, anchor="lm")
    return linhas


L = 700
paineis = [("corpo_frente", "de frente (com a cabeça)", set()), ("corpo_frente_sem_cabeca", "de frente, sem cabeça e sem capa", {"p48", "c1"}),
           ("corpo_costas", "de costas, sem cabeça e sem capa (o 'esquerdo' dele fica à direita da imagem)", {"p48", "c1"})]
imgs, todos = [], []
for nome, _, esc in paineis:
    im, usados = painel(nome, L, so_tipos={"corpo", "mao"}, escondidos=esc)
    imgs.append(im)
    todos += [u for u in usados if u not in todos]
todos.sort(key=lambda i: (P[i]["n"] is None, P[i]["n"] or 0, i))
TOPO, LEG = 100, 5
W = L * 3 + 16 * 4
alt_leg = math.ceil(len(todos) / LEG) * 32 + 20
mapa = Image.new("RGB", (W, TOPO + L + 54 + alt_leg), BG)
d = ImageDraw.Draw(mapa)
d.text((16, 14), "Neo - mapa numerado do corpo (o número é o do osso; mãos no outro mapa)", font=fonte(32, True), fill=TEXTO)
d.text((16, 60), "Cada cor é uma parte (um osso). A cabeça (a estrela de espinhos) tampa o resto, por isso há as vistas sem ela.", font=fonte(19), fill=SUAVE)
for i, (im, (_, rot, _)) in enumerate(zip(imgs, paineis)):
    x = 16 + i * (L + 16)
    mapa.paste(im, (x, TOPO))
    d.text((x + 6, TOPO + L + 8), rot, font=fonte(18), fill=SUAVE)
legenda(d, todos, 16, TOPO + L + 54, LEG, (W - 32) // LEG)
mapa.save(os.path.join(PASTA, "mapa_corpo.png"), optimize=True)
print("mapa_corpo.png", mapa.size)

LM = 900
pe, ue = painel("mao_esquerda", LM, so_tipos={"mao", "dedo"})
pd, ud = painel("mao_direita", LM, so_tipos={"mao", "dedo"})
alt = pe.size[1]
mapa2 = Image.new("RGB", (LM + 24, 120 + alt * 2 + 130), BG)
d = ImageDraw.Draw(mapa2)
d.text((12, 14), "Neo - mapa numerado das mãos (vista de cima)", font=fonte(32, True), fill=TEXTO)
d.text((12, 62), "Os dedos saem da palma em ordem: 1 = junto da palma, 4 = ponta (o polegar tem 3).", font=fonte(19), fill=SUAVE)
mapa2.paste(pe, (12, 100))
mapa2.paste(pd, (12, 100 + alt + 10))
d.text((22, 104), "mão esquerda (lado esquerdo da imagem)", font=fonte(20, True), fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
d.text((22, 104 + alt + 10), "mão direita (lado direito da imagem)", font=fonte(20, True), fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
y = 100 + alt * 2 + 24
d.text((14, y), "Esquerda: palma 8, polegar 5-7, indicador 9-12, médio 13-16, anelar 17-20, mindinho 21-24.", font=fonte(20), fill=TEXTO)
d.text((14, y + 36), "Direita: palma 28, mindinho 29-32, anelar 33-36, médio 37-40, indicador 41-44, polegar 45-47.", font=fonte(20), fill=TEXTO)
mapa2.save(os.path.join(PASTA, "mapa_maos.png"), optimize=True)
print("mapa_maos.png", mapa2.size)
