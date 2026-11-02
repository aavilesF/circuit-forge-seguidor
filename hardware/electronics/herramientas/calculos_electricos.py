#!/usr/bin/env python3
"""Cálculos eléctricos de la PCB (reproducibles) -> docs/CALCULOS_ELECTRICOS.md.
Los datos de partes indican su origen: [F] hoja de datos/ficha verificada, [S] supuesto conservador, [D] decisión."""
import json
import math
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "hardware", "electronics", "generador"))
sys.path.insert(0, os.path.join(RAIZ, "sim"))
import config as CF  # noqa: E402
import diseno as D  # noqa: E402

RHO_CU = 1.72e-8          # Ω·m a 20 °C
OZ = 35e-6                # m (1 oz)


def ipc2221(ancho_mm, oz=1.0, dT=10.0, externa=True):
    """Corriente admisible IPC-2221: I = k·ΔT^0.44·A^0.725 (A en mil²)."""
    area_mil2 = (ancho_mm / 0.0254) * (oz * 1.378)
    k = 0.048 if externa else 0.024
    return k * dT ** 0.44 * area_mil2 ** 0.725


def r_pista(largo_mm, ancho_mm, oz=1.0):
    return RHO_CU * largo_mm * 1e-3 / (ancho_mm * 1e-3 * oz * OZ)


def main():
    cfg = CF.cargar()
    mot = CF.motor(cfg, cfg["arquitectura"]["motor"])
    vb = cfg["bateria"]["V_llena"]
    i_bl = vb / mot.R                          # bloqueo a batería llena
    rutas = json.load(open(os.path.join(RAIZ, "hardware", "electronics", "generador", "rutas.json")))
    largo = {}
    for t in rutas["pistas"]:
        L = math.hypot(t["x2"] - t["x1"], t["y2"] - t["y1"])
        largo.setdefault(t["red"], []).append((L, t["w"]))
    filas = []
    for red, i_max, nota in [("VBAT_IN", 2 * i_bl + 0.1, "2 motores en bloqueo + lógica"), ("VBAT_F", 2 * i_bl + 0.1, ""),
                             ("VBAT_SRC", 2 * i_bl + 0.1, ""), ("VBAT_SW", 2 * i_bl + 0.1, ""),
                             ("MOT_L_1", i_bl, "bloqueo a 8.4 V"), ("MOT_L_2", i_bl, ""), ("MOT_R_1", i_bl, ""), ("MOT_R_2", i_bl, ""),
                             ("BUCK_SW", 0.47 + 0.7, "carga pico + mitad del rizo del inductor"), ("EMIT_K", 16 * 0.028, "16 emisores a 28 mA (peor caso)")]:
        segs = largo.get(red, [])
        if not segs:
            continue
        w_min = min(w for _, w in segs)
        L_tot = sum(L for L, _ in segs)
        R = sum(r_pista(L, w) for L, w in segs)
        L_corto = sum(L for L, w in segs if ipc2221(w) < i_max)
        filas.append((red, i_max, w_min, ipc2221(w_min), L_tot, R, i_max * R, nota, L_corto))
    # caídas de la entrada a VM del DRV8833
    r_fet = 0.10      # [S] por MOSFET (conservador; AO3401A a VGS ≈ −7.6 V)
    r_ptc = 0.12      # [S] PTC 1812L150 (resistencia máxima tras disparo del rango de la serie, conservador)
    r_trazo = sum(f[5] for f in filas if f[0].startswith("VBAT"))
    i_tot = 2 * i_bl + 0.1
    caida = i_tot * (2 * r_fet + r_ptc + r_trazo)
    # puente H
    rds_drv = 0.36    # [F] DRV8833: HS + LS 360 mΩ (características, TI)
    p_drv = 2 * i_bl ** 2 * rds_drv
    # emisores y sensores
    vf_min, vf_max = 1.2, 1.6        # [F] QRE1113 a 20 mA (típ., máx.)
    r_led = 75.0
    if_max = (3.3 - vf_min) / r_led; if_min = (3.3 - vf_max) / r_led
    p_rled = if_max ** 2 * r_led
    i_emis = 16 * if_max
    # ADC
    f_adc = 170e6 / 4
    t_conv = (47.5 + 12.5) / f_adc
    n_serie = max(len([p for p in D.ADC_INST if D.ADC_INST[p] == 1]), len([p for p in D.ADC_INST if D.ADC_INST[p] == 2]))
    t_barrido = n_serie * t_conv
    t_lectura = 2 * t_barrido + cfg["optica"]["t_emisor"]
    tau = (10e3 + 1e3) * 10e-12          # [S] 1 kΩ interno + 5 pF de muestreo + 5 pF del pin
    # 3.3 V
    i_33_pico = i_emis + 0.030 + 0.010 + 16 * 3.3 / 10e3 + 0.003
    i_33_medio = i_emis * (cfg["optica"]["t_emisor"] + t_barrido) / 1e-3 + 0.030 + 0.010 + 16 * 3.3 / 10e3 * 0.5 + 0.003
    L_buck, f_sw = 2.2e-6, 650e3
    d = 3.3 / vb
    rizo = (vb - 3.3) * d / (L_buck * f_sw)
    # divisor de batería
    r3, r4 = 100e3, 33e3
    v_adc = vb * r4 / (r3 + r4)
    # encoders
    cpr = cfg["motores"][cfg["arquitectura"]["motor"]]["cpr_motor"] * mot.G
    v_max = cfg["control"][cfg["arquitectura"]["control"]]["v_max"]
    cuentas_ms = v_max / (math.pi * cfg["geometria"]["D_llanta"]) * cpr / 1000
    L = ["# Cálculos eléctricos de la PCB-chasis (generado por hardware/electronics/herramientas/calculos_electricos.py)", "",
         "Origen de los datos: [F] hoja de datos o ficha verificada, [S] supuesto conservador, [C] calculado. "
         "Pistas exteriores de 1 oz (35 µm). Corrientes admisibles según IPC-2221 con 10 °C de elevación.", "",
         "## 1. Corrientes y anchos de pista (rutas reales de la PCB)", "",
         "| Red | I máx [C] | Ancho mínimo usado | I admisible (IPC-2221, 10 °C) | Largo total | Largo bajo I máx | R de pista | Caída | Nota |",
         "|---|---|---|---|---|---|---|---|---|"]
    for red, i, w, ia, Lt, R, dv, nota, Lc in filas:
        L.append(f"| {red} | {i:.2f} A | {w:.2f} mm | {ia:.2f} A | {Lt:.1f} mm | {Lc:.1f} mm | {R * 1000:.1f} mΩ | {dv * 1000:.1f} mV | {nota} |")
    L += ["", "\"Largo bajo I máx\" suma los tramos cuya corriente admisible (IPC-2221, 10 °C) es menor que el peor caso de la red. "
          "En VBAT_SW es la entrada al pin 12 (VM) del DRV8833: 1.35 mm de pista de 0.30 mm entre la vía y el pin (el propio pad del "
          "encapsulado mide 0.40 mm), encerrada entre las ramas del bus PWM. Solo se acerca al límite con **los dos motores bloqueados a "
          "la vez con la batería llena** (1.05 A); el firmware corta a los 0.3 s de bloqueo y el pico simulado en carrera es 0.48 A por "
          "motor. Una pista de 0.30 mm admite 1.0 A con 10 °C y ≈ 1.3 A con 20 °C de elevación (misma fórmula): aceptado.", "",
          "Los demás tramos delgados de las redes de potencia son entradas a pads pequeños (0402/0603) que solo llevan "
          "corriente de señal (divisor, habilitación, desacoplo); el tronco que lleva la corriente del motor es de 0.8 mm (VBAT) y 0.5 mm (motores). "
          "GND y +3V3 van por planos internos completos (In1.Cu y In2.Cu) más relleno de GND en ambas caras.", "",
          "## 2. Ruta de potencia y caídas", "",
          f"- Corriente de bloqueo por motor a {vb} V: {vb:.1f} V / {mot.R:.1f} Ω = **{i_bl:.3f} A** [C, R = 12 V / 0.75 A, ficha Pololu]",
          f"- Peor caso de la entrada (2 motores en bloqueo + lógica): {i_tot:.2f} A",
          f"- Caída batería → VM: PTC ({r_ptc} Ω [S]) + 2 MOSFET ({r_fet} Ω c/u [S]) + pistas ({r_trazo * 1000:.0f} mΩ [C]) = "
          f"**{caida:.2f} V** a {i_tot:.2f} A (el simulador ya usa R_interna = {cfg['bateria']['R_interna']} Ω para todo el lazo)",
          f"- Disipación en cada MOSFET: {(i_tot ** 2 * r_fet) * 1000:.0f} mW (SOT-23) — sin disipador",
          f"- Fusible PTC 1812L150/12DR: corriente de mantenimiento 1.5 A [F] > {i_tot:.2f} A de peor caso; dispara ante corto",
          f"- DRV8833PWPR: 1.5 A RMS por canal [F] contra {i_bl:.2f} A de bloqueo; disipación en bloqueo de ambos motores "
          f"{p_drv * 1000:.0f} mW con HS+LS = {rds_drv} Ω [F]; la almohadilla térmica va a GND con vías térmicas (huella oficial)",
          f"- Protección contra inversión: Q1 bloquea con su diodo interno; |VGS| = {vb * 100 / 110:.1f} V con la batería llena "
          "(R1 100 k / R2 10 k) < 12 V máx. [F]. El interruptor SW1 solo conmuta la compuerta (≈ 80 µA) y es de 100 mA / 12 V [F]",
          "- TVS SMAJ9.0A: VRWM 9.0 V [F] > 8.4 V; recorta picos inductivos y de conexión. **No conectar baterías 3S** "
          "(12.6 V): el TVS conduciría y el PTC dispararía; el DRV8833 admite 11.8 V máx. [F]", "",
          "## 3. Regulador de 3.3 V (TPS563200)", "",
          f"- VOUT = 0.765 V · (1 + 33.2 k / 10 k) = **{0.765 * (1 + 33.2 / 10):.3f} V** [F, VFB y tabla de la hoja de datos]",
          f"- Carga pico: emisores {i_emis * 1000:.0f} mA + MCU 30 mA + encoders 10 mA + resistencias de los sensores {16 * 3.3 / 10:.1f} mA + LED = "
          f"**{i_33_pico * 1000:.0f} mA**; promedio con emisores pulsados ≈ {i_33_medio * 1000:.0f} mA. Capacidad: 3 A [F]",
          f"- Rizo de corriente del inductor (2.2 µH, 650 kHz, {vb} V): {rizo:.2f} A pico a pico; pico del inductor "
          f"{i_33_pico + rizo / 2:.2f} A, muy por debajo de la corriente nominal del 74438357022 (7 A Idc según RS; 5.2 A en la ficha de DigiKey) [F]",
          "- Entrada 2 × 10 µF + 100 nF, salida 2 × 22 µF (dentro del rango 20-68 µF de la tabla [F]), arranque 100 nF [F]", "",
          "## 4. Sensores QRE1113GR y emisores", "",
          f"- Corriente de cada LED: (3.3 − VF) / 75 Ω = {if_min * 1000:.1f}-{if_max * 1000:.1f} mA (VF 1.2-1.6 V [F]); máximo continuo 50 mA [F]",
          f"- Disipación en la resistencia de 75 Ω (0603, 100 mW): {p_rled * 1000:.0f} mW con el emisor encendido continuo (peor caso)",
          f"- Q3 AO3400A conmuta {i_emis:.2f} A (5.7 A [F])",
          "- Fototransistor con 10 kΩ a 3.3 V: con IC(ON) = 0.1-0.9 mA [F, a 1 mm sobre espejo] la salida satura sobre blanco; "
          "a 3.05 mm sobre fórmica la señal real es una medición pendiente (M8)", "",
          "## 5. Tiempos del ADC (ADC1 y ADC2 en paralelo, reloj HCLK/4 = 42.5 MHz)", "",
          f"- Conversión: (47.5 + 12.5) ciclos = {t_conv * 1e6:.2f} µs; {n_serie} conversiones en serie por ADC = {t_barrido * 1e6:.1f} µs por barrido",
          f"- Lectura con resta de luz ambiente: 2 barridos + {cfg['optica']['t_emisor'] * 1e6:.0f} µs de establecimiento = "
          f"**{t_lectura * 1e6:.0f} µs** (el simulador usa {CF.construir().t_lectura * 1e6:.0f} µs: conservador)",
          f"- Muestreo con fuente de 10 kΩ: τ ≈ {tau * 1e9:.0f} ns; 47.5 ciclos = {47.5 / f_adc * 1e6:.2f} µs = {47.5 / f_adc / tau:.0f} τ → error < 1 LSB", "",
          "## 6. Batería, encoders y USART", "",
          f"- Divisor 100 k / 33 k: {vb} V → {v_adc:.3f} V en el ADC (< 3.3 V); corriente {vb / (r3 + r4) * 1e6:.0f} µA",
          f"- Encoders: {cpr:.1f} cuentas por vuelta de rueda ({cfg['motores'][cfg['arquitectura']['motor']]['cpr_motor']} CPR [F] × {mot.G}); "
          f"a v_max = {v_max} m/s, {cuentas_ms:.2f} cuentas por ms (por eso la curvatura del control usa el modelo del motor y los encoders "
          "se usan para la detección de rueda trabada y la telemetría; el modo seguro C3e los usa con filtro)",
          f"- USART1: BRR = 170 MHz / 115200 = {round(170e6 / 115200)} → error {abs(170e6 / round(170e6 / 115200) - 115200) / 115200 * 100:.3f} %", "",
          "## 7. Funciones alternas del MCU (verificadas con STM32_open_pin_data de ST y con el símbolo oficial de KiCad)", "",
          "| Pin | Función | AF |", "|---|---|---|"]
    for nm, (red, fun, af) in sorted(D.FIJOS.items()):
        L.append(f"| {nm} | {red} ({fun}) | {af if af is not None else '—'} |")
    L += ["", "| Pin | Señal | ADC | Canal |", "|---|---|---|---|"]
    for nm, red in sorted(D.ADC_ASIG.items(), key=lambda kv: (kv[1][0], int(kv[1][1:]) if kv[1][1:].isdigit() else 99)):
        L.append(f"| {nm} | {red} | ADC{D.ADC_INST[nm]} | IN{D.canales_adc(nm)[D.ADC_INST[nm]]} |")
    ruta = os.path.join(RAIZ, "docs", "CALCULOS_ELECTRICOS.md")
    open(ruta, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("escrito", os.path.relpath(ruta, RAIZ))


if __name__ == "__main__":
    main()
