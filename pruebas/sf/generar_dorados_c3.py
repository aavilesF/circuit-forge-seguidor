"""Vectores dorados del control C3 (curvatura del modelo del motor y del giroscopio) y de estimar_coord,
generados con el simulador (sim/nucleo.py paso_sf), que es la referencia de la Fase 2.
Robot y parámetros: los de config/robot_maestro.yaml (los mismos que firmware/sf/config_maestra.h).
Uso: python3 generar_dorados_c3.py   (lo llama ejecutar.sh)"""
import csv
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "..", "sim"))
import config as CF  # noqa: E402
import nucleo as N  # noqa: E402
import simulador as S  # noqa: E402

rng = np.random.default_rng(11)
c = CF.construir(control="C3m")
P = S.vector_planta(c)
_, base = S.vector_control(c)
with open(os.path.join(AQUI, "dorados_c3.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["fuente", "k", "e", "dt", "vbat", "gz", "izq", "der", "v_cmd"])
    for fuente in (0, 1, 2):
        prm = base.copy()
        prm[8] = fuente
        ST = np.zeros(6); ST[5] = 1.0
        dl = dr = 0.0
        for k in range(3000):
            t = k * 0.001
            e = 0.02 * np.sin(2 * np.pi * 0.8 * t) + 0.012 * np.sin(2 * np.pi * 2.9 * t) + rng.normal(0, 0.002)
            dt = float(rng.uniform(0.0009, 0.0025))
            vbat = float(rng.uniform(6.8, 8.4))
            gz = float(6.0 * np.sin(2 * np.pi * 0.8 * t + 0.4) + rng.normal(0, 0.05))
            dl, dr = N.paso_sf(ST, float(e), dt, vbat, P, prm, dl, dr, gz)
            w.writerow([fuente, k, f"{e:.9g}", f"{dt:.9g}", f"{vbat:.9g}", f"{gz:.9g}", f"{dl:.9g}", f"{dr:.9g}", f"{ST[4]:.9g}"])
# estimar_coord con la geometría de la barra vigente
with open(os.path.join(AQUI, "dorados_coord.csv"), "w", newline="") as f:
    w = csv.writer(f)
    n = len(c.sy)
    w.writerow([f"l{i}" for i in range(n)] + ["visible", "e", "borde"])
    for k in range(500):
        lect = np.clip(rng.uniform(-0.2, 1.1, n) * (rng.uniform(size=n) < 0.35), 0, 1)
        wts = np.clip((lect - c.umbral) / (1 - c.umbral), 0, 1)
        s = wts.sum()
        vis = s >= 0.5
        e = float((wts * -c.sy).sum() / s) if vis else 0.0
        borde = bool(vis and (wts[0] > 0.3 or wts[-1] > 0.3))
        w.writerow([f"{v:.9g}" for v in lect] + [int(vis), f"{e:.9g}", int(borde)])
print("dorados_c3.csv y dorados_coord.csv escritos")
