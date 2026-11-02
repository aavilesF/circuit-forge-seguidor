#!/usr/bin/env python3
"""Comprobación de conectividad: la netlist que KiCad extrae del esquemático debe ser IDÉNTICA a las conexiones de
diseno.py (mismas redes, mismos pines). Si se pasa --pcb, compara también la red de cada pad de la PCB.
Uso: python3 hardware/electronics/herramientas/verificar_conectividad.py [--pcb]"""
import os
import subprocess
import sys
import xml.etree.ElementTree as ET

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "generador"))
import diseno as D  # noqa: E402

KDIR = os.path.join(D.RAIZ, "hardware", "electronics", "kicad")
VDIR = os.path.join(D.RAIZ, "hardware", "electronics", "verificacion")
KCLI = os.path.join(AQUI, "kicad.sh")


def netlist_esquematico():
    os.makedirs(VDIR, exist_ok=True)
    salida = os.path.join(VDIR, "netlist_esquematico.xml")
    subprocess.run([KCLI, "sch", "export", "netlist", "--format", "kicadxml", "-o", salida, "speed_follower.kicad_sch"],
                   cwd=KDIR, check=True, capture_output=True)
    raiz = ET.parse(salida).getroot()
    redes = {}
    for n in raiz.iter("net"):
        nodos = {(x.get("ref"), x.get("pin")) for x in n.iter("node") if not x.get("ref").startswith("#")}
        if nodos:
            nombre = n.get("name").split("/")[-1]
            redes[nombre] = nodos
    return redes


def normalizar(redes):
    """Conjunto de conjuntos de nodos (independiente de los nombres de red que KiCad elija)."""
    return {frozenset(v) for v in redes.values() if len(v) > 1 or True}


def main():
    esperado = {r: set(v) for r, v in D.redes().items()}
    obtenido = netlist_esquematico()
    # redes de un solo nodo sin conexión (KiCad las nombra "unconnected-...") se ignoran si diseno las marca nc
    obt = {r: v for r, v in obtenido.items() if not r.startswith("unconnected-")}
    err = []
    for red, nodos in esperado.items():
        if red not in obt:
            err.append(f"falta la red {red} en el esquemático")
        elif obt[red] != nodos:
            err.append(f"red {red}: sobran {sorted(obt[red] - nodos)} faltan {sorted(nodos - obt[red])}")
    for red in obt:
        if red not in esperado:
            err.append(f"red inesperada {red}: {sorted(obt[red])}")
    n_nodos = sum(len(v) for v in esperado.values())
    print(f"Esquemático: {len(obt)} redes, {sum(len(v) for v in obt.values())} conexiones; diseño: {len(esperado)} redes, {n_nodos} conexiones")
    if "--pcb" in sys.argv:
        import json
        ruta = os.path.join(VDIR, "pads_pcb.json")
        if not os.path.exists(ruta):
            err.append("no existe verificacion/pads_pcb.json (se genera al construir la PCB)")
        else:
            pads = json.load(open(ruta))
            por_pin = {(r, p): red for red, nodos in esperado.items() for (r, p) in nodos}
            n = 0
            for item in pads:
                k = (item["ref"], item["pad"])
                if k in por_pin:
                    n += 1
                    if item["red"] != por_pin[k]:
                        err.append(f"PCB {k}: red {item['red']} en lugar de {por_pin[k]}")
                elif item["red"] not in ("", None):
                    err.append(f"PCB {k}: pad con red {item['red']} que el diseño no conecta")
            faltan = set(por_pin) - {(i["ref"], i["pad"]) for i in pads}
            for k in sorted(faltan):
                err.append(f"PCB: falta el pad {k}")
            print(f"PCB: {n} pads con red comprobados")
    for e in err:
        print("  ERROR:", e)
    print("CONECTIVIDAD OK" if not err else f"CONECTIVIDAD CON {len(err)} ERRORES")
    return 1 if err else 0


if __name__ == "__main__":
    sys.exit(main())
