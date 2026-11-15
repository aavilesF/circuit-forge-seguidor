#!/usr/bin/env python3
"""Patrones para transferencia de tóner (planchado) a escala 1:1 desde un .kicad_pcb.
Uso: python3 patrones_planchado.py <pcb> <salida.pdf> <nombre>
Cada hoja trae arriba la CARA DE ARRIBA (F.Cu, EN ESPEJO) y abajo la CARA DE ABAJO (B.Cu, sin espejo), con letrero. Dos hojas idénticas (la 2.ª es de repuesto).
Ambas se imprimen sin escalar (100 %, 'tamaño real', sin 'ajustar a página') en láser con papel de transferencia.
Negro = cobre que se queda. Punto blanco en cada pad/vía = guía de broca. Cruces fuera del borde = registro."""
import sys, math, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from sx import parse, find
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
mm = 72/25.4
pcb, out, nombre = sys.argv[1:4]
o = parse(open(pcb).read())
def f(v): return float(v)
def P(e, k): return tuple(f(v) for v in find(e, k)[0][1:3])
borde = []   # polilíneas del contorno (Edge.Cuts), en mm absolutos
for e in find(o, 'gr_rect'):
    if find(e, 'layer')[0][1].strip('"') == 'Edge.Cuts':
        (a, b), (c, d) = P(e, 'start'), P(e, 'end'); borde.append([(a, b), (c, b), (c, d), (a, d), (a, b)])
for e in find(o, 'gr_line'):
    if find(e, 'layer')[0][1].strip('"') == 'Edge.Cuts': borde.append([P(e, 'start'), P(e, 'end')])
for e in find(o, 'gr_arc'):
    if find(e, 'layer')[0][1].strip('"') == 'Edge.Cuts':
        a, m, c = P(e, 'start'), P(e, 'mid'), P(e, 'end')
        d = 2*(a[0]*(m[1]-c[1])+m[0]*(c[1]-a[1])+c[0]*(a[1]-m[1]))
        ux = ((a[0]**2+a[1]**2)*(m[1]-c[1])+(m[0]**2+m[1]**2)*(c[1]-a[1])+(c[0]**2+c[1]**2)*(a[1]-m[1]))/d
        uy = ((a[0]**2+a[1]**2)*(c[0]-m[0])+(m[0]**2+m[1]**2)*(a[0]-c[0])+(c[0]**2+c[1]**2)*(m[0]-a[0]))/d
        R = math.hypot(a[0]-ux, a[1]-uy)
        ang = [math.atan2(q[1]-uy, q[0]-ux) for q in (a, m, c)]
        a0, am, a1 = ang
        def nrm(x, ref): return (x-ref+math.pi) % (2*math.pi)-math.pi
        s1 = nrm(a1, a0); sm = nrm(am, a0)
        if (sm > 0) != (s1 > 0) or abs(sm) > abs(s1): s1 = s1 - math.copysign(2*math.pi, s1)
        borde.append([(ux+R*math.cos(a0+s1*i/40), uy+R*math.sin(a0+s1*i/40)) for i in range(41)])
xs = [q[0] for l in borde for q in l]; ys = [q[1] for l in borde for q in l]
x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
W, H = x1-x0, y1-y0
# elementos: (kind, layer(s), datos) en mm relativos al origen de la placa
segs, vias, pads = [], [], []
for s in find(o, 'segment'):
    a = find(s, 'start')[0]; b = find(s, 'end')[0]
    segs.append((find(s, 'layer')[0][1].strip('"'), f(a[1])-x0, f(a[2])-y0, f(b[1])-x0, f(b[2])-y0, f(find(s, 'width')[0][1])))
for v in find(o, 'via'):
    a = find(v, 'at')[0]; vias.append((f(a[1])-x0, f(a[2])-y0, f(find(v, 'size')[0][1]), f(find(v, 'drill')[0][1])))
for fp in find(o, 'footprint'):
    at = find(fp, 'at')[0]; fx, fy = f(at[1]), f(at[2]); rot = f(at[3]) if len(at) > 3 else 0
    c, sn = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    for p in find(fp, 'pad'):
        if p[2] != 'thru_hole': continue          # solo pads con cobre (los agujeros NPTH no llevan cobre)
        pa = find(p, 'at')[0]; lx, ly = f(pa[1]), f(pa[2])
        prot = f(pa[3]) if len(pa) > 3 else 0
        tot = (rot+prot) % 180
        sz = find(p, 'size')[0]; w, h = f(sz[1]), f(sz[2])
        if round(tot) == 90: w, h = h, w
        d = find(p, 'drill')[0]; dr = f(d[2]) if d[1] == 'oval' else f(d[1])
        pads.append((p[3], fx+lx*c+ly*sn-x0, fy-lx*sn+ly*c-y0, w, h, dr))
cv = canvas.Canvas(out, pagesize=A4)
PW, PH = A4
def cara(lado, espejo, mt, titulo):
    ml = (PW/mm - W)/2                                # margen izquierdo (mm); mt = margen superior (mm)
    def X(x): return (ml + (W-x if espejo else x))*mm
    def Y(y): return PH - (mt + y)*mm
    cv.setFillColorRGB(0, 0, 0); cv.setStrokeColorRGB(0, 0, 0); cv.setLineCap(1)
    for (ly, ax, ay, bx, by, w) in segs:
        if ly != lado: continue
        cv.setLineWidth(w*mm); cv.line(X(ax), Y(ay), X(bx), Y(by))
    for (x, y, d, dr) in vias:
        cv.circle(X(x), Y(y), d/2*mm, stroke=0, fill=1)
    for (sh, x, y, w, h, dr) in pads:
        if sh == 'circle': cv.circle(X(x), Y(y), max(w, h)/2*mm, stroke=0, fill=1)
        elif sh == 'oval':
            cv.setLineWidth(min(w, h)*mm); cv.line(X(x-(w-h)/2 if w > h else x), Y(y-(h-w)/2 if h > w else y), X(x+(w-h)/2 if w > h else x), Y(y+(h-w)/2 if h > w else y))
        else: cv.rect(X(x)-w/2*mm, Y(y)-h/2*mm, w*mm, h*mm, stroke=0, fill=1)
    cv.setFillColorRGB(1, 1, 1)
    for (x, y, d, dr) in vias: cv.circle(X(x), Y(y), 0.25*mm, stroke=0, fill=1)   # guía de broca 0.5 mm
    for (sh, x, y, w, h, dr) in pads: cv.circle(X(x), Y(y), 0.25*mm, stroke=0, fill=1)
    cv.setStrokeColorRGB(0, 0, 0); cv.setFillColorRGB(0, 0, 0); cv.setLineWidth(0.15*mm)
    for l in borde:                                                                # borde de corte
        for (a, b) in zip(l, l[1:]): cv.line(X(a[0]-x0), Y(a[1]-y0), X(b[0]-x0), Y(b[1]-y0))
    for (cx, cy) in ((-4, -4), (W+4, -4), (-4, H+4), (W+4, H+4)):                  # cruces de registro
        px = X(cx); py = Y(cy); cv.line(px-2*mm, py, px+2*mm, py); cv.line(px, py-2*mm, px, py+2*mm)
    cv.setFont('Helvetica-Bold', 14)
    cv.drawString(ml*mm, PH-(mt-7)*mm, titulo)                                     # letrero fuera de la placa

def pagina():
    cv.setFillColorRGB(0, 0, 0); cv.setFont('Helvetica', 8)
    cv.drawString(15*mm, PH-8*mm, f"{nombre} - {W:.0f} x {H:.0f} mm - imprimir al 100 % (tamano real). Barra = 50 mm:")
    cv.setLineWidth(0.5*mm); cv.line(125*mm, PH-7.2*mm, 175*mm, PH-7.2*mm)
    cara('F.Cu', True, 34, 'CARA DE ARRIBA (F.Cu) - EN ESPEJO')
    cara('B.Cu', False, PH/mm-24-H, 'CARA DE ABAJO (B.Cu) - SIN ESPEJO')
    cv.showPage()
pagina(); pagina(); cv.save()
print(out, f'{W:.1f}x{H:.1f} mm', len(segs), 'segmentos', len(vias), 'vias', len(pads), 'pads')
