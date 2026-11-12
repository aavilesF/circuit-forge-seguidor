#!/usr/bin/env python3
"""V2 · Fase 2 — comparación de motorreductores candidatos y límite de frecuencia del mando del ventilador.

Modelo de motor de CD lineal (par = par_bloqueo·(1 − ω/ω0) a la tensión efectiva V_ef; rpm0 y par escalan con V_ef/V_nom);
se ignoran la corriente sin carga y las pérdidas de la reductora (el resultado sobrestima el par disponible ≈ 10 %).
Frenado por inversión (−V_ef con el motor girando): par = par_bloqueo·(1 + ω/ω0), corriente = I_bloqueo·(1 + ω/ω0).
La adherencia sale del modelo de la Fase 1 (sim/v2/fase1_v2.py: 2 ruedas motrices + apoyo, transferencia de carga).

Salidas: sim/resultados/v2_fase2/T10_motores.csv, T11_frecuencia_ventilador.csv.
Uso: python3 sim/v2/fase2_motores.py"""
from __future__ import annotations

import csv
import math
import os
import sys

import yaml

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from fase1_v2 import capacidades, geo_estudio  # noqa: E402  (modelo de adherencia de la Fase 1)

RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
SAL = os.path.join(RAIZ, "sim", "resultados", "v2_fase2")
KGCM = 0.0980665  # N·m por kg·cm

with open(os.path.join(RAIZ, "config", "v2", "parametros_fase2.yaml"), encoding="utf-8") as f:
    P = yaml.safe_load(f)


def v(clave):
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
    print(f"  -> sim/resultados/v2_fase2/{nombre} ({len(filas)} filas)")


def t10_motores():
    r = v("diseno.D_llanta_m") / 2
    mu, Fs, vm, vc = v("diseno.mu"), v("diseno.succion_N"), v("diseno.v_meta_ms"), v("diseno.v_salida_curva_ms")
    g = geo_estudio(x_s=0.0)  # succión centrada sobre el eje motriz (resultado de la Fase 1)
    filas = []
    for m in v("diseno.masas_kg"):
        cap_s = capacidades(m, Fs, mu, g)
        cap_0 = capacidades(m, 0.0, mu, g)
        for c in P["motores"]:
            k = c["V_ef"] / c["V_nom"]
            rpm0, tau, Ib = c["rpm0"] * k, c["par_kgcm"] * k * KGCM, c["I_bloq"] * k
            v0 = math.pi * 2 * r * rpm0 / 60
            a_motor = lambda vel: 2 * tau * (1 - vel / v0) / r / m if vel < v0 else 0.0
            a_fren_motor = 2 * tau * (1 + vm / v0) / r / m
            I_fren = Ib * (1 + vm / v0)
            alcanza = v0 > vm
            # criterio: alcanzar 2.0 m/s con ≥ 25 % de margen de rpm, y frenar a 2.0 m/s con el motor al menos lo que la
            # adherencia con succión permite (si no, el motor y no la llanta limita el frenado)
            cumple = alcanza and vm / v0 <= 0.8 and a_fren_motor >= cap_s["ax_fr"]
            filas.append(dict(
                masa_kg=m, motor=c["nombre"], numero_parte_pololu=c["pn"], V_ef_V=c["V_ef"],
                rpm0_rueda=round(rpm0), v_sin_carga_ms=round(v0, 2), v2_sobre_v0=round(vm / v0, 2) if alcanza else "no alcanza",
                par_bloqueo_kgcm=round(tau / KGCM, 3),
                a_acel_0_ms2=round(a_motor(0), 1), a_acel_salida_curva_ms2=round(a_motor(vc), 1),
                a_acel_1p8_ms2=round(a_motor(1.8), 1),
                a_fren_inversion_2ms_ms2=round(a_fren_motor, 1), I_fren_2ms_A=round(I_fren, 2),
                adherencia_fren_con_succion_ms2=round(cap_s["ax_fr"], 1), adherencia_acel_con_succion_ms2=round(cap_s["ax_ac"], 1),
                adherencia_fren_sin_succion_ms2=round(cap_0["ax_fr"], 1),
                cumple=("sí" if cumple else "no"),
                tipo="calculado (datos del motor verificados en pololu.com; μ y succión supuestos)"))
    escribir("T10_motores.csv", filas)
    return filas


def t11_frecuencia():
    lim_t, lim_f = v("ventilador_driver.MCT8316A_fe_max_Hz"), v("ventilador_driver.MCF8316A_fe_max_Hz")
    filas = []
    for pp in v("ventilador_driver.pares_de_polos"):
        for rpm in v("ventilador_driver.rpm_requeridas"):
            fe = pp * rpm / 60
            filas.append(dict(pares_de_polos=pp, rpm=rpm, f_electrica_Hz=round(fe),
                              MCT8316A_3kHz=("sí" if fe <= lim_t else "NO"), MCF8316A_1p5kHz=("sí" if fe <= lim_f else "NO"),
                              rpm_max_MCT8316A=round(lim_t * 60 / pp), tipo="calculado (f_e = pares de polos × rpm / 60)"))
    escribir("T11_frecuencia_ventilador.csv", filas)
    return filas


def main():
    print("V2 Fase 2 — motores y mando del ventilador")
    for f in t10_motores():
        if f["masa_kg"] == 0.2:
            print(f"   {f['motor']:<34} v0 {f['v_sin_carga_ms']:>5} m/s  v/v0 {f['v2_sobre_v0']!s:>9}  "
                  f"acel salida {f['a_acel_salida_curva_ms2']:>5}  fren(2 m/s) {f['a_fren_inversion_2ms_ms2']:>5} "
                  f"(adherencia {f['adherencia_fren_con_succion_ms2']})  I {f['I_fren_2ms_A']} A  cumple {f['cumple']}")
    t11_frecuencia()


if __name__ == "__main__":
    main()
