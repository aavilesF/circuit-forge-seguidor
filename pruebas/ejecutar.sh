#!/usr/bin/env bash
# Compila y ejecuta las pruebas de la lógica pura. Requiere g++.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p ../.build
g++ -std=c++17 -Wall -Wextra -O1 test_logica.cpp ../firmware/seguidor/posicion.cpp ../firmware/seguidor/pid.cpp ../firmware/seguidor/control.cpp -o ../.build/test_logica
../.build/test_logica
