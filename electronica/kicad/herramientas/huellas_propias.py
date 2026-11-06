#!/usr/bin/env python3.12
"""Huellas propias del robot casero (módulos y piezas que no existen en las bibliotecas de KiCad).

TODAS las medidas son PROVISIONALES: están en docs/pendientes-por-confirmar.md (IDs M01 a M29).
Se crean con pcbnew (Python 3.12). Las pastillas son redondas y grandes (1.8 mm, taladro 0.8 mm) para PCB casera.
Uso: python3.12 huellas_propias.py  -> escribe ../robot_casero.pretty/
"""
import pcbnew
from pathlib import Path

MM = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(MM(x), MM(y))
PAD_D, DRILL = 1.8, 0.8      # pastilla y taladro (broca de 0.8 mm del ticket)


def _huella(nombre, descripcion):
    fp = pcbnew.FOOTPRINT(None)
    fp.SetFPID(pcbnew.LIB_ID("robot_casero", nombre))
    fp.SetReference("REF**")
    fp.SetValue(nombre)
    fp.SetDescription(descripcion)
    return fp


def _pad(fp, numero, x, y, d=PAD_D, taladro=DRILL):
    p = pcbnew.PAD(fp)
    p.SetNumber(str(numero))
    p.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
    p.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
    p.SetSize(V(d, d))
    p.SetDrillSize(V(taladro, taladro))
    p.SetLayerSet(p.PTHMask())
    p.SetPosition(V(x, y))
    p.SetPos0(V(x, y))
    fp.Add(p)


def _linea(fp, x1, y1, x2, y2, capa, ancho=0.15):
    s = pcbnew.FP_SHAPE(fp, pcbnew.SHAPE_T_SEGMENT)
    s.SetLayer(capa)
    s.SetWidth(MM(ancho))
    s.SetStart(V(x1, y1)); s.SetEnd(V(x2, y2))
    s.SetStart0(V(x1, y1)); s.SetEnd0(V(x2, y2))
    fp.Add(s)


def _rect(fp, x1, y1, x2, y2, capa, ancho=0.15):
    for a, b, c, d in [(x1, y1, x2, y1), (x2, y1, x2, y2), (x2, y2, x1, y2), (x1, y2, x1, y1)]:
        _linea(fp, a, b, c, d, capa, ancho)


def _texto(fp, txt, x, y, capa=pcbnew.F_SilkS, tam=1.0):
    t = pcbnew.FP_TEXT(fp)
    t.SetText(txt)
    t.SetLayer(capa)
    t.SetTextSize(V(tam, tam))
    t.SetTextThickness(MM(0.15))
    t.SetPosition(V(x, y)); t.SetPos0(V(x, y))
    fp.Add(t)


def _contorno(fp, x1, y1, x2, y2, aviso):
    _rect(fp, x1, y1, x2, y2, pcbnew.F_SilkS)
    _rect(fp, x1 - 0.3, y1 - 0.3, x2 + 0.3, y2 + 0.3, pcbnew.F_CrtYd, 0.05)
    _texto(fp, aviso, (x1 + x2) / 2, y2 + 1.3, pcbnew.F_Fab, 0.8)


def tcrt5000():
    fp = _huella("TCRT5000_THT", "TCRT5000 suelto. Cuerpo 10.2x5.8 mm (Vishay); patas en linea a 2.54 mm: PROVISIONAL (M18-M20)")
    for i, n in enumerate("AKCE"):
        _pad(fp, n, 0, 2.54 * i)
    _contorno(fp, -2.9, -1.3, 2.9, 8.9, "VERIFICAR M19")
    return fp


def esp32():
    fp = _huella("ESP32_DevKit_38_VERIFICAR",
                 "ESP32 DevKit 38 pines. 19 pines por lado, filas a 25.4 mm, placa 54.4x27.9: PROVISIONAL (M01-M04)")
    for i in range(19):
        _pad(fp, i + 1, 0, 2.54 * i)
        _pad(fp, 38 - i, 25.4, 2.54 * i)
    _contorno(fp, -1.25, -3.0, 26.65, 51.4, "VERIFICAR M01-M04 ESP32")
    _texto(fp, "USB", 12.7, 49.5)
    return fp


def drv8833():
    fp = _huella("Modulo_DRV8833_VERIFICAR", "Modulo DRV8833: orden y medidas SIN FUENTE (M09-M10)")
    for i in range(8):
        _pad(fp, i + 1, 0, 2.54 * i)
    for i in range(4):
        _pad(fp, 9 + i, 15.24, 2.54 * i)
    _contorno(fp, -2.0, -2.0, 17.2, 20.0, "VERIFICAR M09-M10 DRV8833")
    return fp


def mp1584():
    fp = _huella("Modulo_MP1584_VERIFICAR", "Modulo MP1584 22x17x4 mm (sigmanortec); pads: SIN FUENTE (M12-M13)")
    for n, x, y in [(1, 0, 0), (2, 0, 12.7), (3, 19.05, 0), (4, 19.05, 12.7)]:
        _pad(fp, n, x, y)
    _contorno(fp, -1.5, -2.2, 20.5, 14.8, "VERIFICAR M12-M13 MP1584")
    return fp


def ptc():
    fp = _huella("PTC_Radial_VERIFICAR", "Fusible reseteable radial, paso 5 mm SIN FUENTE (M28)")
    _pad(fp, 1, 0, 0)
    _pad(fp, 2, 5.0, 0)
    _contorno(fp, -1.5, -3.0, 6.5, 3.0, "VERIFICAR M28")
    return fp


def mux():
    fp = _huella("Modulo_MUX4067_VERIFICAR",
                 "Modulo 74HC4067 18x41 mm. Canales C0-C15 (pines 9-24) en una columna, control (pines 1-8) en la otra: PROVISIONAL (M16-M17)")
    for i in range(8):
        _pad(fp, 1 + i, 0, 2.54 * i)           # VCC GND S0 S1 S2 S3 SIG EN
    for i in range(16):
        _pad(fp, 9 + i, 15.24, 2.54 * i)       # C0..C15
    _contorno(fp, -1.4, -2.0, 16.64, 39.1, "VERIFICAR M16-M17 MUX")
    return fp


def agujero_m3():
    fp = _huella("AgujeroM3", "Agujero de montaje M3 (3.2 mm)")
    p = pcbnew.PAD(fp)
    p.SetNumber("")
    p.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
    p.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
    p.SetSize(V(3.2, 3.2)); p.SetDrillSize(V(3.2, 3.2))
    ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Mask); ls.AddLayer(pcbnew.B_Mask); p.SetLayerSet(ls)
    p.SetPosition(V(0, 0)); p.SetPos0(V(0, 0))
    fp.Add(p)
    _rect(fp, -2.2, -2.2, 2.2, 2.2, pcbnew.F_CrtYd, 0.05)
    return fp


TODAS = [tcrt5000, esp32, drv8833, mp1584, ptc, mux, agujero_m3]


def escribir_biblioteca(destino):
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    plugin = pcbnew.PCB_PLUGIN() if hasattr(pcbnew, "PCB_PLUGIN") else pcbnew.IO_MGR.PluginFind(pcbnew.IO_MGR.KICAD_SEXP)
    for f in TODAS:
        fp = f()
        plugin.FootprintSave(str(destino), fp)
    return [f().GetFPID().GetLibItemName() for f in TODAS]


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "robot_casero.pretty"
    print("Huellas escritas:", escribir_biblioteca(out))
