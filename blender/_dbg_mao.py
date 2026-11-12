import os, sys
import bpy, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import usuario_neo as U, braco_poses as BP, perna_poses as PP
U.preparar(); BP.zerar()
for lado in U.LADOS: BP.fechar_mao(lado)
corpo = bpy.data.objects["NeoMetal"]
co = BP._coords(corpo)
for lado in U.LADOS:
    w = BP._pesos(lado, BP.GRUPOS_MAO)
    sel = w >= 0.5
    pts = co[sel]
    pb = BP.ossos_braco(lado)
    punho = np.array(BP.p_mundo(pb["palma"].head)[:])
    print(lado, "n", sel.sum(), "bbox min", pts.min(0).round(3), "max", pts.max(0).round(3), "centro", pts.mean(0).round(3), "punho(pose)", punho.round(3))
    nomes = {}
    for vg in corpo.vertex_groups:
        n = PP._sem_acento(vg.name)
        if PP.CHAVE_LADO[lado] in n and any(k in n for k in BP.GRUPOS_MAO):
            nomes[vg.name] = vg.index
    print("  grupos:", list(nomes))
    # vertices por grupo dominante
    idx2nome = {v:k for k,v in nomes.items()}
    cont = {}
    for v in corpo.data.vertices:
        if sel[v.index]:
            dom = max(v.groups, key=lambda g: g.weight)
            cont[dom.group] = cont.get(dom.group, 0) + 1
    print("  dominante:", {corpo.vertex_groups[k].name: c for k, c in cont.items()})
