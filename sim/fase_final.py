#!/usr/bin/env python3
"""Cierre de ingeniería: decisión final por simulación con el hardware DEFINITIVO del YAML v3
(PCB-chasis, arco de 16 QRE1113GR, STM32G431 con 2 ADC, encoders, rueda loca Pololu #951, LiPo Tattu 2S).

Etapas (python3 sim/fase_final.py Z E F):
  Z  cierre del motor: Pololu HPCB 12 V 15:1 (#4789), Pololu HPCB 12 V 10:1 (#3048) y Chihai N20 12 V i10, cada uno
     con el mismo ajuste robusto (búsqueda con deslizamiento ≤ 0.30 m/s, validación con 0.40 m/s), barrido de
     v_max y 200 salidas por punto.
  R  sensibilidad de esa decisión a los datos no publicados [S] (inercia del rotor, corriente de bloqueo) y a μ.
  E  fuente de curvatura del control con el motor elegido: modelo del motor (C3m) contra encoders (C3e), ambos
     ajustados sobre 8 plantas dentro de la incertidumbre de los datos [S] (J_rotor ×0.5-×2, bloqueo ±20 %) y
     elegidos por el peor tiempo esperado.
  F  validación final (200 salidas) y escenarios de robustez de la configuración elegida; escribe el YAML.
Resultados en sim/resultados/final/. Todo es SIMULADO; los datos [S] del YAML siguen sin medir."""
from __future__ import annotations

import csv
import json
import os
import re
import sys
from dataclasses import replace
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import config as CF  # noqa: E402
import experimentos as X  # noqa: E402
import fase3 as F3  # noqa: E402
import pistas as PI  # noqa: E402

SAL = os.path.join(CF.RAIZ, "sim", "resultados", "final")
F3.SAL = SAL                     # reutiliza escribir/correr_lote de la Fase 3 con otra carpeta
N_VAL = 50                       # × 4 pistas = 200 salidas

MOTORES = [("Pololu HPCB 12V 15:1 (#4789)", "pololu_hpcb12_15"),
           ("Pololu HPCB 12V 10:1 (#3048)", "pololu_hpcb12_10"),
           ("Chihai N20 12V i10", "chihai_n20_12v_2200_i10")]


def kw_base(**cambios):
    a = CF.cargar()["arquitectura"]
    kw = dict(control=a["control"], barra=a["barra"], mcu=a["mcu"], motor=a["motor"], succion=False)
    kw.update(cambios)
    return kw


def ajuste_robusto(etq, kw, pool, seed=7):
    r = X.ajustar(etq, dict(kw, desliz_valido=0.30), pool, n_azar=96, n_local=48, sem_aj=tuple(range(1, 9)), seed=seed)
    return r["prm"]


def barrido_vmax(pool, etq, kw, prm, factores=(0.90, 1.0, 1.08, 1.16)):
    filas = []
    for f in factores:
        p = dict(prm, v_max=round(prm["v_max"] * f, 4))
        filas.append(F3.correr_lote(pool, f"{etq} v_max {p['v_max']}", dict(kw, prm=p), n=N_VAL,
                                    extra=dict(v_max=p["v_max"], parametros=json.dumps(p))))
    return filas


def mejor(filas):
    return min(filas, key=lambda f: (f["E_s"], f["t_medio_s"] if f["t_medio_s"] != "" else 1e9))


def etapa_Z(pool):
    filas, elegidos = [], {}
    for etq, mot in MOTORES:
        kw = kw_base(motor=mot, control="C3m")
        prm = ajuste_robusto(etq, kw, pool)
        b = barrido_vmax(pool, etq, kw, prm)
        for f in b:
            f.update(motor=mot, masa_g=round(CF.construir(**kw).masa * 1000, 1))
        filas += b
        m = mejor(b)
        elegidos[mot] = dict(etiqueta=etq, prm=json.loads(m["parametros"]), E=m["E_s"], exito=m["exito"], t=m["t_medio_s"])
    F3.escribir("Z_motores.csv", filas)
    with open(os.path.join(SAL, "Z_parametros.json"), "w", encoding="utf-8") as fh:
        json.dump(elegidos, fh, indent=1, ensure_ascii=False)
    for mot, d in elegidos.items():
        print(f"  {d['etiqueta']:32s} mejor: E {d['E']} s, éxito {d['exito']}, t {d['t']} s")


def etapa_R(pool):
    """Sensibilidad de la decisión de motor a los datos no publicados [S] (inercia del rotor, bloqueo) y a μ:
    cada motor con SUS parámetros de la etapa Z, sin reajustar."""
    z = json.load(open(os.path.join(SAL, "Z_parametros.json"), encoding="utf-8"))
    cfg = CF.cargar()
    filas = []
    for etq, mot in MOTORES:
        kw = kw_base(motor=mot, control="C3m", prm=z[mot]["prm"])
        c0 = CF.construir(**kw)
        Jr = cfg["J_rotor"] * c0.motor.G ** 2
        Ib = cfg["motores"][mot]["I_bloqueo"]
        casos = [("nominal", {}, {}), ("J_rotor ×0.5", {"J_eq": c0.J_eq - 0.5 * Jr}, {}),
                 ("J_rotor ×2", {"J_eq": c0.J_eq + Jr}, {}), ("μ 0.70", {"mu": 0.70}, {})]
        bl = (0.3, 0.8) if cfg["motores"][mot].get("par_kgcm") is None else (0.8 * Ib, 1.2 * Ib)
        for v in bl:
            casos.append((f"I_bloqueo {v:.2f} A", {}, {"I_bloqueo": v}))
        for nom, ch, mc in casos:
            k2 = dict(kw, motor_cambios=mc) if mc else kw
            filas.append(F3.correr_lote(pool, f"{etq}: {nom}", k2, cambios_c=ch, n=30, extra=dict(motor=mot, caso=nom)))
    F3.escribir("R_sensibilidad_motores.csv", filas)


# ---- ajuste con incertidumbre: cada semilla de la búsqueda usa una planta distinta dentro del rango de los datos [S]
INCERT = [(1.0, 1.0), (0.5, 1.0), (2.0, 1.0), (1.0, 0.8), (1.0, 1.2), (0.5, 1.2), (2.0, 0.8), (0.7, 1.0)]  # (×J_rotor, ×I_bloqueo)


def correr_lote_inc(args):
    """Como experimentos.correr_lote, pero la semilla sd usa la planta INCERT[sd % 8]."""
    kw, prm, semillas = args
    cfg = CF.cargar()
    filas = []
    for sd in semillas:
        fJ, fI = INCERT[sd % len(INCERT)]
        mot = kw["motor"]
        c = CF.construir(**kw, prm=prm, motor_cambios={"I_bloqueo": cfg["motores"][mot]["I_bloqueo"] * fI})
        Jr = cfg["J_rotor"] * c.motor.G ** 2
        c = replace(c, J_eq=c.J_eq + (fJ - 1.0) * Jr)
        for pista in X.PISTAS:
            pt = X.S.perturbacion_aleatoria(np.random.default_rng(10_000 + sd))
            r = X.S.correr(c, pista, seed=sd, pt=pt)
            r["pista"] = pista.nombre.split()[0]
            r["semilla"] = sd
            filas.append(r)
    return filas


def ajustar_inc(nombre, kw, pool, seed=21, n_azar=96, n_local=48, top=5):
    """Búsqueda aleatoria + refinamiento (igual a experimentos.ajustar) evaluada sobre las 8 plantas de INCERT."""
    control = kw["control"]
    rng = np.random.default_rng(seed)
    sem_aj = tuple(range(0, 8)); sem_val = tuple(range(100, 116))
    cands = [X.muestrear(rng, control) for _ in range(n_azar)]
    cands[0] = {**dict(CF.cargar()["control"][control]), **X.FIJOS[control]}
    res = pool.map(correr_lote_inc, [(kw, p, sem_aj) for p in cands])
    puntos = sorted(((X.resumir(f)["E"], X.resumir(f)["t"], p) for f, p in zip(res, cands)), key=lambda z: (z[0], z[1]))
    for ronda in range(3):
        mejores = [z[2] for z in puntos[:4]]
        nuevos = [X.vecino(rng, mejores[i % 4], control, 1.0 / (ronda + 1)) for i in range(n_local // 3)]
        res = pool.map(correr_lote_inc, [(kw, p, sem_aj) for p in nuevos])
        puntos = sorted(puntos + [(X.resumir(f)["E"], X.resumir(f)["t"], p) for f, p in zip(res, nuevos)],
                        key=lambda z: (z[0], z[1]))
    finalistas = [z[2] for z in puntos[:top]]
    res = pool.map(correr_lote_inc, [(kw, p, sem_val) for p in finalistas])
    val = sorted(((X.resumir(f), p) for f, p in zip(res, finalistas)), key=lambda z: (z[0]["E"], z[0]["t"]))
    print(f"  {nombre}: E con incertidumbre {val[0][0]['E']:.3f} s, éxito {val[0][0]['p']:.3f}")
    return val[0][1]


def evaluar_inc(pool, etq, kw, prm, n=30):
    """200 salidas nominales + 30 × 4 pistas en cada planta extrema; devuelve filas y el peor E."""
    cfg = CF.cargar()
    mot = kw["motor"]
    filas = [F3.correr_lote(pool, f"{etq}: nominal", dict(kw, prm=prm), n=N_VAL, extra=dict(caso="nominal", parametros=json.dumps(prm)))]
    c0 = CF.construir(**kw, prm=prm)
    Jr = cfg["J_rotor"] * c0.motor.G ** 2
    Ib = cfg["motores"][mot]["I_bloqueo"]
    for nom, ch, mc in [("J_rotor ×0.5", {"J_eq": c0.J_eq - 0.5 * Jr}, {}), ("J_rotor ×2", {"J_eq": c0.J_eq + Jr}, {}),
                        ("I_bloqueo ×0.8", {}, {"I_bloqueo": 0.8 * Ib}), ("I_bloqueo ×1.2", {}, {"I_bloqueo": 1.2 * Ib}),
                        ("μ 0.70", {"mu": 0.70}, {})]:
        k2 = dict(kw, prm=prm, motor_cambios=mc) if mc else dict(kw, prm=prm)
        filas.append(F3.correr_lote(pool, f"{etq}: {nom}", k2, cambios_c=ch, n=n, extra=dict(caso=nom)))
    return filas, max(f["E_s"] for f in filas)


def etapa_E(pool):
    """Fuente de curvatura con el motor elegido (YAML): C3m (modelo del motor) contra C3e (encoders), ambos ajustados
    con la incertidumbre de los datos [S] del motor y elegidos por el PEOR tiempo esperado (nominal y plantas extremas)."""
    mot = CF.cargar()["arquitectura"]["motor"]
    filas, opciones = [], []
    for control in ("C3m", "C3e"):
        kw = kw_base(motor=mot, control=control)
        prm = ajustar_inc(control, kw, pool)
        mejor_c = None
        for f in (0.92, 1.0, 1.06):
            p = dict(prm, v_max=round(prm["v_max"] * f, 4))
            fl, peor = evaluar_inc(pool, f"{control} v_max {p['v_max']}", kw, p)
            for x in fl:
                x.update(control=control, v_max=p["v_max"], peor_E_s=peor)
            filas += fl
            if mejor_c is None or peor < mejor_c[0]:
                mejor_c = (peor, p, fl[0])
        opciones.append((mejor_c[0], control, mejor_c[1], mejor_c[2]))
    F3.escribir("E_fuente_curvatura.csv", filas)
    etapa_S(pool)


def etapa_S(pool=None):
    """Elección final entre los candidatos de la etapa E: menor tiempo esperado MEDIO sobre la planta nominal y las
    5 plantas extremas (todas igual de probables: no se sabe cuál es la real hasta medir). El peor caso se reporta."""
    import collections
    filas = list(csv.DictReader(open(os.path.join(SAL, "E_fuente_curvatura.csv"), encoding="utf-8")))
    grupos = collections.OrderedDict()
    for f in filas:
        grupos.setdefault((f["control"], f["v_max"]), []).append(f)
    tabla = []
    for (control, vmax), fs in grupos.items():
        Es = [float(f["E_s"]) for f in fs]
        nom = next(f for f in fs if f["caso"] == "nominal")
        tabla.append(dict(control=control, v_max=float(vmax), E_medio=sum(Es) / len(Es), peor_E=max(Es),
                          min_exito=min(float(f["exito"]) for f in fs), E_nominal=float(nom["E_s"]),
                          exito_nominal=float(nom["exito"]), t_nominal=float(nom["t_medio_s"]),
                          prm=json.loads(nom["parametros"])))
    tabla.sort(key=lambda z: z["E_medio"])
    for t in tabla:
        print(f"  {t['control']} v_max {t['v_max']:.4f}: E medio {t['E_medio']:.2f} s, peor {t['peor_E']:.2f} s, "
              f"éxito mínimo {t['min_exito']:.3f}, nominal {t['t_nominal']:.2f} s")
    e = tabla[0]
    seguro = min((t for t in tabla if t["min_exito"] >= 0.999), key=lambda z: z["E_medio"], default=None)
    with open(os.path.join(SAL, "E_eleccion.json"), "w", encoding="utf-8") as fh:
        json.dump(dict(motor=CF.cargar()["arquitectura"]["motor"], criterio="E medio sobre 6 plantas", control=e["control"],
                       prm=e["prm"], E_medio=e["E_medio"], peor_E=e["peor_E"], E_nominal=e["E_nominal"],
                       exito_nominal=e["exito_nominal"], t_nominal=e["t_nominal"], modo_seguro=seguro, tabla=tabla), fh, indent=1)
    print(f"  elegido: {e['control']} v_max {e['v_max']} (nominal {e['t_nominal']} s); modo seguro: "
          f"{seguro['control'] + ' v_max ' + str(seguro['v_max']) if seguro else 'ninguno'}")


def _sin_uso():
    peor, control, prm, nom = min(opciones, key=lambda z: z[0])
    with open(os.path.join(SAL, "E_eleccion.json"), "w", encoding="utf-8") as fh:
        json.dump(dict(motor=mot, control=control, prm=prm, peor_E=peor, E_nominal=nom["E_s"], exito_nominal=nom["exito"],
                       t_nominal=nom["t_medio_s"], opciones=[dict(control=o[1], peor_E=o[0], prm=o[2]) for o in opciones]),
                  fh, indent=1)
    print(f"  elegido: {control}, peor E {peor} s, nominal {nom['t_medio_s']} s ({nom['exito']})")


def escribir_yaml(control, prm, nota, cambiar_arquitectura=True):
    ruta = os.path.join(CF.RAIZ, "config", "robot_maestro.yaml")
    txt = open(ruta, encoding="utf-8").read()
    fuente = {"C3m": "modelo", "C3e": "encoder"}[control]
    linea = (f"  {control}: {{" + ", ".join(f"{k}: {round(prm[k], 4)}" for k in ("v_max", "a_lat", "a_lon", "k_pp", "kp",
             "kd", "tau_d", "tau_k")) + f", fuente_k: {fuente}, piso: {round(prm['piso'], 4)}}}   # [O] VIGENTE: {nota}")
    txt = re.sub(rf"  {control}: \{{[^\n]*", linea, txt)
    if cambiar_arquitectura:
        txt = re.sub(r"(arquitectura:[^\n]*\n(?:  [^\n]*\n)*?  control: )\S+", rf"\g<1>{control}", txt)
    open(ruta, "w", encoding="utf-8").write(txt)


def etapa_F(pool):
    e = json.load(open(os.path.join(SAL, "E_eleccion.json"), encoding="utf-8"))
    if e.get("modo_seguro"):
        escribir_yaml(e["modo_seguro"]["control"], e["modo_seguro"]["prm"], "MODO SEGURO (100 % en las 6 plantas, E_eleccion.json)",
                      cambiar_arquitectura=False)
    escribir_yaml(e["control"], e["prm"], "cierre de ingeniería, competencia (sim/resultados/final/E_eleccion.json)")
    kw = kw_base()
    c0 = CF.construir(**kw)
    filas = [F3.correr_lote(pool, "nominal", kw, n=N_VAL)]
    casos_c = [
        ("μ 0.70 (−12 %)", {"mu": 0.70}), ("μ 0.60 (−25 %)", {"mu": 0.60}),
        ("CG 10 mm más adelante", {"x_cg": c0.x_cg + 0.010}), ("CG 10 mm más atrás", {"x_cg": c0.x_cg - 0.010}),
        ("masa +10 g (batería de 37 g)", {"masa": c0.masa + 0.010, "Iz": c0.Iz * (c0.masa + 0.010) / c0.masa}),
        ("masa +40 g", {"masa": c0.masa + 0.040, "Iz": c0.Iz * (c0.masa + 0.040) / c0.masa}),
        ("sensor más alto: mancha ×1.6", {"mancha": c0.mancha * 1.6}),
        ("ruido de sensores ×2", {"ruido": c0.ruido * 2}), ("ruido de sensores ×3", {"ruido": c0.ruido * 3}),
        ("fototransistor lento: t_emisor 400 µs", {"t_lectura": c0.t_lectura + 2 * 200e-6}),
        ("encoder desconectado (CPR 0)", {"cpr_rueda": 0.0}),
    ]
    for etq, ch in casos_c:
        filas.append(F3.correr_lote(pool, etq, kw, cambios_c=ch, n=30))
    filas.append(F3.correr_lote(pool, "batería baja (6.9 V)", kw, pt_kw={"V_oc": 6.9}, n=30))
    filas.append(F3.correr_lote(pool, "latencia +1 ms", kw, pt_kw={"t_extra": 0.001}, n=30))
    filas.append(F3.correr_lote(pool, "motores desparejos ±10 %", kw, pt_kw={"f_keL": 0.90, "f_keR": 1.10}, n=30))
    mot = CF.cargar()["motores"][kw["motor"]]
    for f in (0.8, 1.2):
        filas.append(F3.correr_lote(pool, f"I de bloqueo ×{f}", dict(kw, motor_cambios={"I_bloqueo": mot["I_bloqueo"] * f}), n=30))
    F3.escribir("F_validacion_robustez.csv", filas)


def etapa_G(pool):
    """Modo seguro (C3e) revalidado con las masas y el CG del CAD; incluye el caso crítico del modo de competencia
    (CG 10 mm más adelante), para saber si el modo seguro es el respaldo correcto ante ese riesgo."""
    kw = kw_base(control="C3e")
    c0 = CF.construir(**kw)
    filas = [F3.correr_lote(pool, "C3e nominal", kw, n=N_VAL)]
    for etq, ch in [("C3e CG 5 mm más adelante", {"x_cg": c0.x_cg + 0.005}),
                    ("C3e CG 10 mm más adelante", {"x_cg": c0.x_cg + 0.010}), ("C3e μ 0.60 (−25 %)", {"mu": 0.60}),
                    ("C3e masa +10 g", {"masa": c0.masa + 0.010, "Iz": c0.Iz * (c0.masa + 0.010) / c0.masa})]:
        filas.append(F3.correr_lote(pool, etq, kw, cambios_c=ch, n=30))
    # tolerancia de CG del control de competencia (criterio de aceptación de la medición M2 del manual)
    kc = kw_base()
    for d in (0.003, 0.005, 0.007):
        filas.append(F3.correr_lote(pool, f"C3m CG {d * 1000:.0f} mm más adelante", kc, cambios_c={"x_cg": c0.x_cg + d}, n=30))
    F3.escribir("G_modo_seguro.csv", filas)


if __name__ == "__main__":
    etapas = sys.argv[1:] or ["Z", "E", "F"]
    os.makedirs(SAL, exist_ok=True)
    with Pool(int(os.environ.get("SIM_PROCESOS", os.cpu_count() or 2))) as pool:
        for et in etapas:
            print(f"Etapa {et}")
            {"Z": etapa_Z, "R": etapa_R, "E": etapa_E, "S": etapa_S, "F": etapa_F, "G": etapa_G}[et](pool)
