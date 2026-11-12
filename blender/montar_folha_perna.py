"""Folha de uma parte do chute: uma linha por quadro, 4 colunas = Sonic X (corpo todo) | Neo + contorno do Sonic X | Sonic X (so as pernas, de perto) | Neo + contorno (pernas de perto).
Uso: python montar_folha_perna.py <pasta da rodada> <saida.png> <vista: lado|34> <titulo>"""
import json
import math
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

PASTA, SAIDA, VISTA, TITULO = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
QUADROS = [(273, "A - preparacao"), (274, "B - passo"), (275, "C - impacto"), (276, "D - perna esticada")]
ALTURA = 400
FONTE = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 17)
FONTE_B = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 19)
MAGENTA = (230, 0, 200)
J = json.load(open(os.path.join(PASTA, "metricas_273_274_275_276.json")))


def abrir(caminho):
    """(rgb sobre branco, mascara do que nao e transparente)."""
    img = Image.open(caminho).convert("RGBA")
    fundo = Image.new("RGBA", img.size, (255, 255, 255, 255))
    fundo.alpha_composite(img)
    return fundo.convert("RGB"), img.getchannel("A").point(lambda v: 255 if v > 10 else 0)


def contorno(m, espessura=2):
    dil = m.filter(ImageFilter.MaxFilter(2 * espessura + 1))
    ero = m.filter(ImageFilter.MinFilter(2 * espessura + 1))
    return ImageChops.subtract(dil, ero)


def uniao(*caixas):
    caixas = [c for c in caixas if c is not None]
    return (min(c[0] for c in caixas), min(c[1] for c in caixas), max(c[2] for c in caixas), max(c[3] for c in caixas))


def norm(v):
    return math.sqrt(sum(x * x for x in v))


def sub(a, b):
    return [x - y for x, y in zip(a, b)]


def angulo(a, b):
    c = sum(x * y for x, y in zip(a, b)) / norm(a) / norm(b)
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def celulas(q, ref_nome, neo_nome):
    ref, m_ref = abrir(os.path.join(PASTA, "q%03d_%s.png" % (q, ref_nome)))
    neo, m_neo = abrir(os.path.join(PASTA, "q%03d_%s.png" % (q, neo_nome)))
    caixa = uniao(m_ref.getbbox(), m_neo.getbbox())
    pad = 12
    caixa = (max(caixa[0] - pad, 0), max(caixa[1] - pad, 0), min(caixa[2] + pad, ref.width), min(caixa[3] + pad, ref.height))
    sobre = neo.copy()
    sobre.paste(Image.new("RGB", sobre.size, MAGENTA), (0, 0), contorno(m_ref, 2))
    return ref.crop(caixa), sobre.crop(caixa)


def redimensionar(im):
    return im.resize((max(1, int(im.width * ALTURA / im.height)), ALTURA), Image.LANCZOS)


linhas = []
for q, nome in QUADROS:
    suf_corpo, suf_pernas = ("lado", "pernas") if VISTA == "lado" else ("34", "pernas34")
    ref_c, neo_c = celulas(q, "ref_" + suf_corpo, "neosocapa_" + suf_corpo)
    ref_p, neo_p = celulas(q, "ref_" + suf_pernas, "neo_" + suf_pernas)
    mn = J["quadros"][str(q)]["medidas_neo"]
    anda = norm(mn["desloca"])

    def linha(px, rotulo):
        dobra = angulo(sub(px["joelho"], px["quadril"]), sub(px["tornozelo"], px["joelho"]))
        solta = px["erro_ponta"] * J["escala_corpo"] * 100
        return "%s: joelho dobra %.0f graus, coxa %.2f m (natural %.2f), pe a %.0f cm da ponta do tenis do Sonic X" % (rotulo, dobra, px["coxa_esticada"], px["coxa_natural"], solta)
    texto = [linha(mn["pernas"]["X"], "direita (chuta)") + "; corpo andou %.2f m" % anda, linha(mn["pernas"]["Y"], "esquerda (apoio)")]
    linhas.append((nome, [redimensionar(ref_c), redimensionar(neo_c), redimensionar(ref_p), redimensionar(neo_p)], texto))

rotulos = ["Sonic X", "Neo com o contorno do Sonic X", "Sonic X, pernas de perto", "Neo, pernas de perto"]
larg_col = [max(l[1][i].width for l in linhas) for i in range(4)]
largura = sum(larg_col) + 10 * 5
alt_linha = ALTURA + 84
folha = Image.new("RGB", (largura, 86 + alt_linha * len(linhas)), (255, 255, 255))
dr = ImageDraw.Draw(folha)
dr.text((10, 8), TITULO, fill=(0, 0, 0), font=FONTE_B)
dr.text((10, 34), "Contorno magenta = Sonic X por cima do Neo. As renders do Neo estao sem a capa. Vista: %s." % ("de lado" if VISTA == "lado" else "3/4"), fill=(70, 70, 70), font=FONTE)
x = 10
for i in range(4):
    dr.text((x + 4, 62), rotulos[i], fill=(0, 0, 0), font=FONTE_B)
    x += larg_col[i] + 10
y = 86
for nome, ims, texto in linhas:
    dr.text((10, y), nome, fill=(0, 0, 0), font=FONTE_B)
    x = 10
    for i, im in enumerate(ims):
        folha.paste(im, (x + (larg_col[i] - im.width) // 2, y + 24))
        dr.rectangle([x, y + 24, x + larg_col[i], y + 24 + ALTURA], outline=(205, 205, 205))
        x += larg_col[i] + 10
    for k, t in enumerate(texto):
        dr.text((10 + larg_col[0] + 10, y + 26 + ALTURA + 22 * k), t, fill=(60, 60, 60), font=FONTE)
    y += alt_linha
folha.save(SAIDA)
print("ok", SAIDA, folha.size)
