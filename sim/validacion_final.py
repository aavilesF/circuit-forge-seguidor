#!/usr/bin/env python3
"""Validación de la arquitectura seleccionada (config/robot_maestro.yaml, sección arquitectura + control):
1) 50 salidas por pista con dispersión normal -> tasa de éxito con intervalo de Wilson al 95 %.
2) Escenarios desfavorables (avance de la auditoría de robustez): batería baja, μ bajo, latencia extra,
   ruido ×2, error de medición de batería.
3) Opción B (succión) con su propio ajuste (de etapa C), para comparar.
4) Repetibilidad del ajuste: se repite la etapa A para los dos mejores controles con otra semilla de búsqueda.
Escribe sim/resultados/fase2/E_*.csv y F*.png.

Uso: python3 sim/validacion_final.py"""
from __future__ import annotations

import csv
import json
import math
import os
import sys
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import config as CF  # noqa: E402
import experimentos as X  # noqa: E402
import pistas as PI  # noqa: E402
import simulador as S  # noqa: E402

SAL = X.SALIDA
N_SEM = 50


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def tarea(args):
    nombre, kw, pt_kw, sd, clave = args
    c = CF.construir(**kw)
    rng = np.random.default_rng(50_000 + sd)
    pt = S.perturbacion_aleatoria(rng)
    if pt_kw:
        pt = S.Perturbacion(**{**pt.__dict__, **pt_kw})
    r = S.correr(c, PI.construir(clave), seed=50_000 + sd, pt=pt)
    r.update(escenario=nombre, pista=clave, semilla=sd)
    return r


ESCENARIOS = [
    ("nominal", {}),
    ("batería baja 6.9 V", {"V_oc": 6.9}),
    ("μ −25 %", {"f_mu": 0.75}),
    ("latencia +1 ms", {"t_extra": 0.001}),
    ("ruido de sensores ×2", {"f_ruido": 2.0}),
    ("medición de batería +5 %", {"f_vmed": 1.05}),
]


def resumen(filas, etiqueta):
    out = []
    for esc in dict.fromkeys(r["escenario"] for r in filas):
        rs = [r for r in filas if r["escenario"] == esc]
        for clave in PI.ORDEN + ("todas",):
            sub = rs if clave == "todas" else [r for r in rs if r["pista"] == clave]
            k = sum(r["completa"] for r in sub)
            lo, hi = wilson(k, len(sub))
            ok = [r for r in sub if r["completa"]]
            fallas = {}
            for r in sub:
                if not r["completa"]:
                    fallas[r["motivo"]] = fallas.get(r["motivo"], 0) + 1
            t = float(np.mean([r["t_vuelta"] for r in ok])) if ok else float("nan")
            p = k / len(sub)
            out.append(dict(configuracion=etiqueta, escenario=esc, pista=clave, corridas=len(sub), completas=k,
                            exito=round(p, 3), ic95_bajo=round(lo, 3), ic95_alto=round(hi, 3),
                            t_medio_s=round(t, 3) if ok else "",
                            t_p95_s=round(float(np.percentile([r["t_vuelta"] for r in ok], 95)), 3) if ok else "",
                            v_media_ms=round(float(np.mean([r["v_media"] for r in ok])), 3) if ok else "",
                            E_s=round(p * t + (1 - p) * 300, 2) if ok else 300.0,
                            I_max_A=round(max(r["I_max"] for r in sub), 3),
                            mAh_vuelta=round(float(np.mean([r["mAh"] for r in ok])), 3) if ok else "",
                            V_min=round(min(r["V_min"] for r in sub), 3),
                            fallas="; ".join(f"{a}: {b}" for a, b in fallas.items())))
    return out


def graficas(kw, etiqueta):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    cols = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.grid": True, "grid.color": "#e6e5e1", "grid.linewidth": 0.6,
                         "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb"})
    c = CF.construir(**kw)
    fig, axs = plt.subplots(2, 2, figsize=(11, 6.2))
    for ax, clave, col in zip(axs.flat, PI.ORDEN, cols):
        p = PI.construir(clave)
        r, T = S.correr(c, p, seed=7, traza=True)
        ax.plot(p.x, p.y, color="#c3c2b7", lw=1.2, zorder=1)
        sc = ax.scatter(T[:, 1], T[:, 2], c=T[:, 4], s=3, cmap="viridis", vmin=0, vmax=1.4, zorder=3)
        ax.set_aspect("equal")
        ax.set_title(f"{p.nombre}: {r['t_vuelta']:.2f} s, media {r['v_media']:.2f} m/s", fontsize=9, loc="left")
        ax.set_xticks([]); ax.set_yticks([])
    fig.colorbar(sc, ax=axs, shrink=0.8, label="velocidad del eje (m/s)")
    fig.suptitle(f"Trayectoria del eje (color = velocidad) y línea de la pista (gris) — {etiqueta}", x=0.01, ha="left")
    fig.savefig(os.path.join(SAL, "F5_trayectorias.png"), dpi=130, bbox_inches="tight")
    plt.close(fig)

    p = PI.construir("P4")
    r, T = S.correr(c, p, seed=7, traza=True)
    fig, ax = plt.subplots(3, 1, figsize=(9, 6.5), sharex=True)
    ax[0].plot(T[:, 10], T[:, 4], color=cols[0], lw=1.6, label="velocidad real")
    ax[0].plot(T[:, 10], T[:, 8], color=cols[1], lw=1.2, label="velocidad pedida (v_cmd)")
    ax[0].set_ylabel("m/s"); ax[0].legend(frameon=False, fontsize=8)
    ax[1].plot(T[:, 10], T[:, 5] * 1000, color=cols[2], lw=1.2)
    ax[1].set_ylabel("error e (mm)")
    ax[2].plot(T[:, 10], T[:, 6], color=cols[0], lw=1.0, label="ciclo izquierdo")
    ax[2].plot(T[:, 10], T[:, 7], color=cols[1], lw=1.0, label="ciclo derecho")
    ax[2].set_ylabel("ciclo PWM"); ax[2].set_xlabel("avance sobre la pista (m)")
    ax[2].legend(frameon=False, fontsize=8)
    ax[0].set_title(f"P4 exigente R150 — {etiqueta}: {r['t_vuelta']:.2f} s", loc="left")
    fig.tight_layout()
    fig.savefig(os.path.join(SAL, "F6_senales_P4.png"), dpi=130)
    plt.close(fig)


def graficas_comparacion():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    cols = ["#2a78d6", "#eb6834"]

    def leer(n):
        return list(csv.DictReader(open(os.path.join(SAL, n), encoding="utf-8")))
    fig, axs = plt.subplots(1, 3, figsize=(13, 3.8))
    for ax, (n, tit) in zip(axs, (("A_controles.csv", "Controles (12 V 15:1, arco16, STM32)"),
                                  ("B_barras_mcu.csv", "Barras de sensores × MCU"),
                                  ("C_motores_succion.csv", "Motores, sin y con succión"))):
        f = leer(n)
        y = np.arange(len(f))
        t = [float(r["t_medio_s"]) if r["t_medio_s"] else np.nan for r in f]
        e = [float(r["exito"]) for r in f]
        colores = [cols[1] if ("con succión" in r["arquitectura"]) else cols[0] for r in f]
        ax.barh(y, t, color=colores, height=0.6)
        for i, (ti, ei) in enumerate(zip(t, e)):
            if np.isfinite(ti):
                ax.text(ti + 0.03, i, f"{ti:.2f} s · {100*ei:.0f} %", va="center", fontsize=7.5)
        ax.set_yticks(y, [r["arquitectura"].replace("pololu_hpcb", "").replace("_analogread", "") for r in f], fontsize=8)
        ax.invert_yaxis()
        ax.set_xlabel("tiempo medio de vuelta en las 4 pistas (s)")
        ax.set_xlim(0, max(np.nanmax(t) * 1.3, 1))
        ax.set_title(tit, loc="left", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(SAL, "F7_comparacion.png"), dpi=130)
    plt.close(fig)
    f = leer("D_cuello.csv")
    fig, ax = plt.subplots(figsize=(6, 3.4))
    L = [float(r["arquitectura"].split("=")[1].split()[0]) for r in f]
    ax.plot(L, [float(r["t_medio_s"]) if r["t_medio_s"] else np.nan for r in f], marker="o", color=cols[0], lw=2)
    for li, r in zip(L, f):
        ax.annotate(f"{100*float(r['exito']):.0f} %", (li, float(r["t_medio_s"]) if r["t_medio_s"] else 0),
                    textcoords="offset points", xytext=(0, 6), ha="center", fontsize=8)
    ax.set_xlabel("largo del cuello L (mm)"); ax.set_ylabel("tiempo medio de vuelta (s)")
    ax.set_title("Cuello: simulación dinámica (etiqueta = tasa de éxito)", loc="left", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(SAL, "F8_cuello_dinamico.png"), dpi=130)
    plt.close(fig)


def main():
    cfg = CF.cargar()
    arq = cfg["arquitectura"]
    kw = dict(motor=arq["motor"], barra=arq["barra"], mcu=arq["mcu"], control=arq["control"], succion=False)
    etiqueta = f"{arq['control']}, {arq['barra']}, {arq['mcu']}, {CF.motor(cfg, arq['motor']).nombre}, L {cfg['geometria']['L_cuello']*1000:.0f} mm"
    sel = json.load(open(os.path.join(SAL, "seleccion.json")))
    tareas = []
    for nombre, pt in ESCENARIOS:
        for clave in PI.ORDEN:
            for sd in range(N_SEM):
                tareas.append((nombre, kw, pt, sd, clave))
    # opción B: succión con su motor y sus parámetros de la etapa C
    filasC = list(csv.DictReader(open(os.path.join(SAL, "C_motores_succion.csv"), encoding="utf-8")))
    # opción B: solo motores cuya corriente pico no dispara la protección del driver (OCP ≥ 2 A)
    con = [r for r in filasC if "con succión" in r["arquitectura"] and float(r["I_max_A"]) < 2.0]
    mejorB = min(con, key=lambda r: float(r["E_s"]))
    motB = mejorB["arquitectura"].split()[0]
    kwB = dict(kw, motor=motB, succion=True, prm=json.loads(mejorB["parametros"]))
    for clave in PI.ORDEN:
        for sd in range(N_SEM):
            tareas.append(("nominal", kwB, {}, sd, clave))
    with Pool(os.cpu_count() or 1) as pool:
        res = pool.map(tarea, tareas, chunksize=20)
    base = [r for r, t in zip(res, tareas) if not t[1].get("succion")]
    opB = [r for r, t in zip(res, tareas) if t[1].get("succion")]
    filas = resumen(base, f"vigente: {etiqueta}") + resumen(opB, f"opción B con succión: {motB}")
    X.escribir("E_validacion.csv", filas)
    for f in filas:
        if f["pista"] == "todas":
            print(f"{f['configuracion'][:40]:40s} {f['escenario']:28s} éxito {f['exito']:.3f} "
                  f"[{f['ic95_bajo']:.3f}-{f['ic95_alto']:.3f}] t {f['t_medio_s']} s  E {f['E_s']}  {f['fallas']}")
    # repetibilidad del ajuste (etapa A con otra semilla de búsqueda)
    filasA = list(csv.DictReader(open(os.path.join(SAL, "A_controles.csv"), encoding="utf-8")))
    top2 = sorted(filasA, key=lambda r: float(r["E_s"]))[:2]
    rep = []
    with Pool(os.cpu_count() or 1) as pool:
        for r in top2:
            ctrl = r["arquitectura"]
            for semilla in (1, 2):
                a = X.ajustar(ctrl, dict(X.BASE, control=ctrl), pool, seed=semilla)
                rep.append(dict(control=ctrl, semilla_busqueda=semilla, E_s=round(a["val"]["E"], 3),
                                exito=round(a["val"]["p"], 3), t_medio_s=round(a["val"]["t"], 3),
                                E_s_semilla0=r["E_s"]))
                print(f"repetibilidad {ctrl} semilla {semilla}: E {a['val']['E']:.3f} (semilla 0: {r['E_s']})")
    X.escribir("E_repetibilidad_ajuste.csv", rep)
    graficas(dict(kw), etiqueta)
    graficas_comparacion()
    print("gráficas F5-F8 escritas")


if __name__ == "__main__" and not ({"perfiles", "cara", "desempate", "mu"} & set(sys.argv)):
    main()


def perfiles_por_radio():
    """Si el equipo ve la pista antes del intento (se entrega el mismo día), puede elegir v_max según el radio
    mínimo visible. Se barre v_max con los demás parámetros fijos, solo en la pista cuyo radio mínimo coincide."""
    cfg = CF.cargar()
    arq = cfg["arquitectura"]
    kw = dict(motor=arq["motor"], barra=arq["barra"], mcu=arq["mcu"], control=arq["control"], succion=False)
    base = dict(cfg["control"][arq["control"]])
    filas = []
    with Pool(os.cpu_count() or 1) as pool:
        for clave, rmin in (("P4", 0.15), ("P3", 0.20), ("P2", 0.40)):
            for vmax in (0.8, 0.9, 1.0, 1.1, 1.2, 1.3):
                prm = dict(base, v_max=vmax)
                tareas = [("perfil", dict(kw, prm=prm), {}, sd, clave) for sd in range(30)]
                res = pool.map(tarea, tareas, chunksize=10)
                k = sum(r["completa"] for r in res)
                ok = [r for r in res if r["completa"]]
                t = float(np.mean([r["t_vuelta"] for r in ok])) if ok else float("nan")
                p = k / len(res)
                lo, hi = wilson(k, len(res))
                filas.append(dict(pista=clave, radio_min_m=rmin, v_max=vmax, exito=round(p, 3), ic95_bajo=round(lo, 3),
                                  t_medio_s=round(t, 3) if ok else "", E_s=round(p * t + (1 - p) * 300, 2) if ok else 300))
                print(f"perfil {clave} R{rmin} v_max {vmax}: éxito {p:.2f}, t {t:.3f}")
    X.escribir("E_perfil_por_radio.csv", filas)


if __name__ == "__main__" and "perfiles" in sys.argv:
    perfiles_por_radio()


def kw_de_fila(archivo, nombre):
    """Reconstruye la configuración y los parámetros ajustados de una arquitectura de las etapas A-D."""
    if archivo.startswith("F_"):
        d = json.load(open(os.path.join(SAL, "F_parametros.json"), encoding="utf-8"))[nombre]
        return dict(d["kw"], prm=d["prm"])
    sel = json.load(open(os.path.join(SAL, "seleccion.json")))
    fila = [r for r in csv.DictReader(open(os.path.join(SAL, archivo), encoding="utf-8")) if r["arquitectura"] == nombre][0]
    prm = json.loads(fila["parametros"])
    if archivo.startswith("A_"):
        kw = dict(X.BASE, control=nombre)
    elif archivo.startswith("B_"):
        barra, mcu = nombre.split(" + ")
        kw = dict(X.BASE, control=sel["control"], barra=barra, mcu=mcu)
    elif archivo.startswith("C_"):
        mot, succ = nombre.split()[0], nombre.split()[1]
        kw = dict(control=sel["control"], barra=sel["barra"], mcu=sel["mcu"], motor=mot, succion=(succ == "con"),
                  L=0.100)   # la etapa C corrió con L = 100 mm
    else:
        L = float(nombre.split("=")[1].split()[0]) / 1000
        kw = dict(control=sel["control"], barra=sel["barra"], mcu=sel["mcu"], motor=sel["motor"], succion=False, L=L)
    return dict(kw, prm=prm)


def cara_a_cara(finalistas, n=N_SEM):
    """Cada finalista con SUS parámetros ajustados, 50 salidas nuevas por pista (semillas 50 000+)."""
    filas = []
    with Pool(os.cpu_count() or 1) as pool:
        for etiqueta, archivo, nombre in finalistas:
            kw = kw_de_fila(archivo, nombre)
            tareas = [("nominal", kw, {}, sd, clave) for clave in PI.ORDEN for sd in range(n)]
            res = pool.map(tarea, tareas, chunksize=20)
            f = [x for x in resumen(res, etiqueta) if x["pista"] == "todas"][0]
            filas.append(f)
            print(f"cara a cara {etiqueta:38s} éxito {f['exito']:.3f} [{f['ic95_bajo']:.3f}-{f['ic95_alto']:.3f}] "
                  f"t {f['t_medio_s']} s E {f['E_s']} {f['fallas']}")
    X.escribir("E_cara_a_cara.csv", filas)
    return filas


if __name__ == "__main__" and "cara" in sys.argv:
    filasF = sorted(csv.DictReader(open(os.path.join(SAL, "F_finalistas.csv"), encoding="utf-8")),
                    key=lambda r: (float(r["E_s"]), float(r["t_medio_s"] or 99)))
    finalistas = [(f"F {r['arquitectura']}", "F_finalistas.csv", r["arquitectura"]) for r in filasF[:5]]
    filasC = list(csv.DictReader(open(os.path.join(SAL, "C_motores_succion.csv"), encoding="utf-8")))
    conB = min([r for r in filasC if "con succión" in r["arquitectura"] and float(r["I_max_A"]) < 2.0],
               key=lambda r: float(r["E_s"]))
    finalistas.append((f"C {conB['arquitectura']} (opción B)", "C_motores_succion.csv", conB["arquitectura"]))
    cara_a_cara(finalistas)


def desempate(finalistas, n=30):
    """Escenarios desfavorables para los finalistas empatados en condiciones nominales."""
    filas = []
    with Pool(os.cpu_count() or 1) as pool:
        for etiqueta, archivo, nombre in finalistas:
            kw = kw_de_fila(archivo, nombre)
            tareas = [(esc, kw, pt, sd, clave) for esc, pt in ESCENARIOS[1:] for clave in PI.ORDEN for sd in range(n)]
            res = pool.map(tarea, tareas, chunksize=20)
            for f in resumen(res, etiqueta):
                if f["pista"] == "todas":
                    filas.append(f)
                    print(f"desempate {etiqueta:34s} {f['escenario']:26s} éxito {f['exito']:.3f} t {f['t_medio_s']} {f['fallas']}")
    X.escribir("E_desempate_robustez.csv", filas)


if __name__ == "__main__" and "desempate" in sys.argv:
    desempate([("recta8 + ESP32 + L110", "F_finalistas.csv", "recta8 + esp32_analogread + L110"),
               ("arco16 + ESP32 + L110", "F_finalistas.csv", "arco16 + esp32_analogread + L110"),
               ("arco13 + ESP32 + L100", "F_finalistas.csv", "arco13 + esp32_analogread + L100"),
               ("arco13 + STM32 + L110", "F_finalistas.csv", "arco13 + stm32g431 + L110")])


def perfil_por_mu(n=30):
    """Con los parámetros vigentes (YAML), ¿qué v_max (y a_lat proporcional) recupera el 100 % si μ es menor?"""
    cfg = CF.cargar(); arq = cfg["arquitectura"]
    base = dict(motor=arq["motor"], barra=arq["barra"], mcu=arq["mcu"], control=arq["control"], succion=False,
                prm=dict(cfg["control"][arq["control"]]))
    filas = []
    with Pool(os.cpu_count() or 1) as pool:
        for f_mu in (1.0, 0.875, 0.75, 0.625):
            for esc in (1.0, 0.95, 0.9, 0.85, 0.8):
                prm = dict(base["prm"], v_max=base["prm"]["v_max"] * esc, a_lat=base["prm"]["a_lat"] * f_mu)
                kw = dict(base, prm=prm)
                tareas = [("mu", kw, {"f_mu": f_mu}, sd, clave) for clave in PI.ORDEN for sd in range(n)]
                res = pool.map(tarea, tareas, chunksize=20)
                k = sum(r["completa"] for r in res)
                ok = [r for r in res if r["completa"]]
                t = float(np.mean([r["t_vuelta"] for r in ok])) if ok else float("nan")
                p = k / len(res)
                lo, hi = wilson(k, len(res))
                filas.append(dict(mu=round(0.8 * f_mu, 3), v_max=round(prm["v_max"], 3), a_lat=round(prm["a_lat"], 2),
                                  exito=round(p, 3), ic95_bajo=round(lo, 3), t_medio_s=round(t, 3) if ok else "",
                                  E_s=round(p * t + (1 - p) * 300, 2) if ok else 300))
                print(f"μ {0.8*f_mu:.2f} v_max {prm['v_max']:.3f}: éxito {p:.3f} t {t:.3f}")
    X.escribir("E_perfil_por_mu.csv", filas)


if __name__ == "__main__" and "mu" in sys.argv:
    perfil_por_mu()
