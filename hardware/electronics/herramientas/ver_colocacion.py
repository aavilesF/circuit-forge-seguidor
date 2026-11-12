#!/usr/bin/env python3
"""Dibuja la colocación (cortijos, pads, contorno, zonas prohibidas) desde generador/geometria_pcb.json y lista
los cortijos que se traslapan en la misma cara. Uso: ver_colocacion.py salida.png"""
import json, os, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
AQUI = os.path.dirname(os.path.abspath(__file__))
G = json.load(open(os.path.join(AQUI, "..", "generador", "geometria_pcb.json")))
plan = json.load(open(os.path.join(AQUI, "..", "generador", "plan_pcb.json")))
from shapely.geometry import Polygon as SP, box
def traslapes():
    out = []
    hs = [h for h in G["huellas"] if len(h["cortijo"]) >= 3]
    polys = [(h, SP(h["cortijo"]).buffer(0)) for h in hs]
    for i in range(len(polys)):
        for j in range(i + 1, len(polys)):
            a, pa = polys[i]; b, pb = polys[j]
            if a["lado"] != b["lado"]:
                continue
            if pa.intersects(pb) and pa.intersection(pb).area > 0.01:
                out.append((a["ref"], b["ref"], round(pa.intersection(pb).area, 2)))
    zp = [box(*z) for z in plan["zonas_prohibidas"]]
    for h, p in polys:
        if h["lado"] == "F" and not h["ref"].startswith("H"):
            for z in zp:
                if p.intersects(z) and p.intersection(z).area > 0.01:
                    out.append((h["ref"], "ZONA_SOPORTE", round(p.intersection(z).area, 2)))
    borde = SP(plan["contorno"])
    for h, p in polys:
        if h["ref"] == "SW1":     # interruptor de borde: el cortijo incluye el actuador, que sobresale a propósito 2 mm
            continue
        if not borde.buffer(0.01).contains(p):
            out.append((h["ref"], "FUERA_DEL_BORDE", round(p.difference(borde).area, 2)))
    return out
if __name__ == "__main__":
    t = traslapes()
    for x in t: print("TRASLAPE", x)
    print(len(t), "traslapes")
    if len(sys.argv) > 1:
        fig, ax = plt.subplots(1, 2, figsize=(26, 10))
        for k, lado in enumerate("FB"):
            a = ax[k]
            a.add_patch(Polygon(plan["contorno"], fill=False, ec="k"))
            for z in plan["zonas_prohibidas"]:
                a.add_patch(Polygon([(z[0], z[1]), (z[2], z[1]), (z[2], z[3]), (z[0], z[3])], fc="#fdd", ec="r"))
            for h in G["huellas"]:
                if h["lado"] != lado or len(h["cortijo"]) < 3: continue
                a.add_patch(Polygon(h["cortijo"], fill=False, ec="b", lw=0.5))
                a.text(h["X"], h["Y"], h["ref"], fontsize=5, ha="center", va="center")
            for p in G["pads"]:
                if lado in p["capas"]:
                    a.plot(p["X"], p["Y"], ".", ms=1.5, color="g" if p["red"] else "gray")
            a.set_aspect("equal"); a.invert_yaxis(); a.set_title("cara " + lado)
        plt.tight_layout(); plt.savefig(sys.argv[1], dpi=110)
