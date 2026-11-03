#!/usr/bin/env python3
"""V2 · Fase 1 — medidas de los modelos 3D entregados del ventilador y su montaje (hardware/v2/referencia_succion/).

Carga cada malla OBJ (mm), une vértices, y la corta con planos horizontales (eje y del archivo = vertical) para obtener
contornos, agujeros y volumen. Para el rotor mide además radio interior y exterior y número de álabes.
Uso: python3 sim/v2/analisis_obj.py   (requiere trimesh y shapely)"""
from __future__ import annotations

import glob
import os

import numpy as np
import trimesh
from shapely.geometry import Polygon

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DIR = os.path.join(RAIZ, "hardware", "v2", "referencia_succion")


def cargar(ruta):
    m = trimesh.load(ruta, force="mesh", process=False)
    m.merge_vertices(merge_tex=True, merge_norm=True)
    m.process()
    return m


def lazos(m, y):
    s = m.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    if s is None:
        return []
    out = []
    for d in s.discrete:
        if len(d) >= 4:
            p = Polygon(d[:, [0, 2]])
            if p.is_valid and p.area > 1e-3:
                out.append(p)
    return out


def regiones(ls):
    """Agrupa lazos en regiones con huecos (paridad de anidamiento)."""
    ls = sorted(ls, key=lambda p: -p.area)
    nivel = [sum(1 for q in ls[:i] if q.contains(p.representative_point())) for i, p in enumerate(ls)]
    ext = [(p, []) for p, n in zip(ls, nivel) if n % 2 == 0]
    for p, n in zip(ls, nivel):
        if n % 2 == 1:
            for e, hs in ext:
                if e.contains(p.representative_point()):
                    hs.append(p)
                    break
    return ext


def main():
    for ruta in sorted(glob.glob(os.path.join(DIR, "*.obj"))):
        m = cargar(ruta)
        b = m.bounds
        print(f"== {os.path.basename(ruta)}: {np.round(b[1] - b[0], 2)} mm (x, y vertical, z); estanco {m.is_watertight}; "
              f"volumen {m.volume:.1f} mm³")
        for y in np.linspace(b[0][1] + 0.05, b[1][1] - 0.05, 6):
            rs = regiones(lazos(m, y))
            solido = sum(e.area - sum(h.area for h in hs) for e, hs in rs)
            desc = []
            for e, hs in rs[:3]:
                bx = e.bounds
                hd = ", ".join(f"Ø{2 * np.sqrt(h.area / np.pi):.2f}@({h.centroid.x:.1f},{h.centroid.y:.1f})"
                               for h in sorted(hs, key=lambda h: -h.area)[:9])
                desc.append(f"[{bx[2] - bx[0]:.1f}×{bx[3] - bx[1]:.1f} huecos {len(hs)}: {hd}]")
            print(f"   y = {y:6.2f}: {len(rs):2d} regiones, área sólida {solido:7.1f} mm²  {' '.join(desc)}")
        if "Ventilador" in ruta:
            radios = []
            for p in lazos(m, (b[0][1] + b[1][1]) / 2):
                c = np.array(p.exterior.coords)
                r = np.hypot(c[:, 0], c[:, 1])
                radios.append((r.min(), r.max()))
            print(f"   álabes: {len(radios)}, r interior {min(r[0] for r in radios):.2f} mm, r exterior {max(r[1] for r in radios):.2f} mm; "
                  f"niveles de las caras horizontales: {np.unique(np.round(m.vertices[:, 1], 3))}")


if __name__ == "__main__":
    main()
