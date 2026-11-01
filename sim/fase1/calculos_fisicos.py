#!/usr/bin/env python3
"""Fase 1 - cálculos físicos del Speed Follower.

Lee sim/fase1/robot_maestro_v1.yaml (copia congelada de la configuración v1, commit 0143148) y escribe
CSV y gráficas en sim/resultados/fase1/. Es evidencia histórica: la configuración vigente es config/robot_maestro.yaml
y la verificación de estos cálculos está en sim/verificacion_fase1.py.
Todo lo que sale de aquí es CALCULADO a partir de la configuración: no es una
medición. Los supuestos están marcados en el YAML.

Uso:  python3 sim/fase1/calculos_fisicos.py
"""
from __future__ import annotations

import csv
import math
import os
from dataclasses import dataclass, replace

import numpy as np
import yaml

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SALIDA = os.path.join(RAIZ, "sim", "resultados", "fase1")
G = 9.81
KGCM = 0.0980665  # N·m por kg·cm


def cargar():
    with open(os.path.join(os.path.dirname(__file__), "robot_maestro_v1.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


CFG = cargar()


# ----------------------------------------------------------------- motor
@dataclass(frozen=True)
class Motor:
    nombre: str
    V_nom: float
    rpm: float
    T_bl: float  # N·m
    I_bl: float
    I0: float
    masa: float
    limite_V: float | None

    @property
    def w0(self):
        return self.rpm * 2 * math.pi / 60

    @property
    def R(self):
        return self.V_nom / self.I_bl

    @property
    def Ke(self):
        return (self.V_nom - self.I0 * self.R) / self.w0

    @property
    def Kt(self):
        return self.T_bl / (self.I_bl - self.I0)


def motor(clave):
    m = CFG["motores"][clave]
    return Motor(m["nombre"], m["V_nom"], m["rpm"], m["par_kgcm"] * KGCM, m["I_bloqueo"],
                 m["I_vacio"], m["masa"], m["limite_V"])


# ----------------------------------------------------------------- robot
@dataclass(frozen=True)
class Robot:
    motor: Motor
    masa: float
    L: float
    W: float
    D: float
    mu: float
    f_motriz: float
    c_rr: float
    Fd: float          # N, succión
    f_down: float
    V_oc: float
    R_int: float
    I_log: float
    I_lim: float       # A por motor en frenado inverso (driver)

    @property
    def r(self):
        return self.D / 2

    @property
    def N_motriz(self):
        return self.f_motriz * self.masa * G + self.f_down * self.Fd

    @property
    def a_max(self):
        """Aceleración total máxima (círculo de fricción de las ruedas motrices)."""
        return self.mu * self.N_motriz / self.masa


def masa_base():
    return sum(CFG["masa"].values())


def robot_base(**cambios):
    c = CFG
    m = motor(c["motor_base"])
    succ = c["succion"]
    Fd = succ["F_down_gf"] / 1000 * G
    masa = masa_base() + (succ["masa_extra"] if Fd > 0 else 0.0)
    r = Robot(motor=m, masa=masa, L=c["geometria"]["L_cuello"], W=c["geometria"]["W_via"],
              D=c["geometria"]["D_llanta"], mu=c["traccion"]["mu"],
              f_motriz=c["traccion"]["f_motriz"], c_rr=c["traccion"]["c_rodadura"],
              Fd=Fd, f_down=succ["f_down_motriz"], V_oc=c["bateria"]["V_nominal"],
              R_int=c["bateria"]["R_interna"], I_log=c["bateria"]["I_logica"],
              I_lim=c["conductor"]["I_pico"])
    return replace(r, **cambios)


def fuerza_motriz(rb: Robot, v):
    """Fuerza de tracción total (2 motores, PWM al 100 %) a velocidad v, con caída de batería."""
    m = rb.motor
    w = max(v, 0.0) / rb.r
    # V_bus = V_oc - R_int (2 I + I_log),  I = (V_app - Ke w)/R
    Vbus = (rb.V_oc + 2 * rb.R_int * m.Ke * w / m.R - rb.R_int * rb.I_log) / (1 + 2 * rb.R_int / m.R)
    Vapp = Vbus if m.limite_V is None else min(Vbus, m.limite_V)
    if m.limite_V is not None and Vapp < Vbus:
        Vbus = rb.V_oc - rb.R_int * (2 * max((Vapp - m.Ke * w) / m.R, 0) + rb.I_log)
    I = (Vapp - m.Ke * w) / m.R
    T = m.Kt * (I - m.I0)
    return 2 * T / rb.r, I, Vbus


def fuerza_frenado(rb: Robot, v, modo="inverso"):
    m = rb.motor
    w = max(v, 0.0) / rb.r
    if modo == "inverso":
        Vapp = rb.V_oc if m.limite_V is None else min(rb.V_oc, m.limite_V)
        I = min((Vapp + m.Ke * w) / m.R, rb.I_lim)
    elif modo == "corto":
        I = m.Ke * w / m.R
    else:  # libre
        I = 0.0
    T = m.Kt * I + m.Kt * m.I0  # la fricción interna también frena
    return 2 * T / rb.r


def v_libre(rb: Robot):
    lo, hi = 0.0, 10.0
    for _ in range(60):
        mid = (lo + hi) / 2
        F, _, _ = fuerza_motriz(rb, mid)
        if F - rb.c_rr * rb.masa * G > 0:
            lo = mid
        else:
            hi = mid
    return lo


# ----------------------------------------------------------------- pistas
@dataclass(frozen=True)
class Pista:
    nombre: str
    segs: tuple  # ("S", largo) o ("A", R, grados con signo: + izquierda)


def chicana(R, th, signo=-1):
    """Chicana de un solo lado: th, -2th, th. signo -1 = abulta a la derecha."""
    return (("A", R, signo * th), ("A", R, -2 * signo * th), ("A", R, signo * th))


def pistas():
    c40_20 = chicana(0.20, 40)
    x_c20 = 4 * 0.20 * math.sin(math.radians(40))
    c40_15 = chicana(0.15, 40)
    x_c15 = 4 * 0.15 * math.sin(math.radians(40))
    p3_inf = 0.30 + x_c20 + 0.30
    return [
        Pista("P1 óvalo R150", (("S", 1.60), ("A", 0.15, 180), ("S", 1.60), ("A", 0.15, 180))),
        Pista("P2 óvalo R400", (("S", 1.20), ("A", 0.40, 180), ("S", 1.20), ("A", 0.40, 180))),
        Pista("P3 S y cambios de radio", (("S", 0.30), *c40_20, ("S", 0.30), ("A", 0.20, 90),
                                          ("S", 0.30), ("A", 0.20, 90), ("S", p3_inf), ("A", 0.35, 180))),
        Pista("P4 exigente R150", (("S", 0.40), *c40_15, ("S", 0.50), ("A", 0.15, 180),
                                   ("S", 0.40), *c40_15, ("S", 0.50), ("A", 0.15, 180))),
    ]


def trazar(p: Pista, ds=0.002):
    x = y = h = 0.0
    pts = [(x, y)]
    for s in p.segs:
        if s[0] == "S":
            n = max(int(s[1] / ds), 1)
            for _ in range(n):
                x += s[1] / n * math.cos(h)
                y += s[1] / n * math.sin(h)
                pts.append((x, y))
        else:
            R, th = s[1], math.radians(s[2])
            n = max(int(abs(th) * R / ds), 1)
            for _ in range(n):
                dh = th / n
                x += 2 * R * math.sin(abs(dh) / 2) * math.cos(h + dh / 2)
                y += 2 * R * math.sin(abs(dh) / 2) * math.sin(h + dh / 2)
                h += dh
                pts.append((x, y))
    return np.array(pts), h


def largo_linea(p: Pista):
    return sum(s[1] if s[0] == "S" else s[1] * math.radians(abs(s[2])) for s in p.segs)


def validar_pista(p: Pista):
    reg = CFG["reglamento"]
    pts, h = trazar(p)
    cierre = float(np.hypot(*(pts[-1] - pts[0])))
    giro = math.degrees(h)
    ext = pts.max(0) - pts.min(0)
    cabe = ext[0] <= reg["tablero"][0] - 0.12 and ext[1] <= reg["tablero"][1] - 0.12
    # separación: puntos alejados más de 0.6 m sobre la línea deben distar >= 0.20 m
    sub = pts[::10]
    s = np.arange(len(sub)) * 0.02
    Ltot = largo_linea(p)
    d = np.hypot(sub[:, None, 0] - sub[None, :, 0], sub[:, None, 1] - sub[None, :, 1])
    ds_ = np.abs(s[:, None] - s[None, :])
    ds_ = np.minimum(ds_, Ltot - ds_)
    mask = ds_ > 0.6
    sep = float(d[mask].min()) if mask.any() else float("inf")
    rmin = min(s_[1] for s_ in p.segs if s_[0] == "A")
    amax = max(abs(s_[2]) for s_ in p.segs if s_[0] == "A")
    return dict(pista=p.nombre, largo_linea_m=round(Ltot, 3), cierre_mm=round(cierre * 1000, 2),
                giro_total_grados=round(giro, 1), extension_x_m=round(ext[0], 3),
                extension_y_m=round(ext[1], 3), cabe_en_tablero=cabe,
                separacion_min_m=round(sep, 3), radio_min_m=rmin, arco_max_grados=amax,
                cumple=bool(cierre < 0.005 and cabe and sep >= reg["separacion_min"] - 1e-3
                            and rmin > reg["radio_min_linea"] - 1e-9))


# ----------------------------------------------------------------- vuelta cuasiestática
def radio_eje(R, L):
    return math.sqrt(R * R - L * L) if R > L else float("nan")


def perfil(rb: Robot, p: Pista, ds=0.001):
    """Velocidad máxima del EJE sobre su trayectoria (seguimiento perfecto, sin control)."""
    kap, sl = [], []  # curvatura del eje por tramo
    for s in p.segs:
        if s[0] == "S":
            n = int(round(s[1] / ds))
            kap += [0.0] * n
        else:
            Ra = radio_eje(s[1], rb.L)
            if math.isnan(Ra):
                return None
            n = int(round(math.radians(abs(s[2])) * Ra / ds))
            kap += [1.0 / Ra] * n
    kap = np.array(kap)
    n = len(kap)
    amax = rb.a_max
    vl = v_libre(rb)
    vcap = np.full(n, vl)
    curva = kap > 0
    Ra = np.where(curva, 1 / np.maximum(kap, 1e-9), np.inf)
    vcap[curva] = np.minimum(np.sqrt(amax * Ra[curva]),
                             vl / (1 + rb.W / 2 * kap[curva]))  # rueda exterior <= v libre
    # pasada hacia atrás (frenado), cíclica para que la meta no imponga detenerse
    vb = vcap.copy()
    for _ in range(2):
        for i in range(n - 1, -1, -1):
            j = (i + 1) % n
            alat = vb[j] ** 2 * kap[i]
            alon = math.sqrt(max(amax ** 2 - alat ** 2, 0))
            dec = min(fuerza_frenado(rb, vb[j]) / rb.masa, alon) + rb.c_rr * G
            vb[i] = min(vb[i], math.sqrt(vb[j] ** 2 + 2 * dec * ds))
    # pasada hacia adelante desde parado
    v = np.zeros(n + 1)
    for i in range(n):
        alat = v[i] ** 2 * kap[i]
        alon = math.sqrt(max(amax ** 2 - alat ** 2, 0))
        F, _, _ = fuerza_motriz(rb, v[i])
        acc = min(F / rb.masa, alon) - rb.c_rr * G
        v[i + 1] = min(math.sqrt(max(v[i] ** 2 + 2 * acc * ds, 0)), vb[i])
    vm = np.maximum((v[1:] + v[:-1]) / 2, 1e-4)
    t = float(np.sum(ds / vm))
    return dict(t=t, v=v, kap=kap, vmax=float(v.max()), ds=ds)


def vuelta(rb, p):
    r = perfil(rb, p)
    if r is None:
        return dict(t_vuelta_s=float("nan"), v_media_linea_ms=float("nan"), v_max_ms=float("nan"))
    return dict(t_vuelta_s=round(r["t"], 4), v_media_linea_ms=round(largo_linea(p) / r["t"], 4),
                v_max_ms=round(r["vmax"], 4))


# ----------------------------------------------------------------- barra de sensores
def captura_barra(R, L):
    """Desplazamiento lateral de la línea en la barra cuando el eje entra a una curva de radio R
    con el robot aún recto (peor caso geométrico, sin corrección del control)."""
    recta = R - math.sqrt(R * R - L * L) if R > L else float("nan")
    # barra en arco de radio L centrado en el eje: la línea corta ese círculo en la cuerda de largo L
    alfa = math.asin(min(L / (2 * R), 1.0))
    arco_lat = L * math.sin(alfa) if L <= 2 * R else float("nan")
    arco_ang = math.degrees(alfa)
    return recta, arco_lat, arco_ang


def escribir(nombre, filas):
    os.makedirs(SALIDA, exist_ok=True)
    ruta = os.path.join(SALIDA, nombre)
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
    print(f"  {os.path.relpath(ruta, RAIZ)} ({len(filas)} filas)")


# ----------------------------------------------------------------- secciones
def sec_pistas(P):
    filas = [validar_pista(p) for p in P]
    escribir("C0_pistas.csv", filas)
    return filas


def sec_motores(P):
    filas = []
    for clave in CFG["motores"]:
        for D in (0.028, 0.034, 0.040):
            for V in (CFG["bateria"]["V_llena"], CFG["bateria"]["V_nominal"], CFG["bateria"]["V_baja"]):
                rb = robot_base(motor=motor(clave), D=D, V_oc=V)
                F0, I0, Vb = fuerza_motriz(rb, 0)
                fila = dict(motor=rb.motor.nombre, D_mm=D * 1000, V_bat=V,
                            v_libre_ms=round(v_libre(rb), 3),
                            a_arranque_motor_ms2=round(F0 / rb.masa, 2),
                            a_arranque_agarre_ms2=round(rb.a_max, 2),
                            I_bloqueo_por_motor_A=round(I0, 3))
                for p in P:
                    fila[f"t_{p.nombre.split()[0]}_s"] = vuelta(rb, p)["t_vuelta_s"]
                filas.append(fila)
    escribir("C1_motores_llanta_bateria.csv", filas)
    return filas


def sec_cuello(P):
    filas = []
    reg = CFG["reglamento"]
    medio = reg["ancho_max"] / 2 - CFG["diseno"]["margen_caja"]
    for L in np.arange(0.050, 0.1451, 0.005):
        L = round(float(L), 3)
        rb = robot_base(L=L)
        rec, arc, ang = captura_barra(reg["radio_min_linea"], L)
        Ra = radio_eje(reg["radio_min_linea"], L)
        fila = dict(L_mm=round(L * 1000), R_eje_en_R150_mm=round(Ra * 1000, 1),
                    lateral_barra_recta_mm=round(rec * 1000, 1),
                    lateral_barra_arco_mm=round(arc * 1000, 1),
                    semiancho_disponible_mm=round(medio * 1000, 1),
                    barra_recta_captura=bool(rec + reg["ancho_linea"] / 2 <= medio),
                    barra_arco_captura=bool(arc + reg["ancho_linea"] / 2 <= medio),
                    rueda_interior_avanza=bool(Ra > rb.W / 2))
        for p in P:
            fila[f"t_{p.nombre.split()[0]}_s"] = vuelta(rb, p)["t_vuelta_s"]
        filas.append(fila)
    escribir("C2_cuello.csv", filas)
    return filas


def sec_succion(P):
    filas = []
    for gf in (0, 25, 50, 100, 200, 300, 400):
        rb = robot_base(Fd=gf / 1000 * G, masa=masa_base() + (CFG["succion"]["masa_extra"] if gf else 0))
        fila = dict(F_down_gf=gf, masa_kg=round(rb.masa, 4), a_max_ms2=round(rb.a_max, 2),
                    v_curva_R150_eje_ms=round(math.sqrt(rb.a_max * radio_eje(0.15, rb.L)), 3))
        for p in P:
            fila[f"t_{p.nombre.split()[0]}_s"] = vuelta(rb, p)["t_vuelta_s"]
        filas.append(fila)
    escribir("C3_succion.csv", filas)
    return filas


def sec_sensibilidad(P):
    base = robot_base()
    var = [
        ("mu", "mu", 0.60, 1.00),
        ("f_motriz", "f_motriz", 0.55, 0.80),
        ("masa", "masa", base.masa * 0.8, base.masa * 1.3),
        ("V_oc", "V_oc", CFG["bateria"]["V_baja"], CFG["bateria"]["V_llena"]),
        ("R_int", "R_int", 0.05, 0.50),
        ("L", "L", 0.080, 0.120),
        ("D", "D", 0.030, 0.038),
        ("W", "W", 0.075, 0.090),
    ]
    filas = []
    for p in P:
        t0 = vuelta(base, p)["t_vuelta_s"]
        for etiqueta, campo, lo, hi in var:
            tlo = vuelta(replace(base, **{campo: lo}), p)["t_vuelta_s"]
            thi = vuelta(replace(base, **{campo: hi}), p)["t_vuelta_s"]
            filas.append(dict(pista=p.nombre, parametro=etiqueta, base=round(getattr(base, campo), 4),
                              bajo=round(lo, 4), alto=round(hi, 4), t_base_s=t0,
                              t_bajo_s=tlo, t_alto_s=thi,
                              cambio_bajo_pct=round(100 * (tlo / t0 - 1), 2),
                              cambio_alto_pct=round(100 * (thi / t0 - 1), 2)))
    escribir("C4_sensibilidad.csv", filas)
    return filas


def sec_frenado():
    filas = []
    base = robot_base()
    m = base.motor
    for v in (0.5, 1.0, 1.5, 2.0, 2.5):
        w = v / base.r
        fem = m.Ke * w
        fila = dict(v_ms=v, fem_por_motor_V=round(fem, 3))
        for modo in ("libre", "corto", "inverso"):
            F = fuerza_frenado(base, v, modo)
            fila[f"dec_{modo}_motor_ms2"] = round(F / base.masa + base.c_rr * G, 2)
        fila["dec_limite_agarre_ms2"] = round(base.a_max, 2)
        fila["I_inverso_por_motor_A"] = round(min((base.V_oc + fem) / m.R, base.I_lim), 3)
        fila["I_corto_por_motor_A"] = round(fem / m.R, 3)
        fila["fem_supera_VM_llena"] = bool(fem > CFG["bateria"]["V_llena"])
        filas.append(fila)
    escribir("C5_frenado.csv", filas)
    return filas


def sec_lazo():
    filas = []
    for L in (0.08, 0.10, 0.12):
        Ra = radio_eje(0.15, L)
        pendiente = L / Ra  # dy/dx de la línea vista en la barra recta al entrar a R150
        for v in (1.0, 1.5, 2.0, 2.5, 3.0):
            for p in (0.006, 0.008, 0.010, 0.0125):
                v_lat = v * pendiente
                filas.append(dict(L_mm=L * 1000, v_ms=v, paso_mm=p * 1000,
                                  barrido_lateral_ms=round(v_lat, 3),
                                  T_max_medio_paso_ms=round(p / 2 / v_lat * 1000, 3),
                                  avance_por_2ms_mm=round(v * 2.0, 2),
                                  t_hueco_5mm_ms=round(0.005 / v * 1000, 2)))
    escribir("C6_lazo_y_sensores.csv", filas)
    return filas


def sec_masa():
    filas = []
    tot = masa_base()
    for k, v in sorted(CFG["masa"].items(), key=lambda kv: -kv[1]):
        filas.append(dict(subsistema=k, masa_g=round(v * 1000, 1), fraccion_pct=round(100 * v / tot, 1)))
    filas.append(dict(subsistema="TOTAL", masa_g=round(tot * 1000, 1), fraccion_pct=100.0))
    filas.append(dict(subsistema="TOTAL + succión (opción)",
                      masa_g=round((tot + CFG["succion"]["masa_extra"]) * 1000, 1), fraccion_pct=""))
    filas.append(dict(subsistema="límite de diseño", masa_g=CFG["diseno"]["masa_limite_diseno"] * 1000,
                      fraccion_pct=""))
    filas.append(dict(subsistema="límite reglamento", masa_g=CFG["reglamento"]["masa_max"] * 1000,
                      fraccion_pct=""))
    escribir("C7_masa.csv", filas)
    return filas


def sec_energia():
    filas = []
    base = robot_base()
    for I_ventilador in (0.0, 1.0, 2.0, 4.0):
        for I_mot_prom in (0.3, 0.6, 1.0):
            I = I_mot_prom + base.I_log + I_ventilador
            mah_intento = I * CFG["reglamento"]["t_max_intento"] / 3.6
            filas.append(dict(I_ventilador_A=I_ventilador, I_motores_prom_A=I_mot_prom,
                              I_total_A=round(I, 2), mAh_intento_5min=round(mah_intento, 1),
                              intentos_con_500mAh_al_80pct=round(400 / mah_intento, 1),
                              caida_V_por_R_int=round(I * base.R_int, 2)))
    escribir("C8_energia.csv", filas)
    return filas


def sec_motor_succion(P):
    """Con succión el agarre sube y el motor puede pasar a ser el límite: se repite la comparación."""
    filas = []
    for gf in (0, 100, 200):
        for clave in CFG["motores"]:
            rb = robot_base(motor=motor(clave), Fd=gf / 1000 * G,
                            masa=masa_base() + (CFG["succion"]["masa_extra"] if gf else 0))
            F0, _, _ = fuerza_motriz(rb, 0)
            fila = dict(F_down_gf=gf, motor=rb.motor.nombre, a_max_agarre_ms2=round(rb.a_max, 2),
                        a_arranque_motor_ms2=round(F0 / rb.masa, 2), v_libre_ms=round(v_libre(rb), 3))
            for p in P:
                fila[f"t_{p.nombre.split()[0]}_s"] = vuelta(rb, p)["t_vuelta_s"]
            filas.append(fila)
    escribir("C10_motor_con_succion.csv", filas)
    return filas


# ----------------------------------------------------------------- gráficas
def graficas(P, cuello, succ, sens):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    cols = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.edgecolor": "#52514e", "axes.labelcolor": "#0b0b0b",
                         "xtick.color": "#52514e", "ytick.color": "#52514e",
                         "axes.grid": True, "grid.color": "#e6e5e1", "grid.linewidth": 0.6,
                         "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb"})

    # pistas
    fig, ax = plt.subplots(1, len(P), figsize=(12, 3.2))
    for a, p, c in zip(ax, P, cols):
        pts, _ = trazar(p)
        pts = pts - pts.min(0)
        a.plot(pts[:, 0], pts[:, 1], color="#0b0b0b", lw=2)
        a.set_aspect("equal")
        a.set_xlim(-0.05, 2.44)
        a.set_ylim(-0.05, 1.22)
        a.set_title(p.nombre, fontsize=9)
    fig.suptitle("Pistas de prueba dentro del tablero de 2.44 × 1.22 m", x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(os.path.join(SALIDA, "F0_pistas.png"), dpi=130)
    plt.close(fig)

    # cuello
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    Ls = [f["L_mm"] for f in cuello]
    for p, c in zip(P, cols):
        k = f"t_{p.nombre.split()[0]}_s"
        ax.plot(Ls, [f[k] for f in cuello], color=c, lw=2, marker="o", ms=4, label=p.nombre)
    lim = max(f["L_mm"] for f in cuello if f["barra_arco_captura"])
    ax.axvline(lim, color="#52514e", lw=1, ls="--")
    y0 = ax.get_ylim()[0]
    ax.text(lim + 1, y0 + 0.02, f"límite de captura de la barra\nen arco en R150: L ≤ {lim} mm",
            va="bottom", ha="left", fontsize=8, color="#52514e")
    ax.set_xlabel("Largo del cuello L (mm)")
    ax.set_ylabel("Tiempo de vuelta ideal (s)")
    ax.set_title("Tiempo de vuelta contra largo del cuello (cálculo cuasiestático)", loc="left")
    ax.legend(frameon=False, fontsize=8, loc="lower left")
    fig.tight_layout()
    fig.savefig(os.path.join(SALIDA, "F1_cuello.png"), dpi=130)
    plt.close(fig)

    # succión
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    g = [f["F_down_gf"] for f in succ]
    for p, c in zip(P, cols):
        k = f"t_{p.nombre.split()[0]}_s"
        t0 = succ[0][k]
        ax.plot(g, [100 * (f[k] / t0 - 1) for f in succ], color=c, lw=2, marker="o", ms=4, label=p.nombre)
    ax.set_xlabel("Fuerza de succión (gramos-fuerza), con +30 g de ventilador")
    ax.set_ylabel("Cambio del tiempo de vuelta (%)")
    ax.set_title("Efecto de la succión sobre el tiempo de vuelta", loc="left")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(SALIDA, "F2_succion.png"), dpi=130)
    plt.close(fig)

    # sensibilidad (pista P4)
    filas = [f for f in sens if f["pista"].startswith("P4")]
    filas.sort(key=lambda f: max(abs(f["cambio_bajo_pct"]), abs(f["cambio_alto_pct"])))
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    y = np.arange(len(filas))
    ax.barh(y - 0.18, [f["cambio_bajo_pct"] for f in filas], height=0.34, color=cols[0], label="valor bajo")
    ax.barh(y + 0.18, [f["cambio_alto_pct"] for f in filas], height=0.34, color=cols[1], label="valor alto")
    ax.set_yticks(y, [f"{f['parametro']} ({f['bajo']:g} / {f['alto']:g})" for f in filas])
    ax.axvline(0, color="#52514e", lw=1)
    ax.set_xlabel("Cambio del tiempo de vuelta en P4 (%)")
    ax.set_title("Sensibilidad del tiempo de vuelta (P4 exigente R150)", loc="left")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(SALIDA, "F3_sensibilidad_P4.png"), dpi=130)
    plt.close(fig)

    # perfil de velocidad P4
    rb = robot_base()
    r = perfil(rb, P[3])
    s = np.arange(len(r["v"])) * r["ds"]
    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.plot(s, r["v"], color=cols[0], lw=2)
    ax.set_xlabel("Distancia recorrida por el eje (m)")
    ax.set_ylabel("Velocidad del eje (m/s)")
    ax.set_title(f"Perfil de velocidad ideal en P4 (base: {rb.motor.nombre}, L = {rb.L*1000:.0f} mm)",
                 loc="left")
    fig.tight_layout()
    fig.savefig(os.path.join(SALIDA, "F4_perfil_P4.png"), dpi=130)
    plt.close(fig)
    print("  gráficas F0-F4 escritas")


def main():
    print("Fase 1: cálculos físicos")
    P = pistas()
    pist = sec_pistas(P)
    for f in pist:
        if not f["cumple"]:
            print("  AVISO: pista fuera de reglamento:", f)
    sec_motores(P)
    cu = sec_cuello(P)
    su = sec_succion(P)
    se = sec_sensibilidad(P)
    sec_frenado()
    sec_lazo()
    sec_masa()
    sec_energia()
    sec_motor_succion(P)
    base = robot_base()
    m = base.motor
    resumen = [dict(dato="motor", valor=m.nombre),
               dict(dato="R_motor_ohm", valor=round(m.R, 3)),
               dict(dato="Ke_Vs_rad", valor=round(m.Ke, 5)),
               dict(dato="Kt_Nm_A", valor=round(m.Kt, 5)),
               dict(dato="masa_kg", valor=round(base.masa, 4)),
               dict(dato="a_max_agarre_ms2", valor=round(base.a_max, 3)),
               dict(dato="v_libre_ms", valor=round(v_libre(base), 3))]
    for p in P:
        r = vuelta(base, p)
        resumen.append(dict(dato=f"vuelta_{p.nombre.split()[0]}", valor=f"{r['t_vuelta_s']} s; "
                            f"media {r['v_media_linea_ms']} m/s; max {r['v_max_ms']} m/s"))
    escribir("C9_resumen_base.csv", resumen)
    graficas(P, cu, su, se)


if __name__ == "__main__":
    main()
