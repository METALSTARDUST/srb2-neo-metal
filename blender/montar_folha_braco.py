"""Folha de uma parte do chute (bracos e maos), corpo todo: uma linha por quadro, 4 colunas = Sonic X (de lado) | Neo + contorno do Sonic X (de lado) | Sonic X (3/4) | Neo + contorno (3/4).
Embaixo de cada quadro, as medidas dos dois bracos (direita P e esquerda Q) contra o Sonic X. Os closes de cada braco vem de montar_antes_depois_braco.py.
Uso: python montar_folha_braco.py <pasta da rodada> <saida.png> <titulo> [<altura da celula, padrao 420>]
Os centimetros da legenda estao no tamanho do Neo na cena (corpo x escala_corpo)."""
import json
import math
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

PASTA, SAIDA, TITULO = sys.argv[1], sys.argv[2], sys.argv[3]
ALTURA = int(sys.argv[4]) if len(sys.argv) > 4 else 420
QUADROS = [(273, "A - preparacao"), (274, "B - passo"), (275, "C - impacto"), (276, "D - perna esticada")]
FONTE = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 16)
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
    return ImageChops.subtract(m.filter(ImageFilter.MaxFilter(2 * espessura + 1)), m.filter(ImageFilter.MinFilter(2 * espessura + 1)))


def uniao(*caixas):
    caixas = [c for c in caixas if c is not None]
    return (min(c[0] for c in caixas), min(c[1] for c in caixas), max(c[2] for c in caixas), max(c[3] for c in caixas))


def norm(v):
    return math.sqrt(sum(x * x for x in v))


def sub(a, b):
    return [x - y for x, y in zip(a, b)]


def angulo(a, b):
    n = norm(a) * norm(b)
    return 0.0 if n < 1e-9 else math.degrees(math.acos(max(-1.0, min(1.0, sum(x * y for x, y in zip(a, b)) / n))))


def celulas(q, vista):
    ref, m_ref = abrir(os.path.join(PASTA, "q%03d_ref_%s.png" % (q, vista)))
    neo, m_neo = abrir(os.path.join(PASTA, "q%03d_neosocapa_%s.png" % (q, vista)))
    caixa = uniao(m_ref.getbbox(), m_neo.getbbox())
    pad = 12
    caixa = (max(caixa[0] - pad, 0), max(caixa[1] - pad, 0), min(caixa[2] + pad, ref.width), min(caixa[3] + pad, ref.height))
    sobre = neo.copy()
    sobre.paste(Image.new("RGB", sobre.size, MAGENTA), (0, 0), contorno(m_ref, 2))
    return ref.crop(caixa), sobre.crop(caixa)


def redimensionar(im):
    return im.resize((max(1, int(im.width * ALTURA / im.height)), ALTURA), Image.LANCZOS)


def linha_braco(b, rotulo):
    cotovelo = angulo(sub(b["cotovelo"], b["ombro"]), sub(b["pulso"], b["cotovelo"]))
    haste = b["esticou"] * J["escala_corpo"] * 100
    return "%s: mao a %.0f cm da luva, aponta %.0f graus fora; braco %.0f graus fora; punho dobra %.0f (Sonic X %.0f); cotovelo dobra %.0f; haste %s %.0f cm" % (
        rotulo, b["erro_centro"] * J["escala_corpo"] * 100, b["erro_dir_mao"], b["erro_dir_braco"], b["punho_neo"], b["punho_ref"], cotovelo,
        "esticou" if haste >= 0 else "encolheu", abs(haste))


linhas = []
for q, nome in QUADROS:
    ref_l, neo_l = celulas(q, "lado")
    ref_3, neo_3 = celulas(q, "34")
    mn = J["quadros"][str(q)]["medidas_neo"]
    texto = [linha_braco(mn["bracos"]["P"], "direita (P)"), linha_braco(mn["bracos"]["Q"], "esquerda (Q)")]
    linhas.append((nome, [redimensionar(ref_l), redimensionar(neo_l), redimensionar(ref_3), redimensionar(neo_3)], texto))

rotulos = ["Sonic X, de lado", "Neo com o contorno, de lado", "Sonic X, 3/4", "Neo com o contorno, 3/4"]
larg_col = [max(l[1][i].width for l in linhas) for i in range(4)]
largura = sum(larg_col) + 10 * 5
alt_linha = ALTURA + 84
folha = Image.new("RGB", (largura, 86 + alt_linha * len(linhas)), (255, 255, 255))
dr = ImageDraw.Draw(folha)
dr.text((10, 8), TITULO, fill=(0, 0, 0), font=FONTE_B)
dr.text((10, 34), "Contorno magenta = Sonic X por cima do Neo. As renders do Neo estao sem a capa. 'aponta N graus fora' = direcao da mao (punho -> centro da luva) contra a do Sonic X.", fill=(70, 70, 70), font=FONTE)
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
        dr.text((10, y + 26 + ALTURA + 20 * k), t, fill=(60, 60, 60), font=FONTE)
    y += alt_linha
folha.save(SAIDA)
print("ok", SAIDA, folha.size)
