#!/usr/bin/env python3
"""V2 · Barra de sensores (PCB separable): diseño eléctrico, colocación y plan de la PCB.

16 × QRE1113GR en arco de radio L (cara INFERIOR, hacia el piso), resta de luz ambiente con los emisores conmutados por un
AO3400A, 2 multiplexores analógicos 8:1 74HC4051 (las 16 señales llegan al MCU por 2 hilos + 3 de selección) y un
conector JST SH de 8 vías hacia la PCB principal. Todo lo que no es sensor va en la cara SUPERIOR (la que toca la placa del
chasis, que tiene una ventana encima): así la cara inferior queda libre para la cachucha.

Uso: python3 hardware/v2/electronica/generador/barra_sensores.py   -> esquemático + plan_pcb.json"""
from __future__ import annotations

import json
import math
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun as K  # noqa: E402

G = yaml.safe_load(open(os.path.join(K.RAIZ, "config", "v2", "robot_v2.yaml"), encoding="utf-8"))
v = lambda sec, k: G[sec][k]["valor"]   # noqa: E731
L = v("robot", "L_sensores")
N = v("barra_sensores", "n")
PASO = v("barra_sensores", "paso_arco")
R_IN, R_OUT, Y_MAX = v("barra_sensores", "R_interior"), v("barra_sensores", "R_exterior"), v("barra_sensores", "y_max")

D = K.Diseno("barra_sensores", "Speed Follower V2 — Barra de sensores",
             [("sensores", "16 sensores QRE1113GR"), ("interfaz", "Multiplexores, emisores y conector")],
             papel={"sensores": "A2", "interfaz": "A3"}, banderas={"+3V3": "interfaz", "GND": "interfaz"})
HS, HI = "sensores", "interfaz"
# Símbolo propio con pines pasivos (como V1): el símbolo oficial marca el emisor como "open emitter" y el ERC lo
# rechaza contra la bandera de alimentación de GND aunque la conexión es la de la hoja de datos.
D.simbolos_propios.append(K.simbolo_rect("QRE1113GR", [("1", "A"), ("2", "K")], [("3", "C"), ("4", "E")], ref="U",
                                         descr="Sensor reflectivo IR onsemi QRE1113GR (LED + fototransistor), CASE 100CY",
                                         huella="OptoDevice:OnSemi_CASE100CY", ancho=7.62,
                                         tipo_por_nombre=lambda n: "passive"))


def ang(i):
    """Ángulo del sensor i (0 = el más a la izquierda, y > 0), rad."""
    return (N / 2 - 0.5 - i) * PASO / L


def polar(r, a):
    return r * math.cos(a), r * math.sin(a)


# ----------------------------------------------------------------------------------------------- sensores
for i in range(N):
    a = ang(i)
    x, y = polar(L, a)
    s = f"S{i + 1}"
    # Huella CASE100CY: pads a lo largo de su eje y local (±2 mm). El eje y local va RADIAL (el ancho tangencial es ±1.3 mm
    # y cabe en el paso de 5.5 mm). rot en el marco del robot; la cara inferior se resuelve en pcb.py.
    D.P(ref=f"U{i + 1}", lib_id=f"{K.LIB_PROPIA}:QRE1113GR", valor="QRE1113GR", huella="OptoDevice:OnSemi_CASE100CY",
        fabricante="onsemi", mpn="QRE1113GR", descripcion="Sensor reflectivo IR (LED 940 nm + fototransistor), CASE 100CY",
        hoja=HS, pines={"1": "+3V3", "2": f"K{i + 1}", "3": s, "4": "GND"}, x=x, y=y, rot=math.degrees(a) + 90, lado="B",
        datasheet=K.DS["QRE1113"])
    xe, ye = polar(118.6, a)
    D.R(f"R{i + 1}", "75", f"K{i + 1}", "EMIT_K", HS, enc="0603", x=xe, y=ye, rot=math.degrees(a))
    xp, yp = polar(115.4, a)
    D.R(f"R{i + 17}", "10k", "+3V3", s, HS, x=xp, y=yp, rot=math.degrees(a))

# ----------------------------------------------------------------------------------------------- interfaz
# Canal de cada sensor en su multiplexor: U17 lee S1-S8 (mitad izquierda), U18 lee S9-S16. El orden de canales sigue el
# arco para acortar pistas; el firmware usa la tabla CANAL de este archivo (exportada en plan_pcb.json).
CANALES_74HC4051 = {0: "13", 1: "14", 2: "15", 3: "12", 4: "1", 5: "5", 6: "2", 7: "4"}   # A0..A7 -> pin del 74HC4051
CANAL = {}
for m, (ref, salida, y0) in enumerate((("U17", "SENS_A", 17.0), ("U18", "SENS_B", -17.0))):
    pines = {"3": salida, "6": "GND", "7": "GND", "8": "GND", "9": "MUX_S2", "10": "MUX_S1", "11": "MUX_S0", "16": "+3V3"}
    orden = list(range(8)) if m == 0 else list(range(7, -1, -1))
    for k in range(8):
        sensor = 8 * m + orden[k]
        pines[CANALES_74HC4051[k]] = f"S{sensor + 1}"
        CANAL[f"S{sensor + 1}"] = (salida, k)
    D.P(ref=ref, lib_id="74xx:74HC4051", valor="74HC4051PW", huella="Package_SO:TSSOP-16_4.4x5mm_P0.65mm",
        fabricante="Nexperia", mpn="74HC4051PW,118", descripcion="Multiplexor analógico 8:1 (2-10 V), TSSOP-16",
        hoja=HI, pines=pines, x=106.5, y=y0, rot=90 if m == 0 else -90, datasheet=K.DS["74HC4051"])
    D.C(f"C{m + 1}", "100n", "+3V3", "GND", HI, x=103.2, y=y0 + (4.0 if m == 0 else -4.0), rot=90)

D.P(ref="Q1", lib_id="Transistor_FET:AO3400A", valor="AO3400A", huella="Package_TO_SOT_SMD:SOT-23",
    fabricante="Alpha & Omega Semiconductor", mpn="AO3400A", descripcion="MOSFET N 30 V 5.7 A SOT-23: conmuta los 16 emisores (≈ 0.45 A)",
    hoja=HI, pines={"1": "EMIT", "2": "GND", "3": "EMIT_K"}, x=109.0, y=-6.5, rot=180, datasheet=K.DS["AO3400A"])
D.R("R33", "100k", "EMIT", "GND", HI, x=106.0, y=-8.0, rot=0)
D.C("C3", "10u", "+3V3", "GND", HI, enc="0805", x=109.6, y=6.6, rot=90)
D.C("C4", "100n", "+3V3", "GND", HI, x=107.3, y=6.6, rot=90)
D.P(ref="J1", lib_id="Connector_Generic_MountingPin:Conn_01x08_MountingPin", valor="SENSORES",
    huella="Connector_JST:JST_SH_BM08B-SRSS-TB_1x08-1MP_P1.00mm_Vertical", fabricante="JST", mpn="BM08B-SRSS-TB",
    descripcion="Conector JST SH 8 vías vertical (cable a la PCB principal)", hoja=HI,
    pines={"1": "+3V3", "2": "EMIT", "3": "MUX_S0", "4": "MUX_S1", "5": "MUX_S2", "6": "SENS_A", "7": "SENS_B", "8": "GND",
           "MP": "GND"}, x=104.0, y=0.0, rot=-90, datasheet=K.DS["BM0xB"])
AGUJEROS = [polar(112.0, math.radians(21.0)), polar(112.0, math.radians(-21.0)), (112.0, 0.0)]
for k, (x, y) in enumerate(AGUJEROS):
    D.P(ref=f"H{k + 1}", lib_id="Mechanical:MountingHole", valor="M2", huella="MountingHole:MountingHole_2.2mm_M2",
        fabricante="—", mpn="—", descripcion="Agujero M2 (fija barra + cachucha a la placa del chasis)", hoja=HI, pines={},
        x=x, y=y, en_bom=False)


def contorno():
    """Polígono del contorno (robot, mm): sector anular R_IN-R_OUT recortado a |y| <= Y_MAX."""
    a_in = math.radians(22.5)
    r_codo = Y_MAX / math.sin(a_in)
    a_out = math.asin(Y_MAX / R_OUT)
    pts = []
    for k in range(41):                          # arco interior de -a_in a +a_in
        a = -a_in + 2 * a_in * k / 40
        pts.append(polar(R_IN, a))
    pts.append(polar(r_codo, a_in))              # borde radial izquierdo
    for k in range(41):                          # arco exterior de +a_out a -a_out
        a = a_out - 2 * a_out * k / 40
        pts.append(polar(R_OUT, a))
    pts.append(polar(r_codo, -a_in))
    return [(round(x, 4), round(y, 4)) for x, y in pts]


def nombres_red():
    """Nombre de cada red como lo pone KiCad al leer el esquemático: las locales llevan la ruta de su hoja."""
    hojas_de, titulo = {}, dict(D.hojas)
    for p in D.partes:
        for pin, r in p.pines.items():
            hojas_de.setdefault(r, set()).add(p.hoja)
    return {r: (r if (len(h) > 1 or r in D.power) else f"/{titulo[next(iter(h))]}/{r}") for r, h in hojas_de.items()}


def plan():
    nr = nombres_red()
    partes = []
    for p in D.partes:
        lib, fp = p.huella.split(":")
        partes.append(dict(ref=p.ref, valor=p.valor, lib=lib, fp=fp, X=round(p.x, 4), Y=round(K.Y0 - p.y, 4),
                           rot=round(p.rot, 3), lado=p.lado, redes={k: nr[vv] for k, vv in p.pines.items() if k not in p.nc},
                           en_bom=p.en_bom, mpn=p.mpn, fabricante=p.fabricante, hoja=p.hoja))
    return dict(
        proy=D.proy, titulo=D.titulo, capas=2, espesor=1.6, X0=0.0, Y0=K.Y0, origen_aux=[R_IN, K.Y0],
        contorno=[[x, K.Y0 - y] for x, y in contorno()], partes=partes,
        clases={"Default": dict(pista=0.2, separacion=0.2, separacion_drc=0.15, via=0.6, taladro=0.3, patrones=[]),
                "Potencia": dict(pista=0.5, separacion=0.2, separacion_drc=0.15, via=0.6, taladro=0.3, patrones=["+3V3", "GND", "*EMIT_K"])},
        planos=[dict(capa="B", red="GND"), dict(capa="F", red="GND")],
        nombres_red=nr,
        textos=[dict(texto="CIRCUIT FORGE V2 · BARRA DE SENSORES · REV A", X=102.6, Y=K.Y0, rot=90, lado="B", tam=1.0)],
        canal=CANAL)


def principal():
    err = D.verificar()
    if err:
        raise SystemExit("\n".join(err))
    K.escribir_esquematico(D, notas={"interfaz": [
        "Canales: U17 (SENS_A) lee S1-S8 (izquierda); U18 (SENS_B) lee S9-S16. Tabla CANAL en plan_pcb.json.",
        "Conector J1 = cable JST SH 8 vías a la PCB principal (J? SENSORES), mismo orden de pines en ambos extremos.",
        "Emisores: ánodo a +3V3, cátodo por 75 Ω al drenador de Q1 (EMIT alto = encendidos, ≈ 28 mA c/u)."]})
    os.makedirs(os.path.join(K.V2E, "generador", "salida"), exist_ok=True)
    ruta = os.path.join(K.V2E, "generador", "salida", "plan_barra_sensores.json")
    json.dump(plan(), open(ruta, "w"), indent=1)
    print("plan ->", os.path.relpath(ruta, K.RAIZ))


if __name__ == "__main__":
    principal()
