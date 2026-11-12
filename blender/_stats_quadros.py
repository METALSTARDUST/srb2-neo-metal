import bpy, numpy as np, re
obj = [o for o in bpy.data.objects if o.type == "MESH" and o.data.shape_keys][0]
kbs = obj.data.shape_keys.key_blocks
n = len(obj.data.vertices)
out = {}
for i in range(1, len(kbs)):
    a = np.empty(n * 3, dtype=np.float32); kbs[i].data.foreach_get("co", a); a = a.reshape(-1, 3)
    nome = re.sub(r"^\d+_", "", kbs[i].name).replace("SPR2_", "")
    nome = re.sub(r"\s*\d+$", "", nome)
    r = float(np.sqrt((a[:, 0] ** 2 + a[:, 1] ** 2).max()))
    d = out.setdefault(nome, [1e9, -1e9, 0.0, 0])
    d[0] = min(d[0], float(a[:, 2].min())); d[1] = max(d[1], float(a[:, 2].max())); d[2] = max(d[2], r); d[3] += 1
for k, v in out.items():
    print("%-12s n=%-3d z %6.2f..%6.2f  raio %5.2f" % (k, v[3], v[0], v[1], v[2]))
