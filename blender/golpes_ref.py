"""Leitor do XSONIC.md3 em numpy puro (sem bpy) para medir os golpes do Dark Sonic.
Coordenadas de saida no mesmo sistema do Blender: o personagem olha para -Y, +X e o lado direito da imagem de frente (x_blender = y_md3 * 0.1, y_blender = -x_md3 * 0.1, z_blender = z_md3 * 0.1).
O MD3 estaciona as pecas que nao aparecem em um quadro em pontos soltos, com centenas de vertices empilhados: vertice visivel = posicao repetida menos de 20 vezes no quadro."""
import struct

import numpy as np

MD3_XSONIC = r"C:\tmp\srb2-metal-homing\habilidades-metal\modelos-celular\xsonic\XSONIC.md3"
ESCALA = 0.1
LIMITE_PARQUEADO = 20


def ler(caminho=MD3_XSONIC):
    """Retorna (nomes_dos_quadros, superficies); cada superficie tem tris [nt,3], st [nv,2] (UV do MD3) e pos [nq,nv,3] ja em eixos do Blender."""
    d = open(caminho, "rb").read()
    nome, flags, nq, nt, ns, nsk, ofs_q, ofs_t, ofs_s, ofs_eof = struct.unpack_from("<64siiiiiiiii", d, 8)
    quadros = []
    for i in range(nq):
        quadros.append(struct.unpack_from("<16s", d, ofs_q + i * 56 + 40)[0].split(b"\0")[0].decode("latin1"))
    sup = []
    o = ofs_s
    for _ in range(ns):
        (_id, snome, _fl, sq, nsh, nv, ntr, ofs_tr, ofs_sh, ofs_st, ofs_xyz, ofs_end) = struct.unpack_from("<4s64siiiiiiiiii", d, o)
        tris = np.frombuffer(d, dtype="<i4", count=3 * ntr, offset=o + ofs_tr).reshape(ntr, 3).copy()
        st = np.frombuffer(d, dtype="<f4", count=2 * nv, offset=o + ofs_st).reshape(nv, 2).copy()
        # cada vertice e 4 shorts (x, y, z, normal); le todos os quadros de uma vez
        bruto = np.frombuffer(d, dtype="<i2", count=sq * nv * 4, offset=o + ofs_xyz).reshape(sq, nv, 4)[:, :, :3].astype(np.float64) / 64.0
        pos = np.stack([bruto[:, :, 1] * ESCALA, -bruto[:, :, 0] * ESCALA, bruto[:, :, 2] * ESCALA], axis=-1)
        sup.append(dict(nome=snome.split(b"\0")[0].decode("latin1"), tris=tris, st=st, pos=pos))
        o += ofs_end
    return quadros, sup


def mascara_visivel(sup, q):
    """Lista de mascaras booleanas (uma por superficie) dos vertices visiveis no quadro q."""
    todos = np.concatenate([s["pos"][q] for s in sup])
    chave = np.round(todos * 1000).astype(np.int64)
    _, inv, cont = np.unique(chave, axis=0, return_inverse=True, return_counts=True)
    vis = cont[inv.reshape(-1)] < LIMITE_PARQUEADO
    saida, i = [], 0
    for s in sup:
        n = s["pos"].shape[1]
        saida.append(vis[i:i + n])
        i += n
    return saida


def altura_visivel(sup, q):
    m = mascara_visivel(sup, q)
    pts = np.concatenate([s["pos"][q][mm] for s, mm in zip(sup, m)])
    return pts.min(axis=0), pts.max(axis=0)


def componentes(nv, tris):
    """Rotulo de ilha topologica (0..n-1) de cada vertice de uma superficie, por uniao dos vertices de cada triangulo."""
    pai = np.arange(nv)

    def achar(a):
        while pai[a] != a:
            pai[a] = pai[pai[a]]
            a = pai[a]
        return a
    for a, b, c in tris:
        ra = achar(a)
        pai[achar(b)] = ra
        pai[achar(c)] = ra
    raiz = np.array([achar(i) for i in range(nv)])
    _, rot = np.unique(raiz, return_inverse=True)
    return rot
