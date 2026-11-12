"""Mede quanto cada ilha da cabeca sai do lugar em relacao a um corpo rigido que acompanha a cabeca, em cada quadro posado da cena (so le; nao grava nada).
Ajusta uma semelhanca (escala, rotacao, translacao: Umeyama) dos vertices 100% cabeca em repouso para os mesmos vertices na pose; essa e a posicao que uma ilha 100% cabeca
teria. A diferenca para a posicao real da ilha e o que o peso em outros ossos puxa.
Uso: blender -b <pasta>/cena_<quadros>.blend --python medir_deslocamento_cabeca.py -- <metricas.json> <raiz,raiz,...>
Imprime, por quadro e ilha, o deslocamento medio e maximo em metros da cena e em pixels do render (TAM 560) e a flexao do espinho: angulo entre o eixo do 1o e do 2o terco."""
import json
import sys

import bpy
import numpy as np

arg = sys.argv[sys.argv.index("--") + 1:]
met = json.load(open(arg[0]))
RAIZES = [int(x) for x in arg[1].split(",")]
TAM = 560
ESC = met["escala_render"]
CABECA = "head (cabeça)"

base = bpy.data.objects["NeoMetal"]
me = base.data
n = len(me.vertices)
nomes = {vg.index: vg.name for vg in base.vertex_groups}
pesos = [{nomes[g.group]: g.weight for g in v.groups if g.weight > 1e-4} for v in me.vertices]
cabeca_pura = np.array([abs(w.get(CABECA, 0.0) - 1.0) < 1e-3 and len(w) == 1 for w in pesos])

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


def mundo(obj):
    co = np.empty(len(obj.data.vertices) * 3)
    obj.data.vertices.foreach_get("co", co)
    mw = np.array(obj.matrix_world)
    return co.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]


def umeyama(a, b):
    """Escala s, rotacao R e translacao t que levam a em b (b ~ s R a + t)."""
    ma, mb = a.mean(axis=0), b.mean(axis=0)
    A, B = a - ma, b - mb
    U, S, Vt = np.linalg.svd(B.T @ A / len(a))
    D = np.eye(3)
    if np.linalg.det(U) * np.linalg.det(Vt) < 0:
        D[2, 2] = -1
    R = U @ D @ Vt
    s = np.trace(np.diag(S) @ D) / A.var(axis=0).sum()
    return s, R, mb - s * R @ ma


def flexao(p, idx):
    """Angulo (graus) entre o eixo do 1o terco e o do 2o terco do espinho: pontos ordenados pela distancia ate o ponto mais proximo da cabeca."""
    q = p[idx]
    c = q.mean(axis=0)
    u, s, vt = np.linalg.svd(q - c)
    eixo = vt[0]
    t = (q - c) @ eixo
    ordem = np.argsort(t)
    k = max(len(idx) // 3, 2)
    a = q[ordem[:k]].mean(axis=0), q[ordem[k:2 * k]].mean(axis=0), q[ordem[-k:]].mean(axis=0)
    v1, v2 = a[1] - a[0], a[2] - a[1]
    return float(np.degrees(np.arccos(np.clip(v1 @ v2 / (np.linalg.norm(v1) * np.linalg.norm(v2)), -1, 1))))


rep = mundo(base)
for obj in sorted((o for o in bpy.data.objects if o.name.startswith("NeoPose_")), key=lambda o: o.name):
    pose = mundo(obj)
    s, R, t = umeyama(rep[cabeca_pura], pose[cabeca_pura])
    esperado = (s * (R @ rep.T)).T + t
    res_ref = np.linalg.norm(pose[cabeca_pura] - esperado[cabeca_pura], axis=1)
    print("%s: ajuste da cabeca com %d vertices puros, escala %.3f, erro medio %.4f m maximo %.4f m" % (obj.name, cabeca_pura.sum(), s, res_ref.mean(), res_ref.max()))
    for r in RAIZES:
        idx = np.flatnonzero(raiz == r)
        dist = np.linalg.norm(pose[idx] - esperado[idx], axis=1)
        print("   ilha %5d (%2d vertices): sai do lugar em media %.3f m (%.1f px), no maximo %.3f m (%.1f px); flexao em repouso %.1f graus, na pose %.1f, se fosse rigida %.1f" % (
            r, len(idx), dist.mean(), dist.mean() / ESC * TAM, dist.max(), dist.max() / ESC * TAM, flexao(rep, idx), flexao(pose, idx), flexao(esperado, idx)))
