#!/bin/bash
# Gera os .blend temporarios e renderiza todos os quadros dos modelos em 8 angulos (192 px). Uso: bash rodar_angulos.sh
B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
R=/c/tmp/srb2-metal-homing
S=$R/neo/fontes/blender
O=$R/neo/pacote-blender/angulos
H=$R/habilidades-metal
mkdir -p $O/_blend
rodar() {
  id=$1; md3=$2; png=$3
  echo "== $id"
  "$B" -b --python $S/importar_md3.py -- "$md3" "$png" $O/_blend/$id.blend 2>&1 | grep -E "quadros|Error|Trace"
  "$B" -b $O/_blend/$id.blend --python $S/renderizar_angulos.py -- $O/$id 192 0 todos 2>&1 | grep -E "renderiz|Error|Trace"
}
rodar metal_atual_ixryzisen "$H/od-rs-27out/backup-27out-fx/verif2_163449_md3_1/Metal_Sonic.md3" "$H/od-rs-27out/backup-27out-fx/verif2_163449_png_1/Metal_Sonic.png"
rodar metal_base_play "$H/modelos-celular/PLAY/METAL_SONIC.md3" "$H/modelos-celular/PLAY/METAL_SONIC.png"
rodar metal_antigo "$H/instalar9/ANTIGO/METAL_SONIC.md3" "$H/instalar9/ANTIGO/METAL_SONIC.png"
rodar neo_metal_v36 "$H/od-rs-27out/neo-tex/NEO_METAL_v36.md3" "$H/od-rs-27out/neo-tex/NEO_METAL_v36.png"
rodar sonic_x "$H/modelos-celular/xsonic/XSONIC.md3" "$H/modelos-celular/xsonic/XSONIC.png"
echo FIM
