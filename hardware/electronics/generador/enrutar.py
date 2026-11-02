#!/usr/bin/env python3
"""Enrutador de rejilla (A*, 2 capas de señal F.Cu/B.Cu con vías; In1 = plano GND, In2 = plano +3V3).

Separaciones EXACTAS en los centros de celda (rejilla de 0.05 mm) contra pads (rectángulo/redondeado/óvalo/círculo
girados), pistas y vías ya colocadas, agujeros y borde. Margen propio de 0.03 mm sobre la separación de la regla
para cubrir la discretización. Entrada: geometria_pcb.json + plan_pcb.json; salida: rutas.json."""
from __future__ import annotations

import heapq
import json
import math
import random
import os
import sys
import time

import numpy as np
from numba import njit
from scipy import ndimage
from matplotlib.path import Path

AQUI = os.path.dirname(os.path.abspath(__file__))
G = 0.05                                   # mm por celda
CL = 0.15                                  # separación de la regla de la placa (todas las clases: 0.15 mm)
MARGEN = 0.03
BORDE = 0.30                               # cobre al borde
H_PISTA = [0.10, 0.15, 0.20, 0.25, 0.40]   # medias anchuras de pista disponibles (0.2, 0.3, 0.4, 0.5, 0.8 mm)
R_VIA = 0.275                              # vía 0.55/0.25 mm (anillo 0.15 mm)
TALADRO_VIA = 0.25
COSTO_VIA = 30.0                           # celdas (1.5 mm)
PLANOS = {"GND", "+3V3"}
ESCAPES = False                            # escape tipo hueso del MCU (probado: empeora; queda desactivado)
ANCHO_CLASE = {"Potencia": 0.40, "Motor": 0.25, "Alimentacion": 0.20, "Default": 0.10}
# Bus PWM del MCU (pines 30-33, paso 0.5 mm) al DRV8833 (pines 16, 15, 10, 9): se traza a mano antes que todo, como
# 4 pistas paralelas de 0.2 mm en F.Cu que se abren a 45° frente al DRV8833 (par A hacia arriba, par B hacia abajo).
# El enrutador automático encerraba alguno de los 4 pines entre las vías de sus vecinos.
BUS_PWM = (("PWM_AIN1", 0), ("PWM_AIN2", 1), ("PWM_BIN1", 0), ("PWM_BIN2", 1))   # (red, orden desde afuera)
X_BIFURCA = 133.0                          # mm (KiCad): inicio del abanico de 45° frente al DRV8833


def clase_de(red, clases):
    import fnmatch
    for nombre, c in clases.items():
        if nombre == "Default":
            continue
        for pat in c["patrones"]:
            if fnmatch.fnmatchcase(red, pat):
                return nombre
    return "Default"


# ------------------------------------------------------------------------------------------- geometría
def dist_pad(px, py, pad):
    """Distancia con signo de los puntos (px, py) al pad (negativa adentro)."""
    a = -math.radians(pad["ang"])
    dx, dy = px - pad["X"], py - pad["Y"]
    # el ángulo de KiCad es antihorario en pantalla con Y hacia abajo
    ca, sa = math.cos(a), math.sin(a)
    lx = dx * ca + dy * sa
    ly = -dx * sa + dy * ca
    w, h = pad["w"] / 2, pad["h"] / 2
    if pad["forma"] == "circle":
        return np.hypot(dx, dy) - w
    r = 0.0
    if pad["forma"] == "oval":
        r = min(w, h)
    elif pad["forma"] == "roundrect":
        r = min(pad.get("radio", 0.0), w, h)
    qx = np.abs(lx) - (w - r); qy = np.abs(ly) - (h - r)
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r


def dist_seg(px, py, x1, y1, x2, y2):
    vx, vy = x2 - x1, y2 - y1
    L2 = vx * vx + vy * vy
    if L2 < 1e-12:
        return np.hypot(px - x1, py - y1)
    t = np.clip(((px - x1) * vx + (py - y1) * vy) / L2, 0, 1)
    return np.hypot(px - (x1 + t * vx), py - (y1 + t * vy))


class Rejilla:
    def __init__(self, plan, geom):
        xs = [p[0] for p in plan["contorno"]]; ys = [p[1] for p in plan["contorno"]]
        self.x0 = math.floor(min(xs) / G) * G - 1.0; self.y0 = math.floor(min(ys) / G) * G - 1.0
        self.W = int((max(xs) - self.x0 + 1.0) / G) + 1; self.H = int((max(ys) - self.y0 + 1.0) / G) + 1
        self.clases = plan["clases"]
        # ocupación por clase de anchura (pistas) y para vías: -1 libre, -2 bloqueado, k = red k
        self.nh = len(H_PISTA)
        self.cov = np.full((self.nh + 1, 2, self.H, self.W), -1, np.int16)    # índice nh = vías
        self.nets = {}
        self.cobre = {}                                                       # red -> lista de objetos propios
        self.no_via = np.zeros((self.H, self.W), bool)
        self.pistas, self.vias = [], []
        self._borde(plan)
        for pad in geom["pads"]:
            self.agregar_pad(pad)
        bx, by = plan["agujero_bola"]["centro"]; br = plan["agujero_bola"]["diametro"] / 2
        self.bloquear_circulo(bx, by, br)

    def idx(self, red):
        if red not in self.nets:
            self.nets[red] = len(self.nets) + 1
        return self.nets[red]

    def ventana(self, x0, y0, x1, y1):
        i0 = max(int((x0 - self.x0) / G) - 1, 0); i1 = min(int((x1 - self.x0) / G) + 2, self.W)
        j0 = max(int((y0 - self.y0) / G) - 1, 0); j1 = min(int((y1 - self.y0) / G) + 2, self.H)
        X = self.x0 + np.arange(i0, i1) * G; Y = self.y0 + np.arange(j0, j1) * G
        return i0, i1, j0, j1, np.meshgrid(X, Y)

    def _borde(self, plan):
        X = self.x0 + np.arange(self.W) * G; Y = self.y0 + np.arange(self.H) * G
        XX, YY = np.meshgrid(X, Y)
        dentro = Path(plan["contorno"]).contains_points(np.c_[XX.ravel(), YY.ravel()]).reshape(self.H, self.W)
        d = ndimage.distance_transform_edt(dentro) * G
        for c in range(self.nh + 1):
            r = (R_VIA if c == self.nh else H_PISTA[c]) + BORDE + MARGEN
            self.cov[c, :, d < r] = -2
        self.no_via |= d < R_VIA + BORDE + MARGEN

    def bloquear_circulo(self, x, y, r):
        i0, i1, j0, j1, (XX, YY) = self.ventana(x - r - 1, y - r - 1, x + r + 1, y + r + 1)
        d = np.hypot(XX - x, YY - y) - r
        for c in range(self.nh + 1):
            hc = R_VIA if c == self.nh else H_PISTA[c]
            m = d < 0.25 + hc + MARGEN
            self.cov[c, :, j0:j1, i0:i1][:, m] = -2
        self.no_via[j0:j1, i0:i1] |= d < 0.25 + R_VIA + MARGEN

    def _marcar(self, capas, red, i0, i1, j0, j1, d):
        k = self.idx(red) if red else -2
        for c in range(self.nh + 1):
            hc = R_VIA if c == self.nh else H_PISTA[c]
            m = d < CL + hc + MARGEN
            for L in capas:
                sub = self.cov[c, L, j0:j1, i0:i1]
                v = sub[m]
                if k == -2:
                    v[:] = -2
                else:
                    v = np.where(v == -1, k, np.where(v == k, k, -2)).astype(np.int16)
                sub[m] = v

    def agregar_pad(self, pad):
        if pad.get("npth"):
            self.bloquear_circulo(pad["X"], pad["Y"], max(pad["w"], pad["taladro"]) / 2)
            return
        capas = [0 if c == "F" else 1 for c in pad["capas"]]
        r = max(pad["w"], pad["h"]) / 2 + CL + 0.5
        i0, i1, j0, j1, (XX, YY) = self.ventana(pad["X"] - r, pad["Y"] - r, pad["X"] + r, pad["Y"] + r)
        d = dist_pad(XX, YY, pad)
        self._marcar(capas, pad["red"], i0, i1, j0, j1, d)
        self.no_via[j0:j1, i0:i1] |= d < R_VIA + CL + MARGEN if not pad["red"] else d < R_VIA + 0.05
        if pad["red"]:
            self.cobre.setdefault(pad["red"], []).append(("pad", pad, capas))
        if pad["taladro"] > 0:
            self.no_via[j0:j1, i0:i1] |= np.hypot(XX - pad["X"], YY - pad["Y"]) < pad["taladro"] / 2 + 0.25 + R_VIA

    def agregar_pista(self, red, L, x1, y1, x2, y2, h, fija=False):
        r = h + CL + 0.6
        i0, i1, j0, j1, (XX, YY) = self.ventana(min(x1, x2) - r, min(y1, y2) - r, max(x1, x2) + r, max(y1, y2) + r)
        d = dist_seg(XX, YY, x1, y1, x2, y2) - h
        self._marcar([L], red, i0, i1, j0, j1, d)
        self.cobre.setdefault(red, []).append(("pista", (x1, y1, x2, y2, h), [L]))
        self.pistas.append(dict(red=red, capa="FB"[L], x1=round(x1, 4), y1=round(y1, 4), x2=round(x2, 4), y2=round(y2, 4), w=round(2 * h, 3)))
        if fija:
            self.pistas[-1]["fija"] = True

    def agregar_via(self, red, x, y):
        r = R_VIA + CL + 0.6
        i0, i1, j0, j1, (XX, YY) = self.ventana(x - r, y - r, x + r, y + r)
        d = np.hypot(XX - x, YY - y) - R_VIA
        self._marcar([0, 1], red, i0, i1, j0, j1, d)
        self.no_via[j0:j1, i0:i1] |= np.hypot(XX - x, YY - y) < 2 * R_VIA + 0.25
        self.cobre.setdefault(red, []).append(("via", (x, y), [0, 1]))
        self.vias.append(dict(red=red, x=round(x, 4), y=round(y, 4), d=2 * R_VIA, t=TALADRO_VIA))

    # ---------------------------------------------------------------------- fuentes y destinos
    def mascara_objetos(self, objs, i0, i1, j0, j1):
        """Celdas (2, h, w) dentro de los pads/vías/ejes de pista dados (ventana)."""
        X = self.x0 + np.arange(i0, i1) * G; Y = self.y0 + np.arange(j0, j1) * G
        XX, YY = np.meshgrid(X, Y)
        m = np.zeros((2, j1 - j0, i1 - i0), bool)
        for tipo, o, capas in objs:
            if tipo == "pad":
                d = dist_pad(XX, YY, o) <= -0.02
            elif tipo == "via":
                d = np.hypot(XX - o[0], YY - o[1]) <= R_VIA * 0.7
            else:
                d = dist_seg(XX, YY, *o[:4]) <= G * 0.75
            for L in capas:
                m[L] |= d
        return m


@njit(cache=True)
def astar(paso_ok, via_ok, fuente, destino, costo_via, hx, hy, giro=2.0):
    """A* en una ventana. paso_ok (2,h,w) bool, via_ok (h,w) bool, fuente/destino (2,h,w) bool.
    hx, hy: centro aproximado del destino (celdas) para la heurística. Devuelve la ruta como arreglo (n,3)."""
    nL, h, w = paso_ok.shape
    N = nL * h * w
    g = np.full(N, 1e30, np.float32)
    prev = np.full(N, -1, np.int64)
    cerrado = np.zeros(N, np.bool_)
    heap_c = np.empty(N // 2 + 1000, np.float32)
    heap_i = np.empty(N // 2 + 1000, np.int64)
    n = 0
    for L in range(nL):
        for y in range(h):
            for x in range(w):
                if fuente[L, y, x] and paso_ok[L, y, x]:
                    s = (L * h + y) * w + x
                    g[s] = 0.0
                    f = math.sqrt((x - hx) ** 2 + (y - hy) ** 2)
                    # push
                    i = n; n += 1
                    heap_c[i] = f; heap_i[i] = s
                    while i > 0:
                        p = (i - 1) // 2
                        if heap_c[p] <= heap_c[i]:
                            break
                        heap_c[p], heap_c[i] = heap_c[i], heap_c[p]; heap_i[p], heap_i[i] = heap_i[i], heap_i[p]
                        i = p
    dxs = np.array([1, -1, 0, 0, 1, 1, -1, -1]); dys = np.array([0, 0, 1, -1, 1, -1, 1, -1])
    cs = np.array([1.0, 1.0, 1.0, 1.0, 1.4142, 1.4142, 1.4142, 1.4142])
    fin = -1
    while n > 0:
        s = heap_i[0]
        n -= 1
        heap_c[0] = heap_c[n]; heap_i[0] = heap_i[n]
        i = 0
        while True:
            l = 2 * i + 1; r = l + 1; m = i
            if l < n and heap_c[l] < heap_c[m]:
                m = l
            if r < n and heap_c[r] < heap_c[m]:
                m = r
            if m == i:
                break
            heap_c[m], heap_c[i] = heap_c[i], heap_c[m]; heap_i[m], heap_i[i] = heap_i[i], heap_i[m]
            i = m
        if cerrado[s]:
            continue
        cerrado[s] = True
        L = s // (h * w); y = (s // w) % h; x = s % w
        if destino[L, y, x]:
            fin = s
            break
        gs = g[s]
        ps = prev[s]
        pdx = 0; pdy = 0
        if ps >= 0 and ps // (h * w) == L:
            pdx = x - ps % w; pdy = y - (ps // w) % h
        for k in range(9):
            if k < 8:
                nx = x + dxs[k]; ny = y + dys[k]; nL2 = L; c = cs[k]
                if nx < 0 or ny < 0 or nx >= w or ny >= h:
                    continue
                if not paso_ok[nL2, ny, nx]:
                    continue
                if k >= 4:   # diagonal: no cortar esquinas bloqueadas
                    if not paso_ok[nL2, y, nx] or not paso_ok[nL2, ny, x]:
                        continue
            else:
                if nL < 2 or not via_ok[y, x]:
                    continue
                nx = x; ny = y; nL2 = 1 - L; c = costo_via
                if not paso_ok[nL2, ny, nx]:
                    continue
            t = (nL2 * h + ny) * w + nx
            if cerrado[t]:
                continue
            if k < 8 and (pdx != 0 or pdy != 0) and (dxs[k] != pdx or dys[k] != pdy):
                c += giro
            ng = gs + c
            if ng < g[t]:
                g[t] = ng; prev[t] = s
                f = ng + math.sqrt((nx - hx) ** 2 + (ny - hy) ** 2)
                if n >= heap_c.shape[0]:
                    return np.zeros((0, 3), np.int64)
                i = n; n += 1
                heap_c[i] = f; heap_i[i] = t
                while i > 0:
                    p = (i - 1) // 2
                    if heap_c[p] <= heap_c[i]:
                        break
                    heap_c[p], heap_c[i] = heap_c[i], heap_c[p]; heap_i[p], heap_i[i] = heap_i[i], heap_i[p]
                    i = p
    if fin < 0:
        return np.zeros((0, 3), np.int64)
    cnt = 0
    s = fin
    while s >= 0:
        cnt += 1; s = prev[s]
    out = np.zeros((cnt, 3), np.int64)
    s = fin; k = cnt - 1
    while s >= 0:
        out[k, 0] = s // (h * w); out[k, 1] = (s // w) % h; out[k, 2] = s % w
        k -= 1; s = prev[s]
    return out


class Enrutador:
    def __init__(self):
        self.plan = json.load(open(os.path.join(AQUI, "plan_pcb.json")))
        self.geom = json.load(open(os.path.join(AQUI, "geometria_pcb.json")))
        t = time.time()
        self.R = Rejilla(self.plan, self.geom)
        print(f"rejilla {self.R.W}×{self.R.H} ({time.time() - t:.1f} s)")
        self.pads_red = {}
        for p in self.geom["pads"]:
            if p["red"] and not p.get("npth"):
                self.pads_red.setdefault(p["red"], []).append(p)
        self.fallas = []
        self.prerruteadas = set()
        self.azar = random.Random(7)              # reintentos reproducibles

    def libre(self, red, L, x1, y1, x2, y2, h):
        """¿El eje del tramo cae solo en celdas libres o de la misma red (clase de anchura h)?"""
        R = self.R
        k = R.idx(red)
        i0, i1, j0, j1, (XX, YY) = R.ventana(min(x1, x2) - 0.2, min(y1, y2) - 0.2, max(x1, x2) + 0.2, max(y1, y2) + 0.2)
        m = dist_seg(XX, YY, x1, y1, x2, y2) <= G * 0.5
        c = R.cov[H_PISTA.index(h), L, j0:j1, i0:i1][m]
        return bool(np.all((c == -1) | (c == k)))

    def prerrutas(self):
        pad = {(p["ref"], p["red"]): p for p in self.geom["pads"] if p["ref"] in ("U1", "U3") and p["red"]}
        h = 0.10
        for red, orden in BUS_PWM:
            a, b = pad[("U1", red)], pad[("U3", red)]
            x1 = X_BIFURCA - 0.2 * orden
            dy = b["Y"] - a["Y"]
            pts = [(a["X"], a["Y"]), (x1, a["Y"]), (x1 - abs(dy), b["Y"]), (b["X"], b["Y"])]
            segs = list(zip(pts, pts[1:]))
            if all(self.libre(red, 0, *p, *q, h) for p, q in segs):
                for p, q in segs:
                    self.R.agregar_pista(red, 0, *p, *q, h, fija=True)
                self.prerruteadas.add(red)
            else:
                print(f"  prerruta {red}: choca, se deja al enrutador automático")
        print(f"prerrutas: {sorted(self.prerruteadas)}")

    def conectar(self, red, objs_fuente, pad_dest, h, permitir_via=True, margen=12.0, destino_via=False, zona_via=None,
                 objs_dest=None, anillo=None):
        R = self.R
        cls = H_PISTA.index(h)
        k = R.idx(red)
        if pad_dest is not None and objs_dest is None:
            objs_dest = [("pad", pad_dest, [0 if c == "F" else 1 for c in pad_dest["capas"]])]
        xs, ys = [], []
        dx_, dy_ = [], []
        for tipo, o, _ in (objs_dest or []):
            if tipo == "pad":
                dx_.append(o["X"]); dy_.append(o["Y"])
            elif tipo == "via":
                dx_.append(o[0]); dy_.append(o[1])
            else:
                dx_ += [o[0], o[2]]; dy_ += [o[1], o[3]]
        xs += dx_; ys += dy_
        for tipo, o, _ in objs_fuente:
            if tipo == "pad":
                xs.append(o["X"]); ys.append(o["Y"])
            elif tipo == "via":
                xs.append(o[0]); ys.append(o[1])
            else:
                xs += [o[0], o[2]]; ys += [o[1], o[3]]
        if destino_via:
            margen = 6.0
        i0, i1, j0, j1, _ = R.ventana(min(xs) - margen, min(ys) - margen, max(xs) + margen, max(ys) + margen)
        cov = R.cov[cls, :, j0:j1, i0:i1]
        paso = (cov == -1) | (cov == k)
        cv = R.cov[R.nh, :, j0:j1, i0:i1]
        via_ok = ((cv[0] == -1) | (cv[0] == k)) & ((cv[1] == -1) | (cv[1] == k)) & ~R.no_via[j0:j1, i0:i1]
        fuente = R.mascara_objetos(objs_fuente, i0, i1, j0, j1)
        if destino_via:
            vz = via_ok.copy()
            if zona_via is not None:
                X = R.x0 + np.arange(i0, i1) * G; Y = R.y0 + np.arange(j0, j1) * G
                XX, YY = np.meshgrid(X, Y)
                vz &= (XX >= zona_via[0]) & (XX <= zona_via[2]) & (YY >= zona_via[1]) & (YY <= zona_via[3])
                if anillo is not None:
                    vz &= np.maximum(np.abs(XX - anillo[0]), np.abs(YY - anillo[1])) >= anillo[2]
            destino = np.stack([vz, vz]) & paso
            destino &= ~fuente
            hx, hy = (np.mean(xs) - R.x0) / G - i0, (np.mean(ys) - R.y0) / G - j0
        else:
            destino = R.mascara_objetos(objs_dest, i0, i1, j0, j1)
            hx, hy = (np.mean(dx_) - R.x0) / G - i0, (np.mean(dy_) - R.y0) / G - j0
        if not permitir_via:
            via_ok = np.zeros_like(via_ok)
        ruta = astar(paso, via_ok, fuente, destino, COSTO_VIA, hx, hy)
        if len(ruta) == 0:
            return None
        pts = [(int(L), R.x0 + (x + i0) * G, R.y0 + (y + j0) * G) for L, y, x in ruta]
        return pts

    def trazar(self, red, pts, h, pad_dest=None, via_final=False):
        """Convierte la secuencia de celdas en pistas (tramos colineales unidos) y vías."""
        R = self.R
        segs = []
        ini = 0
        for i in range(1, len(pts) + 1):
            fin_tramo = i == len(pts) or pts[i][0] != pts[i - 1][0]
            if fin_tramo:
                tramo = pts[ini:i]
                L = tramo[0][0]
                # unir colineales
                cur = [tramo[0]]
                for p in tramo[1:]:
                    if len(cur) >= 2:
                        a, b = cur[-2], cur[-1]
                        d1 = (round((b[1] - a[1]) / G), round((b[2] - a[2]) / G))
                        d2 = (round((p[1] - b[1]) / G), round((p[2] - b[2]) / G))
                        n1 = math.gcd(abs(d1[0]), abs(d1[1])) or 1; n2 = math.gcd(abs(d2[0]), abs(d2[1])) or 1
                        if (d1[0] // n1, d1[1] // n1) == (d2[0] // n2, d2[1] // n2):
                            cur[-1] = p
                            continue
                    cur.append(p)
                for a, b in zip(cur, cur[1:]):
                    segs.append((L, a[1], a[2], b[1], b[2]))
                if i < len(pts):
                    R.agregar_via(red, pts[i - 1][1], pts[i - 1][2])
                ini = i
        if pad_dest is not None:
            L, x, y = pts[-1]
            segs.append((L, x, y, pad_dest["X"], pad_dest["Y"]))
        if via_final:
            L, x, y = pts[-1]
            R.agregar_via(red, x, y)
        for L, x1, y1, x2, y2 in segs:
            if abs(x1 - x2) > 1e-6 or abs(y1 - y2) > 1e-6:
                R.agregar_pista(red, L, x1, y1, x2, y2, h)

    def abanico(self, red):
        """Cada pad SMD de un plano recibe una vía cercana (pista de 0.3 mm)."""
        for pad in self.pads_red.get(red, []):
            if pad["taladro"] > 0:
                continue
            if pad["ref"].startswith("U3") and pad["pad"] == "17":
                continue                              # PowerPAD: vías térmicas de la huella
            capas = [0 if c == "F" else 1 for c in pad["capas"]]
            ok = False
            zona = None
            if pad["ref"] == "U1":       # vías de alimentación del MCU debajo del encapsulado: libera el anillo exterior
                u1 = next(hh for hh in self.geom["huellas"] if hh["ref"] == "U1")
                zona = (u1["X"] - 2.6, u1["Y"] - 2.6, u1["X"] + 2.6, u1["Y"] + 2.6)
            for h in (0.15, 0.10):
                pts = self.conectar(red, [("pad", pad, capas)], None, h, permitir_via=False, destino_via=True, zona_via=zona)
                if pts:
                    pts = [(pts[0][0], pad["X"], pad["Y"])] + pts
                    self.trazar(red, pts, h, via_final=True)
                    ok = True
                    break
            if not ok:
                self.fallas.append((red, pad["ref"], pad["pad"], "abanico"))

    def red_arbol(self, red, h0, permitir_via=True):
        """Une los pads de la red en el orden del árbol de expansión mínima (tramos cortos primero); cada tramo va
        del cobre de una componente al cobre de la otra."""
        pads = self.pads_red[red]
        n = len(pads)
        comp = list(range(n))

        def raiz(i):
            while comp[i] != i:
                comp[i] = comp[comp[i]]; i = comp[i]
            return i
        objs = {i: [("pad", pads[i], [0 if c == "F" else 1 for c in pads[i]["capas"]])] for i in range(n)}
        # el cobre ya colocado de la red (abanicos/escapes) pertenece al pad del que salió
        for o in self.R.cobre.get(red, []):
            if o[0] != "pad" and len(o) > 3:
                objs[o[3]].append(o[:3])
        if red in self.prerruteadas:          # la prerruta ya une el pad del MCU con el del DRV8833
            iu1 = next(i for i in range(n) if pads[i]["ref"] == "U1")
            iu3 = next(i for i in range(n) if pads[i]["ref"] == "U3")
            comp[iu3] = iu1
            objs[iu1] = objs[iu1] + objs[iu3] + [o[:3] for o in self.R.cobre.get(red, []) if o[0] == "pista" and len(o) == 3]
        aristas = sorted((math.hypot(pads[i]["X"] - pads[j]["X"], pads[i]["Y"] - pads[j]["Y"]), i, j)
                         for i in range(n) for j in range(i + 1, n))
        anchos = [h for h in H_PISTA if h <= h0][::-1]
        for d, i, j in aristas:
            a, b = raiz(i), raiz(j)
            if a == b:
                continue
            hecho = False
            for h in anchos:
                for margen in (8.0, 30.0):
                    antes = len(self.R.cobre.get(red, []))
                    pts = self.conectar(red, objs[a], None, h, permitir_via, margen, objs_dest=objs[b])
                    if pts:
                        self.trazar(red, pts, h)
                        nuevos = self.R.cobre[red][antes:]
                        comp[b] = a
                        objs[a] = objs[a] + objs[b] + [o[:3] for o in nuevos]
                        hecho = True
                        break
                if hecho:
                    break
            if not hecho:
                p = pads[j]
                self.fallas.append((red, p["ref"], p["pad"], "ruta"))
                comp[b] = a
                objs[a] = objs[a] + objs[b]

    def escapes_mcu(self):
        """Escape tipo 'hueso' de cada pin de señal del MCU: pista corta + vía en un anillo a 1.6-3.2 mm del borde
        de los pads, antes de las rutas largas (evita que una ruta temprana encierre un pin)."""
        u1 = next(hh for hh in self.geom["huellas"] if hh["ref"] == "U1")
        cx, cy = u1["X"], u1["Y"]
        pads = [p for p in self.geom["pads"] if p["ref"] == "U1" and p["red"] and p["red"] not in PLANOS
                and p["red"] != "+3V3A"]
        pads.sort(key=lambda p: math.atan2(p["Y"] - cy, p["X"] - cx))
        for paso in (0, 1):
            for k, pad in enumerate(pads):
                if k % 2 != paso:
                    continue
                d0 = 5.6 + 1.0 * paso
                zona_ext = (cx - d0 - 1.6, cy - d0 - 1.6, cx + d0 + 1.6, cy + d0 + 1.6)
                hecho = False
                for h in (0.10,):
                    pts = self.conectar(pad["red"], [("pad", pad, [0])], None, h, permitir_via=False, destino_via=True,
                                        zona_via=zona_ext, anillo=(cx, cy, d0))
                    if pts:
                        pts = [(0, pad["X"], pad["Y"])] + pts
                        antes = len(self.R.cobre.get(pad["red"], []))
                        self.trazar(pad["red"], pts, h, via_final=True)
                        idx = next(i for i, q in enumerate(self.pads_red[pad["red"]]) if q is pad or (q["ref"] == "U1" and q["pad"] == pad["pad"]))
                        self.R.cobre[pad["red"]][antes:] = [tuple(o) + (idx,) for o in self.R.cobre[pad["red"]][antes:]]
                        hecho = True
                        break
                if not hecho:
                    self.fallas.append((pad["red"], "U1", pad["pad"], "escape"))

    def reconstruir(self, quitar):
        """Rejilla nueva con todo el cobre colocado excepto el de las redes en `quitar`."""
        pistas = [x for x in self.R.pistas if x["red"] not in quitar or x.get("fija")]
        vias = [x for x in self.R.vias if x["red"] not in quitar]
        self.R = Rejilla(self.plan, self.geom)
        for v in vias:
            self.R.agregar_via(v["red"], v["x"], v["y"])
        for x in pistas:
            self.R.agregar_pista(x["red"], 0 if x["capa"] == "F" else 1, x["x1"], x["y1"], x["x2"], x["y2"], x["w"] / 2, x.get("fija", False))

    def reparar(self, iteraciones=24, radio=2.5):
        """Arranca y reenruta: por cada falla, quita las redes que tienen cobre cerca del pad que no se pudo unir,
        enruta primero la red fallida y luego las quitadas. Conserva el mejor estado (si empeora, regresa)."""
        def estado():
            return ([dict(x) for x in self.R.pistas], [dict(x) for x in self.R.vias], list(self.fallas))

        def restaurar(st):
            pistas, vias, fallas = st
            self.R = Rejilla(self.plan, self.geom)
            for v in vias:
                self.R.agregar_via(v["red"], v["x"], v["y"])
            for x in pistas:
                self.R.agregar_pista(x["red"], 0 if x["capa"] == "F" else 1, x["x1"], x["y1"], x["x2"], x["y2"], x["w"] / 2, x.get("fija", False))
            self.fallas = list(fallas)
        mejor = estado()
        intentos = {}
        for it in range(iteraciones):
            pend = [f for f in self.fallas if f[0] not in PLANOS]
            if not pend:
                return
            cand = [f for f in pend if intentos.get((f[0], f[1], f[2]), 0) < 4]
            if not cand:
                break
            red, ref, num, _ = cand[0]
            clave = (red, ref, num)
            intentos[clave] = intentos.get(clave, 0) + 1
            pad = next(p for p in self.geom["pads"] if p["ref"] == ref and p["pad"] == num)
            r = radio * (1.0 + 0.5 * (intentos[clave] - 1))
            vecinas = set()
            for x in self.R.pistas:
                if x["red"] not in PLANOS and x["red"] != red and \
                        dist_seg(np.array(pad["X"]), np.array(pad["Y"]), x["x1"], x["y1"], x["x2"], x["y2"]) < r:
                    vecinas.add(x["red"])
            for v in self.R.vias:
                if v["red"] not in PLANOS and v["red"] != red and math.hypot(v["x"] - pad["X"], v["y"] - pad["Y"]) < r:
                    vecinas.add(v["red"])
            quitar = {red} | vecinas | {f[0] for f in pend}
            self.reconstruir(quitar)
            self.fallas = [f for f in self.fallas if f[0] not in quitar]
            orden = [red] + sorted(quitar - {red}, key=lambda q: 0 if q in {f[0] for f in pend} else 1)
            if intentos[clave] > 1:                   # en los reintentos, otro orden para las redes arrancadas
                resto = orden[1:]
                self.azar.shuffle(resto)
                orden = [red] + resto
            for q in orden:
                c = clase_de(q, self.plan["clases"])
                self.red_arbol(q, ANCHO_CLASE[c], permitir_via=True)
            n = len([f for f in self.fallas if f[0] not in PLANOS])
            print(f"  reparación {it + 1}: {red} radio {r:.1f} (quitadas {len(quitar) - 1}) -> {n} fallas")
            if n < len([f for f in mejor[2] if f[0] not in PLANOS]):
                mejor = estado()
            elif n > len([f for f in mejor[2] if f[0] not in PLANOS]):
                restaurar(mejor)
        restaurar(mejor)

    def orden(self, primero=()):
        redes = [r for r in self.pads_red if r not in PLANOS and len(self.pads_red[r]) > (2 if r in self.prerruteadas else 1)]

        def largo(r):
            ps = self.pads_red[r]
            return max(math.hypot(a["X"] - b["X"], a["Y"] - b["Y"]) for a in ps for b in ps)
        prioridad = {"Potencia": 0, "Motor": 1, "Alimentacion": 2, "Default": 3}
        return sorted(redes, key=lambda r: (0 if r in primero else 1,
                                            prioridad[clase_de(r, self.plan["clases"])] if not r.startswith("S") else 3, largo(r)))

    def correr(self, primero=()):
        t = time.time()
        self.prerrutas()
        for red in ("GND", "+3V3"):
            self.abanico(red)
        print(f"abanico de planos: {len(self.R.vias)} vías ({time.time() - t:.1f} s)")
        if ESCAPES:
            self.escapes_mcu()
        for red in self.orden(primero):
            c = clase_de(red, self.plan["clases"])
            self.red_arbol(red, ANCHO_CLASE[c], permitir_via=True)
        print(f"rutas: {len(self.R.pistas)} pistas, {len(self.R.vias)} vías, {len(self.fallas)} fallas ({time.time() - t:.1f} s)")
        self.reparar()
        print(f"tras reparar: {len(self.fallas)} fallas ({time.time() - t:.1f} s)")
        for f in self.fallas:
            print("  FALLA", f)
        return len(self.fallas)


def principal(pasadas=4):
    primero = []
    mejor = None
    for k in range(pasadas):
        e = Enrutador()
        n = e.correr(tuple(primero))
        if mejor is None or n < mejor[0]:
            mejor = (n, e)
            json.dump(dict(pistas=e.R.pistas, vias=e.R.vias, fallas=e.fallas), open(os.path.join(AQUI, "rutas.json"), "w"), indent=0)
        if n == 0:
            break
        for f in e.fallas:
            if f[0] not in primero:
                primero.insert(0, f[0])
        print(f"pasada {k + 1}: {n} fallas; se repite con {primero[:8]} primero")
    print(f"mejor resultado: {mejor[0]} fallas")
    return mejor[0]


if __name__ == "__main__":
    sys.exit(1 if principal(int(sys.argv[1]) if len(sys.argv) > 1 else 4) else 0)
