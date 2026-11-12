#!/usr/bin/env python3
"""V2 · CAD mecánico (CadQuery): chasis impreso con cámara de succión de 70 × 70 mm, alojamiento del ventilador del
usuario, cachucha de la barra de sensores, soportes de motor, bahía del ESC, portabaterías, rueda loca y postes de la PCB
principal. Ensamble con los modelos de compra simplificados (APROX) y verificación de interferencias, masa y CG.

Marco del robot (mm): x adelante desde el eje de ruedas, y a la izquierda, z arriba desde el piso. Parámetros en
config/v2/robot_v2.yaml. Los modelos del ventilador del usuario (hardware/v2/referencia_succion/*.obj) NO se modifican:
se colocan en el marco del robot para comprobar el ajuste y se exportan juntos en ventilador_usuario_en_robot.stl.

Uso: python3 hardware/v2/mecanica/cad/generar_cad_v2.py"""
from __future__ import annotations

import glob
import json
import math
import os
import sys

import cadquery as cq
import numpy as np
import trimesh
import yaml

AQUI = os.path.dirname(os.path.abspath(__file__))
MEC = os.path.abspath(os.path.join(AQUI, ".."))
RAIZ = os.path.abspath(os.path.join(MEC, "..", "..", ".."))
sys.path.insert(0, AQUI)
import vistas_v2 as VI  # noqa: E402
sys.path.insert(0, os.path.join(os.path.abspath(os.path.join(AQUI, "..", "..", "..", "..")), "sim", "v2"))
import fase35 as F35  # noqa: E402  (altura del faldón con la compresión de las llantas)

G = yaml.safe_load(open(os.path.join(RAIZ, "config", "v2", "robot_v2.yaml"), encoding="utf-8"))
v = lambda s, k: G[s][k]["valor"]   # noqa: E731
OBJ_DIR = os.path.join(RAIZ, "hardware", "v2", "referencia_succion")
WEACT_STEP = os.path.join(MEC, "modelos_compra", "WeAct-STM32G47x_CoreBoard_3D.step")
BARRA_STEP = os.path.join(RAIZ, "hardware", "v2", "electronica", "fabricacion", "barra_sensores", "barra_sensores_pcba.step")
SAL = {k: os.path.join(MEC, k) for k in ("step", "stl", "render", "planos")}
for d in SAL.values():
    os.makedirs(d, exist_ok=True)

# ------------------------------------------------------------------------------------------------ cotas principales
Z_PB = v("chasis", "z_inferior_placa")             # 5.1: cara inferior de la placa = techo de la cámara
E_P = v("chasis", "espesor_placa")                 # 2.0
Z_PT = Z_PB + E_P                                  # 7.1: cara superior de la placa
X_TR = v("chasis", "x_trasero")                    # -33.5
CAM_X = v("camara", "x_centro")                    # 4.0
CAM_IN = v("camara", "interior")[0] / 2            # 35
CAM_W = v("camara", "pared")                       # 1.2
RANURA = v("camara", "ranura")                     # 0.5
XF = v("ventilador", "x")                          # 27.5
R_RUEDA = v("ruedas", "D") / 2
Y_RUEDA = v("ruedas", "y_centro")
A_RUEDA = v("ruedas", "ancho")
Y_CARA = v("motores", "y_cara_reductora")          # 37
L_MOT = v("motores", "largo")                      # 32
L_SENS = v("robot", "L_sensores")                  # 125
XB = v("bateria", "x_centro")                      # 57
BAT = v("bateria", "dim_xyz")
ESC = v("esc", "envolvente"); ESC_C = v("esc", "centro")
PCB = v("pcb_principal", "contorno"); Z_PCB = v("pcb_principal", "z_inferior"); E_PCB = v("pcb_principal", "espesor")
Z_PCB_T = Z_PCB + E_PCB
X_BOLA = v("rueda_loca", "x"); D_BOLA = v("rueda_loca", "bola")
Z_CARA_SENS = v("barra_sensores", "z_cara_sensor")
Z_CACH = v("barra_sensores", "cachucha_z_borde")
E_BARRA = v("barra_sensores", "espesor")
Z_BARRA_B = Z_PB - E_BARRA                          # 3.5: cara inferior de la barra
ANG_SENS = (v("barra_sensores", "n") / 2 - 0.5) * v("barra_sensores", "paso_arco") / L_SENS   # rad, último sensor
TORN_FALDON = [(-29.0, 36.2), (-29.0, -36.2), (37.0, 36.2), (37.0, -36.2)]
POSTES = [(-28.0, 30.0), (-28.0, -30.0)]
BOSSES_PCB = [(0.0, 27.0), (0.0, -27.0)]
CHIMENEA = (-20.0, 22.0)
AG_BARRA = [(112.0 * math.cos(math.radians(a)), 112.0 * math.sin(math.radians(a))) for a in (21.0, -21.0)] + [(112.0, 0.0)]
SOP_Y = (22.0, 35.0)                               # |y| de las abrazaderas de motor
SOP_TORN = [(8.75, 23.5), (-8.75, 23.5), (8.75, 33.5), (-8.75, 33.5)]


# ------------------------------------------------------------------------------------------------ utilidades
def caja(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0).translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))


def cil(x, y, z0, z1, d):
    return cq.Workplane("XY").circle(d / 2).extrude(z1 - z0).translate((x, y, z0))


def poligono(pts, z0, z1):
    return cq.Workplane("XY").polyline(pts).close().extrude(z1 - z0).translate((0, 0, z0))


def sector(r0, r1, a, y_max, z0, z1, n=60):
    """Sector anular de radios r0-r1 y semiángulo a (rad), recortado a |y| <= y_max."""
    pts = [(r0 * math.cos(t), r0 * math.sin(t)) for t in np.linspace(-a, a, n)]
    pts += [(r1 * math.cos(t), r1 * math.sin(t)) for t in np.linspace(a, -a, n)]
    s = poligono(pts, z0, z1)
    return s.intersect(caja(r0 - 5, r1 + 5, -y_max, y_max, z0 - 1, z1 + 1))


# ------------------------------------------------------------------------------------------------ chasis
def chasis():
    # contorno de la placa: cuerpo entre ruedas (más ancho fuera de las llantas), cuello y sector de la barra
    cuerpo = caja(X_TR, 47.0, -39.5, 39.5, Z_PB, Z_PT)
    for s in (1, -1):    # muesca de las llantas (con 2 mm de holgura en x y 1.5 en y)
        cuerpo = cuerpo.cut(caja(-R_RUEDA - 2.0, R_RUEDA + 2.0, s * 37.5, s * 45, Z_PB - 1, Z_PT + 1) if s > 0 else
                            caja(-R_RUEDA - 2.0, R_RUEDA + 2.0, -45, -37.5, Z_PB - 1, Z_PT + 1))
    cuello = poligono([(40, 36), (70, 36), (98, 12.5), (98, -12.5), (70, -36), (40, -36)], Z_PB, Z_PT)
    frente = sector(97.5, 131.0, math.radians(25), 45.5, Z_PB, Z_PT)
    p = cuerpo.union(cuello).union(frente)
    # alojamiento del ventilador del usuario: bolsillo para el realce de la base, entrada Ø20 y 4 tornillos
    p = p.cut(caja(XF - 16.1, XF + 16.1, -16.1, 16.1, Z_PT - 0.9, Z_PT + 1))
    p = p.cut(cil(XF, 0, Z_PB - 1, Z_PT + 1, v("ventilador", "entrada_placa")))
    for sx in (1, -1):
        for sy in (1, -1):
            p = p.cut(cil(XF + sx * 15, sy * 15, Z_PB - 1, Z_PT + 1, 1.8))
    # cunas de los motores (los motores se apoyan en z = 11) con agujeros ciegos para tornillo autorroscante
    for s in (1, -1):
        y0, y1 = sorted((s * SOP_Y[0], s * SOP_Y[1]))
        p = p.union(caja(-11, 11, y0, y1, Z_PT - 0.01, 11.0))
        for x, y in SOP_TORN:
            p = p.cut(cil(x, s * y, Z_PB + 0.6, 11.01, 1.8))
    # postes traseros de la PCB principal (agujero ciego: la cámara queda sellada)
    for x, y in POSTES:
        p = p.union(cil(x, y, Z_PT - 0.01, Z_PCB, 6.0)).cut(cil(x, y, Z_PCB - 8.0, Z_PCB + 0.1, 1.8))
    # chimenea al sensor de presión de la cámara (la PCB apoya sobre un empaque de 1 mm)
    cx, cy = CHIMENEA
    p = p.union(cil(cx, cy, Z_PT - 0.01, Z_PCB - 1.0, 8.0)).cut(cil(cx, cy, Z_PB - 1, Z_PCB, 4.0))
    # bahía del ESC (cinta Dual Lock dentro; el ESC pesa < 10 g, C09)
    ex, ey = ESC_C
    bx0, bx1 = ex - ESC[0] / 2 - 0.3, ex + ESC[0] / 2 + 0.3
    by0, by1 = ey - ESC[1] / 2 - 0.3, ey + ESC[1] / 2 + 0.3
    p = p.union(caja(bx0 - 1.2, bx1 + 1.2, by0 - 1.2, by1 + 1.2, Z_PT - 0.01, Z_PT + 3.0).cut(caja(bx0, bx1, by0, by1, Z_PT - 0.5, Z_PT + 4)))
    p = p.cut(caja(bx0 - 2, bx0 + 3, -3, 3, Z_PT, Z_PT + 4))          # salida de cables del ESC hacia atrás
    # portabaterías: rieles laterales, topes y ranuras para la correa (fuera de la cámara)
    for s in (1, -1):
        y0, y1 = sorted((s * (BAT[1] / 2 + 0.3), s * (BAT[1] / 2 + 1.8)))
        p = p.union(caja(XB - BAT[0] / 2, XB + BAT[0] / 2, y0, y1, Z_PT - 0.01, Z_PT + 7.0))
        y0, y1 = sorted((s * 32.8, s * 34.8))
        p = p.cut(caja(XB - 4.5, XB + 4.5, y0, y1, Z_PB - 1, Z_PT + 1))
    for sx in (1, -1):
        x0 = XB + sx * (BAT[0] / 2 + 0.3)
        p = p.union(caja(min(x0, x0 + sx * 1.5), max(x0, x0 + sx * 1.5), -12, 12, Z_PT - 0.01, Z_PT + 4.0))
    # rueda loca: alojamiento bajo la placa con labio de retención (abertura Ø5.6 < bola 6.35)
    p = p.union(cil(X_BOLA, 0, 1.0, Z_PB + 0.01, 11.0))
    p = p.cut(cil(X_BOLA, 0, 1.6, Z_PT + 1, D_BOLA + 0.55)).cut(cil(X_BOLA, 0, 0.5, 1.7, 5.8))
    # ventana sobre los componentes de la barra de sensores y agujeros de sus tornillos
    p = p.cut(sector(102.5, 120.6, math.radians(19.6), 60, Z_PB - 1, Z_PT + 1))
    for x, y in AG_BARRA[:2]:
        p = p.cut(cil(x, y, Z_PB - 1, Z_PT + 1, 2.2))
    # tornillos del faldón
    for x, y in TORN_FALDON:
        p = p.cut(cil(x, y, Z_PB - 1, Z_PT + 1, 2.2))
    return p


def borde_faldon(delta=None):
    """Alturas del borde del faldón (trasero, delantero; mm sobre el piso con la geometría del CAD = llantas sin
    comprimir) para la compresión de llanta de diseño delta (m): sim/v2/fase35.py, modelo sim/v2/hundimiento.py."""
    d = v("fase35", "compresion_llanta_diseno") if delta is None else delta
    S, _ = F35.suspension(d)
    e_t, e_d = F35.borde_faldon(S)
    return e_t * 1e3, e_d * 1e3, S


def faldon(delta=None):
    """Cámara de succión: marco de 70 × 70 mm interior, pared de 1.2 mm. El borde NO es horizontal: sube hacia atrás
    para que, con las llantas comprimidas por la succión y las cargas dinámicas (fase35.py), quede siempre a ≥ 0.5 mm
    de la pista. Tornillos desde ARRIBA (autorroscantes en los refuerzos): nada sobresale por debajo del borde."""
    e_t, e_d, _ = borde_faldon(delta)
    x0, x1 = CAM_X - CAM_IN, CAM_X + CAM_IN
    xa, xb = x0 - CAM_W, x1 + CAM_W
    f = caja(xa, xb, -CAM_IN - CAM_W, CAM_IN + CAM_W, 0.0, Z_PB).cut(caja(x0, x1, -CAM_IN, CAM_IN, -1, Z_PB + 1))
    pend = (e_d - e_t) / (xb - xa)
    for x, y in TORN_FALDON:
        zb = e_t + pend * (x - xa) + 1.0
        f = f.union(cil(x, y, zb, Z_PB, 4.6)).cut(cil(x, y, zb + 0.6, Z_PB + 1, 1.8))
    ext = 10.0
    cuna = (cq.Workplane("XZ").polyline([(xa - ext, -5), (xb + ext, -5), (xb + ext, e_d + pend * ext), (xa - ext, e_t - pend * ext)])
            .close().extrude(60, both=True))
    return f.cut(cuna)


def tapa_motor(s):
    """Tapa de la abrazadera del motor (s = 1 izquierdo, -1 derecho) con el apoyo de la PCB principal encima."""
    y0, y1 = sorted((s * SOP_Y[0], s * SOP_Y[1]))
    t = caja(-11, 11, y0, y1, 11.0, 23.0).cut(caja(-6.15, 6.15, y0 - 1, y1 + 1, 10.9, 21.15))
    for x, y in SOP_TORN:
        t = t.cut(cil(x, s * y, 10, 24, 2.2)).cut(cil(x, s * y, 22.0, 24, 4.0))
    bx, by = BOSSES_PCB[0 if s > 0 else 1]
    t = t.union(cil(bx, by, 22.99, Z_PCB, 5.0)).cut(cil(bx, by, Z_PCB - 4.0, Z_PCB + 0.1, 1.8))
    return t


def cachucha():
    """Escudo de luz de la barra de sensores: brida contra la cara inferior de la barra con una ventana alrededor
    de los 16 sensores y paredes hasta Z_CACH del piso."""
    a_v = ANG_SENS + math.radians(1.1)
    brida = sector(108.5, 130.5, math.radians(24), 45.5, Z_BARRA_B - 1.0, Z_BARRA_B)
    ventana = sector(121.6, 128.4, a_v, 60, Z_BARRA_B - 2, Z_BARRA_B + 1)
    c = brida.cut(ventana)
    marco = sector(120.4, 129.6, a_v + math.radians(0.55), 60, Z_CACH, Z_BARRA_B - 0.99).cut(
        sector(121.6, 128.4, a_v, 60, Z_CACH - 1, Z_BARRA_B))
    c = c.union(marco)
    for x, y in AG_BARRA:
        c = c.cut(cil(x, y, 0, 6, 2.2))
    return c


def tapa_bola():
    return cil(X_BOLA, 0, Z_PT, Z_PT + 1.0, 10.0).union(cil(X_BOLA, 0, Z_PT - 0.6, Z_PT, D_BOLA + 0.4))


# ------------------------------------------------------------------------------------------------ compras (APROX)
def motor(s):
    y = lambda a, b: sorted((s * a, s * b))   # noqa: E731
    zc = R_RUEDA
    red = caja(-6, 6, *y(Y_CARA - 9.0, Y_CARA), zc - 5, zc + 5)
    mot = caja(-6, 6, *y(12.6, Y_CARA - 9.0), zc - 5, zc + 5)
    enc = caja(-7.5, 7.5, *y(Y_CARA - L_MOT, 12.6), 9.5, 22.5)
    eje = cq.Workplane("XZ").circle(1.5).extrude(-9.0 if s > 0 else 9.0).translate((0, s * Y_CARA, zc))
    return red.union(mot).union(enc).union(eje)


def rueda(s):
    w = cq.Workplane("XZ").circle(R_RUEDA).circle(1.5).extrude(-A_RUEDA if s > 0 else A_RUEDA)
    return w.translate((0, s * (Y_RUEDA - A_RUEDA / 2), R_RUEDA))


def ventilador_aprox():
    """Conjunto del usuario simplificado para el STEP (las mallas reales se usan en la verificación)."""
    base = caja(XF - 19, XF + 19, -19, 19, Z_PT, Z_PT + 1.05).union(caja(XF - 15.9, XF + 15.9, -15.9, 15.9, Z_PT - 0.85, Z_PT))
    base = base.cut(cil(XF, 0, 0, 20, 18.6))
    pil = [caja(XF + sx * 15 - 2.75, XF + sx * 15 + 2.75, sy * 15 - 2.4, sy * 15 + 2.4, Z_PT + 1.05, Z_PT + 23.05)
           for sx in (1, -1) for sy in (1, -1)]
    sop = caja(XF - 17.9, XF + 17.9, -17.9, 17.9, 30.75, 32.75)
    rotor = cil(XF, 0, 9.35, 17.35, 34.0)
    mot = cil(XF, 0, 17.35, 30.75, 14.3)
    r = base.union(sop)
    for q in pil:
        r = r.union(q)
    return r, rotor, mot


def pcb_principal():
    x0, x1, y0, y1 = PCB
    p = caja(x0, x1, y0, y1, Z_PCB, Z_PCB_T)
    for x, y in POSTES + BOSSES_PCB:
        p = p.cut(cil(x, y, Z_PCB - 1, Z_PCB_T + 1, 2.2))
    return p


def componentes_pcb():
    """Bloques de los componentes altos de la PCB principal (posiciones de principal.py), para accesibilidad."""
    t = Z_PCB_T
    c = {
        "zocalos_modulo": caja(-35.03 - 1.3, -7.09 + 1.3, 9.16, 13.7, t, t + 8.5).union(caja(-35.03 - 1.3, -7.09 + 1.3, -13.7, -9.16, t, t + 8.5)),
        "XT30": caja(-38.6, -33.4, -34.1, -23.9, t, t + 8.0),
        "interruptor": caja(-42.6, -37.8, -23.3, -14.7, t, t + 4.4),
        "fusible": caja(-31.5, -20.5, -32.4, -28.6, t, t + 11.0),
        "START_CAL": caja(-41.5, -35.5, 21.0, 27.0, t, t + 3.1).union(caja(-41.5, -35.5, 28.5, 34.5, t, t + 3.1)),
        "RESET": caja(-41.0, -38.0, 15.75, 18.25, t, t + 1.6),
        "zumbador": caja(-19.0, -7.0, 21.5, 33.5, t, t + 3.0),
        "J2_J3_J4": caja(2.4, 6.6, 25.0, 35.0, t, t + 4.25).union(caja(2.4, 6.6, 23.5, 29.5, t, t + 4.25))
                    .union(caja(2.4, 6.6, -20.0, -14.0, t, t + 4.25)),
        "J6_ESC": caja(-34.3, -31.7, -22.3, -14.7, t, t + 8.5),
    }
    return c


def modulo_weact():
    """Modelo 3D oficial del módulo (repositorio WeAct), sin sus tiras de pines; centro en (-23.86, 0), USB hacia -x."""
    if not WEACT_STEP or not os.path.exists(WEACT_STEP):
        return caja(-42.0, -5.72, -14.07, 14.07, Z_PCB_T + 8.5, Z_PCB_T + 8.5 + 1.6)
    s = cq.importers.importStep(WEACT_STEP)
    sol = [x for x in s.val().Solids() if not (abs(x.Volume() - 390.1) < 1.0)]
    comp = cq.Compound.makeCompound(sol)
    return cq.Workplane("XY").add(comp.translate(cq.Vector(-23.86 - 18.14, -14.07, Z_PCB_T + 8.5 + 1.59)))


def barra_sensores():
    if not os.path.exists(BARRA_STEP):
        return sector(100, 130, math.radians(22.5), 45, Z_BARRA_B, Z_PB)
    s = cq.importers.importStep(BARRA_STEP)
    bb = s.val().BoundingBox()
    # La barra mide R 100-130 y |y| <= 45; los sensores (1.45 mm) son lo más bajo: zmin -> Z_CARA_SENS
    dx = 100.0 * math.cos(math.radians(22.5)) - bb.xmin if bb.xmin < 50 else 0.0
    dx = 92.388 - bb.xmin
    dy = -(bb.ymin + bb.ymax) / 2
    dz = Z_CARA_SENS - bb.zmin - 0.035     # el STEP de KiCad incluye el cobre exterior
    return cq.Workplane("XY").add(s.val().translate(cq.Vector(dx, dy, dz)))


# ------------------------------------------------------------------------------------------------ mallas del usuario
def mallas_ventilador():
    """Mallas OBJ del usuario en el marco del robot. OBJ: y vertical; base centrada en x = -39.75; el rotor viene
    aparte en el origen con el disco abajo (y -1) y el ojo arriba (y 7): se voltea para que el ojo mire a la base."""
    out = {}
    for f in sorted(glob.glob(os.path.join(OBJ_DIR, "*.obj"))):
        m = trimesh.load(f, force="mesh", process=False)
        m.merge_vertices(merge_tex=True, merge_norm=True); m.process()
        nombre = os.path.basename(f).replace("ATS1.obj", "")
        V = m.vertices.copy()
        if nombre == "Ventilador":
            xr, yr, zr = V[:, 0] + XF, V[:, 2], (7.0 - V[:, 1]) + 9.35
        else:
            xr, yr, zr = V[:, 0] + 39.75 + XF, V[:, 2], V[:, 1] + 18.35
        m.vertices = np.column_stack([xr, yr, zr])
        if nombre == "Ventilador":
            m.invert()                      # la reflexión invierte la orientación de las caras
        if nombre == "Pilar":
            cx, cy = m.bounds.mean(axis=0)[:2]
            copias = []
            for sx in (1, -1):
                for sy in (1, -1):
                    c = m.copy(); c.apply_translation([XF + sx * 15 - cx, sy * 15 - cy, 0]); copias.append(c)
            out[nombre] = trimesh.util.concatenate(copias)
        else:
            out[nombre] = m
    return out


def a_malla(forma, tol=0.05):
    sh = forma.val() if hasattr(forma, "val") else forma
    if hasattr(forma, "vals") and len(forma.vals()) > 1:
        sh = cq.Compound.makeCompound(forma.vals())
    vs, ts = sh.tessellate(tol, 0.3)
    return trimesh.Trimesh(np.array([p.toTuple() for p in vs]), np.array(ts), process=True)


# ------------------------------------------------------------------------------------------------ principal
def main():
    print("V2 CAD: piezas impresas")
    impresas = {"chasis": chasis(), "faldon_camara": faldon(), "tapa_motor_izq": tapa_motor(1), "tapa_motor_der": tapa_motor(-1),
                "cachucha_sensores": cachucha(), "tapa_rueda_loca": tapa_bola()}
    for n, f in impresas.items():
        cq.exporters.export(f, os.path.join(SAL["step"], f"{n}.step"))
        cq.exporters.export(f, os.path.join(SAL["stl"], f"{n}.stl"), tolerance=0.02, angularTolerance=0.2)
    variantes = {}
    for d in v("fase35", "variantes_compresion"):
        nombre = f"faldon_camara_llanta_{d * 1e3:.1f}mm".replace(".", "p")
        e_t, e_d, _ = borde_faldon(d)
        variantes[nombre] = {"compresion_llanta_mm": d * 1e3, "borde_trasero_mm": round(e_t, 2), "borde_delantero_mm": round(e_d, 2)}
        cq.exporters.export(faldon(d), os.path.join(SAL["stl"], f"{nombre}.stl"), tolerance=0.02, angularTolerance=0.2)
    print("V2 CAD: compras y PCB")
    vent, rotor, mot_v = ventilador_aprox()
    compras = {"motor_izq_APROX": motor(1), "motor_der_APROX": motor(-1), "rueda_izq": rueda(1), "rueda_der": rueda(-1),
               "bateria_APROX": caja(XB - BAT[0] / 2, XB + BAT[0] / 2, -BAT[1] / 2, BAT[1] / 2, Z_PT, Z_PT + BAT[2]),
               "esc_APROX": caja(ESC_C[0] - ESC[0] / 2, ESC_C[0] + ESC[0] / 2, ESC_C[1] - ESC[1] / 2, ESC_C[1] + ESC[1] / 2,
                                 Z_PT, Z_PT + ESC[2]),
               "bola": cq.Workplane("XY").sphere(D_BOLA / 2).translate((X_BOLA, 0, D_BOLA / 2)),
               "ventilador_montaje_APROX": vent, "ventilador_rotor_APROX": rotor, "ventilador_motor_1104_APROX": mot_v,
               "pcb_principal": pcb_principal(), "modulo_weact": modulo_weact(), "barra_sensores_pcba": barra_sensores()}
    for k, f in componentes_pcb().items():
        compras[f"pcb_{k}_APROX"] = f

    # ---------------------------------------------------------------- interferencias (sólidos)
    print("V2 CAD: interferencias")
    todos = {**impresas, **compras}
    nombres = list(todos)
    cajas = {n: todos[n].val().BoundingBox() if len(todos[n].vals()) == 1 else
             cq.Compound.makeCompound(todos[n].vals()).BoundingBox() for n in nombres}
    choques = []
    excluir = {frozenset(("pcb_principal", k)) for k in todos if k.startswith("pcb_") and k != "pcb_principal"}
    excluir |= {frozenset(("modulo_weact", "pcb_zocalos_modulo_APROX")), frozenset(("ventilador_rotor_APROX", "ventilador_motor_1104_APROX"))}
    for i, a in enumerate(nombres):
        for b in nombres[i + 1:]:
            if frozenset((a, b)) in excluir:
                continue
            A, B = cajas[a], cajas[b]
            if A.xmax < B.xmin or B.xmax < A.xmin or A.ymax < B.ymin or B.ymax < A.ymin or A.zmax < B.zmin or B.zmax < A.zmin:
                continue
            try:
                vol = todos[a].intersect(todos[b]).val().Volume()
            except Exception:
                vol = 0.0
            if vol > 0.5:
                choques.append((a, b, round(vol, 2)))
    # mallas reales del ventilador del usuario contra el chasis y las demás piezas
    mallas = mallas_ventilador()
    vent_real = trimesh.util.concatenate(list(mallas.values()))
    vent_real.export(os.path.join(SAL["stl"], "ventilador_usuario_en_robot.stl"))
    choques_malla = []
    for mm in mallas.values():
        trimesh.repair.fix_normals(mm)
    for n in ("chasis", "tapa_motor_izq", "tapa_motor_der", "motor_izq_APROX", "motor_der_APROX", "bateria_APROX",
              "pcb_principal", "esc_APROX"):
        M = a_malla(todos[n]); trimesh.repair.fix_normals(M)
        for mn, mm in mallas.items():
            try:
                inter = trimesh.boolean.intersection([M, mm], engine="manifold")
                vol = float(inter.volume) if inter is not None and len(inter.faces) else 0.0
            except Exception as e:  # noqa: BLE001
                print("   malla", n, mn, "no comprobable:", str(e)[:80]); vol = float("nan")
            if not (vol <= 0.5):
                choques_malla.append((n, mn, round(vol, 2)))
    # holguras útiles
    holg = {
        "rotor_a_base_mm": 9.35 - (Z_PT + 1.05),
        "pilar_trasero_a_abrazadera_mm": SOP_Y[0] - (15 + 2.4),      # en y (en x se traslapan: 9.75 contra 11)
        "entrada_a_pared_camara_mm": (CAM_X + CAM_IN) - (XF + v("ventilador", "entrada_placa") / 2),
        "pared_camara_a_llanta_mm": (Y_RUEDA - A_RUEDA / 2) - (CAM_IN + CAM_W),
        "faldon_al_piso_mm": RANURA, "cachucha_al_piso_mm": Z_CACH, "cara_sensor_al_piso_mm": Z_CARA_SENS,
        "encoder_a_pcb_mm": Z_PCB - 22.5,
    }

    # ---------------------------------------------------------------- masa y CG
    print("V2 CAD: masa y CG")
    DENS = 1.24e-3    # g/mm³ PLA sólido (cota superior: la impresión con relleno pesa menos)
    masas = []
    for n, f in impresas.items():
        vol = f.val().Volume()
        c = f.val().Center()
        masas.append((n, vol * DENS, c.toTuple(), "calculado (volumen CAD × 1.24 g/cm³, PLA sólido)"))
    for n, f, m, tipo in (
        ("motor_izq", compras["motor_izq_APROX"], 11.0, "verificado (Pololu #5183)"),
        ("motor_der", compras["motor_der_APROX"], 11.0, "verificado (Pololu #5183)"),
        ("rueda_izq", compras["rueda_izq"], 3.12, "verificado (Pololu #1087, par 6.24 g)"),
        ("rueda_der", compras["rueda_der"], 3.12, "verificado (Pololu #1087)"),
        ("bateria", compras["bateria_APROX"], 28.4, "verificado (vendedor; la tabla también dice 37 g)"),
        ("esc", compras["esc_APROX"], 4.0, "supuesto (ESC 20 A de un canal)"),
        ("bola", compras["bola"], 1.05, "verificado (V1)"),
        ("ventilador_motor", compras["ventilador_motor_1104_APROX"], 6.0, "estimado (1104 de referencia 5.1-5.9 g)"),
        ("ventilador_rotor", compras["ventilador_rotor_APROX"], 1986.6 * 1.01e-3, "calculado (malla del usuario, PA12)"),
        ("ventilador_montaje", compras["ventilador_montaje_APROX"], (1279.6 + 702.2 + 4 * 405.3) * 1.01e-3, "calculado (mallas del usuario, PA12)"),
        ("pcb_principal_placa", compras["pcb_principal"], None, "calculado (FR-4 1.85 g/cm³)"),
        ("pcb_principal_componentes", compras["pcb_principal"], 8.0, "estimado"),
        ("modulo_weact_y_zocalos", compras["pcb_zocalos_modulo_APROX"], 8.0, "estimado"),
        ("barra_sensores_pcba", compras["barra_sensores_pcba"], None, "calculado (FR-4) + 1.5 g de componentes"),
        ("tornilleria_cables_cinta", compras["pcb_principal"], 8.0, "estimado"),
    ):
        sh = f.val() if len(f.vals()) == 1 else cq.Compound.makeCompound(f.vals())
        if m is None:
            if n.startswith("pcb_principal"):
                m = (PCB[1] - PCB[0]) * (PCB[3] - PCB[2]) * E_PCB * 1.85e-3
            else:
                m = 0.5 * (130 ** 2 - 100 ** 2) * math.radians(45) * E_BARRA * 1.85e-3 + 1.5
        bb = sh.BoundingBox()
        c = ((bb.xmin + bb.xmax) / 2, (bb.ymin + bb.ymax) / 2, (bb.zmin + bb.zmax) / 2)
        masas.append((n, m, c, tipo))
    M = sum(m for _, m, _, _ in masas)
    cg = tuple(sum(m * c[i] for _, m, c, _ in masas) / M for i in range(3))
    # estabilidad: el apoyo delantero debe seguir cargado al acelerar a; con la succión centrada en CAM_X
    b = X_BOLA
    a_max_sin_vuelco = 9.81 * cg[0] / cg[2]
    carga_apoyo = (M * 9.81e-3) * cg[0] / b
    prop = {"masa_total_g": round(M, 1), "cg_mm": [round(x, 1) for x in cg], "x_apoyo_mm": b,
            "a_max_sin_levantar_apoyo_ms2_sin_succion": round(a_max_sin_vuelco, 1),
            "carga_estatica_apoyo_N": round(carga_apoyo, 3), "densidad_impresas": "PLA sólido 1.24 g/cm³ (cota superior)",
            "piezas": [{"pieza": n, "masa_g": round(m, 2), "centro_mm": [round(x, 1) for x in c], "tipo": t} for n, m, c, t in masas]}
    json.dump(prop, open(os.path.join(MEC, "propiedades_masa.json"), "w"), indent=1, ensure_ascii=False)
    ver = {"interferencias_solidos": choques, "interferencias_mallas_usuario": choques_malla, "holguras_mm": holg,
           "largo_mm": None, "ancho_mm": None}

    # ---------------------------------------------------------------- ensamble, dimensiones, vistas, planos
    print("V2 CAD: ensamble y vistas")
    asm = cq.Assembly(name="speed_follower_v2")
    colores = {}
    paleta = {"chasis": (0.15, 0.17, 0.2), "faldon_camara": (0.85, 0.45, 0.1), "cachucha_sensores": (0.85, 0.45, 0.1),
              "tapa_motor_izq": (0.3, 0.32, 0.36), "tapa_motor_der": (0.3, 0.32, 0.36), "tapa_rueda_loca": (0.3, 0.32, 0.36),
              "pcb_principal": (0.05, 0.35, 0.15), "modulo_weact": (0.1, 0.2, 0.55), "barra_sensores_pcba": (0.05, 0.35, 0.15),
              "bateria_APROX": (0.75, 0.75, 0.2), "esc_APROX": (0.2, 0.2, 0.25)}
    for n, f in todos.items():
        col = paleta.get(n, (0.6, 0.6, 0.62) if "motor" in n else (0.25, 0.25, 0.27) if "rueda" in n else (0.7, 0.7, 0.72))
        colores[n] = col
        asm.add(f, name=n, color=cq.Color(*col, 1.0))
    asm.save(os.path.join(SAL["step"], "robot_v2_completo.step"))
    comp = cq.Compound.makeCompound([s for f in todos.values() for s in f.vals()])
    bb = comp.BoundingBox()
    ver["largo_mm"] = round(bb.xlen, 1); ver["ancho_mm"] = round(bb.ylen, 1); ver["alto_mm"] = round(bb.zlen, 1)
    ver["extremos_mm"] = [round(bb.xmin, 1), round(bb.xmax, 1), round(bb.ymin, 1), round(bb.ymax, 1), round(bb.zmin, 2), round(bb.zmax, 1)]
    ver["cabe_en_caja_192x92"] = bool(round(bb.xlen, 1) <= 192.0 and round(bb.ylen, 1) <= 92.0)   # la caja OCC suma tolerancia
    ver["lo_mas_bajo_sin_contacto_mm"] = round(min(cajas[n].zmin for n in nombres if n not in ("bola", "rueda_izq", "rueda_der")), 2)
    # holgura con el chasis hundido (llantas comprimidas, succión máxima con 500 Pa, cargas dinámicas): cada vértice bajo
    # z = 8 mm de cada pieza que no toca el piso, contra la envolvente de hundimiento; mínimo exigido 0.5 mm
    _, _, S = borde_faldon()
    peor = []
    for n in nombres:
        if n in ("bola", "rueda_izq", "rueda_der"):
            continue
        try:
            mm = a_malla(todos[n], tol=0.1)
        except Exception:
            continue
        vb = mm.vertices[mm.vertices[:, 2] < 8.0]
        if not len(vb):
            continue
        h = np.array([z - 1e3 * S.envolvente(x / 1e3, y / 1e3) for x, y, z in vb])
        h0 = np.array([z - 1e3 * S.envolvente_sin_succion(x / 1e3, y / 1e3) for x, y, z in vb])
        i = int(np.argmin(h))
        peor.append((n, round(float(h[i]), 3), [round(float(c), 1) for c in vb[i]], round(float(h0.min()), 3)))
    peor.sort(key=lambda r: r[1])
    ver["holgura_con_hundimiento_mm"] = [{"pieza": n, "holgura_peor_caso_mm": h, "punto_mm": p, "holgura_sin_succion_mm": h0}
                                         for n, h, p, h0 in peor[:6]]
    ver["holgura_minima_con_hundimiento_mm"] = peor[0][1]
    ver["cumple_margen_0p5mm"] = bool(peor[0][1] >= 0.5 - 1e-3)
    ver["faldon_variantes"] = variantes
    ver["compresion_llanta_diseno_mm"] = v("fase35", "compresion_llanta_diseno") * 1e3
    json.dump(ver, open(os.path.join(MEC, "verificacion_mecanica.json"), "w"), indent=1, ensure_ascii=False)
    piezas_vista = [(n, f, colores[n]) for n, f in todos.items() if n not in ("ventilador_montaje_APROX", "ventilador_rotor_APROX")]
    VI.renders(piezas_vista, [(vent_real, (0.92, 0.92, 0.95))], SAL["render"], prefijo="robot_v2")
    VI.renders([(n, f, colores[n]) for n, f in impresas.items()], [(vent_real, (0.92, 0.92, 0.95))], SAL["render"],
               prefijo="chasis_v2", vistas=("isometrica", "inferior", "superior"))
    for n, f in impresas.items():
        VI.plano_pieza(n, f.val(), SAL["planos"], "Impresión 3D: PLA/PETG (FDM, 0.2 mm, 4 perímetros) o PA12 (MJF)")
    print(json.dumps({"masa_g": prop["masa_total_g"], "cg": prop["cg_mm"], "choques": choques, "choques_malla": choques_malla,
                      "dim": ver["extremos_mm"], "caja": ver["cabe_en_caja_192x92"], "holguras": holg}, ensure_ascii=False, indent=0))


if __name__ == "__main__":
    main()
