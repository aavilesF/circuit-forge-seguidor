#!/usr/bin/env python3
"""Genera los DXF 2D de la placa única (opción A) del robot casero (AutoCAD, milímetros) desde parametros.yaml.

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
    """Contorno de la placa única: zona delantera (sensores), centro con muescas para las ruedas y zona trasera (PCB)."""
    ch, R = P["chasis"], P["ruedas_y_motores"]
    d, c0, t, c = ch["delantera"], ch["centro"], ch["trasera"], ch["chaflan_mm"]
    nx, ny = R["muesca_rueda_medio_largo_mm"], R["muesca_rueda_y_interior_mm"]
    hd, hc, ht = d["medio_ancho"], c0["medio_ancho"], t["medio_ancho"]
    der = [(t["x1"] + c, -ht), (t["x2"], -ht), (t["x2"], -hc), (-nx, -hc), (-nx, -ny), (nx, -ny), (nx, -hc),
           (d["x1"], -hc), (d["x1"], -hd), (d["x2"] - c, -hd), (d["x2"], -hd + c)]
    izq = [(x, -y) for x, y in reversed(der)]
    return der + izq + [(t["x1"], ht - c), (t["x1"], -ht + c)]


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
    g = {"contorno": contorno_placa(P), "agujeros": [], "ranuras": [], "huecos": [], "ventanas": [], "fantasmas": []}
    d_m3 = ch["agujero_tornillo_m3_mm"]
    for nombre, pcb, xf, capa in (("PCB principal", pr, P["pcbs"]["principal"]["x_frente_mm"], "PIEZAS_FANTASMA"),
                                  ("Placa de sensores", se, P["pcbs"]["sensores"]["x_frente_mm"], "PIEZAS_FANTASMA")):
        for hx, hy in pcb["agujeros_m3_mm"]:
            g["agujeros"].append((*pcb_a_placa(pcb, xf, hx, hy), d_m3, nombre))
        bx1, by1, bx2, by2 = pcb["contorno_mm"]
        g["fantasmas"].append((capa, nombre, [pcb_a_placa(pcb, xf, x, y) for x, y in ((bx1, by1), (bx2, by1), (bx2, by2), (bx1, by2))]))
    # ventilador: hueco de aire igual al de la PCB principal (huella HV de KiCad)
    V = M["ventilador_4010"]
    for hx, hy, d in pr.get("huecos_ventilador_mm", []):
        x, y = pcb_a_placa(pr, P["pcbs"]["principal"]["x_frente_mm"], hx, hy)
        g["huecos"].append((x, y, V["hueco_mm"], "ventilador"))
        g["fantasmas"].append(("PIEZAS_FANTASMA_ENTRE", "Ventilador 4010 (sobre la PCB)", rect(x, y, V["lado_mm"], V["lado_mm"])))
        for dx in (-16, 16):
            for dy in (-16, 16):
                g["agujeros"].append((x + dx, y + dy, P["chasis"]["agujero_tornillo_m3_mm"], "ventilador"))
    # ventanas para que los 12 sensores atraviesen la placa (7 x 11 mm, giradas como cada sensor)
    S = M["sensores"]
    xs = P["pcbs"]["sensores"]["x_frente_mm"]
    for i in range(S["n"]):
        th = (i - (S["n"] - 1) / 2) * S["paso_mm"] / S["radio_arco_mm"]
        xp = 50 + S["radio_arco_mm"] * math.sin(th)
        yp = 14 + S["radio_arco_mm"] - S["radio_arco_mm"] * math.cos(th) + 3.81
        x, y = pcb_a_placa(se, xs, xp, yp)
        g["ventanas"].append((x, y, 11.0, 7.0, -th))   # sensor 10.2 x 5.8 + 0.4 por lado
    # motores N20 sobre la placa con aseguradores
    mw, ml = val(R["motor_ancho_mm"]), val(R["motor_largo_mm"])
    ye, la = R["cara_exterior_llanta_y_mm"], R["llanta_ancho"]["mm"]
    yc = ye - la - 0.5
    A = R["asegurador"]
    for lado in (1, -1):
        g["fantasmas"].append(("PIEZAS_FANTASMA", "Motor N20", rect(0, lado * (yc - ml / 2), mw, ml)))
        g["fantasmas"].append(("PIEZAS_FANTASMA_ABAJO", "Rueda", rect(0, lado * (ye - la / 2), R["llanta_diametro"]["mm"], la)))
        ya = lado * (yc - ml + A["largo_mm"] / 2 + 2)
        for dx in (-A["sep_agujeros_mm"] / 2, A["sep_agujeros_mm"] / 2):
            g["agujeros"].append((dx, ya, A["diametro_agujero_mm"], "asegurador"))
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
    for x, y, dx, dy, a in g["ventanas"]:
        ca, sa = math.cos(a), math.sin(a)
        pts = [(x + px * ca - py * sa, y + px * sa + py * ca) for px, py in rect(0, 0, dx + comp, dy + comp)]
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "CORTE"})
        quitado += dx * dy
    for capa, nombre, pts in g["fantasmas"]:
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": capa})
    # límite de tamaño del reglamento (200 x 100) alineado con la parte trasera
    xr = ch["trasera"]["x1"]
    Lm, Am = P["reglamento"]["largo_max_mm"]["valor"], P["reglamento"]["ancho_max_mm"]["valor"]
    msp.add_lwpolyline(rect(xr + Lm / 2, 0, Lm, Am), close=True, dxfattribs={"layer": "REFERENCIA"})
    msp.add_line((-10, 0), (10, 0), dxfattribs={"layer": "REFERENCIA"})
    msp.add_line((0, -10), (0, 10), dxfattribs={"layer": "REFERENCIA"})
    notas = [
        f"ROBOT CASERO - placa unica (opcion A) - {material.upper()} {esp:g} mm - unidades: mm",
        "Origen = centro del eje de las ruedas. X al frente, Y a la izquierda. Gris punteado = limite de tamano del reglamento (200 x 100 mm).",
        "Magenta = encima de la placa: PCB principal, placa de sensores, motores y ventilador. Cian = ruedas (en las muescas). Rojo pequeno = ventanas de los sensores.",
        "PENDIENTE: espesor C01, kerf/holgura C05, motor N20 M05-M06, asegurador M31, ventilador M21. Ver docs/pendientes-por-confirmar.md",
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
    lineas = ["# Resumen de la placa única, opción A (generado por generar_dxf.py)", "",
              "| Material | Espesor (mm) | Peso estimado (g) | Archivo |", "|---|---|---|---|"]
    for m in MATERIALES:
        arch, peso, a = generar(m, P, pr, se)
        lineas.append(f"| {m} | {P['chasis']['espesor_mm'][m]:g} | {peso:.0f} (placa sola, maciza) | `{arch.name}` |")
        print(arch.name, f"peso estimado {peso:.0f} g, area {a:.0f} mm2")
    (AQUI / "RESUMEN.md").write_text("\n".join(lineas) + "\n")
