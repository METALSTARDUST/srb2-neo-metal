"""Renderiza os quadros de um .blend criado por importar_md3.py como SPRITES em varios angulos (camera ortografica girando em volta do personagem, fundo transparente).
Cada animacao tem o seu proprio enquadramento (o mesmo para todos os quadros e angulos dela): o centro da imagem fica sobre o eixo do personagem (a origem do MD3), assim a pose gira
de verdade de um angulo para o outro e o pe nao "anda" entre as vistas.
Uso: blender -b <modelo.blend> --python renderizar_angulos.py -- <saida> <tamanho_px> <elevacao_graus> <todos|resumo> [grupos_separados_por_virgula]
Saida: <saida>/<GRUPO>/<GRUPO>_<NN>_<angulo>.png e <saida>/<GRUPO>/enquadramento.json"""
import bpy, sys, os, math, json, re, mathutils
import numpy as np

arg = sys.argv[sys.argv.index("--") + 1:]
saida = os.path.abspath(arg[0]); os.makedirs(saida, exist_ok=True)
tam = int(arg[1]); elev = float(arg[2]); modo = arg[3]
so_grupos = set(arg[4].split(",")) if len(arg) > 4 else None
ANGULOS = [(0, "frente"), (45, "frente_direita"), (90, "lado_direito"), (135, "costas_direita"), (180, "costas"), (225, "costas_esquerda"), (270, "lado_esquerdo"), (315, "frente_esquerda")]
RESUMO = json.loads(os.environ.get("RESUMO_QUADROS", "{}"))          # {"RUN_": 2, ...} (so no modo resumo)

sc = bpy.context.scene
obj = [o for o in bpy.data.objects if o.type == "MESH" and o.data.shape_keys][0]
kbs = obj.data.shape_keys.key_blocks
nv = len(obj.data.vertices)


def analisar(nome):
    n = re.sub(r"^\d+_", "", nome)
    m = re.match(r"^(SPR2_|SUPER)([A-Za-z0-9_]{4})(?:\+i)?(\d{2,3})$", n)
    if m:
        return ("SUPER" if m.group(1) == "SUPER" else "") + m.group(2), int(m.group(3))
    m = re.match(r"^(.*?)(?:\+i)?(\d{2,3})$", n)
    if m:
        return m.group(1).strip().replace(" ", "_"), int(m.group(2))
    return n.replace(" ", "_"), 0


quadros = {}          # grupo -> [(indice, frame_blender, zmin, zmax, raio)]
tri = np.empty(len(obj.data.polygons) * 3, dtype=np.int32); obj.data.polygons.foreach_get("vertices", tri); tri = tri.reshape(-1, 3)
for i in range(1, len(kbs)):
    a = np.empty(nv * 3, dtype=np.float32); kbs[i].data.foreach_get("co", a); a = a.reshape(-1, 3)
    # so conta o que aparece: superficies recolhidas em um ponto (triangulos de area zero) ficam de fora do enquadramento
    area = np.linalg.norm(np.cross(a[tri[:, 1]] - a[tri[:, 0]], a[tri[:, 2]] - a[tri[:, 0]]), axis=1)
    usados = np.unique(tri[area > 1e-5].ravel())
    a = a[usados] if len(usados) else a
    g, k = analisar(kbs[i].name)
    quadros.setdefault(g, []).append((k, i, float(a[:, 2].min()), float(a[:, 2].max()), float(np.sqrt((a[:, 0] ** 2 + a[:, 1] ** 2).max()))))

cd = bpy.data.cameras.new("cam"); cd.type = "ORTHO"; cd.clip_start = 0.1; cd.clip_end = 500
cam = bpy.data.objects.new("cam", cd); sc.collection.objects.link(cam); sc.camera = cam
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "TEXTURE"; sc.display.shading.show_cavity = False
sc.display.render_aa = "8"
sc.view_settings.view_transform = "Standard"
sc.view_settings.exposure = float(os.environ.get("EXPOSICAO", "0"))
sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = tam
sc.render.image_settings.color_mode = "RGBA"
e = math.radians(elev)
total = 0
for g, lista in quadros.items():
    if g == "base" or (so_grupos and g not in so_grupos):
        continue
    if modo == "resumo":
        if g not in RESUMO:
            continue
        lista_r = [q for q in lista if q[0] == RESUMO[g]]
    else:
        lista_r = lista
    zmin, zmax, R = min(q[2] for q in lista), max(q[3] for q in lista), max(q[4] for q in lista)
    H = zmax - zmin
    S = max(2 * R, H * math.cos(e) + 2 * R * math.sin(e)) * 1.1
    zc = (zmin + zmax) / 2
    pasta = os.path.join(saida, g); os.makedirs(pasta, exist_ok=True)
    json.dump(dict(grupo=g, ortho=S, px_por_unidade_blender=tam / S, zmin=zmin, zmax=zmax, raio=R, elevacao=elev), open(os.path.join(pasta, "enquadramento.json"), "w"))
    cd.ortho_scale = S
    alvo = mathutils.Vector((0, 0, zc))
    for k, fb, *_ in sorted(lista_r):
        sc.frame_set(fb)
        for th, nome in ANGULOS:
            t = math.radians(th)
            d = mathutils.Vector((-math.sin(t) * math.cos(e), -math.cos(t) * math.cos(e), math.sin(e)))
            cam.location = alvo + d * 60
            cam.rotation_euler = (alvo - cam.location).to_track_quat("-Z", "Y").to_euler()
            sc.render.filepath = os.path.join(pasta, "%s_%02d_%s.png" % (g, k, nome))
            bpy.ops.render.render(write_still=True)
            total += 1
print("renderizados", total)
