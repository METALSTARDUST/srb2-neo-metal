"""Importa um modelo MD3 do SRB2 para o Blender: malha unica com UVs, textura e UMA SHAPE KEY por quadro da animacao.
Os quadros passam sozinhos conforme a linha do tempo (quadro N do Blender = quadro N do MD3) e as animacoes ganham marcadores (STND, WALK, RUN_...) para pular de uma para outra.

No Blender: aba Scripting > Open > este arquivo, ajuste CAMINHO_MD3 / CAMINHO_PNG logo abaixo e clique em Run Script.
Por linha de comando: blender -b --python importar_md3.py -- <modelo.md3> <textura.png> <saida.blend>"""
import os
import re
import struct
import sys

import bpy

CAMINHO_MD3 = r"C:\caminho\para\XSONIC.md3"
CAMINHO_PNG = r"C:\caminho\para\XSONIC.png"
# Eixos: o MD3 tem x = frente, y = esquerda; aqui o personagem fica olhando para -Y (de frente na vista Front, Numpad 1), o padrao do Blender.
ESCALA = 0.1          # unidades do MD3 -> metros do Blender (0,1 deixa o Sonic com mais ou menos 4 m de altura na tela)


def ler_md3(caminho):
    d = open(caminho, "rb").read()
    ident, versao = struct.unpack_from("<4si", d, 0)
    assert ident == b"IDP3", "nao e um MD3"
    nome, flags, nq, nt, ns, nsk, ofs_q, ofs_t, ofs_s, ofs_eof = struct.unpack_from("<64siiiiiiiii", d, 8)
    quadros = []
    for i in range(nq):
        o = ofs_q + i * 56
        quadros.append(struct.unpack_from("<16s", d, o + 40)[0].split(b"\0")[0].decode("latin1"))
    superficies = []
    o = ofs_s
    for _ in range(ns):
        (_id, snome, _fl, sq, nsh, nv, ntr, ofs_tr, ofs_sh, ofs_st, ofs_xyz, ofs_end) = struct.unpack_from("<4s64siiiiiiiiii", d, o)
        tris = [struct.unpack_from("<3i", d, o + ofs_tr + 12 * k) for k in range(ntr)]
        st = [struct.unpack_from("<2f", d, o + ofs_st + 8 * k) for k in range(nv)]
        frames = []
        for q in range(sq):
            base = o + ofs_xyz + q * nv * 8
            frames.append([tuple(c / 64.0 for c in struct.unpack_from("<3h", d, base + 8 * k)) for k in range(nv)])
        superficies.append(dict(nome=snome.split(b"\0")[0].decode("latin1"), tris=tris, st=st, frames=frames))
        o += ofs_end
    return quadros, superficies


def importar(caminho_md3, caminho_png=None, escala=ESCALA):
    quadros, sup = ler_md3(caminho_md3)
    nome = os.path.splitext(os.path.basename(caminho_md3))[0]
    faces, uvs, desloc = [], [], 0
    for s in sup:
        for a, b, c in s["tris"]:
            faces.append((desloc + a, desloc + c, desloc + b))          # MD3: frente = sentido horario; Blender: anti-horario
        uvs += s["st"]
        desloc += len(s["st"])
    n_total = desloc
    pos0 = [p for s in sup for p in s["frames"][0]]
    malha = bpy.data.meshes.new(nome)
    malha.from_pydata([(y * escala, -x * escala, z * escala) for x, y, z in pos0], [], faces)
    malha.update()
    uv = malha.uv_layers.new(name="UV")
    for lp in malha.loops:
        s, t = uvs[lp.vertex_index]
        uv.data[lp.index].uv = (s, 1.0 - t)
    obj = bpy.data.objects.new(nome, malha)
    bpy.context.scene.collection.objects.link(obj)
    mat = bpy.data.materials.new(nome)
    mat.use_nodes = True
    if caminho_png and os.path.exists(caminho_png):
        img = bpy.data.images.load(os.path.abspath(caminho_png))
        img.pack()
        no = mat.node_tree.nodes.new("ShaderNodeTexImage")
        no.image = img
        no.interpolation = "Closest"
        mat.node_tree.links.new(no.outputs["Color"], mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
    malha.materials.append(mat)
    for p in malha.polygons:
        p.use_smooth = True
    obj.shape_key_add(name="Basis", from_mix=False)
    chave = malha.shape_keys
    for q, qn in enumerate(quadros):
        kb = obj.shape_key_add(name="%03d_%s" % (q, qn), from_mix=False)
        flat = []
        for s in sup:
            for x, y, z in s["frames"][q]:
                flat += (y * escala, -x * escala, z * escala)
        kb.data.foreach_set("co", flat)
    chave.use_relative = False
    chave.eval_time = 0.0
    # o motor mostra um quadro por vez: o quadro N da linha do tempo vira a shape key N + 1 (a 0 e a Basis)
    for i, kb in enumerate(chave.key_blocks):
        kb.interpolation = "KEY_LINEAR"
    drv = chave.driver_add("eval_time").driver
    drv.type = "SCRIPTED"
    drv.expression = "frame * %s" % repr(_passo(chave))
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, max(2, len(quadros))
    anim = None
    for q, qn in enumerate(quadros):
        grupo = re.sub(r"\d+$", "", qn)
        if grupo != anim:
            sc.timeline_markers.new(grupo or qn, frame=q + 1)
            anim = grupo
    print("%s: %d quadros, %d vertices, %d superficies" % (nome, len(quadros), n_total, len(sup)))
    return obj


def _passo(chave):
    return chave.key_blocks[1].frame - chave.key_blocks[0].frame if len(chave.key_blocks) > 1 else 1.0


if __name__ == "__main__":
    if "--" in sys.argv:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        a = sys.argv[sys.argv.index("--") + 1:]
        importar(a[0], a[1] if len(a) > 1 else None)
        if len(a) > 2:
            bpy.ops.wm.save_as_mainfile(filepath=a[2])
    else:
        importar(CAMINHO_MD3, CAMINHO_PNG)
