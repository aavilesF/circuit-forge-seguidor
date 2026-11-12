#!/usr/bin/env bash
# V2 · Pruebas del firmware en la PC: genera los datos (pistas y vectores dorados del simulador), compila la lógica con
# g++ (-Wall -Wextra -Werror, AddressSanitizer y UndefinedBehaviorSanitizer) y corre test_v2.
set -euo pipefail
cd "$(dirname "$0")"
OUT=${OUT:-build}
mkdir -p "$OUT"
python3 generar_datos.py "$OUT/datos" >/dev/null
L=../logica
g++ -std=c++17 -O1 -g -Wall -Wextra -Werror -fsanitize=address,undefined -fno-sanitize-recover=all \
    test_v2.cpp $L/mapa.cpp $L/motor_v2.cpp $L/succion.cpp $L/estados_v2.cpp $L/indicadores.cpp $L/consola.cpp \
    $L/parametros_v2.cpp $L/nucleo_v2.cpp ../../logica/sf_logica.cpp ../../logica/posicion.cpp \
    -o "$OUT/test_v2"
"$OUT/test_v2" "$OUT/datos"
