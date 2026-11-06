#!/usr/bin/env python3.12
"""Genera la PCB (casera, una cara) a partir de la netlist del esquemático.

Pasos: netlist (kicad-cli) -> placa con huellas colocadas -> ruteo con Freerouting -> DRC con pcbnew.
Reglas de PCB casera: pistas 0.8 mm, separación 0.5 mm, pastillas redondas, taladro 0.8 mm.
Las pistas de la cara SUPERIOR (F.Cu) son PUENTES DE ALAMBRE: no se graban en la placa; se sueldan por las vías.
TODAS las medidas de módulos son PROVISIONALES (docs/pendientes-por-confirmar.md).
Uso: python3.12 generar_pcb.py barra_sensores|principal [--sin-ruteo]
"""
import json
import math
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pcbnew

RAIZ = Path(__file__).resolve().parent.parent
MM = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(MM(x), MM(y))
FREEROUTING = Path("/tmp/fr/fr.jar")

REGLAS = dict(clearance=0.5, pista=0.8, via_d=1.6, via_taladro=0.8)


def proyecto_json(nombre):
    return {
        "meta": {"filename": f"{nombre}.kicad_pro", "version": 1},
        "board": {"design_settings": {"rules": {
            "min_clearance": 0.5, "min_track_width": 0.8, "min_via_diameter": 1.4,
            "min_through_hole_diameter": 0.7, "min_via_annular_width": 0.3,
            "min_copper_edge_clearance": 0.5, "min_hole_to_hole": 0.5, "min_hole_clearance": 0.25,
            "min_resolved_spokes": 1}}},
        "net_settings": {"classes": [{
            "name": "Default", "clearance": REGLAS["clearance"], "track_width": REGLAS["pista"],
            "via_diameter": REGLAS["via_d"], "via_drill": REGLAS["via_taladro"],
            "diff_pair_width": 0.8, "diff_pair_gap": 0.5, "diff_pair_via_gap": 0.5,
            "microvia_diameter": 0.3, "microvia_drill": 0.1, "pcb_color": "rgba(0, 0, 0, 0.000)",
            "schematic_color": "rgba(0, 0, 0, 0.000)", "wire_width": 6, "bus_width": 12,
            "line_style": 0}], "meta": {"version": 3}}}


def leer_netlist(sch):
    xml = Path("/tmp") / (sch.stem + "_pcb.xml")
    r = subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "-o", str(xml), str(sch)],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit("kicad-cli falló: " + r.stderr)
    raiz = ET.parse(xml).getroot()
    comps = {}
    for c in raiz.find("components"):
        fp = c.find("footprint")
        comps[c.get("ref")] = (c.find("value").text, fp.text if fp is not None else "")
    nets = {}
    for n in raiz.find("nets"):
        nodos = [(x.get("ref"), x.get("pin")) for x in n.findall("node")]
        nets[n.get("name")] = nodos
    return comps, nets


def cargar_huella(nombre):
    lib, fp = nombre.split(":")
    ruta = RAIZ / "robot_casero.pretty" if lib == "robot_casero" else Path(f"/usr/share/kicad/footprints/{lib}.pretty")
    f = pcbnew.FootprintLoad(str(ruta), fp)
    if f is None:
        sys.exit(f"No encuentro la huella {nombre}")
    f.SetFPID(pcbnew.LIB_ID(lib, fp))
    return f


# ---------------------------------------------------------------- colocación (x, y, rotación) del PIN 1 / origen de la huella
def colocacion_barra():
    """12 sensores en arco (R = 110 mm); detrás, dos filas de resistencias (330 y 10k); módulo del multiplexor y conector atrás."""
    cx, R, y0 = 50.0, 110.0, 14.0
    cy = y0 + R
    pos = {}
    for i in range(12):
        th = (i - 5.5) * 7.5 / R                     # ángulo respecto al centro (rad)
        px, py = cx + R * math.sin(th), cy - R * math.cos(th)
        fi = -math.degrees(th)                        # giro de la huella
        fr = math.radians(fi)
        ox, oy = px - 3.81 * math.sin(fr), py - 3.81 * math.cos(fr)   # origen = pin A
        pos[f"OP{i + 1}"] = (ox, oy, fi)
        xr = cx + (i - 5.5) * 7.5
        pos[f"R{i + 1}"] = (xr, 38.54, 180)           # R del LED: pin 2 (LEDA) arriba, pin 1 (+3V3) abajo
        pos[f"R{13 + i}"] = (xr, 46.0, 0)             # R de carga: pin 1 (SEN) arriba, pin 2 (+3V3) abajo
    pos["U1"] = (cx - 20.32, 62.0 + 15.24, 90)         # canales al frente, mando atrás
    pos["J1"] = (cx - 9.0, 86.0, 90)
    pos["C1"] = (cx + 24.0, 60.0, 0)
    pos["C2"] = (cx + 24.0, 67.0, 0)
    pos["R25"] = (cx + 30.0, 74.0, 0)
    pos["Q1"] = (cx + 36.0, 76.0, 0)
    huecos = [(10, 58), (90, 58), (10, 84), (90, 84)]
    return pos, (3.0, 8.0, 97.0, 90.0), huecos


def colocacion_principal():
    pos = {
        "J5": (22, 6, 90), "A1": (31, 16, 0), "U3": (60.5, 16, 0),
        "U1": (6, 16, 0), "U2": (6, 36, 0), "D2": (6, 54, 0),
        "J1": (6, 62, 0), "F1": (12, 62, 0), "SW1": (22, 62, 0), "C1": (6, 72, 0), "C2": (20, 72, 0),
        "R1": (6, 80, 0), "R2": (6, 85, 0), "C3": (6, 90, 0),
        "SW2": (32, 74, 0), "SW3": (32, 84, 0), "SW4": (46, 74, 0),
        "J2": (62, 40, 0), "J3": (68, 40, 0), "J4": (74, 40, 0),
        "C4": (60, 47, 0), "C5": (68, 47, 0),
        "Q1": (60, 54, 0), "R4": (60, 60, 0), "R5": (60, 65, 0), "D1": (60, 70, 0), "R3": (60, 76, 0),
    }
    huecos = [(6, 6), (74, 6), (6, 90), (74, 90)]
    return pos, (2.0, 2.0, 78.0, 94.0), huecos


DISENOS = {"barra_sensores": colocacion_barra, "principal": colocacion_principal}


def construir(nombre, carpeta):
    sch = carpeta / f"{nombre}.kicad_sch"
    comps, nets = leer_netlist(sch)
    pos, (bx1, by1, bx2, by2), huecos = DISENOS[nombre]()
    faltan = set(comps) - set(pos)
    if faltan:
        sys.exit(f"Sin posición: {sorted(faltan)}")
    b = pcbnew.BOARD()
    # nets
    info = {}
    for n, nodos in nets.items():
        if len(nodos) < 2:
            continue
        ni = pcbnew.NETINFO_ITEM(b, n)
        b.Add(ni)
        info[n] = ni
    pad_net = {}
    for n, nodos in nets.items():
        if n in info:
            for ref, pin in nodos:
                pad_net[(ref, pin)] = info[n]
    for ref, (valor, fpn) in comps.items():
        fp = cargar_huella(fpn)
        fp.SetReference(ref)
        fp.SetValue(valor)
        x, y, rot = pos[ref]
        fp.SetPosition(V(x, y))
        fp.SetOrientationDegrees(rot)
        for pad in fp.Pads():
            ni = pad_net.get((ref, pad.GetNumber()))
            if ni:
                pad.SetNet(ni)
        fp.Reference().SetTextSize(V(1.0, 1.0))
        fp.Reference().SetLayer(pcbnew.F_SilkS)
        fp.Value().SetLayer(pcbnew.F_Fab)
        b.Add(fp)
    # contorno
    for a, c, d, e in [(bx1, by1, bx2, by1), (bx2, by1, bx2, by2), (bx2, by2, bx1, by2), (bx1, by2, bx1, by1)]:
        s = pcbnew.PCB_SHAPE(b)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(MM(0.1))
        s.SetStart(V(a, c)); s.SetEnd(V(d, e))
        b.Add(s)
    # agujeros de montaje M3 en las esquinas
    for k, (hx, hy) in enumerate(huecos):
        h = cargar_huella("robot_casero:AgujeroM3")
        h.SetReference(f"H{k + 1}")
        h.Reference().SetLayer(pcbnew.F_Fab)
        h.SetPosition(V(hx, hy))
        b.Add(h)
    # reglas del diseño
    ds = b.GetDesignSettings()
    ds.SetCopperLayerCount(2)
    nc = ds.m_NetSettings.m_DefaultNetClass
    nc.SetClearance(MM(REGLAS["clearance"])); nc.SetTrackWidth(MM(REGLAS["pista"]))
    nc.SetViaDiameter(MM(REGLAS["via_d"])); nc.SetViaDrill(MM(REGLAS["via_taladro"]))
    # título
    t = pcbnew.PCB_TEXT(b)
    t.SetText(f"{nombre} - robot casero - PROVISIONAL (medidas por confirmar) - 5 nov 2026")
    t.SetLayer(pcbnew.F_SilkS); t.SetTextSize(V(1.0, 1.0)); t.SetPosition(V(bx1 + 40, by2 - 3.0))
    b.Add(t)
    (carpeta / f"{nombre}.kicad_pro").write_text(json.dumps(proyecto_json(nombre), indent=2))
    libs = ["Resistor_THT", "Capacitor_THT", "Diode_THT", "Package_TO_SOT_THT", "Connector_PinHeader_2.54mm", "Button_Switch_THT"]
    tabla = ['(fp_lib_table', '  (version 7)',
             '  (lib (name "robot_casero")(type "KiCad")(uri "${KIPRJMOD}/../robot_casero.pretty")(options "")'
             '(descr "Huellas propias del robot casero (medidas provisionales)"))']
    for l in libs:
        tabla.append(f'  (lib (name "{l}")(type "KiCad")(uri "${{KICAD7_FOOTPRINT_DIR}}/{l}.pretty")(options "")(descr "Biblioteca estandar de KiCad"))')
    (carpeta / "fp-lib-table").write_text("\n".join(tabla) + "\n)\n")
    (carpeta / f"{nombre}_mecanica.json").write_text(json.dumps(
        {"contorno_mm": [bx1, by1, bx2, by2], "agujeros_m3_mm": huecos,
         "nota": "Coordenadas de la PCB (x derecha, y hacia atrás). Las usa mecanica/autocad/generar_dxf.py"}, indent=1))
    ruta = carpeta / f"{nombre}.kicad_pcb"
    pcbnew.SaveBoard(str(ruta), b)
    return ruta


def rutear(ruta):
    """Enrutador propio (herramientas/ruteador.py): sin programas externos."""
    from ruteador import Ruteador
    b = pcbnew.LoadBoard(str(ruta))
    r = Ruteador(b, **REGLAS)
    res = r.correr()
    print("Ruteo:", res)
    pcbnew.SaveBoard(str(ruta), b)
    return res


def drc(ruta):
    b = pcbnew.LoadBoard(str(ruta))
    inf = ruta.with_name(ruta.stem + "_drc.rpt")
    pcbnew.WriteDRCReport(b, str(inf), pcbnew.EDA_UNITS_MILLIMETRES, True)
    return inf


if __name__ == "__main__":
    nombre = sys.argv[1]
    carpeta = RAIZ / nombre
    ruta = construir(nombre, carpeta)
    print("Placa creada:", ruta)
    if "--sin-ruteo" not in sys.argv:
        rutear(ruta)
    print("Informe DRC:", drc(ruta))
