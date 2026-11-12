"""Inspeciona um .blend: objetos, malhas, esqueletos, ossos, grupos de vertices,
modificadores, materiais/imagens, acoes e linha do tempo. So le, nao grava."""
import sys

import bpy
from mathutils import Vector

arqs = sys.argv[sys.argv.index("--") + 1:]
saida = arqs[0] if arqs else None
linhas = []


def p(*a):
    linhas.append(" ".join(str(x) for x in a))


def v3(v):
    return "(%.4f, %.4f, %.4f)" % (v[0], v[1], v[2])


cena = bpy.context.scene
p("BLENDER", bpy.app.version_string, "ARQUIVO", bpy.data.filepath)
p("CENA", cena.name, "quadros", cena.frame_start, cena.frame_end, "atual", cena.frame_current,
  "fps", cena.render.fps, "unidade", cena.unit_settings.system, "escala", cena.unit_settings.scale_length)
p("OBJETOS", len(bpy.data.objects), "MALHAS", len(bpy.data.meshes), "ARMATURAS", len(bpy.data.armatures),
  "ACOES", len(bpy.data.actions), "MATERIAIS", len(bpy.data.materials), "IMAGENS", len(bpy.data.images))
p("-" * 70)

for o in bpy.data.objects:
    p("OBJ", repr(o.name), o.type, "pai=", o.parent.name if o.parent else None,
      "tipo_pai=", o.parent_type, "osso_pai=", o.parent_bone or None)
    p("   loc", v3(o.location), "rot", v3(o.rotation_euler), "esc", v3(o.scale), "modo_rot", o.rotation_mode)
    p("   dim", v3(o.dimensions), "oculto", o.hide_viewport, o.hide_render, o.hide_get() if hasattr(o, "hide_get") else "")
    p("   colecoes", [c.name for c in o.users_collection])
    if o.modifiers:
        p("   modificadores", [(m.name, m.type, getattr(m, "object", None) and m.object.name) for m in o.modifiers])
    if o.constraints:
        p("   constraints", [(c.name, c.type) for c in o.constraints])
    if o.type == "MESH":
        me = o.data
        p("   malha", repr(me.name), "verts", len(me.vertices), "arestas", len(me.edges), "faces", len(me.polygons),
          "tris", sum(len(pg.vertices) - 2 for pg in me.polygons))
        p("   grupos_de_vertices", len(o.vertex_groups))
        if o.vertex_groups:
            p("   ", [g.name for g in o.vertex_groups])
        p("   uv", [u.name for u in me.uv_layers], "materiais", [s.material.name if s.material else None for s in o.material_slots])
        if me.shape_keys:
            p("   shape_keys", [k.name for k in me.shape_keys.key_blocks])
        if me.vertices:
            xs = [v.co.x for v in me.vertices]
            ys = [v.co.y for v in me.vertices]
            zs = [v.co.z for v in me.vertices]
            p("   bbox_local x", "%.4f..%.4f" % (min(xs), max(xs)), "y", "%.4f..%.4f" % (min(ys), max(ys)),
              "z", "%.4f..%.4f" % (min(zs), max(zs)))
    if o.type == "ARMATURE":
        ar = o.data
        p("   esqueleto", repr(ar.name), "ossos", len(ar.bones), "pose_position", ar.pose_position,
          "display", ar.display_type)
        p("   colecoes_de_ossos", [c.name for c in ar.collections_all] if hasattr(ar, "collections_all") else None)
    if o.animation_data:
        p("   anim", o.animation_data.action.name if o.animation_data.action else None,
          "drivers", len(o.animation_data.drivers))
    p("")

p("-" * 70)
for o in bpy.data.objects:
    if o.type != "ARMATURE":
        continue
    ar = o.data
    p("ESQUELETO", o.name, "ossos", len(ar.bones))
    pm = o.matrix_world

    def imprime(b, nivel):
        cab = pm @ b.head_local
        cau = pm @ b.tail_local
        pb = o.pose.bones.get(b.name)
        extra = ""
        if pb is not None:
            extra = " rot_mode=%s" % pb.rotation_mode
        p("%s%s  cab=%s cauda=%s len=%.4f%s" % ("  " * nivel, b.name, v3(cab), v3(cau), b.length, extra))
        for f in b.children:
            imprime(f, nivel + 1)

    for raiz in [b for b in ar.bones if b.parent is None]:
        imprime(raiz, 0)
    p("")

p("-" * 70)
for im in bpy.data.images:
    p("IMG", repr(im.name), "arquivo", repr(im.filepath), "empacotada", bool(im.packed_file),
      "tam", tuple(im.size), "fonte", im.source)
for m in bpy.data.materials:
    p("MAT", repr(m.name), "nos", bool(m.use_nodes))
    if m.use_nodes and m.node_tree:
        for n in m.node_tree.nodes:
            if n.type == "TEX_IMAGE":
                p("   no_imagem", n.name, n.image.name if n.image else None)
            elif n.type == "BSDF_PRINCIPLED":
                p("   principled base_color", tuple(round(x, 3) for x in n.inputs["Base Color"].default_value))
for a in bpy.data.actions:
    fcs = list(a.fcurves) if hasattr(a, "fcurves") else []
    p("ACAO", repr(a.name), "intervalo", tuple(a.frame_range), "curvas", len(fcs))
p("MARCADORES", [(m.frame, m.name) for m in cena.timeline_markers])

texto = "\n".join(linhas)
if saida:
    with open(saida, "w", encoding="utf-8") as f:
        f.write(texto)
print(texto)
