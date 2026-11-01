"""Lazo cerrado: física a 0.25 ms, control a T_ctrl con latencia de lectura."""
import math
import numpy as np
from modelo import Robot, Pista, G


def _sensores(robot, pista, X, Y, th, idx, rng):
    """Lectura normalizada (0 blanco, 1 negro) de cada sensor y error verdadero en la barra."""
    n = robot.n_sens
    xs = (np.arange(n) - (n - 1) / 2) * robot.paso           # + a la derecha
    fx, fy = math.cos(th), math.sin(th)
    rx, ry = math.sin(th), -math.cos(th)
    px = X + robot.L * fx + xs * rx
    py = Y + robot.L * fy + xs * ry
    N = len(pista.s)
    if pista.cerrada:
        ventana = (idx + np.arange(-150, 600)) % N
    else:
        ventana = np.arange(max(0, idx - 150), min(N, idx + 600))
    qx, qy = pista.xy[ventana, 0], pista.xy[ventana, 1]
    d2 = (px[:, None] - qx[None, :]) ** 2 + (py[:, None] - qy[None, :]) ** 2
    j = np.argmin(d2, axis=1)
    dist = np.sqrt(d2[np.arange(n), j])
    hueco = pista.hueco[ventana[j]]
    cov = np.clip((0.0125 + robot.mancha - dist) / (2 * robot.mancha), 0, 1)
    cov[hueco] = 0.0
    lect = np.clip(cov + rng.normal(0, robot.ruido, n), 0, 1)
    # error verdadero en el centro de la barra
    cx, cy = X + robot.L * fx, Y + robot.L * fy
    d2c = (cx - qx) ** 2 + (cy - qy) ** 2
    k = int(np.argmin(d2c))
    gi = int(ventana[k])
    tx, ty = math.cos(pista.th[gi]), math.sin(pista.th[gi])
    e_signo = (cx - qx[k]) * (-ty) + (cy - qy[k]) * tx      # + si la línea está a la derecha de la barra
    return lect, xs, e_signo, gi


def _estimar(lect, xs, umbral=0.25):
    w = np.clip((lect - umbral) / (1 - umbral), 0, 1)
    s = w.sum()
    if s < 0.5:
        return None, False
    e = float((w * xs).sum() / s)
    borde = bool(w[0] > 0.3 or w[-1] > 0.3)
    return e, borde


def correr(robot: Robot, pista: Pista, crear_control, t_max=30.0, semilla=1, traza=False):
    rng = np.random.default_rng(semilla)
    ctl = crear_control()
    m = robot.motor
    dt = 0.00025
    T = max(robot.T_ctrl, robot.t_lectura() + 0.0002)        # el ciclo no puede ser más corto que la lectura
    lat = robot.t_lectura() + 0.0001                          # de la muestra a la orden aplicada
    X, Y = float(pista.xy[0, 0]), float(pista.xy[0, 1])
    th = float(pista.th[0])
    X -= robot.L * math.cos(th); Y -= robot.L * math.sin(th)  # barra sobre el inicio
    vx = vy = w = 0.0
    idx = 0
    d_izq = d_der = 0.0
    pend = []
    t_sig = 0.0
    e_ult, visto_ult_t = 0.0, 0.0
    res = dict(ok=False, fin="tiempo", t=0.0, e_max=0.0, e_rms=0.0, perdidas=0, t_inv=0.0, t_reversa=0.0, i_pico=0.0,
               i_rms=0.0, p_driver=0.0, t_derrape=0.0, v_max=0.0)
    acc_e2 = acc_i2 = 0.0; n_e = n_i = 0
    visible_prev = True
    vuelta_iniciada = False
    tr = [] if traza else None
    R_on = 0.5  # Ω alto+bajo por canal (TB6612 típico) para estimar disipación del driver
    t = 0.0
    while t < t_max:
        if t >= t_sig:
            lect, xs, e_true, idx = _sensores(robot, pista, X, Y, th, idx, rng)
            e_est, borde = _estimar(lect, xs)
            vis = e_est is not None
            if vis:
                e_ult, visto_ult_t = e_est, t
            elif t - visto_ult_t > 0.3:
                res["fin"] = "linea_perdida"; break
            if visible_prev and not vis: res["perdidas"] += 1
            visible_prev = vis
            e_uso = e_est if vis else e_ult
            izq, der, info = ctl(e_uso, vis, borde if vis else True, T, robot, robot.v_bat)
            pend.append((t + lat, izq, der, info.get("inv", False)))
            acc_e2 += e_true ** 2; n_e += 1
            res["e_max"] = max(res["e_max"], abs(e_true))
            if abs(e_true) > 0.0125 + (robot.n_sens - 1) * robot.paso / 2 + 0.01:
                res["fin"] = "fuera_de_barra"; break
            t_sig += T
            if idx > 50: vuelta_iniciada = True
            if (not pista.cerrada and idx >= len(pista.s) - 30) or (pista.cerrada and vuelta_iniciada and idx < 20 and t > 0.5):
                res["ok"] = True; res["fin"] = "meta"; break
        while pend and pend[0][0] <= t:
            _, d_izq, d_der, inv = pend.pop(0)
            res["_inv"] = inv
        if res.get("_inv"): res["t_inv"] += dt
        # ruedas
        vl = vx + w * robot.W / 2      # + w = giro horario (derecha) -> rueda izquierda más rápida
        vr = vx - w * robot.W / 2
        if min(vl, vr) < -0.02: res["t_reversa"] += dt
        Tl, il = m.par(d_izq * robot.v_bat, vl / robot.r)
        Tr, ir = m.par(d_der * robot.v_bat, vr / robot.r)
        Fmax = robot.mu * robot.masa * G * robot.f_motriz / 2
        Fl = max(-Fmax, min(Fmax, Tl / robot.r))
        Fr = max(-Fmax, min(Fmax, Tr / robot.r))
        # inercia rotacional de motores despreciada; resistencia a la rodadura 2 % del peso
        Frr = 0.02 * robot.masa * G * (1 if vx > 0.01 else 0)
        ax = (Fl + Fr - Frr) / robot.masa + w * vy * 0   # (marco: x adelante)
        # dinámica lateral: fricción lateral limitada por agarre
        F_lat_max = robot.mu * robot.masa * G * robot.f_motriz
        F_lat = max(-F_lat_max, min(F_lat_max, -robot.masa * vy / 0.003))
        ay = -vx * w + F_lat / robot.masa             # marco del cuerpo, y a la derecha; w horario
        if abs(F_lat) >= F_lat_max * 0.999: res["t_derrape"] += dt
        aw = (Fl - Fr) * robot.W / 2 / robot.J
        vx += ax * dt; vy += ay * dt; w += aw * dt
        vx = max(vx, -0.5)
        # integración en el mundo: rumbo th (CCW +); w horario => th disminuye
        th -= w * dt
        X += (vx * math.cos(th) + vy * math.sin(th)) * dt
        Y += (vx * math.sin(th) - vy * math.cos(th)) * dt
        for i_ in (il, ir):
            res["i_pico"] = max(res["i_pico"], abs(i_))
            acc_i2 += i_ * i_; n_i += 1
        res["v_max"] = max(res["v_max"], vx)
        if tr is not None and int(t / dt) % 20 == 0:
            tr.append((t, X, Y, vx, d_izq, d_der, il, ir))
        t += dt
    res["t"] = t
    res["e_rms"] = math.sqrt(acc_e2 / max(n_e, 1))
    res["i_rms"] = math.sqrt(acc_i2 / max(n_i, 1))
    res["p_driver"] = 2 * res["i_rms"] ** 2 * R_on
    res["T_ctrl"] = T
    res["lat"] = lat
    res.pop("_inv", None)
    if tr is not None: res["traza"] = tr
    return res
