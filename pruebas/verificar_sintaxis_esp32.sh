#!/usr/bin/env bash
# Comprueba sintaxis y tipos del firmware de hardware contra un stub de Arduino (NO es el SDK real).
# Prueba los dos perfiles de sensor y las dos versiones de la API de PWM.
set -euo pipefail
cd "$(dirname "$0")/.."
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
for perfil in 1 2; do
  for api in 2 3; do
    sed "s/#define PERFIL_SENSOR   PERFIL_QTR8A/#define PERFIL_SENSOR   $perfil/" firmware/seguidor/pines.h > "$tmp/pines.h"
    cp firmware/seguidor/{parametros,posicion,pid,control,hardware}.h firmware/seguidor/{hardware,seguidor.ino}* "$tmp/" 2>/dev/null || true
    cp firmware/seguidor/seguidor.ino "$tmp/seguidor.cpp"
    for f in hardware.cpp seguidor.cpp; do
      g++ -std=c++17 -fsyntax-only -Wall -Wextra -I"$tmp" -Ipruebas/stub_arduino -DESP_ARDUINO_VERSION_MAJOR=$api "$tmp/$f"
    done
    echo "OK perfil=$perfil API-PWM=$api"
  done
done
