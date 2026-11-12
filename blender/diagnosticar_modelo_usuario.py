"""Diagnostico do modelo do usuario: transformacoes reais (mundo), pose atual vs repouso, qualidade dos pesos
(vertices sem peso, soma dos pesos, influencias por vertice), grupos x ossos, e centro dos dedos/palma.
So le. Uso: blender -b <modelo.blend> --python diagnosticar_modelo_usuario.py -- <saida.txt>"""
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

arqs = sys.argv[sys.argv.index("--") + 1:]
saida = arqs[0]
L = []


def p(*a):
    L.append(" ".join(str(x) for x in a))


def v3(v):
    return "(%.4f, %.4f, %.4f)" % (v[0], v[1], v[2])


arm = bpy.data.objects["Armação"]
corpo = bpy.data.objects["NeoMetal"]
capa = bpy.data.objects["capa"]
dg = bpy.context.evaluated_depsgraph_get()

p("== MATRIZES DE MUNDO ==")
for o in (arm, corpo, capa):
    p(o.name, "pai", o.parent.name if o.parent else None)
    m = o.matrix_world
    for r in m:
        p("   ", "  ".join("%9.4f" % x for x in r))
    p("   parent_inverse")
    for r in o.matrix_parent_inverse:
        p("   ", "  ".join("%9.4f" % x for x in r))

p("")
p("== POSE ATUAL (ossos fora do repouso) ==")
fora = 0
for pb in arm.pose.bones:
    q = pb.rotation_quaternion
    desvio = abs(q.w - 1) + abs(q.x) + abs(q.y) + abs(q.z) + pb.location.length + (pb.scale - Vector((1, 1, 1))).length
    if desvio > 1e-5:
        fora += 1
        p("  ", pb.name, "quat", tuple(round(x, 4) for x in q), "loc", v3(pb.location), "esc", v3(pb.scale))
p("   ossos fora do repouso:", fora)

p("")
p("== GRUPOS x OSSOS ==")
nomes_ossos = {b.name for b in arm.data.bones}
for o in (corpo, capa):
    g = {vg.name for vg in o.vertex_groups}
    p(o.name, "grupos sem osso:", sorted(g - nomes_ossos), "| ossos sem grupo:", sorted(nomes_ossos - g))

p("")
p("== PESOS ==")
for o in (corpo, capa):
    me = o.data
    nv = len(me.vertices)
    soma = np.zeros(nv)
    ninf = np.zeros(nv, dtype=int)
    for v in me.vertices:
        s = 0.0
        n = 0
        for ge in v.groups:
            if ge.weight > 1e-4:
                s += ge.weight
                n += 1
        soma[v.index] = s
        ninf[v.index] = n
    p(o.name, "verts", nv, "sem peso:", int((ninf == 0).sum()), "soma<0.99:", int(((soma < 0.99) & (ninf > 0)).sum()),
      "soma>1.01:", int((soma > 1.01).sum()), "influencias max", int(ninf.max()),
      "dist influencias", {int(k): int((ninf == k).sum()) for k in np.unique(ninf)})
    # vertices por grupo dominante
    dom = {}
    for v in me.vertices:
        if not v.groups:
            continue
        gi = max(v.groups, key=lambda ge: ge.weight).group
        dom[o.vertex_groups[gi].name] = dom.get(o.vertex_groups[gi].name, 0) + 1
    p("   verts por grupo dominante:")
    for k in sorted(dom, key=lambda x: -dom[x]):
        p("      %5d  %s" % (dom[k], repr(k)))

p("")
p("== MALHA CORPO em mundo (avaliada, pose atual) ==")
ev = corpo.evaluated_get(dg)
me = ev.to_mesh()
co = np.array([(corpo.matrix_world @ v.co)[:] for v in me.vertices])
p("verts avaliados", len(co), "bbox x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f" % (co[:, 0].min(), co[:, 0].max(), co[:, 1].min(), co[:, 1].max(), co[:, 2].min(), co[:, 2].max()))
ev.to_mesh_clear()
me = corpo.data
co0 = np.array([(corpo.matrix_world @ v.co)[:] for v in me.vertices])
p("verts em repouso (dados brutos)", len(co0), "bbox x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f" % (co0[:, 0].min(), co0[:, 0].max(), co0[:, 1].min(), co0[:, 1].max(), co0[:, 2].min(), co0[:, 2].max()))

p("")
p("== CAPA em mundo (dados brutos) ==")
co1 = np.array([(capa.matrix_world @ v.co)[:] for v in capa.data.vertices])
p("verts", len(co1), "bbox x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f" % (co1[:, 0].min(), co1[:, 0].max(), co1[:, 1].min(), co1[:, 1].max(), co1[:, 2].min(), co1[:, 2].max()))
cl = [m for m in capa.modifiers if m.type == "CLOTH"]
if cl:
    c = cl[0]
    p("CLOTH: quadros", c.point_cache.frame_start, c.point_cache.frame_end, "grupo fixacao", repr(c.settings.vertex_group_mass),
      "massa", c.settings.mass, "show_viewport", c.show_viewport, "show_render", c.show_render)
for m in capa.modifiers:
    p("   modificador", m.name, m.type, "viewport", m.show_viewport, "render", m.show_render)

p("")
p("== CENTRO DOS DEDOS EM MUNDO (media dos vertices dominados por cada grupo da mao esquerda e direita) ==")
for lado in ("esquerdo", "direito"):
    for nome in [vg.name for vg in corpo.vertex_groups if lado in vg.name.lower() and ("polegar" in vg.name.lower() or "indicador" in vg.name.lower() or "medio" in vg.name.lower() or "anelar" in vg.name.lower() or "mindinho" in vg.name.lower() or "punho" in vg.name.lower())]:
        idx = corpo.vertex_groups[nome].index
        pts = [co0[v.index] for v in corpo.data.vertices if v.groups and max(v.groups, key=lambda ge: ge.weight).group == idx]
        if pts:
            pts = np.array(pts)
            p("  %-40s n=%4d centro (%.3f, %.3f, %.3f) z %.3f..%.3f" % (repr(nome), len(pts), *pts.mean(axis=0), pts[:, 2].min(), pts[:, 2].max()))
        else:
            p("  %-40s n=   0" % repr(nome))

texto = "\n".join(L)
open(saida, "w", encoding="utf-8").write(texto)
print(texto)
