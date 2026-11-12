#!/usr/bin/env python3
"""Gráficas de la Fase 3 a partir de sim/resultados/fase3/*.csv. Uso: python3 sim/graficas_fase3.py"""
import csv
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import config as CF  # noqa: E402
import validacion_final as V  # noqa: E402

SAL = os.path.join(CF.RAIZ, "sim", "resultados", "fase3")
AZUL, NARANJA, GRIS = "#2a78d6", "#eb6834", "#c3c2b7"


def leer(n):
    return list(csv.DictReader(open(os.path.join(SAL, n), encoding="utf-8")))


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                         "grid.color": "#e6e5e1", "grid.linewidth": 0.6, "figure.facecolor": "#fcfcfb",
                         "axes.facecolor": "#fcfcfb"})
    # F1: candidatos de la etapa T
    f = leer("T_candidatos.csv")
    fig, ax = plt.subplots(figsize=(8, 3.6))
    y = np.arange(len(f))
    t = [float(r["t_medio_s"]) for r in f]
    col = [AZUL if float(r["exito"]) >= 0.995 else NARANJA for r in f]
    ax.barh(y, t, color=col, height=0.6)
    for i, r in enumerate(f):
        ax.text(t[i] + 0.04, i, f"{t[i]:.2f} s · {100*float(r['exito']):.1f} % · I {float(r['I_max_A']):.2f} A", va="center", fontsize=8)
    ax.set_yticks(y, [r["configuracion"] for r in f])
    ax.invert_yaxis(); ax.set_xlim(0, 8.5)
    ax.set_xlabel("tiempo medio de vuelta en las 4 pistas (s), 200 salidas")
    ax.set_title("Etapa T: motor × barra (C3m, ESP32, L 110 mm). Naranja = éxito < 99.5 %", loc="left")
    fig.tight_layout(); fig.savefig(os.path.join(SAL, "F1_candidatos.png"), dpi=130); plt.close(fig)

    # F2: robustez (éxito por escenario)
    filas = [(r["configuracion"], float(r["exito"]), "motor") for r in leer("S_sensibilidad_motor.csv")]
    filas += [(r["configuracion"], float(r["exito"]), "montaje") for r in leer("M_fabricacion.csv") if r["configuracion"] != "nominal"]
    filas += [(r["configuracion"], float(r["exito"]), "operación") for r in leer("P_escenarios.csv")]
    fig, ax = plt.subplots(figsize=(8, 9))
    y = np.arange(len(filas))
    ax.barh(y, [100 * e for _, e, _ in filas], color=[AZUL if e >= 0.99 else NARANJA for _, e, _ in filas], height=0.65)
    ax.axvline(99, color="#52514e", ls="--", lw=1)
    ax.set_yticks(y, [f"[{g}] {n}" for n, _, g in filas], fontsize=7.5)
    ax.invert_yaxis(); ax.set_xlim(0, 105)
    ax.set_xlabel("vueltas completas (%), 120 salidas por escenario; línea = criterio 99 %")
    ax.set_title("Auditoría de robustez de la arquitectura de $2,000 (simulada)", loc="left")
    fig.tight_layout(); fig.savefig(os.path.join(SAL, "F2_robustez.png"), dpi=130); plt.close(fig)

    # F3/F4: trayectorias y señales de la arquitectura vigente (mismas funciones que la Fase 2)
    cfg = CF.cargar(); a = cfg["arquitectura"]
    kw = dict(motor=a["motor"], barra=a["barra"], mcu=a["mcu"], control=a["control"], succion=False)
    etq = f"{a['control']}, {a['barra']}, {a['mcu']}, {CF.motor(cfg, a['motor']).nombre}"
    V.SAL = SAL
    V.graficas(kw, etq)
    os.replace(os.path.join(SAL, "F5_trayectorias.png"), os.path.join(SAL, "F3_trayectorias.png"))
    os.replace(os.path.join(SAL, "F6_senales_P4.png"), os.path.join(SAL, "F4_senales_P4.png"))
    print("F1-F4 escritas en sim/resultados/fase3/")


if __name__ == "__main__":
    main()
