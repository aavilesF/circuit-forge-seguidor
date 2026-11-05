"""V2 · Modelo de hundimiento del chasis por la compresión de las llantas (lo usan sim/v2/fase35.py y el CAD).

El chasis se apoya en 3 puntos: las 2 llantas motrices (y = ±Y_RUEDA, x = 0) y la bola de acero de la rueda loca
(x = X_BOLA, y = 0; rígida). Si la llanta izquierda se comprime dL y la derecha dR, cada punto (x, y) del chasis baja

    s(x, y) = (1 − x / X_BOLA) · [ (dL + dR) / 2 + (dL − dR) / 2 · y / Y_RUEDA ]

(plano por los 3 apoyos). Detrás del eje (x < 0) el factor es > 1: la parte trasera de la cámara baja MÁS que el eje.
Delante de la bola (x > X_BOLA) el chasis SUBE cuando las llantas se comprimen y BAJA cuando se descargan (frenado).

Las llantas se modelan como resortes lineales: d = N / k. La rigidez k sale del supuesto de diseño "la llanta se comprime
DELTA_DISENO con la carga estática máxima (succión de cámara cerrada)". Unidades: m, N, kg, m/s²."""
from __future__ import annotations

G0 = 9.81


def cargas_ruedas(m, x_cg, h, b, W, Fs, x_s, ax=0.0, ay=0.0):
    """Cargas normales (izquierda, derecha) de las llantas. ax > 0 acelera (carga pasa a las llantas), ay > 0 gira a la
    izquierda (carga pasa a la llanta derecha). b: distancia eje-bola; W: vía."""
    N = (m * G0 * (b - x_cg) + Fs * (b - x_s) + m * ax * h) / b
    dN = m * ay * h / W
    return max(N / 2 - dN, 0.0), max(N / 2 + dN, 0.0)


def hundimiento(x, y, dL, dR, x_bola, y_rueda):
    return (1 - x / x_bola) * ((dL + dR) / 2 + (dL - dR) / 2 * y / y_rueda)


def casos_carga(a_acc, a_fr, ay_max):
    """(nombre, ax, ay): estática, aceleración, frenado, curva a la izquierda y derecha, y combinados al 70 %."""
    return [("estatico", 0.0, 0.0), ("acelera", a_acc, 0.0), ("frena", -a_fr, 0.0),
            ("curva_izq", 0.0, ay_max), ("curva_der", 0.0, -ay_max),
            ("acelera_curva_izq", 0.7 * a_acc, 0.7 * ay_max), ("acelera_curva_der", 0.7 * a_acc, -0.7 * ay_max),
            ("frena_curva_izq", -0.7 * a_fr, 0.7 * ay_max), ("frena_curva_der", -0.7 * a_fr, -0.7 * ay_max)]


class Suspension:
    """Rigidez calibrada con el supuesto de diseño y envolvente de hundimiento sobre los casos de carga."""

    def __init__(self, m, x_cg, h, b, W, y_rueda, x_s, F_max, delta_diseno, a_acc, a_fr, ay_max, sin_succion=(4.0, 5.0, 6.0)):
        self.m, self.x_cg, self.h, self.b, self.W, self.yr, self.x_s = m, x_cg, h, b, W, y_rueda, x_s
        self.F_max = F_max
        N0 = sum(cargas_ruedas(m, x_cg, h, b, W, F_max, x_s)) / 2
        self.k = N0 / delta_diseno                                 # N/m por llanta
        self.casos = casos_carga(a_acc, a_fr, ay_max)
        self.casos_sin = casos_carga(*sin_succion)                 # (a_acc, a_fr, ay_max) sin succión

    def compresiones(self, Fs, ax=0.0, ay=0.0):
        NL, NR = cargas_ruedas(self.m, self.x_cg, self.h, self.b, self.W, Fs, self.x_s, ax, ay)
        return NL / self.k, NR / self.k

    def hundimiento(self, x, y, Fs, ax=0.0, ay=0.0):
        dL, dR = self.compresiones(Fs, ax, ay)
        return hundimiento(x, y, dL, dR, self.b, self.yr)

    def envolvente(self, x, y, Fs=None):
        """Máximo hundimiento (lo más que baja el punto) sobre los casos, con la succión Fs (F_max si None)."""
        F = self.F_max if Fs is None else Fs
        return max(self.hundimiento(x, y, F, ax, ay) for _, ax, ay in self.casos)

    def envolvente_sin_succion(self, x, y):
        """Lo más que baja el punto con el ventilador apagado (casos de carga sin succión, aceleraciones menores)."""
        return max(self.hundimiento(x, y, 0.0, ax, ay) for _, ax, ay in self.casos_sin)
