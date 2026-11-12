"""Confere o .blend gerado: textura empacotada, vertices sem peso, ossos fora do repouso (so dedos devem estar)."""
import bpy

img = bpy.data.images["NEO_METAL.png"]
print("TEXTURA", tuple(img.size), "empacotada", bool(img.packed_file))
corpo = bpy.data.objects["NeoMetal"]
sem = sum(1 for v in corpo.data.vertices if not any(g.weight > 1e-4 for g in v.groups))
print("SEM_PESO", sem)
arm = bpy.data.objects["Armação"]
fora = []
for pb in arm.pose.bones:
    q = pb.rotation_quaternion
    if abs(q.w - 1) + abs(q.x) + abs(q.y) + abs(q.z) > 1e-5:
        fora.append(pb.name.strip())
print("OSSOS_FORA_DO_REPOUSO", len(fora))
nao_dedo = [n for n in fora if not any(k in n.lower() for k in ("indicador", "medio", "anelar", "mindinho", "polegar"))]
print("FORA_QUE_NAO_SAO_DEDO", nao_dedo)
print("CAPA oculta no viewport:", bpy.data.objects["capa"].hide_get(), "| tecido:", [m.name for m in bpy.data.objects["capa"].modifiers])
print("QUADRO", bpy.context.scene.frame_current)
