#!/usr/bin/env python3
"""Suma docs/BOM_FINAL.csv y comprueba el presupuesto de config/robot_maestro.yaml (presupuesto.maximo).
Columnas usadas: cantidad, precio_objetivo_u, precio_estimado_u, precio_maximo_u, incluido (sí/no), verificar.
Uso: python3 herramientas/presupuesto.py   (código 1 si el estimado o el máximo superan el límite)"""
from __future__ import annotations

import csv
import os
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(RAIZ, "sim"))
import config as CF  # noqa: E402


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def main():
    cfg = CF.cargar()
    lim = cfg["presupuesto"]["maximo_mxn"]
    reserva = cfg["presupuesto"]["reserva_mxn"]
    filas = list(csv.DictReader(open(os.path.join(RAIZ, "docs", "BOM_FINAL.csv"), encoding="utf-8")))
    tot = {"objetivo": 0.0, "estimado": 0.0, "maximo": 0.0}
    por_verificar = 0.0
    for f in filas:
        if f.get("incluido", "sí").strip().lower() not in ("sí", "si"):
            continue
        q = num(f["cantidad"])
        for k in tot:
            tot[k] += q * num(f[f"precio_{k}_u"])
        if f.get("verificar", "").strip().lower() in ("sí", "si"):
            por_verificar += q * num(f["precio_estimado_u"])
    print(f"Componentes (sin reserva): objetivo ${tot['objetivo']:.0f}, estimado ${tot['estimado']:.0f}, "
          f"máximo ${tot['maximo']:.0f} MXN")
    print(f"Reserva para imprevistos: ${reserva:.0f} MXN")
    print(f"Total estimado + reserva: ${tot['estimado'] + reserva:.0f} de ${lim:.0f} MXN")
    print(f"Total con el máximo permitido por partida + reserva: ${tot['maximo'] + reserva:.0f} MXN")
    print(f"Partidas con precio por verificar antes de comprar: ${por_verificar:.0f} MXN del estimado")
    fallas = []
    if tot["estimado"] + reserva > lim:
        fallas.append("el estimado con reserva supera el presupuesto")
    if tot["maximo"] + reserva > lim:
        fallas.append("el escenario de precios máximos con reserva supera el presupuesto")
    print("PRESUPUESTO OK" if not fallas else "PRESUPUESTO EXCEDIDO: " + "; ".join(fallas))
    sys.exit(1 if fallas else 0)


if __name__ == "__main__":
    main()
