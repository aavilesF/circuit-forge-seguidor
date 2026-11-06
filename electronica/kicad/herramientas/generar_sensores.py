#!/usr/bin/env python3
"""Genera el esquemático de la PLACA DE SENSORES EN CURVA: 12 × TCRT5000 + multiplexor 74HC4067 + interruptor de emisores.

A la placa principal llegan solo 8 hilos (conector J1): +3V3, GND, S0, S1, S2, S3, SIG, EMIT_EN.
Todo trabaja a 3.3 V para que la salida analógica nunca pase de 3.3 V (límite del ADC del ESP32).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from kicad_gen import Esquematico
import biblioteca_propia as bp

SALIDA = Path(__file__).resolve().parent.parent / "sensores"
N = 12
FP_R = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P2.54mm_Vertical"   # resistencia de 1/4 W parada
FP_C = "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm"                    # VERIFICAR con el cerámico comprado
FP_OP = "robot_casero:TCRT5000_THT"                                    # se crea al medir la pieza


def construir():
    s = Esquematico(
        "sensores", "Placa de sensores TCRT5000 (12 canales)", "A",
        ["Robot casero - Circuit Forge. Rama engineering/robot-casero",
         "Generado por herramientas/generar_sensores.py (no editar a mano)",
         "Todo a 3.3 V. 12 sensores: S0..S3 eligen el canal, SIG va al ADC del ESP32",
         "EMIT_EN enciende los LED infrarrojos para restar la luz ambiente"])
    s.usar_propio("robot_casero:TCRT5000", bp.tcrt5000())
    s.usar_oficial("Device:R")
    s.usar_oficial("Device:C")
    s.usar_oficial("Device:Q_NPN_EBC")
    s.usar_oficial("Connector_Generic:Conn_01x08")
    s.usar_propio("robot_casero:MUX4067_Modulo", bp.modulo_mux())

    s.texto("PLACA DE SENSORES EN CURVA - 12 x TCRT5000, paso 7.5 mm (ver mecanica). Cada fila: LED, sensor y resistencia de carga.",
            20, 12, 1.8, True)
    s.texto("R LED (330 ohm): ~5.6 mA por LED a 3.3 V. R carga (10 kohm): sube la señal del fototransistor a +3V3.",
            20, 18)

    y0, paso = 36.0, 12.7
    for i in range(1, N + 1):
        y = y0 + (i - 1) * paso
        # Resistencia del LED: +3V3 -> ánodo
        s.pieza(f"R{i}", "Device:R", "330", FP_R, 30.48, y, 90, {"1": "+3V3", "2": f"LEDA{i}"})
        # Sensor: ánodo, cátodo común (EMIT_K), colector (SENn), emisor a tierra
        s.pieza(f"OP{i}", "robot_casero:TCRT5000", "TCRT5000", FP_OP, 78.74, y, 0,
                {"A": f"LEDA{i}", "K": "EMIT_K", "C": f"SEN{i}", "E": "GND"})
        # Resistencia de carga del fototransistor
        s.pieza(f"R{N + i}", "Device:R", "10k", FP_R, 127.0, y, 90, {"1": f"SEN{i}", "2": "+3V3"})

    # Multiplexor
    mx, my = 233.68, 119.38
    redes = {"VCC": "+3V3", "GND": "GND", "EN": "GND", "S0": "S0", "S1": "S1", "S2": "S2", "S3": "S3", "SIG": "SIG"}
    for i in range(N):
        redes[f"C{i}"] = f"SEN{i + 1}"
    s.pieza("U1", "robot_casero:MUX4067_Modulo", "Modulo 74HC4067", "robot_casero:Modulo_MUX4067_VERIFICAR", mx, my, 0, redes,
            nc=("C12", "C13", "C14", "C15"))
    s.texto("Modulo 74HC4067: EN a GND = siempre habilitado. Orden de pines por confirmar (M17)", mx - 20, my - 36)

    # Interruptor de emisores: 2N2222 (PN2222A, pines E-B-C), enciende todos los cátodos a la vez
    s.pieza("R25", "Device:R", "330", FP_R, 312.42, 53.34, 90, {"1": "EMIT_EN", "2": "BASE_Q1"})
    s.pieza("Q1", "Device:Q_NPN_EBC", "PN2222A", "Package_TO_SOT_THT:TO-92_Inline_Wide", 383.54, 53.34, 0,
            {"E": "GND", "B": "BASE_Q1", "C": "EMIT_K"})
    s.texto("Interruptor de emisores (resta de luz ambiente)", 320, 36)

    # Desacoplo (100 nF) cerca del multiplexor y del conector
    s.pieza("C1", "Device:C", "100n", FP_C, 305.0, 127.0, 90, {"1": "+3V3", "2": "GND"})
    s.pieza("C2", "Device:C", "100n", FP_C, 355.6, 127.0, 90, {"1": "+3V3", "2": "GND"})

    # Conector hacia la placa principal (8 hilos)
    s.pieza("J1", "Connector_Generic:Conn_01x08", "A placa principal", "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical",
            330.2, 190.5, 0,
            {"1": "+3V3", "2": "GND", "3": "S0", "4": "S1", "5": "S2", "6": "S3", "7": "SIG", "8": "EMIT_EN"})
    s.texto("J1: 1=+3V3  2=GND  3=S0  4=S1  5=S2  6=S3  7=SIG  8=EMIT_EN", 300, 168)
    s.pwr_flag("+3V3", 300.0, 205.0)
    s.pwr_flag("GND", 312.0, 205.0)
    return s


if __name__ == "__main__":
    s = construir()
    SALIDA.mkdir(parents=True, exist_ok=True)
    s.escribir(SALIDA / "sensores.kicad_sch")
    import json
    (SALIDA / "esperado.json").write_text(json.dumps(
        {"conexiones": s.conexiones, "nc": s.nc}, ensure_ascii=False, indent=1))
    from biblioteca_propia import archivo_biblioteca
    (SALIDA / "robot_casero.kicad_sym").write_text(archivo_biblioteca([bp.tcrt5000(), bp.modulo_mux()]))
    print("OK:", SALIDA / "sensores.kicad_sch", f"({len(s.conexiones)} conexiones)")
