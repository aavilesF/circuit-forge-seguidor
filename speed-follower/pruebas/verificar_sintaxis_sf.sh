#!/usr/bin/env bash
# Comprueba sintaxis y tipos del firmware del Speed Follower contra el stub de Arduino
# (pruebas/stub_arduino). NO es el SDK real del ESP32: no sustituye compilar con arduino-esp32.
# Cubre 2 drivers × 2 motores × 2 versiones de la API de PWM.
set -euo pipefail
cd "$(dirname "$0")/../.."
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
for drv in DRIVER_DRV8833 DRIVER_TB6612; do
  for mot in MOTOR_POLOLU_12V_15 MOTOR_GA12_6V; do
    for api in 2 3; do
      cp speed-follower/firmware/sf/*.h speed-follower/firmware/sf/*.cpp "$tmp/"
      cp speed-follower/firmware/sf/sf.ino "$tmp/sf_ino.cpp"
      sed -i "s/^#define DRIVER DRIVER_DRV8833/#define DRIVER $drv/; s/^#define MOTOR MOTOR_POLOLU_12V_15/#define MOTOR $mot/" "$tmp/pines_sf.h"
      for f in "$tmp"/*.cpp; do
        g++ -std=c++17 -fsyntax-only -Wall -Wextra -Werror -I"$tmp" -Ipruebas/stub_arduino -DESP_ARDUINO_VERSION_MAJOR=$api "$f"
      done
      echo "OK $drv $mot API-PWM=$api"
    done
  done
done
