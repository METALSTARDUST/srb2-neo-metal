"""Gruda o cinto do Neo (aro, tachas e tiras, que moram no objeto 'capa') no corpo, numa COPIA do .blend do usuario.
No arquivo do usuario a capa com o cinto esta 1,8 m atras do corpo (objeto movido em Y), as 17 tachas do aro e as 2 tiras penduradas nao tem
peso em nenhum osso (so estao no grupo do tecido) e por isso ficam paradas no mundo quando o corpo mexe. O que este script faz:
1. move a capa (o cinto vai junto) para o aro ficar centrado no eixo vertical da pelve, na mesma altura que ja estava;
2. cada tacha e cada tira ganha, como bloco unico, o peso dos ossos do ponto do aro mais perto dela (o aro e a capa ficam como o usuario pintou);
3. as tiras entram no grupo de fixacao do tecido (peso 1), como as tachas, para o tecido nao derrubar;
4. mostra a capa (estava escondida) e aponta a textura para o arquivo que existe neste PC.
Nada mais muda: pose, ossos, cloth, malha do corpo e pesos do corpo ficam como estavam.
Uso: blender -b "<original>.blend" --python corrigir_cinto.py -- <saida.blend>"""
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix

arg = sys.argv[sys.argv.index("--") + 1:]
SAIDA = os.path.abspath(arg[0])
TEXTURA = r"C:\tmp\srb2-metal-homing\neo\pacote-blender\neo-metal\NEO_METAL.png"
GRUPO_TECIDO = "capa_fixacao"

capa = bpy.data.objects["capa"]
arm = bpy.data.objects["Armação"]
me = capa.data
n = len(me.vertices)
nomes = {vg.index: vg.name for vg in capa.vertex_groups}


def pesos_osso(i):
    """Pesos de osso do vertice i (tudo menos o grupo do tecido)."""
    return {nomes[g.group]: g.weight for g in me.vertices[i].groups if g.weight > 1e-4 and nomes[g.group] != GRUPO_TECIDO}


# ilhas por conectividade
pai = list(range(n))


def achar(a):
    while pai[a] != a:
        pai[a] = pai[pai[a]]
        a = pai[a]
    return a


for p in me.polygons:
    vs = list(p.vertices)
    r0 = achar(vs[0])
    for x in vs[1:]:
        pai[achar(x)] = r0
raiz = np.array([achar(i) for i in range(n)])
ilhas = {r: np.where(raiz == r)[0] for r in set(raiz)}
saia = max(ilhas, key=lambda r: len(ilhas[r]))
cinto = [r for r in ilhas if r != saia]

co = np.empty(n * 3)
me.vertices.foreach_get("co", co)
co = co.reshape(-1, 3)
m = np.array(capa.matrix_world)
mundo = co @ m[:3, :3].T + m[:3, 3]

# 1. posicao: centro do aro (ilhas do cinto que ja tem peso de osso e mais de 25 vertices) para o eixo da pelve
com_peso = {r: [i for i in ilhas[r] if sum(pesos_osso(i).values()) > 0.5] for r in cinto}
aro = [r for r in cinto if len(ilhas[r]) > 25 and len(com_peso[r]) == len(ilhas[r])]
pts_aro = mundo[np.concatenate([ilhas[r] for r in aro])]
centro_aro = (pts_aro.min(axis=0) + pts_aro.max(axis=0)) / 2
pelve = arm.matrix_world @ arm.pose.bones["spine (espinha vertebral)"].bone.head_local
delta = np.array([pelve.x - centro_aro[0], pelve.y - centro_aro[1], 0.0])
capa.matrix_world = Matrix.Translation(delta) @ capa.matrix_world
print("aro: %d ilhas, centro %s; pelve %s; capa movida por %s" % (len(aro), centro_aro.round(3), np.array(pelve[:]).round(3), delta.round(3)))

# 2. pesos: tacha ou tira sem peso de osso copia, como bloco, os pesos do ponto de aro mais perto do seu centro
fontes = [int(i) for r in aro for i in ilhas[r]]
sem_peso = [r for r in cinto if len(com_peso[r]) == 0]
fonte_pts = mundo[fontes]
for r in sem_peso:
    idx = ilhas[r]
    centro = mundo[idx].mean(axis=0)
    perto = fontes[int(np.argmin(np.linalg.norm(fonte_pts - centro, axis=1)))]
    w = pesos_osso(perto)
    for nome, valor in w.items():
        capa.vertex_groups[nome].add([int(i) for i in idx], valor, "REPLACE")
    print("ilha de %2d vertices em %s ganhou os pesos de %s" % (len(idx), centro.round(2), {k: round(v, 2) for k, v in w.items()}))

# 3. as ilhas fora do grupo do tecido entram nele (peso 1)
vg = capa.vertex_groups[GRUPO_TECIDO]
fora = [int(i) for r in cinto for i in ilhas[r] if not any(nomes[g.group] == GRUPO_TECIDO and g.weight > 0 for g in me.vertices[i].groups)]
if fora:
    vg.add(fora, 1.0, "REPLACE")
print("vertices do cinto postos no grupo do tecido:", len(fora))

# 4. capa visivel e textura
capa.hide_set(False)
img = bpy.data.images.get("NEO_METAL.png")
if img is not None and os.path.exists(TEXTURA):
    img.filepath = TEXTURA
bpy.ops.wm.save_as_mainfile(filepath=SAIDA)
print("salvo", SAIDA)
