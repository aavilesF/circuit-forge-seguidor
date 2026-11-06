#!/usr/bin/env python3
"""Verifica los DXF de la placa: auditoría, unidades, capas, polilíneas cerradas, límite de tamaño del reglamento,
márgenes de agujeros y que las piezas fantasma de un mismo lado no se encimen. Genera vista previa en PNG.
Uso: python3 verificar_dxf.py
"""
import math
import sys
from pathlib import Path

import ezdxf
import yaml

AQUI = Path(__file__).resolve().parent
P = yaml.safe_load(open(AQUI / "parametros.yaml"))
CAPAS = ["CORTE", "GRABADO", "TALADROS", "REFERENCIA", "COTAS", "PIEZAS_FANTASMA", "PIEZAS_FANTASMA_ABAJO", "PIEZAS_FANTASMA_ENTRE"]


def bbox(pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def solapan(a, b, tol=0.0):
    return a[0] < b[2] - tol and b[0] < a[2] - tol and a[1] < b[3] - tol and b[1] < a[3] - tol


def dist_a_poligono(x, y, pts):
    d = 1e9
    for i in range(len(pts)):
        (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % len(pts)]
        dx, dy = x2 - x1, y2 - y1
        t = max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
        d = min(d, math.hypot(x - (x1 + t * dx), y - (y1 + t * dy)))
    return d


def verificar(archivo, material):
    errores, avisos = [], []
    doc = ezdxf.readfile(archivo)
    aud = doc.audit()
    if aud.errors:
        errores.append(f"auditoría: {len(aud.errors)} errores")
    if doc.units != 4 or doc.header.get("$MEASUREMENT") != 1:
        errores.append("unidades no son milímetros")
    for c in CAPAS:
        if c not in doc.layers:
            errores.append(f"falta la capa {c}")
    msp = doc.modelspace()
    cortes = [e for e in msp.query("LWPOLYLINE") if e.dxf.layer == "CORTE"]
    for e in msp.query("LWPOLYLINE"):
        if not e.closed:
            errores.append("polilínea abierta en " + e.dxf.layer)
    if any(e.dxf.layer == "0" for e in msp):
        errores.append("hay entidades en la capa 0")
    esp = P["chasis"]["espesor_mm"][material]
    placa = max(cortes, key=lambda e: len(e))                 # el contorno exterior (más vértices)
    pts = [(p[0], p[1]) for p in placa.get_points("xy")]
    x1, y1, x2, y2 = bbox(pts)
    L, A = x2 - x1, y2 - y1
    Lmax, Amax = P["reglamento"]["largo_max_mm"]["valor"], P["reglamento"]["ancho_max_mm"]["valor"]
    if L > Lmax or A > Amax:
        errores.append(f"la placa {L:.1f} x {A:.1f} excede el límite de tamaño {Lmax} x {Amax}")
    # todo lo físico dentro del límite de tamaño
    todo = [(p[0], p[1]) for e in msp.query("LWPOLYLINE") if e.dxf.layer != "REFERENCIA" for p in e.get_points("xy")]
    bx1, by1, bx2, by2 = bbox(todo)
    if (bx2 - bx1) > Lmax or (by2 - by1) > Amax:
        errores.append(f"con las piezas fantasma el conjunto mide {bx2 - bx1:.1f} x {by2 - by1:.1f} y excede el límite de tamaño")
    # agujeros: margen al borde >= 2 x espesor y a otros agujeros >= 2 mm
    circ = [(c.dxf.center.x, c.dxf.center.y, c.dxf.radius) for c in msp.query("CIRCLE") if c.dxf.layer in ("TALADROS", "CORTE")]
    for (x, y, r) in circ:
        d = dist_a_poligono(x, y, pts) - r
        if d < 2 * esp:
            errores.append(f"agujero en ({x:.1f},{y:.1f}) a {d:.1f} mm del borde (mín {2 * esp:g})")
    for i in range(len(circ)):
        for j in range(i + 1, len(circ)):
            d = math.hypot(circ[i][0] - circ[j][0], circ[i][1] - circ[j][1]) - circ[i][2] - circ[j][2]
            if d < 2.0:
                errores.append(f"agujeros muy juntos ({circ[i][0]:.1f},{circ[i][1]:.1f}) y ({circ[j][0]:.1f},{circ[j][1]:.1f}): {d:.1f} mm")
    # ranuras (cortes pequeños): margen a agujeros
    ranuras = [e for e in cortes if e is not placa]
    for r in ranuras:
        b = bbox([(p[0], p[1]) for p in r.get_points("xy")])
        for (x, y, rad) in circ:
            if x + rad > b[0] - 2 and x - rad < b[2] + 2 and y + rad > b[1] - 2 and y - rad < b[3] + 2:
                errores.append(f"ranura y agujero a menos de 2 mm cerca de ({x:.1f},{y:.1f})")
    # piezas fantasma del mismo lado no se encimen
    for capa in ("PIEZAS_FANTASMA", "PIEZAS_FANTASMA_ABAJO", "PIEZAS_FANTASMA_ENTRE"):
        rects = [(bbox([(p[0], p[1]) for p in e.get_points("xy")]), id(e)) for e in msp.query("LWPOLYLINE") if e.dxf.layer == capa]
        for i in range(len(rects)):
            for j in range(i + 1, len(rects)):
                if solapan(rects[i][0], rects[j][0]):
                    # las llantas (en la muesca) están junto al motor por diseño: solo se avisa si no tocan la muesca
                    errores.append(f"{capa}: dos piezas se enciman {tuple(round(v, 1) for v in rects[i][0])} y {tuple(round(v, 1) for v in rects[j][0])}")
        # que estén dentro del contorno de la placa en X (las ruedas pueden salir en Y: van en muescas)
    return errores, avisos, (L, A)


def vista_previa(archivo):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from ezdxf.addons.drawing import Frontend, RenderContext
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    doc = ezdxf.readfile(archivo)
    fig = plt.figure(figsize=(14, 8))
    ax = fig.add_axes([0, 0, 1, 1])
    ctx = RenderContext(doc)
    Frontend(ctx, MatplotlibBackend(ax)).draw_layout(doc.modelspace(), finalize=True)
    ax.set_aspect("equal")
    fig.savefig(str(archivo).replace(".dxf", ".png"), dpi=130)
    plt.close(fig)


if __name__ == "__main__":
    mal = 0
    for m in ("acrilico", "mdf", "pla"):
        f = AQUI / f"placa_{m}.dxf"
        e, a, (L, A) = verificar(f, m)
        print(f"{f.name}: {'OK' if not e else 'ERRORES'} (placa {L:.1f} x {A:.1f} mm)")
        for t in e + a:
            print("   -", t)
        mal += len(e)
        if m == "acrilico":
            vista_previa(f)
    sys.exit(1 if mal else 0)
