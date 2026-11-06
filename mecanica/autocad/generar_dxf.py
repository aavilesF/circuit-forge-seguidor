#!/usr/bin/env python3
"""Genera los DXF de la placa plana del robot casero (AutoCAD, milímetros) a partir de parametros.yaml.

Un DXF por material: acrilico (láser), mdf (láser), pla (impresión 3D). Cambian el espesor y la compensación de agujeros.
Ejes: origen en el centro del eje de las ruedas, X hacia el frente, Y hacia la izquierda.
Las posiciones de los agujeros de las PCB salen de electronica/kicad/*/ *_mecanica.json (una sola fuente de verdad).
TODAS las medidas "nominal/pendiente" están en docs/pendientes-por-confirmar.md. No cortar antes de confirmarlas.
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
         ("PIEZAS_FANTASMA", 6, "DASHED"),           # piezas ARRIBA de la placa (PCB, ventilador)
         ("PIEZAS_FANTASMA_ABAJO", 4, "DASHED"),      # piezas DEBAJO de la placa (motores, batería, rueda loca)
         ("PIEZAS_FANTASMA_ENTRE", 30, "DASHED")]    # piezas entre la placa y las PCB (ventilador, bajo los separadores)
MATERIALES = ["acrilico", "mdf", "pla"]


def val(d, k="valor"):
    return d[k] if isinstance(d, dict) else d


def contorno_placa(P):
    ch = P["chasis"]
    xr, xf, h, c = ch["x_trasero_mm"], ch["x_delantero_mm"], ch["ancho_mm"] / 2, ch["chaflan_mm"]
    R = P["ruedas_y_motores"]
    nx = R["muesca_rueda_largo_mm"] / 2
    ny = h - R["muesca_rueda_profundo_mm"]
    return [(xr + c, -h), (-nx, -h), (-nx, -ny), (nx, -ny), (nx, -h), (xf - c, -h), (xf, -h + c), (xf, h - c),
            (xf - c, h), (nx, h), (nx, ny), (-nx, ny), (-nx, h), (xr + c, h), (xr, h - c), (xr, -h + c)]


def pcb_a_placa(pcb, x_frente, x, y):
    """Convierte (x, y) de la PCB (x derecha, y hacia atrás) a coordenadas de la placa (X frente, Y izquierda)."""
    bx1, by1, bx2, by2 = pcb["contorno_mm"]
    return x_frente - (y - by1), -(x - (bx1 + bx2) / 2)


def rect(cx, cy, dx, dy):
    return [(cx - dx / 2, cy - dy / 2), (cx + dx / 2, cy - dy / 2), (cx + dx / 2, cy + dy / 2), (cx - dx / 2, cy + dy / 2)]


def area(pts):
    return abs(sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))) / 2


def datos():
    P = yaml.safe_load(open(AQUI / "parametros.yaml"))
    pr = json.load(open(RAIZ / "electronica/kicad/principal/principal_mecanica.json"))
    ba = json.load(open(RAIZ / "electronica/kicad/barra_sensores/barra_sensores_mecanica.json"))
    return P, pr, ba


def generar(material, P, pr, ba):
    ch, R, M = P["chasis"], P["ruedas_y_motores"], P["modulos"]
    esp = ch["espesor_mm"][material]
    kerf, hol = ch["kerf_laser_mm"]["valor"], ch["holgura_fdm_mm"]["valor"]
    # compensación del diámetro de los agujeros: láser quita 'kerf'; la impresora los cierra 'hol'
    comp = -kerf if material in ("acrilico", "mdf") else +hol
    doc = ezdxf.new("R2010", setup=True)
    doc.units = units.MM
    doc.header["$MEASUREMENT"] = 1
    for n, c, t in CAPAS:
        doc.layers.add(n, color=c, linetype=t)
    msp = doc.modelspace()
    cortes, huecos = [], []   # para el peso

    def poli(pts, capa="CORTE"):
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": capa})

    def agujero(x, y, d, capa="TALADROS"):
        msp.add_circle((x, y), (d + comp) / 2, dxfattribs={"layer": capa})
        huecos.append(math.pi * (d / 2) ** 2)

    def ranura(x, y, dx, dy):
        pts = rect(x, y, dx + comp, dy + comp)
        poli(pts)
        huecos.append(dx * dy)

    def texto(x, y, t, h=2.5, capa="COTAS"):
        msp.add_text(t, height=h, dxfattribs={"layer": capa}).set_placement((x, y))

    # --- placa
    placa = contorno_placa(P)
    poli(placa)
    area_placa = area(placa)

    # --- agujeros de las PCB (salen de generar_pcb.py)
    d_m3 = ch["agujero_tornillo_m3_mm"]
    for pcb, xf in ((pr, P["pcbs"]["principal"]["x_frente_mm"]), (ba, P["pcbs"]["barra"]["x_frente_mm"])):
        for hx, hy in pcb["agujeros_m3_mm"]:
            x, y = pcb_a_placa(pcb, xf, hx, hy)
            agujero(x, y, d_m3)
        bx1, by1, bx2, by2 = pcb["contorno_mm"]
        esq = [pcb_a_placa(pcb, xf, x, y) for x, y in ((bx1, by1), (bx2, by1), (bx2, by2), (bx1, by2))]
        poli(esq, "PIEZAS_FANTASMA")

    # --- ventilador (4010): hueco de succión + 4 agujeros de tornillo
    V = M["ventilador_4010"]
    fx = V["x_centro_mm"]
    msp.add_circle((fx, 0), V["hueco_mm"] / 2 - kerf / 2 * (comp < 0), dxfattribs={"layer": "CORTE"})
    huecos.append(math.pi * (V["hueco_mm"] / 2) ** 2)
    s = V["separacion_agujeros_mm"] / 2
    for dx in (-s, s):
        for dy in (-s, s):
            agujero(fx + dx, dy, V["agujero_mm"])
    poli(rect(fx, 0, V["lado_mm"], V["lado_mm"]), "PIEZAS_FANTASMA_ENTRE")

    # --- motores N20: cuerpo debajo de la placa, 2 cinchos por motor
    mw, ml = val(R["motor_ancho_mm"]), val(R["motor_largo_mm"])
    yc = R["cara_motor_y_mm"]
    eje, llanta_d, llanta_a = val(R["eje_largo_mm"]), val(R["llanta_diametro_mm"]), val(R["llanta_ancho_mm"])
    sl, sa = R["cincho_slot_mm"]["largo"], R["cincho_slot_mm"]["ancho"]
    for lado in (1, -1):
        poli(rect(0, lado * (yc - ml / 2), mw, ml), "PIEZAS_FANTASMA_ABAJO")
        msp.add_line((0, lado * yc), (0, lado * (yc + eje)), dxfattribs={"layer": "PIEZAS_FANTASMA_ABAJO"})
        poli(rect(0, lado * (yc + 1.5 + llanta_a / 2), llanta_d, llanta_a), "PIEZAS_FANTASMA_ABAJO")
        for yy in (22.0, 32.0):
            for xx in (-mw / 2 - 2.5, mw / 2 + 2.5):
                ranura(xx, lado * yy, sa, sl)

    # --- batería LiPo: debajo, 2 cinchos
    Lp = M["lipo_2s"]
    lx = Lp["x_centro_mm"]
    poli(rect(lx, 0, Lp["largo_mm"], Lp["ancho_mm"]), "PIEZAS_FANTASMA_ABAJO")
    for xx in (lx - 15, lx + 15):
        for yy in (-(Lp["ancho_mm"] / 2 + 2.5), Lp["ancho_mm"] / 2 + 2.5):
            ranura(xx, yy, sl, sa)

    # --- rueda loca (atrás): 2 agujeros
    rl = R["rueda_loca"]
    for dy in (-rl["y_mm"], rl["y_mm"]):
        agujero(rl["x_mm"], dy, rl["diametro_tornillo_mm"])
    poli(rect(rl["x_mm"], 0, 10, 2 * rl["y_mm"] + 6), "PIEZAS_FANTASMA_ABAJO")

    # --- referencias
    xr = ch["x_trasero_mm"]
    box = rect(xr + P["reglamento"]["caja_largo_max_mm"]["valor"] / 2, 0, P["reglamento"]["caja_largo_max_mm"]["valor"],
               P["reglamento"]["caja_ancho_max_mm"]["valor"])
    msp.add_lwpolyline(box, close=True, dxfattribs={"layer": "REFERENCIA"})
    msp.add_line((-10, 0), (10, 0), dxfattribs={"layer": "REFERENCIA"})
    msp.add_line((0, -10), (0, 10), dxfattribs={"layer": "REFERENCIA"})
    # --- notas (en el idioma del equipo)
    ytxt = -58
    for i, t in enumerate([
        f"ROBOT CASERO - placa plana - {material.upper()} {esp:g} mm - unidades: mm - 5 nov 2026",
        "Origen = centro del eje de las ruedas. X al frente, Y a la izquierda. Linea punteada gris = caja de 200 x 100 mm del reglamento.",
        "PENDIENTE (docs/pendientes-por-confirmar.md): espesor C01, kerf/holgura C05, motor M05-M07, PCB M01-M20, ventilador M21, LiPo M14, rueda loca.",
        "NO CORTAR hasta confirmar las medidas con la regla/vernier. Piezas fantasma: magenta = PCB arriba; cian = debajo de la placa; naranja = ventilador entre placa y PCB.",
        f"Compensacion de agujeros: {comp:+.1f} mm en el diametro ({'laser: quita el kerf' if comp < 0 else 'FDM: la impresora cierra los agujeros'}).",
    ]):
        texto(xr, ytxt - i * 4.0, t, 2.2)
    # cotas simples (texto) del contorno
    texto(xr, -52, f"Largo placa {ch['x_delantero_mm'] - ch['x_trasero_mm']:g} mm x ancho {ch['ancho_mm']:g} mm", 2.2)

    salida = AQUI / f"placa_{material}.dxf"
    doc.saveas(salida)
    densidad = ch["densidad_g_cm3"][material]
    peso = (area_placa - sum(huecos)) * esp / 1000 * densidad
    return salida, peso, area_placa


if __name__ == "__main__":
    P, pr, ba = datos()
    lineas = ["# Resumen de la placa plana (generado por generar_dxf.py)", "",
              "| Material | Espesor (mm) | Peso estimado (g) | Archivo |", "|---|---|---|---|"]
    for m in MATERIALES:
        arch, peso, a = generar(m, P, pr, ba)
        lineas.append(f"| {m} | {P['chasis']['espesor_mm'][m]:g} | {peso:.0f} (macizo, sin ventilador ni piezas) | `{arch.name}` |")
        print(arch.name, f"peso estimado {peso:.0f} g, area {a:.0f} mm2")
    (AQUI / "RESUMEN.md").write_text("\n".join(lineas) + "\n")
