#!/usr/bin/env python3
"""Modelo 3D del robot armado (DXF con mallas MESH para AutoCAD + PNG), a partir de parametros.yaml y de las PCB.

Es un modelo de VOLÚMENES para ver cómo queda todo armado (posiciones y alturas), no un modelo de fabricación:
las piezas son prismas y cilindros con las medidas de docs/especificaciones-componentes.md (por confirmar con vernier).
Salidas: robot_3d.dxf (abrir en AutoCAD con vista 3D / estilo visual "Realista") y robot_3d.png.
Uso: python3 generar_3d.py
"""
import math
from pathlib import Path

import ezdxf
from ezdxf import units
from ezdxf.math import Vec2
from ezdxf.math.triangulation import mapbox_earcut_2d
from ezdxf.render import MeshBuilder

from generar_dxf import datos, geometria, pcb_a_placa, rect, val

AQUI = Path(__file__).resolve().parent
P, PR, SE = datos()
G = geometria(P, PR, SE)
ch, R, M = P["chasis"], P["ruedas_y_motores"], P["modulos"]
ESP = ch["espesor_mm"]["acrilico"]
Z0 = ch["z_inferior_mm"]                 # cara inferior de la placa
Z1 = Z0 + ESP                            # cara superior
PIEZAS = []                              # (capa, color matplotlib, color AutoCAD, lista de caras [(x,y,z)...])


def prisma(capa, color, aci, pts, z0, z1):
    caras = []
    tri = mapbox_earcut_2d([Vec2(p) for p in pts])
    for t in tri:
        caras.append([(p.x, p.y, z0) for p in t])
        caras.append([(p.x, p.y, z1) for p in t])
    n = len(pts)
    for i in range(n):
        (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % n]
        caras.append([(x1, y1, z0), (x2, y2, z0), (x2, y2, z1), (x1, y1, z1)])
    PIEZAS.append((capa, color, aci, caras))


def caja(capa, color, aci, x1, x2, y1, y2, z0, z1):
    prisma(capa, color, aci, [(x1, y1), (x2, y1), (x2, y2), (x1, y2)], z0, z1)


def cilindro_y(capa, color, aci, xc, zc, r, y1, y2, n=32):
    """Cilindro con el eje paralelo a Y (ruedas)."""
    caras = []
    pts = [(xc + r * math.cos(2 * math.pi * i / n), zc + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
    for i in range(n):
        (a, b), (c, d) = pts[i], pts[(i + 1) % n]
        caras.append([(a, y1, b), (c, y1, d), (c, y2, d), (a, y2, b)])
    caras.append([(a, y1, b) for a, b in pts])
    caras.append([(a, y2, b) for a, b in pts])
    PIEZAS.append((capa, color, aci, caras))


def cilindro_z(capa, color, aci, xc, yc, r, z0, z1, n=16):
    pts = [(xc + r * math.cos(2 * math.pi * i / n), yc + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
    prisma(capa, color, aci, pts, z0, z1)


# ---------------- placa plana en T
prisma("3D_PLACA", "#cfe3f5", 4, G["contorno"], Z0, Z1)
# ---------------- ruedas y motores (encima de la placa, con aseguradores)
ye, la = R["cara_exterior_llanta_y_mm"], R["llanta_ancho"]["mm"]
rr = R["llanta_diametro"]["mm"] / 2
mw, ml, mh = val(R["motor_ancho_mm"]), val(R["motor_largo_mm"]), val(R["motor_alto_mm"])
A = R["asegurador"]
yc = ye - la - 0.5
for s_ in (1, -1):
    y1, y2 = sorted((s_ * (ye - la), s_ * ye))
    cilindro_y("3D_RUEDAS", "#1a1a1a", 250, 0, rr, rr, y1, y2)
    yo1, yo2 = sorted((s_ * ye, s_ * (ye + 0.4)))
    cilindro_y("3D_RUEDAS", "#b8bcc2", 9, 0, rr, R["rin_diametro"]["mm"] / 2, yo1, yo2)
    m1, m2 = sorted((s_ * (yc - ml), s_ * yc))
    caja("3D_MOTORES", "#8a6d3b", 42, -mw / 2, mw / 2, m1, m2, rr - mh / 2, rr + mh / 2)
    a1, a2 = sorted((s_ * (yc - ml + 2), s_ * (yc - ml + 2 + A["largo_mm"])))
    caja("3D_ASEGURADORES", "#f2f2f2", 7, -A["ancho_mm"] / 2, A["ancho_mm"] / 2, a1, a2, Z1, rr + mh / 2 + 1.0)
# ---------------- PCB principal (baja, sobre separadores cortos)
zp = Z1 + P["pcbs"]["principal"]["separadores_mm"]
xf = P["pcbs"]["principal"]["x_frente_mm"]
for x, y, d, quien in G["agujeros"]:
    if quien == "PCB principal":
        cilindro_z("3D_SEPARADORES", "#c0c0c0", 8, x, y, 2.5, Z1, zp)
bx1, by1, bx2, by2 = PR["contorno_mm"]
esq = [pcb_a_placa(PR, xf, a, b) for a, b in ((bx1, by1), (bx2, by1), (bx2, by2), (bx1, by2))]
prisma("3D_PCB", "#1f6f43", 96, esq, zp, zp + 1.6)


def modulo(nombre, aci, color, x0, y0, ancho, largo, alto, sobre=8.5):
    pts = [pcb_a_placa(PR, xf, a, b) for a, b in ((x0, y0), (x0 + ancho, y0), (x0 + ancho, y0 + largo), (x0, y0 + largo))]
    z0 = zp + 1.6 + sobre
    prisma("3D_MODULOS", color, aci, pts, z0, z0 + alto)
    return pts, z0 + alto


esp_pts, z_esp = modulo("ESP32", 5, "#222831", 34.7, 14.3, 28.0, 51.0, 1.6 + 3.2)
modulo("DRV8833", 1, "#111111", 73.6, 12.4, 18.0, 15.5, 1.6)
modulo("MP1584 5V", 3, "#2e8b57", 3.75, 12.5, 22.0, 16.5, 4.0)
modulo("MP1584 6V", 3, "#2e8b57", 3.75, 31.5, 22.0, 16.5, 4.0)
modulo("74HC4067", 5, "#1d3f8f", 73.1, 53.0, 18.0, 41.0, 1.6)
# LiPo pegada encima del ESP32 (a lo largo)
L = M["lipo_2s"]
cx = sum(p[0] for p in esp_pts) / 4
caja("3D_BATERIA", "#e3a21a", 40, cx - L["largo_mm"] / 2, cx + L["largo_mm"] / 2, -L["ancho_mm"] / 2, L["ancho_mm"] / 2, z_esp, z_esp + L["alto_mm"])
# ventilador sobre su hueco, con separadores de 8 mm
V = M["ventilador_4010"]
for hx, hy, d in PR.get("huecos_ventilador_mm", []):
    x, y = pcb_a_placa(PR, xf, hx, hy)
    caja("3D_VENTILADOR", "#2a7f62", 94, x - 20, x + 20, y - 20, y + 20, zp + 1.6 + V["separadores_mm"],
         zp + 1.6 + V["separadores_mm"] + V["alto_mm"])
# ---------------- placa de sensores sobre la MISMA placa, sensores por las ventanas
xs = P["pcbs"]["sensores"]["x_frente_mm"]
alt = M["sensores"]["altura_al_piso_mm"]
zs = Z1 + P["pcbs"]["sensores"]["separadores_mm"]
for x, y, d, quien in G["agujeros"]:
    if quien == "Placa de sensores":
        cilindro_z("3D_SEPARADORES", "#c0c0c0", 8, x, y, 2.5, Z1, zs)
bx1, by1, bx2, by2 = SE["contorno_mm"]
esq = [pcb_a_placa(SE, xs, a, b) for a, b in ((bx1, by1), (bx2, by1), (bx2, by2), (bx1, by2))]
prisma("3D_PCB", "#1f6f43", 96, esq, zs, zs + 1.6)
Rk, n, paso = M["sensores"]["radio_arco_mm"], M["sensores"]["n"], M["sensores"]["paso_mm"]
for i in range(n):
    th = (i - (n - 1) / 2) * paso / Rk
    xp = 50 + Rk * math.sin(th)
    yp = 14 + Rk - Rk * math.cos(th) + 3.81
    x, y = pcb_a_placa(SE, xs, xp, yp)
    caja("3D_SENSORES", "#c0392b", 1, x - 5.1, x + 5.1, y - 2.9, y + 2.9, zs - M["tcrt5000"]["alto_mm"], zs)
# patín delantero: tornillo de cabeza redonda de nailon bajo el agujero central de la placa de sensores
x, y = pcb_a_placa(SE, xs, 50, 30)
cilindro_z("3D_PATIN", "#eeeeee", 9, x, y, 3.0, 0.3, Z0)


def escribir_dxf():
    doc = ezdxf.new("R2010", setup=True)
    doc.units = units.MM
    doc.header["$MEASUREMENT"] = 1
    msp = doc.modelspace()
    for capa, _, aci, caras in PIEZAS:
        if capa not in doc.layers:
            doc.layers.add(capa, color=aci)
        mb = MeshBuilder()
        for c in caras:
            mb.add_face(c)
        mb.render_mesh(msp, dxfattribs={"layer": capa})
    doc.layers.add("COTAS", color=2)
    msp.add_text("ROBOT CASERO armado, opcion A (modelo de volumenes, mm). Medidas por confirmar con vernier.", height=3,
                 dxfattribs={"layer": "COTAS"}).set_placement((-30, -65))
    doc.saveas(AQUI / "robot_3d.dxf")


def escribir_png():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig = plt.figure(figsize=(16, 9))
    vistas = [(22, 35, "Vista 3/4 desde el frente"), (30, -140, "Vista 3/4 desde atrás"), (0, -90, "Vista lateral (piso = 0, frente a la derecha)")]
    for k, (elev, azim, tit) in enumerate(vistas):
        ax = fig.add_subplot(1, 3, k + 1, projection="3d")
        for capa, color, _, caras in PIEZAS:
            a = 0.75 if capa == "3D_PLACA" else 1.0
            ax.add_collection3d(Poly3DCollection(caras, facecolor=color, alpha=a, edgecolor=(0, 0, 0, 0.0 if capa == "3D_PLACA" else 0.25), linewidths=0.2))
        ax.set_xlim(-130, 75); ax.set_ylim(-60, 60); ax.set_zlim(0, 50)
        ax.set_box_aspect((205, 120, 50))
        ax.view_init(elev=elev, azim=azim)
        ax.set_title(tit, fontsize=10)
        ax.set_axis_off()
    fig.suptitle("Robot casero armado, opción A: una sola placa de acrílico (modelo de volúmenes, mm; medidas por confirmar)\n"
                 "Azul claro: placa · verde: PCB · negro: ruedas · café: motores N20 · blanco: aseguradores · amarillo: LiPo · "
                 "verde oscuro: ventilador · rojo: sensores TCRT5000 · gris: separadores y patín", fontsize=10)
    fig.savefig(AQUI / "robot_3d.png", dpi=140, bbox_inches="tight")


if __name__ == "__main__":
    escribir_dxf()
    escribir_png()
    d = ezdxf.readfile(AQUI / "robot_3d.dxf")
    print("robot_3d.dxf:", len(d.modelspace().query("MESH")), "mallas, auditoría:", len(d.audit().errors), "errores")
