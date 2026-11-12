"""Separa o corpo do Neo em UMA PARTE POR OSSO numa COPIA do .blend de trabalho e fotografa cada parte,
para o usuario dizer o que e cada uma. Nao altera pesos, ossos nem o arquivo de origem.

Regra: cada triangulo da malha vai para o osso (grupo de vertices) com a maior soma de pesos dos seus 3 vertices;
triangulo sem peso nenhum fica como "sem osso". A capa (objeto 'capa') vira 2 partes extras: tecido e cinto.

Uso (na copia de trabalho; saida em uma pasta nova):
  blender -b <base>.blend --python separar_partes.py -- <pasta_saida> [dominante_original.npy]
Para gerar o .npy do arquivo ORIGINAL do usuario (so para marcar o que eu ajustei nos pesos):
  blender -b <original>.blend --python separar_partes.py -- --dump <dominante_original.npy>"""
import colorsys
import json
import os
import sys

import bmesh
import bpy
import numpy as np
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

arg = sys.argv[sys.argv.index("--") + 1:]
DEDOS = ("polegar", "indicador", "medio", "anelar", "mindinho")
CINZA = (0.50, 0.53, 0.58, 1.0)
DESTAQUE = (1.0, 0.42, 0.0, 1.0)
LIMITE_PESO = 0.3          # soma minima dos pesos (3 vertices) para o triangulo ter osso

arm = bpy.data.objects["Armação"]
corpo = bpy.data.objects["NeoMetal"]
capa = bpy.data.objects["capa"]
ossos = {b.name: b for b in arm.data.bones}


def triangulos(me):
    t = np.array([p.vertices[:] for p in me.polygons])
    assert t.shape[1] == 3, "esperava so triangulos"
    return t


def dominantes(obj, so_ossos=True):
    """(dominante[nf], pureza[nf]): indice do grupo de maior peso por triangulo (-1 = sem osso) e a fatia dele no total."""
    me = obj.data
    ng = len(obj.vertex_groups)
    W = np.zeros((len(me.vertices), ng), dtype=np.float64)
    for v in me.vertices:
        for g in v.groups:
            W[v.index, g.group] = g.weight
    if so_ossos:
        for vg in obj.vertex_groups:
            if vg.name not in ossos:
                W[:, vg.index] = 0.0
    S = W[triangulos(me)].sum(axis=1)
    total = S.sum(axis=1)
    mx = S.max(axis=1)
    dom = S.argmax(axis=1)
    dom[mx < LIMITE_PESO] = -1
    pureza = np.where(total > 0, mx / np.maximum(total, 1e-9), 0.0)
    return dom, pureza


if arg[0] == "--dump":
    dom, _ = dominantes(corpo)
    np.save(os.path.abspath(arg[1]), dom)
    print("dominante do original gravado:", len(dom), "triangulos")
    sys.exit(0)

SAIDA = os.path.abspath(arg[0])
ORIGINAL = os.path.abspath(arg[1]) if len(arg) > 1 and os.path.exists(arg[1]) else None
os.makedirs(os.path.join(SAIDA, "miniaturas"), exist_ok=True)

# ---------------------------------------------------------------- repouso, capa visivel, sem simulacao de tecido
for pb in arm.pose.bones:
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = (1, 0, 0, 0)
    pb.location = (0, 0, 0)
    pb.scale = (1, 1, 1)
capa.hide_set(False)
capa.hide_viewport = False
capa.hide_render = False
for md in capa.modifiers:
    if md.type == "CLOTH":
        md.show_viewport = False
        md.show_render = False
bpy.context.view_layer.update()

# ---------------------------------------------------------------- quem pertence a quem
dom_c, pur_c = dominantes(corpo)
nomes_g = {vg.index: vg.name for vg in corpo.vertex_groups}
assert set(nomes_g.values()) == set(ossos), "grupos de vertices e ossos nao batem"
tri_c = triangulos(corpo.data)
dom_o = np.load(ORIGINAL) if ORIGINAL else None
if dom_o is not None:
    assert len(dom_o) == len(dom_c)
mudou = (dom_o != dom_c) if dom_o is not None else np.zeros(len(dom_c), bool)

# capa: maior ilha = tecido; as demais ilhas = cinto (aro, tachas, tiras)
me_k = capa.data
pai = list(range(len(me_k.vertices)))


def achar(a):
    while pai[a] != a:
        pai[a] = pai[pai[a]]
        a = pai[a]
    return a


tri_k = triangulos(me_k)
for a, b, c in tri_k:
    r = achar(a)
    pai[achar(b)] = r
    pai[achar(c)] = r
raiz_tri = np.array([achar(t[0]) for t in tri_k])
tam = {r: int((raiz_tri == r).sum()) for r in set(raiz_tri)}
tecido_raiz = max(tam, key=tam.get)
tri_tecido = np.where(raiz_tri == tecido_raiz)[0]
tri_cinto = np.where(raiz_tri != tecido_raiz)[0]
dom_k, pur_k = dominantes(capa)
nomes_k = {vg.index: vg.name for vg in capa.vertex_groups}


def ilhas_de(tris, tri_idx):
    p = {}

    def f(a):
        p.setdefault(a, a)
        while p[a] != a:
            p[a] = p[p[a]]
            a = p[a]
        return a

    for i in tri_idx:
        a, b, c = (int(x) for x in tris[i])
        r = f(a)
        p[f(b)] = r
        p[f(c)] = r
    return len({f(x) for x in p})


# ---------------------------------------------------------------- cria as partes
col = bpy.data.collections.new("Partes (uma por osso)")
bpy.context.scene.collection.children.link(col)
col_orig = bpy.data.collections.new("Originais (ocultos)")
bpy.context.scene.collection.children.link(col_orig)
for o in (corpo, capa):
    for c in list(o.users_collection):
        c.objects.unlink(o)
    col_orig.objects.link(o)
col_orig.hide_viewport = True
col_orig.hide_render = True


def fazer_parte(obj, tris_idx, nome):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    manter = {int(i) for i in tris_idx}
    apagar = [f for f in bm.faces if f.index not in manter]
    bmesh.ops.delete(bm, geom=apagar, context="FACES")
    soltos = [v for v in bm.verts if not v.link_faces]
    if soltos:
        bmesh.ops.delete(bm, geom=soltos, context="VERTS")
    me2 = bpy.data.meshes.new(nome)
    bm.to_mesh(me2)
    bm.free()
    for m in obj.data.materials:
        me2.materials.append(m)
    o2 = obj.copy()
    o2.data = me2
    o2.name = nome
    for md in list(o2.modifiers):
        if md.type == "CLOTH":
            o2.modifiers.remove(md)
    o2.hide_viewport = False
    o2.hide_render = False
    col.objects.link(o2)
    return o2


def limpo(nome):
    return " ".join(nome.split())


def tipo_de(nome):
    n = nome.lower()
    if any(d in n for d in DEDOS):
        return "dedo"
    if n.strip().startswith("punho"):
        return "mao"
    return "corpo"


def lado_de(nome):
    n = nome.lower()
    return "esquerdo" if "esquerd" in n else "direito" if "direit" in n else "centro"


partes = []


def cor(i, total=64):
    h = (i * 0.61803398875) % 1.0
    s = 0.85 if i % 2 == 0 else 0.55
    v = 0.95 if i % 3 != 1 else 0.78
    return colorsys.hsv_to_rgb(h, s, v) + (1.0,)


for g in sorted(nomes_g):
    nome = nomes_g[g]
    n = g + 1
    osso = ossos[nome]
    idx = np.where(dom_c == g)[0]
    info = dict(n=n, id="p%02d" % n, osso=limpo(nome), osso_cru=nome, pai=limpo(osso.parent.name) if osso.parent else None,
                filhos=[limpo(c.name) for c in osso.children], cabeca=[round(x, 4) for x in (arm.matrix_world @ osso.head_local)],
                cauda=[round(x, 4) for x in (arm.matrix_world @ osso.tail_local)], comprimento=round(osso.length, 4),
                tipo=tipo_de(nome), lado=lado_de(nome), origem="NeoMetal", triangulos=int(len(idx)),
                ajustado=int(mudou[idx].sum()) if len(idx) else 0, pureza=round(float(pur_c[idx].mean()), 2) if len(idx) else 0.0)
    if len(idx):
        info["ilhas"] = ilhas_de(tri_c, idx)
        info["objeto"] = fazer_parte(corpo, idx, "%02d %s" % (n, limpo(nome))).name
        info["cor"] = [round(x, 3) for x in cor(g)]
    partes.append(info)

sem_osso = np.where(dom_c == -1)[0]
if len(sem_osso):
    partes.append(dict(n=0, id="p00", osso="(sem osso)", osso_cru="", pai=None, filhos=[], tipo="corpo", lado="centro", origem="NeoMetal",
                       triangulos=int(len(sem_osso)), ajustado=0, pureza=0.0, ilhas=ilhas_de(tri_c, sem_osso),
                       objeto=fazer_parte(corpo, sem_osso, "00 sem osso").name, cor=[0.9, 0.1, 0.1, 1.0]))


def osso_dominante_k(tris_idx):
    cont = {}
    for i in tris_idx:
        if dom_k[i] >= 0:
            cont[nomes_k[dom_k[i]]] = cont.get(nomes_k[dom_k[i]], 0) + 1
    return limpo(max(cont, key=cont.get)) if cont else None


for id_, nome, idx, texto in (("c1", "capa (tecido)", tri_tecido, "Tecido da capa"), ("c2", "cinto (aro, tachas e tiras)", tri_cinto, "Cinto")):
    info = dict(n=None, id=id_, osso=texto, osso_cru=nome, pai=None, filhos=[], tipo="corpo", lado="centro", origem="capa",
                triangulos=int(len(idx)), ajustado=int(len(idx)) if id_ == "c2" else 0,
                pureza=round(float(pur_k[idx].mean()), 2) if len(idx) else 0.0, osso_dominante=osso_dominante_k(idx))
    info["ilhas"] = ilhas_de(tri_k, idx)
    info["objeto"] = fazer_parte(capa, idx, "%s %s" % (id_.upper(), nome)).name
    info["cor"] = [round(x, 3) for x in cor(60 + len(id_) + int(id_[1]))]
    partes.append(info)

bpy.context.view_layer.update()

# ---------------------------------------------------------------- geometria avaliada de cada parte (repouso)
dg = bpy.context.evaluated_depsgraph_get()
obj_de = {p["id"]: bpy.data.objects[p["objeto"]] for p in partes if p.get("objeto")}
mundo = {}
for pid, o in obj_de.items():
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    buf = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", buf)
    m = np.array(o.matrix_world)
    mundo[pid] = buf.reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]
    ev.to_mesh_clear()
for p in partes:
    if p["id"] in mundo:
        a = mundo[p["id"]]
        p["vertices"] = int(len(a))
        p["bbox_min"] = [round(float(x), 4) for x in a.min(axis=0)]
        p["bbox_max"] = [round(float(x), 4) for x in a.max(axis=0)]
        p["centro"] = [round(float(x), 4) for x in a.mean(axis=0)]

# ---------------------------------------------------------------- cena de fotos
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sh = sc.display.shading
sh.light = "STUDIO"
sh.color_type = "OBJECT"
sh.show_cavity = False
sh.show_object_outline = True
sh.object_outline_color = (0.04, 0.04, 0.05)
sc.display.render_aa = "8"
sc.view_settings.view_transform = "Standard"
sc.render.film_transparent = True
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGBA"
cd = bpy.data.cameras.new("cam_partes")
cd.type = "ORTHO"
cd.clip_start = 0.1
cd.clip_end = 500
cam = bpy.data.objects.new("cam_partes", cd)
sc.collection.objects.link(cam)
sc.camera = cam


def enquadrar(vista, alvo, escala, w, h):
    sc.render.resolution_x, sc.render.resolution_y = w, h
    alvo = Vector(alvo)
    if vista == "frente":                      # camera em -Y olhando para +Y (o Neo olha para -Y)
        cam.location = alvo + Vector((0, -60, 0))
        cam.rotation_euler = (np.pi / 2, 0, 0)
    elif vista == "costas":                    # camera em +Y olhando para -Y
        cam.location = alvo + Vector((0, 60, 0))
        cam.rotation_euler = (np.pi / 2, 0, np.pi)
    else:                                      # de cima, olhando para -Z (direita da imagem = +X, topo = +Y)
        cam.location = alvo + Vector((0, 0, 60))
        cam.rotation_euler = (0, 0, 0)
    cd.ortho_scale = escala
    bpy.context.view_layer.update()


def projetar(p3d, w, h):
    v = world_to_camera_view(sc, cam, Vector(p3d))
    return [round(float(v.x * w), 1), round(float((1 - v.y) * h), 1)]


def pintar(cores):
    for pid, o in obj_de.items():
        o.color = cores(pid)


def foto(caminho):
    sc.render.filepath = caminho
    bpy.ops.render.render(write_still=True)


def so_visivel(ids):
    for pid, o in obj_de.items():
        o.hide_render = pid not in ids


def tudo_visivel():
    for o in obj_de.values():
        o.hide_render = False


COR = {p["id"]: tuple(p["cor"]) for p in partes if p.get("objeto")}
TAM_MINI = 330


def maior_ilha(pid):
    """indices dos vertices da maior ilha (peca conectada) da parte: o numero do mapa fica em cima dela"""
    me = obj_de[pid].data
    pai_v = list(range(len(me.vertices)))

    def f(a):
        while pai_v[a] != a:
            pai_v[a] = pai_v[pai_v[a]]
            a = pai_v[a]
        return a

    for pg in me.polygons:
        vs = list(pg.vertices)
        r = f(vs[0])
        for x in vs[1:]:
            pai_v[f(x)] = r
    raiz = np.array([f(i) for i in range(len(me.vertices))])
    vals, cont = np.unique(raiz, return_counts=True)
    return np.where(raiz == vals[int(np.argmax(cont))])[0]

# miniatura de cada parte: corpo todo em cinza (A) + so a parte em laranja (B), mesma camera
for p in partes:
    if p["id"] not in mundo:
        continue
    mn, mx = np.array(p["bbox_min"]), np.array(p["bbox_max"])
    c = (mn + mx) / 2
    if p["tipo"] in ("dedo", "mao"):
        vista, esc = "topo", max(max(mx[0] - mn[0], mx[1] - mn[1]) * 1.7, 0.42)
    else:
        vista, esc = "frente", max(max(mx[0] - mn[0], mx[2] - mn[2]) * 1.5, 0.9)
    p["vista"] = vista
    enquadrar(vista, c, esc, TAM_MINI, TAM_MINI)
    tudo_visivel()
    pintar(lambda pid: CINZA)
    foto(os.path.join(SAIDA, "miniaturas", "%s_A.png" % p["id"]))
    pintar(lambda pid: DESTAQUE)
    so_visivel({p["id"]})
    foto(os.path.join(SAIDA, "miniaturas", "%s_B.png" % p["id"]))
tudo_visivel()

# mapas coloridos (uma cor por parte) com a ancora de cada numero: vertice da parte mais perto do centro dela
pintar(lambda pid: COR[pid])
todos = np.vstack(list(mundo.values()))
mapas = {}
CENTRO = (todos.min(axis=0) + todos.max(axis=0)) / 2
ESC_CORPO = max(todos[:, 2].max() - todos[:, 2].min(), todos[:, 0].max() - todos[:, 0].min()) * 1.1
AJUSTES = {                                    # nome: (vista, alvo, escala, largura, altura, ids escondidos)
    "corpo_frente": ("frente", CENTRO, ESC_CORPO, 1100, 1100, set()),
    "corpo_frente_sem_cabeca": ("frente", CENTRO, ESC_CORPO, 1100, 1100, {"p48", "c1"}),
    "corpo_costas": ("costas", CENTRO, ESC_CORPO, 1100, 1100, {"c1", "p48"}),
    "mao_esquerda": ("topo", np.array([-1.43, 0.0, 1.8]), 1.4, 1000, 700, {"p48", "c1"}),
    "mao_direita": ("topo", np.array([1.36, 0.0, 1.8]), 1.4, 1000, 700, {"p48", "c1"}),
}
for nome_mapa, (vista, alvo, esc, w, h, escondidos) in AJUSTES.items():
    enquadrar(vista, alvo, esc, w, h)
    for pid, o in obj_de.items():
        o.hide_render = pid in escondidos
    foto(os.path.join(SAIDA, "mapa_%s_cru.png" % nome_mapa))
    anc = {}
    for p in partes:
        if p["id"] not in mundo or p["id"] in escondidos:
            continue
        pts = mundo[p["id"]][maior_ilha(p["id"])]
        c = pts.mean(axis=0)
        k = int(np.argmin(np.linalg.norm(pts - c, axis=1)))
        anc[p["id"]] = projetar(pts[k], w, h)
    mapas[nome_mapa] = dict(vista=vista, w=w, h=h, ancoras=anc)

# ---------------------------------------------------------------- salva: copia de trabalho com as partes coloridas no 3D
tudo_visivel()
bpy.data.objects.remove(cam)
bpy.data.cameras.remove(cd)
for scr in bpy.data.screens:
    for area in scr.areas:
        if area.type == "VIEW_3D":
            for sp in area.spaces:
                if sp.type == "VIEW_3D":
                    sp.shading.color_type = "OBJECT"
                    sp.shading.type = "SOLID"
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(SAIDA, "neo_partes_por_osso.blend"))

dados = dict(base=bpy.data.filepath, limite_peso=LIMITE_PESO, partes=partes, mapas=mapas, sem_osso=int(len(sem_osso)),
             total_triangulos_neometal=int(len(dom_c)), total_triangulos_capa=int(len(tri_k)))
with open(os.path.join(SAIDA, "partes.json"), "w", encoding="utf-8") as f:
    json.dump(dados, f, ensure_ascii=False, indent=1)

print("PARTES:", len([p for p in partes if p.get("objeto")]), "com malha;", len([p for p in partes if not p.get("objeto")]), "sem malha")
for p in partes:
    print("%-4s %-45s tri=%4s ilhas=%-3s pureza=%.2f ajustado=%s" % (p["id"], p["osso"][:45], p["triangulos"], p.get("ilhas", "-"), p["pureza"], p["ajustado"]))
