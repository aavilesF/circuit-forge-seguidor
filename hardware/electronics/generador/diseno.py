"""Diseño electrónico DEFINITIVO del Speed Follower (fuente única).

De aquí salen el esquemático (esquematico.py), la PCB (pcb.py), la BOM de ensamblaje, el pick-and-place y la
cabecera de pines del firmware (firmware/stm32/pines_generados.h). Ningún otro archivo repite estas conexiones.

Coordenadas de colocación en el marco del ROBOT (mm): x hacia adelante desde el centro del eje de ruedas,
y a la izquierda; rot en grados (antihorario visto desde arriba); lado "F" (arriba) o "B" (abajo, hacia el piso).
Origen de datos de cada parte: ver la columna `verificado` de la BOM (docs/BOM_FINAL.csv)."""
from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass, field

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "sim"))
sys.path.insert(0, os.path.join(RAIZ, "hardware"))
sys.path.insert(0, os.path.join(AQUI, "..", "herramientas"))
import config as CF  # noqa: E402
import geometria as GEO  # noqa: E402
import sexpr  # noqa: E402

KICAD = os.environ.get("KICAD_SHARE", "/opt/resolute/usr/share/kicad")
LIB_PROPIA = "circuitforge"


@dataclass
class Parte:
    ref: str
    lib_id: str              # símbolo "Biblioteca:Nombre"
    valor: str
    huella: str              # "Biblioteca:Huella"
    fabricante: str
    mpn: str
    descripcion: str
    hoja: str                # hoja del esquemático
    pines: dict              # número de pin -> red
    x: float = 0.0
    y: float = 0.0
    rot: float = 0.0
    lado: str = "F"
    datasheet: str = ""
    dnp: bool = False        # no se monta (p. ej. agujeros) / no va a la BOM
    en_bom: bool = True
    nc: tuple = ()           # pines sin conexión intencional
    extra: dict = field(default_factory=dict)


PARTES: list[Parte] = []


def P(**kw):
    p = Parte(**kw)
    PARTES.append(p)
    return p


# --------------------------------------------------------------------------------------------- catálogo
DS = {
    "STM32G431CB": "https://www.st.com/resource/en/datasheet/stm32g431cb.pdf",
    "DRV8833": "https://www.ti.com/lit/ds/symlink/drv8833.pdf",
    "TPS563200": "https://www.ti.com/lit/ds/symlink/tps563200.pdf",
    "QRE1113": "https://www.onsemi.com/pdf/datasheet/qre1113-d.pdf",
    "AO3401A": "https://www.aosmd.com/res/datasheets/AO3401A.pdf",
    "AO3400A": "https://www.aosmd.com/res/datasheets/AO3400A.pdf",
    "SMAJ": "https://www.littelfuse.com/assetdocs/littelfuse-tvs-diode-smaj-datasheet",
    "1812L": "https://www.littelfuse.com/assetdocs/littelfuse-ptc-1812l-datasheet",
    "XT30UPB": "https://www.tme.eu/Document/e5863b891432488e7531b3c4468225ac/XT30PB-M.pdf",
    "BM06B": "https://www.jst-mfg.com/product/pdf/eng/eSH.pdf",
    "M50-35": "https://www.harwin.com/products/M50-3500742/",
    "OS102011": "https://www.ckswitches.com/media/1428/os.pdf",
    "B3FS": "https://omronfs.omron.com/en_US/ecb/products/pdf/en-b3fs.pdf",
    "B3U": "https://omronfs.omron.com/en_US/ecb/products/pdf/en-b3u.pdf",
    "APT1608": "https://www.kingbrightusa.com/images/catalog/SPEC/APT1608SGC.pdf",
    "BLM18PG": "https://www.murata.com/en-us/products/productdetail?partno=BLM18PG221SN1D",
    "MAPI": "https://www.we-online.com/components/products/datasheet/74438357022.pdf",
    "GRM": "https://www.murata.com/en-us/products/capacitor/ceramiccapacitor",
    "RC_YAGEO": "https://www.yageo.com/upload/media/product/productsearch/datasheet/rchip/PYu-RC_Group_51_RoHS_L_12.pdf",
}

# Resistencias Yageo RC (1 %), condensadores Murata GRM: (valor, encapsulado) -> MPN
RES = {("100k", "0402"): "RC0402FR-07100KL", ("10k", "0402"): "RC0402FR-0710KL", ("33k", "0402"): "RC0402FR-0733KL",
       ("33.2k", "0402"): "RC0402FR-0733K2L", ("1k", "0402"): "RC0402FR-071KL", ("100", "0402"): "RC0402FR-07100RL",
       ("75", "0603"): "RC0603FR-0775RL"}
CAP = {("100n", "0402"): ("GRM155R71C104KA88D", "16 V X7R"), ("10n", "0402"): ("GRM155R71H103KA88D", "50 V X7R"),
       ("1n", "0402"): ("GRM155R71H102KA01D", "50 V X7R"), ("1u", "0402"): ("GRM155R61A105KE15D", "10 V X5R"),
       ("2.2u", "0402"): ("GRM155R60J225ME15D", "6.3 V X5R"), ("4.7u", "0603"): ("GRM188R61A475KE15D", "10 V X5R"),
       ("10u", "0805"): ("GRM21BR61E106KA73L", "25 V X5R"), ("22u", "0805"): ("GRM21BR61E226ME44L", "25 V X5R")}
HUELLA_RC = {"0402": "Resistor_SMD:R_0402_1005Metric", "0603": "Resistor_SMD:R_0603_1608Metric"}
HUELLA_C = {"0402": "Capacitor_SMD:C_0402_1005Metric", "0603": "Capacitor_SMD:C_0603_1608Metric",
            "0805": "Capacitor_SMD:C_0805_2012Metric"}


def R(ref, valor, a, b, hoja, enc="0402", **kw):
    return P(ref=ref, lib_id="Device:R", valor=valor + ("Ω" if valor[-1].isdigit() else ""), huella=HUELLA_RC[enc],
             fabricante="YAGEO", mpn=RES[(valor, enc)], descripcion=f"Resistencia {valor}Ω 1 % {enc}",
             hoja=hoja, pines={"1": a, "2": b}, datasheet=DS["RC_YAGEO"], **kw)


def C(ref, valor, a, b, hoja, enc="0402", **kw):
    mpn, tipo = CAP[(valor, enc)]
    return P(ref=ref, lib_id="Device:C", valor=valor.replace("u", "µ") + "F", huella=HUELLA_C[enc], fabricante="Murata",
             mpn=mpn, descripcion=f"Condensador cerámico {valor.replace('u', 'µ')}F {tipo} {enc}", hoja=hoja,
             pines={"1": a, "2": b}, datasheet=DS["GRM"], **kw)


# --------------------------------------------------------------------------------------------- pines del MCU
MCU_ALT = {}       # nombre de pin (PA0...) -> lista de funciones alternas (del símbolo oficial de KiCad)
MCU_NUM = {}       # nombre de pin -> número en LQFP-48 (solo pines con nombre único: GPIO)
MCU_LISTA = []     # (número, nombre) de los 48 pines


def _cargar_mcu():
    lib = sexpr.parse(open(os.path.join(KICAD, "symbols", "MCU_ST_STM32G4.kicad_sym"), encoding="utf-8").read())
    for s in sexpr.hijos(lib, "symbol"):
        if s[1] == "STM32G431C_6-8-B_Tx":
            for u in sexpr.hijos(s, "symbol"):
                for p in sexpr.hijos(u, "pin"):
                    nm = sexpr.hijo(p, "name")[1]
                    MCU_LISTA.append((sexpr.hijo(p, "number")[1], nm))
                    MCU_NUM[nm.split("-")[0]] = sexpr.hijo(p, "number")[1]
                    MCU_ALT[nm.split("-")[0]] = [a[1] for a in sexpr.hijos(p, "alternate")]


_cargar_mcu()

# Funciones fijas (AF verificadas con STM32_open_pin_data de ST, ver docs/CALCULOS_ELECTRICOS.md)
FIJOS = {
    "PA8": ("PWM_AIN1", "TIM1_CH1", 6), "PA9": ("PWM_AIN2", "TIM1_CH2", 6), "PA10": ("PWM_BIN1", "TIM1_CH3", 6),
    "PA11": ("PWM_BIN2", "TIM1_CH4", 11),
    "PA15": ("ENC_L_A", "TIM2_CH1", 1), "PB3": ("ENC_L_B", "TIM2_CH2", 1),
    "PB4": ("ENC_R_A", "TIM3_CH1", 2), "PB5": ("ENC_R_B", "TIM3_CH2", 2),
    "PB6": ("UART_TX", "USART1_TX", 7), "PB7": ("UART_RX", "USART1_RX", 7),
    "PA13": ("SWDIO", "SYS_JTMS-SWDIO", 0), "PA14": ("SWCLK", "SYS_JTCK-SWCLK", 0),
    "PC13": ("BTN_START", "GPIO_IN", None), "PC14": ("BTN_CAL", "GPIO_IN", None), "PC15": ("DRV_FAULT", "GPIO_IN", None),
    "PB9": ("EMIT_G", "GPIO_OUT", None), "PB10": ("DRV_SLEEP", "GPIO_OUT", None),
    "PB13": ("LED_OK", "GPIO_OUT", None), "PA12": ("LED_ERR", "GPIO_OUT", None),
    "PB8": ("BOOT0", "BOOT0", None), "PG10": ("NRST", "NRST", None),
}
for _pin, (_red, _fun, _af) in FIJOS.items():
    if _fun.startswith(("TIM", "USART", "SYS")):
        assert _fun in MCU_ALT[_pin], (_pin, _fun)          # la función existe en ese pin según ST/KiCad

ADC_PINES = [p for p in MCU_ALT if any(a.startswith(("ADC1_IN", "ADC2_IN")) for a in MCU_ALT[p])]
assert len(ADC_PINES) == 17, ADC_PINES


def canales_adc(pin):
    """{1: canal, 2: canal} según las funciones alternas del pin."""
    out = {}
    for a in MCU_ALT[pin]:
        if a.startswith("ADC1_IN"):
            out[1] = int(a[7:])
        elif a.startswith("ADC2_IN"):
            out[2] = int(a[7:])
    return out


# --------------------------------------------------------------------------------------------- geometría
G = GEO.cargar()
N_SENS = G.n_sensores
POS_MCU = (64.0, 0.0, 180.0)         # x, y, rot del STM32: lado de los pines 1-12 hacia adelante (arco)


def _pads_lqfp():
    fp = sexpr.parse(open(os.path.join(KICAD, "footprints", "Package_QFP.pretty", "LQFP-48_7x7mm_P0.5mm.kicad_mod"),
                          encoding="utf-8").read())
    return {p[1]: (float(sexpr.hijo(p, "at")[1]), float(sexpr.hijo(p, "at")[2])) for p in sexpr.hijos(fp, "pad")}


def pad_mcu_robot(num):
    """Posición en el marco del robot del pad `num` del MCU (KiCad: x a la derecha, y hacia abajo)."""
    px, py = _pads_lqfp()[num]
    xr, yr, rot = POS_MCU
    a = math.radians(rot)
    # footprint en KiCad -> robot: x_robot = x_kicad, y_robot = -y_kicad
    dx, dy = px, -py
    return xr + dx * math.cos(a) - dy * math.sin(a), yr + dx * math.sin(a) + dy * math.cos(a)


def asignar_adc():
    """Asigna los 16 sensores y la medición de batería a los 17 pines con ADC sin cruces en el abanico.
    Se recorre el perímetro del MCU en sentido antihorario empezando por el lado derecho del robot (y−), pasando por
    el frente y la izquierda hasta la parte trasera; los sensores se asignan en el mismo orden, de S16 (derecha) a S1
    (izquierda). El último pin del recorrido (trasero) mide la batería."""
    cx, cy = POS_MCU[0], POS_MCU[1]

    def param(p):
        x, y = pad_mcu_robot(MCU_NUM[p])
        return (math.degrees(math.atan2(y - cy, x - cx)) + 90.0) % 360.0

    orden = sorted(ADC_PINES, key=param)
    asig = {p: f"S{N_SENS - i}" for i, p in enumerate(orden[:N_SENS])}
    vbat = orden[N_SENS]
    asig[vbat] = "VBAT_MED"
    adc = {}
    for p in orden:
        ch = canales_adc(p)
        if len(ch) == 1:
            adc[p] = next(iter(ch))
    for p in orden:
        if p not in adc:
            c1 = sum(1 for q in adc if adc[q] == 1 and asig[q] != "VBAT_MED")
            c2 = sum(1 for q in adc if adc[q] == 2 and asig[q] != "VBAT_MED")
            adc[p] = 1 if c1 <= c2 else 2
    return asig, adc


ADC_ASIG, ADC_INST = asignar_adc()

# --------------------------------------------------------------------------------------------- hoja 1: alimentación
H1 = "alimentacion"
P(ref="J1", lib_id="Connector_Generic:Conn_01x02", valor="XT30UPB-M", huella="Connector_AMASS:AMASS_XT30UPB-M_1x02_P5.0mm_Vertical",
  fabricante="Changzhou Amass Electronics", mpn="XT30UPB-M", descripcion="Conector de batería XT30 macho vertical para PCB, 15 A (pin 1 −, pin 2 +)",
  hoja=H1, pines={"1": "GND", "2": "VBAT_IN"}, x=26.0, y=-25.0, rot=90, datasheet=DS["XT30UPB"],
  extra=dict(modelo3d="propio:AMASS_XT30UPB-M"))
P(ref="F1", lib_id="Device:Polyfuse", valor="1.5A/12V", huella="Fuse:Fuse_1812_4532Metric", fabricante="Littelfuse",
  mpn="1812L150/12DR", descripcion="Fusible reajustable PTC 1812, Ihold 1.5 A, 12 V", hoja=H1,
  pines={"1": "VBAT_IN", "2": "VBAT_F"}, x=33.5, y=-22.0, rot=90, datasheet=DS["1812L"], extra=dict(modelo3d="propio:Fuse_1812L"))
P(ref="Q1", lib_id="Transistor_FET:AO3401A", valor="AO3401A", huella="Package_TO_SOT_SMD:SOT-23", fabricante="Alpha & Omega Semiconductor",
  mpn="AO3401A", descripcion="MOSFET P −30 V −4 A SOT-23 (protección contra inversión)", hoja=H1,
  pines={"1": "PFET_G", "2": "VBAT_SRC", "3": "VBAT_F"}, x=37.5, y=-25.5, rot=0, datasheet=DS["AO3401A"])
P(ref="Q2", lib_id="Transistor_FET:AO3401A", valor="AO3401A", huella="Package_TO_SOT_SMD:SOT-23", fabricante="Alpha & Omega Semiconductor",
  mpn="AO3401A", descripcion="MOSFET P −30 V −4 A SOT-23 (interruptor de encendido)", hoja=H1,
  pines={"1": "PFET_G", "2": "VBAT_SRC", "3": "VBAT_SW"}, x=37.5, y=-19.0, rot=180, datasheet=DS["AO3401A"])
R("R1", "100k", "VBAT_SRC", "PFET_G", H1, x=41.0, y=-22.5, rot=90)
R("R2", "10k", "PFET_G", "SW_COM", H1, x=43.0, y=-22.5, rot=90)
P(ref="SW1", lib_id="Switch:SW_SPDT", valor="ENCENDIDO", huella="Button_Switch_THT:SW_Slide_SPDT_Angled_CK_OS102011MA1Q",
  fabricante="C&K", mpn="OS102011MA1QN1", descripcion="Interruptor deslizante SPDT de ángulo recto, 100 mA 12 V (solo conmuta la compuerta)",
  hoja=H1, pines={"1": "GND", "2": "SW_COM", "3": "SW_OFF"}, x=47.0, y=-26.5, rot=-90, datasheet=DS["OS102011"], nc=("3",))
P(ref="D1", lib_id="Diode:SMAJ9.0A", valor="SMAJ9.0A", huella="Diode_SMD:D_SMA", fabricante="Littelfuse", mpn="SMAJ9.0A",
  descripcion="TVS unidireccional 400 W, 9.0 V de trabajo (DO-214AC)", hoja=H1, pines={"1": "VBAT_SW", "2": "GND"},
  x=31.0, y=-15.0, rot=0, datasheet=DS["SMAJ"])
C("C1", "22u", "VBAT_SW", "GND", H1, enc="0805", x=22.0, y=-4.5, rot=90)
C("C2", "22u", "VBAT_SW", "GND", H1, enc="0805", x=22.0, y=4.5, rot=90)
R("R3", "100k", "VBAT_SW", "VBAT_MED", H1, x=52.5, y=-10.0, rot=0)
R("R4", "33k", "VBAT_MED", "GND", H1, x=55.0, y=-10.0, rot=0)
C("C3", "100n", "VBAT_MED", "GND", H1, x=55.0, y=-8.6, rot=0)
# regulador 3.3 V
P(ref="U2", lib_id="Regulator_Switching:TPS563200", valor="TPS563200", huella="Package_TO_SOT_SMD:SOT-23-6", fabricante="Texas Instruments",
  mpn="TPS563200DDCR", descripcion="Convertidor reductor síncrono 4.5-17 V, 3 A, 650 kHz (SOT-23-6)", hoja=H1,
  pines={"1": "GND", "2": "BUCK_SW", "3": "VBAT_SW", "4": "BUCK_FB", "5": "BUCK_EN", "6": "BUCK_BST"},
  x=42.0, y=-12.0, rot=0, datasheet=DS["TPS563200"])
C("C4", "10u", "VBAT_SW", "GND", H1, enc="0805", x=37.5, y=-12.0, rot=90)
C("C5", "10u", "VBAT_SW", "GND", H1, enc="0805", x=35.5, y=-12.0, rot=90)
C("C6", "100n", "VBAT_SW", "GND", H1, x=39.6, y=-10.4, rot=0)
R("R5", "100k", "VBAT_SW", "BUCK_EN", H1, x=39.6, y=-14.2, rot=0)
C("C7", "100n", "BUCK_BST", "BUCK_SW", H1, x=44.6, y=-14.2, rot=0)
P(ref="L1", lib_id="Device:L", valor="2.2µH", huella="Inductor_SMD:L_Wuerth_MAPI-4030", fabricante="Würth Elektronik", mpn="74438357022",
  descripcion="Inductor blindado WE-MAPI 4030, 2.2 µH, IR 7.1 A, Isat 9.2 A, 26 mΩ", hoja=H1,
  pines={"1": "BUCK_SW", "2": "+3V3"}, x=47.5, y=-15.5, rot=0, datasheet=DS["MAPI"])
R("R6", "33.2k", "+3V3", "BUCK_FB", H1, x=44.6, y=-10.0, rot=0)
R("R7", "10k", "BUCK_FB", "GND", H1, x=44.6, y=-8.8, rot=0)
C("C8", "22u", "+3V3", "GND", H1, enc="0805", x=51.5, y=-15.0, rot=90)
C("C9", "22u", "+3V3", "GND", H1, enc="0805", x=53.5, y=-15.0, rot=90)
P(ref="D2", lib_id="Device:LED", valor="PWR", huella="LED_SMD:LED_0603_1608Metric", fabricante="Kingbright", mpn="APT1608SGC",
  descripcion="LED verde 0603 (3.3 V presente)", hoja=H1, pines={"1": "GND", "2": "LED_PWR"}, x=56.0, y=-20.0, rot=180,
  datasheet=DS["APT1608"])
R("R8", "1k", "+3V3", "LED_PWR", H1, x=56.0, y=-18.5, rot=0)

# --------------------------------------------------------------------------------------------- hoja 2: MCU y programación
H2 = "mcu"
pin_red = {}
for nm, num in MCU_NUM.items():
    if nm in FIJOS:
        pin_red[num] = FIJOS[nm][0]
    elif nm in ADC_ASIG:
        pin_red[num] = ADC_ASIG[nm]
for num, nm in MCU_LISTA:
    if nm.startswith("VDDA") or nm == "VREF+":
        pin_red[num] = "+3V3A"
    elif nm.startswith(("VDD", "VBAT")):
        pin_red[num] = "+3V3"
    elif nm.startswith(("VSS",)):
        pin_red[num] = "GND"
libres = [num for num, nm in MCU_LISTA if num not in pin_red]
assert not libres, libres
P(ref="U1", lib_id="MCU_ST_STM32G4:STM32G431CBTx", valor="STM32G431CBT6", huella="Package_QFP:LQFP-48_7x7mm_P0.5mm",
  fabricante="STMicroelectronics", mpn="STM32G431CBT6", descripcion="MCU Arm Cortex-M4F 170 MHz, 128 KB flash, 32 KB RAM, 2 ADC 12 bits, LQFP-48",
  hoja=H2, pines=pin_red, x=POS_MCU[0], y=POS_MCU[1], rot=POS_MCU[2], datasheet=DS["STM32G431CB"])
# desacoplo (un 100 nF por par VDD/VSS + 4.7 µF)
for i, (x, y) in enumerate([(59.6, 4.6), (68.4, -4.6), (68.4, 4.6), (59.6, -4.6)]):
    C(f"C{10 + i}", "100n", "+3V3", "GND", H2, x=x, y=y, rot=45)
C("C14", "4.7u", "+3V3", "GND", H2, enc="0603", x=58.0, y=-7.0, rot=0)
P(ref="FB1", lib_id="Device:FerriteBead_Small", valor="220Ω@100MHz", huella="Inductor_SMD:L_0603_1608Metric", fabricante="Murata",
  mpn="BLM18PG221SN1D", descripcion="Ferrita 220 Ω a 100 MHz, 1.4 A, 0603 (filtro de VDDA)", hoja=H2, pines={"1": "+3V3", "2": "+3V3A"},
  x=61.0, y=-8.5, rot=0, datasheet=DS["BLM18PG"])
C("C15", "1u", "+3V3A", "GND", H2, x=63.5, y=-8.0, rot=0)
C("C16", "100n", "+3V3A", "GND", H2, x=65.5, y=-8.0, rot=0)
C("C17", "100n", "NRST", "GND", H2, x=57.0, y=2.5, rot=90)
R("R9", "10k", "BOOT0", "GND", H2, x=67.0, y=8.0, rot=0)
P(ref="SW4", lib_id="Switch:SW_Push", valor="RESET", huella="Button_Switch_SMD:SW_SPST_B3U-1000P", fabricante="Omron", mpn="B3U-1000P",
  descripcion="Pulsador táctil SMD 3.0 × 2.5 mm (reinicio)", hoja=H2, pines={"1": "NRST", "2": "GND"}, x=55.0, y=8.0, rot=0,
  datasheet=DS["B3U"])
P(ref="SW2", lib_id="Switch:SW_Push", valor="START", huella="Button_Switch_SMD:SW_SPST_Omron_B3FS-100xP", fabricante="Omron", mpn="B3FS-1000P",
  descripcion="Pulsador táctil SMD 6 × 6 × 3.1 mm (arranque, regla R08)", hoja=H2, pines={"1": "BTN_START", "2": "GND"},
  x=40.0, y=21.0, rot=0, datasheet=DS["B3FS"])
P(ref="SW3", lib_id="Switch:SW_Push", valor="CAL", huella="Button_Switch_SMD:SW_SPST_Omron_B3FS-100xP", fabricante="Omron", mpn="B3FS-1000P",
  descripcion="Pulsador táctil SMD 6 × 6 × 3.1 mm (calibración)", hoja=H2, pines={"1": "BTN_CAL", "2": "GND"},
  x=40.0, y=11.0, rot=0, datasheet=DS["B3FS"])
P(ref="D3", lib_id="Device:LED", valor="OK", huella="LED_SMD:LED_0603_1608Metric", fabricante="Kingbright", mpn="APT1608SGC",
  descripcion="LED verde 0603 (estado)", hoja=H2, pines={"1": "GND", "2": "LED_OK_A"}, x=50.0, y=24.0, rot=180, datasheet=DS["APT1608"])
R("R10", "1k", "LED_OK", "LED_OK_A", H2, x=50.0, y=22.5, rot=0)
P(ref="D4", lib_id="Device:LED", valor="ERR", huella="LED_SMD:LED_0603_1608Metric", fabricante="Kingbright", mpn="APT1608EC",
  descripcion="LED rojo 0603 (falla / batería baja)", hoja=H2, pines={"1": "GND", "2": "LED_ERR_A"}, x=53.5, y=24.0, rot=180,
  datasheet=DS["APT1608"])
R("R11", "1k", "LED_ERR", "LED_ERR_A", H2, x=53.5, y=22.5, rot=0)
# STDC14 (STLINK-V3MINIE): pines 1, 2, 9, 10, 11 sin conexión en el destino (UM2910)
P(ref="J4", lib_id="Connector_Generic:Conn_02x07_Odd_Even", valor="STDC14", huella="Connector_PinHeader_1.27mm:PinHeader_2x07_P1.27mm_Vertical",
  fabricante="Harwin", mpn="M50-3500742", descripcion="Conector 2×7 1.27 mm THT para el cable STDC14 del STLINK-V3MINIE (SWD + puerto serie virtual)",
  hoja=H2, pines={"3": "+3V3", "4": "SWDIO", "5": "GND", "6": "SWCLK", "7": "GND", "8": "SWO_NC", "12": "NRST", "13": "UART_RX", "14": "UART_TX",
                  "1": "STDC_1", "2": "STDC_2", "9": "STDC_9", "10": "STDC_10", "11": "STDC_11"},
  x=74.0, y=14.0, rot=0, datasheet=DS["M50-35"], nc=("1", "2", "8", "9", "10", "11"))

# --------------------------------------------------------------------------------------------- hoja 3: motores y encoders
H3 = "motores"
P(ref="U3", lib_id="Driver_Motor:DRV8833PWP", valor="DRV8833PWPR", huella="Package_SO:HTSSOP-16-1EP_4.4x5mm_P0.65mm_EP3.4x5mm_Mask2.46x2.31mm_ThermalVias",
  fabricante="Texas Instruments", mpn="DRV8833PWPR", descripcion="Puente H doble 2.7-10.8 V, 1.5 A RMS por canal (HTSSOP-16 PowerPAD)", hoja=H3,
  pines={"1": "DRV_SLEEP", "2": "MOT_L_1", "3": "GND", "4": "MOT_L_2", "5": "MOT_R_2", "6": "GND", "7": "MOT_R_1", "8": "DRV_FAULT",
         "9": "PWM_BIN1", "10": "PWM_BIN2", "11": "DRV_VCP", "12": "VBAT_SW", "13": "GND", "14": "DRV_VINT", "15": "PWM_AIN2",
         "16": "PWM_AIN1", "17": "GND"}, x=17.0, y=0.0, rot=90, datasheet=DS["DRV8833"])
C("C20", "10u", "VBAT_SW", "GND", H3, enc="0805", x=17.0, y=5.6, rot=0)
C("C21", "100n", "VBAT_SW", "GND", H3, x=20.0, y=3.0, rot=0)
C("C22", "10n", "DRV_VCP", "VBAT_SW", H3, x=20.0, y=1.5, rot=0)
C("C23", "2.2u", "DRV_VINT", "GND", H3, x=20.0, y=-1.0, rot=0)
R("R12", "10k", "+3V3", "DRV_FAULT", H3, x=13.5, y=-4.0, rot=90)
R("R13", "100k", "DRV_SLEEP", "GND", H3, x=13.5, y=4.0, rot=90)
for lado, ref, y in (("L", "J2", 11.0), ("R", "J3", -11.0)):
    P(ref=ref, lib_id="Connector_Generic_MountingPin:Conn_01x06_MountingPin", valor=f"ENC_{lado}", huella="Connector_JST:JST_SH_BM06B-SRSS-TB_1x06-1MP_P1.00mm_Vertical",
      fabricante="JST", mpn="BM06B-SRSS-TB", descripcion=f"Conector JST SH 6 pines vertical: motor y encoder {'izquierdo' if lado == 'L' else 'derecho'} (cable Pololu #4765)",
      hoja=H3, pines={"1": "GND", "2": f"ENC_{lado}_B", "3": f"ENC_{lado}_A", "4": "+3V3", "5": f"MOT_{lado}_2", "6": f"MOT_{lado}_1",
                      "MP": "GND"}, x=10.5, y=y, rot=90, datasheet=DS["BM06B"])
for i, (red, x, y) in enumerate([("ENC_L_A", 24.0, 9.0), ("ENC_L_B", 25.2, 9.0), ("ENC_R_A", 24.0, -9.0), ("ENC_R_B", 25.2, -9.0)]):
    C(f"C{24 + i}", "1n", red, "GND", H3, x=x, y=y, rot=90)

# --------------------------------------------------------------------------------------------- hoja 4: sensores
H4 = "sensores"
P(ref="Q3", lib_id="Transistor_FET:AO3400A", valor="AO3400A", huella="Package_TO_SOT_SMD:SOT-23", fabricante="Alpha & Omega Semiconductor",
  mpn="AO3400A", descripcion="MOSFET N 30 V 5.7 A SOT-23 (conmuta los 16 emisores, ≈ 0.42 A)", hoja=H4,
  pines={"1": "EMIT_GATE", "2": "GND", "3": "EMIT_K"}, x=84.0, y=6.0, rot=0, datasheet=DS["AO3400A"])
R("R14", "100", "EMIT_G", "EMIT_GATE", H4, x=80.5, y=6.0, rot=0)
R("R15", "100k", "EMIT_GATE", "GND", H4, x=84.0, y=3.6, rot=0)
for i in range(N_SENS):
    xs, ys, ang = G.sensor(i)          # mm y grados (marco del robot)
    a = math.radians(ang)
    r_led = GEO.polar(G.r_resistencias_mm, ang)
    r_pu = GEO.polar(G.r_resistencias_mm - 2.6, ang)
    k = i + 1
    P(ref=f"U{10 + k}", lib_id=f"{LIB_PROPIA}:QRE1113GR", valor="QRE1113GR", huella="OptoDevice:OnSemi_CASE100CY", fabricante="onsemi",
      mpn="QRE1113GR", descripcion=f"Sensor reflectivo IR (LED 940 nm + fototransistor), canal S{k}", hoja=H4,
      pines={"1": "+3V3", "2": f"K{k}", "3": f"S{k}", "4": "GND"}, x=xs, y=ys, rot=ang - 90 + 180, lado="B", datasheet=DS["QRE1113"])
    R(f"R{20 + 2 * i}", "75", f"K{k}", "EMIT_K", H4, enc="0603", x=r_led[0], y=r_led[1], rot=ang, lado="B")
    R(f"R{21 + 2 * i}", "10k", "+3V3", f"S{k}", H4, x=r_pu[0], y=r_pu[1], rot=ang, lado="B")

# --------------------------------------------------------------------------------------------- mecánicos de la PCB
H5 = "mecanica"
for i, (x, y) in enumerate(G.agujeros_soportes_mm()):
    P(ref=f"H{i + 1}", lib_id="Mechanical:MountingHole", valor="M2", huella="MountingHole:MountingHole_2.2mm_M2",
      fabricante="—", mpn="—", descripcion="Agujero M2 sin metalizar (soporte de motor)", hoja=H5, pines={}, x=x, y=y, en_bom=False)
for j, (x, y) in enumerate(G.agujeros_rueda_loca_mm()):
    P(ref=f"H{20 + j}", lib_id="Mechanical:MountingHole", valor="M2", huella="MountingHole:MountingHole_2.2mm_M2",
      fabricante="—", mpn="—", descripcion="Agujero M2 sin metalizar (rueda loca)", hoja=H5, pines={}, x=x, y=y, en_bom=False)
PUNTOS_PRUEBA = [("TP1", "VBAT_SW", 28.0, -8.0), ("TP2", "+3V3", 50.0, -19.0), ("TP3", "GND", 28.0, 8.0), ("TP4", "GND", 74.0, -6.0),
                 ("TP5", "+3V3A", 67.5, -10.5), ("TP6", "EMIT_K", 88.0, 6.0), ("TP7", "S8", 88.0, -6.0), ("TP8", "ENC_L_A", 27.0, 12.0),
                 ("TP9", "ENC_R_A", 27.0, -12.0), ("TP10", "PWM_AIN1", 26.0, 3.0), ("TP11", "VBAT_MED", 57.5, -11.5), ("TP12", "UART_TX", 79.0, 9.0)]
for ref, red, x, y in PUNTOS_PRUEBA:
    P(ref=ref, lib_id="Connector:TestPoint", valor=red, huella="TestPoint:TestPoint_Pad_D1.0mm", fabricante="—", mpn="—",
      descripcion=f"Punto de prueba {red}", hoja=H5, pines={"1": red}, x=x, y=y, en_bom=False)

# --------------------------------------------------------------------------------------------- utilidades
def por_ref():
    return {p.ref: p for p in PARTES}


def redes():
    """red -> [(ref, pin)]"""
    out = {}
    for p in PARTES:
        for pin, red in p.pines.items():
            if pin in p.nc:
                continue
            out.setdefault(red, []).append((p.ref, pin))
    return out


def verificar():
    """Comprobaciones de integridad del diseño (sin KiCad)."""
    err = []
    refs = [p.ref for p in PARTES]
    if len(refs) != len(set(refs)):
        err.append("referencias repetidas")
    for red, nodos in redes().items():
        if len(nodos) < 2 and not red.startswith(("STDC_", "SW_OFF", "SWO_NC")):
            err.append(f"red {red} con un solo nodo {nodos}")
    u1 = por_ref()["U1"]
    usados = {red for red in u1.pines.values()}
    for k in range(1, N_SENS + 1):
        if f"S{k}" not in usados:
            err.append(f"S{k} no llega al MCU")
    return err


if __name__ == "__main__":
    e = verificar()
    print(f"{len(PARTES)} partes, {len(redes())} redes; ADC: {ADC_ASIG}")
    print("ERRORES:", e if e else "ninguno")
    sys.exit(1 if e else 0)
