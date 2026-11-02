#!/usr/bin/env python3
"""Plan de la PCB (JSON) a partir de diseno.py y geometria.py; lo consume pcb_kicad.py (pcbnew de KiCad 9).

Marco: robot (x adelante, y izquierda, mm) -> KiCad: X = X0 + x, Y = Y0 − y."""
from __future__ import annotations

import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import diseno as D  # noqa: E402
import esquematico as E  # noqa: E402

X0, Y0 = 100.0, 100.0
SALIDA = os.path.join(D.RAIZ, "hardware", "electronics", "generador", "plan_pcb.json")
COLOC = os.path.join(D.RAIZ, "hardware", "electronics", "generador", "colocacion.json")

CLASES = {
    # nombre: (pista mm, separación mm, vía diámetro, vía taladro, patrones)
    "Default": (0.20, 0.15, 0.55, 0.25, []),
    "Potencia": (0.80, 0.15, 0.55, 0.25, ["VBAT_IN", "VBAT_F", "VBAT_SRC", "VBAT_SW"]),
    "Motor": (0.50, 0.15, 0.55, 0.25, ["MOT_*", "BUCK_SW"]),
    "Alimentacion": (0.40, 0.15, 0.55, 0.25, ["+3V3*", "GND", "DRV_VINT", "DRV_VCP", "EMIT_K", "K*"]),
}


def k(x, y):
    return round(X0 + x, 4), round(Y0 - y, 4)


def generar():
    G = D.G
    coloc = json.load(open(COLOC)) if os.path.exists(COLOC) else {}
    pts, arco = G.contorno_pcb()
    partes = []
    for p in D.PARTES:
        lib, fp = p.huella.split(":")
        x, y, rot, lado = p.x, p.y, p.rot, p.lado
        if p.ref in coloc:
            x, y, rot = coloc[p.ref]["x"], coloc[p.ref]["y"], coloc[p.ref]["rot"]
        X, Y = k(x, y)
        rot = round(rot, 1)            # 0.1°: con más decimales KiCad marca la huella como distinta de la biblioteca
        campos = {"Fabricante": p.fabricante, "MPN": p.mpn, "Descripcion": p.descripcion}
        if p.datasheet:
            campos["Datasheet"] = p.datasheet
        partes.append(dict(ref=p.ref, lib=lib, fp=fp, valor=p.valor, X=X, Y=Y, rot=rot, lado=lado,
                           redes={pin: red for pin, red in p.pines.items() if pin not in p.nc},
                           campos=campos, en_bom=p.en_bom,
                           ruta=f"/{E.uid('hoja', p.hoja)}/{E.uid('s', p.hoja, p.ref)}",
                           hoja=p.hoja, modelo3d=p.extra.get("modelo3d"), modelo3d_oficial=p.extra.get("modelo3d_oficial"), fijo=p.ref.startswith(("U1", "H")) or p.lado == "B"
                           or p.ref.startswith("U1") or p.ref in ("J1", "J2", "J3", "SW1")))
    # nombres de red tal como los nombra el esquemático (las etiquetas locales llevan la ruta de la hoja); si la PCB usa
    # otros nombres, la prueba de paridad del DRC los marca como conflicto de red
    nombres_red = {}
    sin_conexion = {}                 # (ref, pin) -> "unconnected-(...)": KiCad da red propia a cada pin sin conexión
    netlist = os.path.join(D.RAIZ, "hardware", "electronics", "verificacion", "netlist_esquematico.xml")
    if os.path.exists(netlist):
        import xml.etree.ElementTree as ET
        for n in ET.parse(netlist).getroot().iter("net"):
            completo = n.get("name")
            if completo.startswith("unconnected-"):
                for nodo in n.iter("node"):
                    sin_conexion[(nodo.get("ref"), nodo.get("pin"))] = completo
            else:
                nombres_red[completo.split("/")[-1]] = completo
    for parte in partes:
        for (ref, pin), nombre in sin_conexion.items():
            if ref == parte["ref"] and pin not in parte["redes"]:
                parte["redes"][pin] = nombre
    plan = dict(
        X0=X0, Y0=Y0, nombres_red=nombres_red,
        contorno=[k(x, y) for x, y in pts],
        arco=dict(centro=k(0, 0), r=arco["r"], inicio=k(*arco["p0"]), fin=k(*arco["p1"])),
        agujero_bola=dict(centro=k(G.x_apoyo, 0), diametro=6.4),
        zonas_prohibidas=[[*k(z[0], z[3]), *k(z[2], z[1])] for z in G.zonas_prohibidas_sup()],
        clases={n: dict(pista=c[0], separacion=c[1], via=c[2], taladro=c[3], patrones=c[4]) for n, c in CLASES.items()},
        partes=partes,
        textos=textos_serigrafia(partes, [k(x, y) for x, y in pts]),
        espesor=G.t_pcb, r_sensores=G.L * 1000,
    )
    json.dump(plan, open(SALIDA, "w"), indent=1, ensure_ascii=False)
    print(f"plan: {len(partes)} huellas -> {os.path.relpath(SALIDA, D.RAIZ)}")
    return plan


def textos_serigrafia(partes, contorno):
    """Rótulos funcionales de la serigrafía. Cada rótulo junto a una pieza se coloca automáticamente en la primera
    posición libre (arriba, abajo, a la derecha o a la izquierda, a distancia creciente) que no toque los cortijos
    ni los pads de otras piezas de la misma cara, ni otro rótulo, y quede dentro del borde con 0.6 mm de margen."""
    from shapely.geometry import Polygon, box
    T = []
    pos = {p["ref"]: p for p in partes}
    geom_json = os.path.join(D.RAIZ, "hardware", "electronics", "generador", "geometria_pcb.json")
    cort = []
    if os.path.exists(geom_json):
        G_ = json.load(open(geom_json))
        for h in G_["huellas"]:
            if len(h["cortijo"]) >= 3:
                cort.append((h["ref"], h["lado"], Polygon(h["cortijo"]).buffer(0)))
        for pd in G_["pads"]:
            hw, hh = pd["w"] / 2 + 0.15, pd["h"] / 2 + 0.15
            cort.append((pd["ref"], "F" if "F" in pd["capas"] else "B", box(pd["X"] - hw, pd["Y"] - hh, pd["X"] + hw, pd["Y"] + hh)))
            if "B" in pd["capas"] and "F" in pd["capas"]:
                cort.append((pd["ref"], "B", box(pd["X"] - hw, pd["Y"] - hh, pd["X"] + hw, pd["Y"] + hh)))
    rutas_json = os.path.join(D.RAIZ, "hardware", "electronics", "generador", "rutas.json")
    if os.path.exists(rutas_json):            # las vías no van tapadas por máscara: la serigrafía no debe pisarlas
        for v in json.load(open(rutas_json))["vias"]:
            r = v["d"] / 2 + 0.15
            for lado in ("F", "B"):
                cort.append(("via", lado, box(v["x"] - r, v["y"] - r, v["x"] + r, v["y"] + r)))
    borde = Polygon(contorno).buffer(-0.6)
    ocupado = []

    def caja_texto(txt, X, Y, tam):
        w = len(txt) * tam * 1.0 + 0.4; h = tam * 1.25 + 0.4      # medido en KiCad 9: ≈ 0.98·tamaño por carácter
        return box(X - w / 2, Y - h / 2, X + w / 2, Y + h / 2)

    def libre(c, lado, propio):
        if not borde.contains(c):
            return False
        if any(o.intersects(c) for o in ocupado):
            return False
        return not any(l == lado and r != propio and poly.intersects(c) for r, l, poly in cort)

    def t(txt, x, y, lado="F", tam=1.0, rot=0):
        X, Y = k(x, y)
        T.append(dict(texto=txt, X=X, Y=Y, lado=lado, tam=tam, rot=rot))
        ocupado.append(caja_texto(txt, X, Y, tam))

    def junto(ref, txt, tam=0.9, preferencia=("arriba", "abajo", "derecha", "izquierda")):
        p = pos[ref]
        mio = [poly for r, l, poly in cort if r == ref and l == p["lado"]]
        bx = mio[0].bounds if mio else (p["X"] - 1, p["Y"] - 1, p["X"] + 1, p["Y"] + 1)
        for extra in (0.4, 0.9, 1.5, 2.2, 3.0, 4.0):
            for d in preferencia:
                c0 = caja_texto(txt, 0, 0, tam).bounds
                w2, h2 = (c0[2] - c0[0]) / 2, (c0[3] - c0[1]) / 2
                X, Y = {"arriba": ((bx[0] + bx[2]) / 2, bx[1] - extra - h2), "abajo": ((bx[0] + bx[2]) / 2, bx[3] + extra + h2),
                        "derecha": (bx[2] + extra + w2, (bx[1] + bx[3]) / 2), "izquierda": (bx[0] - extra - w2, (bx[1] + bx[3]) / 2)}[d]
                c = caja_texto(txt, X, Y, tam)
                if libre(c, p["lado"], ref):
                    T.append(dict(texto=txt, X=round(X, 3), Y=round(Y, 3), lado=p["lado"], tam=tam, rot=0))
                    ocupado.append(c)
                    return
        raise SystemExit(f"sin lugar libre para el rótulo {txt!r} de {ref}")

    def libre_en(txt, candidatos, tam, lado="F", propio=None):
        for x, y in candidatos:
            X, Y = k(x, y)
            c = caja_texto(txt, X, Y, tam)
            if libre(c, lado, propio):
                T.append(dict(texto=txt, X=X, Y=Y, lado=lado, tam=tam, rot=0)); ocupado.append(c)
                return
        raise SystemExit(f"sin lugar libre para {txt!r}")
    # la huella oficial de J1 (AMASS XT30UPB-M) ya trae los signos + y − de cada pin en la serigrafía
    junto("J1", "BAT 2S", tam=1.0, preferencia=("abajo", "arriba", "izquierda", "derecha"))
    junto("J2", "ENC IZQ"); junto("J3", "ENC DER")
    junto("SW1", "ON/OFF")
    junto("SW2", "START"); junto("SW3", "CAL"); junto("SW4", "RST", tam=0.8)
    junto("J4", "SWD STDC14", tam=0.8)
    junto("D2", "3V3", tam=0.8, preferencia=("derecha", "izquierda", "arriba", "abajo"))
    junto("D3", "OK", tam=0.8, preferencia=("derecha", "izquierda", "arriba", "abajo"))
    junto("D4", "ERR", tam=0.8, preferencia=("derecha", "izquierda", "arriba", "abajo"))
    libre_en("CIRCUIT FORGE SPEED FOLLOWER v1.0", [(x, y) for y in (-27.0, -25.5, 24.0, 26.0, 20.0, -20.0) for x in (56.0, 52.0, 60.0, 48.0, 64.0)], 1.1)
    libre_en("RMX2026  4 CAPAS 1.6 mm", [(x, y) for y in (27.0, 25.0, 22.0, -24.0) for x in (56.0, 50.0, 62.0)], 1.0)
    for i in range(D.N_SENS):
        x, y, a = D.G.sensor(i)
        xt, yt = D.GEO.polar(99.0, a)
        t(f"S{i + 1}", xt, yt, lado="B", tam=0.8, rot=0)
    xa = D.G.x_apoyo
    libre_en("RUEDA LOCA 1/4 in", [(xa - dx, dy) for dx in (12.0, 14.0, 16.0, 18.0) for dy in (6.0, 8.0, -6.0, -8.0)], 0.9, lado="B")
    libre_en("CARA INFERIOR: 16 SENSORES QRE1113GR", [(x, y) for x in (60.0, 56.0, 64.0, 50.0) for y in (4.0, -4.0, 12.0, -12.0)], 1.2, lado="B")
    return T


if __name__ == "__main__":
    generar()
