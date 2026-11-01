"""Vectores dorados: entradas aleatorias reproducibles -> salidas del control Python (referencia).
El test C++ (test_sf.cpp) debe reproducirlas. Uso: python3 generar_dorados.py"""
import sys, math, csv
import numpy as np
sys.path.insert(0, "../sim")
from modelo import Robot, MOTORES
from control import ControlSF, ParamSF
from simular import _estimar

CASOS = [
    ("pololu15", Robot(MOTORES["Pololu HPCB 12V 15:1"], L=0.13, n_sens=8, paso=0.0095), ParamSF(v_max=1.2, kp=120, kd=4, a_lat=4.0)),
    ("ga12_6v", Robot(MOTORES["GA12-N20 6V 1000RPM (supuesto)"], L=0.13, n_sens=8, paso=0.0095, v_max_motor=6.0), ParamSF(v_max=1.3, kp=80, kd=2, a_lat=4.0)),
    ("inversion", Robot(MOTORES["Pololu HPCB 12V 15:1"], L=0.13, n_sens=8, paso=0.0095), ParamSF(v_max=1.2, kp=200, kd=6, a_lat=4.0, permitir_inversion=True)),
    ("freno", Robot(MOTORES["Pololu HPCB 12V 10:1"], L=0.13, n_sens=8, paso=0.0095), ParamSF(v_max=1.4, kp=120, kd=4, a_lat=6.0, a_lon=6.0, freno_activo=True)),
]
rng = np.random.default_rng(7)
with open("dorados_control.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["caso", "k", "e", "borde", "dt", "vbat", "izq", "der", "v_cmd"])
    for nombre, robot, prm in CASOS:
        c = ControlSF(prm)
        semi = (robot.n_sens - 1) * robot.paso / 2
        for k in range(3000):
            t = k * 0.0012
            e = 0.025 * math.sin(2 * math.pi * 0.7 * t) + 0.015 * math.sin(2 * math.pi * 3.1 * t) + float(rng.normal(0, 0.002))
            if 1200 <= k < 1300: e = 0.032 * (1 if (k // 50) % 2 else -1)   # saltos hacia el borde
            borde = abs(e) > 0.8 * semi
            dt = float(rng.uniform(0.0010, 0.0016))
            vbat = float(rng.uniform(6.6, 8.4))
            dl, dr, info = c(e, True, borde, dt, robot, vbat)
            w.writerow([nombre, k, f"{e:.9g}", int(borde), f"{dt:.9g}", f"{vbat:.9g}", f"{dl:.9g}", f"{dr:.9g}", f"{info['v_cmd']:.9g}"])
with open("dorados_estimar.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["n", "paso"] + [f"l{i}" for i in range(12)] + ["visible", "e", "borde"])
    for k in range(500):
        n = int(rng.choice([8, 12]))
        paso = 0.0095 if n == 8 else 0.008
        lect = np.clip(rng.uniform(-0.2, 1.1, n) * (rng.uniform(size=n) < 0.4), 0, 1)
        xs = (np.arange(n) - (n - 1) / 2) * paso
        e, borde = _estimar(lect, xs)
        fila = [n, paso] + [f"{x:.9g}" for x in lect] + [""] * (12 - n)
        fila += [int(e is not None), f"{(e if e is not None else 0.0):.9g}", int(borde)]
        w.writerow(fila)
print("ok")
