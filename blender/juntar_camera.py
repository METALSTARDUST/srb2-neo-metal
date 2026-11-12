"""Junta as cameras (centros, escala_render, pernas_cam) de varias rodadas do golpes_soco.py num camera_*.json para NEO_CAMERA_JSON.
Uso: python juntar_camera.py <saida.json> <metricas_a.json> [<metricas_b.json> ...]
escala_render = a maior das rodadas (tudo cabe)."""
import json
import sys

saida, fontes = sys.argv[1], sys.argv[2:]
cam = {"centros": {}, "pernas_cam": {}, "escala_render": 0.0}
for f in fontes:
    m = json.load(open(f))
    cam["centros"].update({str(k): v for k, v in m["centros"].items()})
    cam["pernas_cam"].update({str(k): v for k, v in m.get("pernas_cam", {}).items()})
    cam["escala_render"] = max(cam["escala_render"], m["escala_render"])
json.dump(cam, open(saida, "w"), indent=1)
print("camera", saida, "quadros", sorted(cam["centros"]), "escala_render", round(cam["escala_render"], 3))
