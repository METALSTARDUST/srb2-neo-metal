"""Faz as pecas soltas do corpo do Neo (ilhas sem peso de osso) seguirem o osso mais proximo, numa COPIA do .blend de trabalho.
No arquivo do usuario 12 ilhas pequenas de 'NeoMetal' (429 vertices: detalhes do peito e da cintura, 4 detalhes das canelas, uma pecinha de dedo e uma da lateral do quadril)
nao tem peso em osso nenhum, entao ficam paradas no mundo quando o corpo mexe (a do dedo fica flutuando no ar). Cada ilha ganha, como bloco unico,
os pesos do vertice com peso mais perto do centro dela. Nada mais muda: forma, textura e pesos ja pintados ficam como estavam.
Uso: blender -b "<base>.blend" --python corrigir_ilhas_sem_peso.py -- <saida.blend>"""
import os
import sys

import bpy
import numpy as np

arg = sys.argv[sys.argv.index("--") + 1:]
SAIDA = os.path.abspath(arg[0])
# as ombreiras (ilhas de 56 vertices) ficam logo acima do ombro, a menos de 0,15 da cabeca do osso do braco: elas seguem o OMBRO (o tronco) e nao o braco,
# senao esticam junto com a haste do braco
LIMITE_OMBREIRA = 0.15

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
    r0 = achar(vs[0])
    for x in vs[1:]:
        pai[achar(x)] = r0
raiz = np.array([achar(i) for i in range(n)])

co = np.empty(n * 3)
me.vertices.foreach_get("co", co)
co = co.reshape(-1, 3)
m = np.array(obj.matrix_world)
mundo = co @ m[:3, :3].T + m[:3, 3]

pesos = [{nomes[g.group]: g.weight for g in v.groups if nomes[g.group] in ossos and g.weight > 1e-4} for v in me.vertices]
total = np.array([sum(w.values()) for w in pesos])
com_peso = total >= 0.5

for r in sorted(set(raiz)):
    idx = np.where(raiz == r)[0]
    if (~com_peso[idx]).mean() < 0.5:
        continue
    centro = mundo[idx].mean(axis=0)
    candidatos = np.where(com_peso)[0]
    perto = int(candidatos[np.argmin(np.linalg.norm(mundo[candidatos] - centro, axis=1))])
    w = pesos[perto]
    nome_braco = next(iter(w)) if len(w) == 1 else ""
    if nome_braco.startswith("braço") and "ombro " + nome_braco.split()[-1] in obj.vertex_groups:
        osso_braco = bpy.data.objects["Armação"].data.bones[nome_braco]
        cabeca = np.array(bpy.data.objects["Armação"].matrix_world @ osso_braco.head_local)
        eixo = np.array(bpy.data.objects["Armação"].matrix_world @ osso_braco.tail_local) - cabeca
        if (centro - cabeca) @ (eixo / np.linalg.norm(eixo)) < LIMITE_OMBREIRA:
            w = {"ombro " + nome_braco.split()[-1]: 1.0}
    for nome, valor in w.items():
        obj.vertex_groups[nome].add([int(i) for i in idx], valor, "REPLACE")
    print("ilha de %2d vertices em %s ganhou os pesos de %s" % (len(idx), centro.round(2), {k: round(v, 2) for k, v in w.items()}))

bpy.ops.wm.save_as_mainfile(filepath=SAIDA)
print("salvo", SAIDA)
