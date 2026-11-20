#!/usr/bin/env bash
# Robot de emergencia · compila y ejecuta las pruebas de la lógica en la PC (g++ ≥ 9) y compara los pines con el
# esquema. Uso: ./ejecutar.sh   (Windows: .\ejecutar.ps1)
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p ../.build
S=../emergencia
SAN="-fsanitize=address,undefined"
case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) SAN="" ;; esac   # MinGW no trae los sanitizers
g++ -std=c++17 -Wall -Wextra -Werror -O1 $SAN -I"$S" test_emergencia.cpp \
  "$S/posicion.cpp" "$S/pid.cpp" "$S/control.cpp" "$S/filtro.cpp" "$S/motor.cpp" "$S/estados.cpp" \
  "$S/indicadores.cpp" "$S/ajustes.cpp" -o ../.build/test_emergencia
../.build/test_emergencia
PY=$(command -v python3 || command -v python)
"$PY" verificar_pines.py
