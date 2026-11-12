"""Geometría DEFINITIVA del robot (fuente única para la PCB, el CAD y las verificaciones mecánicas).

Todo sale de config/robot_maestro.yaml (secciones geometria, barras y mecanica). Marco del robot en mm:
x hacia adelante desde el centro del eje de ruedas, y a la izquierda, z hacia arriba desde el piso."""
from __future__ import annotations

import math
import os
import sys

import numpy as np

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(RAIZ, "sim"))
import config as CF  # noqa: E402


def polar(r, ang_deg):
    a = math.radians(ang_deg)
    return r * math.cos(a), r * math.sin(a)


class Geometria:
    def __init__(self, cfg):
        self.cfg = cfg
        g, m = cfg["geometria"], cfg["mecanica"]
        arq = cfg["arquitectura"]
        self.barra = cfg["barras"][arq["barra"]]
        self.L = g["L_cuello"]                                   # m
        self.n_sensores = self.barra["n"]
        self.paso = self.barra["paso"]                           # m
        self.W = g["W_via"] * 1000
        self.D = g["D_llanta"] * 1000
        self.ancho_llanta = g["ancho_llanta"] * 1000
        self.x_apoyo = g["x_apoyo"] * 1000
        self.m = m
        self.t_pcb = m["pcb_espesor"]
        self.z_pcb_inf = m["z_pcb_inferior"]
        self.z_pcb_sup = self.z_pcb_inf + self.t_pcb
        self.r_rueda = self.D / 2
        self.z_eje = self.r_rueda
        sx, sz = m["motor_seccion"]
        self.motor_sx, self.motor_sz = sx, sz
        self.z_motor_inf = self.z_eje - sz / 2
        self.z_motor_sup = self.z_eje + sz / 2
        self.y_reductora = m["cara_reductora_y"]
        self.y_motor_fin = self.y_reductora - m["largo_reductora"] - m["largo_motor"]   # tapa trasera del motor
        self.y_encoder_fin = self.y_motor_fin - m["largo_encoder"]
        self.r_resistencias_mm = m["r_resistencias"]

    # ---------------------------------------------------------------- sensores
    def sensor(self, i):
        """(x, y, ángulo) en mm y grados del sensor i (0 = el de más a la izquierda), igual que sim/config.sensores."""
        k = i - (self.n_sensores - 1) / 2
        phi = -k * self.paso / self.L
        return self.L * 1000 * math.cos(phi), self.L * 1000 * math.sin(phi), math.degrees(phi)

    # ---------------------------------------------------------------- PCB
    def contorno_pcb(self, paso_arco_deg=1.0):
        """Polígono cerrado del contorno (lista de (x, y) mm, antihorario) y el arco exterior como (centro, r, a0, a1)."""
        c = self.m["contorno"]
        ym, ro = c["y_max"], c["r_exterior"]
        xo = math.sqrt(ro ** 2 - ym ** 2)
        x_flare = c["x_cuello_fin"] + (ym - c["y_cuello"]) * 0.79       # fin del ensanche (pendiente fija)
        a = math.degrees(math.asin(ym / ro))
        der = [(c["x_trasero"], -c["y_trasero"]), (c["x_hombro"], -c["y_trasero"]), (c["x_cuello"], -c["y_cuello"]),
               (c["x_cuello_fin"], -c["y_cuello"]), (x_flare, -ym), (xo, -ym)]
        arco = [polar(ro, t) for t in np.arange(-a, a + 1e-9, paso_arco_deg)][1:-1]
        izq = [(x, -y) for (x, y) in reversed(der)]
        pts = der + arco + izq
        return pts, dict(r=ro, a0=-a, a1=a, p0=(xo, -ym), p1=(xo, ym))

    def area_pcb_mm2(self):
        pts, _ = self.contorno_pcb(0.25)
        x = np.array([p[0] for p in pts]); y = np.array([p[1] for p in pts])
        return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))

    def centroide_pcb_mm(self):
        pts, _ = self.contorno_pcb(0.25)
        x = np.array([p[0] for p in pts]); y = np.array([p[1] for p in pts])
        cr = x * np.roll(y, -1) - np.roll(x, -1) * y
        A = cr.sum() / 2
        return float(((x + np.roll(x, -1)) * cr).sum() / (6 * A)), float(((y + np.roll(y, -1)) * cr).sum() / (6 * A))

    def agujeros_soportes_mm(self):
        out = []
        for lado in (1, -1):
            for x, ya in self.m["agujeros_soporte"]:
                out.append((x, lado * ya))
        return out

    def agujeros_rueda_loca_mm(self):
        return [tuple(p) for p in self.m["agujeros_rueda_loca"]]

    def zonas_prohibidas_sup(self):
        """Rectángulos (x0, y0, x1, y1) de la cara superior que ocupan los soportes, encoders y conectores del cable."""
        z = []
        for s in (1, -1):
            y0, y1 = sorted((s * (self.y_motor_fin), s * self.y_reductora))
            z.append((-12.5, y0, 12.5, y1))                         # soporte del motor
            e0, e1 = sorted((s * self.y_encoder_fin, s * self.y_motor_fin))
            z.append((-7.0, e0, 7.0, e1))                           # tarjeta del encoder (sobresale hacia abajo)
            c0, c1 = sorted((s * (self.y_encoder_fin - 5.0), s * self.y_encoder_fin))
            z.append((-3.5, c0, 3.5, c1))                           # clavija del cable (entrada superior)
        return z


def cargar(cfg=None):
    return Geometria(cfg or CF.cargar())


if __name__ == "__main__":
    G = cargar()
    print("área PCB %.0f mm², centroide %s, z PCB %.2f-%.2f mm, motor y %.1f..%.1f, encoder hasta %.1f" % (
        G.area_pcb_mm2(), tuple(round(v, 1) for v in G.centroide_pcb_mm()), G.z_pcb_inf, G.z_pcb_sup,
        G.y_motor_fin, G.y_reductora, G.y_encoder_fin))
    for i in (0, 7, 8, 15):
        print("sensor", i, tuple(round(v, 2) for v in G.sensor(i)))
