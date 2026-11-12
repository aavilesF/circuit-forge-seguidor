"""Simulador del Speed Follower (fase de arquitectura). Python + numpy.

Modela:
  * motor DC con reductora (curva par-velocidad lineal) a partir de datos de ficha: V nominal,
    RPM sin carga, par de bloqueo, corriente de bloqueo y sin carga
  * dinámica del robot: masa, inercia de giro, tracción limitada por agarre (μ) en cada rueda,
    deslizamiento lateral si la aceleración centrípeta supera μ·g·f_motriz
  * barra de sensores recta: n sensores, paso, distancia al eje (cuello L), mancha de lectura,
    ruido, tiempo de lectura por canal, periodo de control y latencia
  * controladores candidatos (ver control.py)
Todo es reproducible (semilla fija). No modela: zona muerta de motores, rizado PWM, flexión del chasis.
"""
from dataclasses import dataclass, field, replace
import math
import numpy as np

G = 9.81


# ------------------------------------------------------------------ motor
@dataclass(frozen=True)
class Motor:
    nombre: str
    v_nom: float      # V
    rpm0: float       # RPM sin carga a v_nom (salida de la reductora)
    ts: float         # par de bloqueo a v_nom, N·m (salida)
    i_s: float        # corriente de bloqueo a v_nom, A
    i0: float         # corriente sin carga, A
    masa: float       # kg
    fuente: str = ""

    @property
    def R(self):  # resistencia de armadura
        return self.v_nom / self.i_s

    @property
    def w0(self):  # rad/s a v_nom
        return self.rpm0 * 2 * math.pi / 60

    @property
    def ke(self):  # V·s/rad (referido a la salida)
        return (self.v_nom - self.i0 * self.R) / self.w0

    @property
    def kt(self):  # N·m/A (referido a la salida, incluye eficiencia de la reductora)
        return self.ts / (self.i_s - self.i0)

    def par(self, v, w):
        """Par en la salida y corriente para voltaje promedio v y velocidad w (rad/s)."""
        i = (v - self.ke * w) / self.R
        perdida = self.i0 * math.copysign(1.0, w) if abs(w) > 1e-3 else 0.0
        return self.kt * (i - perdida), i


KGCM = 0.0980665  # N·m por kg·cm

# Datos de ficha (Pololu, tabla "micro metal gearmotors"; valores de bloqueo extrapolados por Pololu)
MOTORES = {
    "Pololu HPCB 12V 10:1": Motor("Pololu HPCB 12V 10:1", 12.0, 3400, 0.17 * KGCM, 0.75, 0.08, 0.0095, "pololu.com (#3037; tabla micro metal gearmotors)"),
    "Pololu HPCB 12V 15:1": Motor("Pololu HPCB 12V 15:1", 12.0, 2200, 0.25 * KGCM, 0.75, 0.08, 0.0095, "pololu.com (tabla micro metal gearmotors)"),
    "Pololu HPCB 6V 10:1":  Motor("Pololu HPCB 6V 10:1", 6.0, 3300, 0.17 * KGCM, 1.5, 0.15, 0.0095, "pololu.com #3061"),
    "Pololu HPCB 6V 15:1":  Motor("Pololu HPCB 6V 15:1", 6.0, 2100, 0.25 * KGCM, 1.5, 0.17, 0.0095, "pololu.com tabla"),
    "Pololu HP 6V 10:1":    Motor("Pololu HP 6V 10:1", 6.0, 3100, 0.22 * KGCM, 1.6, 0.10, 0.0095, "pololu.com tabla"),
    "Pololu HPCB 6V 30:1":  Motor("Pololu HPCB 6V 30:1", 6.0, 1100, 0.45 * KGCM, 1.5, 0.17, 0.0095, "pololu.com tabla"),
    # GA12-N20 6 V 1000 RPM (UNIT): solo RPM y "par ≥ 0.15 kg·cm" y I0 ≤ 0.2 A publicados.
    # Bloqueo SUPUESTO para poder simular (PENDIENTE de medición): 0.67 A y 0.30 kg·cm.
    "GA12-N20 6V 1000RPM (supuesto)": Motor("GA12-N20 6V 1000RPM (supuesto)", 6.0, 1000, 0.30 * KGCM, 0.67, 0.2, 0.010, "UNIT + SUPUESTOS"),
}


# ------------------------------------------------------------------ robot
@dataclass(frozen=True)
class Robot:
    motor: Motor
    v_bat: float = 7.4            # V en el bus de motores
    v_max_motor: float = 99.0     # límite de voltaje promedio en el motor (6.0 para motores de 6 V en 2S)
    diam: float = 0.033           # m, diámetro de rueda
    W: float = 0.085              # m, separación entre ruedas
    masa: float = 0.20            # kg total
    radio_giro: float = 0.045     # m, radio de giro para la inercia de guiñada
    f_motriz: float = 0.70        # fracción del peso sobre las ruedas motrices
    mu: float = 0.80              # coeficiente de fricción llanta-fórmica (SUPUESTO)
    L: float = 0.100              # m, cuello: eje -> barra de sensores
    n_sens: int = 12
    paso: float = 0.008           # m
    mancha: float = 0.003         # m, radio de la zona que ve cada sensor
    ruido: float = 0.03           # desviación estándar de la lectura normalizada
    t_canal: float = 40e-6        # s por canal leído (incluye mux y ADC) (SUPUESTO, medir)
    t_emisor: float = 100e-6      # s de establecimiento al encender/apagar emisores (5·20 µs de ficha)
    resta_ambiente: bool = True
    T_ctrl: float = 0.001         # s, periodo de control

    @property
    def r(self):
        return self.diam / 2

    @property
    def J(self):
        return self.masa * self.radio_giro ** 2

    def t_lectura(self):
        k = 2 if self.resta_ambiente else 1
        return k * (self.n_sens * self.t_canal + self.t_emisor)

    def v_libre(self):
        v = min(self.v_bat, self.v_max_motor)
        return v / self.motor.v_nom * self.motor.w0 * self.r


# ------------------------------------------------------------------ pista
@dataclass
class Pista:
    xy: np.ndarray        # (N,2) línea central cada ds
    th: np.ndarray        # rumbo
    s: np.ndarray         # longitud de arco
    hueco: np.ndarray     # bool
    kappa: np.ndarray     # curvatura con signo (+ izquierda)
    cerrada: bool
    nombre: str = ""

    @property
    def largo(self):
        return float(self.s[-1])


class Constructor:
    def __init__(self, x=0.15, y=0.15, th=0.0, ds=0.002):
        self.ds = ds
        self.p = [(x, y, th, False, 0.0)]

    def _avanza(self, n, dth, hueco=False, k=0.0):
        x, y, th, _, _ = self.p[-1]
        for _ in range(n):
            th += dth / 2
            x += self.ds * math.cos(th)
            y += self.ds * math.sin(th)
            th += dth / 2
            self.p.append((x, y, th, hueco, k))
        return self

    def recta(self, L, hueco=False):
        return self._avanza(max(1, round(L / self.ds)), 0.0, hueco, 0.0)

    def arco(self, R, grados):
        ang = math.radians(grados)
        n = max(1, round(abs(ang) * R / self.ds))
        return self._avanza(n, ang / n, False, math.copysign(1 / R, ang))

    def pista(self, nombre, cerrada=True):
        a = np.array(self.p, dtype=object)
        xy = np.array([[q[0], q[1]] for q in self.p], float)
        th = np.array([q[2] for q in self.p], float)
        hu = np.array([q[3] for q in self.p], bool)
        ka = np.array([q[4] for q in self.p], float)
        s = np.arange(len(self.p)) * self.ds
        return Pista(xy, th, s, hu, ka, cerrada, nombre)


def pistas_reglamento():
    """Circuitos cerrados dentro de 2.44 x 1.22 m, sin cruces, curvas de radio >= 150 mm,
    secciones en U y discontinuidades de 5 mm. Son EJEMPLOS: la pista real es desconocida."""
    out = []
    # P1: óvalo largo con huecos (rectas de ~1.6 m, U de 400 mm)
    c = Constructor(0.45, 0.20)
    c.recta(0.79).recta(0.005, True).recta(0.785).arco(0.40, 180).recta(0.6).recta(0.005, True).recta(0.975).arco(0.40, 180)
    out.append(c.pista("P1 óvalo (U R400)"))
    # P2: técnica, curvas de R 150-250 y S
    c = Constructor(0.25, 0.20)
    (c.recta(0.9).arco(0.15, 80).arco(0.25, -80).recta(0.30).arco(0.15, 80).arco(0.15, 80).recta(0.25)
       .recta(0.005, True).recta(0.40).arco(0.20, 90).recta(0.10).arco(0.15, -70).arco(0.15, 70)
       .recta(0.12))
    out.append(c.pista("P2 técnica (R150-250)", cerrada=False))
    # P3: serpentina con rectas medianas y U de R 200
    c = Constructor(0.20, 0.15)
    (c.recta(1.4).arco(0.20, 180).recta(0.6).recta(0.005, True).recta(0.595).arco(0.20, -180).recta(1.0))
    out.append(c.pista("P3 serpentina (U R200)", cerrada=False))
    return out
