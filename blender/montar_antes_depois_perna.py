"""Antes e depois de uma parte do chute na MESMA camera: Sonic X | Neo antes | Neo depois, uma linha por quadro (so as pernas, de perto), com o contorno do Sonic X em magenta.
Uso: python montar_antes_depois_perna.py <pasta antes> <pasta depois> <saida.png> <vista: lado|34> <titulo> <perna: X|Y>
As pastas sao rodadas de golpes_chute.py com a mesma NEO_CAMERA_JSON (assim o enquadramento e igual); a perna dita qual linha de medidas vai embaixo (X direita que chuta, Y esquerda de apoio)."""
import json
import math
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ANTES, DEPOIS, SAIDA, VISTA, TITULO, PERNA = sys.argv[1:7]
QUADROS = [(273, "A - preparacao"), (274, "B - passo"), (275, "C - impacto"), (276, "D - perna esticada")]
ALTURA = 400
FONTE = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 17)
FONTE_B = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 19)
MAGENTA = (230, 0, 200)
SUFIXO = "pernas" if VISTA == "lado" else "pernas34"
NOME_PERNA = {"X": "direita (chuta)", "Y": "esquerda (apoio)"}[PERNA]


def abrir(caminho):
    img = Image.open(caminho).convert("RGBA")
    fundo = Image.new("RGBA", img.size, (255, 255, 255, 255))
    fundo.alpha_composite(img)
    return fundo.convert("RGB"), img.getchannel("A").point(lambda v: 255 if v > 10 else 0)


def contorno(m, espessura=2):
    return ImageChops.subtract(m.filter(ImageFilter.MaxFilter(2 * espessura + 1)), m.filter(ImageFilter.MinFilter(2 * espessura + 1)))


def uniao(caixas):
    caixas = [c for c in caixas if c is not None]
    return (min(c[0] for c in caixas), min(c[1] for c in caixas), max(c[2] for c in caixas), max(c[3] for c in caixas))


def norm(v):
    return math.sqrt(sum(x * x for x in v))


def sub(a, b):
    return [x - y for x, y in zip(a, b)]


def angulo(a, b):
    c = sum(x * y for x, y in zip(a, b)) / norm(a) / norm(b)
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def medidas(pasta, q):
    J = json.load(open(os.path.join(pasta, "metricas_273_274_275_276.json")))
    px = J["quadros"][str(q)]["medidas_neo"]["pernas"][PERNA]
    dobra = angulo(sub(px["joelho"], px["quadril"]), sub(px["tornozelo"], px["joelho"]))
    solta = px["erro_ponta"] * J["escala_corpo"] * 100
    return "coxa %.2f m, joelho dobra %.0f graus, pe a %.0f cm da ponta do Sonic X" % (px["coxa_esticada"], dobra, solta)


def redimensionar(im):
    return im.resize((max(1, int(im.width * ALTURA / im.height)), ALTURA), Image.LANCZOS)


linhas = []
for q, nome in QUADROS:
    ref, m_ref = abrir(os.path.join(DEPOIS, "q%03d_ref_%s.png" % (q, SUFIXO)))
    antes, m_a = abrir(os.path.join(ANTES, "q%03d_neo_%s.png" % (q, SUFIXO)))
    depois, m_d = abrir(os.path.join(DEPOIS, "q%03d_neo_%s.png" % (q, SUFIXO)))
    caixa = uniao([m_ref.getbbox(), m_a.getbbox(), m_d.getbbox()])
    pad = 12
    caixa = (max(caixa[0] - pad, 0), max(caixa[1] - pad, 0), min(caixa[2] + pad, ref.width), min(caixa[3] + pad, ref.height))
    celulas = [ref]
    for img in (antes, depois):
        sobre = img.copy()
        sobre.paste(Image.new("RGB", sobre.size, MAGENTA), (0, 0), contorno(m_ref, 2))
        celulas.append(sobre)
    linhas.append((nome, [redimensionar(c.crop(caixa)) for c in celulas], (medidas(ANTES, q), medidas(DEPOIS, q))))

rotulos = ["Sonic X (as pernas)", "Neo ANTES (Parte 2)", "Neo DEPOIS (Parte 3)"]
larg_col = [max(l[1][i].width for l in linhas) for i in range(3)]
largura = sum(larg_col) + 10 * 4
alt_linha = ALTURA + 84
folha = Image.new("RGB", (largura, 86 + alt_linha * len(linhas)), (255, 255, 255))
dr = ImageDraw.Draw(folha)
dr.text((10, 8), TITULO, fill=(0, 0, 0), font=FONTE_B)
dr.text((10, 34), "Contorno magenta = Sonic X por cima do Neo. Mesma camera nas tres colunas. Linha de medidas: perna %s. Vista: %s." % (NOME_PERNA, "de lado" if VISTA == "lado" else "3/4"), fill=(70, 70, 70), font=FONTE)
x = 10
for i in range(3):
    dr.text((x + 4, 62), rotulos[i], fill=(0, 0, 0), font=FONTE_B)
    x += larg_col[i] + 10
y = 86
for nome, ims, (t_antes, t_depois) in linhas:
    dr.text((10, y), nome, fill=(0, 0, 0), font=FONTE_B)
    x = 10
    for i, im in enumerate(ims):
        folha.paste(im, (x + (larg_col[i] - im.width) // 2, y + 24))
        dr.rectangle([x, y + 24, x + larg_col[i], y + 24 + ALTURA], outline=(205, 205, 205))
        x += larg_col[i] + 10
    dr.text((10 + larg_col[0] + 10, y + 26 + ALTURA), "antes: " + t_antes, fill=(60, 60, 60), font=FONTE)
    dr.text((10 + larg_col[0] + 10, y + 26 + ALTURA + 22), "depois: " + t_depois, fill=(60, 60, 60), font=FONTE)
    y += alt_linha
folha.save(SAIDA)
print("ok", SAIDA, folha.size)
