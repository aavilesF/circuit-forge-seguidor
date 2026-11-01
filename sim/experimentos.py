#!/usr/bin/env python3
"""Fase 2: comparación de controles, barras de sensores, MCU, motores, cuello y succión con el simulador
dinámico. Todo lee config/robot_maestro.yaml. Resultados en sim/resultados/fase2/.

Criterio: tiempo esperado por intento E = p·t + (1 − p)·300 s, promediado en las 4 pistas
(reglamento C07: perder la línea después del primer metro registra 5 min). Cada arquitectura se ajusta
con la misma búsqueda (aleatoria + refinamiento local) y las mismas semillas, y luego se valida con
semillas nuevas.

Uso: python3 sim/experimentos.py [etapa ...]    (sin argumentos: todas)"""
from __future__ import annotations

import csv
import json
import math
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import config as CF  # noqa: E402
import pistas as PI  # noqa: E402
import simulador as S  # noqa: E402

SALIDA = os.path.join(CF.RAIZ, "sim", "resultados", "fase2")
T_FALLA = 300.0
PISTAS = PI.todas()

ESPACIO = {
    "C1": dict(b0=(0.25, 1.0), k_freno=(0.0, 0.8), e_ref=(0.01, 0.05), kp=(5.0, 80.0), kd=(0.0, 3.0),
               rueda_min=(-0.5, 0.0)),
    "SF": dict(v_max=(0.8, 3.5), a_lat=(2.0, 10.0), a_lon=(2.0, 10.0), k_pp=(0.0, 1.5), kp=(10.0, 400.0),
               kd=(0.0, 20.0), tau_k=(0.01, 0.08), piso=(-1.0, 0.0)),
}
FIJOS = {"C1": {}, "C2": {"tau_d": 0.004}, "C3m": {"tau_d": 0.004, "fuente_k": "modelo"},
         "C3g": {"tau_d": 0.004, "fuente_k": "giroscopio"}}
LOG = ("kp", "kd")   # se muestrean en escala logarítmica


def espacio(control):
    return ESPACIO["C1"] if control == "C1" else ESPACIO["SF"]


def muestrear(rng, control):
    p = {}
    for k, (lo, hi) in espacio(control).items():
        if k in LOG and lo > 0:
            p[k] = float(math.exp(rng.uniform(math.log(lo), math.log(hi))))
        elif k in LOG:
            p[k] = float(rng.uniform(lo, hi))
        else:
            p[k] = float(rng.uniform(lo, hi))
    p.update(FIJOS[control])
    if control != "C1":
        p.setdefault("tau_d", 0.004)
    return p


def vecino(rng, p, control, escala):
    q = dict(p)
    for k, (lo, hi) in espacio(control).items():
        if k in LOG and lo > 0:
            q[k] = float(np.clip(math.exp(math.log(p[k]) + rng.normal(0, 0.4 * escala)), lo, hi))
        else:
            q[k] = float(np.clip(p[k] + rng.normal(0, 0.15 * escala * (hi - lo)), lo, hi))
    return q


def correr_lote(args):
    """args = (kw de construir, prm, semillas). Devuelve una fila por (pista, semilla)."""
    kw, prm, semillas = args
    c = CF.construir(**kw, prm=prm)
    filas = []
    for pista in PISTAS:
        for sd in semillas:
            pt = S.perturbacion_aleatoria(np.random.default_rng(10_000 + sd))
            r = S.correr(c, pista, seed=sd, pt=pt)
            r["pista"] = pista.nombre.split()[0]
            r["semilla"] = sd
            filas.append(r)
    return filas


def resumir(filas):
    """p, t medio y tiempo esperado por pista; promedio de las 4 pistas."""
    por = {}
    for r in filas:
        por.setdefault(r["pista"], []).append(r)
    out = {}
    E = []
    for k, rs in por.items():
        ok = [r for r in rs if r["completa"]]
        p = len(ok) / len(rs)
        t = float(np.mean([r["t_vuelta"] for r in ok])) if ok else float("nan")
        e = (p * t + (1 - p) * T_FALLA) if ok else T_FALLA
        out[k] = dict(p=p, t=t, E=e)
        E.append(e)
    out["E"] = float(np.mean(E))
    out["p"] = float(np.mean([out[k]["p"] for k in por]))
    ts = [out[k]["t"] for k in por]
    out["t"] = float(np.mean(ts)) if all(np.isfinite(ts)) else float("nan")
    return out


def ajustar(nombre, kw, pool, n_azar=96, n_local=48, sem_aj=(1, 2, 3), sem_val=tuple(range(100, 115)),
            top=5, seed=0):
    """Búsqueda aleatoria + refinamiento local con semillas comunes; valida los mejores con semillas nuevas."""
    control = kw.get("control")
    rng = np.random.default_rng(seed)
    cands = [muestrear(rng, control) for _ in range(n_azar)]
    base = dict(CF.cargar()["control"][control])
    cands[0] = {**base, **FIJOS[control]}
    res = pool.map(correr_lote, [(kw, p, sem_aj) for p in cands])
    puntos = [(resumir(f)["E"], resumir(f)["t"], p) for f, p in zip(res, cands)]
    puntos.sort(key=lambda z: (z[0], z[1]))
    for ronda in range(3):
        mejores = [z[2] for z in puntos[:4]]
        nuevos = [vecino(rng, mejores[i % 4], control, 1.0 / (ronda + 1)) for i in range(n_local // 3)]
        res = pool.map(correr_lote, [(kw, p, sem_aj) for p in nuevos])
        puntos += [(resumir(f)["E"], resumir(f)["t"], p) for f, p in zip(res, nuevos)]
        puntos.sort(key=lambda z: (z[0], z[1]))
    finalistas = [z[2] for z in puntos[:top]]
    res = pool.map(correr_lote, [(kw, p, sem_val) for p in finalistas])
    val = sorted(((resumir(f), p, f) for f, p in zip(res, finalistas)), key=lambda z: (z[0]["E"], z[0]["t"]))
    s, p, f = val[0]
    return dict(nombre=nombre, kw=kw, prm=p, val=s, filas=f, n_eval=len(puntos))


def fila_resumen(etapa, a):
    s = a["val"]
    fila = dict(etapa=etapa, arquitectura=a["nombre"], E_s=round(s["E"], 3), exito=round(s["p"], 3),
                t_medio_s=round(s["t"], 3) if np.isfinite(s["t"]) else "")
    for k in ("P1", "P2", "P3", "P4"):
        fila[f"{k}_exito"] = round(s[k]["p"], 3)
        fila[f"{k}_t_s"] = round(s[k]["t"], 3) if np.isfinite(s[k]["t"]) else ""
    v = [r for r in a["filas"] if r["completa"]]
    fila["v_media_ms"] = round(float(np.mean([r["v_media"] for r in v])), 3) if v else ""
    fila["v_max_ms"] = round(float(np.max([r["v_max"] for r in v])), 3) if v else ""
    fila["I_max_A"] = round(float(np.max([r["I_max"] for r in a["filas"]])), 3)
    fila["T_ctrl_ms"] = round(a["filas"][0]["T_ctrl"] * 1000, 3)
    fallas = {}
    for r in a["filas"]:
        if not r["completa"]:
            fallas[r["motivo"]] = fallas.get(r["motivo"], 0) + 1
    fila["fallas"] = "; ".join(f"{k}: {v}" for k, v in fallas.items())
    fila["parametros"] = json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in a["prm"].items()},
                                    ensure_ascii=False)
    fila["n_evaluados"] = a["n_eval"]
    return fila


def escribir(nombre, filas):
    os.makedirs(SALIDA, exist_ok=True)
    claves = []
    for f in filas:
        for k in f:
            if k not in claves:
                claves.append(k)
    with open(os.path.join(SALIDA, nombre), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=claves)
        w.writeheader()
        w.writerows(filas)
    print(f"  -> sim/resultados/fase2/{nombre}")


def escribir_corridas(nombre, arqs):
    filas = []
    for a in arqs:
        for r in a["filas"]:
            filas.append(dict(arquitectura=a["nombre"], pista=r["pista"], semilla=r["semilla"],
                              completa=int(r["completa"]), motivo=r["motivo"], t_vuelta_s=round(r["t_vuelta"], 4),
                              v_media_ms=round(r["v_media"], 4), v_max_ms=round(r["v_max"], 4),
                              avance_m=round(r["avance"], 3), I_max_A=round(r["I_max"], 3),
                              mAh=round(r["mAh"], 3), V_min=round(r["V_min"], 3),
                              frac_saturado=round(r["frac_saturado"], 3), desliz_max_ms=round(r["desliz_max"], 3)))
    escribir(nombre, filas)


BASE = dict(motor="pololu_hpcb12_15", barra="arco16", mcu="stm32g431", succion=False)


def etapa_A(pool):
    """Controles con el mismo hardware."""
    arqs = []
    for ctrl in ("C1", "C2", "C3m", "C3g"):
        t0 = time.time()
        a = ajustar(ctrl, dict(BASE, control=ctrl), pool)
        arqs.append(a)
        print(f"  A {ctrl}: E {a['val']['E']:.2f} s, éxito {a['val']['p']:.2f}, t {a['val']['t']:.3f} s "
              f"({time.time()-t0:.0f} s)")
    return arqs


def etapa_B(pool, ctrl):
    """Barras de sensores × MCU (latencia) con el mejor control."""
    arqs = []
    for barra in ("recta8", "recta12", "arco13", "arco16"):
        for mcu in ("esp32_analogread", "stm32g431"):
            nombre = f"{barra} + {mcu}"
            a = ajustar(nombre, dict(BASE, control=ctrl, barra=barra, mcu=mcu), pool, n_azar=64, n_local=36)
            arqs.append(a)
            print(f"  B {nombre}: E {a['val']['E']:.2f}, éxito {a['val']['p']:.2f}, t {a['val']['t']:.3f}, "
                  f"T_ctrl {a['filas'][0]['T_ctrl']*1000:.2f} ms")
    return arqs


def etapa_C(pool, ctrl, barra, mcu):
    """Motores, sin succión y con succión (opción B)."""
    arqs = []
    for mot in ("pololu_hpcb12_10", "pololu_hpcb12_15", "pololu_hpcb6_15", "pololu_hpcb6_30"):
        for succ in (False, True):
            nombre = f"{mot} {'con' if succ else 'sin'} succión"
            a = ajustar(nombre, dict(control=ctrl, barra=barra, mcu=mcu, motor=mot, succion=succ), pool,
                        n_azar=64, n_local=36)
            arqs.append(a)
            print(f"  C {nombre}: E {a['val']['E']:.2f}, éxito {a['val']['p']:.2f}, t {a['val']['t']:.3f}, "
                  f"I_max {max(r['I_max'] for r in a['filas']):.2f} A")
    return arqs


def etapa_D(pool, kw):
    """Largo del cuello (la barra en arco tiene radio = L)."""
    arqs = []
    for L in (0.080, 0.090, 0.100, 0.110, 0.120):
        nombre = f"L = {L*1000:.0f} mm"
        a = ajustar(nombre, dict(kw, L=L), pool, n_azar=64, n_local=36)
        arqs.append(a)
        print(f"  D {nombre}: E {a['val']['E']:.2f}, éxito {a['val']['p']:.2f}, t {a['val']['t']:.3f}")
    return arqs


def etapa_F(pool):
    """Finalistas con el motor elegido por criterio técnico (12 V 15:1: 0.6 A frente a 1.5 A de los de 6 V,
    con < 2 % de diferencia de tiempo en la etapa C) y control C2: barra × MCU × cuello."""
    arqs = []
    for barra in ("recta8", "arco13", "arco16"):
        for mcu in ("esp32_analogread", "stm32g431"):
            for L in (0.100, 0.110):
                nombre = f"{barra} + {mcu} + L{L*1000:.0f}"
                kw = dict(control="C2", barra=barra, mcu=mcu, motor="pololu_hpcb12_15", succion=False, L=L)
                a = ajustar(nombre, kw, pool, n_azar=64, n_local=36)
                arqs.append(a)
                print(f"  F {nombre}: E {a['val']['E']:.2f}, éxito {a['val']['p']:.2f}, t {a['val']['t']:.3f}")
    return arqs


def mejor(arqs):
    return min(arqs, key=lambda a: (a["val"]["E"], a["val"]["t"]))


def main():
    os.makedirs(SALIDA, exist_ok=True)
    etapas = sys.argv[1:] or ["A", "B", "C", "D"]
    estado_ruta = os.path.join(SALIDA, "seleccion.json")
    sel = json.load(open(estado_ruta)) if os.path.exists(estado_ruta) else {}
    with Pool(max(1, os.cpu_count() or 1)) as pool:
        if "A" in etapas:
            print("Etapa A: controles")
            A = etapa_A(pool)
            escribir("A_controles.csv", [fila_resumen("A", a) for a in A])
            escribir_corridas("A_corridas.csv", A)
            sel["control"] = mejor(A)["kw"]["control"]
        if "B" in etapas:
            print("Etapa B: barras y MCU")
            B = etapa_B(pool, sel["control"])
            escribir("B_barras_mcu.csv", [fila_resumen("B", a) for a in B])
            escribir_corridas("B_corridas.csv", B)
            m = mejor(B)
            sel["barra"], sel["mcu"] = m["kw"]["barra"], m["kw"]["mcu"]
        if "C" in etapas:
            print("Etapa C: motores y succión")
            C = etapa_C(pool, sel["control"], sel["barra"], sel["mcu"])
            escribir("C_motores_succion.csv", [fila_resumen("C", a) for a in C])
            escribir_corridas("C_corridas.csv", C)
            sin = [a for a in C if not a["kw"]["succion"]]
            sel["motor"] = mejor(sin)["kw"]["motor"]
            sel["motor_con_succion"] = mejor([a for a in C if a["kw"]["succion"]])["kw"]["motor"]
        if "D" in etapas:
            print("Etapa D: cuello")
            kw = dict(control=sel["control"], barra=sel["barra"], mcu=sel["mcu"], motor=sel["motor"], succion=False)
            D = etapa_D(pool, kw)
            escribir("D_cuello.csv", [fila_resumen("D", a) for a in D])
            escribir_corridas("D_corridas.csv", D)
            m = mejor(D)
            sel["L"] = m["kw"]["L"]
            sel["prm"] = m["prm"]
        if "F" in etapas:
            print("Etapa F: finalistas (C2, 12 V 15:1)")
            F = etapa_F(pool)
            escribir("F_finalistas.csv", [fila_resumen("F", a) for a in F])
            escribir_corridas("F_corridas.csv", F)
            with open(os.path.join(SALIDA, "F_parametros.json"), "w") as fh:
                json.dump({a["nombre"]: dict(kw=a["kw"], prm=a["prm"]) for a in F}, fh, indent=1, ensure_ascii=False)
    with open(estado_ruta, "w") as f:
        json.dump(sel, f, indent=2, ensure_ascii=False)
    print("Selección:", json.dumps(sel, ensure_ascii=False))


if __name__ == "__main__":
    main()
