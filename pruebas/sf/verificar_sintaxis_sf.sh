#!/usr/bin/env bash
# Comprueba sintaxis y tipos del firmware del Speed Follower contra el stub de Arduino
# (pruebas/stub_arduino). NO es el SDK real del ESP32: no sustituye compilar con arduino-esp32.
# Cubre 2 drivers × 2 versiones de la API de PWM (motor y sensores vienen de config_maestra.h).
set -euo pipefail
cd "$(dirname "$0")/../.."
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
for drv in DRIVER_DRV8833 DRIVER_TB6612; do
    for api in 2 3; do
      cp firmware/sf/*.h firmware/sf/*.cpp "$tmp/"
      cp firmware/sf/sf.ino "$tmp/sf_ino.cpp"
      sed -i "s/^#define DRIVER CFG_DRIVER/#define DRIVER $drv/" "$tmp/pines_sf.h"
      for f in "$tmp"/*.cpp; do
        g++ -std=c++17 -fsyntax-only -Wall -Wextra -Werror -I"$tmp" -Ipruebas/stub_arduino -DESP_ARDUINO_VERSION_MAJOR=$api "$f"
      done
      echo "OK $drv API-PWM=$api"
  done
done
