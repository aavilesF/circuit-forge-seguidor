#!/usr/bin/env python3
"""V2 · Verificación de un proyecto KiCad generado: conectividad diseño = esquemático (= PCB), ERC y DRC.
Escribe verificacion/<proy>/resumen.json y termina con código 1 si hay errores.
Uso: python3 hardware/v2/electronica/generador/verificar.py barra_sensores|principal"""
from __future__ import annotations

import importlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun as K  # noqa: E402


def leer_rpt(ruta):
    if not os.path.exists(ruta):
        return None
    t = open(ruta, encoding="utf-8").read()
    tipos = {}
    for m in re.finditer(r"^\[(\w+)\]:.*\n\s+(?:[^;\n]*; )?(\w+)", t, re.M):
        tipos.setdefault((m.group(1), m.group(2)), 0)
        tipos[(m.group(1), m.group(2))] += 1
    return tipos


def main(proy):
    mod = importlib.import_module(proy)
    D = mod.D
    vdir = os.path.join(K.V2E, "verificacion", proy)
    pads = None
    ruta_pads = os.path.join(vdir, "pads_pcb.json")
    if os.path.exists(os.path.join(D.dir, proy + ".kicad_pcb")) and os.path.exists(ruta_pads):
        nr = mod.nombres_red() if hasattr(mod, "nombres_red") else {}
        inv = {vv: kk for kk, vv in nr.items()}
        pads = [dict(p, red=inv.get(p["red"], p["red"].split("/")[-1])) for p in json.load(open(ruta_pads))]
    err = K.verificar_conectividad(D, vdir, pads)
    erc = leer_rpt(os.path.join(vdir, "erc.rpt")) or {}
    drc = leer_rpt(os.path.join(vdir, "drc.rpt"))
    res = {"conectividad_errores": err,
           "erc": {f"{a} ({b})": n for (a, b), n in erc.items()},
           "drc": None if drc is None else {f"{a} ({b})": n for (a, b), n in drc.items()}}
    if drc is not None:
        t = open(os.path.join(vdir, "drc.rpt"), encoding="utf-8").read()
        res["drc_conteos"] = {k: int(n) for n, k in re.findall(r"\*\* Found (\d+) ([\w ]+?) \*\*", t)}
    json.dump(res, open(os.path.join(vdir, "resumen.json"), "w"), indent=1, ensure_ascii=False)
    errores_erc = sum(n for (a, b), n in erc.items() if b == "error")
    errores_drc = 0 if drc is None else sum(n for (a, b), n in drc.items() if b == "error")
    print(f"  ERC: {sum(erc.values())} mensajes ({errores_erc} errores)" +
          ("" if drc is None else f" | DRC: {res['drc_conteos']} -> {errores_drc} errores; detalle {dict(res['drc'])}"))
    malo = bool(err) or errores_erc or errores_drc
    print("  VERIFICACIÓN", "CON ERRORES" if malo else "OK")
    return 1 if malo else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
