"""Tira o peso dos dedos das pecas da cabeca do Neo, numa COPIA do .blend de trabalho (o arquivo do usuario nao e tocado).
No arquivo do usuario tres pecas que moram na cabeca tem peso em ossos de DEDO: o espinho comprido do lado esquerdo (ilha de 14 vertices, 8 a 25% no 'mindinho esquerdo 4'),
a peca de tras do pescoco do lado direito (16 vertices, 3 a 12% no 'mindinho direito 4') e, de leve, o outro espinho do lado esquerdo (16 vertices, 1%). Os gemeos do outro lado
sao 100% cabeca. Com a mao longe da cabeca (soco) o dedo puxa essas pecas e elas entortam ou esticam: no quadro B do soco o espinho esquerdo saia ate 0,69 m do lugar.
Cada vertice dessas ilhas passa a ter so o osso da cabeca, peso 1. Nada mais muda: forma, textura e os outros pesos ficam como estavam.
Acha as ilhas sozinho: ilha pequena (ate 40 vertices) com a cabeca em todos os vertices (>= 0,75) e algum peso em osso de dedo.
Uso: blender -b "<base>.blend" --python corrigir_espinhos_cabeca.py -- <saida.blend>"""
import os
import sys

import bpy
import numpy as np

arg = sys.argv[sys.argv.index("--") + 1:]
SAIDA = os.path.abspath(arg[0])
CABECA = "head (cabeça)"
DEDOS = ("indicador", "medio", "médio", "anelar", "mindinho", "polegar")
ESPERADAS = {1340, 2917, 3116}

obj = bpy.data.objects["NeoMetal"]
me = obj.data
n = len(me.vertices)
nomes = {vg.index: vg.name for vg in obj.vertex_groups}
ossos = {b.name for b in bpy.data.objects["Armação"].data.bones}
pai = list(range(n))


def achar(a):
    while pai[a] != a:
        pai[a] = pai[pai[a]]
        a = pai[a]
    return a


for p in me.polygons:
    vs = list(p.vertices)
    for v in vs[1:]:
        ra, rb = achar(vs[0]), achar(v)
        if ra != rb:
            pai[rb] = ra
raiz = np.array([achar(i) for i in range(n)])
pesos = [{nomes[g.group]: g.weight for g in v.groups if nomes[g.group] in ossos and g.weight > 1e-4} for v in me.vertices]

achadas = []
for r in np.unique(raiz):
    idx = np.flatnonzero(raiz == r)
    if len(idx) > 40:
        continue
    if min(pesos[i].get(CABECA, 0.0) for i in idx) < 0.75:
        continue
    if any(any(d in nome for d in DEDOS) for i in idx for nome in pesos[i]):
        achadas.append(int(r))
print("ilhas achadas:", achadas)
assert set(achadas) == ESPERADAS, "esperava %s e achei %s: confira o arquivo antes de gravar" % (sorted(ESPERADAS), sorted(achadas))

for r in achadas:
    idx = np.flatnonzero(raiz == r)
    antes = {}
    for i in idx:
        for nome, w in pesos[i].items():
            antes.setdefault(nome, []).append(w)
    print("ilha %d (%d vertices): antes %s" % (r, len(idx), {k: "%.3f..%.3f (%d)" % (min(v), max(v), len(v)) for k, v in antes.items()}))
    lista = [int(i) for i in idx]
    for nome in antes:
        if nome != CABECA:
            obj.vertex_groups[nome].remove(lista)
    obj.vertex_groups[CABECA].add(lista, 1.0, "REPLACE")

nomes = {vg.index: vg.name for vg in obj.vertex_groups}
for r in achadas:
    idx = np.flatnonzero(raiz == r)
    depois = {}
    for i in idx:
        for g in me.vertices[int(i)].groups:
            if nomes[g.group] in ossos and g.weight > 1e-4:
                depois.setdefault(nomes[g.group], []).append(g.weight)
    print("ilha %d: depois %s" % (r, {k: "%.3f..%.3f (%d)" % (min(v), max(v), len(v)) for k, v in depois.items()}))
    assert set(depois) == {CABECA} and min(depois[CABECA]) > 0.999 and len(depois[CABECA]) == len(idx)

bpy.ops.wm.save_as_mainfile(filepath=SAIDA)
print("salvo", SAIDA)
