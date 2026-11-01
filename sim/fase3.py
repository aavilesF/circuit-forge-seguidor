#!/usr/bin/env python3
"""Fase 3: reingeniería con presupuesto de $2,000 MXN (sin succión).

Etapas (python3 sim/fase3.py T S M P):
  T  ajusta el control C3m para cada combinación motor × barra candidata (ESP32, L 110 mm) y la valida con
     200 salidas; compara contra la arquitectura de la Fase 2 (Pololu 12 V 15:1 + arco16c).
  S  sensibilidad del motor elegido a sus datos no publicados (I de bloqueo, eficiencia, rpm ±10 %).
  M  sensibilidad a errores de fabricación y montaje (paso de la barra, cuello, diámetro de llantas
     desigual, CG, mancha óptica / altura del sensor, giro de la barra).
  P  pruebas dirigidas: frenado en recta, pérdida de línea (hueco largo) y curva aislada.
Resultados en sim/resultados/fase3/. Todo lo que dependa de datos [S] del YAML es SIMULADO sobre supuestos."""
from __future__ import annotations

import csv
import json
import math
import os
import sys
from dataclasses import replace
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import config as CF  # noqa: E402
import experimentos as X  # noqa: E402
import pistas as PI  # noqa: E402
import simulador as S  # noqa: E402
import validacion_final as V  # noqa: E402

SAL = os.path.join(CF.RAIZ, "sim", "resultados", "fase3")
N_VAL = 50

CANDIDATOS = [
    ("Fase 2: Pololu 12V 15:1 + arco16c", "pololu_hpcb12_15", "arco16c"),
    ("GA12-N20 6V + arco16c", "ga12_n20_6v_1000", "arco16c"),
    ("Chihai 12V i10 + arco16c", "chihai_n20_12v_2200_i10", "arco16c"),
    ("Pololu 12V 15:1 + recta8 TCRT", "pololu_hpcb12_15", "recta8_tcrt"),
    ("GA12-N20 6V + recta8 TCRT", "ga12_n20_6v_1000", "recta8_tcrt"),
    ("Chihai 12V i10 + recta8 TCRT", "chihai_n20_12v_2200_i10", "recta8_tcrt"),
]


def escribir(nombre, filas):
    os.makedirs(SAL, exist_ok=True)
    claves = []
    for f in filas:
        for k in f:
            if k not in claves:
                claves.append(k)
    with open(os.path.join(SAL, nombre), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=claves)
        w.writeheader()
        w.writerows(filas)
    print(f"  -> sim/resultados/fase3/{nombre}")


def tarea(args):
    """(etiqueta, kw de construir, cambios de Config, Perturbacion extra, semilla, pista)."""
    etq, kw, cambios_c, pt_kw, sd, clave = args
    c = CF.construir(**kw)
    if cambios_c:
        c = replace(c, **cambios_c)
    rng = np.random.default_rng(70_000 + sd)
    pt = S.perturbacion_aleatoria(rng)
    if pt_kw:
        pt = S.Perturbacion(**{**pt.__dict__, **pt_kw})
    r = S.correr(c, PI.construir(clave), seed=70_000 + sd, pt=pt)
    r.update(etiqueta=etq, pista=clave, semilla=sd)
    return r


def resumen(res, etq, extra=None):
    k = sum(r["completa"] for r in res)
    ok = [r for r in res if r["completa"]]
    p = k / len(res)
    lo, hi = V.wilson(k, len(res))
    t = float(np.mean([r["t_vuelta"] for r in ok])) if ok else float("nan")
    fallas = {}
    for r in res:
        if not r["completa"]:
            fallas[r["motivo"]] = fallas.get(r["motivo"], 0) + 1
    f = dict(configuracion=etq, corridas=len(res), exito=round(p, 3), ic95_bajo=round(lo, 3), ic95_alto=round(hi, 3),
             t_medio_s=round(t, 3) if ok else "", E_s=round(p * t + (1 - p) * 300, 2) if ok else 300.0,
             v_media_ms=round(float(np.mean([r["v_media"] for r in ok])), 3) if ok else "",
             v_max_ms=round(float(np.max([r["v_max"] for r in ok])), 3) if ok else "",
             I_max_A=round(max(r["I_max"] for r in res), 3), n_ocp=sum(r["n_ocp"] for r in res),
             mAh_vuelta=round(float(np.mean([r["mAh"] for r in ok])), 3) if ok else "",
             V_min=round(min(r["V_min"] for r in res), 3),
             desliz_max_ms=round(max(r["desliz_max"] for r in res), 3),
             fallas="; ".join(f"{a}: {b}" for a, b in fallas.items()))
    for clave in PI.ORDEN:
        sub = [r for r in res if r["pista"] == clave and r["completa"]]
        f[f"{clave}_t_s"] = round(float(np.mean([r["t_vuelta"] for r in sub])), 3) if sub else ""
    if extra:
        f.update(extra)
    return f


def correr_lote(pool, etq, kw, cambios_c=None, pt_kw=None, n=N_VAL, extra=None):
    tareas = [(etq, kw, cambios_c or {}, pt_kw or {}, sd, clave) for clave in PI.ORDEN for sd in range(n)]
    res = pool.map(tarea, tareas, chunksize=20)
    f = resumen(res, etq, extra)
    print(f"  {etq:42s} éxito {f['exito']:.3f} [{f['ic95_bajo']:.3f}] t {f['t_medio_s']} s  I_max {f['I_max_A']} A  {f['fallas']}")
    return f


def etapa_T(pool):
    filas, prm_todos = [], {}
    for etq, mot, barra in CANDIDATOS:
        kw = dict(control="C3m", barra=barra, mcu="esp32_analogread", motor=mot, succion=False)
        a = X.ajustar(etq, kw, pool, n_azar=96, n_local=48, sem_aj=(1, 2, 3, 4, 5, 6), seed=3)
        prm_todos[etq] = dict(kw=kw, prm=a["prm"])
        filas.append(correr_lote(pool, etq, dict(kw, prm=a["prm"]),
                                 extra=dict(motor=mot, barra=barra, T_ctrl_ms=round(a["filas"][0]["T_ctrl"] * 1000, 2),
                                            masa_g=round(CF.construir(**kw).masa * 1000, 1),
                                            parametros=json.dumps({k: (round(v, 4) if isinstance(v, float) else v)
                                                                   for k, v in a["prm"].items()}, ensure_ascii=False))))
    escribir("T_candidatos.csv", filas)
    with open(os.path.join(SAL, "T_parametros.json"), "w", encoding="utf-8") as fh:
        json.dump(prm_todos, fh, indent=1, ensure_ascii=False)


def vigente():
    cfg = CF.cargar()
    a = cfg["arquitectura"]
    return dict(control=a["control"], barra=a["barra"], mcu=a["mcu"], motor=a["motor"], succion=False,
                prm=dict(cfg["control"][a["control"]]))


def etapa_S(pool):
    """Datos no publicados del motor vigente: el mismo control (sin reajustar) con el motor real distinto."""
    kw = vigente()
    filas = []
    casos = [("nominal", {})]
    for Ib in (0.35, 0.45, 0.8, 1.0):
        casos.append((f"I_bloqueo {Ib} A", {"I_bloqueo": Ib}))
    for eta in (0.6, 0.7, 0.85):
        casos.append((f"eficiencia {eta}", {"eta": eta}))
    cfg = CF.cargar()
    rpm0 = cfg["motores"][kw["motor"]]["rpm"]
    for f in (0.9, 1.1):
        casos.append((f"rpm {f:.0%} del nominal", {"rpm": rpm0 * f}))
    for etq, mc in casos:
        if mc and cfg["motores"][kw["motor"]].get("par_kgcm") is not None and ("eta" in mc or "I_bloqueo" in mc):
            continue
        filas.append(correr_lote(pool, etq, dict(kw, motor_cambios=mc), n=30, extra=dict(cambio=json.dumps(mc))))
    escribir("S_sensibilidad_motor.csv", filas)


def etapa_M(pool):
    """Errores de fabricación y montaje: el firmware conserva la geometría nominal; la planta cambia."""
    kw = vigente()
    c0 = CF.construir(**kw)
    filas = [correr_lote(pool, "nominal", kw, n=30)]
    casos = [
        ("barra 3 mm más adelante (L + 3 mm)", {"sx": c0.sx + 0.003}),
        ("barra 3 mm más atrás (L − 3 mm)", {"sx": c0.sx - 0.003}),
        ("barra desplazada 2 mm a la izquierda", {"sy": c0.sy + 0.002}),
        ("barra girada 3°", {"sx": c0.sx * math.cos(math.radians(3)) - c0.sy * math.sin(math.radians(3)),
                             "sy": c0.sx * math.sin(math.radians(3)) + c0.sy * math.cos(math.radians(3))}),
        ("paso de sensores +5 % (planta)", {"sy": c0.sy * 1.05}),
        ("sensor más alto: mancha ×1.6", {"mancha": c0.mancha * 1.6}),
        ("CG 10 mm más adelante", {"x_cg": c0.x_cg + 0.010}),
        ("CG 10 mm más atrás", {"x_cg": max(c0.x_cg - 0.010, 0.002)}),
        ("vía W ±3 mm (88 mm)", {"W": c0.W + 0.003}),
        ("llanta 1 mm menor (D 33 mm)", {"r": c0.r - 0.0005}),
        ("masa +40 g", {"masa": c0.masa + 0.040, "Iz": c0.Iz * (c0.masa + 0.040) / c0.masa}),
    ]
    for etq, ch in casos:
        filas.append(correr_lote(pool, etq, kw, cambios_c=ch, n=30))
    # llantas desiguales y motores desparejos: vía la constante de cada motor en la perturbación
    filas.append(correr_lote(pool, "motores desparejos ±10 % (izq rápido)", kw, pt_kw={"f_keL": 0.90, "f_keR": 1.10}, n=30))
    escribir("M_fabricacion.csv", filas)


def etapa_P(pool):
    """Pruebas dirigidas: frenado, pérdida de línea y escenarios de batería y fricción."""
    kw = vigente()
    filas = []
    for etq, pt in (("batería llena 8.4 V", {"V_oc": 8.4}), ("batería 7.4 V", {"V_oc": 7.4}),
                    ("batería baja 6.9 V", {"V_oc": 6.9}), ("μ 0.70", {"f_mu": 0.875}), ("μ 0.60", {"f_mu": 0.75}),
                    ("μ 0.90", {"f_mu": 1.125}), ("latencia +2 ms", {"t_extra": 0.002}),
                    ("ruido ×3", {"f_ruido": 3.0})):
        filas.append(correr_lote(pool, etq, kw, pt_kw=pt, n=30))
    # huecos más largos que el reglamento (5 mm): margen de recuperación ante pérdida parcial de línea
    c = CF.construir(**kw)
    for ancho in (0.005, 0.010, 0.020, 0.040):
        res = []
        for clave in PI.ORDEN:
            p = PI.construir(clave, ancho_hueco=ancho)
            for sd in range(15):
                pt = S.perturbacion_aleatoria(np.random.default_rng(90_000 + sd))
                r = S.correr(c, p, seed=90_000 + sd, pt=pt)
                r["pista"] = clave
                res.append(r)
        f = resumen(res, f"huecos de {ancho*1000:.0f} mm")
        print(f"  huecos {ancho*1000:.0f} mm: éxito {f['exito']}")
        filas.append(f)
    escribir("P_escenarios.csv", filas)
    # frenado en recta: de v_max a 0 con el ciclo mínimo permitido por el control (piso) y con inverso total
    filas2 = []
    import nucleo as N
    from verificacion_fase1 import recta
    for etq, d2 in (("freno con piso del control", c.prm.get("piso", 0.0)), ("freno corto (ciclo 0)", 0.0),
                    ("inverso total (−1)", -1.0)):
        P = S.vector_planta(c, S.Perturbacion(), 4.0)
        prm = np.array([1.0, 1.0, 1.5, d2, d2], float)
        p = recta()
        R, T = N.simular(p.x, p.y, p.rumbo, p.hueco, P, c.sx, c.sy, N.C_LAZO_ABIERTO, prm, 0, True)
        k = T[:, 0] > 1.5
        v = T[k, 4]; t = T[k, 0]
        j = int(np.argmax(v < 0.2 * v[0])) if (v < 0.2 * v[0]).any() else len(v) - 1
        dec = (v[0] - v[j]) / (t[j] - t[0])
        dist = float(np.trapezoid(v[:j + 1], t[:j + 1]))
        filas2.append(dict(modo=etq, ciclo=d2, v_inicial_ms=round(float(v[0]), 3), desaceleracion_media_ms2=round(dec, 2),
                           distancia_al_20pct_m=round(dist, 3), I_max_A=round(R[7], 3)))
        print(f"  frenado {etq}: {dec:.2f} m/s² desde {v[0]:.2f} m/s, I_max {R[7]:.2f} A")
    escribir("P_frenado.csv", filas2)


def main():
    etapas = sys.argv[1:] or ["T", "S", "M", "P"]
    os.makedirs(SAL, exist_ok=True)
    with Pool(os.cpu_count() or 1) as pool:
        if "T" in etapas:
            print("Etapa T: candidatos")
            etapa_T(pool)
        if "S" in etapas:
            print("Etapa S: sensibilidad del motor")
            etapa_S(pool)
        if "M" in etapas:
            print("Etapa M: fabricación y montaje")
            etapa_M(pool)
        if "P" in etapas:
            print("Etapa P: escenarios dirigidos")
            etapa_P(pool)


if __name__ == "__main__":
    main()
