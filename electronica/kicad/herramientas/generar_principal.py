#!/usr/bin/env python3
"""Genera el esquemático de la PLACA PRINCIPAL del robot casero.

Lee los pines de ../pines_robot_casero.h (fuente de verdad). No editar el .kicad_sch a mano.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from kicad_gen import Esquematico
import biblioteca_propia as bp

BASE = Path(__file__).resolve().parent.parent
SALIDA = BASE / "principal"

# GPIO del ESP32: restricciones para validar el .h
PROHIBIDOS = set(range(6, 12)) | {1, 3}
SOLO_ENTRADA = set(range(34, 40))
ARRANQUE = {0, 2, 5, 12, 15}
ADC1 = {32, 33, 34, 35, 36, 39}

# Pin del .h -> (nombre de la red, dirección)
SENALES = {
    "PIN_MUX_S0": ("S0", "out"), "PIN_MUX_S1": ("S1", "out"), "PIN_MUX_S2": ("S2", "out"),
    "PIN_MUX_S3": ("S3", "out"), "PIN_MUX_SIG": ("SIG", "adc"), "PIN_EMISORES": ("EMIT_EN", "out"),
    "PIN_AIN1": ("AIN1", "out"), "PIN_AIN2": ("AIN2", "out"), "PIN_BIN1": ("BIN1", "out"),
    "PIN_BIN2": ("BIN2", "out"), "PIN_SLEEP": ("DRV_SLEEP", "out"), "PIN_VENTILADOR": ("FAN_PWM", "out"),
    "PIN_START": ("START", "in"), "PIN_CAL": ("CAL", "in"), "PIN_BATERIA": ("VBAT_SENSE", "adc"),
}


def leer_pines():
    txt = (BASE / "pines_robot_casero.h").read_text()
    pines = {k: int(v) for k, v in re.findall(r"constexpr int (PIN_\w+)\s*=\s*(\d+)\s*;", txt)}
    faltan = set(SENALES) - set(pines)
    if faltan:
        raise SystemExit(f"Faltan pines en pines_robot_casero.h: {sorted(faltan)}")
    usados = {}
    for nom, gpio in pines.items():
        if gpio in usados:
            raise SystemExit(f"GPIO {gpio} repetido: {nom} y {usados[gpio]}")
        usados[gpio] = nom
        if gpio in PROHIBIDOS:
            raise SystemExit(f"{nom}=GPIO{gpio} está prohibido (flash o serie)")
        red, d = SENALES[nom]
        if d in ("out",) and gpio in SOLO_ENTRADA:
            raise SystemExit(f"{nom}=GPIO{gpio} es solo entrada y se usa como salida")
        if d == "adc" and gpio not in ADC1:
            raise SystemExit(f"{nom}=GPIO{gpio} debe ser ADC1")
        if gpio in ARRANQUE:
            raise SystemExit(f"{nom}=GPIO{gpio} es pin de arranque")
    return pines


FP_R = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal"
FP_CD = "Capacitor_THT:C_Disc_D7.5mm_W5.0mm_P7.50mm"                # cerámico: 7 mm entre patas (M23, escalímetro)
FP_CP = "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm"                    # 470 uF: diámetro 8 mm; Alan midió 3 mm entre patas (M23)
FP_H2 = "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"
FP_H8 = "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical"
FP_SW = "Button_Switch_THT:SW_PUSH_6mm"                              # pulsador pequeño 6 x 6 mm (M26)
FP_SW12 = "Button_Switch_THT:SW_PUSH-12mm"                           # pulsador mediano 12 x 12 mm (M26)
FP_D = "robot_casero:D_DO-201AD_P35.56mm_Taladro1.3"               # 1N5822: 3.5 cm entre patas (M24); patas de 1.3 mm
FP_ESP = "robot_casero:ESP32_DevKit_30"
FP_DRV = "robot_casero:Modulo_DRV8833"
FP_MP = "robot_casero:Modulo_MP1584"
FP_PTC = "robot_casero:PTC_Radial_VERIFICAR"


def construir():
    pines = leer_pines()
    gpio_red = {pines[k]: SENALES[k][0] for k in SENALES}

    s = Esquematico(
        "principal", "Robot casero: placa principal (ESP32 + DRV8833 + ventilador)", "A",
        ["Robot casero - Circuit Forge. Rama engineering/robot-casero",
         "Generado por herramientas/generar_principal.py desde pines_robot_casero.h (no editar a mano)",
         "Modulos comerciales: orden de pines y medidas POR VERIFICAR con la pieza real",
         "ERC oficial de KiCad no corrido (KiCad 7 CLI no lo incluye): correrlo en la interfaz"])
    s.usar_propio("robot_casero:ESP32_DevKit_30", bp.esp32_devkit_30())
    s.usar_propio("robot_casero:DRV8833_Modulo", bp.modulo_drv8833())
    s.usar_propio("robot_casero:MP1584_Modulo", bp.modulo_mp1584())
    for lid in ("Device:R", "Device:C", "Device:C_Polarized", "Device:D_Schottky", "Device:Polyfuse",
                "Device:Q_NMOS_GDS", "Switch:SW_Push", "Switch:SW_SPST", "Connector_Generic:Conn_01x02",
                "Connector_Generic:Conn_01x08"):
        s.usar_oficial(lid)

    s.texto("PLACA PRINCIPAL - robot casero (ESP32 DevKit 30 pines, DRV8833, ventilador)", 20, 14, 1.8, True)

    # ------------------------------------------------ Entrada de batería y protección
    s.texto("1. BATERIA, FUSIBLE E INTERRUPTOR", 20, 28, 1.4, True)
    s.pieza("J1", "Connector_Generic:Conn_01x02", "LiPo 2S (JST-RC)", FP_H2, 40.64, 40.64, 0,
            {"1": "VBAT_RAW", "2": "GND"})
    s.pieza("F1", "Device:Polyfuse", "PTC 1.5 A", FP_PTC, 88.9, 40.64, 90, {"1": "VBAT_RAW", "2": "VBAT_F"})
    s.pieza("SW1", "Switch:SW_SPST", "Interruptor", FP_H2, 139.7, 40.64, 0, {"1": "VBAT_F", "2": "VBAT_SW"})
    s.pieza("C1", "Device:C_Polarized", "470u 16V", FP_CP, 190.5, 40.64, 90, {"1": "VBAT_SW", "2": "GND"})

    # ------------------------------------------------ Reguladores
    s.texto("2. REGULADORES: 5 V PARA EL ESP32 Y 6 V FIJOS PARA LOS MOTORES (ajustar con multimetro ANTES de conectar)", 20, 78, 1.4, True)
    s.pieza("U1", "robot_casero:MP1584_Modulo", "MP1584 -> 5.0 V", FP_MP, 63.5, 101.6, 0,
            {"1": "VBAT_SW", "2": "GND", "3": "+5V", "4": "GND"})
    s.pieza("U2", "robot_casero:MP1584_Modulo", "MP1584 -> 6.0 V", FP_MP, 63.5, 139.7, 0,
            {"1": "VBAT_SW", "2": "GND", "3": "+6V_MOT", "4": "GND"})
    s.pieza("C2", "Device:C_Polarized", "470u 16V", FP_CP, 139.7, 139.7, 90, {"1": "+6V_MOT", "2": "GND"})
    s.pieza("D2", "Device:D_Schottky", "1N5822", FP_D, 139.7, 101.6, 180, {"1": "ESP_5V", "2": "+5V"})
    s.texto("D2 evita que el USB del ESP32 devuelva corriente al regulador", 112, 94)

    # ------------------------------------------------ ESP32
    mapa_izq = {1: "+3V3", 2: "GND"}
    mapa_der = {30: "ESP_5V", 29: "GND", 16: "EN"}
    ESP_NOMBRE_GPIO = {n: nm for n, nm in bp.ESP32_IZQ + bp.ESP32_DER}
    redes_esp, nc_esp = {}, []
    for num, nm in bp.ESP32_IZQ + bp.ESP32_DER:
        if num in mapa_izq:
            redes_esp[str(num)] = mapa_izq[num]
        elif num in mapa_der:
            redes_esp[str(num)] = mapa_der[num]
        else:
            m = re.match(r"IO(\d+)", nm)
            g = int(m.group(1)) if m else None
            if g in gpio_red:
                redes_esp[str(num)] = gpio_red[g]
            else:
                nc_esp.append(str(num))
    # IO36 aparece como "IO36_SVP": el regex lo toma como 36
    s.pieza("A1", "robot_casero:ESP32_DevKit_30", "ESP32 DevKit 30", FP_ESP, 241.3, 152.4, 0, redes_esp, nc=nc_esp)
    s.texto("3. ESP32 (el radio WiFi/Bluetooth NO se inicializa: el reglamento lo prohibe)", 195, 100, 1.4, True)

    # Botones
    s.pieza("SW2", "Switch:SW_Push", "START", FP_SW12, 50.8, 190.5, 0, {"1": "START", "2": "GND"})
    s.pieza("SW3", "Switch:SW_Push", "CAL", FP_SW, 50.8, 210.82, 0, {"1": "CAL", "2": "GND"})
    s.pieza("SW4", "Switch:SW_Push", "RESET", FP_SW, 50.8, 231.14, 0, {"1": "EN", "2": "GND"})
    s.texto("4. BOTONES (START solo arranca; CAL calibra a mano)", 20, 180, 1.4, True)

    # Medición de batería
    s.texto("5. MEDICION DE BATERIA (divisor 100k/33k: 8.4 V -> 2.08 V)", 112, 180, 1.4, True)
    s.pieza("R1", "Device:R", "100k", FP_R, 127.0, 195.58, 90, {"1": "VBAT_SW", "2": "VBAT_SENSE"})
    s.pieza("R2", "Device:R", "33k", FP_R, 127.0, 215.9, 90, {"1": "VBAT_SENSE", "2": "GND"})
    s.pieza("C3", "Device:C", "100n", FP_CD, 127.0, 236.22, 90, {"1": "VBAT_SENSE", "2": "GND"})

    # ------------------------------------------------ Driver y motores
    s.texto("6. DRIVER DE MOTORES DRV8833 (alimentado a 6 V fijos)", 330, 100, 1.4, True)
    s.pieza("U3", "robot_casero:DRV8833_Modulo", "DRV8833", FP_DRV, 355.6, 139.7, 0,
            {"4": "+6V_MOT", "3": "GND", "6": "AIN1", "5": "AIN2", "2": "BIN1", "1": "BIN2",
             "7": "DRV_SLEEP", "8": "MOTL_A", "9": "MOTL_B", "10": "MOTR_A", "11": "MOTR_B"},
            nc=("12",))
    s.pieza("R3", "Device:R", "10k", FP_R, 330.2, 190.5, 90, {"1": "DRV_SLEEP", "2": "GND"})
    s.texto("R3 mantiene el driver dormido mientras el ESP32 arranca", 300, 183)
    s.pieza("J2", "Connector_Generic:Conn_01x02", "Motor izquierdo", FP_H2, 330.2, 215.9, 0,
            {"1": "MOTL_A", "2": "MOTL_B"})
    s.pieza("C4", "Device:C", "100n", FP_CD, 375.0, 215.9, 90, {"1": "MOTL_A", "2": "MOTL_B"})
    s.pieza("J3", "Connector_Generic:Conn_01x02", "Motor derecho", FP_H2, 330.2, 236.22, 0,
            {"1": "MOTR_A", "2": "MOTR_B"})
    s.pieza("C5", "Device:C", "100n", FP_CD, 375.0, 236.22, 90, {"1": "MOTR_A", "2": "MOTR_B"})
    s.texto("C4 y C5 van soldados en las terminales de cada motor (quitan ruido)", 300, 247)

    # ------------------------------------------------ Ventilador
    s.texto("7. VENTILADOR (motor DC con escobillas, voltaje y corriente POR DEFINIR)", 195, 196, 1.4, True)
    s.pieza("R4", "Device:R", "100", FP_R, 200.66, 213.36, 90, {"1": "FAN_PWM", "2": "FAN_G"})
    s.pieza("R5", "Device:R", "10k", FP_R, 200.66, 228.6, 90, {"1": "FAN_G", "2": "GND"})
    s.pieza("Q1", "Device:Q_NMOS_GDS", "IRLZ44N", "Package_TO_SOT_THT:TO-220-3_Vertical", 254.0, 226.06, 0,
            {"G": "FAN_G", "D": "FAN_SW", "S": "GND"})
    s.pieza("D1", "Device:D_Schottky", "1N5822", FP_D, 289.56, 205.74, 0, {"1": "VBAT_SW", "2": "FAN_SW"})
    s.pieza("J4", "Connector_Generic:Conn_01x02", "Ventilador", FP_H2, 289.56, 233.68, 0,
            {"1": "VBAT_SW", "2": "FAN_SW"})
    s.texto("D1 protege al MOSFET del pico de voltaje del motor del ventilador", 195, 246)

    # ------------------------------------------------ Barra de sensores
    s.texto("8. HACIA LA PLACA DE SENSORES (8 hilos)", 330, 28, 1.4, True)
    s.pieza("J5", "Connector_Generic:Conn_01x08", "A placa de sensores", FP_H8, 391.16, 38.1, 0,
            {"1": "+3V3", "2": "GND", "3": "S0", "4": "S1", "5": "S2", "6": "S3", "7": "SIG", "8": "EMIT_EN"})

    s.pwr_flag("GND", 20.0, 264.0)
    s.pwr_flag("+3V3", 40.0, 264.0)
    s.pwr_flag("+5V", 60.0, 264.0)

    # Notas
    s.texto("NOTAS: 1) Poner los MP1584 en 5.0 V y 6.0 V con multimetro ANTES de conectar el ESP32 y el driver.", 20, 255)
    s.texto("2) No conectar el USB del ESP32 con los motores encendidos hasta probar el diodo D2.", 20, 261)
    s.texto("3) Corte por bajo voltaje en el firmware: la LiPo 2S no debe bajar de ~6.0 V (3.0 V por celda).", 20, 267)
    return s, pines


if __name__ == "__main__":
    s, pines = construir()
    SALIDA.mkdir(parents=True, exist_ok=True)
    s.escribir(SALIDA / "principal.kicad_sch")
    (SALIDA / "esperado.json").write_text(json.dumps({"conexiones": s.conexiones, "nc": s.nc},
                                                      ensure_ascii=False, indent=1))
    from biblioteca_propia import archivo_biblioteca
    (SALIDA / "robot_casero.kicad_sym").write_text(archivo_biblioteca(
        [bp.esp32_devkit_30(), bp.modulo_drv8833(), bp.modulo_mp1584()]))
    print("OK:", SALIDA / "principal.kicad_sch", f"({len(s.conexiones)} conexiones)")
