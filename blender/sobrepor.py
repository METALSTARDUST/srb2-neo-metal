"""Neo por cima do fantasma (XSonic) para conferir encaixe e tamanho: o fantasma fica esmaecido embaixo e o Neo (tudo o que nao e fundo) em cima.
Uso: python sobrepor.py <saida.png> <modo 1|2> <rotulo> <ref.png> <neo.png> [<rotulo> <ref.png> <neo.png> ...]
modo 1: Neo por cima do fantasma esmaecido; modo 2: fantasma translucido por cima do Neo. Cada trio gera uma celula; as celulas ficam lado a lado."""
import sys

from PIL import Image, ImageChops, ImageDraw


def mascara_de(img):
    bg = img.getpixel((0, 0))
    dif = ImageChops.difference(img, Image.new("RGB", img.size, bg)).convert("L")
    return dif.point(lambda v: 255 if v > 10 else 0)


def sobrepor(ref, neo, alfa_fantasma=0.55):
    r = Image.open(ref).convert("RGB")
    n = Image.open(neo).convert("RGB")
    if MODO == "2":
        # fantasma translucido POR CIMA do Neo: onde os dois existem, a mistura mostra se coincidem
        saida = n.copy()
        mr = mascara_de(r)
        misto = Image.blend(n, r, 0.5)
        saida.paste(misto, mask=mr)
        return saida
    branco = Image.new("RGB", r.size, (255, 255, 255))
    fundo = Image.blend(r, branco, alfa_fantasma)
    saida = fundo.copy()
    saida.paste(n, mask=mascara_de(n))
    return saida


MODO = sys.argv[2]
saida = sys.argv[1]
trios = sys.argv[3:]
celulas = []
for i in range(0, len(trios), 3):
    rotulo, ref, neo = trios[i:i + 3]
    img = sobrepor(ref, neo)
    d = ImageDraw.Draw(img)
    d.text((8, 6), rotulo, fill=(0, 0, 0))
    celulas.append(img)
w, h = celulas[0].size
folha = Image.new("RGB", (w * len(celulas), h), (255, 255, 255))
for i, c in enumerate(celulas):
    folha.paste(c, (i * w, 0))
folha.save(saida)
print("salvo", saida, folha.size)
