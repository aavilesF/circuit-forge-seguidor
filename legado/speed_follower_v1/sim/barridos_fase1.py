"""Barridos de la fase de arquitectura. Reproducible: python3 barridos_fase1.py  (escribe resultados/*.csv)."""
import csv, itertools, math, os, json
from multiprocessing import Pool
import numpy as np
from modelo import Robot, MOTORES, pistas_reglamento, G
from control import ControlSF, ParamSF, ControlDuty, ParamDuty
from simular import correr

os.makedirs("resultados", exist_ok=True)
P = pistas_reglamento()
BASE_CTRL = dict(kp=120, kd=4, a_lat=4.0)


def guardar(nombre, filas):
    with open(f"resultados/{nombre}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys())); w.writeheader(); w.writerows(filas)


def evalua(args):
    etiqueta, robot, prm, tipo = args
    out = dict(etiqueta)
    tot, ok, emax, rev, inv, ip, irms, der = 0.0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    for p in P:
        mk = (lambda: ControlSF(prm)) if tipo == "SF" else (lambda: ControlDuty(prm))
        r = correr(robot, p, mk, t_max=25)
        tot += r["t"] if r["ok"] else float("nan")
        ok += r["ok"]; emax = max(emax, r["e_max"]); rev += r["t_reversa"]; inv += r["t_inv"]
        ip = max(ip, r["i_pico"]); irms = max(irms, r["i_rms"]); der += r["t_derrape"]
    out.update(ok=ok, t_total=round(tot, 2) if ok == 3 else "", e_max_mm=round(emax * 1000, 1), t_reversa=round(rev, 3),
               t_inv=round(inv, 3), i_pico=round(ip, 2), i_rms=round(irms, 3), t_derrape=round(der, 3),
               T_ctrl_ms=round(max(robot.T_ctrl, robot.t_lectura() + 0.0002) * 1000, 2), lat_ms=round((robot.t_lectura() + 0.0001) * 1000, 2))
    return out


def correr_tareas(tareas):
    with Pool() as pool:
        return pool.map(evalua, tareas)


def perfil_ideal(p, v_max, a_lat, a_lon):
    """Tiempo de vuelta con la pista conocida (mapa): v(s) <= sqrt(a_lat/|κ|), aceleración y frenado <= a_lon."""
    k = np.abs(p.kappa); ds = p.s[1] - p.s[0]
    v = np.minimum(v_max, np.sqrt(a_lat / np.maximum(k, 1e-9)))
    v[0] = 0.0
    for i in range(1, len(v)): v[i] = min(v[i], math.sqrt(v[i - 1] ** 2 + 2 * a_lon * ds))
    if not p.cerrada: pass
    for i in range(len(v) - 2, -1, -1): v[i] = min(v[i], math.sqrt(v[i + 1] ** 2 + 2 * a_lon * ds))
    return float(np.sum(ds / np.maximum(v[1:], 1e-3)))


if __name__ == "__main__":
    resumen = {}
    m12 = MOTORES["Pololu HPCB 12V 10:1"]
    base = Robot(m12, v_bat=7.4)

    # S1: techo teórico con mapa vs. velocidad máxima (grip μ=0.8, f=0.7 -> a_lat <= 5.5; se usa 4)
    filas = []
    for vm in (1.0, 1.5, 2.0, 2.5, 3.0):
        fila = dict(v_max=vm)
        for p in P: fila[p.nombre] = round(perfil_ideal(p, vm, 4.0, 4.0), 2)
        filas.append(fila)
    guardar("S1_techo_con_mapa", filas)

    # S2: control reactivo, cuello L x velocidad máxima
    t = [(dict(L_mm=int(L * 1000), v_max=vm), Robot(m12, v_bat=7.4, L=L), ParamSF(v_max=vm, **BASE_CTRL), "SF")
         for L, vm in itertools.product((0.06, 0.08, 0.10, 0.12, 0.14, 0.16), (0.8, 1.0, 1.2, 1.4))]
    guardar("S2_cuello_velocidad", correr_tareas(t))

    # S3: barra de sensores (n, paso) con latencia de lectura real por canal
    combos = [(8, 0.0095), (8, 0.012), (12, 0.008), (16, 0.006), (6, 0.016)]
    t = [(dict(n=n, paso_mm=pa * 1000, ancho_mm=round((n - 1) * pa * 1000 + 3, 1), t_canal_us=int(tc * 1e6)),
          Robot(m12, v_bat=7.4, L=0.10, n_sens=n, paso=pa, t_canal=tc), ParamSF(v_max=1.0, **BASE_CTRL), "SF")
         for (n, pa), tc in itertools.product(combos, (40e-6, 120e-6))]
    guardar("S3_barra", correr_tareas(t))

    # S4: motores (mismo control, v_max 1.0 y 1.2; diámetro 33 mm; motores de 6 V limitados a 6 V promedio)
    t = []
    for nombre, m in MOTORES.items():
        vmm = 6.0 if m.v_nom == 6.0 else 99
        for d in (0.033, 0.043):
            for vm in (1.0, 1.2):
                r = Robot(m, v_bat=7.4, v_max_motor=vmm, diam=d)
                t.append((dict(motor=nombre, diam_mm=int(d * 1000), v_max=vm, v_libre=round(r.v_libre(), 2)), r, ParamSF(v_max=vm, **BASE_CTRL), "SF"))
    guardar("S4_motores", correr_tareas(t))

    # S5: control: anterior (PD sobre PWM con inversión) vs SF sin inversión vs SF con inversión de emergencia vs sin FF de aceleración
    t = [(dict(control="C1 PD-PWM (prototipo anterior)", v_max=vm), base, ParamDuty(base=vm / base.v_libre()), "duty") for vm in (0.8, 1.0, 1.2)]
    for vm in (0.8, 1.0, 1.2):
        t.append((dict(control="C2 SF sin inversión", v_max=vm), base, ParamSF(v_max=vm, **BASE_CTRL), "SF"))
        t.append((dict(control="C2 SF + inversión de emergencia", v_max=vm), base, ParamSF(v_max=vm, permitir_inversion=True, **BASE_CTRL), "SF"))
        t.append((dict(control="C2 SF sin FF de aceleración", v_max=vm), base, ParamSF(v_max=vm, ff_acel=False, **BASE_CTRL), "SF"))
        t.append((dict(control="C2 SF sin persecución pura", v_max=vm), base, ParamSF(v_max=vm, k_pp=0, **BASE_CTRL), "SF"))
    guardar("S5_control", correr_tareas(t))

    # S6: sensibilidad (latencia de control, ruido, agarre, masa)
    t = []
    for tc in (0.001, 0.002, 0.004, 0.008):
        t.append((dict(variable="T_ctrl_ms", valor=tc * 1000), Robot(m12, v_bat=7.4, T_ctrl=tc), ParamSF(v_max=1.0, **BASE_CTRL), "SF"))
    for ru in (0.03, 0.10, 0.20):
        t.append((dict(variable="ruido", valor=ru), Robot(m12, v_bat=7.4, ruido=ru), ParamSF(v_max=1.0, **BASE_CTRL), "SF"))
    for mu in (0.5, 0.65, 0.8, 1.0):
        t.append((dict(variable="mu", valor=mu), Robot(m12, v_bat=7.4, mu=mu), ParamSF(v_max=1.0, **BASE_CTRL), "SF"))
    for ma in (0.15, 0.20, 0.30, 0.45):
        t.append((dict(variable="masa_kg", valor=ma), Robot(m12, v_bat=7.4, masa=ma), ParamSF(v_max=1.0, **BASE_CTRL), "SF"))
    guardar("S6_sensibilidad", correr_tareas(t))
    print("listo")
