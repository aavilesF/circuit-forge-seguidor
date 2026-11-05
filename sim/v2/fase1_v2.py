#!/usr/bin/env python3
"""V2 · Fase 1 — física de tracción, anticipación geométrica, succión paramétrica, fallos y energía.

NO es la simulación dinámica del robot (eso es la Fase 4): son modelos de primer orden, reproducibles, con TODOS los
datos como variables explícitas en config/v2/parametros_fase1.yaml, cada una con su tipo:
  calculado · simulado · estimado · supuesto (escenario) · verificado documentalmente · pendiente de medición física.
Nada de lo que sale de aquí es una medición. Escribe sim/resultados/v2_fase1/*.csv y *.png.

Uso: python3 sim/v2/fase1_v2.py
"""
from __future__ import annotations

import csv
import itertools
import math
import os
import sys

import numpy as np
import yaml
from numba import njit

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
SAL = os.path.join(RAIZ, "sim", "resultados", "v2_fase1")
sys.path.insert(0, os.path.join(RAIZ, "sim", "fase1"))
G = 9.81


def cargar():
    with open(os.path.join(RAIZ, "config", "v2", "parametros_fase1.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


P = cargar()


def v(clave):
    """Valor de un parámetro del YAML (cada entrada es {valor, tipo, fuente})."""
    x = P
    for k in clave.split("."):
        x = x[k]
    return x["valor"] if isinstance(x, dict) and "valor" in x else x


def escribir(nombre, filas):
    os.makedirs(SAL, exist_ok=True)
    with open(os.path.join(SAL, nombre), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
    print(f"  -> sim/resultados/v2_fase1/{nombre} ({len(filas)} filas)")


# ===================================================================== modelo de adherencia (2 ruedas motrices + apoyo)
class Geo:
    """Geometría de ESTUDIO (no es el diseño V2): eje de ruedas en x = 0, apoyo delantero en x = b, CG en (x_cg, h),
    centro de presión de la succión en x_s. El apoyo (bola o patín) no da fuerza lateral ni de frenado."""

    def __init__(self, b, x_cg, h, W, x_s):
        self.b, self.x_cg, self.h, self.W, self.x_s = b, x_cg, h, W, x_s


def N_motriz(m, Fs, g: Geo):
    """Normal estática sobre las 2 ruedas motrices (N): peso repartido entre eje y apoyo + parte de la succión."""
    return m * G * (g.b - g.x_cg) / g.b + Fs * (g.b - g.x_s) / g.b


def capacidades(m, Fs, mu, g: Geo):
    N0 = N_motriz(m, Fs, g)
    ay = mu * N0 / m                                            # lateral (solo ruedas motrices)
    ax_fr = mu * N0 / (m * (1 + mu * g.h / g.b))                 # frenado: la carga pasa al apoyo
    ax_ac = mu * N0 / (m * (1 - mu * g.h / g.b))                 # aceleración: la carga pasa al eje
    ay_vuelco = N0 * (g.W / 2) / (m * g.h)                      # rueda interior en el límite de despegar
    return dict(N0=N0, ay=ay, ax_fr=ax_fr, ax_ac=ax_ac, ay_vuelco=ay_vuelco)


def ax_frenado_combinado(m, Fs, mu, g: Geo, ay):
    """Máxima desaceleración con aceleración lateral ay (círculo de fricción con transferencia al apoyo):
    m·sqrt(ax² + ay²) = μ·(N0 − m·ax·h/b), resuelta en forma cerrada. Devuelve -1 si ay ya excede la capacidad."""
    return _ax_comb(mu * N_motriz(m, Fs, g) / m, mu * g.h / g.b, ay)


@njit(cache=True)
def _ax_comb(C, k, ay):
    """C = μ·N0/m (capacidad sin transferencia), k = μ·h/b. Solución de (1−k²)ax² + 2Ck·ax + ay² − C² = 0."""
    if abs(ay) > C:
        return -1.0
    disc = C * C * k * k - (1 - k * k) * (ay * ay - C * C)
    return (-C * k + math.sqrt(max(disc, 0.0))) / (1 - k * k)


# ===================================================================== T1: tracción requerida (fórmulas del enunciado)
def t1_traccion():
    filas = []
    for m, mu, R, vel in itertools.product(v("estudio.masas_kg"), v("estudio.mu"), v("estudio.radios_m"), v("estudio.velocidades_ms")):
        F_lat = m * vel ** 2 / R
        F_dn = max(0.0, m * vel ** 2 / (mu * R) - m * G)                      # enunciado: todo el robot adhiere
        g = geo_estudio()
        # 2 ruedas motrices + apoyo sin agarre lateral: μ·N_motriz ≥ m v²/R  ->  Fs ≥ ...
        Fs_2wd = max(0.0, (m * vel ** 2 / (mu * R) - m * G * (g.b - g.x_cg) / g.b) * g.b / (g.b - g.x_s))
        filas.append(dict(masa_kg=m, mu=mu, radio_m=R, v_ms=vel, F_lateral_N=round(F_lat, 3),
                          a_lat_ms2=round(vel ** 2 / R, 2), a_lat_g=round(vel ** 2 / R / G, 2),
                          F_down_formula_N=round(F_dn, 3), F_down_formula_gf=round(F_dn / G * 1000, 0),
                          F_down_2rm_N=round(Fs_2wd, 3), F_down_2rm_gf=round(Fs_2wd / G * 1000, 0),
                          tipo="calculado"))
    escribir("T1_traccion_requerida.csv", filas)
    return filas


def geo_estudio(**cambios):
    d = dict(b=v("geometria_estudio.b_apoyo_m"), x_cg=v("geometria_estudio.x_cg_m"), h=v("geometria_estudio.h_cg_m"),
             W=v("geometria_estudio.via_m"), x_s=v("geometria_estudio.x_succion_m"))
    d.update(cambios)
    return Geo(**d)


# ===================================================================== T2: distribución de carga por rueda
def t2_carga():
    filas = []
    m = v("estudio.masa_ref_kg"); mu = v("estudio.mu_ref")
    for Fs, xs in itertools.product(v("estudio.F_succion_N"), v("estudio.x_succion_m")):
        g = geo_estudio(x_s=xs)
        c = capacidades(m, Fs, mu, g)
        N0 = c["N0"]
        Napoyo = m * G + Fs - N0
        casos = {
            "estático": (0.0, 0.0),
            "aceleración máxima": (c["ax_ac"], 0.0),
            "frenado máximo": (-c["ax_fr"], 0.0),
            "curva al límite": (0.0, c["ay"]),
            "frenado en curva (ay = 50 % del límite)": (-ax_frenado_combinado(m, Fs, mu, g, 0.5 * c["ay"]), 0.5 * c["ay"]),
        }
        for nombre, (ax, ay) in casos.items():
            Neje = N0 + m * ax * g.h / g.b                          # ax > 0 acelera (carga al eje), < 0 frena
            dN = m * ay * g.h / g.W                                  # transferencia lateral (solo el eje resiste el balanceo)
            Nin, Nout = Neje / 2 - dN, Neje / 2 + dN
            demanda = m * math.hypot(ax, ay)
            filas.append(dict(F_succion_N=Fs, x_succion_m=xs, caso=nombre, ax_ms2=round(ax, 2), ay_ms2=round(ay, 2),
                              N_eje_N=round(Neje, 3), N_rueda_interior_N=round(Nin, 3), N_rueda_exterior_N=round(Nout, 3),
                              N_apoyo_N=round(m * G + Fs - Neje, 3),
                              uso_adherencia=round(demanda / (mu * Neje), 3) if Neje > 0 else float("nan"),
                              ay_vuelco_ms2=round(c["ay_vuelco"], 1), tipo="calculado"))
    escribir("T2_distribucion_carga.csv", filas)
    return filas


# ===================================================================== T3: anticipación geométrica (cinemática + fricción)
def trayectoria(L, R, x_cg, ds=0.0005, recta=0.4, arco_extra=1.6):
    """La barra (a L delante del eje) sigue exactamente la línea; el eje la persigue como un remolque (tractriz).
    Línea: recta en +x hasta s = 0 y después un arco de radio R a la izquierda. Devuelve, por paso de la barra:
    s_barra, longitud recorrida por el CG, curvatura de la trayectoria del CG."""
    s = np.arange(-recta, arco_extra * math.pi * R, ds)
    Px = np.where(s < 0, s, R * np.sin(np.maximum(s, 0) / R))
    Py = np.where(s < 0, 0.0, R * (1 - np.cos(np.maximum(s, 0) / R)))
    Ax, Ay = Px[0] - L, Py[0]
    Cx = np.empty_like(s); Cy = np.empty_like(s)
    for i in range(len(s)):
        dx, dy = Px[i] - Ax, Py[i] - Ay
        d = math.hypot(dx, dy)
        ux, uy = dx / d, dy / d
        if i + 1 < len(s):
            mx, my = Px[i + 1] - Px[i], Py[i + 1] - Py[i]
            k = ux * mx + uy * my                                  # el eje solo avanza en su dirección
            Ax += ux * k; Ay += uy * k
        Cx[i] = Ax + x_cg * ux; Cy[i] = Ay + x_cg * uy
    dCx, dCy = np.gradient(Cx), np.gradient(Cy)
    dsc = np.hypot(dCx, dCy)
    th = np.unwrap(np.arctan2(dCy, dCx))
    kap = np.gradient(th) / np.maximum(dsc, 1e-12)
    n = len(s) - 5                                               # el último paso no avanza el eje: se descarta
    return s[:n], (np.cumsum(dsc) - dsc[0])[:n], dsc[:n], np.abs(kap)[:n]


def v0_max_reactiva(traj, m, Fs, mu, g: Geo, delta, t_r, R):
    """Mayor velocidad de crucero con la que el robot, SIN conocer la curva, puede detectarla (la línea se separa δ de
    la prolongación de la recta: s_det = sqrt(2Rδ)), reaccionar en t_r y frenar dentro del círculo de fricción sin
    exceder la adherencia lateral en ningún punto."""
    s, sc, dsc, kap = traj
    s_det = math.sqrt(2 * R * delta)
    i_det = int(np.searchsorted(s, s_det))
    ay_max = capacidades(m, Fs, mu, g)["ay"]

    C = mu * N_motriz(m, Fs, g) / m
    k = mu * g.h / g.b
    lo, hi = 0.2, 6.0
    for _ in range(20):
        mid = (lo + hi) / 2
        if _factible(mid, s, dsc, kap, i_det, t_r, ay_max, C, k):
            lo = mid
        else:
            hi = mid
    return lo


@njit(cache=True)
def _factible(v0, s, dsc, kap, i_det, t_r, ay_max, C, k):
    vel = v0
    frenando = False
    t = 0.0
    for i in range(len(s)):
        ay = vel * vel * kap[i]
        if i >= i_det and not frenando:
            t += dsc[i] / max(vel, 1e-6)
            if t >= t_r:
                frenando = True
        if not frenando:
            if ay > ay_max * 1.0000001:
                return False
            continue
        ax = _ax_comb(C, k, ay)
        if ax < 0:
            return False
        vel = math.sqrt(max(vel * vel - 2 * ax * dsc[i], 0.04))
    return True


def v_curva(R, L, m, Fs, mu, g: Geo):
    """Velocidad estable del CG en un arco de la línea de radio R (barra sobre la línea, eje por dentro)."""
    Ra = math.sqrt(max(R * R - L * L, 1e-9))
    Rc = math.hypot(Ra, g.x_cg)
    return math.sqrt(capacidades(m, Fs, mu, g)["ay"] * Rc), Rc


def t3_anticipacion():
    filas = []
    g0 = geo_estudio()
    cache = {}
    for L, R in itertools.product(v("estudio.cuellos_m"), v("estudio.radios_anticipacion_m")):
        if L >= R:
            continue
        cache[(L, R)] = trayectoria(L, R, g0.x_cg)
    for (L, R), traj in cache.items():
        for m, mu, Fs, t_r, delta in itertools.product(v("estudio.masas_kg"), v("estudio.mu"), v("estudio.F_succion_N"),
                                                       v("estudio.latencias_s"), v("estudio.umbral_deteccion_m")):
            v0 = v0_max_reactiva(traj, m, Fs, mu, g0, delta, t_r, R)
            vc, Rc = v_curva(R, L, m, Fs, mu, g0)
            c = capacidades(m, Fs, mu, g0)
            # fórmula del enunciado, con la desaceleración en recta: d = v·t + (v² − vc²)/(2a)
            d_req_2 = 2.0 * t_r + max(4.0 - vc ** 2, 0) / (2 * c["ax_fr"])
            filas.append(dict(cuello_L_m=L, radio_m=R, masa_kg=m, mu=mu, F_succion_N=Fs, latencia_s=t_r,
                              umbral_m=delta, s_deteccion_m=round(math.sqrt(2 * R * delta), 4),
                              v_curva_ms=round(vc, 3), a_frenado_ms2=round(c["ax_fr"], 2), a_lat_ms2=round(c["ay"], 2),
                              v_crucero_max_reactiva_ms=round(v0, 3), cumple_2ms=v0 >= 2.0,
                              d_req_desde_2ms_m=round(d_req_2, 4), d_disponible_aprox_m=round(L - math.sqrt(2 * R * delta), 4),
                              tipo="calculado (cinemático + círculo de fricción)"))
    escribir("T3_anticipacion.csv", filas)
    return filas


def t3b_succion_para_2ms():
    """Fuerza de succión total mínima para que la velocidad de crucero reactiva llegue a 2.0 m/s (curva R 0.15)."""
    filas = []
    g0 = geo_estudio()
    for L in v("estudio.cuellos_m"):
        traj = trayectoria(L, 0.15, g0.x_cg)
        for m, mu, x_s in itertools.product(v("estudio.masas_kg"), v("estudio.mu"), v("estudio.x_succion_m")):
            g = geo_estudio(x_s=x_s)
            lo, hi = 0.0, 20.0
            if v0_max_reactiva(traj, m, hi, mu, g, 0.002, 0.010, 0.15) < 2.0:
                Fs = float("nan")
            else:
                for _ in range(16):
                    mid = (lo + hi) / 2
                    if v0_max_reactiva(traj, m, mid, mu, g, 0.002, 0.010, 0.15) >= 2.0:
                        hi = mid
                    else:
                        lo = mid
                Fs = hi
            filas.append(dict(cuello_L_m=L, masa_kg=m, mu=mu, x_succion_m=x_s, F_succion_total_N=round(Fs, 2),
                              F_succion_total_gf=round(Fs / G * 1000, 0) if Fs == Fs else float("nan"),
                              peso_aparente_g=round(m * 1000 + Fs / G * 1000, 0) if Fs == Fs else float("nan"),
                              tipo="calculado (cinemático + círculo de fricción; t_r 10 ms, δ 2 mm)"))
    escribir("T3b_succion_para_2ms.csv", filas)
    return filas


# ===================================================================== T4: frenado (fórmula del enunciado)
def t4_frenado():
    filas = []
    for a, t_r in itertools.product(v("estudio.deceleraciones_ms2"), v("estudio.latencias_s")):
        for vel in (1.0, 1.5, 2.0):
            filas.append(dict(v_ms=vel, a_ms2=a, latencia_s=t_r, d_parada_m=round(vel * t_r + vel ** 2 / (2 * a), 4),
                              d_hasta_1ms_m=round(vel * t_r + max(vel ** 2 - 1.0, 0) / (2 * a), 4), tipo="calculado"))
    escribir("T4_frenado.csv", filas)


# ===================================================================== T5-T6: ventilador y punto de funcionamiento
def rho_sitio():
    """Densidad del aire (atmósfera estándar ISA) a la altitud del evento."""
    h = v("aire.altitud_m")
    return 1.225 * (1 - 2.25577e-5 * h) ** 4.25588


def dp0_teorica(rpm, rho):
    """Presión de cierre ideal de un rotor de álabes radiales: ½ρω²(r2² − r1²) (vórtice forzado en los canales)."""
    w = rpm * 2 * math.pi / 60
    r1, r2 = v("ventilador.r1_m"), v("ventilador.r2_m")
    return 0.5 * rho * w * w * (r2 * r2 - r1 * r1)


def q0_teorico(rpm, phi):
    """Caudal libre de orden de magnitud: φ·π·D2·b2·u2 (φ = coeficiente de caudal, supuesto)."""
    u2 = rpm * 2 * math.pi / 60 * v("ventilador.r2_m")
    return phi * math.pi * 2 * v("ventilador.r2_m") * v("ventilador.b2_m") * u2


def t5_ventilador():
    filas = []
    for rpm in v("estudio.rpm_ventilador"):
        for rho, sitio in ((1.204, "nivel del mar 20 °C"), (rho_sitio(), "León (ISA)")):
            dp = dp0_teorica(rpm, rho)
            filas.append(dict(rpm=rpm, sitio=sitio, rho_kgm3=round(rho, 3), u2_ms=round(rpm * 2 * math.pi / 60 * v("ventilador.r2_m"), 1),
                              dP0_ideal_Pa=round(dp, 0),
                              dP0_con_rendimiento_bajo_Pa=round(dp * v("ventilador.sigma_presion")[0], 0),
                              dP0_con_rendimiento_alto_Pa=round(dp * v("ventilador.sigma_presion")[1], 0),
                              Q0_phi_bajo_Ls=round(q0_teorico(rpm, v("ventilador.phi_caudal")[0]) * 1000, 2),
                              Q0_phi_alto_Ls=round(q0_teorico(rpm, v("ventilador.phi_caudal")[1]) * 1000, 2),
                              tipo="calculado (modelo ideal; NO es la curva del fabricante)"))
    escribir("T5_ventilador_teorico.csv", filas)
    return filas


def punto_funcionamiento(dP0, Q0, area, perim, gap, rho, K_ducto=None, A_ent=None, k_curva=2.0, Cd=None, lab=None):
    """Intersección de la curva del ventilador ΔP_f(Q) = ΔP0·(1 − (Q/Q0)^k) menos la pérdida del conducto de entrada
    K·½ρ(Q/A)² con la curva de la cámara (fugas por la ranura del faldón): Q = Cd·perímetro·ranura·sqrt(2ΔP/ρ).
    Devuelve (ΔP_cámara, Q, fuerza)."""
    K = v("camara.K_entrada") if K_ducto is None else K_ducto
    A_in = v("modulo.A_entrada_m2") if A_ent is None else A_ent
    Cd = v("camara.Cd_ranura") if Cd is None else Cd
    lab = v("camara.labio_m") if lab is None else lab

    def dp_fan(Q):
        return max(dP0 * (1 - (Q / Q0) ** k_curva), 0.0) - K * 0.5 * rho * (Q / A_in) ** 2

    def q_fuga(dp):
        return Cd * perim * gap * math.sqrt(2 * max(dp, 0) / rho)
    lo, hi = 0.0, Q0
    for _ in range(80):
        Q = (lo + hi) / 2
        if q_fuga(dp_fan(Q)) > Q:
            lo = Q
        else:
            hi = Q
    Q = lo
    dp = max(dp_fan(Q), 0.0)
    A_ef = area + perim * lab / 2                                # el labio del faldón aporta la mitad de su área
    return dp, Q, dp * A_ef


def t6_operacion():
    filas = []
    rho = rho_sitio()
    for (nombre, lx, ly), gap, (dP0, Q0) in itertools.product(v("camara.escenarios"), v("camara.ranuras_m"),
                                                               v("ventilador.escenarios_curva")):
        area, perim = lx * ly, 2 * (lx + ly)
        dp, Q, F = punto_funcionamiento(dP0, Q0, area, perim, gap, rho)
        filas.append(dict(camara=nombre, lx_m=lx, ly_m=ly, area_cm2=round(area * 1e4, 1), ranura_mm=gap * 1000,
                          dP0_Pa=dP0, Q0_Ls=Q0 * 1000, dP_camara_Pa=round(dp, 0), fraccion_dP0=round(dp / dP0, 3),
                          Q_Ls=round(Q * 1000, 3), F_succion_N=round(F, 3), F_succion_gf=round(F / G * 1000, 0),
                          P_fluido_W=round(dp * Q, 3), tipo="calculado sobre escenarios supuestos (sin curva del fabricante)"))
    escribir("T6_punto_funcionamiento.csv", filas)
    return filas


# ===================================================================== T7: fallos del sistema de succión
def t7_fallos():
    """Cada fallo se expresa como fracción de la fuerza nominal y sus consecuencias en la curva más cerrada (R 0.15 m)
    a la velocidad planeada con succión nominal."""
    rho = rho_sitio()
    lx, ly = v("fallos.camara_m")
    area, perim = lx * ly, 2 * (lx + ly)
    gap0 = v("fallos.ranura_m")
    dP0, Q0 = v("fallos.ventilador")
    _, _, F_nom = punto_funcionamiento(dP0, Q0, area, perim, gap0, rho)
    Vbat_lleno, Vbat_bajo = v("bateria.V_llena"), v("bateria.V_baja")
    escenarios = [
        ("nominal", F_nom, "—"),
        ("pérdida total de alimentación", 0.0, "corriente del ventilador ≈ 0 / tacómetro sin pulsos"),
        ("RPM al 80 %", punto_funcionamiento(dP0 * 0.64, Q0 * 0.8, area, perim, gap0, rho)[2], "tacómetro"),
        ("RPM al 60 %", punto_funcionamiento(dP0 * 0.36, Q0 * 0.6, area, perim, gap0, rho)[2], "tacómetro"),
        ("batería baja sin compensar (ΔP ∝ V²)", punto_funcionamiento(dP0 * (Vbat_bajo / Vbat_lleno) ** 2, Q0 * Vbat_bajo / Vbat_lleno,
                                                                       area, perim, gap0, rho)[2], "medición de VBAT"),
        ("ranura 0.5 → 1.0 mm (faldón gastado)", punto_funcionamiento(dP0, Q0, area, perim, 0.001, rho)[2], "solo con sensor de presión"),
        ("ranura 0.5 → 2.0 mm (pérdida de depresión: escalón, unión del tablero)", punto_funcionamiento(dP0, Q0, area, perim, 0.002, rho)[2],
         "solo con sensor de presión o por deslizamiento"),
        ("entrada obstruida al 75 %", punto_funcionamiento(dP0, Q0, area, perim, gap0, rho, A_ent=v("modulo.A_entrada_m2") * 0.25)[2],
         "corriente del ventilador (cambia con el caudal)"),
        ("fallo del sensor de supervisión", F_nom, "se desconoce: el firmware debe asumir el peor caso"),
    ]
    filas = []
    m = v("estudio.masa_ref_kg"); mu = v("estudio.mu_ref"); g = geo_estudio()
    L = v("fallos.cuello_m"); R = 0.15
    vc_nom, Rc = v_curva(R, L, m, F_nom, mu, g)
    v_plan = vc_nom * v("fallos.factor_plan")
    for nombre, F, deteccion in escenarios:
        vc, _ = v_curva(R, L, m, F, mu, g)
        cap = capacidades(m, F, mu, g)["ay"]
        dem = v_plan ** 2 / Rc
        filas.append(dict(escenario=nombre, F_succion_N=round(F, 3), fraccion_nominal=round(F / F_nom, 3) if F_nom else 0,
                          v_curva_R150_ms=round(vc, 3), v_planeada_ms=round(v_plan, 3),
                          uso_adherencia_en_curva=round(dem / cap, 3), derrapa=dem > cap, deteccion=deteccion,
                          tipo="calculado sobre escenario supuesto"))
    escribir("T7_fallos.csv", filas)
    # tiempo hasta el derrape si la succión cae exponencialmente (giro libre del rotor, τ supuesto)
    filas2 = []
    for tau, k_plan in itertools.product(v("fallos.tau_caida_s"), (0.8, 0.9, 1.0)):
        vplan = vc_nom * k_plan
        dem = vplan ** 2 / Rc
        cap0 = capacidades(m, 0.0, mu, g)["ay"]; capN = capacidades(m, F_nom, mu, g)["ay"]
        # cap(t) = cap0 + (capN − cap0)·e^(−t/τ); derrape cuando cap(t) < dem
        if dem <= cap0:
            t_d = float("inf")
        else:
            t_d = -tau * math.log((dem - cap0) / (capN - cap0))
        filas2.append(dict(tau_s=tau, factor_plan=k_plan, v_planeada_ms=round(vplan, 3),
                           t_hasta_derrape_ms=("sin derrape" if math.isinf(t_d) else round(t_d * 1000, 1)), tipo="calculado"))
    escribir("T7b_tiempo_derrape.csv", filas2)
    return filas, F_nom


# ===================================================================== T8: energía y tiempo de vuelta (cuasiestático)
def topes_pista(pista, m, Fs, mu, g: Geo, L, v_tope, ds):
    """Tope de velocidad en cada punto de la pista (coordenada a lo largo de la línea, paso ds), medido en la barra
    (sobre la línea): v_tope en recta; en un arco, la velocidad estable del CG llevada a la barra (vc · R / Rc)."""
    cap = []
    for seg in pista.segs:
        if seg[0] == "S":
            cap += [v_tope] * max(int(round(seg[1] / ds)), 1)
        else:
            R, th = seg[1], math.radians(abs(seg[2]))
            vc, Rc = v_curva(R, L, m, Fs, mu, g)
            cap += [min(v_tope, vc * R / Rc)] * max(int(round(th * R / ds)), 1)
    return np.array(cap, dtype=float)


def perfil_vuelta(cap, a_acc, a_fr, ds, horizonte=None, v_ini=0.0):
    """Perfil de velocidad FACTIBLE sobre los topes cap (uno por tramo de largo ds) desde v_ini.

    Pasada hacia atrás (frenado con a_fr) y hacia adelante (aceleración con a_acc). horizonte = None: el robot conoce
    toda la pista (mapa). horizonte = k tramos: robot reactivo, solo "ve" k tramos adelante (la barra va L delante del
    eje): el frenado por un tope que aún no ve no puede empezar antes. Devuelve (v en los nodos [n + 1], t por tramo,
    desaceleración máxima exigida). Si esa desaceleración supera a_fr, el perfil reactivo NO es factible (el robot
    llega a la curva más rápido de lo que puede frenar): se informa, no se oculta."""
    n = len(cap)
    if horizonte is None:
        vb = cap.copy()
        for i in range(n - 2, -1, -1):
            vb[i] = min(vb[i], math.sqrt(vb[i + 1] ** 2 + 2 * a_fr * ds))
    else:
        k = int(horizonte)
        vb = cap.copy()
        d = np.arange(1, k + 1) * ds
        for i in range(n):
            ven = cap[i + 1:i + 1 + k]
            if len(ven):
                vb[i] = min(vb[i], float(np.min(np.sqrt(ven ** 2 + 2 * a_fr * d[:len(ven)]))))
    vel = np.zeros(n + 1)
    vel[0] = v_ini
    a_req = 0.0
    for i in range(n):
        v_sig = min(math.sqrt(vel[i] ** 2 + 2 * a_acc * ds), vb[i])
        a_req = max(a_req, (vel[i] ** 2 - v_sig ** 2) / (2 * ds))
        vel[i + 1] = v_sig
    dt = 2 * ds / np.maximum(vel[1:] + vel[:-1], 1e-9)       # exacto con aceleración constante en cada tramo
    return vel, dt, a_req


def tiempo_vuelta(pista, m, Fs, mu, g: Geo, L, v_crucero, a_acc_max, ds=0.002, detalle=False):
    """Vuelta desde parado de un robot REACTIVO: tope v_crucero (la anticipación de la Fase 1 lo limita) y en cada
    arco la velocidad estable de ese radio; solo puede frenar por lo que la barra ya vio (horizonte = L).
    Corrige la versión anterior (antes de la Fase 3.5), que sumaba (v_crucero − v)/a negativo cuando el robot salía de
    un arco más rápido que v_crucero y no limitaba la velocidad del arco a v_crucero."""
    c = capacidades(m, Fs, mu, g)
    cap = topes_pista(pista, m, Fs, mu, g, L, v_crucero, ds)
    vel, dt, a_req = perfil_vuelta(cap, min(c["ax_ac"], a_acc_max), c["ax_fr"], ds, horizonte=round(L / ds))
    t = float(np.sum(dt))
    if detalle:
        return dict(t=t, vel=vel, dt=dt, a_req=a_req, a_fr=c["ax_fr"], factible=a_req <= c["ax_fr"] * (1 + 1e-6))
    return t


def tiempo_vuelta_mapa(pista, m, Fs, mu, g: Geo, L, v_tope, a_acc_max, ds=0.002, detalle=False):
    """Cota de referencia: el robot conoce la pista (mapa aprendido en la vuelta) y frena ANTES de cada curva."""
    c = capacidades(m, Fs, mu, g)
    cap = topes_pista(pista, m, Fs, mu, g, L, v_tope, ds)
    vel, dt, a_req = perfil_vuelta(cap, min(c["ax_ac"], a_acc_max), c["ax_fr"], ds, horizonte=None)
    t = float(np.sum(dt))
    if detalle:
        return dict(t=t, vel=vel, dt=dt, a_req=a_req, a_fr=c["ax_fr"], factible=a_req <= c["ax_fr"] * (1 + 1e-6))
    return t


def t8_energia(t3):
    import calculos_fisicos as F1  # pistas sintéticas de la Fase 1 (dentro del reglamento)
    filas = []
    g = geo_estudio()
    m = v("estudio.masa_ref_kg"); mu = v("estudio.mu_ref"); L = v("energia.cuello_m")
    t_r = v("energia.latencia_s"); delta = v("energia.umbral_m")
    rho = rho_sitio()
    lx, ly = v("fallos.camara_m")
    dP0, Q0 = v("fallos.ventilador")
    traj = trayectoria(L, 0.15, g.x_cg)
    for nivel, f_rpm in v("energia.niveles"):
        if f_rpm > 0:
            _, _, Fs = punto_funcionamiento(dP0 * f_rpm ** 2, Q0 * f_rpm, lx * ly, 2 * (lx + ly), v("fallos.ranura_m"), rho)
        else:
            Fs = 0.0
        m_eff = m + (0.0 if f_rpm == 0 and v("energia.sin_ventilador_quita_masa") else 0.0)
        v0 = v0_max_reactiva(traj, m_eff, Fs, mu, g, delta, t_r, 0.15)
        v_cr = min(v0, v("energia.v_tope_ms"))
        for P_max in v("energia.P_ventilador_max_W"):
            Pf = P_max * f_rpm ** 3
            det = [tiempo_vuelta(p, m_eff, Fs, mu, g, L, v_cr, v("energia.a_acc_motor_ms2"), detalle=True) for p in F1.pistas()]
            tiempos = [d["t"] for d in det]
            tm = sum(tiempos) / len(tiempos)
            I_fan = Pf / v("bateria.V_nominal")
            filas.append(dict(nivel=nivel, fraccion_rpm=f_rpm, F_succion_N=round(Fs, 3), v_crucero_ms=round(v_cr, 3),
                              **{f"t_{p.nombre.split()[0]}_s": round(x, 3) for p, x in zip(F1.pistas(), tiempos)},
                              t_medio_s=round(tm, 3), P_ventilador_max_W=P_max, P_ventilador_W=round(Pf, 2),
                              E_ventilador_por_vuelta_J=round(Pf * tm, 1),
                              mAh_ventilador_por_vuelta=round(I_fan * tm / 3.6, 2),
                              caida_tension_V=round(I_fan * v("bateria.R_interna_ohm"), 3),
                              perfil_factible=all(d["factible"] for d in det),
                              tipo="calculado (cuasiestático, perfil factible adelante/atrás; NO es la simulación dinámica)"))
    escribir("T8_energia.csv", filas)
    return filas


def t8b_reactivo_vs_mapa():
    import calculos_fisicos as F1
    filas = []
    g = geo_estudio()
    m = v("estudio.masa_ref_kg"); mu = v("estudio.mu_ref"); L = v("energia.cuello_m")
    traj = trayectoria(L, 0.15, g.x_cg)
    for Fs in v("estudio.F_succion_N"):
        v0 = v0_max_reactiva(traj, m, Fs, mu, g, v("energia.umbral_m"), v("energia.latencia_s"), 0.15)
        v_cr = min(v0, v("energia.v_tope_ms"))
        dr = [tiempo_vuelta(p, m, Fs, mu, g, L, v_cr, v("energia.a_acc_motor_ms2"), detalle=True) for p in F1.pistas()]
        dm = [tiempo_vuelta_mapa(p, m, Fs, mu, g, L, v("energia.v_tope_ms"), v("energia.a_acc_motor_ms2"), detalle=True)
              for p in F1.pistas()]
        tr = [d["t"] for d in dr]
        tm = [d["t"] for d in dm]
        filas.append(dict(F_succion_N=Fs, v_crucero_reactiva_ms=round(v_cr, 3), t_medio_reactivo_s=round(sum(tr) / 4, 3),
                          t_medio_con_mapa_s=round(sum(tm) / 4, 3),
                          ganancia_mapa=round(1 - sum(tm) / sum(tr), 3),
                          perfil_factible=all(d["factible"] for d in dr + dm),
                          tipo="calculado (cuasiestático, perfil factible; mapas permitidos por los organizadores)"))
    escribir("T8b_reactivo_vs_mapa.csv", filas)


# ===================================================================== T9: requisitos de motor (para la Fase 2)
def t9_motor():
    filas = []
    for m, D, a in itertools.product(v("estudio.masas_kg"), v("motor_req.diametros_m"), v("estudio.deceleraciones_ms2")):
        F = m * a                                     # fuerza total en el piso (2 ruedas)
        T = F * D / 2 / 2                             # par por rueda
        w = 2.0 / (D / 2)
        filas.append(dict(masa_kg=m, D_llanta_m=D, a_ms2=a, F_total_N=round(F, 3), par_por_rueda_Nm=round(T, 4),
                          par_por_rueda_kgcm=round(T / 0.0980665, 3), rpm_rueda_a_2ms=round(w * 60 / (2 * math.pi), 0),
                          P_mec_por_motor_a_2ms_W=round(T * w, 2), tipo="calculado"))
    escribir("T9_requisitos_motor.csv", filas)


# ===================================================================== gráficas
def graficas(t3, t6):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 2, figsize=(13, 5))
    for ax, mu in zip(axs, (0.8, 0.6)):
        for L in v("estudio.cuellos_m"):
            pts = sorted({(f["F_succion_N"], f["v_crucero_max_reactiva_ms"]) for f in t3 if f["cuello_L_m"] == L and f["radio_m"] == 0.15
                          and f["masa_kg"] == v("estudio.masa_ref_kg") and f["mu"] == mu and f["latencia_s"] == 0.01
                          and f["umbral_m"] == 0.002})
            if pts:
                ax.plot([p[0] for p in pts], [p[1] for p in pts], "o-", label=f"cuello L = {L * 1000:.0f} mm")
        ax.axhline(2.0, color="r", ls="--", lw=1, label="meta 2.0 m/s")
        ax.set_xlabel("fuerza de succión total [N] (70 % sobre las ruedas motrices: centro 30 mm delante del eje)"); ax.set_ylabel("velocidad de crucero máxima (reactiva) [m/s]")
        ax.set_title(f"Anticipación: curva R 150 mm, μ = {mu}, m = {v('estudio.masa_ref_kg') * 1000:.0f} g, t_r 10 ms, δ 2 mm", fontsize=9)
        ax.grid(alpha=0.3); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(SAL, "F1_anticipacion.png"), dpi=150); plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 5))
    for nombre, lx, ly in v("camara.escenarios"):
        for (dP0, Q0) in v("ventilador.escenarios_curva")[1:2]:
            pts = [(f["ranura_mm"], f["F_succion_N"]) for f in t6 if f["camara"] == nombre and f["dP0_Pa"] == dP0 and f["Q0_Ls"] == Q0 * 1000]
            ax.plot([p[0] for p in pts], [p[1] for p in pts], "o-", label=f"{nombre} ({lx * 1000:.0f}×{ly * 1000:.0f} mm)")
    ax.set_xlabel("ranura del faldón [mm]"); ax.set_ylabel("fuerza de succión [N]")
    d, q = v("ventilador.escenarios_curva")[1]
    ax.set_title(f"Fuerza contra ranura — ventilador SUPUESTO ΔP0 {d} Pa, Q0 {q * 1000:.0f} L/s (León)", fontsize=9)
    ax.grid(alpha=0.3); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(SAL, "F2_succion_ranura.png"), dpi=150); plt.close(fig)


def main():
    os.makedirs(SAL, exist_ok=True)
    print("V2 Fase 1 — densidad del aire en el sitio (ISA): %.3f kg/m³" % rho_sitio())
    t1_traccion()
    t2_carga()
    t3 = t3_anticipacion()
    t3b_succion_para_2ms()
    t4_frenado()
    t5_ventilador()
    t6 = t6_operacion()
    t7_fallos()
    t8_energia(t3)
    t8b_reactivo_vs_mapa()
    t9_motor()
    graficas(t3, t6)


if __name__ == "__main__":
    main()
