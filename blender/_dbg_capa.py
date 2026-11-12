"""Inspeciona a capa e o cinto: grupos de vertices com peso, ilhas, caixa de cada ilha, cloth e pose."""
import os, sys
import bpy, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import usuario_neo as U, braco_poses as BP, perna_poses as PP
sys.path.insert(0, r"C:\tmp\srb2-metal-homing\neo\fontes\blender")
import golpes_ref as G
U.preparar()
capa = bpy.data.objects["capa"]
me = capa.data
print("capa: vertices", len(me.vertices), "faces", len(me.polygons), "grupos", len(capa.vertex_groups))
w_por_grupo = {}
for v in me.vertices:
    for g in v.groups:
        if g.weight > 1e-4:
            w_por_grupo.setdefault(capa.vertex_groups[g.group].name, []).append(g.weight)
print("grupos com peso:", {k: (len(v), round(float(np.mean(v)), 2)) for k, v in w_por_grupo.items()})
sem = sum(1 for v in me.vertices if not any(g.weight > 1e-4 for g in v.groups))
print("vertices sem nenhum peso:", sem)
for m in capa.modifiers:
    print("modificador", m.name, m.type, "viewport", m.show_viewport, "render", m.show_render)
    if m.type == "CLOTH":
        s = m.settings
        print("   cloth: pin_group", repr(s.vertex_group_mass), "quality", s.quality, "mass", s.mass, "tension", s.tension_stiffness, "bending", s.bending_stiffness, "pin_stiffness", s.pin_stiffness)
        print("   cache frame_start", m.point_cache.frame_start, "end", m.point_cache.frame_end, "baked", m.point_cache.is_baked, "info", m.point_cache.info)
        print("   colisao:", m.collision_settings.use_collision, "obj", getattr(m.collision_settings, "collection", None))
# ilhas por conectividade
n = len(me.vertices)
tris = np.array([p.vertices[:] for p in me.polygons for _ in range(1)], dtype=object)
pai = list(range(n))
def achar(a):
    while pai[a] != a:
        pai[a] = pai[pai[a]]; a = pai[a]
    return a
for p in me.polygons:
    vs = list(p.vertices)
    r0 = achar(vs[0])
    for x in vs[1:]:
        pai[achar(x)] = r0
raiz = np.array([achar(i) for i in range(n)])
co = np.empty(n * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
m = np.array(capa.matrix_world); wco = co @ m[:3, :3].T + m[:3, 3]
print("ilhas:", len(set(raiz)))
for r in sorted(set(raiz), key=lambda r: wco[raiz == r][:, 2].max(), reverse=True)[:30]:
    pts = wco[raiz == r]
    print("  ilha %5d  n=%4d  centro %s  min %s  max %s" % (r, len(pts), pts.mean(0).round(3), pts.min(0).round(3), pts.max(0).round(3)))
# a capa segue o corpo?
BP.zerar()
dg = bpy.context.evaluated_depsgraph_get()
def centro():
    ev = capa.evaluated_get(dg); mm = ev.to_mesh()
    a = np.empty(len(mm.vertices) * 3); mm.vertices.foreach_get("co", a); ev.to_mesh_clear()
    return (a.reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]).mean(0)
c0 = centro()
import math
from mathutils import Matrix
R = Matrix.Rotation(math.radians(40), 3, "X")
BP.pose_corpo(R, (0, -0.5, 0))
dg = bpy.context.evaluated_depsgraph_get()
c1 = centro()
print("centro da capa em repouso", c0.round(3), "depois de girar o corpo 40 graus e andar -0,5 em Y", c1.round(3))
print("matriz_mundo da capa:\n", np.round(np.array(capa.matrix_world), 3), "\n matrix_parent_inverse:\n", np.round(np.array(capa.matrix_parent_inverse), 3))
