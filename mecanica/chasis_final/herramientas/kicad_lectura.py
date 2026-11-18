"""Lectura mínima de .kicad_pcb (solo lectura) para el chasis: contorno, pads, pistas, vías y cuerpos.
No modifica ningún archivo de electrónica."""
import math, re, hashlib, pathlib

def parse(txt):
    tok = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+')
    st = [[]]
    for m in tok.finditer(txt):
        t = m.group(0)
        if t == '(':
            st.append([])
        elif t == ')':
            x = st.pop(); st[-1].append(x)
        else:
            st[-1].append(t[1:-1] if t.startswith('"') else t)
    return st[0][0]

def find(n, name):
    return [c for c in n if isinstance(c, list) and c and c[0] == name]

def first(n, name):
    r = find(n, name)
    return r[0] if r else None

def md5(path):
    return hashlib.md5(pathlib.Path(path).read_bytes()).hexdigest()

class PCB:
    """Geometría de una PCB en coordenadas de KiCad (mm, Y hacia abajo)."""
    def __init__(self, path):
        self.path = str(path)
        self.md5 = md5(path)
        p = parse(pathlib.Path(path).read_text())
        self.segs = []      # (x1, y1, x2, y2, medio_ancho, capa)
        for s in find(p, 'segment'):
            a, b = first(s, 'start'), first(s, 'end')
            self.segs.append((float(a[1]), float(a[2]), float(b[1]), float(b[2]), float(first(s, 'width')[1]) / 2, first(s, 'layer')[1]))
        for s in find(p, 'arc'):
            pts = [first(s, k) for k in ('start', 'mid', 'end')]
            w = float(first(s, 'width')[1]) / 2; l = first(s, 'layer')[1]
            for i in range(2):
                self.segs.append((float(pts[i][1]), float(pts[i][2]), float(pts[i+1][1]), float(pts[i+1][2]), w, l))
        self.vias = [(float(first(v, 'at')[1]), float(first(v, 'at')[2]), float(first(v, 'size')[1]) / 2) for v in find(p, 'via')]
        self.zonas = len(find(p, 'zone'))
        self.pads = []      # (x, y, radio_equivalente, ref, tipo)
        self.cuerpos = []   # (ref, capa, xmin, ymin, xmax, ymax) desde CrtYd/Fab
        self.huellas = {}
        for f in find(p, 'footprint'):
            at = first(f, 'at'); x, y = float(at[1]), float(at[2]); r = float(at[3]) if len(at) > 3 else 0.0
            ref = [pr[2] for pr in find(f, 'property') if pr[1] == 'Reference'][0]
            capa = first(f, 'layer')[1]
            a = math.radians(-r)
            tr = lambda px, py: (x + px*math.cos(a) - py*math.sin(a), y + px*math.sin(a) + py*math.cos(a))
            self.huellas[ref] = (x, y, r, capa, f[1])
            for pad in find(f, 'pad'):
                pa = first(pad, 'at'); sz = first(pad, 'size')
                bx, by = tr(float(pa[1]), float(pa[2]))
                self.pads.append((bx, by, math.hypot(float(sz[1]), float(sz[2])) / 2, ref, pad[2]))
            xs, ys = [], []
            for g in f:
                if isinstance(g, list) and g and g[0].startswith('fp_'):
                    l = first(g, 'layer')
                    if l and ('CrtYd' in l[1]):
                        for k in ('start', 'end', 'mid'):
                            e = first(g, k)
                            if e:
                                X, Y = tr(float(e[1]), float(e[2])); xs.append(X); ys.append(Y)
            if xs:
                self.cuerpos.append((ref, capa, min(xs), min(ys), max(xs), max(ys)))
        # contorno
        self.borde = []
        for g in p:
            if isinstance(g, list) and g and g[0].startswith('gr_'):
                l = first(g, 'layer')
                if l and l[1] == 'Edge.Cuts':
                    d = {k: (float(first(g, k)[1]), float(first(g, k)[2])) for k in ('start', 'end', 'mid', 'center') if first(g, k)}
                    self.borde.append((g[0], d))
        xs = [pt[0] for _, d in self.borde for k, pt in d.items() if k != 'center']
        ys = [pt[1] for _, d in self.borde for k, pt in d.items() if k != 'center']
        self.bbox = (min(xs), min(ys), max(xs), max(ys))

    @staticmethod
    def _dseg(px, py, x1, y1, x2, y2):
        dx, dy = x2 - x1, y2 - y1; L = dx*dx + dy*dy
        t = 0 if L == 0 else max(0, min(1, ((px - x1)*dx + (py - y1)*dy) / L))
        return math.hypot(px - (x1 + t*dx), py - (y1 + t*dy))

    def cobre_libre(self, px, py):
        """Distancia del punto al cobre más cercano (pistas, vías y pads metalizados de ambas caras)."""
        d = 1e9; quien = ''
        for s in self.segs:
            e = self._dseg(px, py, *s[:4]) - s[4]
            if e < d: d, quien = e, 'pista ' + s[5]
        for vx, vy, vr in self.vias:
            e = math.hypot(px - vx, py - vy) - vr
            if e < d: d, quien = e, 'vía'
        for bx, by, br, ref, tipo in self.pads:
            if tipo == 'np_thru_hole':
                continue
            e = math.hypot(px - bx, py - by) - br
            if e < d: d, quien = e, 'pad ' + ref
        return d, quien

    def cuerpo_cercano(self, px, py):
        best = (1e9, '')
        for ref, capa, x1, y1, x2, y2 in self.cuerpos:
            dd = math.hypot(max(x1 - px, 0, px - x2), max(y1 - py, 0, py - y2))
            if dd < best[0]: best = (dd, ref)
        return best
