#!/usr/bin/env bash
# Compila el simulador. Uso: sim/ejecutar.sh [clave=valor ...]
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p ../.build resultados
g++ -std=c++17 -O2 -Wall -Wextra simular.cpp ../firmware/seguidor/posicion.cpp ../firmware/seguidor/pid.cpp ../firmware/seguidor/control.cpp -o ../.build/simular
../.build/simular "$@"
