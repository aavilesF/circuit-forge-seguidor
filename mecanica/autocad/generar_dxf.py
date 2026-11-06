#!/usr/bin/env python3
"""Genera los DXF 2D de la placa plana en "T" del robot casero (AutoCAD, milímetros) desde parametros.yaml.

Un DXF por material (acrilico y mdf para láser, pla para impresión 3D): cambian el espesor y la compensación de agujeros.
Ejes: origen en el centro del eje de las ruedas, X al frente, Y a la izquierda.
Los agujeros de las PCB salen de electronica/kicad/*/*_mecanica.json (misma fuente de verdad que la PCB).
Medidas por confirmar: docs/pendientes-por-confirmar.md. NO cortar antes de confirmarlas.
Uso: python3 generar_dxf.py
"""
import json
import math
from pathlib import Path

import ezdxf
import yaml
from ezdxf import units

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
CAPAS = [("CORTE", 1, "CONTINUOUS"), ("GRABADO", 5, "CONTINUOUS"), ("TALADROS", 3, "CONTINUOUS"),
         ("REFERENCIA", 8, "DASHED"), ("COTAS", 2, "CONTINUOUS"),
         ("PIEZAS_FANTASMA", 6, "DASHED"),           # arriba de la placa (PCB principal)
         ("PIEZAS_FANTASMA_ABAJO", 4, "DASHED"),     # debajo (motores, ruedas, rueda loca, placa de sensores)
         ("PIEZAS_FANTASMA_ENTRE", 30, "DASHED")]    # entre la placa y la PCB principal (batería, ventilador)
MATERIALES = ["acrilico", "mdf", "pla"]


def val(d):
    if isinstance(d, dict):
        return d.get("valor", d.get("mm"))
    return d


def contorno_placa(P):
    """Contorno en T: base trasera con muescas para las ruedas, espina y travesaño delantero."""
    ch, R = P["chasis"], P["ruedas_y_motores"]
    b, e, t, c = ch["base"], ch["espina"], ch["travesano"], ch["chaflan_mm"]
    nx, ny = R["muesca_rueda_medio_largo_mm"], R["muesca_rueda_y_interior_mm"]
    hb, he, ht = b["medio_ancho"], e["medio_ancho"], t["medio_ancho"]
    der = [  # lado derecho (y negativa), de atrás hacia adelante
        (b["x1"] + c, -hb), (-nx, -hb), (-nx, -ny), (nx, -ny), (nx, -hb), (b["x2"], -hb), (b["x2"], -he),
        (t["x1"], -he), (t["x1"], -ht), (t["x2"] - c, -ht), (t["x2"], -ht + c)]
    izq = [(x, -y) for x, y in reversed(der)]
    return der + izq + [(b["x1"], hb - c), (b["x1"], -hb + c)]


def pcb_a_placa(pcb, x_frente, x, y):
    """(x, y) de la PCB (x derecha, y hacia atrás, vista desde arriba) -> (X frente, Y izquierda) de la placa."""
    bx1, by1, bx2, by2 = pcb["contorno_mm"]
    return x_frente - (y - by1), -(x - (bx1 + bx2) / 2)


def rect(cx, cy, dx, dy):
    return [(cx - dx / 2, cy - dy / 2), (cx + dx / 2, cy - dy / 2), (cx + dx / 2, cy + dy / 2), (cx - dx / 2, cy + dy / 2)]


def area(pts):
    return abs(sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))) / 2


def datos():
    P = yaml.safe_load(open(AQUI / "parametros.yaml"))
    pr = json.load(open(RAIZ / "electronica/kicad/principal/principal_mecanica.json"))
    se = json.load(open(RAIZ / "electronica/kicad/sensores/sensores_mecanica.json"))
    return P, pr, se


def geometria(P, pr, se):
    """Devuelve todo lo que se dibuja, en una estructura que también usa generar_3d.py."""
    ch, R, M = P["chasis"], P["ruedas_y_motores"], P["modulos"]
    g = {"contorno": contorno_placa(P), "agujeros": [], "ranuras": [], "huecos": [], "fantasmas": []}
    d_m3 = ch["agujero_tornillo_m3_mm"]
    for nombre, pcb, xf, capa in (("PCB principal", pr, P["pcbs"]["principal"]["x_frente_mm"], "PIEZAS_FANTASMA"),
                                  ("Placa de sensores", se, P["pcbs"]["sensores"]["x_frente_mm"], "PIEZAS_FANTASMA_ABAJO")):
        for hx, hy in pcb["agujeros_m3_mm"]:
            g["agujeros"].append((*pcb_a_placa(pcb, xf, hx, hy), d_m3, nombre))
        bx1, by1, bx2, by2 = pcb["contorno_mm"]
        g["fantasmas"].append((capa, nombre, [pcb_a_placa(pcb, xf, x, y) for x, y in ((bx1, by1), (bx2, by1), (bx2, by2), (bx1, by2))]))
    V = M["ventilador_4010"]
    fx, s = V["x_centro_mm"], V["separacion_agujeros_mm"] / 2
    g["huecos"].append((fx, 0, V["hueco_mm"], "ventilador"))
    for dx in (-s, s):
        for dy in (-s, s):
            g["agujeros"].append((fx + dx, dy, V["agujero_mm"], "ventilador"))
    g["fantasmas"].append(("PIEZAS_FANTASMA_ENTRE", "Ventilador 4010", rect(fx, 0, V["lado_mm"], V["lado_mm"])))
    mw, ml, eje = val(R["motor_ancho_mm"]), val(R["motor_largo_mm"]), val(R["eje_largo_mm"])
    ye = R["cara_exterior_llanta_y_mm"]
    la = R["llanta_ancho"]["mm"]
    yc = ye - la - 0.5                                    # cara del reductor
    sl, sa = R["cincho_slot_mm"]["largo"], R["cincho_slot_mm"]["ancho"]
    for lado in (1, -1):
        g["fantasmas"].append(("PIEZAS_FANTASMA_ABAJO", "Motor N20", rect(0, lado * (yc - ml / 2), mw, ml)))
        g["fantasmas"].append(("PIEZAS_FANTASMA_ABAJO", "Rueda", rect(0, lado * (ye - la / 2), R["llanta_diametro"]["mm"], la)))
        for yy in (yc - 5, yc - ml + 5):
            for xx in (-mw / 2 - 2.5, mw / 2 + 2.5):
                g["ranuras"].append((xx, lado * yy, sa, sl))
    L = M["lipo_2s"]
    g["fantasmas"].append(("PIEZAS_FANTASMA_ENTRE", "LiPo 2S", rect(L["x_centro_mm"], 0, L["ancho_mm"], L["largo_mm"])))
    for yy in (-21, 21):
        for xx in (L["x_centro_mm"] - L["ancho_mm"] / 2 - 2.5, L["x_centro_mm"] + L["ancho_mm"] / 2 + 2.5):
            g["ranuras"].append((xx, yy, sa, sl))
    rl = R["rueda_loca"]
    for dy in (-rl["sep_tornillos_mm"] / 2, rl["sep_tornillos_mm"] / 2):
        g["agujeros"].append((rl["x_mm"], dy, rl["diametro_tornillo_mm"], "rueda loca"))
    g["fantasmas"].append(("PIEZAS_FANTASMA_ABAJO", "Rueda loca", rect(rl["x_mm"], 0, 10, rl["sep_tornillos_mm"] + 6)))
    return g


def generar(material, P, pr, se):
    ch = P["chasis"]
    esp = ch["espesor_mm"][material]
    kerf, hol = ch["kerf_laser_mm"]["valor"], ch["holgura_fdm_mm"]["valor"]
    comp = -kerf if material in ("acrilico", "mdf") else +hol
    g = geometria(P, pr, se)
    doc = ezdxf.new("R2010", setup=True)
    doc.units = units.MM
    doc.header["$MEASUREMENT"] = 1
    for n, c, t in CAPAS:
        doc.layers.add(n, color=c, linetype=t)
    msp = doc.modelspace()
    quitado = 0.0
    msp.add_lwpolyline(g["contorno"], close=True, dxfattribs={"layer": "CORTE"})
    for x, y, d, _ in g["agujeros"]:
        msp.add_circle((x, y), (d + comp) / 2, dxfattribs={"layer": "TALADROS"})
        quitado += math.pi * (d / 2) ** 2
    for x, y, d, _ in g["huecos"]:
        msp.add_circle((x, y), (d + comp) / 2, dxfattribs={"layer": "CORTE"})
        quitado += math.pi * (d / 2) ** 2
    for x, y, dx, dy in g["ranuras"]:
        msp.add_lwpolyline(rect(x, y, dx + comp, dy + comp), close=True, dxfattribs={"layer": "CORTE"})
        quitado += dx * dy
    for capa, nombre, pts in g["fantasmas"]:
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": capa})
    # límite de tamaño del reglamento (200 x 100) alineado con la parte trasera
    xr = ch["base"]["x1"]
    Lm, Am = P["reglamento"]["largo_max_mm"]["valor"], P["reglamento"]["ancho_max_mm"]["valor"]
    msp.add_lwpolyline(rect(xr + Lm / 2, 0, Lm, Am), close=True, dxfattribs={"layer": "REFERENCIA"})
    msp.add_line((-10, 0), (10, 0), dxfattribs={"layer": "REFERENCIA"})
    msp.add_line((0, -10), (0, 10), dxfattribs={"layer": "REFERENCIA"})
    notas = [
        f"ROBOT CASERO - placa plana en T - {material.upper()} {esp:g} mm - unidades: mm",
        "Origen = centro del eje de las ruedas. X al frente, Y a la izquierda. Gris punteado = limite de tamano del reglamento (200 x 100 mm).",
        "Magenta = PCB principal (arriba). Cian = debajo: motores, ruedas, rueda loca y placa de sensores. Naranja = entre placa y PCB: LiPo y ventilador.",
        "PENDIENTE: espesor C01, kerf/holgura C05, motor N20 M05-M07, LiPo M14, ventilador M21, rueda loca M30. Ver docs/pendientes-por-confirmar.md",
        f"Compensacion de agujeros: {comp:+.1f} mm en el diametro. NO CORTAR hasta confirmar las medidas con vernier.",
    ]
    for i, t in enumerate(notas):
        msp.add_text(t, height=2.2, dxfattribs={"layer": "COTAS"}).set_placement((xr, -58 - 4 * i))
    salida = AQUI / f"placa_{material}.dxf"
    doc.saveas(salida)
    a = area(g["contorno"])
    peso = (a - quitado) * esp / 1000 * ch["densidad_g_cm3"][material]
    return salida, peso, a


if __name__ == "__main__":
    P, pr, se = datos()
    lineas = ["# Resumen de la placa plana en T (generado por generar_dxf.py)", "",
              "| Material | Espesor (mm) | Peso estimado (g) | Archivo |", "|---|---|---|---|"]
    for m in MATERIALES:
        arch, peso, a = generar(m, P, pr, se)
        lineas.append(f"| {m} | {P['chasis']['espesor_mm'][m]:g} | {peso:.0f} (placa sola, maciza) | `{arch.name}` |")
        print(arch.name, f"peso estimado {peso:.0f} g, area {a:.0f} mm2")
    (AQUI / "RESUMEN.md").write_text("\n".join(lineas) + "\n")
