#!/usr/bin/env python3
"""V2 · Datos para las pruebas del firmware en la PC (se generan en cada corrida, no se guardan en el repositorio):
  pistas_<P>.csv   las pistas sintéticas P1-P4 del simulador (sim/pistas.py): x, y, rumbo, curvatura, hueco cada 1 mm
  oro_perfil.json/.txt  vectores dorados: perfil_vuelta() de sim/v2/fase1_v2.py sobre los topes por curvatura de cada pista,
                   para comprobar que v2::perfil_factible() del firmware da lo mismo.
Uso: python3 generar_datos.py <carpeta de salida>"""
import json
import math
import os
import sys

import numpy as np

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "sim"))
sys.path.insert(0, os.path.join(RAIZ, "sim", "v2"))
import pistas as PI                      # noqa: E402
from fase1_v2 import perfil_vuelta       # noqa: E402

salida = sys.argv[1]
os.makedirs(salida, exist_ok=True)
oro = []
for clave in PI.ORDEN:
    p = PI.construir(clave)
    np.savetxt(os.path.join(salida, f"pistas_{clave}.csv"),
               np.column_stack([p.x, p.y, p.rumbo, p.kappa, p.hueco.astype(float)]), fmt="%.6f", delimiter=",")
    ds = 0.01
    k = p.kappa[::10]
    for a_lat, a_acc, a_fr, vmax, v_ini in ((7.06, 8.0, 6.0, 2.0, 0.0), (12.0, 10.5, 9.0, 2.5, 0.3)):
        cap = np.array([min(vmax, math.sqrt(a_lat / abs(x))) if abs(x) > 1e-6 else vmax for x in k])
        vel, dt, a_req = perfil_vuelta(cap, a_acc, a_fr, ds, horizonte=None, v_ini=v_ini)
        oro.append(dict(pista=clave, ds=ds, a_acc=a_acc, a_fr=a_fr, v_ini=v_ini, cap=cap.tolist(), vel=vel.tolist(),
                        t=float(np.sum(dt)), a_req=float(a_req)))
json.dump(oro, open(os.path.join(salida, "oro_perfil.json"), "w"))
with open(os.path.join(salida, "oro_perfil.txt"), "w") as f:     # el mismo contenido en texto simple para C++
    for o in oro:
        f.write(f"{o['pista']} {o['ds']} {o['a_acc']} {o['a_fr']} {o['v_ini']} {len(o['cap'])} {o['t']:.9f} {o['a_req']:.9f}\n")
        f.write(" ".join(f"{v:.9f}" for v in o["cap"]) + "\n")
        f.write(" ".join(f"{v:.9f}" for v in o["vel"]) + "\n")
print("datos de prueba ->", salida, "|", len(oro), "perfiles dorados")
