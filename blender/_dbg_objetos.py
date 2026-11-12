"""Lista os objetos do .blend do Neo: tipo, pai, modificadores, vertices, grupos de vertices e caixa (em repouso)."""
import os, sys
import bpy, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import usuario_neo as U
U.preparar()
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
for o in bpy.data.objects:
    info = "%-22s tipo=%-9s pai=%-12s tipo_pai=%-8s osso_pai=%-6s hide_vp=%s hide_r=%s" % (o.name, o.type, o.parent.name if o.parent else None, o.parent_type if o.parent else "-", o.parent_bone or "-", o.hide_viewport, o.hide_render)
    print(info)
    print("    matriz_mundo translacao", np.round(np.array(o.matrix_world)[:3, 3], 3), "escala", np.round(np.array(o.matrix_world.to_scale()), 3))
    if o.type == "MESH":
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        a = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", a); a = a.reshape(-1, 3)
        m = np.array(o.matrix_world); w = a @ m[:3, :3].T + m[:3, 3]
        print("    vertices", len(me.vertices), "faces", len(me.polygons), "modificadores", [(md.name, md.type, getattr(md, "object", None) and md.object.name, md.show_viewport) for md in o.modifiers],
              "grupos", len(o.vertex_groups), "materiais", [s.material.name if s.material else None for s in o.material_slots])
        print("    caixa mundo (avaliada) min", w.min(0).round(3), "max", w.max(0).round(3))
        ev.to_mesh_clear()
