"""Modelo de pista en Python del control del robot de emergencia (puerto 1:1 de la lógica en C++).

Por qué existe: en la PC del equipo Windows (Smart App Control) bloquea ejecutar los .exe de prueba compilados.
Este modelo reproduce la MISMA lógica que `emergencia/` (posicion, filtro, pid, control con turbo de recta y
motor) para simular una pista recta → curva R150 → recta → curva R200 → recta. La referencia sigue siendo el C++:
`test_emergencia.cpp` contiene la misma pista y debe ejecutarse donde se pueda.

Uso:  python modelo_pista.py            (tabla comparativa y comprobaciones; sale con 1 si alguna falla)
"""
import math
import random
import sys

# ------------------------------------------------------------------ perfiles (ajustes.cpp) y valores de fábrica
BASE = dict(kp=0.010, ki=0.0, kd=0.0004, vbase=0.25, freno=0.30, error_ref=30.0, vmin_rel=0.50, u_max=0.60,
            rueda_min=-0.30, tau_d=0.010, t_ret=0.060, t_busq=1.5, u_busq=0.35, v_busq=0.40,
            pwm_max=0.80, v_motor_max=6.0, i_max=1.2, i_total=2.0, rampa=4.0, rampa_freno=8.0,
            m_R=6.0, m_ke=0.0533, m_tau=0.08, alfa=0.6, umbral=0.10, confianza=0.30, paso_mm=12.7,
            # turbo (Turbo en ajustes.h)
            v_recta=0.0, recta_e_in=3.0, recta_e_out=6.0, recta_de_in=40.0, recta_de_out=150.0,
            recta_conf_in=1.2, recta_conf_out=0.8, t_confirmar=0.15, t_acel=0.5, recta_tau_de=0.04, recta_n_out=2)
PERFILES = {
    "seguro": dict(vbase=0.25, pwm_max=0.80, rampa=4.0, rampa_freno=8.0, kp=0.010, kd=0.0004, freno=0.30),
    "normal": dict(vbase=0.35, pwm_max=0.90, rampa=6.0, rampa_freno=12.0, kp=0.010, kd=0.0004, freno=0.30),
    "rapido": dict(vbase=0.50, pwm_max=1.00, rampa=8.0, rampa_freno=16.0, kp=0.012, kd=0.0006, freno=0.40),
}


def _num_sensores():
    """NUM_SENSORES de emergencia/config.h: el modelo usa siempre la misma cantidad que el firmware."""
    import pathlib
    import re
    txt = (pathlib.Path(__file__).resolve().parent.parent / "emergencia" / "config.h").read_text(encoding="utf-8")
    return int(re.search(r"^#define\s+NUM_SENSORES\s+(\d+)", txt, re.M).group(1))


N_SENSORES = _num_sensores()


def ajustes(perfil, **extra):
    a = dict(BASE)
    a.update(PERFILES[perfil])
    a.update(extra)
    return a


def lim(x, a, b):
    return a if x < a else (b if x > b else x)


# ------------------------------------------------------------------ filtro.cpp
class Canal:
    def __init__(self):
        self.h = [0.0, 0.0, 0.0]
        self.n = 0
        self.y = 0.0

    def paso(self, x, alfa):
        alfa = min(max(alfa, 0.01), 1.0)
        self.h = [self.h[1], self.h[2], x]
        if self.n < 3:
            self.n += 1
        m = x if self.n < 3 else sorted(self.h)[1]
        self.y = m if self.n == 1 else self.y + alfa * (m - self.y)
        return self.y


# ------------------------------------------------------------------ posicion.cpp
def estimar_posicion(xs, osc, umbral, conf_min):
    escala = max(1.0 - umbral, 0.05)
    suma = mom = 0.0
    for x, o in zip(xs, osc):
        d = (o - umbral) / escala
        if d <= 0.0:
            continue
        d = min(d, 1.0)
        suma += d
        mom += d * x
    if suma >= conf_min:
        return mom / suma, suma, True
    return 0.0, suma, False


# ------------------------------------------------------------------ pid.cpp
class PID:
    def __init__(self, kp, ki, kd, umax, tau):
        self.kp, self.ki, self.kd, self.min, self.max, self.tau = kp, ki, kd, -umax, umax, tau
        self.reiniciar()

    def reiniciar(self):
        self.integ = self.e_prev = self.d_filt = self.ultima = 0.0
        self.ini = False

    def calcular(self, e, dt):
        if not dt > 0:
            return self.ultima
        if self.ini:
            d_cruda = (e - self.e_prev) / dt
            self.d_filt += dt / (self.tau + dt) * (d_cruda - self.d_filt)
        else:
            self.ini = True
            self.d_filt = 0.0
        self.e_prev = e
        p, d = self.kp * e, self.kd * self.d_filt
        cand = self.integ + e * dt
        uc = p + d + self.ki * cand
        if not ((uc > self.max and e > 0) or (uc < self.min and e < 0)):
            self.integ = cand
        if self.ki > 0:
            l = max(abs(self.max), abs(self.min)) / self.ki
            self.integ = lim(self.integ, -l, l)
        u = lim(p + d + self.ki * self.integ, self.min, self.max)
        self.ultima = u
        return u


# ------------------------------------------------------------------ control.cpp (con turbo)
class Control:
    def __init__(self, a):
        self.a = a
        self.pid = PID(a["kp"], a["ki"], a["kd"], a["u_max"], a["tau_d"])
        self.reiniciar()

    def reiniciar(self):
        self.pid.reiniciar()
        self.t_sin = self.ult_e = self.ult_u = 0.0
        self.signo = 1.0
        self.g = self.t_ok = 0.0
        self.recta = False
        self.de_t = self.e_t = 0.0
        self.ini_t = False
        self.n_fuera = 0

    def actualizar(self, pos, conf, visible, dt, permitido=True):
        a = self.a
        buscando = perdida = False
        v_rel = 1.0
        if visible:
            self.t_sin = 0.0
            self.ult_e = pos
            if abs(pos) > 1.0:
                self.signo = 1.0 if pos > 0 else -1.0
            u = self.pid.calcular(pos, dt)
            self.ult_u = u
        else:
            self.t_sin += dt
            if self.t_sin <= a["t_ret"]:
                u = self.ult_u
            elif self.t_sin <= a["t_ret"] + a["t_busq"]:
                buscando = True
                u = self.signo * a["u_busq"]
                v_rel = a["v_busq"]
                self.pid.reiniciar()
            else:
                return dict(izq=0.0, der=0.0, u=0.0, buscando=True, perdida=True, turbo=0.0, v=0.0, error=self.ult_e)
        err = pos if visible else self.ult_e
        # derivada propia del turbo (más filtrada que la del PID); solo con la línea visible
        if visible:
            if self.ini_t:
                self.de_t += dt / (a["recta_tau_de"] + dt) * ((pos - self.e_t) / dt - self.de_t)
            else:
                self.ini_t, self.de_t = True, 0.0
            self.e_t = pos
        else:
            self.ini_t, self.de_t = False, 0.0
        de = self.de_t
        se_aleja = pos * de > 0.0 and abs(pos) > a["recta_e_in"]   # error ya fuera del centro y creciendo
        fuera = abs(pos) > a["recta_e_out"] or (abs(de) > a["recta_de_out"] and se_aleja)
        self.n_fuera = self.n_fuera + 1 if (visible and fuera) else 0
        cancelar = (not permitido or not visible or buscando or not (a["v_recta"] > a["vbase"]) or
                    conf < a["recta_conf_out"] or self.n_fuera >= a["recta_n_out"])
        if cancelar:
            self.g = self.t_ok = 0.0
            self.recta = False
        else:
            if not self.recta:
                entra = abs(pos) < a["recta_e_in"] and abs(de) < a["recta_de_in"] and conf >= a["recta_conf_in"]
                self.t_ok = self.t_ok + dt if entra else 0.0
                if self.t_ok >= a["t_confirmar"]:
                    self.recta = True
            if self.recta:
                self.g = min(1.0, self.g + (dt / a["t_acel"] if a["t_acel"] > 1e-3 else 1.0))
        vb = a["vbase"] + self.g * (a["v_recta"] - a["vbase"])
        if not buscando:
            frac = min(abs(err) / a["error_ref"], 1.0)
            v_rel = max(1.0 - a["freno"] * frac, a["vmin_rel"])
        v = (a["vbase"] if buscando else vb) * v_rel
        izq, der = v + u, v - u
        alto = max(izq, der)
        if alto > 1.0:
            izq -= alto - 1.0
            der -= alto - 1.0
        bajo = min(izq, der)
        if bajo < a["rueda_min"]:
            izq += a["rueda_min"] - bajo
            der += a["rueda_min"] - bajo
        izq = lim(izq, a["rueda_min"], 1.0)
        der = lim(der, a["rueda_min"], 1.0)
        return dict(izq=izq, der=der, u=u, buscando=buscando, perdida=perdida, turbo=self.g, v=v, error=err)


# ------------------------------------------------------------------ motor.cpp
class Accionamiento:
    def __init__(self, a):
        self.a = a
        self.d = [0.0, 0.0]
        self.w = [0.0, 0.0]

    def tope(self, v):
        t = self.a["pwm_max"]
        if v > 0.5:
            t = min(t, self.a["v_motor_max"] / v)
        return lim(t, 0.0, 1.0)

    def actualizar(self, ci, cd, v, dt):
        a = self.a
        R, ke, tau = a["m_R"], a["m_ke"], a["m_tau"]
        tp = self.tope(v)
        d = [0.0, 0.0]
        for k, c in enumerate((lim(ci, -1, 1), lim(cd, -1, 1))):
            x = c * tp
            frenando = (x - self.d[k]) * self.d[k] < 0.0
            paso = (a["rampa_freno"] if frenando else a["rampa"]) * dt
            x = lim(x, self.d[k] - paso, self.d[k] + paso)
            e = ke * self.w[k]
            x = lim(x, (e - a["i_max"] * R) / v, (e + a["i_max"] * R) / v)
            d[k] = lim(x, -tp, tp)
        i0 = (d[0] * v - ke * self.w[0]) / R
        i1 = (d[1] * v - ke * self.w[1]) / R
        s = abs(i0) + abs(i1)
        if s > a["i_total"] and s > 1e-6:
            f = a["i_total"] / s
            d[0] = lim((i0 * f * R + ke * self.w[0]) / v, -tp, tp)
            d[1] = lim((i1 * f * R + ke * self.w[1]) / v, -tp, tp)
        for k in range(2):
            self.d[k] = d[k]
            self.w[k] += dt / (tau + dt) * (d[k] * v / ke - self.w[k])


# ------------------------------------------------------------------ pista (metros): recta → R150 izq → recta → R200 der → recta
class Pista:
    def __init__(self, l1=1.0, r1=0.15, l2=0.6, r2=0.20, l3=0.6):
        self.prim = []   # (tipo, datos, s0, largo)
        s = 0.0
        self.prim.append(("recta", ((0.0, 0.0), (0.0, 1.0), l1), s, l1)); s += l1
        self.entradas = [s]
        c1 = (-r1, l1)
        self.prim.append(("arco", (c1, r1, 0.0, math.pi), s, r1 * math.pi)); s += r1 * math.pi
        p2 = (-2 * r1, l1)
        self.prim.append(("recta", (p2, (0.0, -1.0), l2), s, l2)); s += l2
        self.entradas.append(s)
        p3 = (p2[0], p2[1] - l2)
        c2 = (p3[0] - r2, p3[1])
        self.prim.append(("arco", (c2, r2, 0.0, -math.pi), s, r2 * math.pi)); s += r2 * math.pi
        p4 = (c2[0] - r2, c2[1])
        self.prim.append(("recta", (p4, (0.0, 1.0), l3), s, l3)); s += l3
        self.largo = s

    def distancia(self, px, py):
        """(distancia en m, posición s a lo largo de la pista) del punto más cercano."""
        mejor = (1e9, 0.0)
        for tipo, d, s0, largo in self.prim:
            if tipo == "recta":
                (ax, ay), (ux, uy), L = d
                t = lim((px - ax) * ux + (py - ay) * uy, 0.0, L)
                qx, qy = ax + t * ux, ay + t * uy
                cand = (math.hypot(px - qx, py - qy), s0 + t)
            else:
                (cx, cy), R, a0, barrido = d
                phi = math.atan2(py - cy, px - cx)
                delta = ((phi - a0) if barrido > 0 else (a0 - phi)) % (2 * math.pi)
                if delta <= abs(barrido):
                    cand = (abs(math.hypot(px - cx, py - cy) - R), s0 + R * delta)
                else:
                    a1 = a0 + barrido
                    e0 = math.hypot(px - (cx + R * math.cos(a0)), py - (cy + R * math.sin(a0)))
                    e1 = math.hypot(px - (cx + R * math.cos(a1)), py - (cy + R * math.sin(a1)))
                    cand = (e0, s0) if e0 < e1 else (e1, s0 + largo)
            if cand[0] < mejor[0]:
                mejor = cand
        return mejor


# ------------------------------------------------------------------ simulación (mismo modelo que test_emergencia.cpp)
def simular(a, pista=None, ruido=40.0, picos=0.01, semilla=7, t_max=30.0, permitido=lambda t: True,
            evento=None):
    pista = pista or Pista()
    rng = random.Random(semilla)
    r_rueda, W, tau_real, dt, V = 0.014, 0.080, 0.05, 0.0025, 6.0
    n = N_SENSORES                                           # de config.h (NUM_SENSORES)
    xs = [(i - (n - 1) / 2.0) * a["paso_mm"] for i in range(n)]   # geometria_recta de posicion.cpp
    y_barra = 100.0
    fil = [Canal() for _ in range(n)]
    ctl = Control(a)
    acc = Accionamiento(a)
    x, y, th, wl, wr = 0.0, 0.0, math.pi / 2, 0.0, 0.0
    res = dict(peor=0.0, perdio=False, busquedas=0, t_vuelta=None, dist=0.0, sat=False, reversa=False,
               cambios_turbo=0, t_turbo=0.0, v_max=0.0, entradas=[], vel_entrada=[], d_media=0.0)
    entradas = list(pista.entradas)
    d_ultimo_cancel = None
    turbo_prev = 0.0
    buscando_prev = False
    t = 0.0
    while t < t_max:
        hx, hy, rx, ry = math.cos(th), math.sin(th), math.sin(th), -math.cos(th)
        osc = []
        for i in range(n):
            px = x + (y_barra * hx + xs[i] * rx) / 1000.0
            py = y + (y_barra * hy + xs[i] * ry) / 1000.0
            dist_mm = pista.distancia(px, py)[0] * 1000.0
            o = lim((15.0 - dist_mm) / 5.0, 0.0, 1.0)
            on = 300 + o * 3500 + rng.gauss(0.0, ruido)
            if rng.random() < picos:
                on += 2000
            off = 4000 + rng.gauss(0.0, ruido)
            refl = max(0.0, float(int(off) - int(on)))
            osc.append(fil[i].paso(refl, a["alfa"]))
        oscur = [lim(1.0 - (r - 200.0) / 3500.0, 0.0, 1.0) for r in osc]   # calibración 200..3700
        if evento:
            oscur = evento(t, oscur)
        pos, conf, vis = estimar_posicion(xs, oscur, a["umbral"], a["confianza"])
        s = ctl.actualizar(pos, conf, vis, dt, permitido(t))
        if s["perdida"]:
            res["perdio"] = True
            break
        if s["buscando"] and not buscando_prev:
            res["busquedas"] += 1
        buscando_prev = s["buscando"]
        if max(abs(s["izq"]), abs(s["der"])) >= 0.999:
            res["sat"] = True
        acc.actualizar(s["izq"], s["der"], V, dt)
        if min(acc.d) < -1e-6:
            res["reversa"] = True
        wl += dt / (tau_real + dt) * (acc.d[0] * V / a["m_ke"] - wl)
        wr += dt / (tau_real + dt) * (acc.d[1] * V / a["m_ke"] - wr)
        v = r_rueda * (wl + wr) / 2
        x += v * math.cos(th) * dt
        y += v * math.sin(th) * dt
        th += r_rueda * (wr - wl) / W * dt
        res["dist"] += v * dt
        res["v_max"] = max(res["v_max"], v)
        t += dt
        # turbo: cambios, tiempo y cuándo se cancela respecto a la entrada de cada curva
        if (s["turbo"] > 0) != (turbo_prev > 0):
            res["cambios_turbo"] += 1
            if s["turbo"] == 0:
                d_ultimo_cancel = res["dist"]
        turbo_prev = s["turbo"]
        if s["turbo"] > 0:
            res["t_turbo"] += dt
        bx, by = x + 0.100 * math.cos(th), y + 0.100 * math.sin(th)
        dbar, sbar = pista.distancia(bx, by)
        if t > 0.5:
            res["peor"] = max(res["peor"], dbar * 1000.0)
        if entradas and sbar >= entradas[0]:
            entradas.pop(0)
            res["vel_entrada"].append(v)
            if s["turbo"] > 0:
                res["entradas"].append(["turbo activo", res["dist"]])   # se completa al cancelarse
            else:
                antes = None if d_ultimo_cancel is None else (res["dist"] - d_ultimo_cancel) * 1000.0
                res["entradas"].append(["sin turbo", antes])
        if res["entradas"] and res["entradas"][-1][0] == "turbo activo" and s["turbo"] == 0:
            res["entradas"][-1] = ["cancelado dentro", (res["dist"] - res["entradas"][-1][1]) * 1000.0]
        if sbar >= pista.largo - 0.15:
            res["t_vuelta"] = t
            break
    if res["t_vuelta"]:
        res["d_media"] = res["dist"] / res["t_vuelta"]
    return res


# ------------------------------------------------------------------ el modelo debe usar las constantes del firmware
FIRMWARE = __import__("pathlib").Path(__file__).resolve().parent.parent / "emergencia"
NOMBRES_C = {"recta_tau_de_s": "recta_tau_de", "t_confirmar_s": "t_confirmar", "t_acel_s": "t_acel",
             "recta_t_conf": "t_confirmar", "recta_t_acel": "t_acel"}


def constantes_firmware():
    """Valores por defecto de control.h (ParamControl) y ajustes.h (Ajustes, Turbo), y la tabla de perfiles."""
    import re
    vals = {}
    for archivo in ("control.h", "ajustes.h"):
        for linea in (FIRMWARE / archivo).read_text(encoding="utf-8").splitlines():
            linea = linea.split("//")[0]
            if re.match(r"\s*(float|int)\s", linea):
                for nombre, v in re.findall(r"(\w+)\s*=\s*(-?[\d.]+)f?\b", linea):
                    vals.setdefault(archivo, {})[NOMBRES_C.get(nombre, nombre)] = float(v)
    perfiles = {}
    for nombre, nums in re.findall(r'\{"(\w+)",\s*([-\d.f,\s]+)\}', (FIRMWARE / "ajustes.cpp").read_text(encoding="utf-8")):
        perfiles[nombre] = [float(x.strip().rstrip("f")) for x in nums.split(",") if x.strip()]
    return vals, perfiles


def verificar_constantes():
    vals, perfiles = constantes_firmware()
    errores = []
    turbo = {k: v for k, v in vals["control.h"].items() if k.startswith("recta_") or k in ("t_confirmar", "t_acel")}
    for k, v in turbo.items():
        if abs(BASE[k] - v) > 1e-9:
            errores.append(f"control.h {k}={v} pero el modelo usa {BASE[k]}")
    for k, v in vals["ajustes.h"].items():
        if k in BASE and k != "v_recta" and abs(BASE[k] - v) > 1e-9:
            errores.append(f"ajustes.h {k}={v} pero el modelo usa {BASE[k]}")
    campos = ["vbase", "pwm_max", "rampa", "rampa_freno", "kp", "kd", "freno"]
    for nombre, nums in perfiles.items():
        if nombre not in PERFILES:
            continue
        for c, v in zip(campos, nums):
            if abs(PERFILES[nombre][c] - v) > 1e-9:
                errores.append(f"perfil {nombre}: {c}={v} en ajustes.cpp, {PERFILES[nombre][c]} en el modelo")
        vr = nums[len(campos)] if len(nums) > len(campos) else None
        if vr is None or abs(TURBOS.get(nombre, 0.0) - vr) > 1e-9:
            errores.append(f"perfil {nombre}: v_recta={vr} en ajustes.cpp, {TURBOS.get(nombre, 0.0)} en el modelo")
    return errores


# ------------------------------------------------------------------ comparación y comprobaciones
TURBOS = {"normal": 0.42, "rapido": 0.55}   # v_recta por perfil (seguro: desactivado). Elegidos con el barrido


def main():
    fallas = []

    def check(cond, texto):
        if not cond:
            fallas.append(texto)

    dif = verificar_constantes()
    for d in dif:
        check(False, "constante distinta del firmware: " + d)
    print("constantes del modelo = firmware (control.h, ajustes.h, ajustes.cpp):", "OK" if not dif else "DIFIEREN")

    print("perfil  turbo  v_recta  vuelta[s]  vel.media  desvio_max[mm]  busquedas  perdio  t_turbo[s]  cambios  "
          "entrada R150 / R200")
    resultados = {}
    for perfil in ("seguro", "normal", "rapido"):
        for con in (False, True):
            if con and perfil not in TURBOS:
                continue
            vr = TURBOS.get(perfil, 0.0) if con else 0.0
            r = simular(ajustes(perfil, v_recta=vr))
            resultados[(perfil, con)] = r
            def txt(e):
                if e[0] == "turbo activo":
                    return "TURBO SIN CANCELAR"
                if e[0] == "cancelado dentro":
                    return f"cancelado {e[1]:.0f} mm dentro"
                return "sin turbo previo" if e[1] is None else f"cancelado {e[1]:.0f} mm antes"
            ent = " / ".join(txt(e) + f" ({v:.2f} m/s)" for e, v in zip(r["entradas"], r["vel_entrada"]))
            vuelta = f"{r['t_vuelta']:.2f}" if r["t_vuelta"] else "NO TERMINA"
            print(f"{perfil:7s} {'si' if con else 'no':5s}  {vr:6.2f}   {vuelta:>9s}  {r['d_media']:9.3f}  "
                  f"{r['peor']:14.1f}  {r['busquedas']:9d}  {str(r['perdio']):6s}  {r['t_turbo']:10.2f}  "
                  f"{r['cambios_turbo']:7d}  {ent}")
            check(r["t_vuelta"] is not None and not r["perdio"], f"{perfil} turbo={con}: no termina la pista")
            check(r["busquedas"] == 0, f"{perfil} turbo={con}: perdio la linea {r['busquedas']} veces")
            check(r["peor"] < 30.0, f"{perfil} turbo={con}: desvio {r['peor']:.1f} mm")
            for e in r["entradas"]:
                # la barra va 100 mm delante del eje: cancelar < 60 mm dentro de la curva = el eje aún no llegó
                check(e[0] != "turbo activo", f"{perfil} turbo={con}: el turbo sigue activo en la curva")
                if e[0] == "cancelado dentro":   # < 100 mm: el eje (100 mm detrás de la barra) aún no entra a la curva
                    check(e[1] < 100.0, f"{perfil} turbo={con}: el turbo se cancela {e[1]:.0f} mm dentro de la curva")
    for p in TURBOS:
        sin, con = resultados[(p, False)], resultados[(p, True)]
        if sin["t_vuelta"] and con["t_vuelta"]:
            mejora = (sin["t_vuelta"] - con["t_vuelta"]) / sin["t_vuelta"] * 100
            print(f"  {p}: turbo {'mejora' if mejora > 0 else 'empeora'} la vuelta {abs(mejora):.1f} % "
                  f"(desvio {sin['peor']:.1f} -> {con['peor']:.1f} mm)")
            check(con["peor"] <= sin["peor"] + 5.0, f"{p}: el turbo aumenta el desvio mas de 5 mm")

    # seguro: turbo desactivado = salida idéntica
    a = ajustes("seguro")
    c1, c2 = Control(a), Control(dict(a, v_recta=a["vbase"]))
    rng = random.Random(3)
    iguales = True
    for k in range(4000):
        pos = rng.uniform(-40, 40)
        vis = rng.random() > 0.05
        s1, s2 = c1.actualizar(pos, 2.0, vis, 0.0025), c2.actualizar(pos, 2.0, vis, 0.0025)
        iguales &= (s1["izq"] == s2["izq"] and s1["der"] == s2["der"] and s2["turbo"] == 0.0)
    check(iguales, "perfil seguro: con v_recta <= vbase la salida no es identica")

    # ruido cerca del umbral: recta con la línea corrida ~3 mm y ruido triple
    largo = Pista(l1=4.0)
    for perfil in TURBOS:
        r = simular(ajustes(perfil, v_recta=TURBOS[perfil]), pista=largo, ruido=120.0, picos=0.03, t_max=6.0)
        print(f"  ruido x3 en recta ({perfil}): {r['cambios_turbo']} activaciones/cancelaciones en "
              f"{r['t_turbo']:.2f} s de turbo")
        check(r["cambios_turbo"] <= 6, f"{perfil}: el turbo parpadea con ruido ({r['cambios_turbo']} cambios)")

    # recta larga: aceleración progresiva (no salta), turbo cancelado por pérdida de línea y por permiso retirado
    for perfil in TURBOS:
        a = ajustes(perfil, v_recta=TURBOS[perfil])
        ctl = Control(a)
        gs = [ctl.actualizar(0.0, 2.0, True, 0.0025)["turbo"] for _ in range(400)]   # 1 s centrado
        subidas = [b - a_ for a_, b in zip(gs, gs[1:])]
        check(max(subidas) <= 0.0025 / a["t_acel"] + 1e-9, f"{perfil}: el turbo sube de golpe")
        check(gs[-1] == 1.0, f"{perfil}: no llega al turbo completo en 1 s")
        check(ctl.actualizar(0.0, 0.1, False, 0.0025)["turbo"] == 0.0, f"{perfil}: no se cancela al perder la linea")
        for _ in range(400):
            ctl.actualizar(0.0, 2.0, True, 0.0025)
        check(ctl.actualizar(0.0, 2.0, True, 0.0025, permitido=False)["turbo"] == 0.0,
              f"{perfil}: no se cancela al retirar el permiso (bateria/ciclo/estado)")
        for _ in range(400):
            ctl.actualizar(0.0, 2.0, True, 0.0025)
        check(ctl.actualizar(8.0, 2.0, True, 0.0025)["turbo"] > 0.0, f"{perfil}: un solo ciclo con 8 mm (ruido) lo cancela")
        check(ctl.actualizar(8.0, 2.0, True, 0.0025)["turbo"] == 0.0, f"{perfil}: no se cancela con 8 mm sostenidos 5 ms")
        for _ in range(400):
            ctl.actualizar(0.0, 2.0, True, 0.0025)
        check(ctl.actualizar(0.0, 0.5, True, 0.0025)["turbo"] == 0.0, f"{perfil}: no se cancela con confianza baja")

    # recuperación tras perder la línea a mitad de la recta (3 cm sin línea): busca, la encuentra y termina
    def hueco(t, osc):
        return [0.0] * len(osc) if 1.5 <= t < 1.62 else osc
    for perfil in TURBOS:
        r = simular(ajustes(perfil, v_recta=TURBOS[perfil]), evento=hueco)
        print(f"  linea borrada 120 ms en la recta ({perfil}): busquedas={r['busquedas']} perdio={r['perdio']} "
              f"vuelta={r['t_vuelta']}")
        check(r["t_vuelta"] is not None and not r["perdio"], f"{perfil}: no se recupera tras perder la linea")

    if fallas:
        print("FALLAS:")
        for f in fallas:
            print("  -", f)
        return 1
    print("modelo de pista: todas las comprobaciones OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
