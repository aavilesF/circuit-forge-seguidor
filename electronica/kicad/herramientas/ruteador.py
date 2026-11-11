#!/usr/bin/env python3.12
"""Enrutador propio (A* en rejilla, 2 capas) para la PCB casera DE DOBLE CARA. No depende de programas externos.

Idea: cada pastilla y cada pista ya puesta "reclama" un disco de rejilla (radio = separación + mitad de pista).
Una pista nueva de la red k solo puede pasar por celdas libres o reclamadas por k. Vías = cambio de cara.
Cuando una red no cabe, se le permite cruzar pistas de otras redes con un costo alto ("rip-up and reroute"):
las redes cruzadas se levantan y se vuelven a rutear después. Así no hay que reiniciar todo en cada intento.

Doble cara casera (decisión de Alan, 11 nov): las dos caras se graban (B.Cu abajo, F.Cu arriba), pero NO hay
metalizado. Por eso:
  * Cada vía es un agujero con un alambre soldado por las dos caras: cuesta trabajo, se usa poco (COSTO_VIA).
  * Una pista solo puede llegar a una pata por la cara donde esa pata se puede soldar (ver capas_accesibles):
      - pieza montada ARRIBA con el cuerpo pegado a la placa (módulos en tira hembra, headers, botones, capacitores):
        solo por abajo;
      - pieza montada ARRIBA con el cuerpo separado (resistencias, diodos, transistores): por las dos caras;
      - pieza montada ABAJO (los TCRT5000 de la placa de sensores, que miran al piso): solo por arriba.
"""
import heapq
import math
from collections import defaultdict

import numpy as np
import pcbnew

PASO = 0.25            # mm por celda
CAPAS = (pcbnew.B_Cu, pcbnew.F_Cu)   # índice 0 = cara de abajo, 1 = cara de arriba (las dos se graban)
COSTO_ARRIBA = 1.15    # la cara de arriba cuesta casi lo mismo; un poco más para dejar la de abajo como principal
COSTO_VIA = 300.0     # cada vía es un alambre soldado a mano; cada placa fija su valor en generar_pcb.COSTO_VIA
# Prefijos de referencia cuyas patas SÍ se pueden soldar por la cara de arriba (cuerpo separado de la placa):
# resistencias y diodos acostados, MOSFET TO-220 vertical, transistor TO-92.
SOLDABLE_ARRIBA = ("R", "D", "Q")


def soldable_arriba(ref):
    return ref.rstrip("0123456789") in SOLDABLE_ARRIBA


def capas_accesibles(fp):
    """Índices de CAPAS (0 = abajo, 1 = arriba) por donde se puede soldar una pata de esta huella."""
    if fp.GetLayer() == pcbnew.B_Cu:
        return (1,)
    return (0, 1) if soldable_arriba(fp.GetReference()) else (0,)
MARGEN = 0.12          # error de la rejilla (los discos se miden desde el centro real, no desde la celda)
PENAL = 10.0           # costo por celda al cruzar la pista de otra red (esa red se levanta y se vuelve a rutear)
MAX_LEVANTADAS = 10**9 # ya no se fijan redes: una red fija podía tapar la única salida de una pata. El costo por
                       # historial (ver rutear_red) hace que las redes muy levantadas dejen de ser cruzadas
N_VIA = 3              # celdas libres extra que necesita una vía alrededor (su pad es más ancho que una pista)


def mm(v):
    return pcbnew.ToMM(v)


def aplicar_caras(b):
    """NO SE USA (11 nov): KiCad 10 trata toda pata pasante como cobre en las dos caras y marca errores de separación
    si se rutea pegado al agujero. Se conserva por si se fabrica con un flujo que sí lo admita.
    Deja el cobre de cada pata solo en la cara donde se puede soldar. Devuelve (solo abajo, solo arriba, ambas)."""
    cuenta = [0, 0, 0]
    for fp in b.GetFootprints():
        acc = capas_accesibles(fp)
        for p in fp.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                continue
            if acc == (0, 1):
                cuenta[2] += 1
                continue
            ls = pcbnew.LSET()
            for c in ((pcbnew.B_Cu, pcbnew.B_Mask) if acc == (0,) else (pcbnew.F_Cu, pcbnew.F_Mask)):
                ls.AddLayer(c)
            p.SetLayerSet(ls)
            cuenta[0 if acc == (0,) else 1] += 1
    return tuple(cuenta)


class Ruteador:
    def __init__(self, placa, clearance=0.5, pista=0.8, via_d=1.6, via_taladro=0.8):
        self.b = placa
        self.cl, self.w, self.vd, self.vt = clearance, pista, via_d, via_taladro
        bb = placa.GetBoardEdgesBoundingBox()
        self.x0, self.y0 = mm(bb.GetX()), mm(bb.GetY())
        self.W = int(mm(bb.GetWidth()) / PASO) + 1
        self.H = int(mm(bb.GetHeight()) / PASO) + 1
        self.base = [np.zeros((self.H, self.W), dtype=np.int32) for _ in CAPAS]   # pastillas, agujeros y borde (fijo)
        self.ocup = [np.zeros((self.H, self.W), dtype=np.int16) for _ in CAPAS]   # nº de redes cuyas pistas reclaman la celda
        self.sin_via = np.zeros((self.H, self.W), dtype=bool)   # cerca de un agujero no cabe otra vía (ni de su misma red)
        self.mascara = {}    # red -> [bool por capa] de sus pistas
        self.rutas = {}      # red -> lista de rutas [(capa, cy, cx), ...]
        self.redes = {}      # id -> nombre
        self.pads = defaultdict(list)   # id -> [(x, y)] en mm
        self.capas_pad = {}             # (x, y) -> capas por donde se puede llegar a esa pastilla
        self.limite = 400000   # expansiones máximas de A* por conexión
        self.costo_via = COSTO_VIA
        self.resultado = {"pistas": 0, "vias": 0, "arriba_mm": 0.0, "falló": [], "levantadas": 0}
        self._cargar()

    # ---- rejilla
    def celda(self, x, y):
        return int(round((y - self.y0) / PASO)), int(round((x - self.x0) / PASO))

    def punto(self, cy, cx):
        return self.x0 + cx * PASO, self.y0 + cy * PASO

    def _ventana(self, x, y, r):
        """(rebanada y, rebanada x, máscara) de las celdas cuyo centro está a r o menos del punto real (x, y)."""
        fy, fx = (y - self.y0) / PASO, (x - self.x0) / PASO
        n = r / PASO
        y1, y2 = max(0, int(math.floor(fy - n))), min(self.H, int(math.ceil(fy + n)) + 1)
        x1, x2 = max(0, int(math.floor(fx - n))), min(self.W, int(math.ceil(fx + n)) + 1)
        if y2 <= y1 or x2 <= x1:
            return None
        ys, xs = np.ogrid[y1:y2, x1:x2]
        return slice(y1, y2), slice(x1, x2), ((ys - fy) ** 2 + (xs - fx) ** 2) <= n * n

    def _disco_base(self, capa, x, y, r, red):
        v = self._ventana(x, y, r)
        if v is None:
            return
        sy, sx, m = v
        g = self.base[capa][sy, sx]
        libre = m & (g == 0)
        otro = m & (g != 0) & (g != red)
        g[libre] = red
        g[otro] = -1

    def _cargar(self):
        for fp in self.b.GetFootprints():
            acc = capas_accesibles(fp)
            for p in fp.Pads():
                x, y = mm(p.GetPosition().x), mm(p.GetPosition().y)
                red = p.GetNetCode()
                agujero = mm(p.GetDrillSize().x) / 2 + self.cl + self.w / 2 + MARGEN
                v = self._ventana(x, y, mm(p.GetDrillSize().x) / 2 + self.vd / 2 + self.cl + MARGEN)
                if v is not None:
                    self.sin_via[v[0], v[1]] |= v[2]
                if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                    for c in range(len(CAPAS)):
                        self._disco_base(c, x, y, agujero, -1)
                    continue
                if red == 0:
                    red = 99999   # pastilla sin red: obstáculo para todos
                else:
                    self.redes[red] = p.GetNetname()
                    self.pads[red].append((x, y))
                    self.capas_pad[(x, y)] = acc
                sx_, sy_ = mm(p.GetSize().x), mm(p.GetSize().y)
                redondo = p.GetShape() in (pcbnew.PAD_SHAPE_CIRCLE, pcbnew.PAD_SHAPE_OVAL)
                r = (max(sx_, sy_) if redondo else math.hypot(sx_, sy_)) / 2 + self.cl + self.w / 2 + MARGEN
                for c in range(len(CAPAS)):
                    if c in acc:
                        self._disco_base(c, x, y, r, red)
                    else:
                        # cara donde la pata no se puede soldar: el pad sigue teniendo cobre ahí (KiCad no admite
                        # patas pasantes con cobre en una sola cara), así que se respeta su separación completa y
                        # ninguna red, ni la suya, puede conectarse por esta cara
                        self._disco_base(c, x, y, r, -1)
        m = int(math.ceil((0.5 + self.w / 2 + MARGEN) / PASO))
        for g in self.base:
            g[:m, :] = -1; g[-m:, :] = -1; g[:, :m] = -1; g[:, -m:] = -1

    # ---- ocupación por pistas
    def _estampar(self, red, rutas):
        masc = [np.zeros((self.H, self.W), dtype=bool) for _ in CAPAS]
        r_pista = self.w + self.cl + MARGEN
        r_via = self.vd / 2 + self.cl + self.w / 2 + MARGEN
        for ruta in rutas:
            for i, (c, cy, cx) in enumerate(ruta):
                x, y = self.punto(cy, cx)
                sy, sx, m = self._ventana(x, y, r_pista)
                masc[c][sy, sx] |= m
                if i + 1 < len(ruta) and ruta[i + 1][0] != c:
                    sy, sx, m = self._ventana(x, y, r_via)
                    for cc in range(len(CAPAS)):
                        masc[cc][sy, sx] |= m
        self.mascara[red] = masc
        self.rutas[red] = rutas
        for c in range(len(CAPAS)):
            self.ocup[c] += masc[c]

    def _levantar(self, red):
        for c in range(len(CAPAS)):
            self.ocup[c] -= self.mascara[red][c]
        del self.mascara[red], self.rutas[red]

    def _quien(self, red, c, cy, cx, n=0):
        """Redes (distintas de red) cuyas pistas reclaman la celda o su vecindad de n celdas."""
        fuera = set()
        for k, masc in self.mascara.items():
            if k == red:
                continue
            if n == 0:
                if masc[c][cy, cx]:
                    fuera.add(k)
            elif any(m[max(0, cy - n):cy + n + 1, max(0, cx - n):cx + n + 1].any() for m in masc):
                fuera.add(k)
        return fuera

    # ---- A*
    def _ruta(self, red, fuentes, objetivo, capas_obj, duro, suave, blando, pena=None):
        gy, gx = objetivo
        abiertos, g, previo = [], {}, {}
        for s in fuentes:
            g[s] = 0.0
            heapq.heappush(abiertos, (self._h(s, gy, gx), 0.0, s))
        pasos = [(-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0),
                 (-1, -1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (1, 1, 1.414)]
        H, W, n = self.H, self.W, N_VIA
        expand = 0
        while abiertos:
            expand += 1
            if expand > (self.limite * 3 if blando else self.limite):   # abrirse paso entre pistas explora más
                self.motivo = f"límite de búsqueda ({expand} pasos) hacia {self.punto(gy, gx)}"
                return None
            f, costo, cur = heapq.heappop(abiertos)
            if costo > g.get(cur, 1e18):
                continue
            c, cy, cx = cur
            if cy == gy and cx == gx and c in capas_obj:
                ruta = [cur]
                while cur in previo:
                    cur = previo[cur]
                    ruta.append(cur)
                return ruta[::-1]
            mult = 1.0 if c == 0 else COSTO_ARRIBA
            dc, sc = duro[c], suave[c]
            for dy, dx, d in pasos:
                ny, nx = cy + dy, cx + dx
                if not (0 <= ny < H and 0 <= nx < W) or dc[ny, nx]:
                    continue
                extra = 0.0
                if sc[ny, nx]:
                    if not blando:
                        continue
                    extra = pena[c][ny, nx]
                if dy and dx and (dc[cy, nx] or dc[ny, cx] or (not blando and (sc[cy, nx] or sc[ny, cx]))):
                    continue       # diagonal: que no corte esquinas ocupadas
                nodo = (c, ny, nx)
                nc = costo + d * mult + extra
                if nc < g.get(nodo, 1e18):
                    g[nodo] = nc; previo[nodo] = cur
                    heapq.heappush(abiertos, (nc + self._h(nodo, gy, gx), nc, nodo))
            # vía: necesita su vecindad libre en las dos caras
            y1, y2, x1, x2 = max(0, cy - n), cy + n + 1, max(0, cx - n), cx + n + 1
            if self.sin_via[cy, cx] or duro[0][y1:y2, x1:x2].any() or duro[1][y1:y2, x1:x2].any():
                continue
            extra = 0.0
            if suave[0][y1:y2, x1:x2].any() or suave[1][y1:y2, x1:x2].any():
                if not blando:
                    continue
                extra = PENAL * 4
            nodo = (1 - c, cy, cx)
            nc = costo + self.costo_via + extra
            if nc < g.get(nodo, 1e18):
                g[nodo] = nc; previo[nodo] = cur
                heapq.heappush(abiertos, (nc + self._h(nodo, gy, gx), nc, nodo))
        self.motivo = f"sin camino tras {expand} pasos hacia {self.punto(gy, gx)}"
        return None

    @staticmethod
    def _h(s, gy, gx):
        dy, dx = abs(s[1] - gy), abs(s[2] - gx)
        return (dx + dy) + (1.414 - 2) * min(dx, dy)

    # ---- una red
    def rutear_red(self, red, blando=False, fijas=(), veces=None):
        """Devuelve (rutas, redes_cruzadas) o None. Con blando=True puede cruzar pistas de redes no fijas."""
        pads = self.pads[red]
        if len(pads) < 2:
            return [], set()
        propia = self.mascara.get(red)
        duro, suave = [], []
        for c in range(len(CAPAS)):
            d = (self.base[c] != 0) & (self.base[c] != red)
            for k in fijas:
                if k != red and k in self.mascara:
                    d = d | self.mascara[k][c]
            o = self.ocup[c] - propia[c] if propia else self.ocup[c]
            duro.append(d)
            suave.append((o > 0) & ~d)
        pena = None
        if blando:      # congestión negociada: cruzar una red cuesta más cuantas más veces la han levantado
            pena = [np.zeros((self.H, self.W), dtype=np.float32) for _ in CAPAS]
            for k, masc in self.mascara.items():
                if k != red:
                    costo_k = PENAL * (1 + (veces[k] if veces else 0)) ** 2
                    for c in range(len(CAPAS)):
                        np.maximum(pena[c], masc[c] * np.float32(costo_k), out=pena[c])
        celdas = [self.celda(x, y) for x, y in pads]
        capas = {self.celda(x, y): self.capas_pad.get((x, y), (0, 1)) for x, y in pads}
        arbol = {(c, celdas[0][0], celdas[0][1]) for c in capas[celdas[0]]}
        pendientes = celdas[1:]
        rutas, cruzadas = [], set()
        while pendientes:
            ref = np.array([[t[1], t[2]] for t in arbol])
            mejor = min(pendientes, key=lambda p: np.abs(ref - np.array(p)).sum(axis=1).min())
            ruta = self._ruta(red, arbol, mejor, capas[mejor], duro, suave, blando, pena)
            if ruta is None:
                return None
            for i, (c, cy, cx) in enumerate(ruta):
                arbol.add((c, cy, cx))
                if blando:
                    if suave[c][cy, cx]:
                        cruzadas |= self._quien(red, c, cy, cx)
                    if i + 1 < len(ruta) and ruta[i + 1][0] != c:
                        cruzadas |= self._quien(red, c, cy, cx, N_VIA)
            arbol |= {(c, mejor[0], mejor[1]) for c in capas[mejor]}
            rutas.append(ruta)
            pendientes.remove(mejor)
        return rutas, cruzadas

    # ---- todas
    def _vuelta(self, cola, max_pasos):
        """Rutea la cola con rip-up. Devuelve las redes que no se pudieron poner."""
        from collections import Counter
        veces, ultimo, fijas, fallan, paso = Counter(), Counter(), set(), [], 0
        while cola and paso < max_pasos:
            paso += 1
            r = cola.popleft()
            res = self.rutear_red(r)
            modo = "ok"
            if res is None:
                res = self.rutear_red(r, blando=True, fijas=fijas, veces=veces)
                modo = "ok (levanta)"
                if res is None and fijas and ultimo[r] < 3:   # una red fija le tapa la salida: último recurso
                    ultimo[r] += 1
                    res = self.rutear_red(r, blando=True, veces=veces)
                    modo = "ok (levanta fijas)"
            if res is None:
                fallan.append(r)
                print(f"  {paso:4d} {self.redes[r]:12s} FALLA: {getattr(self, 'motivo', '?')}", flush=True)
                continue
            rutas, cruzadas = res
            for k in cruzadas:
                self._levantar(k)
                veces[k] += 1
                self.resultado["levantadas"] += 1
                cola.append(k)
            if cruzadas:
                veces[r] += 1
            if veces[r] >= MAX_LEVANTADAS:
                fijas.add(r)
            self._estampar(r, rutas)
            print(f"  {paso:4d} {self.redes[r]:12s} {modo}" + (f" -> {[self.redes[k] for k in cruzadas]}" if cruzadas else ""), flush=True)
        return [r for r in dict.fromkeys(fallan + list(cola)) if r not in self.rutas]

    @staticmethod
    def _costo(rutas, costo_via):
        vias = sum(1 for ruta in rutas for a, b in zip(ruta, ruta[1:]) if a[0] != b[0])
        return vias * costo_via + sum(len(ruta) for ruta in rutas), vias

    def _refinar(self, pasadas=3, costo_via=None):
        """Con todo puesto, vuelve a rutear cada red cobrando muy caras las vías; conserva la mejor versión."""
        normal = self.costo_via
        costo_via = costo_via or 2 * normal
        self.costo_via = costo_via
        for n in range(pasadas):
            mejoras = 0
            for r in sorted(self.rutas, key=lambda k: -self._costo(self.rutas[k], costo_via)[0]):
                viejas = self.rutas[r]
                self._levantar(r)
                res = self.rutear_red(r)
                if res is not None and self._costo(res[0], costo_via)[0] < self._costo(viejas, costo_via)[0]:
                    self._estampar(r, res[0]); mejoras += 1
                else:
                    self._estampar(r, viejas)
            total = sum(self._costo(v, costo_via)[1] for v in self.rutas.values())
            print(f"  refinado {n + 1}: {mejoras} redes mejoradas, {total} vías", flush=True)
            if not mejoras:
                break
        self.costo_via = normal

    def correr(self, rondas=3, reinicios=2):
        from collections import deque
        orden = sorted(self.pads, key=self._hpwl)
        for n in range(reinicios + 1):
            fallan = self._vuelta(deque(orden), 40 * len(self.pads))
            if not fallan or n == reinicios:
                break
            print(f"  reinicio {n + 1}: primero {[self.redes[r] for r in fallan]}", flush=True)
            for r in list(self.rutas):
                self._levantar(r)
            orden = fallan + [r for r in orden if r not in fallan]
        for n in range(rondas):
            if not fallan:
                break
            print(f"  ronda extra {n + 1} para {[self.redes[r] for r in fallan]}", flush=True)
            fallan = self._vuelta(deque(fallan), 25 * len(self.pads))
        self._refinar()
        for r in list(fallan):                      # tras el refinado puede haber quedado espacio
            res = self.rutear_red(r)
            if res is not None:
                self._estampar(r, res[0]); fallan.remove(r)
        for r, rutas in self.rutas.items():
            self._guardar(r, rutas)
        self.resultado["falló"] = [self.redes[r] for r in fallan]
        return self.resultado

    def _hpwl(self, r):
        xs = [p[0] for p in self.pads[r]]; ys = [p[1] for p in self.pads[r]]
        return (max(xs) - min(xs)) + (max(ys) - min(ys)) + 3 * len(xs)

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
                    self.resultado["arriba_mm"] += math.hypot(x2 - x1, y2 - y1)
                i = j
        # unir el centro real de cada pastilla con su celda (tramos < 0.2 mm), solo en las caras donde de verdad llega
        # una pista a esa celda (si no, queda un tramo colgante de 0.25 mm: aviso track_dangling del DRC)
        llegan = set()
        for ruta in rutas:
            for (c, cy, cx) in (ruta[0], ruta[-1]):
                llegan.add((c, cy, cx))
        for (x, y) in self.pads[red]:
            cy, cx = self.celda(x, y)
            px, py = self.punto(cy, cx)
            if abs(px - x) > 1e-3 or abs(py - y) > 1e-3:
                caras = [c for c in self.capas_pad.get((x, y), (0, 1)) if (c, cy, cx) in llegan]
                for c in caras:
                    t = pcbnew.PCB_TRACK(b)
                    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
                    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(px), pcbnew.FromMM(py)))
                    t.SetWidth(pcbnew.FromMM(self.w)); t.SetLayer(CAPAS[c]); t.SetNetCode(red)
                    b.Add(t)
