"""(Python do sistema, PIL) Desenha o JSON de _mapa_ilhas_dados.py pintando cada ilha de uma cor.
Uso: python _mapa_ilhas_desenho.py <entrada.json> <saida.png>"""
import colorsys
import json
import sys

from PIL import Image, ImageDraw, ImageFont

dados = json.load(open(sys.argv[1]))
tris, rotulos = dados["tris"], dados["rotulos"]
us = [p[0] for t in tris for p in t[:3]]
vs = [p[1] for t in tris for p in t[:3]]
u0, u1, v0, v1 = min(us), max(us), min(vs), max(vs)
esc = 1300 / max(u1 - u0, v1 - v0)
W, H = int((u1 - u0) * esc) + 60, int((v1 - v0) * esc) + 60
im = Image.new("RGB", (W, H), (236, 238, 242))
d = ImageDraw.Draw(im)
fonte = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 13)


def px(p):
    return (30 + (p[0] - u0) * esc, H - 30 - (p[1] - v0) * esc)


for t in sorted(tris, key=lambda t: t[5]):
    h = (t[3] * 0.137 + t[4] * 0.071) % 1.0
    cor = tuple(int(c * 255) for c in colorsys.hsv_to_rgb(h, 0.55, 0.95))
    d.polygon([px(p) for p in t[:3]], fill=cor, outline=(70, 70, 70))
for u, v, txt, n in rotulos:
    x, y = px((u, v))
    d.text((x - 10, y - 6), txt, fill=(0, 0, 0), font=fonte)
im.save(sys.argv[2])
print("ok", sys.argv[2], im.size)
