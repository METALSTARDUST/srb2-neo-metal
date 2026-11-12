#!/bin/bash
# Parte 2 do chute: perna que chuta reta (joelho na reta quadril -> tornozelo), pe a 50% do crescimento do tenis (padrao), Super 273-276 na camera da v1
cd /c/tmp/srb2-metal-homing/neo/golpes-neo || exit 1
export MSYS_NO_PATHCONV=1
BL="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
S=../fontes/blender/golpes_chute.py
CAM="C:/tmp/srb2-metal-homing/neo/golpes-neo/chute/render_chute_v1/metricas_273_274_275_276.json"
SAIDA=${1:-chute/parte2_v1}
mkdir -p "$SAIDA"
NEO_CAMERA_JSON="$CAM" "$BL" -b neo_base_pose.blend --python $S -- "$SAIDA" 273,274,275,276 560 - 1.4 - 1 1.45 1.4 1.0 > "$SAIDA/log.txt" 2>&1
echo "fim codigo $?" >> "$SAIDA/log.txt"
tail -n 3 "$SAIDA/log.txt" | cut -c1-200
