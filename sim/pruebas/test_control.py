"""El controlador C2 del simulador (nucleo.paso_sf, fuente 0) debe reproducir los vectores dorados que ya
validan el C++ del firmware (firmware/logica/sf_logica.cpp). Uso: python3 sim/pruebas/test_control.py"""
import csv
import math
import os
import sys

import numpy as np

AQUI = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(AQUI, ".."))
import nucleo as N  # noqa: E402

DORADOS = os.path.join(AQUI, "..", "..", "pruebas", "sf", "dorados_control.csv")
KGCM = 0.0980665
# Casos del generador de dorados (motor, robot y parámetros de pruebas/sf/generar_dorados.py)
CASOS = {
    "pololu15": dict(motor=(12.0, 2200, 0.25 * KGCM, 0.75, 0.08), limV=99.0,
                     prm=[1.2, 4.0, 4.0, 1.0, 120.0, 4.0, 0.004, 0.030, 0]),
    "ga12_6v": dict(motor=(6.0, 1000, 0.30 * KGCM, 0.67, 0.2), limV=6.0,
                    prm=[1.3, 4.0, 4.0, 1.0, 80.0, 2.0, 0.004, 0.030, 0]),
}


def vector(caso):
    V, rpm, Ts, Is, I0 = caso["motor"]
    R = V / Is
    w0 = rpm * 2 * math.pi / 60
    P = np.zeros(N.NP)
    P[N.I_M] = 0.20; P[N.I_R] = 0.033 / 2; P[N.I_W] = 0.085; P[N.I_L] = 0.13
    P[N.I_RM] = R; P[N.I_KE] = (V - I0 * R) / w0; P[N.I_KT] = Ts / (Is - I0); P[N.I_I0] = I0
    P[N.I_LIMV] = caso["limV"]
    return P


def main():
    filas = {}
    with open(DORADOS, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            filas.setdefault(r["caso"], []).append(r)
    peor_total = 0.0
    for nombre, caso in CASOS.items():
        P = vector(caso)
        prm = np.array(caso["prm"], float)
        ST = np.zeros(6); ST[5] = 1.0
        peor = 0.0
        for r in filas[nombre]:
            nL, nR = N.paso_sf(ST, float(r["e"]), float(r["dt"]), float(r["vbat"]), P, prm, 0.0, 0.0, 0.0)
            peor = max(peor, abs(nL - float(r["izq"])), abs(nR - float(r["der"])), abs(ST[4] - float(r["v_cmd"])))
        print(f"{nombre}: {len(filas[nombre])} pasos, diferencia máxima {peor:.2e}")
        peor_total = max(peor_total, peor)
    ok = peor_total < 1e-6
    print("C2 del simulador = C2 del firmware (referencia dorada)" if ok else "DIFERENCIA con la referencia")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
