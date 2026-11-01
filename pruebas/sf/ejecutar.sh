#!/usr/bin/env bash
# Pruebas de la lógica del firmware en la PC (g++ con ASan/UBSan, sin microcontrolador).
# 1) C2 contra la referencia Python histórica (vectores dorados de legado/speed_follower_v1/sim).
# 2) C2/C3m/C3g y estimar_coord contra el simulador de la Fase 2 (sim/nucleo.py), con la configuración maestra.
# Uso: pruebas/sf/ejecutar.sh
set -euo pipefail
cd "$(dirname "$0")"
python3 generar_dorados.py > /dev/null
python3 generar_dorados_c3.py > /dev/null
mkdir -p ../../.build
OPC="-std=c++17 -O1 -g -Wall -Wextra -Werror -fsanitize=address,undefined -fno-sanitize-recover=all"
g++ $OPC test_sf.cpp ../../firmware/sf/sf_logica.cpp ../../firmware/sf/estados.cpp -o ../../.build/test_sf
../../.build/test_sf
g++ $OPC test_c3.cpp ../../firmware/sf/sf_logica.cpp -o ../../.build/test_c3
../../.build/test_c3
