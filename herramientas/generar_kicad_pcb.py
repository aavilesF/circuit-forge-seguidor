#!/usr/bin/env python3
"""Genera la PCB de KiCad (.kicad_pcb) del seguidor de linea a partir del esquema cableado.

Entrada : las mismas redes que el esquema (generar_kicad_cableado.py -> generar_kicad.py -> pines.h).
Salida  : docs/diagramas/kicad_cableado/  (seguidor_cableado.kicad_pcb, seguidor.pretty, fp-lib-table, .kicad_pro, .kicad_sch)
Requiere: KiCad 7 con el modulo de Python `pcbnew`, Java y freerouting.jar (variable FREEROUTING_JAR).

Pasos: huellas propias -> colocacion compacta -> exportar DSN -> Freerouting -> importar SES -> vias de tierra
       -> planos de tierra en las dos caras -> guardar.  Despues se revisa con `kicad-cli pcb drc`.

Todas las dimensiones de MODULOS (ESP32, TB6612, CD74HC4067, bucks, QTR-8A) son supuestos tipicos:
hay que compararlas con las piezas reales antes de mandar a fabricar (ver NOTAS_VERIFICAR al final).
"""
import json
import math
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path

import pcbnew
from pcbnew import FromMM, VECTOR2I

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generar_kicad as base                      # noqa: E402
import generar_kicad_cableado as cab              # noqa: E402

SALIDA = base.RAIZ / "docs" / "diagramas" / "kicad_cableado"
NOMBRE = "seguidor_cableado"
LIB = "seguidor"
JAR = os.environ.get("FREEROUTING_JAR", "/tmp/fr/fr.jar")
TMP = Path(os.environ.get("PCB_TMP", "/tmp/kc/pcb"))

# ------------------------------------------------------------------ reglas de diseno (fabricables en JLCPCB / PCBWay)
CLEARANCE = 0.2
PISTA = 0.25
VIA_D, VIA_TALADRO = 0.6, 0.3
ANCHO = {"potencia": 1.0, "alim": 0.5}
REDES_POTENCIA = ["VBAT", "VBAT_BAT", "VBAT_FUS", "+6V", "MOT_IZQ_1", "MOT_IZQ_2", "MOT_DER_1", "MOT_DER_2"]
REDES_ALIM = ["+5V", "+3V3"]

mm = FromMM


def V(x, y):
    return VECTOR2I(mm(x), mm(y))


# ------------------------------------------------------------------ huellas
class FP:
    """Constructor de huellas con coordenadas en mm y origen en el centro."""

    def __init__(self, nombre, descr, tags=""):
        self.nombre = nombre
        b = pcbnew.BOARD()
        self.fp = pcbnew.FOOTPRINT(b)
        self._b = b
        self.fp.SetFPID(pcbnew.LIB_ID(LIB, nombre))
        self.fp.SetDescription(descr)
        self.fp.SetKeywords(tags)

    def pad_th(self, num, x, y, d=1.0, size=1.8, forma="circle", sx=None, sy=None):
        p = pcbnew.PAD(self.fp)
        p.SetNumber(str(num))
        p.SetShape(pcbnew.PAD_SHAPE_OVAL if forma == "oval" else pcbnew.PAD_SHAPE_CIRCLE)
        p.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        p.SetLayerSet(p.PTHMask())
        p.SetDrillSize(V(d, d))
        p.SetSize(V(sx or size, sy or size))
        p.SetPosition(V(x, y))
        p.SetPos0(V(x, y))
        self.fp.Add(p)
        return p

    def pad_smd(self, num, x, y, w, h):
        p = pcbnew.PAD(self.fp)
        p.SetNumber(str(num))
        p.SetShape(pcbnew.PAD_SHAPE_ROUNDRECT)
        p.SetRoundRectRadiusRatio(0.25)
        p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        p.SetLayerSet(p.SMDMask())
        p.SetSize(V(w, h))
        p.SetPosition(V(x, y))
        p.SetPos0(V(x, y))
        self.fp.Add(p)
        return p

    def pad_npth(self, x, y, d):
        p = pcbnew.PAD(self.fp)
        p.SetNumber("")
        p.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        p.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
        p.SetLayerSet(p.UnplatedHoleMask())
        p.SetDrillSize(V(d, d))
        p.SetSize(V(d, d))
        p.SetPosition(V(x, y))
        p.SetPos0(V(x, y))
        self.fp.Add(p)

    def linea(self, x1, y1, x2, y2, capa=pcbnew.F_SilkS, w=0.15):
        s = pcbnew.FP_SHAPE(self.fp)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(V(x1, y1))
        s.SetEnd(V(x2, y2))
        s.SetStart0(V(x1, y1))
        s.SetEnd0(V(x2, y2))
        s.SetLayer(capa)
        s.SetWidth(mm(w))
        self.fp.Add(s)

    def rect(self, x1, y1, x2, y2, capa=pcbnew.F_SilkS, w=0.15):
        for a, b, c, d in ((x1, y1, x2, y1), (x2, y1, x2, y2), (x2, y2, x1, y2), (x1, y2, x1, y1)):
            self.linea(a, b, c, d, capa, w)

    def circulo(self, x, y, r, capa=pcbnew.F_SilkS, w=0.15):
        s = pcbnew.FP_SHAPE(self.fp)
        s.SetShape(pcbnew.SHAPE_T_CIRCLE)
        s.SetStart(V(x, y))
        s.SetEnd(V(x + r, y))
        s.SetStart0(V(x, y))
        s.SetEnd0(V(x + r, y))
        s.SetLayer(capa)
        s.SetWidth(mm(w))
        self.fp.Add(s)

    def patio(self, x1, y1, x2, y2):
        self.rect(x1, y1, x2, y2, pcbnew.F_CrtYd, 0.05)

    def texto(self, s, x, y, tam=0.8, capa=pcbnew.F_SilkS):
        t = pcbnew.FP_TEXT(self.fp)
        t.SetText(s)
        t.SetPosition(V(x, y))
        t.SetPos0(V(x, y))
        t.SetLayer(capa)
        t.SetTextSize(V(tam, tam))
        t.SetTextThickness(mm(0.12))
        self.fp.Add(t)

    def listo(self):
        self.fp.Reference().SetText("REF**")
        self.fp.Reference().SetLayer(pcbnew.F_SilkS)
        self.fp.Reference().SetTextSize(V(0.8, 0.8))
        self.fp.Reference().SetTextThickness(mm(0.12))
        self.fp.Value().SetText(self.nombre)
        self.fp.Value().SetLayer(pcbnew.F_Fab)
        self.fp.Value().SetVisible(False)
        return self.fp


def pines_de(ref, d):
    """funcion -> numero de pad, segun el simbolo del esquema (misma numeracion)."""
    return {p["name"]: p["num"] for p in d.inst[ref]["sym"].pines}


def fp_esp32(num):
    """ESP32 DevKit de 38 pines (tipo DevKitC): 2 filas de 19, separacion 25.4 mm.  VERIFICAR contra la placa real."""
    f = FP("ESP32_DevKit_38", "ESP32 DevKit 38 pines, filas a 25.4 mm (VERIFICAR con la placa real)", "esp32 devkit")
    izq = ["3V3", "EN", "36", "39", "34", "35", "32", "33", "25", "26", "27", "14", "12", "GND", "13", "9", "10", "11", "VIN"]
    der = ["GND", "23", "22", "1", "3", "21", "GND", "19", "18", "5", "17", "16", "4", "0", "2", "15", "8", "7", "6"]
    for i in range(19):
        y = -22.86 + 2.54 * i
        f.pad_th(num(izq[i]), -12.7, y)
        f.pad_th(num(der[i]), 12.7, y)
    f.rect(-13.97, -27.2, 13.97, 27.2, pcbnew.F_Fab, 0.1)
    f.linea(-13.97, 24.0, 13.97, 24.0, pcbnew.F_Fab, 0.1)
    f.texto("USB", 0, 25.8, 1.0, pcbnew.F_Fab)
    f.circulo(-12.7, -25.0, 0.5)
    # patio solo alrededor de las dos filas de pines: debajo del modulo caben piezas SMD bajas (el modulo va en zocalo)
    f.rect(-14.3, -27.5, -11.2, 27.5, pcbnew.F_CrtYd, 0.05)
    f.rect(11.2, -27.5, 14.3, 27.5, pcbnew.F_CrtYd, 0.05)
    return f.listo()


def fp_columnas(nombre, descr, izq, der, num, sep=15.24, ancho=None, largo=None, extra_texto=""):
    """Modulo con dos columnas de pines a 2.54 mm. izq/der: funciones de arriba hacia abajo."""
    n = len(izq)
    f = FP(nombre, descr)
    y0 = -(n - 1) * 1.27
    for i in range(n):
        f.pad_th(num(izq[i]), -sep / 2, y0 + 2.54 * i)
        f.pad_th(num(der[i]), sep / 2, y0 + 2.54 * i)
    w = (ancho or sep + 5.0) / 2
    h = (largo or (n - 1) * 2.54 + 4.0) / 2
    f.rect(-w, -h, w, h)
    f.circulo(-sep / 2, y0 - 1.9, 0.4)
    f.patio(-w - 0.3, -h - 0.3, w + 0.3, h + 0.3)
    return f.listo()


def fp_cabecera(nombre, descr, funciones, num, paso=2.54, horizontal=True, d=1.0, size=1.8):
    f = FP(nombre, descr)
    n = len(funciones)
    for i, fn in enumerate(funciones):
        c = (-(n - 1) / 2 + i) * paso
        f.pad_th(num(fn), c if horizontal else 0, 0 if horizontal else c, d, size)
    L = (n - 1) * paso / 2 + 1.27
    if horizontal:
        f.rect(-L, -1.27, L, 1.27)
        f.patio(-L, -1.52, L, 1.52)
        f.circulo(-(n - 1) / 2 * paso, -2.0, 0.3)
    else:
        f.rect(-1.27, -L, 1.27, L)
        f.patio(-1.52, -L, 1.52, L)
    return f.listo()


def fp_buck(num):
    """Modulo buck miniatura (tipo MP1584, ~22 x 17 mm) con 4 puntos: IN+ IN- a un lado, OUT+ OUT- al otro. VERIFICAR."""
    f = FP("Buck_modulo_4P", "Modulo buck 4 pads (IN+/IN- | OUT+/OUT-), 19.4 x 12.7 mm entre centros (VERIFICAR)")
    for fn, x, y in (("IN+", -9.652, -6.35), ("IN-", -9.652, 6.35), ("OUT+", 9.652, -6.35), ("OUT-", 9.652, 6.35)):
        f.pad_th(num(fn), x, y, 1.1, 2.0)
    f.rect(-11.4, -8.7, 11.4, 8.7)
    f.circulo(-9.652, -8.0, 0.4)
    f.patio(-11.7, -9.0, 11.7, 9.0)
    return f.listo()


def fp_smd2(nombre, w, h, sep, cw, ch, descr):
    f = FP(nombre, descr)
    f.pad_smd("1", -sep / 2, 0, w, h)
    f.pad_smd("2", sep / 2, 0, w, h)
    f.rect(-cw / 2 + 0.2, -ch / 2 + 0.2, cw / 2 - 0.2, ch / 2 - 0.2, w=0.1)
    f.patio(-cw / 2, -ch / 2, cw / 2, ch / 2)
    return f.listo()


def fp_axial(nombre="R_Axial_P7.62"):
    f = FP(nombre, "Resistencia de 1/4 W con patitas (orificio pasante), paso 7.62 mm")
    f.pad_th("1", -3.81, 0, 0.9, 1.8)
    f.pad_th("2", 3.81, 0, 0.9, 1.8)
    f.rect(-3.15, -1.15, 3.15, 1.15)
    f.patio(-4.9, -1.5, 4.9, 1.5)
    return f.listo()


def fp_ceramico():
    f = FP("C_Radial_P2.54", "Capacitor ceramico/multicapa de patitas, paso 2.54 mm (100 nF)")
    f.pad_th("1", -1.27, 0, 0.9, 1.7)
    f.pad_th("2", 1.27, 0, 0.9, 1.7)
    f.rect(-1.9, -1.2, 1.9, 1.2)
    f.patio(-2.4, -1.3, 2.4, 1.3)
    return f.listo()


def fp_to92(num):
    """TO-92 (patas 1-2-3 de izquierda a derecha, cara plana al frente). Orden tipo 2N7000: 1=S, 2=G, 3=D. VERIFICAR."""
    f = FP("TO-92_MOSFET", "MOSFET N de nivel logico en TO-92 (orden 2N7000: 1=S, 2=G, 3=D; VERIFICAR con la pieza)")
    f.pad_th(num("S"), -2.54, 0, 0.9, 1.7)
    f.pad_th(num("G"), 0, 0, 0.9, 1.7)
    f.pad_th(num("D"), 2.54, 0, 0.9, 1.7)
    f.rect(-2.2, -1.9, 2.2, 1.0, w=0.12)
    f.linea(-2.2, 1.0, 2.2, 1.0)
    f.patio(-3.5, -2.5, 3.5, 2.5)
    return f.listo()


def fp_sot23(num):
    f = FP("SOT-23_MOSFET", "MOSFET N de nivel logico en SOT-23 (1=G, 2=S, 3=D)")
    f.pad_smd(num("G"), -1.016, -0.889, 1.4, 0.65)
    f.pad_smd(num("S"), -1.016, 0.889, 1.4, 0.65)
    f.pad_smd(num("D"), 1.016, 0.0, 1.4, 0.65)
    f.rect(-0.7, -1.5, 0.7, 1.5, w=0.1)
    f.patio(-2.0, -1.8, 2.0, 1.8)
    return f.listo()


def fp_radial(num):
    f = FP("CP_Radial_D6.3_P2.5", "Electrolitico radial 6.3 mm, paso 2.5 mm")
    f.pad_th(num("+"), -1.27, 0, 0.9, 1.7)
    f.pad_th(num("-"), 1.27, 0, 0.9, 1.7)
    f.circulo(0, 0, 3.3)
    f.texto("+", -2.9, -2.9, 0.9)
    f.patio(-3.5, -3.5, 3.5, 3.5)
    return f.listo()


def fp_pptc():
    f = FP("PPTC_radial_P5.08", "Fusible reseteable radial, paso 5.08 mm")
    f.pad_th("1", -2.54, 0, 1.0, 2.0)
    f.pad_th("2", 2.54, 0, 1.0, 2.0)
    f.rect(-4.2, -2.0, 4.2, 2.0)
    f.patio(-4.5, -2.3, 4.5, 2.3)
    return f.listo()


def fp_borne(num):
    f = FP("Borne_2P_P5.0", "Borne/conector de bateria 2 pines, paso 5.0 mm (cambiar por XT30/JST real)")
    f.pad_th(num("-"), -2.54, 0, 1.3, 2.6)
    f.pad_th(num("+"), 2.54, 0, 1.3, 2.6)
    f.rect(-5.0, -3.6, 5.0, 3.6)
    f.texto("-", -2.54, -2.4, 0.9)
    f.texto("+", 2.54, -2.4, 0.9)
    f.patio(-5.3, -3.9, 5.3, 3.9)
    return f.listo()


def fp_tactil():
    f = FP("SW_Tactil_6x6_TH", "Boton tactil 6x6 mm, 4 pines (1-1 y 2-2 unidos)")
    for n_, x, y in (("1", -3.302, -2.286), ("1", -3.302, 2.286), ("2", 3.302, -2.286), ("2", 3.302, 2.286)):
        f.pad_th(n_, x, y, 1.0, 1.8)
    f.rect(-3.0, -3.0, 3.0, 3.0)
    f.circulo(0, 0, 1.7)
    f.patio(-4.4, -3.4, 4.4, 3.4)
    return f.listo()


def fp_agujero(d=2.2):
    f = FP("Agujero_M2", "Agujero de montaje M2")
    f.pad_npth(0, 0, d)
    f.circulo(0, 0, d / 2 + 1.0, w=0.12)
    f.patio(-d / 2 - 1.0, -d / 2 - 1.0, d / 2 + 1.0, d / 2 + 1.0)
    return f.listo()


# ------------------------------------------------------------------ lista de piezas: ref -> (constructor, valor)
def huellas(d):
    # los pads repetidos (tierra) o sin uso usan el numero del pin funcional de su simbolo
    tb = pines_de("U4", d)
    mux = pines_de("U5", d)
    nums_esp = {p["num"] for p in d.inst["U1"]["sym"].pines}
    esp_fn = lambda fn: fn if fn in nums_esp else (f"IO{fn}" if fn.isdigit() else fn)
    out = {}
    out["U1"] = fp_esp32(esp_fn)
    out["U4"] = fp_columnas("TB6612FNG_modulo", "Modulo TB6612FNG 2x8 a 15.24 mm (VERIFICAR orden de pines)",
                            ["PWMA", "AIN2", "AIN1", "STBY", "BIN1", "BIN2", "PWMB", "GND"],
                            ["VM", "VCC", "GND", "AO1", "AO2", "BO2", "BO1", "GND"],
                            lambda fn: tb[fn], 15.24, 20.0, 22.0)
    out["U5"] = fp_columnas("CD74HC4067_modulo", "Modulo CD74HC4067 2x12 a 15.24 mm (VERIFICAR orden de pines)",
                            ["S0", "S1", "S2", "S3", "SIG", "E", "VCC", "GND", "I12", "I13", "I14", "I15"],
                            ["I0", "I1", "I2", "I3", "I4", "I5", "I6", "I7", "I8", "I9", "I10", "I11"],
                            lambda fn: mux[fn], 15.24, 18.0, 31.0)
    q = pines_de("U6", d)
    out["U6"] = fp_cabecera("Cabecera_QTR8A_1x11", "Conector del sensor QTR-8A: OUT1..8, LEDON, GND, VIN (VERIFICAR orden)",
                            [f"OUT{i}" for i in range(1, 9)] + ["EMIT_RTN", "GND", "VCC"], lambda fn: q[fn])
    b2 = pines_de("U2", d)
    out["U2"] = fp_buck(lambda fn: b2[fn])
    out["U3"] = fp_buck(lambda fn: b2[fn])
    out["BT1"] = fp_borne(lambda fn: pines_de("BT1", d)[fn])
    out["F1"] = fp_pptc()
    out["SW1"] = fp_cabecera("Cabecera_2P", "2 pines 2.54 mm (cable al interruptor / motor)", ["1", "2"], lambda fn: fn)
    out["M1"] = fp_cabecera("Cabecera_2P", "2 pines 2.54 mm (cable al interruptor / motor)", ["1", "2"], lambda fn: fn)
    out["M2"] = fp_cabecera("Cabecera_2P", "2 pines 2.54 mm (cable al interruptor / motor)", ["1", "2"], lambda fn: fn)
    out["SW2"] = fp_tactil()
    out["SW3"] = fp_tactil()
    out["RV1"] = fp_cabecera("Cabecera_POT_1x3", "Potenciometro: A, cursor, B (cable o recortador)", ["A", "W", "B"],
                             lambda fn: pines_de("RV1", d)[fn])
    for r in ("R1", "R2", "R3", "R4"):
        out[r] = fp_axial()
    for c in ("C2", "C3", "C4"):
        out[c] = fp_ceramico()
    out["C1"] = fp_radial(lambda fn: pines_de("C1", d)[fn])
    out["Q1"] = fp_to92(lambda fn: pines_de("Q1", d)[fn])
    return out


# ------------------------------------------------------------------ colocacion (mm, origen en la esquina superior izquierda de la placa)
ANCHO_PLACA = 63.5
ALTO_PLACA = 68.58
ORIGEN = (100.0, 60.0)          # donde cae la placa en la hoja de KiCad
CHAFLAN = 2.0

FPNAME = {"U1": "ESP32_DevKit_38", "U4": "TB6612FNG_modulo", "U5": "CD74HC4067_modulo", "U6": "Cabecera_QTR8A_1x11",
          "U2": "Buck_modulo_4P", "U3": "Buck_modulo_4P", "BT1": "Borne_2P_P5.0", "F1": "PPTC_radial_P5.08",
          "SW1": "Cabecera_2P", "M1": "Cabecera_2P", "M2": "Cabecera_2P", "SW2": "SW_Tactil_6x6_TH", "SW3": "SW_Tactil_6x6_TH",
          "RV1": "Cabecera_POT_1x3", "R1": "R_Axial_P7.62", "R2": "R_Axial_P7.62", "R3": "R_Axial_P7.62", "R4": "R_Axial_P7.62",
          "C1": "CP_Radial_D6.3_P2.5", "C2": "C_Radial_P2.54", "C3": "C_Radial_P2.54", "C4": "C_Radial_P2.54", "Q1": "TO-92_MOSFET"}

# ref: (x, y, rotacion antihoraria en grados, cara "F" o "B")
COLOCACION = {
    "U1": (16.51, 43.18, 0, "F"),
    "U5": (44.45, 29.21, 0, "F"),
    "U4": (44.45, 57.15, 0, "F"),
    "U6": (44.45, 2.54, 0, "F"),
    "BT1": (10.16, 3.81, 0, "F"),
    "F1": (24.13, 3.81, 0, "F"),
    "SW1": (60.96, 6.35, 270, "F"),
    "SW2": (10.16, 11.43, 0, "F"),
    "SW3": (21.59, 11.43, 0, "F"),
    "RV1": (31.75, 11.43, 0, "F"),
    "C1": (59.69, 41.91, 0, "F"),
    "C2": (57.15, 52.07, 90, "F"),
    "C3": (32.77, 31.75, 90, "F"),
    "C4": (55.88, 6.35, 0, "F"),
    "M1": (60.96, 57.15, 270, "F"),
    "M2": (60.96, 62.23, 90, "F"),
    "R1": (16.51, 24.13, 0, "F"),
    "R2": (16.51, 29.21, 0, "F"),
    "R3": (13.97, 50.8, 0, "F"),
    "R4": (16.51, 54.61, 0, "F"),
    "Q1": (16.51, 59.69, 0, "F"),
    "U2": (16.51, 29.21, 90, "B"),
    "U3": (16.51, 54.61, 90, "B"),
}
AGUJEROS = [(2.54, 12.7), (60.96, 24.13), (57.15, 66.04)]


# ------------------------------------------------------------------ lectura del esquema (valores y uuid de cada simbolo)
def datos_esquema():
    arbol = base.leer_sexp((SALIDA / f"{NOMBRE}.kicad_sch").read_text(encoding="utf-8"))
    out = {}
    for s in base.hijos(arbol, "symbol"):
        props = {pr[1]: pr[2] for pr in base.hijos(s, "property")}
        out[props["Reference"]] = dict(valor=props["Value"], uuid=base.hijo(s, "uuid")[1])
    return out


# ------------------------------------------------------------------ placa
def contorno(w, h, c):
    return [(c, 0), (w - c, 0), (w, c), (w, h - c), (w - c, h), (c, h), (0, h - c), (0, c)]


def construir_placa(d, huell, esq):
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(2)
    ds = board.GetDesignSettings()
    ds.m_TrackMinWidth = mm(0.2)
    ds.m_ViasMinSize = mm(0.5)
    ds.m_MinThroughDrill = mm(0.3)
    ds.m_CopperEdgeClearance = mm(0.3)
    nc = ds.m_NetSettings.m_DefaultNetClass
    nc.SetClearance(mm(CLEARANCE))
    nc.SetTrackWidth(mm(PISTA))
    nc.SetViaDiameter(mm(VIA_D))
    nc.SetViaDrill(mm(VIA_TALADRO))

    nets = {}
    for red in d.spec:
        ni = pcbnew.NETINFO_ITEM(board, red)
        board.Add(ni)
        nets[red] = ni
    pad_red = {}
    for red, pins in d.spec.items():
        for ref, nombre in pins:
            pad_red[(ref, pines_de(ref, d)[nombre])] = red

    ox, oy = ORIGEN
    usados = set()
    for ref, (x, y, rot, cara) in COLOCACION.items():
        f = huell[ref]
        assert f.GetFPID().GetLibItemName() == FPNAME[ref], (ref, f.GetFPID().GetLibItemName())
        f.SetReference(ref)
        f.SetValue(esq[ref]["valor"])
        f.Reference().SetVisible(True)
        for pad in f.Pads():
            red = pad_red.get((ref, pad.GetNumber()))
            if red:
                pad.SetNet(nets[red])
                usados.add((ref, pad.GetNumber()))
                if red == "GND" and ref in ("BT1", "U2", "U3", "C1", "U4"):
                    pad.SetZoneConnection(pcbnew.ZONE_CONNECTION_FULL)     # corriente alta: union solida al plano, sin spokes
        f.SetOrientationDegrees(rot)
        f.SetPosition(V(ox + x, oy + y))
        if cara == "B":
            f.Flip(f.GetPosition(), True)
        f.SetPath(pcbnew.KIID_PATH("/" + esq[ref]["uuid"]))
        board.Add(f)
    faltan = set(pad_red) - usados
    assert not faltan, f"pads sin huella: {sorted(faltan)}"

    for i, (x, y) in enumerate(AGUJEROS, 1):
        h = fp_agujero()
        h.SetReference(f"H{i}")
        h.Reference().SetVisible(False)
        h.SetPosition(V(ox + x, oy + y))
        board.Add(h)

    pts = contorno(ANCHO_PLACA, ALTO_PLACA, CHAFLAN)
    for a, b in zip(pts, pts[1:] + pts[:1]):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(V(ox + a[0], oy + a[1]))
        s.SetEnd(V(ox + b[0], oy + b[1]))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(mm(0.1))
        board.Add(s)
    return board, nets


def guardar(board, ruta):
    pcbnew.SaveBoard(str(ruta), board)


# ------------------------------------------------------------------ ruteo
import ruteador_pcb as rp  # noqa: E402


def a_mm(v):
    return pcbnew.ToMM(v)


def extraer_pads(board):
    ox, oy = ORIGEN
    out = []
    for f in board.GetFootprints():
        for p in f.Pads():
            bb = p.GetBoundingBox()
            x0, y0 = a_mm(bb.GetX()) - ox, a_mm(bb.GetY()) - oy
            x1, y1 = x0 + a_mm(bb.GetWidth()), y0 + a_mm(bb.GetHeight())
            red = p.GetNetname() or None
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                out.append(rp.Pad(None, x0, y0, x1, y1, True, (), a_mm(p.GetDrillSize().x)))
                continue
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                capas = (0, 1)
            else:
                capas = (0,) if p.IsOnLayer(pcbnew.F_Cu) else (1,)
            circ = p.GetShape() == pcbnew.PAD_SHAPE_CIRCLE
            out.append(rp.Pad(red, x0, y0, x1, y1, circ, capas, a_mm(p.GetDrillSize().x)))
    return out


def ancho_de(red):
    if red in REDES_POTENCIA:
        return ANCHO["potencia"]
    if red in REDES_ALIM:
        return ANCHO["alim"]
    return PISTA


def rutear(board, d):
    pads = extraer_pads(board)
    reglas = rp.Reglas(separacion=CLEARANCE, borde=0.3, via_d=VIA_D, via_taladro=VIA_TALADRO,
                       ancho={r: ancho_de(r) for r in d.spec}, ancho_def=PISTA)
    poli = contorno(ANCHO_PLACA, ALTO_PLACA, CHAFLAN)
    r = rp.Ruteador(ANCHO_PLACA, ALTO_PLACA, poli, pads, reglas)

    # 1) tierra: los pads SMD de GND bajan con una via corta al plano inferior; los pasantes ya tocan los dos planos
    for p in pads:
        if p.net == "GND" and p.capas == (0,):
            ruta = r.via_cerca("GND", p.cx, p.cy, 0)
            assert ruta, f"sin via de tierra para el pad en ({p.cx:.2f}, {p.cy:.2f})"
            r._anota_ruta("GND", ruta, PISTA)

    # 2) potencia, alimentacion y senales (las mas cortas primero)
    def tam(red):
        ps = [p for p in pads if p.net == red]
        xs = [p.cx for p in ps]
        ys = [p.cy for p in ps]
        return (max(xs) - min(xs)) + (max(ys) - min(ys))

    redes = [x for x in d.spec if x != "GND"]
    orden = [x for x in REDES_POTENCIA if x in redes] + [x for x in REDES_ALIM if x in redes]
    orden += sorted([x for x in redes if x not in orden], key=tam)
    fallos = r.rutear(orden)
    return r, fallos


def escribir_pistas(board, r, nets):
    ox, oy = ORIGEN
    for red, capa, x0, y0, x1, y1, w in r.segmentos:
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(V(ox + x0, oy + y0))
        t.SetEnd(V(ox + x1, oy + y1))
        t.SetWidth(mm(w))
        t.SetLayer(pcbnew.F_Cu if capa == 0 else pcbnew.B_Cu)
        t.SetNet(nets[red])
        board.Add(t)
    for red, x, y in r.vias:
        v = pcbnew.PCB_VIA(board)
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetPosition(V(ox + x, oy + y))
        v.SetWidth(mm(VIA_D))
        v.SetDrill(mm(VIA_TALADRO))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(nets[red])
        board.Add(v)


def planos(board, nets):
    ox, oy = ORIGEN
    ins = 0.45
    pts = contorno(ANCHO_PLACA - 2 * ins, ALTO_PLACA - 2 * ins, CHAFLAN + 0.3)
    for capa in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        z.SetLayer(capa)
        z.SetNet(nets["GND"])
        z.SetMinThickness(mm(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetThermalReliefGap(mm(0.25))
        z.SetThermalReliefSpokeWidth(mm(0.4))
        z.SetLocalClearance(mm(0.25))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        ol = z.Outline()
        ol.NewOutline()
        for x, y in pts:
            ol.Append(mm(ox + ins + x), mm(oy + ins + y))
        board.Add(z)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())


def rotulos(board):
    """textos de la serigrafia de la placa."""
    ox, oy = ORIGEN
    for txt, x, y in (("SEGUIDOR  v0.1", 31.75, 67.0), ("QTR-8A", 44.45, 5.2), ("BAT", 17.5, 2.8),
                      ("MOT IZQ", 56.4, 57.15), ("MOT DER", 56.4, 62.23), ("SW", 57.9, 9.3)):
        t = pcbnew.PCB_TEXT(board)
        t.SetText(txt)
        t.SetPosition(V(ox + x, oy + y))
        t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(V(0.8, 0.8))
        t.SetTextThickness(mm(0.13))
        board.Add(t)


# ------------------------------------------------------------------ archivos del proyecto
def escribir_biblioteca(d):
    pretty = SALIDA / f"{LIB}.pretty"
    pretty.mkdir(exist_ok=True)
    plugin = pcbnew.IO_MGR.PluginFind(pcbnew.IO_MGR.KICAD_SEXP)
    for f in [*huellas(d).values(), fp_agujero()]:
        f.SetPosition(V(0, 0))
        plugin.FootprintSave(str(pretty), f)
    (SALIDA / "fp-lib-table").write_text(
        f'(fp_lib_table\n  (version 7)\n  (lib (name "{LIB}")(type "KiCad")(uri "${{KIPRJMOD}}/{LIB}.pretty")(options "")'
        f'(descr "Huellas del seguidor de linea"))\n)\n', encoding="utf-8")


def escribir_proyecto():
    pro = {
        "meta": {"filename": f"{NOMBRE}.kicad_pro", "version": 1},
        "board": {"design_settings": {"rules": {"min_clearance": CLEARANCE, "min_track_width": 0.2, "min_via_diameter": 0.5,
                                                "min_through_hole_diameter": 0.3, "min_copper_edge_clearance": 0.3, "min_resolved_spokes": 1}}},
        "net_settings": {
            "classes": [
                {"name": "Default", "clearance": CLEARANCE, "track_width": PISTA, "via_diameter": VIA_D, "via_drill": VIA_TALADRO},
                {"name": "Potencia", "clearance": CLEARANCE, "track_width": ANCHO["potencia"], "via_diameter": VIA_D, "via_drill": VIA_TALADRO},
                {"name": "Alim", "clearance": CLEARANCE, "track_width": ANCHO["alim"], "via_diameter": VIA_D, "via_drill": VIA_TALADRO},
            ],
            "meta": {"version": 3},
            "netclass_patterns": [{"netclass": "Potencia", "pattern": x} for x in REDES_POTENCIA]
            + [{"netclass": "Alim", "pattern": x} for x in REDES_ALIM],
        },
    }
    (SALIDA / f"{NOMBRE}.kicad_pro").write_text(json.dumps(pro, indent=2), encoding="utf-8")


def main():
    SALIDA.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    cab.HUELLAS_ESQ = {ref: f"{LIB}:{n}" for ref, n in FPNAME.items()}
    d, _ = cab.construir()
    cab.escribir_y_verificar(d)                    # regenera el esquema con el campo Footprint
    esq = datos_esquema()
    huell = huellas(d)
    assert set(huell) == set(FPNAME) == set(COLOCACION), set(FPNAME) ^ set(COLOCACION)
    board, nets = construir_placa(d, huell, esq)
    guardar(board, TMP / "sin_rutear.kicad_pcb")
    r, fallos = rutear(board, d)
    print(f"ruteo: {len(r.segmentos)} tramos, {len(r.vias)} vias, fallos: {fallos or 'ninguno'}")
    escribir_pistas(board, r, nets)
    guardar(board, TMP / "pistas.kicad_pcb")
    board = pcbnew.LoadBoard(str(TMP / "pistas.kicad_pcb"))     # el relleno de zonas solo funciona con una placa cargada de archivo
    nets = {n: board.FindNet(n) for n in d.spec}
    planos(board, nets)
    rotulos(board)
    guardar(board, TMP / "ruteada.kicad_pcb")
    if not fallos:
        guardar(board, SALIDA / f"{NOMBRE}.kicad_pcb")
        escribir_biblioteca(d)
        escribir_proyecto()
        print("PCB escrita en", SALIDA.relative_to(base.RAIZ))
    return fallos


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
