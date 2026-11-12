"""Pistas sintéticas que cumplen el reglamento (mismas P1-P4 de la Fase 1) más discontinuidades de 5 mm.
La pista real se conoce hasta el día del evento: estas son casos de prueba, no predicciones del circuito."""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

DS = 0.001  # m entre puntos de la línea


@dataclass(frozen=True)
class Pista:
    nombre: str
    x: np.ndarray
    y: np.ndarray
    rumbo: np.ndarray
    kappa: np.ndarray
    hueco: np.ndarray    # bool: tramo sin vinil
    largo: float


def _chicana(R, th, signo=-1):
    return (("A", R, signo * th), ("A", R, -2 * signo * th), ("A", R, signo * th))


DEFS = {
    "P1": dict(nombre="P1 óvalo R150", inicio=0.50, huecos=(1.10, 3.10),
               segs=(("S", 1.60), ("A", 0.15, 180), ("S", 1.60), ("A", 0.15, 180))),
    "P2": dict(nombre="P2 óvalo R400", inicio=0.50, huecos=(0.90, 1.80),
               segs=(("S", 1.20), ("A", 0.40, 180), ("S", 1.20), ("A", 0.40, 180))),
    "P4": dict(nombre="P4 exigente R150", inicio=0.30, huecos=(0.95, 1.55),
               segs=(("S", 0.40), *_chicana(0.15, 40), ("S", 0.50), ("A", 0.15, 180),
                     ("S", 0.40), *_chicana(0.15, 40), ("S", 0.50), ("A", 0.15, 180))),
}
_x20 = 4 * 0.20 * math.sin(math.radians(40))
DEFS["P3"] = dict(nombre="P3 S y cambios de radio", inicio=0.25, huecos=(0.45, 2.30),
                  segs=(("S", 0.30), *_chicana(0.20, 40), ("S", 0.30), ("A", 0.20, 90), ("S", 0.30),
                        ("A", 0.20, 90), ("S", 0.30 + _x20 + 0.30), ("A", 0.35, 180)))
ORDEN = ("P1", "P2", "P3", "P4")


def construir(clave: str, ancho_hueco: float = 0.005) -> Pista:
    d = DEFS[clave]
    xs, ys, hs, ks = [0.0], [0.0], [0.0], [0.0]
    x = y = h = 0.0
    for s in d["segs"]:
        if s[0] == "S":
            n = int(round(s[1] / DS))
            for _ in range(n):
                x += DS * math.cos(h)
                y += DS * math.sin(h)
                xs.append(x); ys.append(y); hs.append(h); ks.append(0.0)
        else:
            R, th = s[1], math.radians(s[2])
            n = int(round(abs(th) * R / DS))
            dh = th / n
            k = math.copysign(1 / R, th)
            for _ in range(n):
                cuerda = 2 * R * math.sin(abs(dh) / 2)
                x += cuerda * math.cos(h + dh / 2)
                y += cuerda * math.sin(h + dh / 2)
                h += dh
                xs.append(x); ys.append(y); hs.append(h); ks.append(k)
    X, Y, H, K = (np.array(v[:-1]) for v in (xs, ys, hs, ks))  # el último punto repite el primero
    n = len(X)
    s = np.arange(n) * DS
    hueco = np.zeros(n, bool)
    for h0 in d["huecos"]:
        hueco |= (s >= h0) & (s < h0 + ancho_hueco)
    # rotar para que el índice 0 sea la línea de salida
    i0 = int(round(d["inicio"] / DS))
    rot = lambda a: np.roll(a, -i0)
    return Pista(d["nombre"], rot(X), rot(Y), rot(H), rot(K), rot(hueco), n * DS)


def todas(ancho_hueco: float = 0.005):
    return [construir(k, ancho_hueco) for k in ORDEN]
