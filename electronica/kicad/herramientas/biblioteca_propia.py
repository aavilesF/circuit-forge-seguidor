"""Símbolos propios del robot casero (módulos que no existen en las bibliotecas oficiales de KiCad).

IMPORTANTE: son símbolos FUNCIONALES. El orden y los nombres de los pines de los módulos comerciales
(ESP32 DevKit, DRV8833, MP1584) cambian de un fabricante a otro. Hay que compararlos con la pieza real
antes de fabricar (ver electronica/kicad/NOTAS.md, sección "Por verificar").
"""
from kicad_gen import make_custom_symbol

# --- ESP32 DevKit de 38 pines (disposición tipo ESP32-DevKitC: 19 pines por lado). VERIFICAR con la placa real.
ESP32_IZQ = [  # (numero físico, nombre)
    (1, "3V3"), (2, "EN"), (3, "IO36_SVP"), (4, "IO39_SVN"), (5, "IO34"), (6, "IO35"), (7, "IO32"),
    (8, "IO33"), (9, "IO25"), (10, "IO26"), (11, "IO27"), (12, "IO14"), (13, "IO12"), (14, "GND"),
    (15, "IO13"), (16, "SD2"), (17, "SD3"), (18, "CMD"), (19, "5V")]
ESP32_DER = [
    (38, "GND"), (37, "IO23"), (36, "IO22"), (35, "TXD0"), (34, "RXD0"), (33, "IO21"), (32, "GND"),
    (31, "IO19"), (30, "IO18"), (29, "IO5"), (28, "IO17"), (27, "IO16"), (26, "IO4"), (25, "IO0"),
    (24, "IO2"), (23, "IO15"), (22, "SD1"), (21, "SD0"), (20, "CLK")]


def esp32_devkit_38():
    # Numeración del lado derecho: el pin físico 38 queda arriba a la derecha (misma fila que el pin 1).
    return make_custom_symbol("ESP32_DevKit_38", "A", "ESP32 DevKit 38 pines",
                              [(n, nm, "bidirectional") for n, nm in ESP32_IZQ],
                              [(n, nm, "bidirectional") for n, nm in ESP32_DER],
                              half_width=10.16,
                              desc="Modulo ESP32 DevKit de 38 pines; orden de pines por verificar con la placa real")


def modulo_drv8833():
    izq = [(1, "VM"), (2, "GND"), (3, "AIN1"), (4, "AIN2"), (5, "BIN1"), (6, "BIN2"), (7, "SLEEP"), (8, "FAULT")]
    der = [(9, "AOUT1"), (10, "AOUT2"), (11, "BOUT1"), (12, "BOUT2")]
    return make_custom_symbol("DRV8833_Modulo", "U", "Modulo DRV8833", izq, der, half_width=7.62,
                              desc="Modulo puente H doble DRV8833; orden de pines por verificar con el modulo real")


def modulo_mp1584():
    izq = [(1, "IN+"), (2, "IN-")]
    der = [(3, "OUT+"), (4, "OUT-")]
    return make_custom_symbol("MP1584_Modulo", "U", "Modulo MP1584EN", izq, der, half_width=7.62,
                              desc="Modulo reductor MP1584EN ajustable")


def modulo_mux_barrita():
    """Módulo 74HC4067 "en barrita": orden de pines POR CONFIRMAR con la pieza real (ver docs/pendientes-por-confirmar.md M17)."""
    izq = [(1, "VCC"), (2, "GND"), (3, "S0"), (4, "S1"), (5, "S2"), (6, "S3"), (7, "SIG"), (8, "EN")]
    der = [(9 + i, f"C{i}") for i in range(16)]
    return make_custom_symbol("MUX4067_Modulo", "U", "Modulo 74HC4067 16 canales", izq, der, half_width=7.62,
                              desc="Modulo multiplexor analogico 74HC4067 en barrita (orden de pines por confirmar)")


def tcrt5000():
    # Pines nombrados por función (A, K, C, E); las patillas físicas se confirman al medir la pieza.
    return make_custom_symbol("TCRT5000", "OP", "TCRT5000",
                              [("A", "A", "passive"), ("K", "K", "passive")],
                              [("C", "C", "passive"), ("E", "E", "passive")],
                              half_width=5.08,
                              desc="Sensor reflectivo IR (LED + fototransistor), orificio pasante")


def archivo_biblioteca(simbolos):
    return ("(kicad_symbol_lib (version 20220914) (generator robot_casero_gen)\n"
            + "\n".join("  " + s.replace("\n", "\n  ") for s in simbolos) + "\n)\n")
