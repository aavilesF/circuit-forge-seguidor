"""Enrutador de pistas para PCB de 2 capas (rejilla + A*), sin dependencias de KiCad.

Trabaja en milimetros con el origen en la esquina superior izquierda de la placa. Las pistas son ortogonales y
van sobre una rejilla de 0.127 mm (los pines a 1.27 / 2.54 mm caen exactos en ella). Cada red tiene su ancho; las
reglas (separacion, borde, vias) se cumplen inflando el cobre de las demas redes con el radio necesario.

Uso: r = Ruteador(ancho, alto, poligono_convexo, pads, reglas); r.rutear(redes_en_orden) -> segmentos, vias, fallos
"""
import heapq
import math
from dataclasses import dataclass, field

import numpy as np

G = 0.127


@dataclass
class Pad:
    net: str | None
    x0: float
    y0: float
    x1: float
    y1: float
    circulo: bool
    capas: tuple          # (0,) cara superior, (1,) inferior, (0, 1) pasante
    agujero: float = 0.0  # diametro del taladro (0 = sin taladro)

    @property
    def cx(self):
        return (self.x0 + self.x1) / 2

    @property
    def cy(self):
        return (self.y0 + self.y1) / 2


@dataclass
class Reglas:
    separacion: float = 0.2
    borde: float = 0.3
    via_d: float = 0.6
    via_taladro: float = 0.3
    ancho: dict = field(default_factory=dict)      # red -> ancho (mm); el resto usa ancho_def
    ancho_def: float = 0.25
    costo_via: float = 45.0
    costo_giro: float = 4.0
    costo_contra: float = 1.0                       # paso en la direccion no preferida de la capa


def _dist_rect(X, Y, x0, y0, x1, y1):
    dx = np.maximum(np.maximum(x0 - X, X - x1), 0.0)
    dy = np.maximum(np.maximum(y0 - Y, Y - y1), 0.0)
    return np.hypot(dx, dy)


class Ruteador:
    def __init__(self, ancho, alto, poligono, pads, reglas: Reglas):
        self.W, self.H = ancho, alto
        self.nx = int(round(ancho / G)) + 1
        self.ny = int(round(alto / G)) + 1
        self.R = reglas
        self.poli = poligono
        self.pads = pads
        xs = np.arange(self.nx) * G
        ys = np.arange(self.ny) * G
        self.X, self.Y = np.meshgrid(xs, ys)
        anchos = sorted({reglas.ancho_def, *reglas.ancho.values()})
        self.clases = anchos + ["via"]                 # una clase por ancho de pista, mas la via
        self.fijo = {l: {c: np.zeros((self.ny, self.nx), bool) for c in self.clases} for l in (0, 1)}
        self.cuenta = {l: {c: np.zeros((self.ny, self.nx), np.int16) for c in self.clases} for l in (0, 1)}
        self.propio = {}                                # red -> capa -> clase -> bool
        self.padvia = {l: np.zeros((self.ny, self.nx), bool) for l in (0, 1)}   # una via no puede ir sobre ningun pad
        self.segmentos, self.vias = [], []
        self.arbol = {}                                 # red -> set de (capa, ix, iy) ya conectados
        self._borde()
        for p in pads:
            self._estampa_pad(p)

    # --------------------------------------------------------------- geometria
    def radio(self, clase):
        """distancia minima entre el eje de la pista (o centro de la via) y cobre de otra red."""
        if clase == "via":
            return self.R.via_d / 2 + self.R.separacion
        return clase / 2 + self.R.separacion

    def _borde(self):
        pts = self.poli
        n = len(pts)
        # poligono convexo recorrido en sentido horario (en pantalla): distancia con signo a cada arista
        for c in self.clases:
            r = (self.R.via_d / 2 if c == "via" else c / 2) + self.R.borde
            ok = np.ones((self.ny, self.nx), bool)
            for i in range(n):
                ax, ay = pts[i]
                bx, by = pts[(i + 1) % n]
                ex, ey = bx - ax, by - ay
                L = math.hypot(ex, ey)
                # normal hacia el interior (el poligono va en sentido horario con y hacia abajo)
                nxv, nyv = -ey / L, ex / L
                d = (self.X - ax) * nxv + (self.Y - ay) * nyv
                ok &= d >= r - 1e-6
            for l in (0, 1):
                self.fijo[l][c] |= ~ok

    def _estampa(self, arr, x0, y0, x1, y1, off, r):
        """marca en arr las celdas a menos de r de la figura (rectangulo (x0..x1, y0..y1) engrosado en `off`)."""
        m = off + r
        ix0 = max(int(math.floor((x0 - m) / G)), 0)
        ix1 = min(int(math.ceil((x1 + m) / G)), self.nx - 1)
        iy0 = max(int(math.floor((y0 - m) / G)), 0)
        iy1 = min(int(math.ceil((y1 + m) / G)), self.ny - 1)
        if ix0 > ix1 or iy0 > iy1:
            return
        X = self.X[iy0:iy1 + 1, ix0:ix1 + 1]
        Y = self.Y[iy0:iy1 + 1, ix0:ix1 + 1]
        d = _dist_rect(X, Y, x0, y0, x1, y1) - off
        arr[iy0:iy1 + 1, ix0:ix1 + 1] |= d < r - 1e-4

    def _arr_red(self, red, capa, clase):
        d = self.propio.setdefault(red, {}).setdefault(capa, {})
        if clase not in d:
            d[clase] = np.zeros((self.ny, self.nx), bool)
        return d[clase]

    def _poner(self, red, capa, x0, y0, x1, y1, off):
        """cobre de `red` (None = fijo) en la capa; se refleja en todas las clases."""
        for c in self.clases:
            r = self.radio(c)
            if red is None:
                self._estampa(self.fijo[capa][c], x0, y0, x1, y1, off, r)
            else:
                a = self._arr_red(red, capa, c)
                nuevo = np.zeros_like(a)
                self._estampa(nuevo, x0, y0, x1, y1, off, r)
                add = nuevo & ~a
                self.cuenta[capa][c] += add.astype(np.int16)
                a |= nuevo

    def _estampa_pad(self, p: Pad):
        off = p.x1 - p.x0
        for l in p.capas:
            if p.circulo:
                self._poner(p.net, l, p.cx, p.cy, p.cx, p.cy, (p.x1 - p.x0) / 2)
                self._estampa(self.padvia[l], p.cx, p.cy, p.cx, p.cy, (p.x1 - p.x0) / 2, self.R.via_d / 2)
            else:
                self._poner(p.net, l, p.x0, p.y0, p.x1, p.y1, 0.0)
                self._estampa(self.padvia[l], p.x0, p.y0, p.x1, p.y1, 0.0, self.R.via_d / 2)
        if p.agujero and not p.capas:
            for l in (0, 1):
                self._poner(None, l, p.cx, p.cy, p.cx, p.cy, p.agujero / 2 + 0.05)

    # --------------------------------------------------------------- busqueda
    def _bloqueo(self, red, clase):
        """por capa, bytearray plano con 1 donde la red no puede poner el eje de una pista de esa clase."""
        out = []
        for l in (0, 1):
            mio = self.propio.get(red, {}).get(l, {}).get(clase)
            tot = self.cuenta[l][clase]
            b = (tot - (mio.astype(np.int16) if mio is not None else 0)) > 0
            b |= self.fijo[l][clase]
            out.append(b)
        return out

    def _bloqueo_via(self, red):
        v = self._bloqueo(red, "via")
        return (v[0] | v[1] | self.padvia[0] | self.padvia[1])

    def _celda(self, x, y):
        ix, iy = int(round(x / G)), int(round(y / G))
        assert abs(ix * G - x) < 0.02 and abs(iy * G - y) < 0.02, f"pad fuera de rejilla: ({x}, {y})"
        return ix, iy

    def _ruta(self, red, fuentes, meta, capas_meta, ancho, tope=2_000_000):
        nx, ny = self.nx, self.ny
        bl = self._bloqueo(red, ancho)
        bv = self._bloqueo_via(red)
        blq = [bytearray(b.astype(np.uint8).tobytes()) for b in bl]
        viab = bytearray(bv.astype(np.uint8).tobytes())
        mx, my = meta
        R = self.R
        N = nx * ny
        abierto = []
        mejor = {}
        padre = {}
        for (l, ix, iy) in fuentes:
            for d in range(5):
                est = (l, ix, iy, d)
                mejor[est] = 0.0
                h = abs(ix - mx) + abs(iy - my)
                heapq.heappush(abierto, (h, 0.0, est))
        cnt = 0
        pref = {0: 0, 1: 1}                           # capa 0: horizontal preferido (d 0/2); capa 1: vertical (d 1/3)
        mv = ((1, 0), (0, 1), (-1, 0), (0, -1))
        while abierto:
            f, g, est = heapq.heappop(abierto)
            if mejor.get(est, 1e18) < g - 1e-9:
                continue
            l, ix, iy, d = est
            if ix == mx and iy == my and l in capas_meta:
                ruta = [(l, ix, iy)]
                while est in padre:
                    est = padre[est]
                    ruta.append(est[:3])
                return ruta[::-1]
            cnt += 1
            if cnt > tope:
                return None
            # mover en la capa
            for nd in range(4):
                if d < 4 and nd == (d + 2) % 4:
                    continue
                dx, dy = mv[nd]
                jx, jy = ix + dx, iy + dy
                if jx < 0 or jy < 0 or jx >= nx or jy >= ny:
                    continue
                k = jy * nx + jx
                if blq[l][k] and not (jx == mx and jy == my and l in capas_meta):
                    continue
                c = 1.0
                if (nd % 2) != pref[l]:
                    c += R.costo_contra
                if d < 4 and nd != d:
                    c += R.costo_giro
                e2 = (l, jx, jy, nd)
                ng = g + c
                if ng < mejor.get(e2, 1e18) - 1e-9:
                    mejor[e2] = ng
                    padre[e2] = est
                    heapq.heappush(abierto, (ng + abs(jx - mx) + abs(jy - my), ng, e2))
            # cambiar de capa con una via
            k = iy * nx + ix
            if not viab[k] and not blq[1 - l][k]:
                e2 = (1 - l, ix, iy, 4)
                ng = g + R.costo_via
                if ng < mejor.get(e2, 1e18) - 1e-9:
                    mejor[e2] = ng
                    padre[e2] = est
                    heapq.heappush(abierto, (ng + abs(ix - mx) + abs(iy - my), ng, e2))
        return None

    # --------------------------------------------------------------- registrar lo trazado
    def _anota_ruta(self, red, ruta, ancho):
        arbol = self.arbol.setdefault(red, set())
        i = 0
        seg = []
        for a, b in zip(ruta, ruta[1:]):
            arbol.add(a)
            arbol.add(b)
            if a[0] != b[0]:
                x, y = a[1] * G, a[2] * G
                self.vias.append((red, round(x, 4), round(y, 4)))
                for l in (0, 1):
                    self._poner(red, l, x, y, x, y, self.R.via_d / 2)
                continue
            seg.append((a, b))
        # fusionar tramos colineales de la misma capa
        i = 0
        while i < len(seg):
            (a, b) = seg[i]
            j = i
            dx, dy = b[1] - a[1], b[2] - a[2]
            while j + 1 < len(seg) and seg[j + 1][0][:3] == seg[j][1][:3] and \
                    (seg[j + 1][1][1] - seg[j + 1][0][1], seg[j + 1][1][2] - seg[j + 1][0][2]) == (dx, dy):
                j += 1
            fin = seg[j][1]
            x0, y0, x1, y1 = a[1] * G, a[2] * G, fin[1] * G, fin[2] * G
            self.segmentos.append((red, a[0], round(x0, 4), round(y0, 4), round(x1, 4), round(y1, 4), ancho))
            self._poner(red, a[0], min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1), ancho / 2)
            i = j + 1

    def _celdas_pad(self, p):
        ix, iy = self._celda(p.cx, p.cy)
        return [(l, ix, iy) for l in p.capas]

    def rutear_red(self, red):
        pads = [p for p in self.pads if p.net == red]
        if len(pads) < 2:
            return True
        ancho = self.R.ancho.get(red, self.R.ancho_def)
        pend = list(pads)
        ini = pend.pop(0)
        self.arbol[red] = set(self._celdas_pad(ini))
        ok = True
        while pend:
            # el pad pendiente mas cercano al arbol
            def dist(p):
                ix, iy = self._celda(p.cx, p.cy)
                return min(abs(ix - c[1]) + abs(iy - c[2]) for c in self.arbol[red])
            pend.sort(key=dist)
            p = pend.pop(0)
            meta = self._celda(p.cx, p.cy)
            ruta = self._ruta(red, list(self.arbol[red]), meta, p.capas, ancho)
            if ruta is None:
                ok = False
                continue
            self._anota_ruta(red, ruta, ancho)
            for c in self._celdas_pad(p):
                self.arbol[red].add(c)
        return ok

    def quitar_red(self, red):
        """deshace lo trazado de una red (para reintentar con otro orden)."""
        self.segmentos = [s for s in self.segmentos if s[0] != red]
        self.vias = [v for v in self.vias if v[0] != red]
        for l, d in self.propio.get(red, {}).items():
            for c, a in d.items():
                self.cuenta[l][c] -= a.astype(np.int16)
                a[:] = False
        self.propio.pop(red, None)
        self.arbol.pop(red, None)
        for p in self.pads:
            if p.net == red:
                self._estampa_pad(p)

    def rutear(self, orden, intentos=6):
        fallos = []
        for red in orden:
            if not self.rutear_red(red):
                fallos.append(red)
        return fallos

    def via_cerca(self, red, x, y, capa, radio_max=3.0):
        """para tierra: pista corta desde un pad SMD hasta una via que baje al plano inferior."""
        ancho = self.R.ancho.get(red, self.R.ancho_def)
        ix0, iy0 = self._celda(x, y)
        bl = self._bloqueo(red, ancho)
        bv = self._bloqueo_via(red)
        blv = self._bloqueo(red, "via")
        mejor = {(ix0, iy0): 0}
        cola = [(0, ix0, iy0)]
        padre = {}
        lim = int(radio_max / G)
        while cola:
            c, ix, iy = heapq.heappop(cola)
            if mejor[(ix, iy)] < c:
                continue
            if not bv[iy, ix] and not bl[1 - capa][iy, ix] and (ix, iy) != (ix0, iy0):
                ruta = [(capa, ix, iy)]
                k = (ix, iy)
                while k in padre:
                    k = padre[k]
                    ruta.append((capa, k[0], k[1]))
                ruta = ruta[::-1]
                ruta.append((1 - capa, ix, iy))
                return ruta
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                jx, jy = ix + dx, iy + dy
                if abs(jx - ix0) > lim or abs(jy - iy0) > lim or not (0 <= jx < self.nx and 0 <= jy < self.ny):
                    continue
                if bl[capa][jy, jx]:
                    continue
                nc = c + 1
                if nc < mejor.get((jx, jy), 1e9):
                    mejor[(jx, jy)] = nc
                    padre[(jx, jy)] = (ix, iy)
                    heapq.heappush(cola, (nc, jx, jy))
        return None
