"""Pruebas de la planta del simulador contra soluciones analíticas. Uso: python3 sim/pruebas/test_fisica.py
Cada prueba imprime el valor simulado, el analítico y la tolerancia; termina con código 1 si alguna falla."""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config  # noqa: E402
import nucleo as N  # noqa: E402
import simulador as S  # noqa: E402
from pistas import DS, Pista  # noqa: E402

G = 9.81
FALLAS = []


def recta(largo=12.0):
    n = int(largo / DS)
    x = np.arange(n) * DS
    z = np.zeros(n)
    return Pista("recta", x, z.copy(), z.copy(), z.copy(), np.zeros(n, bool), n * DS)


def lazo_abierto(c, izq, der, t_cambio=99.0, izq2=0.0, der2=0.0, t_max=4.0, pt=S.Perturbacion()):
    P = S.vector_planta(c, pt, t_max)
    prm = np.array([izq, der, t_cambio, izq2, der2], float)
    R, T = N.simular(*(lambda p: (p.x, p.y, p.rumbo, p.hueco))(recta()), P, c.sx, c.sy,
                     N.C_LAZO_ABIERTO, prm, 0, True)
    return R, T


def revisar(nombre, sim, ref, tol_rel):
    err = abs(sim - ref) / max(abs(ref), 1e-9)
    ok = err <= tol_rel
    print(f"[{'OK ' if ok else 'MAL'}] {nombre}: simulado {sim:.4f}, referencia {ref:.4f}, error {100*err:.2f} % (tol {100*tol_rel:.1f} %)")
    if not ok:
        FALLAS.append(nombre)
    return err


def v_estacionaria(c, d=1.0):
    """Analítica: 2·Kt·(I − I0)/r = c_rr·m·g, con I = (d·Vbus − Ke·ω)/R y Vbus con caída."""
    m = c.motor
    lo, hi = 0.0, 10.0
    for _ in range(80):
        v = (lo + hi) / 2
        w = v / c.r
        # Vbus = Voc − Rint·(2·d·I + Ilog); I = (d·Vbus − Ke·w)/R  -> lineal en Vbus
        Vbus = (c.V_oc + c.R_int * 2 * d * m.Ke * w / m.R - c.R_int * c.I_log) / (1 + c.R_int * 2 * d * d / m.R)
        I = (d * Vbus - m.Ke * w) / m.R
        F = 2 * m.Kt * (I - m.I0 * math.tanh(w / 2)) / c.r
        if F > c.c_rr * c.masa * G:
            lo = v
        else:
            hi = v
    return lo


def main():
    c = config.construir()
    print(f"Configuración: {c.motor.nombre}, masa {c.masa*1000:.1f} g, x_cg {c.x_cg*1000:.1f} mm, "
          f"f_motriz {c.f_motriz:.3f}, h_cg {c.h_cg*1000:.1f} mm, dt {S.paso_integracion(c)*1e6:.0f} µs\n")

    # 1. velocidad final en recta con ciclo 1.0
    R, T = lazo_abierto(c, 1.0, 1.0, t_max=4.0)
    revisar("velocidad final en recta (ciclo 1)", T[-1, 4], v_estacionaria(c, 1.0), 0.01)
    R, T = lazo_abierto(c, 0.5, 0.5, t_max=4.0)
    revisar("velocidad final en recta (ciclo 0.5)", T[-1, 4], v_estacionaria(c, 0.5), 0.01)

    # 2. aceleración máxima: no puede superar mu·N_motriz/m con la transferencia de carga a favor
    R, T = lazo_abierto(c, 1.0, 1.0, t_max=1.0)
    v = T[:, 4]; t = T[:, 0]
    a = np.gradient(v, t)
    a_max = a[5:].max()
    # cota: N_d = m g (1 - (x_cg - a h /g)/b)
    lim = c.mu * G * (1 - (c.x_cg - a_max * c.h_cg / G) / c.x_apoyo)
    print(f"      aceleración máxima simulada {a_max:.2f} m/s² ≤ cota de agarre {lim:.2f} m/s²")
    if a_max > lim * 1.01:
        FALLAS.append("aceleración sobre el agarre")

    # 3. círculo con ciclos distintos: cinemática diferencial sin deslizamiento
    #    (v_R − v_L)/W = ω_z  y  radio del eje = v_eje/ω_z. Nota: el radio NO es el de las velocidades libres
    #    de cada motor, porque el par lateral del CG adelantado frena una rueda y carga la otra.
    R, T = lazo_abierto(c, 0.30, 0.45, t_max=6.0)
    xy = T[len(T) // 2:, 1:3]
    A = np.c_[2 * xy, np.ones(len(xy))]
    sol = np.linalg.lstsq(A, (xy ** 2).sum(1), rcond=None)[0]
    radio = math.sqrt(sol[2] + sol[0] ** 2 + sol[1] ** 2)
    vL, vR, wz = T[-1, 12], T[-1, 13], T[-1, 11]
    revisar("ω_z = (v_R − v_L)/W en régimen (deslizamiento regularizado < 5 %)", (vR - vL) / c.W, wz, 0.05)
    revisar("radio del eje = ((v_L + v_R)/2)/ω_z", radio, (vL + vR) / 2 / wz, 0.03)
    # balance de momento: ΔFx·W/2 = x_cg·m·a_lat  ->  diferencia de velocidad de rueda respecto a la libre
    a_lat = ((vL + vR) / 2) ** 2 / radio
    print(f"      círculo: radio {radio*1000:.0f} mm, a_lat {a_lat:.2f} m/s²; rueda interior arrastrada "
          f"{(vL - v_estacionaria(c, 0.30))*1000:.0f} mm/s sobre su velocidad libre (momento del CG adelantado)")

    # 4. giro forzado a alta velocidad: la aceleración lateral no supera el agarre (con transferencia)
    R, T = lazo_abierto(c, 1.0, 1.0, t_cambio=1.5, izq2=-0.3, der2=1.0, t_max=2.5)
    k = T[:, 0] > 1.5
    cx = T[k, 1] + c.x_cg * np.cos(T[k, 3]); cy = T[k, 2] + c.x_cg * np.sin(T[k, 3])
    tt = T[k, 0]
    ax = np.gradient(np.gradient(cx, tt), tt); ay = np.gradient(np.gradient(cy, tt), tt)
    a_cg = np.hypot(ax, ay)[3:-3]
    a_sat = np.percentile(a_cg, 99)
    ref = c.mu * G + c.c_rr * G      # cota absoluta: todo el peso con mu, más rodadura
    print(f"      giro forzado: |a| del CG (percentil 99) {a_sat:.2f} m/s²; cota mu·g + c_rr·g = {ref:.2f} m/s²")
    if a_sat > ref * 1.05:
        FALLAS.append("aceleración del CG sobre el agarre")

    # 5. frenado: de velocidad máxima con ciclo −1, la desaceleración media no supera el agarre
    R, T = lazo_abierto(c, 1.0, 1.0, t_cambio=2.0, izq2=-1.0, der2=-1.0, t_max=2.6)
    k = T[:, 0] > 2.0
    v = T[k, 4]; t = T[k, 0]
    j = np.argmax(v < 0.05) if (v < 0.05).any() else len(v) - 1
    dec = (v[0] - v[j]) / (t[j] - t[0])
    lim = c.mu * G * (1 - (c.x_cg + dec * c.h_cg / G) / c.x_apoyo) + c.c_rr * G
    print(f"      frenado con inverso: {dec:.2f} m/s² ≤ agarre con transferencia hacia el apoyo {lim:.2f} m/s²")
    if dec > lim * 1.03:
        FALLAS.append("frenado sobre el agarre")

    # 6. energía: lo que entrega la batería >= energía cinética + pérdidas (balance positivo)
    R, T = lazo_abierto(c, 1.0, 1.0, t_max=1.5)
    Ec = 0.5 * c.masa * T[-1, 4] ** 2 + 2 * 0.5 * c.J_eq * (T[-1, 4] / c.r) ** 2
    print(f"      energía: batería {R[10]:.3f} J ≥ cinética {Ec:.3f} J")
    if R[10] < Ec:
        FALLAS.append("balance de energía")

    # 7. regresión: con latencia de lectura ≥ periodo (ESP32 + 16 canales) la salida se aplica igual
    import pistas as PI
    for barra in ("arco16", "recta12"):
        ce = config.construir(mcu="esp32_analogread", control="C2", barra=barra)
        r, T = S.correr(ce, PI.construir("P2"), seed=1, traza=True)
        cambios = int((np.abs(np.diff(T[:, 6])) > 1e-9).sum())
        print(f"      {barra}: latencia {ce.t_lectura*1000:.2f} ms = periodo {ce.T_ctrl*1000:.2f} ms: avance "
              f"{r['avance']:.2f} m ({r['motivo']}), la salida cambió en {cambios}/{len(T)-1} ciclos")
        if r["avance"] < 1.0 or cambios < 0.5 * (len(T) - 1):
            FALLAS.append(f"salida no aplicada con latencia ≥ periodo ({barra})")

    print("\n" + ("TODAS LAS PRUEBAS DE FÍSICA PASAN" if not FALLAS else f"FALLAS: {FALLAS}"))
    sys.exit(1 if FALLAS else 0)


if __name__ == "__main__":
    main()
