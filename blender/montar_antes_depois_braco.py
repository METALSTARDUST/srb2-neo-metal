"""Antes e depois de uma parte do chute (bracos e maos) na MESMA camera: Sonic X | Neo antes | Neo depois, uma linha por quadro, o close de um braco, com o contorno do Sonic X em magenta.
Uso: python montar_antes_depois_braco.py <pasta antes> <pasta depois> <saida.png> <braco: P|Q> <vista: lado|34> <titulo> [<tamanho da celula, padrao 520>]
As pastas sao rodadas de golpes_chute.py com a mesma NEO_CAMERA_JSON (assim o enquadramento e igual); P e o braco direito (o do lado da perna que chuta), Q o esquerdo.
Os centimetros da legenda estao no tamanho do Neo na cena (corpo x escala_corpo)."""
import json
import math
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ANTES, DEPOIS, SAIDA, BRACO, VISTA, TITULO = sys.argv[1:7]
TAM = int(sys.argv[7]) if len(sys.argv) > 7 else 520
QUADROS = [(273, "A - preparacao"), (274, "B - passo"), (275, "C - impacto"), (276, "D - perna esticada")]
FONTE = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 16)
FONTE_B = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 19)
MAGENTA = (230, 0, 200)
SUFIXO = "braco" + BRACO + ("" if VISTA == "lado" else "34")
NOME = {"P": "direito (P)", "Q": "esquerdo (Q)"}[BRACO]


def abrir(caminho):
    img = Image.open(caminho).convert("RGBA")
    fundo = Image.new("RGBA", img.size, (255, 255, 255, 255))
    fundo.alpha_composite(img)
    return fundo.convert("RGB"), img.getchannel("A").point(lambda v: 255 if v > 10 else 0)


def contorno(m, espessura=2):
    return ImageChops.subtract(m.filter(ImageFilter.MaxFilter(2 * espessura + 1)), m.filter(ImageFilter.MinFilter(2 * espessura + 1)))


def norm(v):
    return math.sqrt(sum(x * x for x in v))


def sub(a, b):
    return [x - y for x, y in zip(a, b)]


def angulo(a, b):
    n = norm(a) * norm(b)
    return 0.0 if n < 1e-9 else math.degrees(math.acos(max(-1.0, min(1.0, sum(x * y for x, y in zip(a, b)) / n))))


def medidas(pasta, q):
    J = json.load(open(os.path.join(pasta, "metricas_273_274_275_276.json")))
    b = J["quadros"][str(q)]["medidas_neo"]["bracos"][BRACO]
    cotovelo = angulo(sub(b["cotovelo"], b["ombro"]), sub(b["pulso"], b["cotovelo"]))
    dir_mao = "mao %.0f graus fora da luva" % b["erro_dir_mao"] if "erro_dir_mao" in b else None
    punho = "punho dobra %.0f (Sonic X %.0f)" % (b["punho_neo"], b["punho_ref"]) if "punho_neo" in b else None
    partes = [p for p in (dir_mao, punho) if p]
    haste = b["esticou"] * J["escala_corpo"] * 100
    partes += ["cotovelo dobra %.0f graus" % cotovelo, ("haste esticou %.0f cm" % haste) if haste >= 0 else ("haste encolheu %.0f cm" % -haste)]
    return ", ".join(partes)


linhas = []
for q, nome in QUADROS:
    ref, m_ref = abrir(os.path.join(DEPOIS, "q%03d_ref_%s.png" % (q, SUFIXO)))
    antes, _ = abrir(os.path.join(ANTES, "q%03d_neo_%s.png" % (q, SUFIXO)))
    depois, _ = abrir(os.path.join(DEPOIS, "q%03d_neo_%s.png" % (q, SUFIXO)))
    celulas = [ref]
    for img in (antes, depois):
        sobre = img.copy()
        sobre.paste(Image.new("RGB", sobre.size, MAGENTA), (0, 0), contorno(m_ref, 2))
        celulas.append(sobre)
    linhas.append((nome, [c.resize((TAM, TAM), Image.LANCZOS) for c in celulas], (medidas(ANTES, q), medidas(DEPOIS, q))))

rotulos = ["Sonic X", "Neo ANTES", "Neo DEPOIS"]
largura = TAM * 3 + 10 * 4
alt_linha = TAM + 70
folha = Image.new("RGB", (largura, 86 + alt_linha * len(linhas)), (255, 255, 255))
dr = ImageDraw.Draw(folha)
dr.text((10, 8), TITULO, fill=(0, 0, 0), font=FONTE_B)
dr.text((10, 34), "Contorno magenta = Sonic X por cima do Neo. Mesma camera nas tres colunas. Braco %s. Vista: %s." % (NOME, "de lado" if VISTA == "lado" else "3/4"), fill=(70, 70, 70), font=FONTE)
for i in range(3):
    dr.text((10 + i * (TAM + 10) + 4, 62), rotulos[i], fill=(0, 0, 0), font=FONTE_B)
y = 86
for nome, ims, (t_antes, t_depois) in linhas:
    dr.text((10, y), nome, fill=(0, 0, 0), font=FONTE_B)
    for i, im in enumerate(ims):
        x = 10 + i * (TAM + 10)
        folha.paste(im, (x, y + 24))
        dr.rectangle([x, y + 24, x + TAM, y + 24 + TAM], outline=(205, 205, 205))
    dr.text((10 + TAM + 10, y + 26 + TAM), "antes: " + t_antes, fill=(60, 60, 60), font=FONTE)
    dr.text((10 + TAM + 10, y + 26 + TAM + 20), "depois: " + t_depois, fill=(60, 60, 60), font=FONTE)
    y += alt_linha
folha.save(SAIDA)
print("ok", SAIDA, folha.size)
