"""Controladores candidatos. Unidades SI. Convención: e > 0 = línea a la DERECHA del robot."""
from dataclasses import dataclass
import math


@dataclass
class ParamDuty:            # C1: el control del prototipo anterior (PD directo sobre el ciclo de PWM)
    kp: float = 40.0        # 1/m  (0.04 /mm)
    kd: float = 2.0         # s/m  (0.002 s/mm)
    base: float = 0.6
    freno: float = 0.3
    e_ref: float = 0.030
    u_max: float = 0.6
    rueda_min: float = -0.3  # permite invertir la rueda interior (lo que se quiere evitar)


@dataclass
class ParamSF:              # C2: perfil de velocidad por curvatura + FF de motor + persecución pura + PD, sin inversión
    v_max: float = 2.0      # m/s velocidad de crucero máxima pedida
    a_lat: float = 5.0      # m/s² aceleración lateral permitida (<= μ·g·f)
    a_lon: float = 4.0      # m/s² rampa del comando de velocidad
    k_pp: float = 1.0       # peso del feed-forward de persecución pura (Δv = k_pp·2·v·e·W/L²)
    kp: float = 30.0        # ciclo de PWM diferencial por metro de error
    kd: float = 1.0         # ciclo de PWM diferencial por (m/s)
    tau_d: float = 0.004    # s, filtro de la derivada
    tau_k: float = 0.030    # s, filtro de la curvatura estimada
    permitir_inversion: bool = False
    e_critico: float = 0.80  # fracción de la semibarra a partir de la cual se permite invertir
    d_inv: float = 0.30      # ciclo máximo de reversa de la rueda interior en emergencia
    ff_acel: bool = True     # feed-forward de aceleración (al frenar baja el ciclo más rápido; con piso 0 = freno corto)
    freno_activo: bool = False  # permite ciclo común negativo (contracorriente) para frenar; NO aprobado aún


class ControlDuty:
    def __init__(self, p: ParamDuty):
        self.p = p
        self.e_prev = None

    def __call__(self, e, visible, borde, dt, robot, v_bat):
        p = self.p
        de = 0.0 if self.e_prev is None else (e - self.e_prev) / dt
        self.e_prev = e
        u = max(-p.u_max, min(p.u_max, p.kp * e + p.kd * de))
        b = p.base * max(0.5, 1 - p.freno * min(1.0, abs(e) / p.e_ref))
        izq, der = b + u, b - u
        hi = max(izq, der)
        if hi > 1: izq -= hi - 1; der -= hi - 1
        izq = max(p.rueda_min, min(1, izq)); der = max(p.rueda_min, min(1, der))
        vmot = min(v_bat, robot.v_max_motor)
        return izq * vmot / v_bat, der * vmot / v_bat, {"inv": (izq < 0) != (der < 0)}


class ControlSF:
    """1) Perfil de velocidad: v_obj = min(v_max, sqrt(a_lat/|κ̂|)), κ̂ = 2e/L² filtrada; rampa a_lon.
       2) Feed-forward de motor (sin encoders): ciclo = (Ke·ω_rueda + R·I0)/Vbat para v y para la
          diferencia de persecución pura Δv = k_pp·2·v·e·W/L².
       3) PD sobre la diferencia de ciclo (da el empuje transitorio que el FF no da).
       4) Sin inversión: si la rueda interior quedaría < 0, se baja el ciclo común (frenado diferencial)
          conservando la diferencia. Reversa (≤ d_inv) solo con |e| > e_critico·semibarra y línea en el borde."""

    def __init__(self, p: ParamSF):
        self.p = p
        self.e_f = None
        self.de_f = 0.0
        self.k_f = 0.0
        self.v_cmd = 0.0

    def __call__(self, e, visible, borde, dt, robot, v_bat):
        p, L, W, m = self.p, robot.L, robot.W, robot.motor
        if self.e_f is None:
            self.e_f = e
        de = (e - self.e_f) / dt
        self.e_f = e
        self.de_f += dt / (p.tau_d + dt) * (de - self.de_f)
        k_inst = 2 * e / (L * L)
        self.k_f += dt / (p.tau_k + dt) * (k_inst - self.k_f)
        v_obj = min(p.v_max, math.sqrt(p.a_lat / max(abs(self.k_f), 1e-6)))
        dv = v_obj - self.v_cmd
        paso = max(-p.a_lon * dt, min(p.a_lon * dt, dv))
        self.v_cmd += paso
        a_cmd = paso / dt
        v = max(self.v_cmd, 0.05)
        lim = min(v_bat, robot.v_max_motor) / v_bat

        def ff(vr_, a=0.0):
            # V = Ke·ω + R·(I0 + I_acel), I_acel = m·a·r / (2·Kt)  (cada motor empuja la mitad)
            w_r = vr_ / robot.r
            i_a = robot.masa * a * robot.r / (2 * m.kt) if p.ff_acel else 0.0
            i0 = math.copysign(m.i0, w_r) if abs(w_r) > 1e-3 else 0.0
            return (m.ke * w_r + m.R * (i0 + i_a)) / v_bat

        base = ff(v, a_cmd)
        dv_pp = p.k_pp * 2 * v * e * W / (L * L)
        delta = (ff(v + dv_pp / 2) - ff(v - dv_pp / 2)) + p.kp * e + p.kd * self.de_f
        dl, dr = base + delta / 2, base - delta / 2
        hi = max(dl, dr)
        if hi > lim: dl -= hi - lim; dr -= hi - lim
        semibarra = (robot.n_sens - 1) * robot.paso / 2
        emergencia = p.permitir_inversion and borde and abs(e) > p.e_critico * semibarra
        piso = -p.d_inv if emergencia else 0.0
        if p.freno_activo and base < 0:          # freno longitudinal: ambas ruedas reciben ciclo negativo
            piso = min(piso, max(base, -lim))     # pero nunca más bajo que lo que pide el FF de aceleración
        bajo = min(dl, dr)
        if bajo < piso:                         # frenado diferencial antes que invertir
            dl, dr = dl - (bajo - piso), dr - (bajo - piso)
        dl = max(-lim, min(lim, dl)); dr = max(-lim, min(lim, dr))
        return dl, dr, {"inv": (dl < 0) != (dr < 0), "v_cmd": self.v_cmd}
