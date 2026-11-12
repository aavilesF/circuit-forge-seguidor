"""Pruebas de regresión del cálculo de vuelta de la Fase 1 V2 (sim/v2/fase1_v2.py).

Origen: auditoría externa del commit cd3ff42. La versión anterior de tiempo_vuelta() sumaba (v_crucero − v)/a, negativo
cuando el robot salía de un arco más rápido que v_crucero, y daba tiempos imposibles. Ahora el perfil es factible:
pasada hacia atrás (frenado) + hacia adelante (aceleración). Estas pruebas fijan esas propiedades.
Uso: python3 -m pytest -q sim/v2/pruebas/"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
import pytest

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, ".."))
import fase1_v2 as F  # noqa: E402
import calculos_fisicos as P1  # noqa: E402  (pistas sintéticas; fase1_v2 agrega sim/fase1 a la ruta)

G = F.geo_estudio()
M, MU, L = 0.20, 0.8, 0.11
DS = 0.002


def _recta(largo):
    return P1.Pista("recta", (("S", largo),))


# ------------------------------------------------------------------------------------------------ perfil genérico
@pytest.mark.parametrize("horizonte", [None, 20])
def test_perfil_respeta_topes_y_aceleraciones(horizonte):
    rng = np.random.default_rng(7)
    cap = np.repeat(rng.uniform(0.4, 2.0, 40), 25)              # escalones de 5 cm
    a_acc, a_fr = 8.0, 12.0
    vel, dt, a_req = F.perfil_vuelta(cap, a_acc, a_fr, DS, horizonte=horizonte)
    assert np.all(vel >= 0) and np.all(dt > 0)
    assert np.all(vel[1:] <= cap + 1e-9), "excede el tope"
    acc = (vel[1:] ** 2 - vel[:-1] ** 2) / (2 * DS)
    assert acc.max() <= a_acc + 1e-6, "acelera más de lo posible"
    if horizonte is None:
        assert -acc.min() <= a_fr + 1e-6 and a_req <= a_fr + 1e-6, "frena más de lo posible"


def test_recta_coincide_con_la_solucion_analitica():
    """Desde parado, aceleración a hasta v y después crucero: t = v/a + (Ls - v²/2a)/v."""
    v, a, Ls = 1.5, 10.0, 1.0
    t = F.perfil_vuelta(np.full(int(Ls / DS), v), a, 15.0, DS)[1].sum()
    t_exacto = v / a + (Ls - v * v / (2 * a)) / v
    assert abs(t - t_exacto) < 2e-3


def test_recta_corta_sin_llegar_a_crucero():
    v, a, Ls = 3.0, 10.0, 0.2                                   # v²/2a = 0.45 m > 0.2 m
    t = F.perfil_vuelta(np.full(int(Ls / DS), v), a, 15.0, DS)[1].sum()
    assert abs(t - math.sqrt(2 * Ls / a)) < 2e-3


# ------------------------------------------------------------------------------------------------ caso del error auditado
def test_salida_de_arco_mas_rapida_que_el_crucero():
    """Arco amplio (v_curva > v_crucero) seguido de recta: con el error, el término de la recta era negativo."""
    pista = P1.Pista("arco amplio", (("S", 0.5), ("A", 1.0, 90), ("S", 0.5)))
    vc, Rc = F.v_curva(1.0, L, M, 3.0, MU, G)
    v_cr = 1.0
    assert vc > v_cr, "la prueba necesita un arco más rápido que el crucero"
    d = F.tiempo_vuelta(pista, M, 3.0, MU, G, L, v_cr, 10.0, detalle=True)
    assert np.all(d["dt"] > 0) and d["t"] > 0
    assert d["vel"].max() <= v_cr + 1e-9, "el robot reactivo no supera su crucero"
    largo = 0.5 + 1.0 * math.pi / 2 + 0.5
    assert d["t"] >= largo / v_cr - 1e-9, "más rápido que ir siempre a v_crucero: imposible"


@pytest.mark.parametrize("Fs", [0.0, 1.0, 3.0])
def test_pistas_sinteticas_tiempos_validos(Fs):
    traj = F.trayectoria(L, 0.15, G.x_cg)
    v0 = F.v0_max_reactiva(traj, M, Fs, MU, G, 0.002, 0.010, 0.15)
    for p in P1.pistas():
        dr = F.tiempo_vuelta(p, M, Fs, MU, G, L, min(v0, 2.0), 10.0, detalle=True)
        dm = F.tiempo_vuelta_mapa(p, M, Fs, MU, G, L, 2.0, 10.0, detalle=True)
        assert np.all(dr["dt"] > 0) and np.all(dm["dt"] > 0)
        assert dr["factible"], f"{p.nombre}: el crucero reactivo de la Fase 1 debe poder frenar dentro del horizonte L"
        assert dm["factible"]
        assert dm["t"] <= dr["t"] + 1e-9, "con mapa nunca se tarda más que reactivo"
        assert dr["t"] >= P1.largo_linea(p) / min(v0, 2.0) - 1e-9


def test_mas_crucero_no_aumenta_el_tiempo():
    p = P1.pistas()[0]
    ts = [F.tiempo_vuelta(p, M, 3.0, MU, G, L, v, 10.0) for v in (0.8, 1.0, 1.2, 1.4, 1.6)]
    assert all(b <= a + 1e-9 for a, b in zip(ts, ts[1:]))


def test_mas_succion_no_aumenta_el_tiempo_con_mapa():
    p = P1.pistas()[3]
    ts = [F.tiempo_vuelta_mapa(p, M, Fs, MU, G, L, 2.0, 10.0) for Fs in (0.0, 1.0, 2.0, 4.0)]
    assert all(b <= a + 1e-9 for a, b in zip(ts, ts[1:]))


def test_tablas_regeneradas_sin_tiempos_imposibles():
    import csv
    raiz = os.path.abspath(os.path.join(AQUI, "..", "..", "resultados", "v2_fase1"))
    for nombre in ("T8_energia.csv", "T8b_reactivo_vs_mapa.csv"):
        for fila in csv.DictReader(open(os.path.join(raiz, nombre), encoding="utf-8")):
            for k, val in fila.items():
                if k.startswith("t_"):
                    assert float(val) > 0, f"{nombre}: {k} = {val}"
            assert fila["perfil_factible"] == "True", f"{nombre}: perfil no factible"
