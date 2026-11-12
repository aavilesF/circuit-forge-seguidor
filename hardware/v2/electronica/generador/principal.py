#!/usr/bin/env python3
"""V2 · PCB principal (plan B de calendario): módulo WeAct STM32G474CEU6 Core Board en zócalos 2 × 12, alimentación,
2 × DRV8874, IMU ISM330DHCX, 2 × LPS22DF (cámara y ambiente), conexiones al ESC, a la barra de sensores y a los motores,
START/CAL/RESET, 4 LED y zumbador piezoeléctrico.

Esta entrega genera el ESQUEMÁTICO (y la biblioteca propia: símbolos del módulo y del DRV8874, huella de los zócalos del
módulo). La PCB se coloca y enruta en la siguiente entrega; las posiciones de este archivo son la colocación inicial que
usa el CAD mecánico (marco del robot, mm).

Asignación de pines del módulo: cada función eligió un pin con el periférico necesario (datos de pines de ST,
STM32_open_pin_data, STM32G474C(B-C-E)Ux) y fuera de lo que el módulo ya usa (USB PA11/PA12, cristal, SWD, flash QSPI
deshabilitada por su /CS en PB11). Ver docs/v2/FASE3_ENTREGA1.md.
Uso: python3 hardware/v2/electronica/generador/principal.py"""
from __future__ import annotations

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun as K  # noqa: E402
from sexpr import Sym  # noqa: E402
import sexpr  # noqa: E402

HA, HC, HM = "alimentacion", "control", "motores"
D = K.Diseno("principal", "Speed Follower V2 — PCB principal",
             [(HA, "Alimentación y protecciones"), (HC, "MCU (módulo WeAct), sensores e interfaz"),
              (HM, "Puentes H, motores, ESC y barra de sensores")],
             papel={HA: "A3", HC: "A2", HM: "A3"},
             banderas={"VBAT_IN": HA, "VBAT_SW": HA, "+3V3": HA, "GND": HA, "VIN_BUCK": HA})

# ------------------------------------------------------------------------------------------------ módulo WeAct
# Cabeceras del módulo (esquemático WeAct STM32G474 Core Board V1.0): P1 y P2, 2 × 12 a 2.54 mm.
P1 = ["VCC", "VCC", "GND", "GND", "PB12", "PB13", "PB14", "PB15", "PC6", "PA8", "PA9", "PA10", "PA11", "PA12", "PA15",
      "PC10", "PC11", "PB3", "PB4", "PB5", "PB6", "PB7", "PB8", "PB9"]
P2 = ["3V3", "3V3", "GND", "GND", "PB10", "PB11", "PB2", "VREF+", "PB0", "PB1", "PA7", "PC4", "PA5", "PA6", "PA3", "PA4",
      "PA1", "PA2", "NRST", "PA0", "PC14", "PC15", "VB", "PC13"]
FUNCION = {   # pin del MCU -> red
    "PA0": "SENS_A", "PA1": "SENS_B", "PA2": "VBAT_MED", "PA3": "IPROPI_I", "PB2": "IPROPI_D",
    "PA4": "EMIT", "PB13": "MUX_S0", "PB14": "MUX_S1", "PB15": "MUX_S2",
    "PB6": "ENC_I_A", "PB7": "ENC_I_B", "PA15": "ENC_D_A", "PB3": "ENC_D_B",
    "PA10": "EN_I", "PA9": "EN_D", "PC10": "PH_I", "PB5": "PH_D", "PB4": "DRV_nSLEEP", "PB12": "DRV_nFAULT",
    "PA8": "I2C_SCL", "PC11": "I2C_SDA", "PB9": "ESC_SEN", "PB8": "ZUMB",
    "PC4": "BTN_START", "PA5": "BTN_CAL", "PB0": "LED_VERDE", "PB1": "LED_AMARILLO", "PB10": "LED_ROJO",
    "NRST": "NRST", "3V3": "+3V3", "GND": "GND"}
NOTA_PIN = {"PA0": "ADC1_IN1", "PA1": "ADC2_IN2", "PA2": "ADC1_IN3", "PA3": "ADC1_IN4", "PB2": "ADC2_IN12",
            "PB6": "TIM4_CH1", "PB7": "TIM4_CH2", "PA15": "TIM2_CH1", "PB3": "TIM2_CH2", "PA10": "TIM1_CH3",
            "PA9": "TIM1_CH2", "PA8": "I2C3_SCL", "PC11": "I2C3_SDA", "PB9": "TIM17_CH1 (DShot/PWM)",
            "PB8": "TIM16_CH1 (BOOT0 al reset)"}
pines_mod, nc_mod = {}, []
for pref, lista in (("A", P1), ("B", P2)):
    for n, nom in enumerate(lista, 1):
        num = f"{pref}{n}"
        if nom in FUNCION:
            pines_mod[num] = FUNCION[nom]
        else:
            nc_mod.append(num)
D.simbolos_propios.append(K.simbolo_rect(
    "WeAct_STM32G474_CoreBoard",
    [(f"B{n}", f"{nom}" + (f" {NOTA_PIN[nom]}" if nom in NOTA_PIN else "")) for n, nom in enumerate(P2, 1)],
    [(f"A{n}", f"{nom}" + (f" {NOTA_PIN[nom]}" if nom in NOTA_PIN else "")) for n, nom in enumerate(P1, 1)],
    ref="A", descr="WeAct Studio STM32G474CEU6 Core Board V1.0 (36.28 × 28.14 mm) en 2 zócalos 2 × 12; P1 = pads A, P2 = pads B",
    huella=f"{K.LIB_PROPIA}:WeAct_STM32G474_CoreBoard_Zocalo", ancho=40.64,
    tipo_por_nombre=lambda n: "power_in" if n in ("3V3", "GND") else ("no_connect" if n == "VCC" else "passive")))
D.P(ref="A1", lib_id=f"{K.LIB_PROPIA}:WeAct_STM32G474_CoreBoard", valor="WeAct STM32G474CEU6",
    huella=f"{K.LIB_PROPIA}:WeAct_STM32G474_CoreBoard_Zocalo", fabricante="WeAct Studio",
    mpn="STM32G474CEU6 Core Board V1.0", descripcion="Módulo MCU STM32G474CEU6 (170 MHz, 512 KB, 128 KB) con USB-C, cristal de 8 MHz, BOOT0 y RESET",
    hoja=HC, pines=pines_mod, nc=tuple(nc_mod), x=-23.86, y=0.0, rot=0, datasheet=K.DS["WEACT"],
    extra=dict(nota="Se monta en 2 zócalos 2 × 12 (ver J? ZÓCALO); VCC del módulo sin conectar: el módulo toma 3.3 V de la placa"))
for k, y in enumerate((11.43, -11.43)):
    D.P(ref=f"J{10 + k}", lib_id="Mechanical:MountingHole", valor="Zócalo 2×12", huella="",
        fabricante="genérico", mpn="Zócalo hembra 2×12, paso 2.54 mm, 8.5 mm de alto (número de parte por elegir)",
        descripcion="Zócalo hembra 2 × 12, 2.54 mm, para el módulo (se suelda en la huella del módulo)", hoja=HC, pines={},
        x=-23.86, y=y, en_bom=True, extra=dict(solo_bom=True))

# ------------------------------------------------------------------------------------------------ alimentación
D.P(ref="J1", lib_id="Connector_Generic:Conn_01x02", valor="XT30UPB-M", huella="Connector_AMASS:AMASS_XT30UPB-M_1x02_P5.0mm_Vertical",
    fabricante="Changzhou Amass Electronics", mpn="XT30UPB-M", descripcion="Conector de batería XT30 macho vertical para PCB, 15 A (pin 1 −, pin 2 +)",
    hoja=HA, pines={"1": "GND", "2": "VBAT_IN"}, x=-36.0, y=-29.0, rot=90, datasheet=K.DS["XT30UPB"])
D.P(ref="F1", lib_id="Device:Fuse", valor="10A", huella="Fuse:Fuse_Blade_Mini_directSolder", fabricante="Littelfuse",
    mpn="0297010.WXNV", descripcion="Fusible de cuchilla MINI 297, 10 A 32 V, acción rápida (soldado)", hoja=HA,
    pines={"1": "VBAT_IN", "2": "VBAT_F"}, x=-26.0, y=-30.5, rot=0, datasheet=K.DS["0297"])
for ref, d, y, desc in (("Q1", "VBAT_F", -24.0, "protección contra inversión"), ("Q2", "VBAT_SW", -18.5, "interruptor de encendido")):
    D.P(ref=ref, lib_id="Transistor_FET:DMP3013SFV", valor="DMP3013SFV", huella="Package_SON:Diodes_PowerDI3333-8",
        fabricante="Diodes Incorporated", mpn="DMP3013SFV-7",
        descripcion=f"MOSFET P −30 V −12 A 9.5 mΩ, VGS ±25 V, PowerDI3333-8 ({desc})", hoja=HA,
        pines={"1": "VBAT_S", "2": "VBAT_S", "3": "VBAT_S", "4": "PFET_G", "5": d}, x=-17.0, y=y, rot=0,
        datasheet=K.DS["DMP3013SFV"])
D.R("R1", "100k", "VBAT_S", "PFET_G", HA, x=-13.0, y=-21.0, rot=90)
D.R("R2", "10k", "PFET_G", "SW_COM", HA, x=-11.5, y=-21.0, rot=90)
D.P(ref="SW1", lib_id="Switch:SW_SPDT", valor="ENCENDIDO", huella="Button_Switch_THT:SW_Slide_SPDT_Angled_CK_OS102011MA1Q",
    fabricante="C&K", mpn="OS102011MA1QN1", descripcion="Interruptor deslizante SPDT de ángulo recto, 100 mA 12 V (solo conmuta la compuerta)",
    hoja=HA, pines={"1": "GND", "2": "SW_COM", "3": "SW_OFF"}, x=-40.0, y=-19.0, rot=90, datasheet=K.DS["OS102011"], nc=("3",))
D.P(ref="D1", lib_id="Diode:SMAJ9.0A", valor="SMAJ9.0A", huella="Diode_SMD:D_SMA", fabricante="Littelfuse", mpn="SMAJ9.0A",
    descripcion="TVS unidireccional 400 W, 9.0 V de trabajo (DO-214AC); cátodo (banda) a VBAT_SW", hoja=HA,
    pines={"1": "VBAT_SW", "2": "GND"}, x=-10.0, y=-31.0, rot=0, datasheet=K.DS["SMAJ"])
D.C("C1", "22u", "VBAT_SW", "GND", HA, enc="0805", x=-6.0, y=-33.0, rot=90)
D.C("C2", "22u", "VBAT_SW", "GND", HA, enc="0805", x=-4.0, y=-33.0, rot=90)
D.R("R3", "100k", "VBAT_SW", "VBAT_MED", HA, x=-8.0, y=-14.5, rot=0)
D.R("R4", "33k", "VBAT_MED", "GND", HA, x=-8.0, y=-13.0, rot=0)
D.C("C3", "100n", "VBAT_MED", "GND", HA, x=-8.0, y=-11.5, rot=0)
D.P(ref="D2", lib_id="Diode:MBR0540", valor="MBR0540", huella="Diode_SMD:D_SOD-123", fabricante="onsemi", mpn="MBR0540T1G",
    descripcion="Schottky 40 V 0.5 A SOD-123: evita que el 3.3 V del USB alimente VBAT_SW a través del reductor", hoja=HA,
    pines={"1": "VIN_BUCK", "2": "VBAT_SW"}, x=-6.0, y=-27.5, rot=90, datasheet=K.DS["MBR0540"])
D.P(ref="U1", lib_id="Regulator_Switching:TPS563200", valor="TPS563200", huella="Package_TO_SOT_SMD:SOT-23-6",
    fabricante="Texas Instruments", mpn="TPS563200DDCR", descripcion="Convertidor reductor síncrono 4.5-17 V, 3 A, 650 kHz (SOT-23-6)",
    hoja=HA, pines={"1": "GND", "2": "BUCK_SW", "3": "VIN_BUCK", "4": "BUCK_FB", "5": "BUCK_EN", "6": "BUCK_BST"},
    x=-6.0, y=-22.0, rot=0, datasheet=K.DS["TPS563200"])
D.C("C4", "10u", "VIN_BUCK", "GND", HA, enc="0805", x=-9.5, y=-24.5, rot=90)
D.C("C5", "100n", "VIN_BUCK", "GND", HA, x=-8.0, y=-24.5, rot=90)
D.R("R5", "100k", "VIN_BUCK", "BUCK_EN", HA, x=-8.5, y=-20.0, rot=0)
D.C("C6", "100n", "BUCK_BST", "BUCK_SW", HA, x=-3.5, y=-24.5, rot=0)
D.P(ref="L1", lib_id="Device:L", valor="2.2µH", huella="Inductor_SMD:L_Wuerth_MAPI-4030", fabricante="Würth Elektronik",
    mpn="74438357022", descripcion="Inductor blindado WE-MAPI 4030, 2.2 µH, IR 7.1 A, Isat 9.2 A, 26 mΩ", hoja=HA,
    pines={"1": "BUCK_SW", "2": "+3V3"}, x=-1.0, y=-20.0, rot=0, datasheet=K.DS["MAPI"])
D.R("R6", "33.2k", "+3V3", "BUCK_FB", HA, x=-3.5, y=-18.0, rot=0)
D.R("R7", "10k", "BUCK_FB", "GND", HA, x=-3.5, y=-16.8, rot=0)
D.C("C7", "22u", "+3V3", "GND", HA, enc="0805", x=2.0, y=-17.0, rot=90)
D.C("C8", "22u", "+3V3", "GND", HA, enc="0805", x=4.0, y=-17.0, rot=90)
D.P(ref="D3", lib_id="Device:LED", valor="PWR", huella="LED_SMD:LED_0603_1608Metric", fabricante="Kingbright", mpn="APT1608SGC",
    descripcion="LED verde 0603 (3.3 V presente)", hoja=HA, pines={"1": "GND", "2": "LED_PWR_A"}, x=-22.0, y=33.5, rot=0,
    datasheet=K.DS["APT1608"])
D.R("R8", "1k", "+3V3", "LED_PWR_A", HA, x=-22.0, y=31.8, rot=0)
for k, (red, x, y) in enumerate((("+3V3", 1.0, -9.0), ("GND", 1.0, -6.5), ("VBAT_SW", -2.0, -33.5), ("GND", 0.5, -33.5))):
    D.P(ref=f"TP{k + 1}", lib_id="Connector:TestPoint", valor=red, huella="TestPoint:TestPoint_Pad_D1.0mm", fabricante="—",
        mpn="—", descripcion="Punto de prueba", hoja=HA, pines={"1": red}, x=x, y=y, en_bom=False)

# ------------------------------------------------------------------------------------------------ control
# IMU (I2C 0x6A con SA0 a GND) y presión: U3 dentro de la chimenea a la cámara (cara inferior, SA0 = 1 -> 0x5D),
# U4 ambiente (cara superior, SA0 = 0 -> 0x5C). CS a VDDIO: modo I2C.
D.P(ref="U2", lib_id="Sensor_Motion:ISM330DHCX", valor="ISM330DHCXTR", huella="Package_LGA:LGA-14_3x2.5mm_P0.5mm_LayoutBorder3x4y",
    fabricante="STMicroelectronics", mpn="ISM330DHCXTR", descripcion="IMU 6 ejes: giroscopio ±125-4000 dps, acelerómetro ±2-16 g, I2C/SPI, LGA-14L",
    hoja=HC, pines={"1": "IMU_SA0", "2": "IMU_AUX", "3": "IMU_AUX", "5": "+3V3", "6": "GND", "7": "GND", "8": "+3V3", "12": "+3V3",
                    "13": "I2C_SCL", "14": "I2C_SDA"}, nc=("4", "9", "10", "11"), x=-2.0, y=2.0, rot=0, datasheet=K.DS["ISM330DHCX"])
D.C("C9", "100n", "+3V3", "GND", HC, x=-2.0, y=4.5, rot=0)
D.R("R29", "10k", "IMU_SA0", "GND", HC, x=-5.0, y=2.0, rot=90)      # SA0 = 0 -> dirección 0x6A
D.R("R30", "10k", "IMU_AUX", "GND", HC, x=-6.3, y=2.0, rot=90)      # bus auxiliar (SDx, SCx) sin uso, a GND
D.C("C10", "100n", "+3V3", "GND", HC, x=-2.0, y=-0.5, rot=0)
for ref, sa0, lado, x, y, desc in (("U3", "+3V3", "B", -20.0, 22.0, "presión de la CÁMARA (cara inferior, sobre la chimenea; 0x5D)"),
                                   ("U4", "GND", "F", 2.5, 6.0, "presión AMBIENTE (cara superior; 0x5C)")):
    D.P(ref=ref, lib_id="Sensor_Pressure:LPS22DF", valor="LPS22DFTR", huella="Package_LGA:ST_HLGA-10_2x2mm_P0.5mm_LayoutBorder3x2y",
        fabricante="STMicroelectronics", mpn="LPS22DFTR", descripcion=f"Barómetro 260-1260 hPa, 200 Hz, I2C: {desc}", hoja=HC,
        pines={"1": "+3V3", "2": "I2C_SCL", "3": "GND", "4": "I2C_SDA", "5": sa0, "6": "+3V3", "8": "GND", "9": "GND", "10": "+3V3"},
        nc=("7",), x=x, y=y, rot=0, lado=lado, datasheet=K.DS["LPS22DF"])
D.C("C11", "100n", "+3V3", "GND", HC, x=-20.0, y=27.5, rot=0, lado="B")   # fuera del empaque de la chimenea
D.C("C12", "100n", "+3V3", "GND", HC, x=4.5, y=6.0, rot=90)
D.R("R9", "2.2k", "+3V3", "I2C_SCL", HC, x=0.5, y=9.5, rot=0)
D.R("R10", "2.2k", "+3V3", "I2C_SDA", HC, x=0.5, y=11.0, rot=0)
# Botones (activos en bajo, con antirrebote RC) y RESET al NRST del módulo
for ref, nom, red, x, y in (("SW2", "START", "BTN_START", -38.5, 24.0), ("SW3", "CAL", "BTN_CAL", -38.5, 31.5)):
    D.P(ref=ref, lib_id="Switch:SW_Push", valor=nom, huella="Button_Switch_SMD:SW_SPST_Omron_B3FS-100xP", fabricante="Omron",
        mpn="B3FS-1000P", descripcion=f"Pulsador táctil SMD 6 × 6 × 3.1 mm ({nom})", hoja=HC, pines={"1": red, "2": "GND"},
        x=x, y=y, rot=0, datasheet=K.DS["B3FS"])
D.R("R11", "10k", "+3V3", "BTN_START", HC, x=-33.0, y=21.0, rot=90)
D.C("C13", "100n", "BTN_START", "GND", HC, x=-31.5, y=21.0, rot=90)
D.R("R12", "10k", "+3V3", "BTN_CAL", HC, x=-33.0, y=28.5, rot=90)
D.C("C14", "100n", "BTN_CAL", "GND", HC, x=-31.5, y=28.5, rot=90)
D.P(ref="SW4", lib_id="Switch:SW_Push", valor="RESET", huella="Button_Switch_SMD:SW_SPST_B3U-1000P", fabricante="Omron",
    mpn="B3U-1000P", descripcion="Pulsador táctil SMD 3.0 × 2.5 mm (RESET del MCU)", hoja=HC, pines={"1": "NRST", "2": "GND"},
    x=-39.5, y=17.0, rot=0, datasheet=K.DS["B3U"])
# LED de estado (activos en alto)
for k, (ref, nom, mpn, red, desc) in enumerate((("D4", "VERDE", "APT1608SGC", "LED_VERDE", "verde"),
                                                ("D5", "AMARILLO", "APT1608YC", "LED_AMARILLO", "amarillo"),
                                                ("D6", "ROJO", "APT1608EC", "LED_ROJO", "rojo"))):
    x = -34.0 + 4.0 * k
    D.P(ref=ref, lib_id="Device:LED", valor=nom, huella="LED_SMD:LED_0603_1608Metric", fabricante="Kingbright", mpn=mpn,
        descripcion=f"LED {desc} 0603 de estado", hoja=HC, pines={"1": "GND", "2": f"{red}_A"}, x=x, y=34.0, rot=0,
        datasheet=K.DS["APT1608"])
    D.R(f"R{13 + k}", "1k", red, f"{red}_A", HC, x=x, y=32.3, rot=0)
# Zumbador piezoeléctrico con excitación externa: VBAT_SW por 2.2 kΩ, el MOSFET lo descarga (onda cuadrada de 0 a VBAT)
D.P(ref="LS1", lib_id="Device:Buzzer", valor="PKLCS1212E4001", huella="Buzzer_Beeper:Buzzer_Murata_PKLCS1212E",
    fabricante="Murata", mpn="PKLCS1212E4001-R1", descripcion="Transductor piezoeléctrico SMD 12 × 12 mm, 4 kHz, excitación externa",
    hoja=HC, pines={"1": "ZUMB_D", "2": "GND"}, x=-13.0, y=27.5, rot=0, datasheet=K.DS["PKLCS1212E"])
D.P(ref="Q3", lib_id="Transistor_FET:AO3400A", valor="AO3400A", huella="Package_TO_SOT_SMD:SOT-23",
    fabricante="Alpha & Omega Semiconductor", mpn="AO3400A", descripcion="MOSFET N 30 V SOT-23 (zumbador)", hoja=HC,
    pines={"1": "ZUMB_G", "2": "GND", "3": "ZUMB_D"}, x=-5.0, y=27.0, rot=0, datasheet=K.DS["AO3400A"])
D.R("R16", "2.2k", "VBAT_SW", "ZUMB_D", HC, x=-5.0, y=30.0, rot=0)
D.R("R17", "100", "ZUMB", "ZUMB_G", HC, x=-5.0, y=24.5, rot=0)
D.R("R18", "100k", "ZUMB_G", "GND", HC, x=-3.0, y=24.5, rot=90)

# ------------------------------------------------------------------------------------------------ motores, ESC, barra
D.simbolos_propios.append(K.simbolo_rect(
    "DRV8874PWPR",
    [("1", "EN/IN1"), ("2", "PH/IN2"), ("3", "nSLEEP"), ("4", "nFAULT"), ("5", "VREF"), ("6", "IPROPI"), ("7", "IMODE"),
     ("16", "PMODE")],
    [("11", "VM"), ("12", "VCP"), ("13", "CPH"), ("14", "CPL"), ("8", "OUT1"), ("10", "OUT2"), ("9", "PGND"), ("15", "GND"),
     ("17", "PAD")],
    ref="U", descr="TI DRV8874 puente H 4.5-37 V, 6 A pico, IPROPI (HTSSOP-16 PWP). Pines: hoja de datos SLVSF66A §5",
    huella="Package_SO:HTSSOP-16-1EP_4.4x5mm_P0.65mm_EP3.4x5mm_Mask2.46x2.31mm", ancho=17.78,
    tipo_por_nombre=lambda n: {"VM": "power_in", "GND": "power_in", "PGND": "power_in", "PAD": "passive",
                               "nFAULT": "open_collector", "IPROPI": "output", "OUT1": "output", "OUT2": "output",
                               "VCP": "passive", "CPH": "passive", "CPL": "passive"}.get(n, "input")))
for lado, ref, x, y, sgn in (("I", "U5", 1.0, 20.0, 1), ("D", "U6", 1.0, -10.5, -1)):
    n0 = 19 if lado == "I" else 21
    D.P(ref=ref, lib_id=f"{K.LIB_PROPIA}:DRV8874PWPR", valor="DRV8874PWPR",
        huella="Package_SO:HTSSOP-16-1EP_4.4x5mm_P0.65mm_EP3.4x5mm_Mask2.46x2.31mm", fabricante="Texas Instruments",
        mpn="DRV8874PWPR", descripcion=f"Puente H del motor {'izquierdo' if lado == 'I' else 'derecho'} (PH/EN, 6 A pico, IPROPI)",
        hoja=HM, pines={"1": f"EN_{lado}", "2": f"PH_{lado}", "3": "DRV_nSLEEP", "4": "DRV_nFAULT", "5": "DRV_VREF",
                        "6": f"IPROPI_{lado}", "7": f"IMODE_{lado}", "16": "GND", "11": "VBAT_SW", "12": f"VCP_{lado}",
                        "13": f"CPH_{lado}", "14": f"CPL_{lado}", "8": f"MOT_{lado}_1", "10": f"MOT_{lado}_2", "9": "GND",
                        "15": "GND", "17": "GND"}, x=x, y=y, rot=0, datasheet=K.DS["DRV8874"])
    D.C(f"C{15 + 4 * (lado == 'D')}", "100n", "VBAT_SW", "GND", HM, x=x + 3.5, y=y + 2.5 * sgn, rot=90)
    D.C(f"C{16 + 4 * (lado == 'D')}", "22u", "VBAT_SW", "GND", HM, enc="0805", x=x + 5.0, y=y + 2.5 * sgn, rot=90)
    D.C(f"C{17 + 4 * (lado == 'D')}", "100n", f"VCP_{lado}", "VBAT_SW", HM, x=x - 3.5, y=y + 2.5 * sgn, rot=90)
    D.C(f"C{18 + 4 * (lado == 'D')}", "22n", f"CPH_{lado}", f"CPL_{lado}", HM, x=x - 3.5, y=y - 2.5 * sgn, rot=90)
    D.R(f"R{n0}", "1.5k", f"IPROPI_{lado}", "GND", HM, x=x + 3.5, y=y - 2.5 * sgn, rot=90)
    D.R(f"R{n0 + 1}", "0", f"IMODE_{lado}", "GND", HM, x=x + 5.0, y=y - 2.5 * sgn, rot=90)
    jref = "J3" if lado == "I" else "J4"
    D.P(ref=jref, lib_id="Connector_Generic_MountingPin:Conn_01x06_MountingPin", valor=f"MOTOR_{lado}",
        huella="Connector_JST:JST_SH_BM06B-SRSS-TB_1x06-1MP_P1.00mm_Vertical", fabricante="JST", mpn="BM06B-SRSS-TB",
        descripcion=f"JST SH 6 vías: motor y encoder {'izquierdo' if lado == 'I' else 'derecho'} (Pololu #5183; cable JST SH 6 vías)",
        hoja=HM, pines={"1": "GND", "2": f"ENC_{lado}_B", "3": f"ENC_{lado}_A", "4": "+3V3", "5": f"MOT_{lado}_2",
                        "6": f"MOT_{lado}_1", "MP": "GND"}, x=4.5, y=y + 6.5 * sgn, rot=90, datasheet=K.DS["BM0xB"])
    for j, ab in enumerate("AB"):
        D.C(f"C{24 + j + 2 * (lado == 'D') + 7}", "1n", f"ENC_{lado}_{ab}", "GND", HM, x=0.0 + 1.3 * j, y=y + 6.5 * sgn, rot=90)
D.R("R23", "10k", "+3V3", "DRV_nFAULT", HM, x=-2.5, y=14.5, rot=90)
D.R("R24", "100k", "DRV_nSLEEP", "GND", HM, x=-4.0, y=14.5, rot=90)
D.R("R25", "10k", "+3V3", "DRV_VREF", HM, x=-2.5, y=12.0, rot=90)
D.R("R26", "4.7k", "DRV_VREF", "GND", HM, x=-4.0, y=12.0, rot=90)   # ITRIP ≈ 1.56 A (Fase 3.5, revisión térmica)
D.C("C23", "100n", "DRV_VREF", "GND", HM, x=-5.5, y=12.0, rot=90)
# ESC comercial (módulo): potencia por 2 hilos soldados, señal por cabecera de servo (S, +, −) con el + sin conectar
D.P(ref="J5", lib_id="Connector_Generic:Conn_01x02", valor="ESC_POT", huella="Connector_Wire:SolderWire-0.5sqmm_1x02_P4.6mm_D0.9mm_OD2.1mm",
    fabricante="—", mpn="—", descripcion="Pads para soldar los cables de potencia del ESC (0.5 mm²): 1 = +VBAT, 2 = GND", hoja=HM,
    pines={"1": "VBAT_SW", "2": "GND"}, x=-25.0, y=-24.0, rot=0, en_bom=False)
D.P(ref="J6", lib_id="Connector_Generic:Conn_01x03", valor="ESC_SEÑAL", huella="Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
    fabricante="genérico", mpn="Cabecera macho 1×3, paso 2.54 mm (número de parte por elegir)", descripcion="Cabecera de servo para la señal del ESC: 1 = señal, 2 = sin conexión, 3 = GND",
    hoja=HM, pines={"1": "ESC_SEN_C", "3": "GND"}, nc=("2",), x=-33.0, y=-16.0, rot=0)
D.R("R27", "100", "ESC_SEN", "ESC_SEN_C", HM, x=-29.5, y=-16.0, rot=0)
D.R("R28", "10k", "ESC_SEN_C", "GND", HM, x=-29.5, y=-17.5, rot=0)
# Barra de sensores: mismo orden de pines que J1 de la barra
D.P(ref="J2", lib_id="Connector_Generic_MountingPin:Conn_01x08_MountingPin", valor="SENSORES",
    huella="Connector_JST:JST_SH_BM08B-SRSS-TB_1x08-1MP_P1.00mm_Vertical", fabricante="JST", mpn="BM08B-SRSS-TB",
    descripcion="JST SH 8 vías a la barra de sensores (cable 1:1)", hoja=HM,
    pines={"1": "+3V3", "2": "EMIT", "3": "MUX_S0", "4": "MUX_S1", "5": "MUX_S2", "6": "SENS_A", "7": "SENS_B", "8": "GND",
           "MP": "GND"}, x=4.5, y=30.0, rot=90, datasheet=K.DS["BM0xB"])
D.C("C35", "1n", "SENS_A", "GND", HM, x=0.5, y=31.5, rot=90)
D.C("C36", "1n", "SENS_B", "GND", HM, x=1.8, y=31.5, rot=90)
for k, (x, y) in enumerate(((-28.0, 30.0), (-28.0, -30.0), (0.0, 27.0), (0.0, -27.0))):
    D.P(ref=f"H{k + 1}", lib_id="Mechanical:MountingHole", valor="M2", huella="MountingHole:MountingHole_2.2mm_M2",
        fabricante="—", mpn="—", descripcion="Agujero M2 de fijación al chasis", hoja=HM, pines={}, x=x, y=y, en_bom=False)

CONTORNO = (-42.0, 6.5, -35.0, 35.0)   # x_min, x_max, y_min, y_max (marco del robot)

# ------------------------------------------------------------------------------------------------ colocación de la PCB
# (x, y, rot) en el marco del robot (rot antihoraria vista desde arriba); "B" = cara inferior. Esquina trasera derecha:
# alimentación (XT30, fusible, MOSFET, interruptor, ESC); trasera izquierda: START, CAL, RESET, LED; franja delantera:
# puentes H, conectores de motor y de la barra, IMU y barómetro ambiente; bajo el módulo: divisor de batería y puntos de prueba.
COLOC = {
    # alimentación (esquina trasera derecha): XT30 -> fusible -> 2 PMOS espalda con espalda -> VBAT_SW (TVS, capacitores, ESC)
    "J1": (-38.8, -31.6, 0), "F1": (-22.4, -32.6, 0), "Q1": (-9.2, -32.6, 180), "Q2": (-4.6, -32.6, 0),
    "R1": (-8.2, -28.8, 90), "R2": (-6.6, -28.8, 90), "SW1": (-35.4, -19.0, -90),
    "C1": (-1.3, -32.6, -90), "C2": (0.9, -32.6, -90), "D1": (4.6, -31.3, -90), "J5": (4.7, -25.0, 90),
    "J6": (-30.0, -19.5, 90), "R27": (-21.9, -18.3, 0), "R28": (-21.9, -17.1, 0),
    "TP1": (-27.5, -15.6, 0), "TP2": (-25.0, -15.6, 0), "TP3": (-22.5, -15.6, 0), "TP4": (-20.0, -15.6, 0),
    # regulador de 3.3 V
    "U1": (-17.0, -22.0, 0), "C4": (-20.6, -22.0, 90), "C5": (-17.0, -24.6, 0), "R5": (-15.0, -24.6, 0), "C6": (-19.0, -19.4, 0),
    "R6": (-16.2, -19.0, 0), "R7": (-16.2, -17.8, 0), "L1": (-11.6, -22.0, 0), "C7": (-7.9, -21.6, 90), "C8": (-7.9, -25.6, 0),
    "D2": (-20.6, -26.2, 0),
    # puentes H en la franja delantera, junto a sus conectores de motor
    # (salidas OUT1/OUT2 hacia la derecha, frente a los pines de motor de J3/J4; capacitores del lado de VM)
    "U5": (-2.6, 13.0, 90), "J3": (3.8, 13.0, -90),
    "U6": (-2.6, -13.0, 90), "J4": (3.8, -13.0, -90),
    "R25": (-4.5, 3.0, 90), "R26": (-3.2, 3.0, 90), "C23": (-1.9, 3.0, 90), "R23": (-4.5, -2.6, 90), "R24": (-3.2, -2.6, 90),
    "C31": (-4.5, 0.2, 90), "C32": (-3.2, 0.2, 90), "C33": (-1.9, 0.2, 90), "C34": (-0.6, 0.2, 90),
    "J2": (3.8, 0.0, 90), "C35": (-0.6, 3.0, 90), "C36": (-0.6, -2.6, 90),
    # bajo el módulo (8.5 mm libres): IMU, barómetro ambiente, pull-ups de I2C, divisor de batería
    "U2": (-15.0, 0.0, 0), "C9": (-17.4, 0.3, 90), "C10": (-12.9, 2.6, 0), "R29": (-11.8, 0.6, 90), "R30": (-11.8, -1.6, 90),
    "R9": (-15.0, -3.7, 0), "R10": (-15.0, -4.8, 0), "U4": (-20.5, -2.0, 0), "C12": (-22.7, -2.0, 90),
    "R3": (-26.0, -2.0, 0), "R4": (-26.0, -3.2, 0), "C3": (-26.0, -4.4, 0),
    # interfaz (esquina trasera izquierda): START, CAL, RESET, LED, zumbador; barómetro de la cámara en la cara inferior
    "SW2": (-36.4, 23.0, 0), "SW3": (-36.4, 31.0, 0), "SW4": (-39.0, 17.0, 0),
    "R11": (-29.6, 21.4, 0), "C13": (-29.6, 22.6, 0), "R12": (-29.6, 24.6, 0), "C14": (-29.6, 25.8, 0),
    "D3": (-24.0, 33.8, 0), "D4": (-21.0, 33.8, 0), "D5": (-18.0, 33.8, 0), "D6": (-15.0, 33.8, 0),
    "R8": (-24.0, 32.1, 0), "R13": (-21.0, 32.1, 0), "R14": (-18.0, 32.1, 0), "R15": (-15.0, 32.1, 0),
    "LS1": (-12.0, 22.5, 0), "Q3": (-22.6, 17.3, 0), "R16": (-20.0, 15.4, 0), "R17": (-25.3, 17.8, 90), "R18": (-26.6, 17.8, 90),
    "U3": (-20.0, 22.0, 0, "B"), "C11": (-20.0, 27.5, 0, "B"),
}
# Celda de cada puente H (U5 y U6 tienen la misma rotación y el mismo conector a la derecha): capacitores y resistencias
# justo frente a sus pines y pistas fijas cortas (ver CELDA_PISTAS), para que el enrutador no tenga que resolver lo más
# apretado. Desplazamientos (dx, dy) desde el centro del DRV8874 en el marco del robot; fila de pines 9-16 hacia +y.
CELDA = {"CPH_CPL": (-0.75, 4.6, 180), "VCP": (0.70, 5.9, 0), "VM_100n": (1.18, 7.35, 90), "VM_22u": (-1.1, 7.4, 180),
         "IPROPI": (0.97, -4.85, -90), "IMODE": (1.62, -6.75, -90)}
REF_CELDA = {"U5": {"CPH_CPL": "C18", "VCP": "C17", "VM_100n": "C15", "VM_22u": "C16", "IPROPI": "R19", "IMODE": "R20", "J": "J3"},
             "U6": {"CPH_CPL": "C22", "VCP": "C21", "VM_100n": "C19", "VM_22u": "C20", "IPROPI": "R21", "IMODE": "R22", "J": "J4"}}
for _u, _refs in REF_CELDA.items():
    _cx, _cy = COLOC[_u][0], COLOC[_u][1]
    for _k, (_dx, _dy, _r) in CELDA.items():
        COLOC[_refs[_k]] = (round(_cx + _dx, 3), round(_cy + _dy, 3), _r)


def celda_pistas():
    """Pistas fijas de cada celda de puente H (marco del robot, mm). ("pad", ref, n) = centro de ese pad."""
    out = []
    for u, refs in REF_CELDA.items():
        cx, cy = COLOC[u][0], COLOC[u][1]
        P = lambda dx, dy: [round(cx + dx, 3), round(cy + dy, 3)]
        j = refs["J"]
        out += [
            dict(pad=(u, "14"), ancho=0.2, puntos=[P(-0.98, 2.86), P(-0.98, 4.6)]),                 # CPL -> C18/C22
            dict(pad=(u, "13"), ancho=0.2, puntos=[P(-0.32, 2.86), P(-0.32, 4.6)]),                 # CPH
            dict(pad=(u, "12"), ancho=0.2, puntos=[P(0.32, 2.86), P(0.32, 5.9)]),                   # VCP -> C17/C21
            dict(pad=(u, "11"), ancho=0.45, puntos=[P(0.97, 2.86), P(0.97, 5.9)]),                  # VM -> C17/C21
            dict(pad=(u, "11"), ancho=0.45, puntos=[P(1.18, 5.9), P(1.18, 6.87), P(0.2, 6.87)]),    # VM -> C15 y C16
            dict(pad=(u, "10"), ancho=0.45, puntos=[P(1.62, 2.86), P(1.62, 4.3), P(3.3, 4.3), P(3.3, -1.5), ("pad", j, "5")]),  # OUT2
            dict(pad=(u, "8"), ancho=0.45, puntos=[P(2.27, -2.86), P(2.27, -4.0), P(4.2, -4.0), P(4.2, -2.5), ("pad", j, "6")]),  # OUT1
            dict(pad=(u, "6"), ancho=0.2, puntos=[P(0.97, -2.86), P(0.97, -4.37)]),                 # IPROPI -> R19/R21
            dict(pad=(u, "7"), ancho=0.2, puntos=[P(1.62, -2.86), P(1.62, -6.27)]),                 # IMODE -> R20/R22
        ]
    return out


for _p in D.partes:
    if _p.ref in COLOC:
        c = COLOC[_p.ref]
        _p.x, _p.y, _p.rot = c[0], c[1], c[2]
        if len(c) > 3:
            _p.lado = c[3]


def nombres_red():
    """Nombre de cada red como lo pone KiCad al leer el esquemático: las locales llevan la ruta de su hoja."""
    hojas_de, titulo = {}, dict(D.hojas)
    for p in D.partes:
        for pin, r in p.pines.items():
            hojas_de.setdefault(r, set()).add(p.hoja)
    return {r: (r if (len(h) > 1 or r in D.power) else f"/{titulo[next(iter(h))]}/{r}") for r, h in hojas_de.items()}


def plan():
    nr = nombres_red()
    x0, x1, y0, y1 = CONTORNO
    r = 1.5                                         # esquinas redondeadas (polígono)
    contorno = []
    for cx, cy, a0 in ((x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180), (x1 - r, y0 + r, 270)):
        for k in range(7):
            a = math.radians(a0 + 15 * k)
            contorno.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    partes = []
    for p in D.partes:
        if not p.huella:
            continue
        lib, fp = p.huella.split(":")
        partes.append(dict(ref=p.ref, valor=p.valor, lib=lib, fp=fp, X=round(p.x, 4), Y=round(K.Y0 - p.y, 4),
                           rot=round(p.rot, 3), lado=p.lado, redes={k: nr[vv] for k, vv in p.pines.items() if k not in p.nc},
                           en_bom=p.en_bom, mpn=p.mpn, fabricante=p.fabricante, hoja=p.hoja,
                           ref_visible=p.ref.startswith(("SW", "J", "TP"))))
    def poli(pts):
        return [[round(x, 4), round(K.Y0 - y, 4)] for x, y in pts]

    # Cobre de la ruta de la batería: polígonos de cobre (F.Cu; VBAT_IN también en B.Cu) sobre las pistas de Freerouting.
    zonas = [
        dict(red=nr["VBAT_IN"], capas=["F", "B"], prioridad=2, puntos=poli([(-36.0, -34.75), (-19.4, -34.75), (-19.4, -29.6), (-36.0, -29.6)])),
        dict(red=nr["VBAT_F"], capas=["F"], prioridad=2, puntos=poli([(-17.3, -34.75), (-8.6, -34.75), (-8.6, -30.3), (-17.3, -30.3)])),
        dict(red=nr["VBAT_S"], capas=["F"], prioridad=2, puntos=poli([(-8.15, -33.95), (-7.05, -33.95), (-7.05, -33.16), (-5.65, -33.16),
                                                                       (-5.65, -31.25), (-6.75, -31.25), (-6.75, -32.04), (-8.15, -32.04)])),
        dict(red=nr["VBAT_SW"], capas=["F"], prioridad=2, puntos=poli([(-5.25, -34.2), (-2.4, -34.2), (-2.4, -32.4), (6.25, -32.4),
                                                                        (6.25, -23.6), (3.4, -23.6), (3.4, -29.6), (-5.25, -29.6)])),
    ]
    agujeros = [dict(X=round(p.x, 4), Y=round(K.Y0 - p.y, 4), r=2.5) for p in D.partes if p.ref.startswith("H")]
    # empaque Ø8/Ø4 de la chimenea del chasis alrededor del barómetro de la cámara (U3, cara inferior): sin vías (fugarían)
    sin_vias = [dict(X=-20.0, Y=K.Y0 - 22.0, r=4.4)]
    vias = [dict(ref=r, pad="17", red="GND", taladro=0.3, diametro=0.6,
                 offsets=[[dx, dy] for dx in (-0.6, 0.6) for dy in (-1.2, 0.0, 1.2)]) for r in ("U5", "U6")]
    return dict(
        proy=D.proy, titulo=D.titulo, capas=4, espesor=1.6, origen_aux=[x0, K.Y0 - y0],
        # 4 capas: señales en F.Cu y B.Cu; In1 = plano de GND, In2 = plano de +3V3 (tipo "power": no se enruta en ellas)
        tipo_capas={"In1.Cu": "power", "In2.Cu": "power"},
        contorno=[[round(x, 4), round(K.Y0 - y, 4)] for x, y in contorno], partes=partes,
        clases={"Default": dict(pista=0.2, separacion=0.2, separacion_drc=0.15, via=0.6, taladro=0.3, patrones=[]),
                # GND y +3V3 no las enruta Freerouting: vías de abanico a sus planos internos (In1, In2)
                "Planos": dict(pista=0.3, separacion=0.2, separacion_drc=0.15, via=0.6, taladro=0.3, patrones=["GND", "+3V3"]),
                "Bateria": dict(pista=0.4, separacion=0.2, separacion_drc=0.2, via=0.8, taladro=0.4,
                                patrones=["*VBAT_IN", "*VBAT_F", "*VBAT_S"]),
                "Motor": dict(pista=0.45, separacion=0.2, separacion_drc=0.15, via=0.8, taladro=0.4, patrones=["*MOT_*", "VBAT_SW"]),
                "Buck": dict(pista=0.5, separacion=0.2, separacion_drc=0.15, via=0.8, taladro=0.4, patrones=["*VIN_BUCK", "*BUCK_SW"])},
        planos=[dict(capa="In1.Cu", red="GND"), dict(capa="In2.Cu", red="+3V3"), dict(capa="B", red="GND"),
                dict(capa="F", red="GND")], zonas=zonas, agujeros=agujeros, sin_vias=sin_vias, vias=vias,
        pistas_fijas=celda_pistas() + [
            # U3 (LPS22DF de la cámara, cara inferior, bajo el empaque: sin vías): pads de +3V3 unidos de a dos por fuera
            dict(pad=("U3", "5"), capa="B", ancho=0.2, puntos=[[-19.5, 22.76], [-19.5, 23.2], [-18.8, 23.2], [-18.8, 22.25], ["pad", "U3", "6"]]),
            dict(pad=("U3", "10"), capa="B", ancho=0.2, puntos=[[-20.5, 21.24], [-20.5, 20.8], [-21.2, 20.8], [-21.2, 21.75], ["pad", "U3", "1"]])],
        abanico=[dict(red="GND", diametro=0.6, taladro=0.3, pista=0.3, separacion=0.25, excluir_pads=["17"],
                      unir_a_pad={"U5": "17", "U6": "17"}),
                 dict(red="+3V3", diametro=0.6, taladro=0.3, pista=0.3, separacion=0.25)],
        redes_plano=["GND", "+3V3"],
        conexion_solida=[["U3", "3"], ["U3", "8"], ["U3", "9"]],    # GND de U3 bajo el empaque: al plano inferior sin alivio
        holgura_local={"U2": 0.127, "U3": 0.127, "U4": 0.127}, nombres_red=nr,
        textos=[dict(texto="CIRCUIT FORGE V2 · PCB PRINCIPAL · REV A", X=-23.86, Y=K.Y0 - 4.0, rot=0, lado="B", tam=1.0),
                dict(texto="START", X=-36.4, Y=K.Y0 - 27.6, rot=0, lado="F", tam=1.0),
                dict(texto="CAL", X=-29.0, Y=K.Y0 - 34.0, rot=0, lado="F", tam=1.0),
                dict(texto="RST", X=-35.0, Y=K.Y0 - 17.0, rot=0, lado="F", tam=1.0),
                dict(texto="P", X=-24.0, Y=K.Y0 - 30.5, rot=0, lado="F", tam=1.0),
                dict(texto="V", X=-21.0, Y=K.Y0 - 30.5, rot=0, lado="F", tam=1.0),
                dict(texto="A", X=-18.0, Y=K.Y0 - 30.5, rot=0, lado="F", tam=1.0),
                dict(texto="R", X=-15.0, Y=K.Y0 - 30.5, rot=0, lado="F", tam=1.0),
                dict(texto="ESC", X=2.1, Y=K.Y0 + 22.7, rot=90, lado="F", tam=1.0),
                dict(texto="+", X=2.6, Y=K.Y0 + 25.6, rot=0, lado="F", tam=1.2),
                dict(texto="-", X=2.6, Y=K.Y0 + 19.6, rot=0, lado="F", tam=1.2),
                dict(texto="ESC SEÑAL", X=-27.5, Y=K.Y0 + 22.3, rot=0, lado="F", tam=1.0),
                dict(texto="BAT+", X=-33.8, Y=K.Y0 + 27.8, rot=0, lado="F", tam=1.0),
                dict(texto="ON", X=-40.0, Y=K.Y0 + 15.0, rot=0, lado="F", tam=1.0)])


def huella_zocalo(dir_lib):
    """Huella con los 48 pines del módulo en su posición real (plano de contorno WeAct: 36.28 × 28.14 mm; primera
    columna a 6.97 mm del borde del USB; filas a 1.37 mm de los bordes largos; 20.32 mm entre filas interiores)."""
    os.makedirs(dir_lib, exist_ok=True)
    W, H = 36.28, 28.14
    fil = {"B_par": 1.37, "B_impar": 3.91, "A_par": H - 3.91, "A_impar": H - 1.37}
    elems = [Sym("footprint"), "WeAct_STM32G474_CoreBoard_Zocalo", [Sym("version"), 20241229], [Sym("generator"), "circuitforge"],
             [Sym("layer"), "F.Cu"],
             [Sym("descr"), "WeAct STM32G474 Core Board V1.0 en 2 zócalos hembra 2x12 2.54 mm; USB-C hacia -X; P1 = pads A, P2 = pads B"],
             [Sym("tags"), "WeAct STM32G474 module socket"], [Sym("attr"), Sym("through_hole")]]

    def texto(tipo, t, x, y, capa, oculto=False):
        nodo = [Sym("property"), tipo, t, [Sym("at"), x, y, 0], [Sym("layer"), capa],
                [Sym("effects"), [Sym("font"), [Sym("size"), 1, 1], [Sym("thickness"), 0.15]]]]
        if oculto:
            nodo.insert(4, [Sym("hide"), Sym("yes")])
        return nodo
    elems += [texto("Reference", "REF**", 0, -H / 2 - 1.5, "F.SilkS"), texto("Value", "WeAct_STM32G474", 0, H / 2 + 1.5, "F.Fab")]
    for capa, m, ancho in (("F.SilkS", 0.11, 0.12), ("F.Fab", 0.0, 0.1)):
        elems.append([Sym("fp_rect"), [Sym("start"), -W / 2 - m, -H / 2 - m], [Sym("end"), W / 2 + m, H / 2 + m],
                      [Sym("stroke"), [Sym("width"), ancho], [Sym("type"), Sym("solid")]], [Sym("fill"), Sym("no")], [Sym("layer"), capa]])
    # Cortijo: solo los 2 zócalos (2 × 12, 30.5 × 5.1 mm). El módulo queda 8.5 mm arriba: debajo caben componentes bajos.
    x0z, x1z = 6.97 - W / 2 - 1.27 - 0.25, 6.97 + 11 * 2.54 - W / 2 + 1.27 + 0.25
    for y0z, y1z in ((fil["B_par"] - H / 2 - 1.27 - 0.25, fil["B_impar"] - H / 2 + 1.27 + 0.25),
                     (fil["A_par"] - H / 2 - 1.27 - 0.25, fil["A_impar"] - H / 2 + 1.27 + 0.25)):
        elems.append([Sym("fp_rect"), [Sym("start"), round(x0z, 3), round(y0z, 3)], [Sym("end"), round(x1z, 3), round(y1z, 3)],
                      [Sym("stroke"), [Sym("width"), 0.05], [Sym("type"), Sym("solid")]], [Sym("fill"), Sym("no")], [Sym("layer"), "F.CrtYd"]])
    elems.append([Sym("fp_text"), Sym("user"), "USB-C", [Sym("at"), -W / 2 + 3.0, 0, 90], [Sym("layer"), "F.SilkS"],
                  [Sym("effects"), [Sym("font"), [Sym("size"), 1, 1], [Sym("thickness"), 0.15]]]])
    for pref in ("A", "B"):
        for n in range(1, 25):
            k = (n - 1) // 2
            fila = f"{pref}_{'par' if n % 2 == 0 else 'impar'}"
            x = round(6.97 + 2.54 * k - W / 2, 4)
            y = round(fil[fila] - H / 2, 4)
            forma = Sym("rect") if n == 1 else Sym("circle")
            elems.append([Sym("pad"), f"{pref}{n}", Sym("thru_hole"), forma, [Sym("at"), x, y], [Sym("size"), 1.7, 1.7],
                          [Sym("drill"), 1.0], [Sym("layers"), "*.Cu", "*.Mask"], [Sym("remove_unused_layers"), Sym("no")]])
    with open(os.path.join(dir_lib, "WeAct_STM32G474_CoreBoard_Zocalo.kicad_mod"), "w", encoding="utf-8") as f:
        f.write(sexpr.dump(elems) + "\n")


def principal():
    err = D.verificar()
    if err:
        raise SystemExit("\n".join(err))
    K.escribir_esquematico(D, notas={
        HC: ["A1: módulo WeAct STM32G474CEU6 Core Board en zócalos. El módulo toma 3.3 V de esta placa (pines 3V3); su VCC queda libre.",
             "El USB-C, BOOT0 y RESET del módulo quedan accesibles en el borde trasero. Cargador DFU por USB (AN2606: HSI48 + CRS, PA11/PA12).",
             "PB11 (/CS de la flash QSPI del módulo) sin conectar: la flash queda deseleccionada y PB0, PB1, PB10 se usan para los LED.",
             "PB8 = BOOT0 al reset: la compuerta de Q3 tiene 100k a GND, así el zumbador no cambia el arranque.",
             "I2C3 (PA8/PC11): ISM330DHCX 0x6A, LPS22DF ambiente 0x5C, LPS22DF de la cámara 0x5D."],
        HM: ["DRV8874: PMODE a GND = PH/EN. ITRIP = VREF / (R_IPROPI × A_IPROPI) = 1.055 V / (1.5 kΩ × 450 µA/A) ≈ 1.56 A por motor (Fase 3.5).",
             "IMODE con 0 Ω a GND (nivel 1); cambiar por 20k/62k cambia el modo de regulación (tabla IMODE de la hoja de datos).",
             "J3/J4: pinout del encoder Pololu (1 GND, 2 B, 3 A, 4 VCC, 5 M2, 6 M1). J2: 1:1 con J1 de la barra de sensores.",
             "ESC: señal por J6 (PB9, TIM17_CH1: PWM, Oneshot o DShot con telemetría bidireccional), potencia por J5."]})
    huella_zocalo(os.path.join(D.dir, f"{K.LIB_PROPIA}.pretty"))
    os.makedirs(os.path.join(K.V2E, "generador", "salida"), exist_ok=True)
    ruta = os.path.join(K.V2E, "generador", "salida", "plan_principal.json")
    json.dump(plan(), open(ruta, "w"), indent=1)
    print("plan ->", os.path.relpath(ruta, K.RAIZ))


if __name__ == "__main__":
    principal()
