#!/usr/bin/env python3
"""V2 · Genera las constantes del firmware desde las fuentes únicas del diseño (no se editan a mano):
  firmware/v2/config_v2.h        geometría, motor, puente H, batería, succión y masa
  firmware/v2/stm32/src/pines_v2.h   pin, puerto y función alterna de cada señal

Fuentes: config/v2/robot_v2.yaml (geometría, Fase 3.5), config/v2/parametros_fase1.yaml (adherencia y plan),
config/v2/parametros_fase2.yaml (motor #5183), hardware/v2/mecanica/propiedades_masa.json (masa del CAD),
hardware/v2/electronica/generador/principal.py (pines del módulo, divisor de batería, R_IPROPI, VREF) y
barra_sensores.py (canal de cada sensor). Las funciones alternas y canales del ADC están verificados con
STM32_open_pin_data de ST (STM32G474C(B-C-E)Ux.xml y GPIO-STM32G47x_gpio_v1_0_Modes.xml).
Uso: python3 firmware/v2/herramientas/generar_config.py"""
import json
import math
import os
import sys

import yaml

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "hardware", "v2", "electronica", "generador"))


def val(d, *claves):
    for c in claves:
        d = d[c]
    return d["valor"] if isinstance(d, dict) and "valor" in d else d


def main():
    rob = yaml.safe_load(open(os.path.join(RAIZ, "config", "v2", "robot_v2.yaml"), encoding="utf-8"))
    f1 = yaml.safe_load(open(os.path.join(RAIZ, "config", "v2", "parametros_fase1.yaml"), encoding="utf-8"))
    f2 = yaml.safe_load(open(os.path.join(RAIZ, "config", "v2", "parametros_fase2.yaml"), encoding="utf-8"))
    masa = json.load(open(os.path.join(RAIZ, "hardware", "v2", "mecanica", "propiedades_masa.json"), encoding="utf-8"))
    import barra_sensores as BS            # noqa: E402  (canal de cada sensor)
    import principal as PR                  # noqa: E402  (pines y valores de la PCB principal)

    # ---------------------------------------------------------------- motor #5183 (fila "15:1 HPCB 6V con encoder")
    mot = next(m for m in f2["motores"] if "5183" in m["pn"])
    f35 = rob["fase35"]

    # ---------------------------------------------------------------- barra: posición de cada sensor (arco)
    n = int(val(rob, "barra_sensores", "n"))
    L = val(rob, "robot", "L_sensores") / 1000.0
    paso = val(rob, "barra_sensores", "paso_arco") / 1000.0
    ys, xs, mux, canal = [], [], [], []
    for i in range(n):
        a = (n / 2 - 0.5 - i) * paso / L
        xs.append(L * math.cos(a)); ys.append(L * math.sin(a))
        salida, k = BS.CANAL[f"S{i + 1}"]
        mux.append(0 if salida == "SENS_A" else 1); canal.append(k)

    # ---------------------------------------------------------------- valores de la PCB principal
    def valor_r(ref):
        p = next(p for p in PR.D.partes if p.ref == ref)
        v = p.valor.replace("Ω", "").strip()
        mult = {"k": 1e3, "M": 1e6}.get(v[-1], 1.0)
        return float(v[:-1]) * mult if v[-1] in "kM" else float(v)
    r_top, r_bot = valor_r("R3"), valor_r("R4")
    r_ipropi = valor_r("R19")
    r25, r26 = valor_r("R25"), valor_r("R26")
    vref = 3.3 * r26 / (r25 + r26)
    a_ipropi = 450e-6                                   # A/A, DRV8874 [V, SLVSF66A §6.5]
    i_trip = vref / (r_ipropi * a_ipropi)

    g = []
    g.append("// GENERADO por firmware/v2/herramientas/generar_config.py — no editar a mano.")
    g.append("// Tipos: [V] verificado (ficha) · [C] calculado · [E] estimado · [S] supuesto · [P] pendiente de medición.")
    g.append("#pragma once")
    g.append("#include <stdint.h>\n")
    g.append("namespace cfg2 {\n")
    g.append("// ---- barra de sensores (barra_sensores.py, robot_v2.yaml)")
    g.append(f"constexpr int   N_SENSORES = {n};")
    g.append(f"constexpr float L_BARRA = {L:.4f}f;          // m, radio del arco medido desde el eje de las ruedas [S]")
    g.append(f"constexpr float PASO_ARCO = {paso:.4f}f;       // m [S]")
    g.append("// coordenada lateral (m, + a la IZQUIERDA) y longitudinal (m, adelante del eje) de S1..S16")
    g.append("constexpr float SENSOR_Y[N_SENSORES] = {" + ", ".join(f"{y:.5f}f" for y in ys) + "};")
    g.append("constexpr float SENSOR_X[N_SENSORES] = {" + ", ".join(f"{x:.5f}f" for x in xs) + "};")
    g.append("// multiplexor (0 = U17 -> SENS_A/PA0, 1 = U18 -> SENS_B/PA1) y canal (S2..S0) de cada sensor")
    g.append("constexpr uint8_t SENSOR_MUX[N_SENSORES] = {" + ", ".join(str(m) for m in mux) + "};")
    g.append("constexpr uint8_t SENSOR_CANAL[N_SENSORES] = {" + ", ".join(str(c) for c in canal) + "};\n")
    g.append("// ---- ruedas, masa")
    g.append(f"constexpr float D_LLANTA = {val(rob, 'ruedas', 'D') / 1000:.4f}f;        // m [V Pololu #1087]")
    g.append(f"constexpr float W_VIA = {2 * val(rob, 'ruedas', 'y_centro') / 1000:.4f}f;           // m [S]")
    g.append(f"constexpr float MASA = {masa['masa_total_g'] / 1000:.4f}f;            // kg, CAD (piezas impresas sólidas) [C/E]")
    g.append(f"constexpr float MU_REF = {_mu(f1):.2f}f;           // adherencia llanta-pista [S, P01: medir]")
    g.append(f"constexpr float FACTOR_PLAN = {_factor(f1):.2f}f;      // fracción de la adherencia que usa el plan [S]\n")
    g.append("// ---- motor Pololu #5183 (15.25:1 HPCB 6 V, encoder 12 CPR) [V pololu.com/product/5183]")
    g.append(f"constexpr float MOTOR_V_NOM = {mot['V_nom']:.1f}f;")
    g.append(f"constexpr float MOTOR_RPM = {mot['rpm0']:.1f}f;           // sin carga a V_NOM")
    g.append(f"constexpr float MOTOR_PAR_BLOQUEO = {mot['par_kgcm'] * 0.0980665:.6f}f;   // N·m ({mot['par_kgcm']} kg·cm, extrapolado por Pololu)")
    g.append(f"constexpr float MOTOR_I_BLOQUEO = {mot['I_bloq']:.2f}f;      // A")
    g.append(f"constexpr float MOTOR_I_VACIO = {val(f35, 'motor_I0_A'):.2f}f;        // A")
    g.append("constexpr float MOTOR_REDUCCION = 15.25f;     // [V]")
    g.append("constexpr float CUENTAS_VUELTA = 12.0f * MOTOR_REDUCCION;   // 4 flancos de A y B: 12 por vuelta del motor [V] = 183 [C]")
    g.append(f"constexpr float MOTOR_LIMITE_V = {mot['V_ef']:.1f}f;       // V efectivos máximos en el motor (6 V nominales) [S]")
    g.append(f"constexpr float MOTOR_R = {val(f35, 'motor_R_ohm'):.2f}f;             // Ω [C]")
    g.append(f"constexpr float MOTOR_KT = {val(f35, 'motor_kt_Nm_A'):.5f}f;         // N·m/A en la salida [C]")
    g.append(f"constexpr float MOTOR_RTH = {val(f35, 'motor_Rth_KW'):.1f}f;           // K/W [E]")
    g.append(f"constexpr float MOTOR_CTH = {val(f35, 'motor_Cth_JK'):.1f}f;            // J/K [E]")
    g.append(f"constexpr float MOTOR_DT_MAX = {val(f35, 'motor_dT_max_K') if 'motor_dT_max_K' in f35 else 50.0:.1f}f;        // K, elevación admitida [S]\n")
    g.append("// ---- puente H DRV8874 (principal.py) [V SLVSF66A]")
    g.append(f"constexpr float R_IPROPI = {r_ipropi:.1f}f;         // Ω (R19/R21)")
    g.append(f"constexpr float A_IPROPI = {a_ipropi:.6f}f;          // A/A")
    g.append(f"constexpr float V_IPROPI_POR_A = R_IPROPI * A_IPROPI; // V/A = {r_ipropi * a_ipropi:.4f}")
    g.append(f"constexpr float I_TRIP = {i_trip:.3f}f;            // A, VREF {vref:.3f} V (R25 {r25:.0f} / R26 {r26:.0f}) [C]")
    g.append("constexpr float I_LIMITE_FIRMWARE = 1.5f;     // A por motor, frenado y arranque (FASE35_CORRECCIONES §3) [C]")
    g.append("constexpr float F_PWM = 20000.0f;             // Hz [S]\n")
    g.append("// ---- batería (divisor R3/R4)")
    g.append(f"constexpr float DIV_BATERIA = {(r_top + r_bot) / r_bot:.5f}f;   // ({r_top:.0f} + {r_bot:.0f}) / {r_bot:.0f} [C]\n")
    g.append("// ---- succión (robot_v2.yaml: cámara y Fase 3.5)")
    cam = val(rob, "camara", "interior")
    g.append(f"constexpr float AREA_CAMARA = {cam[0] * cam[1] / 1e6:.6f}f;    // m² ({cam[0]:.0f} × {cam[1]:.0f} mm) [V]")
    g.append("constexpr float FRACCION_RUEDAS = 0.96f;     // fracción de la succión sobre las ruedas motrices [C, FASE3_ENTREGA1 §6]")
    g.append(f"constexpr float DP0_CONSERVADOR = {val(f35, 'dP0_conservador_Pa'):.1f}f;   // Pa [S]")
    g.append("\n}  // namespace cfg2")
    escribir(os.path.join(RAIZ, "firmware", "v2", "config_v2.h"), g)

    # ---------------------------------------------------------------- pines
    AF = {"PA9": 6, "PA10": 6, "PB6": 2, "PB7": 2, "PA15": 1, "PB3": 1, "PB9": 1, "PB8": 1, "PA8": 2, "PC11": 8}
    ADC = {"PA0": (1, 1), "PA1": (2, 2), "PA2": (1, 3), "PA3": (1, 4), "PB2": (2, 12)}
    p = ["// GENERADO por firmware/v2/herramientas/generar_config.py desde hardware/v2/electronica/generador/principal.py.",
         "// Funciones alternas y canales de ADC: STM32_open_pin_data (ST), STM32G474C(B-C-E)Ux [V].",
         "#pragma once", "#include <stdint.h>", "", "namespace pin2 {", "",
         "struct Gpio { char puerto; uint8_t num; uint8_t af; };", "struct Analogica { char puerto; uint8_t num; uint8_t adc; uint8_t canal; };", ""]
    for mcu, red in sorted(PR.FUNCION.items(), key=lambda kv: kv[1]):
        if not mcu.startswith("P"):
            continue
        nombre = red.replace("+", "").replace("-", "_")
        if mcu in ADC:
            a, c = ADC[mcu]
            p.append(f"constexpr Analogica {nombre}{{'{mcu[1]}', {int(mcu[2:])}, {a}, {c}}};   // {mcu} ADC{a}_IN{c}")
        else:
            p.append(f"constexpr Gpio {nombre}{{'{mcu[1]}', {int(mcu[2:])}, {AF.get(mcu, 0)}}};   // {mcu}" +
                     (f" AF{AF[mcu]}" if mcu in AF else ""))
    p.append("constexpr Gpio LED_SUCCION{'C', 6, 0};   // PC6: LED azul del módulo WeAct [V esquemático WeAct]")
    p += ["", "}  // namespace pin2"]
    escribir(os.path.join(RAIZ, "firmware", "v2", "stm32", "src", "pines_v2.h"), p)


def _mu(f1):
    for sec in f1.values():
        if isinstance(sec, dict) and "mu_ref" in sec:
            return sec["mu_ref"]["valor"]
    raise KeyError("mu_ref")


def _factor(f1):
    for sec in f1.values():
        if isinstance(sec, dict) and "factor_plan" in sec:
            return sec["factor_plan"]["valor"]
    raise KeyError("factor_plan")


def escribir(ruta, lineas):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    open(ruta, "w", encoding="utf-8").write("\n".join(lineas) + "\n")
    print("->", os.path.relpath(ruta, RAIZ))


if __name__ == "__main__":
    main()
