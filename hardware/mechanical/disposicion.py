#!/usr/bin/env python3
"""Disposición en planta del robot a partir de config/robot_maestro.yaml (posiciones, masas y medidas de cada
componente). NO es el CAD definitivo: sirve para comprobar, antes de medir las piezas, que
 1. todo cabe en la caja del reglamento (20 × 10 cm, con la holgura de diseño),
 2. no hay choques entre piezas del mismo nivel (z),
 3. el CG calculado está entre el eje y el apoyo (estabilidad de cabeceo).
Escribe hardware/mechanical/disposicion_planta.png y .svg. Código 1 si algo falla.
Uso: python3 hardware/mechanical/disposicion.py"""
from __future__ import annotations

import os
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "sim"))
import config as CF  # noqa: E402

FALLAS = []


def ok(cond, texto):
    print(f"[{'OK ' if cond else 'MAL'}] {texto}")
    if not cond:
        FALLAS.append(texto)


def piezas(cfg, c):
    """Rectángulos (nombre, x_centro, y_centro, largo_x, ancho_y, nivel). Llantas y motores en pares."""
    out = []
    comp = cfg["componentes"]
    W = c.W
    D = 2 * c.r
    anch_ll = cfg["geometria"]["ancho_llanta"]
    for s in (1, -1):
        out.append((f"llanta {'izq' if s > 0 else 'der'}", 0.0, s * W / 2, D, anch_ll, "ruedas"))
    for nombre, d in comp.items():
        if "dim" not in d or nombre in ("llantas",):
            continue
        lx, ly = d["dim"]
        if nombre == "motores":
            for s in (1, -1):
                y = s * (W / 2 - anch_ll / 2 - 1.5e-3 - ly / 2)
                out.append((f"motor {'izq' if s > 0 else 'der'}", d["x"], y, lx, ly, d.get("nivel", "base")))
            continue
        if nombre == "barra_sensores":
            sy = c.sy
            out.append(("barra de sensores", float(c.sx.mean()), 0.0, lx, float(sy.max() - sy.min()) + 0.008, "base"))
            continue
        out.append((nombre, d["x"], d.get("y", 0.0), lx, ly, d.get("nivel", "base")))
    return out


def main():
    cfg = CF.cargar()
    c = CF.construir(cfg)
    reg, dis = cfg["reglamento"], cfg["diseno"]
    P = piezas(cfg, c)
    xs = [p[1] - p[3] / 2 for p in P] + [p[1] + p[3] / 2 for p in P]
    ys = [p[2] - p[4] / 2 for p in P] + [p[2] + p[4] / 2 for p in P]
    largo, ancho = max(xs) - min(xs), max(ys) - min(ys)
    ok(largo <= reg["largo_max"] - 2 * dis["margen_caja"], f"largo total {largo*1000:.1f} mm ≤ "
       f"{(reg['largo_max'] - 2 * dis['margen_caja'])*1000:.0f} mm")
    ok(ancho <= reg["ancho_max"] - 2 * dis["margen_caja"], f"ancho total {ancho*1000:.1f} mm ≤ "
       f"{(reg['ancho_max'] - 2 * dis['margen_caja'])*1000:.0f} mm")
    # choques en el mismo nivel
    for i in range(len(P)):
        for j in range(i + 1, len(P)):
            a, b = P[i], P[j]
            if a[5] != b[5]:
                continue
            sx = abs(a[1] - b[1]) < (a[3] + b[3]) / 2 - 1e-4
            sy = abs(a[2] - b[2]) < (a[4] + b[4]) / 2 - 1e-4
            ok(not (sx and sy), f"sin choque: {a[0]} / {b[0]} (nivel {a[5]})")
    ok(0 < c.x_cg < c.x_apoyo, f"CG en x = {c.x_cg*1000:.1f} mm, entre el eje (0) y el apoyo ({c.x_apoyo*1000:.0f} mm)")
    ok(c.masa <= dis["masa_limite_diseno"], f"masa {c.masa*1000:.1f} g ≤ {dis['masa_limite_diseno']*1000:.0f} g de diseño")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.patches as mp
    import matplotlib.pyplot as plt
    colores = {"ruedas": "#2a78d6", "base": "#c3c2b7", "alto": "#eb6834"}
    fig, ax = plt.subplots(figsize=(9, 5.2))
    caja = mp.Rectangle((min(xs) - 0.0, -reg["ancho_max"] / 2), reg["largo_max"], reg["ancho_max"], fill=False,
                        ls="--", ec="#52514e", lw=1)
    ax.add_patch(caja)
    for nombre, x, y, lx, ly, nivel in P:
        ax.add_patch(mp.Rectangle((x - lx / 2, y - ly / 2), lx, ly, fc=colores.get(nivel, "#c3c2b7"),
                                  ec="#0b0b0b", lw=0.6, alpha=0.55 if nivel == "alto" else 0.85))
        ax.text(x, y, nombre, ha="center", va="center", fontsize=6.5)
    ax.plot(c.sx, c.sy, "o", ms=2.5, color="#0b0b0b")
    ax.plot([c.x_cg], [0], "x", color="#d03b3b", ms=9, mew=2)
    ax.text(c.x_cg, -0.006, "CG", color="#d03b3b", ha="center", va="top", fontsize=8)
    ax.plot([c.x_apoyo], [0], "s", color="#1baf7a", ms=6)
    ax.text(c.x_apoyo, 0.006, "apoyo", color="#1baf7a", ha="center", fontsize=7)
    ax.set_aspect("equal")
    ax.set_xlim(min(xs) - 0.01, min(xs) + reg["largo_max"] + 0.01)
    ax.set_ylim(-0.06, 0.06)
    ax.set_xlabel("x (m) desde el eje, hacia adelante"); ax.set_ylabel("y (m), izquierda +")
    ax.set_title(f"Disposición en planta (no es CAD definitivo): {largo*1000:.0f} × {ancho*1000:.0f} mm, "
                 f"{c.masa*1000:.0f} g. Caja del reglamento punteada; naranja = segundo nivel", loc="left", fontsize=9)
    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(os.path.join(os.path.dirname(__file__), f"disposicion_planta.{ext}"), dpi=150)
    print(f"\n{len(FALLAS)} fallas")
    sys.exit(1 if FALLAS else 0)


if __name__ == "__main__":
    main()
