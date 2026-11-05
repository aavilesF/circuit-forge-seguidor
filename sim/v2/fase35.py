#!/usr/bin/env python3
"""V2 · Fase 3.5 (correcciones de la auditoría externa):

T12  Altura del faldón: el borde se define con el hundimiento del chasis cuando las llantas se comprimen (succión
     máxima con 500 Pa + cargas dinámicas), con ≥ 0.5 mm de margen en el peor caso. Fuerza de succión, crucero
     reactivo y vueltas que quedan con esa ranura real (500 Pa, conservador).
T13  Revisión térmica del frenado del Pololu #5183 con el DRV8874 (ITRIP ≈ 2.4 A): corriente y calor por vuelta con el
     perfil factible, temperatura del devanado y límite de corriente para el firmware.

Geometría y masa: config/v2/robot_v2.yaml y hardware/v2/mecanica/propiedades_masa.json (CAD).
Uso: python3 sim/v2/fase35.py"""
from __future__ import annotations

import csv
import json
import math
import os
import sys

import numpy as np
import yaml

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import fase1_v2 as F1  # noqa: E402
import hundimiento as H  # noqa: E402
import calculos_fisicos as P1  # noqa: E402

RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
SAL = os.path.join(RAIZ, "sim", "resultados", "v2_fase35")
G = yaml.safe_load(open(os.path.join(RAIZ, "config", "v2", "robot_v2.yaml"), encoding="utf-8"))
v = lambda s, k: G[s][k]["valor"]   # noqa: E731
MP = json.load(open(os.path.join(RAIZ, "hardware", "v2", "mecanica", "propiedades_masa.json"), encoding="utf-8"))

M = MP["masa_total_g"] / 1000
X_CG, Z_CG = MP["cg_mm"][0] / 1000, MP["cg_mm"][2] / 1000
B = v("rueda_loca", "x") / 1000
W = 2 * v("ruedas", "y_centro") / 1000
YR = v("ruedas", "y_centro") / 1000
XS = v("camara", "x_centro") / 1000
L = v("robot", "L_sensores") / 1000
MU = 0.8
CAM = v("camara", "interior")[0] / 1000
PARED = v("camara", "pared") / 1000
DP0 = v("fase35", "dP0_conservador_Pa")
Q0 = v("fase35", "Q0_m3s")
MARGEN = v("fase35", "margen_faldon")
A_ACC_MOTOR = 10.5                                  # T10 (Fase 2): aceleración que dan los #5183 a la salida de curva
GEO = F1.Geo(b=B, x_cg=X_CG, h=Z_CG, W=W, x_s=XS)
RHO = F1.rho_sitio()
PERIM = 4 * (CAM + PARED)                           # perímetro por el centro de la pared
AREA = CAM * CAM
# esquinas y puntos del borde del faldón (marco del robot, m)
XC = v("camara", "x_centro") / 1000
X_TRAS, X_DEL = XC - CAM / 2 - PARED, XC + CAM / 2 + PARED
Y_LAT = CAM / 2 + PARED


def escribir(nombre, filas):
    os.makedirs(SAL, exist_ok=True)
    with open(os.path.join(SAL, nombre), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader(); w.writerows(filas)
    print(f"  -> sim/resultados/v2_fase35/{nombre} ({len(filas)} filas)")


def perimetro(n=400):
    """Puntos del borde del faldón (recorrido del rectángulo por el centro de la pared) y su peso de longitud."""
    pts = []
    lados = [((X_TRAS, -Y_LAT), (X_DEL, -Y_LAT)), ((X_DEL, -Y_LAT), (X_DEL, Y_LAT)),
             ((X_DEL, Y_LAT), (X_TRAS, Y_LAT)), ((X_TRAS, Y_LAT), (X_TRAS, -Y_LAT))]
    for (x0, y0), (x1, y1) in lados:
        for t in (np.arange(n) + 0.5) / n:
            pts.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    return np.array(pts)


def suspension(delta):
    F_max = DP0 * (AREA + PERIM * F1.v("camara.labio_m") / 2)       # cámara cerrada: la fuerza más alta posible
    c = F1.capacidades(M, F_max, MU, GEO)
    c0 = F1.capacidades(M, 0.0, MU, GEO)
    return H.Suspension(M, X_CG, Z_CG, B, W, YR, XS, F_max, delta, min(A_ACC_MOTOR, c["ax_ac"]), c["ax_fr"], c["ay"],
                        sin_succion=(min(A_ACC_MOTOR, c0["ax_ac"]), c0["ax_fr"], c0["ay"])), F_max


def borde_faldon(S):
    """Altura del borde (sin succión, geometría del CAD) lineal en x: en cada extremo, el mayor hundimiento posible en
    sus dos esquinas más el margen. Como el hundimiento de cada caso es lineal en x, la recta entre los extremos
    acota todo el borde (conservador)."""
    e_tras = max(S.envolvente(X_TRAS, y) for y in (Y_LAT, -Y_LAT)) + MARGEN
    e_del = max(S.envolvente(X_DEL, y) for y in (Y_LAT, -Y_LAT)) + MARGEN
    return e_tras, e_del


def altura_borde(x, e_tras, e_del):
    return e_tras + (e_del - e_tras) * (x - X_TRAS) / (X_DEL - X_TRAS)


def t12_faldon():
    filas = []
    pts = perimetro()
    traj = F1.trayectoria(L, 0.15, X_CG)
    for delta in v("fase35", "variantes_compresion"):
        S, F_max = suspension(delta)
        e_tras, e_del = borde_faldon(S)
        e = altura_borde(pts[:, 0], e_tras, e_del)
        # holgura mínima en el peor caso (con la succión máxima) y sin succión
        h_min = min(float(np.min(e - np.array([S.hundimiento(x, y, F_max, ax, ay) for x, y in pts])))
                    for _, ax, ay in S.casos)
        h_min0 = float(np.min(e - np.array([S.envolvente_sin_succion(x, y) for x, y in pts])))
        # punto de trabajo real en recta (estático): iteración succión <-> compresión
        Fs = F_max
        for _ in range(30):
            g = e - np.array([S.hundimiento(x, y, Fs) for x, y in pts])
            h_eq = float(np.mean(np.maximum(g, 0.0)))                   # la fuga es lineal en la ranura: media exacta
            Fs_n = F1.punto_funcionamiento(DP0, Q0, AREA, PERIM, h_eq, RHO)[2]
            if abs(Fs_n - Fs) < 1e-5:
                break
            Fs = 0.5 * (Fs + Fs_n)
        v0 = F1.v0_max_reactiva(traj, M, Fs, MU, GEO, 0.002, 0.010, 0.15)
        vcr = min(v0, 2.0)
        tr = [F1.tiempo_vuelta(p, M, Fs, MU, GEO, L, vcr, A_ACC_MOTOR) for p in P1.pistas()]
        tm = [F1.tiempo_vuelta_mapa(p, M, Fs, MU, GEO, L, 2.0, A_ACC_MOTOR) for p in P1.pistas()]
        filas.append(dict(
            compresion_llanta_diseno_mm=delta * 1e3, rigidez_llanta_N_mm=round(S.k / 1e3, 3),
            F_succion_max_500Pa_N=round(F_max, 3),
            borde_trasero_mm=round(e_tras * 1e3, 2), borde_delantero_mm=round(e_del * 1e3, 2),
            holgura_min_peor_caso_mm=round(h_min * 1e3, 3), holgura_min_sin_succion_mm=round(h_min0 * 1e3, 3),
            ranura_media_en_recta_mm=round(h_eq * 1e3, 3), F_succion_real_N=round(Fs, 3),
            v_crucero_reactiva_ms=round(vcr, 3), t_medio_reactivo_s=round(sum(tr) / len(tr), 3),
            t_medio_con_mapa_s=round(sum(tm) / len(tm), 3),
            tipo="calculado (compresión de llanta SUPUESTA; ΔP0 500 Pa conservador; pendiente de medición física)"))
    escribir("T12_faldon.csv", filas)
    return filas


def t13_termico(succiones):
    """Corriente por motor a lo largo de la vuelta con el perfil factible y calor en el devanado, para cada succión
    (la más alta frena más fuerte y calienta más). Al final, el caso de ABUSO: frenar siempre con la corriente que deja
    pasar el DRV8874 (ITRIP) en vez de la que pide la adherencia."""
    R = v("fase35", "motor_R_ohm"); kt = v("fase35", "motor_kt_Nm_A"); I0 = v("fase35", "motor_I0_A")
    Rth = v("fase35", "motor_Rth_KW"); Cth = v("fase35", "motor_Cth_JK"); dTmax = v("fase35", "motor_dT_max_K")
    r = v("ruedas", "D") / 2000
    filas = []
    for p, modo, Fs_trabajo in [(p, mo, fs) for fs in succiones for p in P1.pistas() for mo in ("reactivo", "mapa")]:
        c = F1.capacidades(M, Fs_trabajo, MU, GEO)
        if True:
            if modo == "mapa":
                d = F1.tiempo_vuelta_mapa(p, M, Fs_trabajo, MU, GEO, L, 2.0, A_ACC_MOTOR, detalle=True)
            else:
                traj = F1.trayectoria(L, 0.15, X_CG)
                vcr = min(F1.v0_max_reactiva(traj, M, Fs_trabajo, MU, GEO, 0.002, 0.010, 0.15), 2.0)
                d = F1.tiempo_vuelta(p, M, Fs_trabajo, MU, GEO, L, vcr, A_ACC_MOTOR, detalle=True)
            vel, dt = d["vel"], d["dt"]
            a = (vel[1:] ** 2 - vel[:-1] ** 2) / (2 * 0.002)
            Fm = M * a / 2                                              # fuerza por llanta
            I = np.abs(Fm) * r / kt + I0                                # el frenado por inversión también es |τ|/kt
            E = float(np.sum(I ** 2 * R * dt))
            T = float(np.sum(dt))
            P_med = E / T
            # 3 vueltas seguidas (una ronda) y después régimen permanente si se dieran vueltas sin parar
            dT_ronda = P_med * Rth * (1 - math.exp(-3 * T / (Rth * Cth)))
            filas.append(dict(
                F_succion_N=round(Fs_trabajo, 3), pista=p.nombre.split()[0], modo=modo, t_vuelta_s=round(T, 3), I_pico_A=round(float(I.max()), 3),
                t_sobre_1p5A_s=round(float(np.sum(dt[I > 1.5])), 3), I_rms_A=round(math.sqrt(E / R / T), 3),
                calor_por_vuelta_J=round(E, 2), P_media_W=round(P_med, 3),
                dT_ronda_3_vueltas_K=round(dT_ronda, 1), dT_permanente_K=round(P_med * Rth, 1),
                dT_max_K=dTmax, a_frenado_adherencia_ms2=round(c["ax_fr"], 2),
                I_frenado_adherencia_A=round(M * c["ax_fr"] / 2 * r / kt + I0, 3),
                tipo="calculado sobre datos del motor verificados y térmicos ESTIMADOS (Rth, Cth)"))
    # abuso: en cada arco el robot frena de 2.0 m/s a la velocidad del arco con la corriente limitada por ITRIP
    for itrip in (2.44, 1.56):
        Fs = max(succiones)
        for p in P1.pistas():
            E = 0.0; t_fr = 0.0
            tau = (itrip - I0) * kt
            a = 2 * tau / r / M                                          # desaceleración pedida (excede la adherencia)
            for seg in p.segs:
                if seg[0] == "A":
                    vc, Rc = F1.v_curva(seg[1], L, M, Fs, MU, GEO)
                    dt_f = max(2.0 - min(vc, 2.0), 0.0) / a
                    E += itrip ** 2 * R * dt_f; t_fr += dt_f
            T = F1.tiempo_vuelta_mapa(p, M, Fs, MU, GEO, L, 2.0, A_ACC_MOTOR)
            filas.append(dict(F_succion_N=round(Fs, 3), pista=p.nombre.split()[0], modo=f"ABUSO frenado a ITRIP {itrip} A",
                              t_vuelta_s=round(T, 3), I_pico_A=itrip, t_sobre_1p5A_s=round(t_fr, 3),
                              I_rms_A=round(math.sqrt(E / R / T), 3), calor_por_vuelta_J=round(E, 2), P_media_W=round(E / T, 3),
                              dT_ronda_3_vueltas_K=round(E / T * Rth * (1 - math.exp(-3 * T / (Rth * Cth))), 1),
                              dT_permanente_K=round(E / T * Rth, 1), dT_max_K=dTmax, a_frenado_adherencia_ms2=round(a, 2),
                              I_frenado_adherencia_A=itrip,
                              tipo="calculado: solo el calor de los frenados (cota inferior del caso de abuso)"))
    escribir("T13_termico_frenado.csv", filas)
    return filas


def main():
    print("V2 Fase 3.5 — faldón, succión conservadora (500 Pa) y térmica del frenado")
    t12 = t12_faldon()
    fs_diseno = next(f["F_succion_real_N"] for f in t12 if abs(f["compresion_llanta_diseno_mm"] - v("fase35", "compresion_llanta_diseno") * 1e3) < 1e-9)
    t13 = t13_termico([max(f["F_succion_real_N"] for f in t12), 3.1])   # 3.1 N: meta de la Fase 1 si la báscula da más
    for f in t12:
        print("   faldón δ={compresion_llanta_diseno_mm} mm: borde {borde_trasero_mm}/{borde_delantero_mm} mm, holgura mín "
              "{holgura_min_peor_caso_mm} mm, ranura media {ranura_media_en_recta_mm} mm, F {F_succion_real_N} N, "
              "crucero {v_crucero_reactiva_ms} m/s, vuelta {t_medio_reactivo_s}/{t_medio_con_mapa_s} s".format(**f))
    normales = [f for f in t13 if not f["modo"].startswith("ABUSO")]
    peor = max(normales, key=lambda f: f["dT_permanente_K"])
    for f in t13:
        if f["modo"].startswith("ABUSO") and f["pista"] == "P4":
            print(f"   {f['modo']}: ΔT permanente {f['dT_permanente_K']} K, por ronda {f['dT_ronda_3_vueltas_K']} K")
    print(f"   térmico (perfil normal): I pico {max(f['I_pico_A'] for f in normales)} A, peor ΔT permanente {peor['dT_permanente_K']} K "
          f"({peor['pista']} {peor['modo']} {peor['F_succion_N']} N), ΔT por ronda ≤ {max(f['dT_ronda_3_vueltas_K'] for f in normales)} K; diseño F={fs_diseno} N")


if __name__ == "__main__":
    main()
