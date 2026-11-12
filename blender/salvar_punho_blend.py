"""Gera o .blend do teste de punho fechado a partir do arquivo do usuario (que continua intacto):
textura empacotada, 12 pecas sem peso corrigidas, esqueleto no repouso com os dois punhos fechados.
A capa fica exatamente como o usuario deixou (escondida, com o tecido).
Uso: blender -b <original.blend> --python salvar_punho_blend.py -- <saida.blend>"""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corrigir_pesos
import punho_fechado as PF
import usuario_neo as U

saida = os.path.abspath(sys.argv[sys.argv.index("--") + 1])

img = bpy.data.images["NEO_METAL.png"]
img.filepath = U.TEXTURA
img.reload()
img.pack()
print("TEXTURA", tuple(img.size), "empacotada", bool(img.packed_file))

corrigir_pesos.corrigir()
U.repouso()
PF.aplicar()
bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=saida)
print("SALVO", saida, os.path.getsize(saida))
