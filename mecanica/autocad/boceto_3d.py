#!/usr/bin/env python3
"""Boceto 3D (solo ilustrativo) del robot casero a partir de parametros.yaml. Alturas supuestas: ver ALTURAS."""
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import yaml
from generar_dxf import contorno_placa

P = yaml.safe_load(open("parametros.yaml"))
ESP = 3.0
Z_PLACA = 24.0                      # cara inferior de la placa sobre el piso (supuesto)
SEP = P["pcbs"]["altura_separadores_mm"]
fig = plt.figure(figsize=(15, 9))
partes = []                         # (caras, color, alfa)


def prisma(pts, z0, z1, color, a=1.0):
    n = len(pts)
    caras = [[(x, y, z0) for x, y in pts], [(x, y, z1) for x, y in pts]]
    for i in range(n):
        (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % n]
        caras.append([(x1, y1, z0), (x2, y2, z0), (x2, y2, z1), (x1, y1, z1)])
    partes.append((caras, color, a))


def caja(x1, x2, y1, y2, z0, z1, color, a=1.0):
    prisma([(x1, y1), (x2, y1), (x2, y2), (x1, y2)], z0, z1, color, a)


def rueda(y_centro, ancho, d, color):
    n = 28
    r = d / 2
    for i in range(n):
        a1, a2 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        x1, z1 = r * math.cos(a1), r * math.sin(a1) + r
        x2, z2 = r * math.cos(a2), r * math.sin(a2) + r
        partes.append(([[(x1, y_centro - ancho / 2, z1), (x2, y_centro - ancho / 2, z2),
                         (x2, y_centro + ancho / 2, z2), (x1, y_centro + ancho / 2, z1)]], color, 1.0))
    partes.append(([[(r * math.cos(2 * math.pi * i / n), y_centro + ancho / 2, r * math.sin(2 * math.pi * i / n) + r) for i in range(n)]], color, 1.0))


ch, R, M = P["chasis"], P["ruedas_y_motores"], P["modulos"]
val = lambda d: d["valor"] if isinstance(d, dict) else d
# placa
prisma(contorno_placa(P), Z_PLACA, Z_PLACA + ESP, "#d9e8f5", 0.85)
# ruedas y motores (debajo)
yc = R["cara_motor_y_mm"]
for lado in (1, -1):
    caja(-6, 6, lado * (yc - val(R["motor_largo_mm"])), lado * yc, 17 - 5, 17 + 5, "#444444")
    rueda(lado * (yc + 1.5 + 3.5), 7, val(R["llanta_diametro_mm"]), "#111111")
# LiPo
L = M["lipo_2s"]
caja(L["x_centro_mm"] - L["largo_mm"] / 2, L["x_centro_mm"] + L["largo_mm"] / 2, -L["ancho_mm"] / 2, L["ancho_mm"] / 2,
     Z_PLACA - L["alto_mm"], Z_PLACA, "#e0a030")
# rueda loca (atrás, debajo)
caja(-67, -57, -11, 11, 8, Z_PLACA, "#888888")
# ventilador 4010 sobre la placa
V = M["ventilador_4010"]
fx = V["x_centro_mm"]
caja(fx - 20, fx + 20, -20, 20, Z_PLACA + ESP, Z_PLACA + ESP + V["alto_mm"], "#2a7f62")
# PCB principal y de la barra sobre separadores
zp = Z_PLACA + ESP + SEP
pr, ba = P["pcbs"]["principal"], P["pcbs"]["barra"]
xf1, l1 = pr["x_frente_mm"], pr["largo_mm"]
caja(xf1 - l1, xf1, -pr["ancho_mm"] / 2, pr["ancho_mm"] / 2, zp, zp + 1.6, "#2e8b57")
caja(xf1 - 56, xf1 - 2, -14, 14, zp + 1.6, zp + 1.6 + 12, "#1c3d73")          # ESP32 (módulo, referencia)
xf2, l2 = ba["x_frente_mm"], ba["largo_mm"]
caja(xf2 - l2, xf2, -ba["ancho_mm"] / 2, ba["ancho_mm"] / 2, zp, zp + 1.6, "#2e8b57")
# sensores TCRT5000 colgando bajo la barra (7 mm)
for i in range(12):
    th = (i - 5.5) * 7.5 / 110.0
    x, y = xf2 - (6 + 110 - 110 * math.cos(th)), -(110 * math.sin(th))
    caja(x - 2.9, x + 2.9, y - 2.9, y + 2.9, zp - 7, zp, "#cc2222")
# separadores
for (x, y) in [(28, 34), (28, -34), (-56, 34), (-56, -34), (68, 40), (68, -40), (42, 40), (42, -40)]:
    caja(x - 1.5, x + 1.5, y - 1.5, y + 1.5, Z_PLACA + ESP, zp, "#bbbbbb")

for idx, (elev, azim, tit) in enumerate([(24, -58, "Vista isométrica (frente a la derecha)"), (8, -90, "Vista lateral")]):
    ax = fig.add_subplot(1, 2, idx + 1, projection="3d")
    for caras, c, a in partes:
        ax.add_collection3d(Poly3DCollection(caras, facecolor=c, edgecolor="#222", linewidths=0.3, alpha=a))
    ax.set_xlim(-75, 125); ax.set_ylim(-60, 60); ax.set_zlim(0, 80)
    ax.set_box_aspect((200, 120, 80))
    ax.view_init(elev=elev, azim=azim)
    ax.set_title(tit)
    ax.set_xlabel("X (frente) mm"); ax.set_ylabel("Y mm"); ax.set_zlabel("Z mm")
fig.suptitle("BOCETO 3D - robot casero (alturas supuestas, medidas por confirmar). Azul claro = placa; verde = PCB; verde oscuro = ventilador; "
             "naranja = LiPo; negro = motores/ruedas; rojo = sensores", fontsize=9)
fig.savefig("boceto_3d.png", dpi=130, bbox_inches="tight")
