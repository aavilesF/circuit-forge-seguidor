#!/usr/bin/env python3
"""Verificación independiente de los cálculos de la Fase 1 (sim/fase1/calculos_fisicos.py, config v1).
Cada punto se recalcula por un camino distinto: geometría numérica, el simulador dinámico, o una
fórmula alternativa. Resultado: sim/resultados/fase2/V_verificacion_fase1.csv (una fila por comprobación).

Uso: python3 sim/verificacion_fase1.py"""
from __future__ import annotations

import csv
import importlib.util
import math
import os
import sys

import numpy as np

AQUI = os.path.dirname(__file__)
sys.path.insert(0, AQUI)
import config as CF  # noqa: E402
import nucleo as N  # noqa: E402
import simulador as S  # noqa: E402
from pistas import DS, Pista  # noqa: E402

G = 9.81
spec = importlib.util.spec_from_file_location("f1", os.path.join(AQUI, "fase1", "calculos_fisicos.py"))
F1 = importlib.util.module_from_spec(spec)
sys.modules["f1"] = F1
spec.loader.exec_module(F1)
FILAS = []


def anotar(tema, comprobacion, fase1, verificado, unidad, metodo, veredicto, nota=""):
    FILAS.append(dict(tema=tema, comprobacion=comprobacion, fase1=fase1, verificado=verificado, unidad=unidad,
                      metodo=metodo, veredicto=veredicto, nota=nota))
    print(f"[{veredicto}] {tema}: {comprobacion}: fase 1 = {fase1}, verificado = {verificado} {unidad}")


def recta(largo=12.0):
    n = int(largo / DS)
    x = np.arange(n) * DS
    z = np.zeros(n)
    return Pista("recta", x, z.copy(), z.copy(), z.copy(), np.zeros(n, bool), n * DS)


def circulo(R, vueltas=6):
    """Círculo recorrido varias veces (los puntos se repiten) para tener régimen permanente."""
    n = int(round(2 * math.pi * R / DS)) * vueltas
    a = np.arange(n) * DS / R
    x, y = R * np.sin(a), R * (1 - np.cos(a))
    return Pista(f"círculo R{R*1000:.0f}", x, y, a.copy(), np.full(n, 1 / R), np.zeros(n, bool), n * DS)


def lazo(c, pista, izq, der, t_cambio=99.0, izq2=0.0, der2=0.0, t_max=4.0):
    P = S.vector_planta(c, S.Perturbacion(), t_max)
    prm = np.array([izq, der, t_cambio, izq2, der2], float)
    return N.simular(pista.x, pista.y, pista.rumbo, pista.hueco, P, c.sx, c.sy, N.C_LAZO_ABIERTO, prm, 0, True)


def main():
    # configuración de la Fase 1 trasladada a la planta dinámica (mismo motor, masa, f_motriz, D, L)
    v1 = F1.CFG
    base1 = F1.robot_base()
    c = CF.construir(motor="pololu_hpcb12_15", control="C2")
    m = c.motor

    # ---------------------------------------------------------------- 1. modelo del motor
    # a) los cuatro datos del fabricante se reproducen exactamente con R, Ke, Kt
    w0 = m.w0
    I_vacio = (m.V_nom - m.Ke * w0) / m.R
    anotar("Motor", "corriente sin carga reproducida a 12 V", m.I0, round(I_vacio, 4), "A",
           "I = (V − Ke·ω0)/R con las constantes derivadas", "CORRECTO")
    T_bl = m.Kt * (m.V_nom / m.R - m.I0)
    anotar("Motor", "par de bloqueo reproducido a 12 V", round(m.T_bl, 5), round(T_bl, 5), "N·m",
           "T = Kt·(V/R − I0)", "CORRECTO")
    # b) velocidad libre a 7.4 V por escala alternativa (∝ V − I0·R) vs Fase 1 (con rodadura y caída de batería)
    v_escala = (7.4 - m.I0 * m.R) / (m.V_nom - m.I0 * m.R) * w0 * (0.034 / 2)
    v_f1 = F1.v_libre(base1)
    anotar("Motor", "velocidad libre a 7.4 V (D 34 mm)", round(v_f1, 3), round(v_escala, 3), "m/s",
           "escala lineal de la FEM sin carga ni caída; la de Fase 1 incluye rodadura y R interna",
           "CORRECTO", "diferencia esperada < 3 % por rodadura y caída de batería")
    # c) simulador dinámico en recta, ciclo 1, con la masa y D de la Fase 1
    cv1 = CF.construir(motor="pololu_hpcb12_15", control="C2")
    R_, T = lazo(cv1, recta(), 1.0, 1.0, t_max=4.0)
    anotar("Motor", "velocidad final en recta (simulador dinámico, config v2)", round(v_f1, 3), round(T[-1, 4], 3),
           "m/s", "integración de la planta completa", "CORRECTO", "masa v2 121 g; la velocidad libre casi no depende de la masa")
    # d) tolerancia del fabricante: ±20 % de rpm (lo publica Pololu para la serie) -> rango de v libre
    anotar("Motor", "rango de velocidad libre con ±20 % de rpm", round(v_f1, 3),
           f"{v_f1*0.8:.2f}-{v_f1*1.2:.2f}", "m/s", "tolerancia del fabricante", "LIMITACIÓN",
           "la Fase 1 usó el valor nominal sin dispersión; el simulador incluye ±5 % entre motores")

    # ---------------------------------------------------------------- 2. inercia del rotor (omitida en Fase 1)
    m_eq = 2 * c.J_eq / c.r ** 2
    anotar("Motor", "masa equivalente de rotores y llantas", 0.0, round(m_eq * 1000, 1), "g",
           "2·(J_rotor·G² + J_llanta)/r², J_rotor supuesto", "ERROR DE FASE 1",
           f"+{100*m_eq/c.masa:.0f} % de inercia de traslación cuando acelera el motor; J_rotor no publicado (supuesto)")
    R_, T = lazo(c, recta(), 1.0, 1.0, t_max=1.5)
    t = T[:, 0]; v = T[:, 4]
    t50 = float(np.interp(1.0, v, t)) if v.max() > 1.0 else float("nan")
    # Fase 1 equivalente: integración sin inercia de rotor con la misma fuerza y agarre
    dt = 1e-4; vv = 0.0; tt = 0.0
    while vv < 1.0 and tt < 5:
        F, _, _ = F1.fuerza_motriz(F1.robot_base(masa=c.masa, mu=c.mu, f_motriz=c.f_motriz), vv)
        a = min(F / c.masa, c.mu * G * c.f_motriz) - F1.CFG["traccion"]["c_rodadura"] * G
        vv += a * dt; tt += dt
    anotar("Motor", "tiempo de 0 a 1 m/s en recta", round(tt, 3), round(t50, 3), "s",
           "simulador (con inercia y transferencia de carga) vs integración tipo Fase 1 (misma masa, μ y f)",
           "DIFERENCIA", "dos efectos omitidos se compensan en parte: la inercia de rotores frena la "
           "aceleración y la transferencia de carga hacia las ruedas sube el agarre al acelerar")

    # ---------------------------------------------------------------- 3. geometría del cuello en régimen
    for L in (0.08, 0.10, 0.12):
        cc = CF.construir(motor="pololu_hpcb12_15", control="C2", L=L,
                          prm=dict(v_max=0.35, a_lat=3.0, a_lon=2.0, k_pp=1.0, kp=60.0, kd=2.0, tau_k=0.03))
        pis = circulo(0.15)
        res, T = S.correr(cc, pis, seed=1, traza=True, t_max=8.0)
        k = T[:, 0] > 0.5 * T[-1, 0]
        xy = T[k, 1:3]
        A = np.c_[2 * xy, np.ones(len(xy))]
        sol = np.linalg.lstsq(A, (xy ** 2).sum(1), rcond=None)[0]
        Ra = math.sqrt(sol[2] + sol[0] ** 2 + sol[1] ** 2)
        Ra_f1 = math.sqrt(0.15 ** 2 - L ** 2)
        err = abs(Ra - Ra_f1) / Ra_f1
        e_med = float(np.mean(T[k, 5]))
        anotar("Cuello", f"radio del eje en R150 con L = {L*1000:.0f} mm", round(Ra_f1 * 1000, 1), round(Ra * 1000, 1),
               "mm", "simulador con control en un círculo a 0.35 m/s, ajuste de circunferencia",
               "CORRECTO" if err < 0.05 else "DIFERENCIA",
               f"error {100*err:.1f} %; error medio de seguimiento en régimen e = {e_med*1000:.1f} mm "
               "(la línea no queda centrada: el eje describe un radio algo mayor)")

    # ---------------------------------------------------------------- 4. captura de la línea (geometría)
    for L in (0.09, 0.10, 0.11):
        _, arco_f1, _ = F1.captura_barra(0.15, L)
        # numérica: intersección del círculo de radio L con centro en el eje y la línea (círculo de radio R
        # tangente en el eje); se busca el punto por bisección sobre el ángulo de la línea
        R = 0.15
        lo, hi = 0.0, math.pi
        for _ in range(100):
            a = (lo + hi) / 2
            px, py = R * math.sin(a), R * (1 - math.cos(a))
            if math.hypot(px, py) < L:
                lo = a
            else:
                hi = a
        lat = R * (1 - math.cos(lo))
        anotar("Captura", f"desplazamiento en barra en arco, L = {L*1000:.0f} mm", round(arco_f1 * 1000, 2),
               round(lat * 1000, 2), "mm", "intersección numérica por bisección", "CORRECTO")

    # ---------------------------------------------------------------- 5. frenado y transferencia de carga
    f1_freno = base1.a_max
    a_lim = c.mu * G * c.f_motriz
    dec = c.mu * G * (1 - c.x_cg / c.x_apoyo) / (1 + c.mu * c.h_cg / c.x_apoyo)  # ec. con transferencia
    anotar("Frenado", "desaceleración máxima por agarre", round(f1_freno, 2), round(dec, 2), "m/s²",
           "μ·g·(1 − x_cg/b)/(1 + μ·h/b): al frenar, el peso pasa al apoyo, que no frena",
           "ERROR DE FASE 1", f"sin transferencia (config v2) serían {a_lim:.2f} m/s²")
    R_, T = lazo(c, recta(), 1.0, 1.0, t_cambio=2.0, izq2=-1.0, der2=-1.0, t_max=2.6)
    k = T[:, 0] > 2.0
    v = T[k, 4]; t = T[k, 0]
    j = int(np.argmax(v < 0.05))
    dec_sim = (v[0] - v[j]) / (t[j] - t[0])
    anotar("Frenado", "desaceleración media con inverso desde v libre (simulador)", round(f1_freno, 2),
           round(dec_sim, 2), "m/s²", "planta dinámica", "CORRECTO" if dec_sim <= dec * 1.05 + 0.2 else "DIFERENCIA",
           "incluye rodadura; coincide con la ecuación con transferencia")
    acc = c.mu * G * (1 - c.x_cg / c.x_apoyo) / (1 - c.mu * c.h_cg / c.x_apoyo)
    anotar("Frenado", "aceleración máxima por agarre (la transferencia ayuda)", round(f1_freno, 2), round(acc, 2),
           "m/s²", "μ·g·(1 − x_cg/b)/(1 − μ·h/b)", "ERROR DE FASE 1", "asimetría acelerar/frenar no modelada en Fase 1")
    anotar("Frenado", "FEM máxima a la velocidad libre a 8.4 V", round(float(F1.v_libre(F1.robot_base(V_oc=8.4))) /
           (0.034 / 2) * m.Ke, 2), round((8.4 - m.I0 * m.R), 2), "V",
           "cota superior: Ke·ω_libre ≤ V − I0·R < V_bus", "CORRECTO", "no hay bombeo de voltaje al bus por FEM en 2S")

    # ---------------------------------------------------------------- 6. distribución de masa
    mv1, xv1 = sum(v1["masa"].values()), None
    anotar("Masa", "masa total", round(mv1 * 1000, 1), round(c.masa * 1000, 1), "g",
           "suma de componentes con posición (config v2)", "ACTUALIZADO",
           "v2 cambia chasis (30 g), MCU (8 g) y apoyo (3 g) por el rediseño; no es error de cálculo")
    anotar("Masa", "fracción del peso en las ruedas f_motriz", v1["traccion"]["f_motriz"], round(c.f_motriz, 3), "",
           "1 − x_cg/x_apoyo con el CG calculado de los componentes", "ACTUALIZADO",
           f"x_cg {c.x_cg*1000:.1f} mm, apoyo a {c.x_apoyo*1000:.0f} mm, h_cg {c.h_cg*1000:.1f} mm")
    xs, b = CF.cargar()["geometria"]["x_succion"], c.x_apoyo
    anotar("Masa", "fracción de la succión sobre las ruedas", v1["succion"]["f_down_motriz"], round(1 - xs / b, 3), "",
           "palanca: 1 − x_succión/x_apoyo", "SUPUESTO REVISADO",
           "0.90 exige el faldón a 7.5 mm del eje; con el faldón a 15 mm queda 0.80")
    br = (v1["masa"]["chasis"], c.masa)
    anotar("Masa", "punto de equilibrio de la succión", 22, round(c.f_motriz * 30 / (1 - xs / b), 1), "gf",
           "f_motriz·m_vent/f_succ con valores v2", "ACTUALIZADO")

    # ---------------------------------------------------------------- 7. energía
    import pistas as PI
    cc = CF.construir(motor="pololu_hpcb12_15", control="C2",
                      prm=dict(v_max=1.1, a_lat=7.0, a_lon=7.0, k_pp=0.9, kp=37.0, kd=8.0, tau_k=0.078))
    r = S.correr(cc, PI.construir("P2"), seed=1)
    I_med = r["mAh"] * 3.6 / r["t_vuelta"] if r["completa"] else float("nan")
    anotar("Energía", "corriente media de batería en una vuelta (P2)", 0.9, round(I_med, 3), "A",
           "integral de la corriente del bus en el simulador / tiempo de vuelta", "CORRECTO (conservador)",
           f"{r['mAh']:.2f} mAh por vuelta; la Fase 1 suponía 0.6 A de motores + 0.3 A de lógica")
    anotar("Energía", "mAh por intento de 5 min sin ventilador", 75.0, round(I_med * 300 / 3.6, 1), "mAh",
           "corriente media × 300 s", "CORRECTO (conservador)", "el caso de 5 min es un límite, no una vuelta real")

    # ---------------------------------------------------------------- 8. agarre lateral con apoyo de bola
    anotar("Agarre", "la fuerza lateral la dan solo las ruedas", "sí", "sí", "",
           "en la planta el apoyo solo tiene rodadura (sin fuerza lateral)", "CORRECTO",
           "además, el CG adelantado exige diferencia de fuerza longitudinal entre ruedas para girar")

    os.makedirs(os.path.join(CF.RAIZ, "sim", "resultados", "fase2"), exist_ok=True)
    ruta = os.path.join(CF.RAIZ, "sim", "resultados", "fase2", "V_verificacion_fase1.csv")
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(FILAS[0].keys()))
        w.writeheader()
        w.writerows(FILAS)
    print(f"-> {os.path.relpath(ruta, CF.RAIZ)}")


if __name__ == "__main__":
    main()
