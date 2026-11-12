"""Folhas de antes e depois de duas rodadas de golpes_soco.py (sem bpy; rodar com o Python do sistema: PIL). As duas rodadas tem que usar a mesma camera (NEO_CAMERA_JSON).
Modo quadros: uma coluna por quadro, linha de cima = antes, linha de baixo = depois, do arquivo inteiro. Cada item de <quadros> e "q" (usa o sufixo padrao) ou "q:sufixo" (outro arquivo).
  python montar_antes_depois.py quadros <saida.png> <pasta_antes> <pasta_depois> <sufixo do arquivo, ex. neo_lado> <quadros q,q:suf,q> [<texto antes> <texto depois> [<celula px>]]
Modo recorte: o mesmo retangulo (pixels do render) cortado dos dois e ampliado; uma linha por recorte, antes | depois.
  python montar_antes_depois.py recorte <saida.png> <pasta_antes> <pasta_depois> <texto antes> <texto depois> <zoom> <arquivo:u0,v0,u1,v1> [<arquivo:u0,v0,u1,v1> ...]"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

FONTE = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 16)


def abrir(caminho):
    img = Image.open(caminho).convert("RGBA")
    fundo = Image.new("RGBA", img.size, "white")
    fundo.alpha_composite(img)
    return fundo.convert("RGB")


def rotular(folha, x, y, texto):
    d = ImageDraw.Draw(folha)
    largura = d.textlength(texto, font=FONTE)
    d.rectangle((x, y, x + largura + 10, y + 24), fill="white")
    d.text((x + 5, y + 3), texto, fill="black", font=FONTE)


modo, saida, antes, depois = sys.argv[1:5]
if modo == "quadros":
    sufixo = sys.argv[5]
    itens = []
    for token in sys.argv[6].split(","):
        q, _, suf = token.partition(":")
        itens.append((int(q), suf or sufixo))
    texto_a = sys.argv[7] if len(sys.argv) > 7 else "antes"
    texto_d = sys.argv[8] if len(sys.argv) > 8 else "depois"
    cel = int(sys.argv[9]) if len(sys.argv) > 9 else 420
    folha = Image.new("RGB", (cel * len(itens), cel * 2), "white")
    for i, (q, suf) in enumerate(itens):
        for j, (pasta, texto) in enumerate(((antes, texto_a), (depois, texto_d))):
            img = abrir(os.path.join(pasta, "q%03d_%s.png" % (q, suf))).resize((cel, cel), Image.LANCZOS)
            folha.paste(img, (i * cel, j * cel))
            rotular(folha, i * cel + 4, j * cel + 4, "quadro %d (%s) - %s" % (q, suf.replace("neo_", ""), texto))
elif modo == "recorte":
    texto_a, texto_d, zoom = sys.argv[5], sys.argv[6], float(sys.argv[7])
    pedidos = []
    for p in sys.argv[8:]:
        arquivo, caixa = p.split(":")
        pedidos.append((arquivo, [int(x) for x in caixa.split(",")]))
    linhas = []
    for arquivo, (u0, v0, u1, v1) in pedidos:
        tam = (int((u1 - u0) * zoom), int((v1 - v0) * zoom))
        linhas.append([abrir(os.path.join(pasta, arquivo)).crop((u0, v0, u1, v1)).resize(tam, Image.LANCZOS) for pasta in (antes, depois)])
    larg = max(l[0].width for l in linhas)
    folha = Image.new("RGB", (larg * 2 + 12, sum(l[0].height for l in linhas) + 6 * len(linhas)), "white")
    y = 0
    for (arquivo, _), (a, d) in zip(pedidos, linhas):
        folha.paste(a, (0, y))
        folha.paste(d, (larg + 12, y))
        rotular(folha, 4, y + 4, "%s - %s" % (arquivo.replace(".png", ""), texto_a))
        rotular(folha, larg + 16, y + 4, "%s - %s" % (arquivo.replace(".png", ""), texto_d))
        y += a.height + 6
else:
    sys.exit("modo desconhecido: %s" % modo)
folha.save(saida)
print("salvo", saida, folha.size)
