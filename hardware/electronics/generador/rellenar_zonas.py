#!/usr/bin/env python3
"""Rellena las zonas de cobre de la PCB guardada (pcbnew de KiCad 9). Se ejecuta en un proceso aparte después de
pcb_kicad.py final: cargar la placa desde el archivo le da proyecto y ajustes al rellenador.
Uso: python3 rellenar_zonas.py   (con el Python que trae pcbnew de KiCad 9)"""
import os
import sys

import pcbnew as K

AQUI = os.path.dirname(os.path.abspath(__file__))
RUTA = os.path.join(AQUI, "..", "kicad", "speed_follower.kicad_pcb")


def main():
    b = K.LoadBoard(RUTA)
    zonas = [z for z in b.Zones() if not z.GetIsRuleArea()]
    K.ZONE_FILLER(b).Fill(b.Zones())
    llenas = sum(1 for z in zonas if z.IsFilled())
    K.SaveBoard(RUTA, b)
    print(f"zonas rellenas: {llenas}/{len(zonas)}")
    return 0 if llenas == len(zonas) else 1


if __name__ == "__main__":
    sys.exit(main())
