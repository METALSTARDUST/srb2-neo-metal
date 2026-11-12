#!/bin/bash
# Parte 4 do chute: bracos e maos (pernas como na Parte 3). Super 273-276; a camera do corpo e das pernas vem da v1 e a dos bracos da primeira rodada da Parte 4 (parte4_base).
# Uso: rodar_parte4.sh [saida] [json de camera]; ambiente opcional: os da Parte 3 (NEO_JOELHO_MIN, NEO_COXA_APOIO_MAX, NEO_APOIO) e os da Parte 4 que o golpes_chute.py ler
cd /c/tmp/srb2-metal-homing/neo/golpes-neo || exit 1
export MSYS_NO_PATHCONV=1
BL="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
S=../fontes/blender/golpes_chute.py
CAM=${2:-"C:/tmp/srb2-metal-homing/neo/golpes-neo/chute/render_chute_v1/metricas_273_274_275_276.json"}
SAIDA=${1:-chute/parte4_base}
mkdir -p "$SAIDA"
NEO_CAMERA_JSON="$CAM" "$BL" -b neo_base_pose.blend --python $S -- "$SAIDA" 273,274,275,276 560 - 1.4 - 1 1.45 1.4 1.0 > "$SAIDA/log.txt" 2>&1
echo "fim codigo $?" >> "$SAIDA/log.txt"
tail -n 3 "$SAIDA/log.txt" | cut -c1-200
