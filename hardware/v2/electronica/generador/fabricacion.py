#!/usr/bin/env python3
"""V2 · Archivos para el fabricante a partir del diseño y de las posiciones que exporta KiCad:
  BOM.csv (agrupada, con fabricante y número de parte), CPL_JLCPCB.csv (Designator, Mid X, Mid Y, Layer, Rotation) y
  LEEME.md con las opciones de pedido. Uso: python3 fabricacion.py barra_sensores"""
from __future__ import annotations

import csv
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun as K  # noqa: E402


def cpl(fab):
    filas = []
    for lado, nombre in (("Top", "posiciones_superior.csv"), ("Bottom", "posiciones_inferior.csv")):
        ruta = os.path.join(fab, nombre)
        if not os.path.exists(ruta):
            continue
        for r in csv.DictReader(open(ruta, encoding="utf-8")):
            filas.append([r["Ref"], f"{float(r['PosX']):.4f}mm", f"{float(r['PosY']):.4f}mm", lado, f"{float(r['Rot']):.2f}"])
    with open(os.path.join(fab, "CPL_JLCPCB.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        w.writerows(sorted(filas))
    return len(filas)


def main(proy):
    D = importlib.import_module(proy).D
    fab = os.path.join(K.V2E, "fabricacion", proy)
    os.makedirs(fab, exist_ok=True)
    K.bom(D, os.path.join(fab, "BOM.csv"))
    n = cpl(fab)
    print(f"  BOM y CPL ({n} posiciones) -> {os.path.relpath(fab, K.RAIZ)}")


if __name__ == "__main__":
    main(sys.argv[1])
