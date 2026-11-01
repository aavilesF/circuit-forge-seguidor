"""Interfaz de Python del simulador dinámico: arma los vectores para el núcleo numba y corre escenarios."""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

import nucleo as N
from config import G, Config
from pistas import Pista

MOTIVOS = {0: "completa", 1: "pierde la línea", 2: "detenido/tiempo", 3: "sentido contrario", 4: "vuelco"}


@dataclass(frozen=True)
class Perturbacion:
    """Variaciones de una corrida (Monte Carlo). Valores 1.0/0.0 = nominal."""
    f_mu: float = 1.0
    V_oc: float | None = None
    f_keL: float = 1.0
    f_keR: float = 1.0
    y0: float = 0.0
    psi0: float = 0.0
    f_ruido: float = 1.0
    f_vmed: float = 1.0      # error de la medición de batería del firmware
    t_extra: float = 0.0     # latencia adicional (s)


def perturbacion_aleatoria(rng: np.random.Generator) -> Perturbacion:
    """Dispersión de una salida normal: μ ±10 %, batería entre 7.6 y 8.3 V, motores ±5 % (izquierdo y
    derecho independientes), colocación ±3 mm y ±2°, error de medición de batería ±2 %."""
    return Perturbacion(f_mu=rng.uniform(0.9, 1.1), V_oc=rng.uniform(7.6, 8.3),
                        f_keL=rng.uniform(0.95, 1.05), f_keR=rng.uniform(0.95, 1.05),
                        y0=rng.uniform(-0.003, 0.003), psi0=math.radians(rng.uniform(-2, 2)),
                        f_vmed=rng.uniform(0.98, 1.02))


def paso_integracion(c: Config) -> float:
    Nmax = 0.7 * (c.masa * G + c.F_succion)
    cmax = c.mu * 1.2 * Nmax / c.eps
    m_rueda = c.J_eq / c.r ** 2
    return min(1e-4, 0.3 * m_rueda / cmax, 0.3 * c.masa / (2 * cmax))


def vector_planta(c: Config, pt: Perturbacion = Perturbacion(), t_max: float = 15.0) -> np.ndarray:
    P = np.zeros(N.NP)
    m = c.motor
    P[N.I_M] = c.masa; P[N.I_XCG] = c.x_cg; P[N.I_H] = c.h_cg; P[N.I_IZ] = c.Iz
    P[N.I_L] = c.L; P[N.I_W] = c.W; P[N.I_R] = c.r; P[N.I_XA] = c.x_apoyo
    P[N.I_XS] = c.x_succion; P[N.I_FS] = c.F_succion; P[N.I_MU] = c.mu * pt.f_mu
    P[N.I_CRR] = c.c_rr; P[N.I_EPS] = c.eps; P[N.I_J] = c.J_eq
    P[N.I_VOC] = pt.V_oc if pt.V_oc is not None else c.V_oc
    P[N.I_RINT] = c.R_int; P[N.I_ILOG] = c.I_log; P[N.I_IFAN] = c.I_fan
    P[N.I_RM] = m.R; P[N.I_KE] = m.Ke; P[N.I_KT] = m.Kt; P[N.I_I0] = m.I0
    P[N.I_LIMV] = m.limite_V if math.isfinite(m.limite_V) else 99.0
    P[N.I_MANCHA] = c.mancha; P[N.I_RUIDO] = c.ruido * pt.f_ruido; P[N.I_UMBRAL] = c.umbral
    t_lect = c.t_lectura + pt.t_extra
    P[N.I_TLECT] = t_lect; P[N.I_TCTRL] = max(c.T_ctrl, t_lect)
    P[N.I_TPERD] = c.t_perdida; P[N.I_IOCP] = c.I_ocp
    P[N.I_GRUIDO] = c.giro_ruido; P[N.I_GSESGO] = c.giro_sesgo; P[N.I_ANCHO] = c.ancho_linea
    P[N.I_KEL] = pt.f_keL; P[N.I_KER] = pt.f_keR; P[N.I_Y0] = pt.y0; P[N.I_PSI0] = pt.psi0
    P[N.I_TMAX] = t_max; P[N.I_DT] = paso_integracion(c); P[N.I_VMEDIDO] = pt.f_vmed
    P[N.I_MUK] = c.mu_k_rel; P[N.I_VSTR] = c.v_str
    return P


def vector_control(c: Config):
    p = c.prm
    if c.control == "C1":
        return N.C_PD, np.array([p["b0"], p["k_freno"], p["e_ref"], p["kp"], p["kd"], p["rueda_min"]], float)
    fuente = {"error": 0, "modelo": 1, "giroscopio": 2}[p.get("fuente_k", "error")]
    return N.C_SF, np.array([p["v_max"], p["a_lat"], p["a_lon"], p["k_pp"], p["kp"], p["kd"],
                             p["tau_d"], p["tau_k"], fuente, p.get("piso", 0.0)], float)


def correr(c: Config, pista: Pista, seed: int = 0, pt: Perturbacion = Perturbacion(),
           traza: bool = False, t_max: float = 15.0):
    P = vector_planta(c, pt, t_max)
    ctrl, prm = vector_control(c)
    R, T = N.simular(pista.x, pista.y, pista.rumbo, pista.hueco, P, c.sx, c.sy, ctrl, prm, seed, traza)
    res = dict(completa=bool(R[0]), t_vuelta=R[1], v_media=R[2], v_max=R[3], motivo=MOTIVOS[int(R[4])],
               avance=R[5], e_max=R[6], I_max=R[7], n_ocp=int(R[8]), mAh=R[9], J=R[10], V_min=R[11],
               frac_saturado=R[12], desliz_max=R[13], T_ctrl=R[14], parado=bool(R[15]))
    if res["completa"] and res["desliz_max"] > c.desliz_valido:
        res.update(completa=False, v_media=0.0, motivo="derrape")
    return (res, T) if traza else res
