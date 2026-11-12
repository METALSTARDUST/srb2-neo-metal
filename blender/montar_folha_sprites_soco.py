"""Folha de conferencia do soco TAL1 com os sprites 2D do Dark Sonic ao lado do Sonic X em 3D e do Neo (sem bpy; rodar com o Python do sistema: PIL).
Uma linha por quadro (A a D = 277 a 280 na forma Super): sprite 2D | Sonic X (lado) | Neo (lado) | Neo (3/4).
Na folha de sprites o A olha para a direita e o B, C e D para a esquerda; os renders 3D olham para a direita, entao o A fica como esta e o B, C e D sao espelhados.
Uso: python montar_folha_sprites_soco.py <pasta_dos_renders> <sprites_tal1.png> <saida.png> <quadros q,q,q,q> [<posicoes a espelhar, 0 a 3, padrao 1,2,3>]"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont, ImageOps

pasta, sprites, saida = sys.argv[1:4]
quadros = [int(x) for x in sys.argv[4].split(",")]
espelhar = {int(x) for x in sys.argv[5].split(",")} if len(sys.argv) > 5 else {1, 2, 3}
CEL = 420
ESCALA_SPRITE = 2
LACUNA = 20
FONTE = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 15)
LETRAS = "ABCDEFGH"


def recortar_sprites(caminho, quantos):
    """Tira o fundo (cor exata do canto) e separa os sprites pelas colunas vazias entre eles."""
    img = Image.open(caminho).convert("RGBA")
    fundo = img.getpixel((3, 3))[:3]
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            if px[x, y][:3] == fundo:
                px[x, y] = (0, 0, 0, 0)
    ocupadas = [any(px[x, y][3] for y in range(img.height)) for x in range(img.width)]
    grupos, inicio, vazias = [], None, 0
    for x, ocupada in enumerate(ocupadas + [False] * (LACUNA + 1)):
        if ocupada:
            if inicio is None:
                inicio = x
            vazias = 0
        elif inicio is not None:
            vazias += 1
            if vazias >= LACUNA:
                grupos.append((inicio, x - vazias))
                inicio = None
    if len(grupos) != quantos:
        sys.exit("esperava %d sprites na folha e achei %d" % (quantos, len(grupos)))
    return [img.crop((x0, 0, x1 + 1, img.height)).crop(img.crop((x0, 0, x1 + 1, img.height)).getbbox()) for x0, x1 in grupos]


def celula_3d(nome):
    img = Image.open(os.path.join(pasta, nome)).convert("RGBA").resize((CEL, CEL), Image.LANCZOS)
    fundo = Image.new("RGBA", img.size, "white")
    fundo.alpha_composite(img)
    return fundo.convert("RGB")


def celula_sprite(sprite):
    grande = sprite.resize((sprite.width * ESCALA_SPRITE, sprite.height * ESCALA_SPRITE), Image.NEAREST)
    fundo = Image.new("RGBA", (CEL, CEL), "white")
    fundo.alpha_composite(grande, ((CEL - grande.width) // 2, (CEL - grande.height) // 2))
    return fundo.convert("RGB")


recortes = recortar_sprites(sprites, len(quadros))
folha = Image.new("RGB", (CEL * 4, CEL * len(quadros)), "white")
d = ImageDraw.Draw(folha)
for i, q in enumerate(quadros):
    sprite = ImageOps.mirror(recortes[i]) if i in espelhar else recortes[i]
    celulas = [(celula_sprite(sprite), "quadro %d (%s) - sprite 2D Dark Sonic%s" % (q, LETRAS[i], ", espelhado" if i in espelhar else "")),
               (celula_3d("q%03d_ref_lado.png" % q), "Sonic X 3D (lado)"),
               (celula_3d("q%03d_neo_lado.png" % q), "Neo (lado)"),
               (celula_3d("q%03d_neo_34.png" % q), "Neo (3/4)")]
    for j, (img, texto) in enumerate(celulas):
        folha.paste(img, (j * CEL, i * CEL))
        d.text((j * CEL + 6, i * CEL + 4), texto, fill="black", font=FONTE)
folha.save(saida)
print("salvo", saida, folha.size, "sprites", [r.size for r in recortes], "espelhados", sorted(espelhar))
