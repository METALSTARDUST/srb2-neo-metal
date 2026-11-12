"""Monta as folhas de conferencia do soco a partir dos renders de golpes_soco.py (sem bpy; rodar com o Python do anaconda: PIL).
Folha do corpo: uma linha por quadro, colunas Sonic X (lado) | Neo (lado) | Neo (3/4).
Folha da mao: uma linha por quadro, colunas Sonic X | Neo, em close na mao que soca (mostra a luva e a manopla crescendo).
Uso: python montar_folha_soco.py <pasta_dos_renders> <saida_corpo.png> <saida_mao.png> <quadros q,q,q> [<quadros_mao q,q,q>]"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

pasta, saida_corpo, saida_mao = sys.argv[1:4]
quadros = [int(x) for x in sys.argv[4].split(",")]
quadros_mao = [int(x) for x in sys.argv[5].split(",")] if len(sys.argv) > 5 else quadros
CEL = 420
FONTE = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 15)


def celula(nome):
    img = Image.open(os.path.join(pasta, nome)).convert("RGBA").resize((CEL, CEL), Image.LANCZOS)
    fundo = Image.new("RGBA", img.size, "white")
    fundo.alpha_composite(img)
    return fundo


def folha(linhas, colunas, rotulos, saida):
    """linhas: lista de quadros; colunas: lista de (sufixo do arquivo, texto); rotulos: texto da linha por quadro."""
    img = Image.new("RGB", (CEL * len(colunas), CEL * len(linhas)), "white")
    d = ImageDraw.Draw(img)
    for i, q in enumerate(linhas):
        for j, (sufixo, texto) in enumerate(colunas):
            img.paste(celula("q%03d_%s.png" % (q, sufixo)).convert("RGB"), (j * CEL, i * CEL))
            d.text((j * CEL + 6, i * CEL + 4), "quadro %d - %s" % (q, texto), fill="black", font=FONTE)
    img.save(saida)
    print("salvo", saida, img.size)


folha(quadros, [("ref_lado", "Sonic X (Dark)"), ("neo_lado", "Neo (lado)"), ("neo_34", "Neo (3/4)")], None, saida_corpo)
folha(quadros_mao, [("ref_mao", "Sonic X, mao"), ("neo_mao", "Neo, mao")], None, saida_mao)
