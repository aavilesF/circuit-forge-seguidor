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
    fp = _huella("ESP32_DevKit_30",
                 "ESP32 DevKit 30 pines (clon USB-C). Placa 51 x 28 mm, filas a 25.4 mm (Alan midio 25.5 con escalimetro), "
                 "15 pines por lado a 2.54 mm. Por confirmar con vernier (M01-M04)")
    for i in range(15):
        _pad(fp, i + 1, 0, 2.54 * i)
        _pad(fp, 30 - i, 25.4, 2.54 * i)
    # placa de 51 mm: los pines quedan centrados a lo largo (35.56 mm de fila)
    y0 = (35.56 - 51.0) / 2
    _contorno(fp, -1.3, y0, 26.7, y0 + 51.0, "ESP32 30p (M01-M04)")
    _texto(fp, "USB-C", 12.7, y0 + 2.0)
    return fp


def drv8833():
    fp = _huella("Modulo_DRV8833",
                 "Modulo DRV8833 comprado: placa 16 x 18.5 mm (dibujo UNIT, M09). 2 filas de 6 pines a 2.54 mm. "
                 "Separacion entre filas 15.24 mm SIN CONFIRMAR (M32: el dibujo no la acota; probar con plantilla 1:1)")
    for i in range(6):
        _pad(fp, i + 1, 0, 2.54 * i)
        _pad(fp, 7 + i, 15.24, 2.54 * i)
    _contorno(fp, -1.63, -1.65, 16.87, 14.35, "DRV8833 16x18.5 (filas: M32)")
    return fp


def mp1584():
    fp = _huella("Modulo_MP1584",
                 "Modulo MP1584 22 x 16.5 x 4 mm (Alan, escalimetro). OUT a la izquierda, IN a la derecha (M13). "
                 "Posicion exacta de los agujeros por confirmar")
    for n, x, y in [(1, 19.5, 13.5), (2, 19.5, 0), (3, 0, 13.5), (4, 0, 0)]:
        _pad(fp, n, x, y)
    _contorno(fp, -1.25, -1.5, 20.75, 15.0, "MP1584 (M12-M13)")
    _texto(fp, "OUT", 3.0, 6.75)
    _texto(fp, "IN", 16.5, 6.75)
    return fp


def diodo_20mm():
    fp = _huella("D_DO-201AD_P20.32mm_Taladro1.3",
                 "Diodo 1N5822 (DO-201AD) acostado, 20.32 mm entre patas (propuesta O03 para ahorrar espacio). Taladro 1.3 mm")
    _pad(fp, 1, 0, 0, d=2.6, taladro=1.3)
    _pad(fp, 2, 20.32, 0, d=2.6, taladro=1.3)
    _contorno(fp, 5.41, -2.9, 14.91, 2.9, "1N5822 franja=pin1")
    return fp


def hueco_ventilador():
    fp = _huella("Hueco_Ventilador_34mm", "Hueco de 34 mm en la PCB para que el ventilador 4010 saque el aire (sin cobre alrededor)")
    p = pcbnew.PAD(fp)
    p.SetNumber("")
    p.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
    p.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
    p.SetSize(V(34, 34)); p.SetDrillSize(V(34, 34))
    ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Mask); ls.AddLayer(pcbnew.B_Mask); p.SetLayerSet(ls)
    p.SetPosition(V(0, 0)); p.SetPos0(V(0, 0))
    fp.Add(p)
    # 4 agujeros M3 del ventilador (32 mm entre agujeros, típico del 4010; por confirmar M21). El ventilador va sobre
    # 4 separadores de 8 mm, por encima de las piezas bajas que queden cerca del hueco.
    for dx in (-16, 16):
        for dy in (-16, 16):
            h = pcbnew.PAD(fp)
            h.SetNumber("")
            h.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
            h.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
            h.SetSize(V(3.2, 3.2)); h.SetDrillSize(V(3.2, 3.2))
            ls2 = pcbnew.LSET(); ls2.AddLayer(pcbnew.F_Mask); ls2.AddLayer(pcbnew.B_Mask); h.SetLayerSet(ls2)
            h.SetPosition(V(dx, dy)); h.SetPos0(V(dx, dy))
            fp.Add(h)
    _rect(fp, -20, -20, 20, 20, pcbnew.F_SilkS)      # contorno del ventilador 40 x 40
    _rect(fp, -18, -18, 18, 18, pcbnew.F_CrtYd, 0.05)
    return fp


def diodo_largo():
    fp = _huella("D_DO-201AD_P35.56mm_Taladro1.3",
                 "Diodo 1N5822 (DO-201AD) acostado, 35.56 mm entre patas como pidio Alan (M24). "
                 "Las patas del 1N5822 miden ~1.3 mm: taladro de 1.3 mm (la broca de 0.8 no sirve)")
    _pad(fp, 1, 0, 0, d=2.6, taladro=1.3)        # 1 = cátodo (franja)
    _pad(fp, 2, 35.56, 0, d=2.6, taladro=1.3)    # 2 = ánodo
    _contorno(fp, 13.03, -2.9, 22.53, 2.9, "1N5822 franja=pin1")
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


TODAS = [tcrt5000, esp32, drv8833, mp1584, diodo_largo, diodo_20mm, hueco_ventilador, ptc, mux, agujero_m3]


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
