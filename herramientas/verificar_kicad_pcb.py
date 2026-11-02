#!/usr/bin/env python3
"""Verifica la PCB generada: reglas de diseno (DRC) y que sus redes coincidan con las del esquema cableado.

DRC: pcbnew.WriteDRCReport (KiCad 7 no trae `kicad-cli pcb drc`).  Redes: se exporta la lista de conexiones
del esquema con `kicad-cli sch export netlist` y se compara, por (referencia, numero de pad), con las redes de la PCB.
Uso: python3 herramientas/verificar_kicad_pcb.py
"""
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generar_kicad as base  # noqa: E402

CARPETA = base.RAIZ / "docs" / "diagramas" / "kicad_cableado"
NOMBRE = "seguidor_cableado"


def drc(pcb):
    placa = pcbnew.LoadBoard(str(pcb))
    with tempfile.TemporaryDirectory() as t:
        inf = Path(t) / "drc.txt"
        pcbnew.WriteDRCReport(placa, str(inf), pcbnew.EDA_UNITS_MILLIMETRES, True)
        txt = inf.read_text()
    bloques = []
    tipo = None
    for linea in txt.splitlines():
        m = re.match(r"\[(\w+)\]:", linea)
        if m:
            tipo = m.group(1)
        m = re.search(r"Severity: (\w+)", linea)
        if m and tipo:
            bloques.append((tipo, "", m.group(1)))
            tipo = None
    return Counter((t, sev) for t, _, sev in bloques)


def redes_pcb(pcb):
    placa = pcbnew.LoadBoard(str(pcb))
    redes = {}
    for f in placa.GetFootprints():
        for p in f.Pads():
            if p.GetNetname():
                redes.setdefault(p.GetNetname(), set()).add((f.GetReference(), p.GetNumber()))
    return {frozenset(v) for v in redes.values() if len(v) >= 2}


def redes_esquema(sch):
    with tempfile.TemporaryDirectory() as t:
        net = Path(t) / "x.net"
        subprocess.run(["kicad-cli", "sch", "export", "netlist", "-o", str(net), str(sch)], check=True, capture_output=True)
        arbol = base.leer_sexp(net.read_text(encoding="utf-8"))
    out = set()
    for n in base.hijos(base.hijo(arbol, "nets"), "net"):
        nodos = frozenset((base.hijo(x, "ref")[1], base.hijo(x, "pin")[1]) for x in base.hijos(n, "node"))
        if len(nodos) >= 2:
            out.add(nodos)
    return out


def main():
    pcb = CARPETA / f"{NOMBRE}.kicad_pcb"
    cuentas = drc(pcb)
    errores = {k: v for k, v in cuentas.items() if k[1] == "error"}
    print("DRC:", dict(cuentas) or "sin avisos")
    esquema, placa = redes_esquema(CARPETA / f"{NOMBRE}.kicad_sch"), redes_pcb(pcb)
    # en la PCB un pad repetido (p. ej. GND del ESP32) cuenta una sola vez por (ref, numero)
    igual = esquema == placa
    print(f"redes: esquema {len(esquema)} | PCB {len(placa)} | iguales: {igual}")
    if not igual:
        print(" solo en esquema:", [sorted(x) for x in esquema - placa][:3])
        print(" solo en PCB:", [sorted(x) for x in placa - esquema][:3])
    sys.exit(0 if igual and not errores else 1)


if __name__ == "__main__":
    main()
