"""Estado original (sem preparar) do .blend do usuario: visibilidade da capa, tecido, textura, quadro atual (somente leitura)."""
import bpy, numpy as np
for o in bpy.data.objects:
    print("%-10s tipo=%-8s hide_get=%s hide_viewport=%s hide_render=%s colecoes=%s" % (o.name, o.type, o.hide_get(), o.hide_viewport, o.hide_render, [c.name for c in o.users_collection]))
capa = bpy.data.objects["capa"]
for m in capa.modifiers:
    print("modificador", m.name, m.type, "viewport", m.show_viewport, "render", m.show_render)
print("loc local da capa", tuple(round(x, 4) for x in capa.location), "rot", tuple(round(x, 4) for x in capa.rotation_euler), "escala", tuple(capa.scale))
print("quadro atual", bpy.context.scene.frame_current, "inicio/fim", bpy.context.scene.frame_start, bpy.context.scene.frame_end)
for i in bpy.data.images:
    print("imagem", i.name, i.filepath, "existe:", __import__("os").path.exists(bpy.path.abspath(i.filepath)), "empacotada:", i.packed_file is not None)
print("armadura pose_position", bpy.data.objects["Armação"].data.pose_position)
arm = bpy.data.objects["Armação"]
pose_nao_zero = [pb.name for pb in arm.pose.bones if abs(pb.rotation_quaternion.w - 1) > 1e-6 or any(abs(x) > 1e-6 for x in pb.location)]
print("ossos fora do repouso:", pose_nao_zero)
