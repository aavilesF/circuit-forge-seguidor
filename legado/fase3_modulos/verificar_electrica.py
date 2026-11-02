#!/usr/bin/env python3
"""Verificación eléctrica automática del diseño de módulos (sustituye al ERC mientras no haya esquemático en KiCad).

Comprueba con config/robot_maestro.yaml, hardware/electronics/conexiones.csv y firmware/sf/pines_sf.h:
 1. Que los pines del CSV y del firmware coincidan.
 2. Reglas del ESP32-WROOM-32: sin pines de flash (6-11), entradas analógicas en ADC1, GPIO34-39 solo como entrada,
    pines de arranque (0, 2, 5, 12, 15) sin cargas que fuercen un nivel, sin pines repetidos.
 3. Límites del driver: VM de la batería llena contra el máximo; corriente de bloqueo (a la tensión máxima que
    permite el firmware) contra la corriente continua del driver; corriente de frenado inverso contra el pico.
 4. Regulador, fusible y dominio de voltaje de la barra de sensores.
Uso: python3 hardware/electronics/verificar_electrica.py   (código 1 si algo falla)"""
from __future__ import annotations

import csv
import math
import os
import re
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "sim"))
import config as CF  # noqa: E402

FALLAS, AVISOS = [], []


def ok(cond, texto, aviso=False):
    marca = "OK " if cond else ("AVISO" if aviso else "MAL")
    print(f"[{marca}] {texto}")
    if not cond:
        (AVISOS if aviso else FALLAS).append(texto)


def pines_firmware():
    txt = open(os.path.join(RAIZ, "firmware", "sf", "pines_sf.h"), encoding="utf-8").read()
    # bloque del driver vigente
    drv = CF.cargar()["conductor"]["modelo"]
    m = re.search(r"#if DRIVER == DRIVER_DRV8833(.*?)#else(.*?)#endif", txt, re.S)
    bloque = m.group(1) if drv == "DRV8833" else m.group(2)
    resto = txt.replace(m.group(0), bloque)
    pines = {}
    for nombre, valor in re.findall(r"(PIN_[A-Z0-9_]+)\s*=\s*(\d+)", resto):
        pines[nombre] = int(valor)
    return pines


def main():
    cfg = CF.cargar()
    c = CF.construir(cfg)
    drv = cfg["conductor"]
    m = c.motor
    print(f"Arquitectura: {m.nombre}, driver {drv['modelo']}, barra {c.barra}, MCU {c.mcu}\n")

    # 1. CSV vs firmware
    filas = list(csv.DictReader(open(os.path.join(os.path.dirname(__file__), "conexiones.csv"), encoding="utf-8")))
    gpio_csv = {}
    for f in filas:
        for lado in ("origen_pin", "destino_pin"):
            g = re.match(r"GPIO(\d+)", f[lado])
            if g:
                gpio_csv[f["red"]] = int(g.group(1))
    fw = pines_firmware()
    mapa = {"MUX_S0": "PIN_MUX_S0", "MUX_S1": "PIN_MUX_S1", "MUX_S2": "PIN_MUX_S2", "MUX_S3": "PIN_MUX_S3",
            "MUX_SIG": "PIN_MUX_SIG", "EMISORES": "PIN_EMISORES", "AIN1": "PIN_AIN1", "AIN2": "PIN_AIN2",
            "BIN1": "PIN_BIN1", "BIN2": "PIN_BIN2", "START": "PIN_START", "CAL": "PIN_CAL", "LED": "PIN_LED",
            "VBAT_MED": "PIN_BATERIA"}
    if drv["modelo"] == "TB6612FNG":
        mapa.update(PWMA="PIN_PWMA", PWMB="PIN_PWMB", STBY="PIN_STBY")
    for red, nombre in mapa.items():
        ok(gpio_csv.get(red) == fw.get(nombre), f"{red}: CSV GPIO{gpio_csv.get(red)} = firmware {nombre} GPIO{fw.get(nombre)}")

    # 2. reglas del ESP32-WROOM-32
    usados = list(fw.values())
    ok(len(usados) == len(set(usados)), f"sin GPIO repetidos en el firmware ({len(usados)} pines)")
    ok(not any(6 <= g <= 11 for g in usados), "ningún pin de la memoria flash (GPIO6-11)")
    adc1 = {32, 33, 34, 35, 36, 37, 38, 39}
    ok(fw["PIN_MUX_SIG"] in adc1 and fw["PIN_BATERIA"] in adc1, "entradas analógicas en ADC1")
    salidas = [v for k, v in fw.items() if k not in ("PIN_MUX_SIG", "PIN_BATERIA", "PIN_START", "PIN_CAL")]
    ok(not any(34 <= g <= 39 for g in salidas), "ninguna salida en GPIO34-39 (solo entrada)")
    arranque = {0, 5, 12, 15}
    ok(not (set(usados) & arranque), "sin GPIO0, 5, 12 ni 15 (pines de arranque); GPIO2 solo con el LED de la placa")

    # 3. driver
    Vmax = cfg["bateria"]["V_llena"]
    if drv["modelo"] == "TB6612FNG":
        vm_rec, vm_abs, i_cont, i_pico = 13.5, drv["TB6612_VM_max_absoluto"], drv["TB6612_I_canal"], 2.0
    else:
        vm_rec, vm_abs, i_cont, i_pico = drv["VM_max_recomendado"], drv["VM_max_absoluto"], drv["I_rms_PWP"], drv["I_ocp_min"]
    ok(Vmax <= vm_rec, f"VM: batería llena {Vmax} V ≤ {vm_rec} V recomendados ({vm_abs} V absolutos)")
    V_mot = min(Vmax, m.limite_V)
    I_bl = V_mot / m.R
    ok(I_bl <= i_cont, f"bloqueo a {V_mot:.1f} V: {I_bl:.2f} A por motor ≤ {i_cont} A continuos del driver")
    w_lib = (V_mot - m.I0 * m.R) / m.Ke
    I_inv = (V_mot + m.Ke * w_lib) / m.R
    ok(I_inv <= i_pico, f"frenado inverso total desde la velocidad libre: {I_inv:.2f} A ≤ {i_pico} A de pico "
       f"(el piso del control, {c.prm.get('piso', 0):.2f}, lo reduce)", aviso=True)
    # 4. regulador, fusible, barra
    I_tot = 2 * I_bl + cfg["bateria"]["I_logica"]
    ok(I_tot <= 1.5, f"fusible PTC 1.5 A: corriente máxima esperada {I_tot:.2f} A (bloqueo doble + lógica)")
    ok(cfg["bateria"]["V_baja"] - 0.3 >= 5.0 + 1.0, f"MP1584: entrada mínima {cfg['bateria']['V_baja'] - 0.3:.1f} V "
       "≥ 6.0 V para sostener 5.0 V (verificar ≥ 4.75 V con carga)", aviso=True)
    barra = cfg["barras"][c.barra]
    if "tcrt" in c.barra:
        ok(False, "barra clon alimentada a 5 V: su salida puede superar 3.3 V en el mux -> 10 kΩ en serie por canal "
           "(limita la corriente de inyección a < 0.2 mA) o alimentar la barra a 3.3 V (menos señal). MEDIR", aviso=True)
        ok(not barra.get("resta_ambiente", True), "sin pin de emisores documentado: el firmware no resta la luz ambiente "
           "(R06: probar con lámpara y luz solar)", aviso=True)
    print(f"\n{len(FALLAS)} fallas, {len(AVISOS)} avisos")
    sys.exit(1 if FALLAS else 0)


if __name__ == "__main__":
    main()
