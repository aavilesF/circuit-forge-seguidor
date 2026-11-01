#!/usr/bin/env bash
# Pruebas de la lógica del Speed Follower en la PC (g++, sin ESP32). Uso: speed-follower/pruebas/ejecutar.sh
set -euo pipefail
cd "$(dirname "$0")"
python3 generar_dorados.py > /dev/null
mkdir -p ../../.build
g++ -std=c++17 -O1 -g -Wall -Wextra -Werror -fsanitize=address,undefined -fno-sanitize-recover=all \
    test_sf.cpp ../firmware/sf/sf_logica.cpp ../firmware/sf/estados.cpp -o ../../.build/test_sf
../../.build/test_sf
