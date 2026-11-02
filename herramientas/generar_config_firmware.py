#!/usr/bin/env python3
"""Genera las cabeceras del firmware a partir de las fuentes únicas:
  firmware/config_maestra.h          <- config/robot_maestro.yaml (motor, geometría, barra, control, batería)
  firmware/stm32/src/pines_generados.h <- hardware/electronics/generador/diseno.py (pines, AF y canales ADC de la PCB)

Uso:
  python3 herramientas/generar_config_firmware.py             # escribe las cabeceras
  python3 herramientas/generar_config_firmware.py --verificar # falla (código 1) si no están sincronizadas
diseno.py lee los símbolos de KiCad 9 (variable KICAD_SHARE; por omisión /opt/resolute/usr/share/kicad)."""
from __future__ import annotations

import hashlib
import math
import os
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(RAIZ, "sim"))
sys.path.insert(0, os.path.join(RAIZ, "hardware", "electronics", "generador"))
import config as CF  # noqa: E402

DESTINO = os.path.join(RAIZ, "firmware", "config_maestra.h")
DESTINO_PINES = os.path.join(RAIZ, "firmware", "stm32", "src", "pines_generados.h")
FUENTES = {"error": 0, "modelo": 1, "giroscopio": 2, "encoder": 3}


def f(v):
    t = f"{float(v):.7g}"
    if not any(ch in t for ch in ".e"):
        t += ".0"
    return t + "f"


def b(v):
    return "true" if v else "false"


def generar() -> str:
    cfg = CF.cargar()
    with open(CF.RUTA, "rb") as fh:
        huella = hashlib.sha256(fh.read()).hexdigest()[:16]
    c = CF.construir(cfg)
    m = c.motor
    arq = cfg["arquitectura"]
    prm = c.prm
    fw = cfg["firmware"]
    lim = m.limite_V if math.isfinite(m.limite_V) else 99.0
    L = ["// GENERADO por herramientas/generar_config_firmware.py — NO EDITAR A MANO.",
         f"// Fuente: config/robot_maestro.yaml (versión {cfg['version']}, sha256 {huella}).",
         "// Para cambiar un valor: editar el YAML, regenerar y correr pruebas/ejecutar_todo.sh.",
         "#pragma once", "", "namespace cfg {",
         f'constexpr const char* HUELLA_YAML = "{huella}";',
         f'constexpr const char* MOTOR = "{m.nombre}";',
         f'constexpr const char* BARRA = "{arq["barra"]}";',
         f'constexpr const char* MCU = "{arq["mcu"]}";',
         f'constexpr const char* CONTROL = "{arq["control"]}";', "",
         "// Motor (datos del fabricante a V_nom, salida de la reductora; ver el YAML para el origen de cada valor)",
         f"constexpr float MOTOR_V_NOM = {f(m.V_nom)};", f"constexpr float MOTOR_RPM = {f(m.rpm)};",
         f"constexpr float MOTOR_PAR_BLOQUEO = {f(m.T_bl)};   // N·m",
         f"constexpr float MOTOR_I_BLOQUEO = {f(m.I_bl)};", f"constexpr float MOTOR_I_VACIO = {f(m.I0)};",
         f"constexpr float MOTOR_LIMITE_V = {f(lim)};      // 99 = sin límite",
         f"constexpr float RELACION = {f(m.G)};",
         f"constexpr float CPR_RUEDA = {f(c.cpr_rueda)};   // cuentas del encoder por vuelta de rueda (4 flancos)", "",
         "// Geometría y masa",
         f"constexpr float L_CUELLO = {f(c.L)};", f"constexpr float W_VIA = {f(c.W)};",
         f"constexpr float D_LLANTA = {f(2 * c.r)};", f"constexpr float MASA = {f(c.masa)};", "",
         "// Barra: posición de cada sensor en el marco del cuerpo (x adelante, y izquierda); índice 0 = S1 (izquierda).",
         f"constexpr int N_SENSORES = {len(c.sx)};",
         "constexpr float SENSOR_X[N_SENSORES] = {" + ", ".join(f(v) for v in c.sx) + "};",
         "constexpr float SENSOR_Y[N_SENSORES] = {" + ", ".join(f(v) for v in c.sy) + "};",
         f"constexpr float UMBRAL = {f(c.umbral)};",
         f"constexpr bool RESTA_AMBIENTE = {b(cfg['barras'][arq['barra']].get('resta_ambiente', cfg['optica']['resta_ambiente']))};",
         f"constexpr unsigned T_EMISOR_US = {int(round(cfg['optica']['t_emisor'] * 1e6))};", "",
         "// Control (vigente: competencia) y modo seguro",
         f"constexpr unsigned long PERIODO_MIN_US = {int(round(cfg['control']['T_min'] * 1e6))};",
         f"constexpr float T_PERDIDA = {f(c.t_perdida)};"]
    for k in ("v_max", "a_lat", "a_lon", "k_pp", "kp", "kd", "tau_d", "tau_k"):
        L.append(f"constexpr float {k.upper()} = {f(prm[k])};")
    L.append(f"constexpr float PISO = {f(prm.get('piso', 0.0))};   // ciclo mínimo de la rueda interior")
    L.append(f"constexpr int FUENTE_CURVATURA = {FUENTES[prm.get('fuente_k', 'error')]};   // 0 C2, 1 C3m, 2 C3g, 3 C3e")
    seg = cfg["control"].get("C3e")
    if seg:
        L.append("// Modo seguro (C3e, 100 % en las 6 plantas de incertidumbre; se elige con la consola)")
        for k in ("v_max", "a_lat", "a_lon", "k_pp", "kp", "kd", "tau_d", "tau_k", "piso"):
            L.append(f"constexpr float SEG_{k.upper()} = {f(seg[k])};")
        L.append(f"constexpr int SEG_FUENTE = {FUENTES[seg.get('fuente_k', 'error')]};")
    L += ["", "// Puente H, batería y seguridad",
          f"constexpr unsigned F_PWM = {int(cfg['conductor']['f_pwm'])};",
          f"constexpr float V_BATERIA_BAJA = {f(cfg['bateria']['V_baja'])};",
          f"constexpr float V_BATERIA_CRITICA = {f(fw['v_bateria_critica'])};",
          f"constexpr float T_BLOQUEO = {f(fw['t_bloqueo'])};",
          f"constexpr bool INVERTIR_MOTOR_IZQ = {b(fw['invertir_motor_izq'])};",
          f"constexpr bool INVERTIR_MOTOR_DER = {b(fw['invertir_motor_der'])};",
          f"constexpr bool INVERTIR_ENCODER_IZQ = {b(fw['invertir_encoder_izq'])};",
          f"constexpr bool INVERTIR_ENCODER_DER = {b(fw['invertir_encoder_der'])};",
          f"constexpr unsigned UART_BAUDIOS = {int(fw['uart_baudios'])};",
          f"constexpr float T_CALIBRACION_MAX = {f(fw['t_calibracion_max'])};",
          f"constexpr float RANGO_CAL_MIN = {f(fw['rango_cal_min'])};",
          "}  // namespace cfg"]
    return "\n".join(L) + "\n"


def generar_pines() -> str:
    import diseno as D
    L = ["// GENERADO por herramientas/generar_config_firmware.py desde hardware/electronics/generador/diseno.py.",
         "// NO EDITAR A MANO: los pines salen del mismo diseño que el esquemático y la PCB.", "#pragma once",
         "#include <stdint.h>", "", "namespace pin {",
         "struct Gpio { char puerto; uint8_t num; int8_t af; };   // af = -1: GPIO o analógico"]
    for nm, (red, fun, af) in sorted(D.FIJOS.items(), key=lambda kv: kv[1][0]):
        if nm in ("PG10", "PB8"):
            continue
        L.append(f"constexpr Gpio {red} = {{'{nm[1]}', {int(nm[2:])}, {af if af is not None else -1}}};   // {nm} {fun}")
    canal = {red: int(fun.split("_CH")[1]) for nm, (red, fun, af) in D.FIJOS.items() if fun.startswith("TIM1_CH")}
    L.append("// Canal de TIM1 que maneja cada entrada del DRV8833")
    for red in ("PWM_AIN1", "PWM_AIN2", "PWM_BIN1", "PWM_BIN2"):
        L.append(f"constexpr int CANAL_{red[4:]} = {canal[red]};")
    adc = {1: [], 2: []}
    for nm, red in D.ADC_ASIG.items():
        inst = D.ADC_INST[nm]
        ch = D.canales_adc(nm)[inst]
        idx = int(red[1:]) - 1 if red.startswith("S") else -1
        adc[inst].append((idx if idx >= 0 else 99, nm, ch, idx))
    for inst in (1, 2):
        adc[inst].sort()
        L.append(f"// ADC{inst}: secuencia regular (sensor -1 = batería)")
        L.append(f"constexpr int ADC{inst}_N = {len(adc[inst])};")
        L.append(f"constexpr uint8_t ADC{inst}_CANAL[ADC{inst}_N] = {{" + ", ".join(str(a[2]) for a in adc[inst]) + "};")
        L.append(f"constexpr int8_t ADC{inst}_SENSOR[ADC{inst}_N] = {{" + ", ".join(str(a[3]) for a in adc[inst]) + "};")
        L.append(f"constexpr Gpio ADC{inst}_PIN[ADC{inst}_N] = {{" + ", ".join(f"{{'{a[1][1]}', {int(a[1][2:])}, -1}}" for a in adc[inst]) + "};")
    r3 = float(D.por_ref()["R3"].valor.rstrip("kΩ")) * 1e3
    r4 = float(D.por_ref()["R4"].valor.rstrip("kΩ")) * 1e3
    L.append(f"constexpr float DIVISOR_VBAT = {f((r3 + r4) / r4)};   // (R3 + R4) / R4")
    L.append("}  // namespace pin")
    return "\n".join(L) + "\n"


def main():
    salidas = [(DESTINO, generar()), (DESTINO_PINES, generar_pines())]
    if "--verificar" in sys.argv:
        mal = [d for d, t in salidas if (open(d, encoding="utf-8").read() if os.path.exists(d) else "") != t]
        if mal:
            print("NO sincronizadas:", ", ".join(os.path.relpath(d, RAIZ) for d in mal),
                  "-> correr python3 herramientas/generar_config_firmware.py")
            sys.exit(1)
        print("config_maestra.h y pines_generados.h sincronizadas con el YAML y el diseño de la PCB")
        return
    for d, t in salidas:
        with open(d, "w", encoding="utf-8") as fh:
            fh.write(t)
        print(f"escrito {os.path.relpath(d, RAIZ)}")


if __name__ == "__main__":
    main()
