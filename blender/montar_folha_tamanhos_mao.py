"""Folha de comparacao do tamanho da mao e da manopla no soco, e do pe e da perna (sem bpy; rodar com o Python do anaconda: PIL).
Uma coluna para o Sonic X e uma por versao do Neo (pasta de saida de golpes_soco.py, por exemplo rodado com o 4o argumento mao_soco ou o 5o escala_perna); uma linha por vista.
Vistas (opcao --vistas=, padrao mao,mao34): mao (lado), mao34 (3/4), braco (o braco inteiro, do ombro ao punho), pernas (as duas pernas de lado), pernas34 (3/4),
lado e 34 (o corpo inteiro de lado e em 3/4).
Uso: python montar_folha_tamanhos_mao.py [--vistas=mao,mao34,braco] <saida.png> <quadro> <pasta_da_referencia> "<texto da referencia>" <pasta_neo> "<texto>" [<pasta_neo> "<texto>" ...]"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

args = sys.argv[1:]
vistas_pedidas = args.pop(0).split("=", 1)[1] if args and args[0].startswith("--vistas=") else "mao,mao34"
saida, quadro, pasta_ref, texto_ref = args[0], int(args[1]), args[2], args[3]
neos = list(zip(args[4::2], args[5::2]))
CEL = 420
FONTE = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 15)
NOMES_VISTA = {"mao": "lado", "mao34": "3/4", "braco": "braço", "pernas": "pernas, lado", "pernas34": "pernas, 3/4", "lado": "corpo, lado", "34": "corpo, 3/4",
               "neosocapa_lado": "sem capa, lado"}
VISTAS = tuple((v, NOMES_VISTA[v]) for v in vistas_pedidas.split(","))


def celula(caminho):
    img = Image.open(caminho).convert("RGBA").resize((CEL, CEL), Image.LANCZOS)
    fundo = Image.new("RGBA", img.size, "white")
    fundo.alpha_composite(img)
    return fundo.convert("RGB")


colunas = [("ref", pasta_ref, texto_ref)] + [("neo", p, t) for p, t in neos]
folha = Image.new("RGB", (CEL * len(colunas), CEL * len(VISTAS)), "white")
d = ImageDraw.Draw(folha)
for i, (sufixo, nome_vista) in enumerate(VISTAS):
    for j, (quem, pasta, texto) in enumerate(colunas):
        folha.paste(celula(os.path.join(pasta, "q%03d_%s_%s.png" % (quadro, quem, sufixo))), (j * CEL, i * CEL))
        d.text((j * CEL + 6, i * CEL + 4), "%s (%s)" % (texto, nome_vista), fill="black", font=FONTE)
folha.save(saida)
print("salvo", saida, folha.size)
