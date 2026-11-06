#!/usr/bin/env bash
# Robot casero · compila y ejecuta las pruebas de la lógica en la PC (g++). Uso: ./ejecutar.sh
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p ../.build
S=../casero
g++ -std=c++17 -Wall -Wextra -O1 -fsanitize=address,undefined -I"$S" test_casero.cpp \
  "$S/posicion.cpp" "$S/pid.cpp" "$S/control.cpp" "$S/filtro.cpp" "$S/motor.cpp" "$S/estados.cpp" \
  "$S/indicadores.cpp" "$S/ajustes.cpp" -o ../.build/test_casero
../.build/test_casero
