#!/usr/bin/env python3
"""Legaliza la colocación: mueve lo mínimo posible las piezas no fijas cuyos cortijos se traslapan, salen del
contorno o caen en las zonas de los soportes. Escribe colocacion.json (marco del robot) para pcb_plan.py."""
import json
import math
import os
import sys

from shapely import affinity
from shapely.geometry import Polygon, box

AQUI = os.path.dirname(os.path.abspath(__file__))
GEOM = os.path.join(AQUI, "geometria_pcb.json")
PLAN = os.path.join(AQUI, "plan_pcb.json")
SAL = os.path.join(AQUI, "colocacion.json")
FIJAS_PREF = ("U1", "J1", "J2", "J3", "SW1", "H", "U1")
BORDE_EXENTO = {"SW1"}            # interruptor de borde: el actuador sobresale a propósito


def main():
    G = json.load(open(GEOM)); plan = json.load(open(PLAN))
    X0, Y0 = plan["X0"], plan["Y0"]
    partes = {p["ref"]: p for p in plan["partes"]}
    borde = Polygon(plan["contorno"]).buffer(-0.25)
    zonas = [box(*z) for z in plan["zonas_prohibidas"]]
    piezas = []
    for h in G["huellas"]:
        if len(h["cortijo"]) < 3:
            continue
        fija = h["ref"].startswith(FIJAS_PREF) or h["lado"] == "B" and h["ref"].startswith("U")
        piezas.append(dict(ref=h["ref"], lado=h["lado"], poly=Polygon(h["cortijo"]).buffer(0), X=h["X"], Y=h["Y"],
                           fija=fija, area=Polygon(h["cortijo"]).area))
    coloc = json.load(open(SAL)) if os.path.exists(SAL) else {}

    def choca(pz, poly, ignorar):
        if pz["ref"] not in BORDE_EXENTO and not borde.contains(poly):
            return True
        if pz["lado"] == "F" and not pz["ref"].startswith("H"):
            for z in zonas:
                if poly.intersection(z).area > 1e-3:
                    return True
        for q in piezas:
            if q is pz or q["lado"] != pz["lado"] or q["ref"] in ignorar:
                continue
            if poly.intersects(q["poly"]) and poly.intersection(q["poly"]).area > 1e-3:
                return True
        return False

    movidas = 0
    orden = sorted([p for p in piezas if not p["fija"]], key=lambda p: -p["area"])
    for it in range(3):
        cambios = 0
        for pz in orden:
            if not choca(pz, pz["poly"], ()):
                continue
            mejor = None
            for r in [0.25 * k for k in range(1, 61)]:
                for a in range(0, 360, 15):
                    dx, dy = r * math.cos(math.radians(a)), r * math.sin(math.radians(a))
                    cand = affinity.translate(pz["poly"], dx, dy)
                    if not choca(pz, cand, ()):
                        mejor = (dx, dy, cand)
                        break
                if mejor:
                    break
            if not mejor:
                print("  sin lugar para", pz["ref"])
                continue
            dx, dy, cand = mejor
            pz["poly"] = cand; pz["X"] += dx; pz["Y"] += dy
            p = partes[pz["ref"]]
            coloc[pz["ref"]] = dict(x=round(pz["X"] - X0, 3), y=round(Y0 - pz["Y"], 3), rot=p["rot"])
            cambios += 1; movidas += 1
            print(f"  {pz['ref']}: movida {math.hypot(dx, dy):.2f} mm")
        if not cambios:
            break
    json.dump(coloc, open(SAL, "w"), indent=1, sort_keys=True)
    restantes = [p["ref"] for p in piezas if choca(p, p["poly"], ())]
    print(f"{movidas} movimientos; piezas con conflicto: {restantes}")
    return 0 if not restantes else 1


if __name__ == "__main__":
    sys.exit(main())
