"""Folha da escada do pe no chute: por quadro (C e D) uma linha com o Sonic X e o Neo em 4 tamanhos de pe, cada Neo com o contorno do Sonic X por cima (magenta)."""
import json
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

BASE = r"C:\tmp\srb2-metal-homing\neo\golpes-neo\chute\pe_escada"
SAIDA = os.path.join(BASE, "folha_pe_chute.png")
VARIANTES = [("f10", "como esta (100%)"), ("f075", "75%"), ("f05", "50%"), ("f025", "25%")]
QUADROS = [(275, "C - impacto"), (276, "D - perna esticada")]
ALTURA_CELULA = 430
FONTE = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 17)
FONTE_B = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 19)
MAGENTA = (230, 0, 200)


def abrir(caminho):
    """Os renders tem fundo transparente: compoe sobre branco."""
    img = Image.open(caminho).convert("RGBA")
    fundo = Image.new("RGBA", img.size, (255, 255, 255, 255))
    fundo.alpha_composite(img)
    return fundo.convert("RGB")


def mascara(img):
    """Pixels que nao sao o fundo (o canto superior esquerdo)."""
    fundo = Image.new("RGB", img.size, img.getpixel((0, 0)))
    dif = ImageChops.difference(img, fundo).convert("L")
    return dif.point(lambda v: 255 if v > 24 else 0)


def contorno(m, espessura=2):
    dil = m.filter(ImageFilter.MaxFilter(2 * espessura + 1))
    ero = m.filter(ImageFilter.MinFilter(2 * espessura + 1))
    return ImageChops.subtract(dil, ero)


def caixa_uniao(imgs):
    caixa = None
    for im in imgs:
        b = mascara(im).getbbox()
        if b is None:
            continue
        caixa = b if caixa is None else (min(caixa[0], b[0]), min(caixa[1], b[1]), max(caixa[2], b[2]), max(caixa[3], b[3]))
    return caixa


linhas = []
for q, titulo in QUADROS:
    ref = abrir(os.path.join(BASE, "f10", "q%03d_ref_lado.png" % q))
    fantasma = abrir(os.path.join(BASE, "f10", "q%03d_fantasma_lado.png" % q))
    contorno_ref = contorno(mascara(fantasma), 2)
    neos = [abrir(os.path.join(BASE, d, "q%03d_neosocapa_lado.png" % q)) for d, _ in VARIANTES]
    caixa = caixa_uniao([ref, fantasma] + neos)
    pad = 14
    caixa = (max(caixa[0] - pad, 0), max(caixa[1] - pad, 0), min(caixa[2] + pad, ref.width), min(caixa[3] + pad, ref.height))
    celulas = [("Sonic X", ref.crop(caixa))]
    for (d, rotulo), neo in zip(VARIANTES, neos):
        com = neo.copy()
        com.paste(Image.new("RGB", com.size, MAGENTA), (0, 0), contorno_ref)
        celulas.append((rotulo, com.crop(caixa)))
    medidas = {}
    for d, _ in VARIANTES:
        J = json.load(open(os.path.join(BASE, d, "metricas_275_276.json")))
        medidas[d] = J["quadros"][str(q)]["medidas_neo"]["pernas"]["X"]
    ref_pe = medidas["f10"]["pe_ref"][1]
    textos = ["tenis = %.0f%% da altura do corpo" % (100 * ref_pe / 2.71)]
    for d, _ in VARIANTES:
        textos.append("pe = %.0f%% da altura (x%.2f)" % (100 * medidas[d]["pe_neo"][1] / 2.71, 1.4 * medidas[d]["extra_pe"]))
    linhas.append((titulo, celulas, textos))

larg_cel = max(int(c.width * ALTURA_CELULA / c.height) for _, cels, _ in linhas for _, c in cels)
margem_t, alt_rot = 46, 52
largura = larg_cel * 5 + 10 * 6
altura = (ALTURA_CELULA + alt_rot + margem_t) * len(linhas) + 70
folha = Image.new("RGB", (largura, altura), (255, 255, 255))
dr = ImageDraw.Draw(folha)
dr.text((10, 8), "Parte 1 - pe do chute (Super). O pe cresce so uma fracao do crescimento do tenis do Sonic X; contorno magenta = Sonic X por cima do Neo", fill=(0, 0, 0), font=FONTE_B)
dr.text((10, 36), "pe = comprimento do pe do Neo em % da altura do corpo parado (Neo 3,93 / Sonic X 2,71); xN = tamanho em relacao ao pe natural do Neo", fill=(70, 70, 70), font=FONTE)
y = 70
for titulo, celulas, textos in linhas:
    dr.text((10, y), titulo, fill=(0, 0, 0), font=FONTE_B)
    y += margem_t - 14
    for i, ((rotulo, im), texto) in enumerate(zip(celulas, textos)):
        w = int(im.width * ALTURA_CELULA / im.height)
        im2 = im.resize((w, ALTURA_CELULA), Image.LANCZOS)
        x = 10 + i * (larg_cel + 10) + (larg_cel - w) // 2
        folha.paste(im2, (x, y))
        dr.rectangle([10 + i * (larg_cel + 10), y, 10 + i * (larg_cel + 10) + larg_cel, y + ALTURA_CELULA], outline=(200, 200, 200))
        dr.text((12 + i * (larg_cel + 10), y + ALTURA_CELULA + 3), rotulo, fill=(0, 0, 0), font=FONTE_B)
        dr.text((12 + i * (larg_cel + 10), y + ALTURA_CELULA + 26), texto, fill=(60, 60, 60), font=FONTE)
    y += ALTURA_CELULA + alt_rot
folha.save(SAIDA)
print("ok", SAIDA, folha.size)
