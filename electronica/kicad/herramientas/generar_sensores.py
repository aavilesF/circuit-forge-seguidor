#!/usr/bin/env python3
"""Genera el esquemático de la PLACA DE SENSORES EN CURVA: 12 × TCRT5000 + multiplexor 74HC4067 + interruptor de emisores.

A la placa principal llegan solo 8 hilos (conector J1): +3V3, GND, S0, S1, S2, S3, SIG, EMIT_EN (P15, Alan 11 nov).
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
FP_C = "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm"                    # cerámico: 5.5 mm entre patas (M23); paso estándar 5.0
FP_OP = "robot_casero:TCRT5000_THT"                                    # se crea al medir la pieza


def construir():
    s = Esquematico(
        "sensores", "Placa de sensores: 12 TCRT5000 + 74HC4067 + interruptor de emisores", "A",
        ["Robot casero - Circuit Forge. Rama engineering/robot-casero",
         "Generado por herramientas/generar_sensores.py (no editar a mano)",
         "Todo a 3.3 V. 12 sensores: S0..S3 eligen el canal, SIG va al ADC del ESP32",
         "Q1 (2N2222, E-B-C) une los catodos EMIT_K a GND cuando EMIT_EN = 1 (resta de luz ambiente)"])
    s.usar_propio("robot_casero:TCRT5000", bp.tcrt5000())
    s.usar_oficial("Device:R")
    s.usar_oficial("Device:C")
    s.usar_propio("robot_casero:MUX4067_Modulo", bp.modulo_mux())
    s.usar_oficial("Connector_Generic:Conn_01x08")
    s.usar_oficial("Device:Q_NPN_EBC")

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

    # Multiplexor: 12 canales usados (C0..C11 = SEN1..SEN12), EN a GND (siempre activo)
    redes_mux = {"VCC": "+3V3", "GND": "GND", "EN": "GND", "S0": "S0", "S1": "S1", "S2": "S2", "S3": "S3", "SIG": "SIG"}
    for i in range(N):
        redes_mux[f"C{i}"] = f"SEN{i + 1}"
    s.pieza("U1", "robot_casero:MUX4067_Modulo", "Modulo 74HC4067", "robot_casero:Modulo_MUX4067_VERIFICAR", 200.0, 90.0, 0,
            redes_mux, nc=("C12", "C13", "C14", "C15"))
    s.pieza("C1", "Device:C", "100n", FP_C, 250.0, 60.0, 90, {"1": "+3V3", "2": "GND"})
    # Interruptor de emisores. R26 mantiene apagados los LED si el cable se desconecta o el ESP32 está arrancando
    s.pieza("R25", "Device:R", "330", FP_R, 200.0, 170.0, 90, {"1": "EMIT_EN", "2": "BASE_Q1"})
    s.pieza("R26", "Device:R", "10k", FP_R, 220.0, 185.0, 90, {"1": "BASE_Q1", "2": "GND"})
    s.pieza("Q1", "Device:Q_NPN_EBC", "2N2222 (E-B-C, M25)", "Package_TO_SOT_THT:TO-92_Inline_Wide", 240.0, 170.0, 0,
            {"E": "GND", "B": "BASE_Q1", "C": "EMIT_K"})
    s.texto("Q1: con EMIT_EN = 1 los LED encienden; R26 los apaga si falta la senal", 180, 155)
    s.pieza("J1", "Connector_Generic:Conn_01x08", "A placa principal",
            "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical", 330.2, 160.0, 0,
            {"1": "+3V3", "2": "GND", "3": "S0", "4": "S1", "5": "S2", "6": "S3", "7": "SIG", "8": "EMIT_EN"})
    s.texto("J1: 1=+3V3 2=GND 3=S0 4=S1 5=S2 6=S3 7=SIG 8=EMIT_EN", 290, 135)
    s.pwr_flag("+3V3", 300.0, 215.0)
    s.pwr_flag("GND", 312.0, 215.0)
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
