"""Símbolos propios del robot casero (módulos que no existen en las bibliotecas oficiales de KiCad).

IMPORTANTE: son símbolos FUNCIONALES. El orden y los nombres de los pines de los módulos comerciales
(ESP32 DevKit, DRV8833, MP1584) cambian de un fabricante a otro. Hay que compararlos con la pieza real
antes de fabricar (ver electronica/kicad/NOTAS.md, sección "Por verificar").
"""
from kicad_gen import make_custom_symbol

# --- ESP32 DevKit de 38 pines (disposición tipo ESP32-DevKitC: 19 pines por lado). VERIFICAR con la placa real.
# ESP32 DevKit de 30 pines (clon), con el USB-C arriba. Orden leído por Alan de la serigrafía (5 nov 2026, M03).
# Izquierda, de arriba (USB) hacia abajo: pines 1 a 15. Derecha: el pin 30 (VIN) queda arriba, el 16 (EN) abajo.
ESP32_IZQ = [  # (numero físico, nombre)
    (1, "3V3"), (2, "GND"), (3, "IO15"), (4, "IO2"), (5, "IO4"), (6, "IO16"), (7, "IO17"), (8, "IO5"),
    (9, "IO18"), (10, "IO19"), (11, "IO21"), (12, "RXD0"), (13, "TXD0"), (14, "IO22"), (15, "IO23")]
ESP32_DER = [
    (30, "VIN"), (29, "GND"), (28, "IO13"), (27, "IO12"), (26, "IO14"), (25, "IO27"), (24, "IO26"), (23, "IO25"),
    (22, "IO33"), (21, "IO32"), (20, "IO35"), (19, "IO34"), (18, "IO39_VN"), (17, "IO36_VP"), (16, "EN")]


def esp32_devkit_30():
    return make_custom_symbol("ESP32_DevKit_30", "A", "ESP32 DevKit 30 pines",
                              [(n, nm, "bidirectional") for n, nm in ESP32_IZQ],
                              [(n, nm, "bidirectional") for n, nm in ESP32_DER],
                              half_width=10.16,
                              desc="ESP32 DevKit de 30 pines (clon con USB-C); orden de pines leido de la serigrafia (M03)")


def modulo_drv8833():
    """Módulo DRV8833 comprado (M10). Serigrafía: EEP = nSLEEP, ULT = nFAULT, VCC = VM (voltaje de motores)."""
    izq = [(1, "IN4"), (2, "IN3"), (3, "GND"), (4, "VCC"), (5, "IN2"), (6, "IN1")]
    der = [(7, "EEP_nSLEEP"), (8, "OUT1"), (9, "OUT2"), (10, "OUT3"), (11, "OUT4"), (12, "ULT_nFAULT")]
    return make_custom_symbol("DRV8833_Modulo", "U", "Modulo DRV8833", izq, der, half_width=7.62,
                              desc="Modulo puente H doble DRV8833 (orden de pines leido del modulo comprado, M10)")


def modulo_mp1584():
    # Orden según la serigrafía del módulo comprado (M13): OUT-, OUT+ a un lado; IN-, IN+ al otro.
    izq = [(1, "IN+"), (2, "IN-")]
    der = [(3, "OUT+"), (4, "OUT-")]
    return make_custom_symbol("MP1584_Modulo", "U", "Modulo MP1584EN", izq, der, half_width=7.62,
                              desc="Modulo reductor MP1584EN ajustable")


def modulo_mux():
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
