#!/usr/bin/env python3
"""Verificación del esquemático SIN el ERC oficial de KiCad.

Motivo: el kicad-cli de KiCad 7 no trae `sch erc`. Este script hace dos cosas:
  1. Exporta la netlist con kicad-cli (esto comprueba que KiCad SÍ lee el archivo) y la compara,
     pin por pin, contra la lista esperada que escribió el generador (esperado.json).
  2. Aplica un ERC propio, más corto que el de KiCad: pines sin conexión no marcados, redes de un solo pin,
     dos salidas en la misma red, pines de alimentación sin fuente, referencias repetidas y huellas vacías.

NO sustituye al ERC oficial: abrir el proyecto en KiCad y correr Inspeccionar > ERC antes de fabricar.
Uso: verificar_esquematico.py <carpeta con el .kicad_sch>
"""
import json
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


def norm(n):
    return n.lstrip("/")


def main(carpeta):
    carpeta = Path(carpeta)
    sch = next(carpeta.glob("*.kicad_sch"))
    esperado = json.loads((carpeta / "esperado.json").read_text())
    xml = Path(tempfile.mkdtemp()) / "net.xml"
    r = subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "-o", str(xml), str(sch)],
                       capture_output=True, text=True)
    if r.returncode != 0 or not xml.exists():
        print("ERROR: kicad-cli no pudo exportar la netlist:", r.stderr or r.stdout)
        return 1
    raiz = ET.parse(xml).getroot()

    errores, avisos = [], []
    pin_red, redes = {}, defaultdict(list)
    for net in raiz.find("nets"):
        nombre = norm(net.get("name"))
        for nodo in net:
            ref, pin, tipo = nodo.get("ref"), nodo.get("pin"), nodo.get("pintype")
            pin_red[(ref, pin)] = nombre
            redes[nombre].append((ref, pin, nodo.get("pinfunction"), tipo))

    # KiCad no incluye en la netlist los símbolos de alimentación (#PWR, #FLG): los PWR_FLAG se toman del generador
    redes_con_flag = {c[4] for c in esperado["conexiones"] if c[0].startswith("#FLG")}

    # --- 1. Comparación contra lo esperado
    for ref, pin, nom, tipo, red in esperado["conexiones"]:
        if ref.startswith("#"):
            continue
        real = pin_red.get((ref, pin))
        if real is None:
            errores.append(f"{ref}.{pin} ({nom}): esperado en '{red}', pero no aparece en ninguna red")
        elif real != red:
            errores.append(f"{ref}.{pin} ({nom}): esperado '{red}', KiCad lo puso en '{real}'")
    esperadas = {(c[0], c[1]) for c in esperado["conexiones"]}
    nc_esp = {(n[0], n[1]) for n in esperado["nc"]}
    for (ref, pin), red in pin_red.items():
        if (ref, pin) in esperadas:
            continue
        if (ref, pin) in nc_esp:
            continue
        errores.append(f"{ref}.{pin}: aparece en la red '{red}' pero el generador no lo declaró")
    for ref, pin in nc_esp:
        red = pin_red.get((ref, pin), "")
        if red and not red.startswith("unconnected"):
            errores.append(f"{ref}.{pin}: marcado NC pero KiCad lo conectó a '{red}'")

    # --- 2. ERC propio
    for nombre, nodos in redes.items():
        reales = [n for n in nodos if not n[0].startswith("#FLG")]
        if nombre.startswith("unconnected"):
            ref, pin = reales[0][0], reales[0][1]
            if (ref, pin) not in nc_esp:
                errores.append(f"pin sin conexión y sin marca NC: {ref}.{pin}")
            continue
        if len(reales) < 2:
            avisos.append(f"red de un solo pin: '{nombre}' ({reales[0][0]}.{reales[0][1]})" if reales else
                          f"red sin pines: '{nombre}'")
        salidas = [n for n in nodos if n[3] in ("output", "power_out") and not n[0].startswith("#")]
        if len(salidas) > 1:
            errores.append(f"varias salidas en la red '{nombre}': {[(n[0], n[1]) for n in salidas]}")
        pwr_in = [n for n in nodos if n[3] == "power_in" and not n[0].startswith("#")]
        fuentes = [n for n in nodos if n[3] in ("power_out",)]
        if pwr_in and not fuentes and nombre not in redes_con_flag:
            errores.append(f"pines de alimentación sin fuente ni PWR_FLAG en '{nombre}'")

    refs = defaultdict(int)
    for comp in raiz.find("components"):
        refs[comp.get("ref")] += 1
        fp = comp.findtext("footprint") or ""
        if not comp.get("ref").startswith("#") and not fp:
            errores.append(f"{comp.get('ref')}: sin huella (footprint)")
    for ref, n in refs.items():
        if n > 1:
            errores.append(f"referencia repetida: {ref}")

    n_comp = sum(1 for c in raiz.find("components") if not c.get("ref").startswith("#"))
    print(f"Netlist leída por KiCad {raiz.find('design').findtext('tool')}: {n_comp} componentes, {len(redes)} redes")
    for a in avisos:
        print("AVISO :", a)
    for e in errores:
        print("ERROR :", e)
    print(f"Resultado: {len(errores)} errores, {len(avisos)} avisos (ERC propio; el ERC oficial de KiCad NO se corrió)")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
