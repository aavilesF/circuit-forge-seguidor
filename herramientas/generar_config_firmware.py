#!/usr/bin/env python3
"""Genera firmware/sf/config_maestra.h a partir de config/robot_maestro.yaml (única fuente de parámetros).

Uso:
  python3 herramientas/generar_config_firmware.py             # escribe la cabecera
  python3 herramientas/generar_config_firmware.py --verificar # falla (código 1) si la cabecera no está sincronizada
La prueba pruebas/ejecutar_todo.sh corre --verificar: un cambio en el YAML sin regenerar rompe las pruebas."""
from __future__ import annotations

import hashlib
import math
import os
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(RAIZ, "sim"))
import config as CF  # noqa: E402

DESTINO = os.path.join(RAIZ, "firmware", "sf", "config_maestra.h")


def f(v):
    t = f"{float(v):.7g}"
    if not any(ch in t for ch in ".e"):
        t += ".0"
    return t + "f"


def generar() -> str:
    cfg = CF.cargar()
    with open(CF.RUTA, "rb") as fh:
        huella = hashlib.sha256(fh.read()).hexdigest()[:16]
    c = CF.construir(cfg)
    m = c.motor
    arq = cfg["arquitectura"]
    prm = c.prm
    fuente = {"error": 0, "modelo": 1, "giroscopio": 2}[prm.get("fuente_k", "error")]
    lim = m.limite_V if math.isfinite(m.limite_V) else 99.0
    L = []
    L.append("// GENERADO por herramientas/generar_config_firmware.py — NO EDITAR A MANO.")
    L.append(f"// Fuente: config/robot_maestro.yaml (versión {cfg['version']}, sha256 {huella}).")
    L.append("// Para cambiar un valor: editar el YAML, regenerar y correr pruebas/ejecutar_todo.sh.")
    L.append("#pragma once")
    L.append("")
    L.append("namespace cfg {")
    L.append(f'constexpr const char* HUELLA_YAML = "{huella}";')
    L.append(f'constexpr const char* MOTOR = "{m.nombre}";')
    L.append(f'constexpr const char* BARRA = "{arq["barra"]}";')
    L.append(f'constexpr const char* MCU = "{arq["mcu"]}";')
    L.append(f'constexpr const char* CONTROL = "{arq["control"]}";')
    L.append("")
    L.append("// Motor (datos del fabricante a V_nom; ver YAML para el origen de cada valor)")
    L.append(f"constexpr float MOTOR_V_NOM = {f(m.V_nom)};")
    L.append(f"constexpr float MOTOR_RPM = {f(m.rpm)};")
    L.append(f"constexpr float MOTOR_PAR_BLOQUEO = {f(m.T_bl)};   // N·m")
    L.append(f"constexpr float MOTOR_I_BLOQUEO = {f(m.I_bl)};")
    L.append(f"constexpr float MOTOR_I_VACIO = {f(m.I0)};")
    L.append(f"constexpr float MOTOR_LIMITE_V = {f(lim)};      // 99 = sin límite")
    L.append("")
    L.append("// Geometría y masa")
    L.append(f"constexpr float L_CUELLO = {f(c.L)};")
    L.append(f"constexpr float W_VIA = {f(c.W)};")
    L.append(f"constexpr float D_LLANTA = {f(2 * c.r)};")
    L.append(f"constexpr float MASA = {f(c.masa)};")
    L.append("")
    L.append("// Barra de sensores: posición de cada sensor en el marco del cuerpo (x adelante, y izquierda),")
    L.append("// índice 0 = extremo derecho. La estimación usa y (sf::estimar_coord).")
    L.append(f"constexpr int N_SENSORES = {len(c.sx)};")
    L.append("constexpr float SENSOR_X[N_SENSORES] = {" + ", ".join(f(v) for v in c.sx) + "};")
    L.append("constexpr float SENSOR_Y[N_SENSORES] = {" + ", ".join(f(v) for v in c.sy) + "};")
    L.append(f"constexpr float UMBRAL = {f(c.umbral)};")
    L.append("")
    L.append("// Control")
    L.append(f"constexpr unsigned long PERIODO_MIN_US = {int(round(cfg['control']['T_min'] * 1e6))};")
    L.append(f"constexpr float T_PERDIDA = {f(c.t_perdida)};")
    if arq["control"] == "C1":
        L.append("// C1 no se implementa en el firmware vigente")
    else:
        for k in ("v_max", "a_lat", "a_lon", "k_pp", "kp", "kd", "tau_d", "tau_k"):
            L.append(f"constexpr float {k.upper()} = {f(prm[k])};")
        L.append(f"constexpr int FUENTE_CURVATURA = {fuente};   // 0 error (C2), 1 modelo del motor (C3m), 2 giroscopio (C3g)")
    L.append("")
    L.append("// Batería")
    L.append(f"constexpr float V_BATERIA_BAJA = {f(cfg['bateria']['V_baja'])};")
    L.append("}  // namespace cfg")
    return "\n".join(L) + "\n"


def main():
    texto = generar()
    if "--verificar" in sys.argv:
        actual = open(DESTINO, encoding="utf-8").read() if os.path.exists(DESTINO) else ""
        if actual != texto:
            print("config_maestra.h NO está sincronizada con config/robot_maestro.yaml: correr "
                  "python3 herramientas/generar_config_firmware.py")
            sys.exit(1)
        print("config_maestra.h sincronizada con config/robot_maestro.yaml")
        return
    with open(DESTINO, "w", encoding="utf-8") as fh:
        fh.write(texto)
    print(f"escrito {os.path.relpath(DESTINO, RAIZ)}")


if __name__ == "__main__":
    main()
