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
         "EMIT_K va al transistor Q2 de la placa principal (resta de luz ambiente)"])
    s.usar_propio("robot_casero:TCRT5000", bp.tcrt5000())
    s.usar_oficial("Device:R")
    s.usar_oficial("Device:C")
    s.usar_oficial("Connector_Generic:Conn_01x08")

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

    # El multiplexor y el transistor de emisores ahora están en la placa principal (opción A, 6 nov):
    # esta placa solo lleva sensores, resistencias y un conector de 15 hilos.
    s.pieza("C1", "Device:C", "100n", FP_C, 305.0, 127.0, 90, {"1": "+3V3", "2": "GND"})
    redes = {"1": "+3V3", "2": "GND", "3": "EMIT_K"}
    for i in range(N):
        redes[str(4 + i)] = f"SEN{i + 1}"
    s.pieza("J1", "Connector_Generic:Conn_01x15", "A placa principal",
            "Connector_PinHeader_2.54mm:PinHeader_1x15_P2.54mm_Vertical", 330.2, 160.0, 0, redes)
    s.texto("J1: 1=+3V3  2=GND  3=EMIT_K (catodos de los LED)  4..15=SEN1..SEN12", 290, 135)
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
    (SALIDA / "robot_casero.kicad_sym").write_text(archivo_biblioteca([bp.tcrt5000()]))
    print("OK:", SALIDA / "sensores.kicad_sch", f"({len(s.conexiones)} conexiones)")
