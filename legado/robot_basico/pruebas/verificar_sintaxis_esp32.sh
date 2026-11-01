#!/usr/bin/env bash
# Comprueba sintaxis y tipos de TODO el firmware contra un stub de Arduino (NO es el SDK real del ESP32).
# Prueba los dos perfiles de sensor y las dos versiones de la API de PWM (arduino-esp32 2.x y 3.x).
set -euo pipefail
cd "$(dirname "$0")/.."
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
for perfil in 1 2; do
  for api in 2 3; do
    cp firmware/seguidor/*.h firmware/seguidor/*.cpp "$tmp/"
    cp firmware/seguidor/seguidor.ino "$tmp/seguidor.cpp"
    sed -i "s/#define PERFIL_SENSOR   PERFIL_QTR8A/#define PERFIL_SENSOR   $perfil/" "$tmp/pines.h"
    for f in hardware.cpp seguidor.cpp estados.cpp posicion.cpp pid.cpp control.cpp; do
      g++ -std=c++17 -fsyntax-only -Wall -Wextra -Werror -I"$tmp" -Ipruebas/stub_arduino -DESP_ARDUINO_VERSION_MAJOR=$api "$tmp/$f"
    done
    echo "OK perfil=$perfil API-PWM=$api"
  done
done
