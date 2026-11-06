#!/usr/bin/env python3.12
"""Enrutador propio (A* en rejilla, 2 capas) para la PCB casera. No depende de programas externos.

Idea: cada pastilla y cada pista ya puesta "reclama" un disco de rejilla (radio = separación + mitad de pista).
Una pista nueva de la red k solo puede pasar por celdas libres o reclamadas por k. Vías = cambio de capa (costoso).
Capa B.Cu = cobre real que se graba. Capa F.Cu = PUENTE DE ALAMBRE (no se graba), cuesta más para usarla poco.
"""
import heapq
import math
from collections import defaultdict

import numpy as np
import pcbnew

PASO = 0.25            # mm por celda
CAPAS = (pcbnew.B_Cu, pcbnew.F_Cu)   # índice 0 = cobre real (abajo), 1 = puente de alambre (arriba)
COSTO_PUENTE = 20.0
COSTO_VIA = 30.0
MARGEN = 0.30          # error de redondeo de la rejilla + holgura


def mm(v):
    return pcbnew.ToMM(v)


class Ruteador:
    def __init__(self, placa, clearance=0.5, pista=0.8, via_d=1.6, via_taladro=0.8):
        self.b = placa
        self.cl, self.w, self.vd, self.vt = clearance, pista, via_d, via_taladro
        bb = placa.GetBoardEdgesBoundingBox()
        self.x0, self.y0 = mm(bb.GetX()) , mm(bb.GetY())
        self.W = int(mm(bb.GetWidth()) / PASO) + 1
        self.H = int(mm(bb.GetHeight()) / PASO) + 1
        self.claim = [np.zeros((self.H, self.W), dtype=np.int32) for _ in CAPAS]
        self.redes = {}      # id -> nombre
        self.pads = defaultdict(list)   # id -> [(x, y)] en mm
        self.resultado = {"pistas": 0, "vias": 0, "puentes_mm": 0.0, "falló": []}
        self._cargar()

    # ---- rejilla
    def celda(self, x, y):
        return int(round((y - self.y0) / PASO)), int(round((x - self.x0) / PASO))

    def punto(self, cy, cx):
        return self.x0 + cx * PASO, self.y0 + cy * PASO

    def _disco(self, capa, x, y, r, red):
        cy, cx = self.celda(x, y)
        n = int(math.ceil(r / PASO)) + 1
        ys, xs = np.ogrid[-n:n + 1, -n:n + 1]
        mask = (ys * ys + xs * xs) * PASO * PASO <= r * r
        y1, y2, x1, x2 = cy - n, cy + n + 1, cx - n, cx + n + 1
        sy1, sx1 = max(0, -y1), max(0, -x1)
        y1c, x1c = max(0, y1), max(0, x1)
        y2c, x2c = min(self.H, y2), min(self.W, x2)
        if y2c <= y1c or x2c <= x1c:
            return
        sub = mask[sy1:sy1 + (y2c - y1c), sx1:sx1 + (x2c - x1c)]
        g = self.claim[capa][y1c:y2c, x1c:x2c]
        libre = sub & (g == 0)
        otro = sub & (g != 0) & (g != red)
        g[libre] = red
        g[otro] = -1

    def _cargar(self):
        b = self.b
        for fp in b.GetFootprints():
            for p in fp.Pads():
                x, y = mm(p.GetPosition().x), mm(p.GetPosition().y)
                red = p.GetNetCode()
                if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                    for c in range(len(CAPAS)):
                        self._disco(c, x, y, mm(p.GetDrillSize().x) / 2 + self.cl + self.w / 2 + MARGEN, -1)
                    continue
                if red == 0:
                    red = 99999   # pastilla sin red: obstáculo para todos
                else:
                    self.redes[red] = p.GetNetname()
                    self.pads[red].append((x, y))
                r = max(mm(p.GetSize().x), mm(p.GetSize().y)) / 2 + self.cl + self.w / 2 + MARGEN
                for c in range(len(CAPAS)):
                    self._disco(c, x, y, r, red)
        # borde: celdas a menos de 0.5 + w/2 del contorno
        m = int(math.ceil((0.5 + self.w / 2 + 0.3) / PASO))
        for c in range(len(CAPAS)):
            g = self.claim[c]
            g[:m, :] = -1; g[-m:, :] = -1; g[:, :m] = -1; g[:, -m:] = -1

    # ---- A*
    def _ruta(self, red, fuentes, objetivo):
        """fuentes: conjunto de (capa, cy, cx); objetivo: (cy, cx) (ambas capas valen)."""
        gy, gx = objetivo
        abiertos, g, previo = [], {}, {}
        for s in fuentes:
            g[s] = 0.0
            heapq.heappush(abiertos, (self._h(s, gy, gx), 0.0, s))
        pasos = [(-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0),
                 (-1, -1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (1, 1, 1.414)]
        expand = 0
        while abiertos:
            expand += 1
            if expand > 250000:
                return None
            f, costo, cur = heapq.heappop(abiertos)
            if costo > g.get(cur, 1e18):
                continue
            c, cy, cx = cur
            if (cy, cx) == (gy, gx):
                ruta = [cur]
                while cur in previo:
                    cur = previo[cur]
                    ruta.append(cur)
                return ruta[::-1]
            mult = 1.0 if c == 0 else COSTO_PUENTE
            gc = self.claim[c]
            for dy, dx, d in pasos:
                ny, nx = cy + dy, cx + dx
                if not (0 <= ny < self.H and 0 <= nx < self.W):
                    continue
                v = gc[ny, nx]
                if v != 0 and v != red:
                    continue
                if dy and dx:      # diagonal: que no corte esquinas ocupadas
                    a, bb = gc[cy, nx], gc[ny, cx]
                    if (a != 0 and a != red) or (bb != 0 and bb != red):
                        continue
                n = (c, ny, nx)
                nc = costo + d * mult
                if nc < g.get(n, 1e18):
                    g[n] = nc; previo[n] = cur
                    heapq.heappush(abiertos, (nc + self._h(n, gy, gx), nc, n))
            # vía
            c2 = 1 - c
            if self._via_ok(red, cy, cx):
                n = (c2, cy, cx)
                nc = costo + COSTO_VIA
                if nc < g.get(n, 1e18):
                    g[n] = nc; previo[n] = cur
                    heapq.heappush(abiertos, (nc + self._h(n, gy, gx), nc, n))
        return None

    @staticmethod
    def _h(s, gy, gx):
        dy, dx = abs(s[1] - gy), abs(s[2] - gx)
        return (dx + dy) + (1.414 - 2) * min(dx, dy)

    def _via_ok(self, red, cy, cx):
        n = int(math.ceil((self.vd / 2 + self.cl - self.w / 2 + 0.9) / PASO))
        for g in self.claim:
            sub = g[max(0, cy - n):cy + n + 1, max(0, cx - n):cx + n + 1]
            if ((sub != 0) & (sub != red)).any():
                return False
        return True

    # ---- una red
    def rutear_red(self, red):
        pads = self.pads[red]
        if len(pads) < 2:
            return True
        celdas = [self.celda(x, y) for x, y in pads]
        arbol = {(c, celdas[0][0], celdas[0][1]) for c in range(len(CAPAS))}
        pendientes = celdas[1:]
        segs = []
        while pendientes:
            ref = np.array([[t[1], t[2]] for t in arbol])
            mejor = min(pendientes, key=lambda p: np.abs(ref - np.array(p)).sum(axis=1).min())
            ruta = self._ruta(red, arbol, mejor)
            if ruta is None:
                return False
            for (c, cy, cx) in ruta:
                arbol.add((c, cy, cx))
            for (c, cy, cx) in ruta:
                x, y = self.punto(cy, cx)
                self._disco(c, x, y, self.w + self.cl + MARGEN, red)
            arbol |= {(c, mejor[0], mejor[1]) for c in range(len(CAPAS))}
            segs.append(ruta)
            pendientes.remove(mejor)
        self._guardar(red, segs)
        return True

    def _guardar(self, red, rutas):
        b = self.b
        for ruta in rutas:
            i = 0
            while i < len(ruta) - 1:
                c, cy, cx = ruta[i]
                c2, ny, nx = ruta[i + 1]
                if c2 != c:                       # vía
                    x, y = self.punto(cy, cx)
                    v = pcbnew.PCB_VIA(b)
                    v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
                    v.SetNetCode(red); v.SetWidth(pcbnew.FromMM(self.vd)); v.SetDrill(pcbnew.FromMM(self.vt))
                    v.SetViaType(pcbnew.VIATYPE_THROUGH)
                    b.Add(v)
                    self.resultado["vias"] += 1
                    i += 1
                    continue
                # tramo recto: extender mientras la dirección no cambie
                dy, dx = ny - cy, nx - cx
                j = i + 1
                while j + 1 < len(ruta) and ruta[j + 1][0] == c and (ruta[j + 1][1] - ruta[j][1], ruta[j + 1][2] - ruta[j][2]) == (dy, dx):
                    j += 1
                ey, ex = ruta[j][1], ruta[j][2]
                x1, y1 = self.punto(cy, cx)
                x2, y2 = self.punto(ey, ex)
                t = pcbnew.PCB_TRACK(b)
                t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
                t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
                t.SetWidth(pcbnew.FromMM(self.w)); t.SetLayer(CAPAS[c]); t.SetNetCode(red)
                b.Add(t)
                self.resultado["pistas"] += 1
                if c == 1:
                    self.resultado["puentes_mm"] += math.hypot(x2 - x1, y2 - y1)
                i = j
        # unir el centro real de cada pastilla con su celda (tramos < 0.2 mm)
        for (x, y) in self.pads[red]:
            cy, cx = self.celda(x, y)
            px, py = self.punto(cy, cx)
            if abs(px - x) > 1e-3 or abs(py - y) > 1e-3:
                for c in range(len(CAPAS)):
                    t = pcbnew.PCB_TRACK(b)
                    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
                    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(px), pcbnew.FromMM(py)))
                    t.SetWidth(pcbnew.FromMM(self.w)); t.SetLayer(CAPAS[c]); t.SetNetCode(red)
                    b.Add(t)

    def correr(self, intentos=4):
        orden = sorted(self.pads, key=lambda r: self._hpwl(r))
        for it in range(intentos):
            fallan = []
            for r in orden:
                ok = self.rutear_red(r)
                print(f'  intento {it + 1}: {self.redes[r]:12s} {"ok" if ok else "FALLA"}', flush=True)
                if not ok:
                    fallan.append(r)
            if not fallan:
                break
            # reiniciar con las redes que fallaron primero
            self._reiniciar()
            orden = fallan + [r for r in orden if r not in fallan]
        self.resultado["falló"] = [self.redes[r] for r in fallan]
        return self.resultado

    def _hpwl(self, r):
        xs = [p[0] for p in self.pads[r]]; ys = [p[1] for p in self.pads[r]]
        return (max(xs) - min(xs)) + (max(ys) - min(ys)) + 3 * len(xs)

    def _reiniciar(self):
        for t in list(self.b.GetTracks()):
            self.b.Remove(t)
        self.claim = [np.zeros((self.H, self.W), dtype=np.int32) for _ in CAPAS]
        self.resultado.update({"pistas": 0, "vias": 0, "puentes_mm": 0.0})
        self.pads = defaultdict(list)
        self._cargar()
