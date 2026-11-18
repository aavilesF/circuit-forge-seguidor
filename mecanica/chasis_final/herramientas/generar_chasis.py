#!/usr/bin/env python3
"""Genera el chasis final (base, tapa, brazo de sensores y pieza de prueba de kerf) en DXF 1:1 (mm),
las vistas previas, la plantilla de taladro de las PCB y el modelo del ensamble para verificar.

Uso:  python3 mecanica/chasis_final/herramientas/generar_chasis.py [--kerf 0.15]
  --kerf K   ancho total del corte del láser en mm. Sin él, la geometría es NOMINAL y todo queda "PENDIENTE DE KERF".
             Con él, los contornos exteriores se agrandan K/2 y los agujeros/ranuras se achican K/2
             (no usar si el software del láser ya compensa).

Ejes del robot: X al frente (0 = borde trasero de la caja de 200 x 100), Y a la izquierda, Z arriba (piso = 0).
Lee las PCB de v2/electronica en modo solo lectura; no modifica nada fuera de mecanica/chasis_final/.
"""
import argparse, json, math, pathlib, subprocess, sys, datetime
import ezdxf
import ezdxf.path
from ezdxf import units
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Polygon as MPoly

HERE = pathlib.Path(__file__).resolve().parent
CF = HERE.parent
REPO = CF.parents[1]
sys.path.insert(0, str(HERE))
from parametros import M, D, v
from kicad_lectura import PCB

PCB_PRINCIPAL = REPO / 'v2/electronica/principal/principal.kicad_pcb'
PCB_SENSORES = REPO / 'v2/electronica/sensores/sensores.kicad_pcb'

# Agujeros nuevos a taladrar en las PCB (coordenadas de KiCad). Elegidos con cobre libre >= 3.7 mm en las dos caras
# (autorizado por el equipo el 17 nov: "Taladrar M3 en zonas sin cobre").
AGUJEROS_PRINCIPAL = {'H1': (191.0, 74.0), 'H2': (148.0, 132.5), 'H3': (112.0, 104.5)}
AGUJEROS_SENSORES = {'S1': (104.75, 122.75), 'S2': (187.5, 120.0)}

# --------------------------------------------------------------------------------------------- geometría
def unit(dx, dy):
    L = math.hypot(dx, dy); return dx / L, dy / L

def poly_fillet(V, Rr):
    """Polígono (CCW) con redondeo por vértice -> lista [x, y, bulge] para LWPOLYLINE."""
    n = len(V); out = []
    for i in range(n):
        p0, p1, p2 = V[i-1], V[i], V[(i+1) % n]; r = Rr[i]
        d1 = unit(p1[0]-p0[0], p1[1]-p0[1]); d2 = unit(p2[0]-p1[0], p2[1]-p1[1])
        th = math.atan2(d1[0]*d2[1] - d1[1]*d2[0], d1[0]*d2[0] + d1[1]*d2[1])
        if r <= 1e-9 or abs(th) < 1e-9:
            out.append([p1[0], p1[1], 0.0]); continue
        t = r * math.tan(abs(th) / 2)
        out.append([p1[0] - d1[0]*t, p1[1] - d1[1]*t, math.tan(th / 4)])
        out.append([p1[0] + d2[0]*t, p1[1] + d2[1]*t, 0.0])
    return out

def ortho_offset(V, Rr, off):
    """Desplaza un polígono ortogonal CCW 'off' mm hacia fuera (negativo = hacia dentro); ajusta radios."""
    n = len(V); NV = []; NR = []
    for i in range(n):
        p0, p1, p2 = V[i-1], V[i], V[(i+1) % n]
        e1 = unit(p1[0]-p0[0], p1[1]-p0[1]); e2 = unit(p2[0]-p1[0], p2[1]-p1[1])
        n1 = (e1[1], -e1[0]); n2 = (e2[1], -e2[0])
        NV.append((p1[0] + off*(n1[0] + n2[0]), p1[1] + off*(n1[1] + n2[1])))
        convexo = (e1[0]*e2[1] - e1[1]*e2[0]) > 0
        NR.append(max(0.0, Rr[i] + (off if convexo else -off)) if Rr[i] > 0 else 0.0)
    return NV, NR

def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]

class Pieza:
    def __init__(self, nombre, comp):
        self.nombre = nombre; self.comp = comp   # comp = kerf/2 (0 = nominal)
        self.cortes = []   # dict(tipo, ...)
        self.grabados = []
        self.etiquetas = []  # (x, y, texto) solo para vistas
    def exterior(self, V, Rr, etiqueta='contorno'):
        V2, R2 = ortho_offset(V, Rr, +self.comp)
        self.cortes.append(dict(tipo='poly', pts=poly_fillet(V2, R2), etiqueta=etiqueta, exterior=True))
    def ventana(self, V, Rr, etiqueta):
        V2, R2 = ortho_offset(V, Rr, -self.comp)
        self.cortes.append(dict(tipo='poly', pts=poly_fillet(V2, R2), etiqueta=etiqueta, exterior=False))
    def agujero(self, x, y, d, etiqueta):
        self.cortes.append(dict(tipo='circle', c=(x, y), r=d/2 - self.comp, etiqueta=etiqueta, exterior=False, nominal_d=d))
    def ranura(self, c1, c2, ancho, etiqueta):
        r = ancho/2 - self.comp
        ux, uy = unit(c2[0]-c1[0], c2[1]-c1[1]); nx, ny = -uy, ux
        pts = [[c1[0]-r*nx, c1[1]-r*ny, 0.0], [c2[0]-r*nx, c2[1]-r*ny, 1.0],
               [c2[0]+r*nx, c2[1]+r*ny, 0.0], [c1[0]+r*nx, c1[1]+r*ny, 1.0]]
        self.cortes.append(dict(tipo='poly', pts=pts, etiqueta=etiqueta, exterior=False, ranura=(c1, c2, ancho)))

def muestrear(pts, paso=0.25):
    """LWPOLYLINE cerrada con bulges -> lista de puntos (para vistas y verificación)."""
    out = []
    n = len(pts)
    for i in range(n):
        x1, y1, b = pts[i]; x2, y2 = pts[(i+1) % n][:2]
        if abs(b) < 1e-12:
            out.append((x1, y1)); continue
        th = 4 * math.atan(b); c = math.hypot(x2-x1, y2-y1)
        r = c / (2 * math.sin(abs(th) / 2))
        mx, my = (x1+x2)/2, (y1+y2)/2; ux, uy = (x2-x1)/c, (y2-y1)/c
        h = r * math.cos(abs(th) / 2); s = 1 if b > 0 else -1
        cx, cy = mx - s*uy*h, my + s*ux*h
        a0 = math.atan2(y1-cy, x1-cx); k = max(4, int(abs(th)*r/paso))
        for j in range(k):
            a = a0 + th * j / k; out.append((cx + r*math.cos(a), cy + r*math.sin(a)))
    return out

# --------------------------------------------------------------------------------------------- modelo
def construir(kerf=None):
    comp = (kerf or 0.0) / 2
    t = D['t']; R = v('llanta_diam') / 2
    pp = PCB(PCB_PRINCIPAL); ps = PCB(PCB_SENSORES)
    # mapeos KiCad -> robot (rotación de -90°, sin espejo; cara de componentes hacia arriba)
    kx0p = (pp.bbox[0] + pp.bbox[2]) / 2; kymaxp = pp.bbox[3]
    kx0s = (ps.bbox[0] + ps.bbox[2]) / 2; kymins = ps.bbox[1]
    mp = lambda kx, ky: (D['x_pcb_principal'] + (kymaxp - ky), kx0p - kx)
    ms = lambda kx, ky: (D['x_frente_sensores'] - (ky - kymins), kx0s - kx)
    L_p = pp.bbox[3] - pp.bbox[1]; W_p = pp.bbox[2] - pp.bbox[0]
    L_s = ps.bbox[3] - ps.bbox[1]

    xb0 = D['x_base_trasera']; x_eje = xb0 + D['x_eje_desde_base']
    x_muesca = x_eje + R + D['holgura_rueda']
    hw = D['medio_ancho']; hwn = D['base_ancho_ruedas']; hwb = D['medio_ancho_brazo']
    sep = v('soporte_sep_agujeros') / 2
    d3 = v('m3_libre')

    # alturas
    z_base_sup = R - v('h_eje'); z_base_inf = z_base_sup - t
    z_tapa_inf = z_base_sup + D['L_base_tapa']; z_tapa_sup = z_tapa_inf + t
    z_pcb_inf = z_tapa_sup + D['L_tapa_pcb']; esp_pcb = v('pcb_espesor')
    z_brazo_inf = z_tapa_sup; z_brazo_sup = z_brazo_inf + t
    z_sens_sup = z_brazo_inf - D['L_brazo_sensores']; z_sens_inf = z_sens_sup - esp_pcb
    z_lente = z_sens_inf - v('tcrt_alto') - v('tcrt_separacion_cuerpo')
    loca = v('loca_caja')

    # posiciones compartidas
    x_bat0, x_bat1 = x_muesca + 2.15, x_muesca + 22.15       # zona de batería (20 mm de fondo)
    x_cincho_t = x_muesca - 0.35; x_cincho_d = x_bat1 + 1.5     # centros de las ranuras de cincho
    vent = v('vent_caja'); vsep = v('vent_agujeros')[0] / 2
    x_vent = x_cincho_d + D['cincho'][0]/2 + 2.0 + vent[0]/2    # centro del ventilador
    x_base_fin = x_vent + vent[0]/2 + 4.0
    x_tapa0 = xb0 + 1.0; x_union = x_vent + 8.0; x_tapa_fin = x_union + 6.0
    x_brazo0 = x_union - 6.0
    sb = {'B1': (D['x_pcb_principal'] + 34.5, 43.5), 'B2': (D['x_pcb_principal'] + 34.5, -43.5),
          'B3': (x_union, 43.5), 'B4': (x_union, -43.5)}           # separadores base-tapa
    j0 = (x_union, 0.0)                                             # tornillo central de unión tapa-brazo
    hp = {k: mp(*kv) for k, kv in AGUJEROS_PRINCIPAL.items()}
    hs = {k: ms(*kv) for k, kv in AGUJEROS_SENSORES.items()}
    x_sens_tras = D['x_frente_sensores'] - L_s
    x_loca = x_sens_tras - 3.0 - loca[1]/2                          # rueda loca justo detrás de la placa de sensores
    kcd = v('kcd1'); x_kcd = x_base_fin + 1.6 + kcd[0]/2; y_kcd = 32.0
    j1 = [ms(*ps.huellas['J1'][:2])]
    x_brazo_fin = 161.0

    piezas = {}
    # ------------------------------------------------ BASE
    b = Pieza('base', comp)
    V = [(xb0, -hwn), (x_muesca, -hwn), (x_muesca, -hw), (x_base_fin, -hw), (x_base_fin, hw), (x_muesca, hw), (x_muesca, hwn), (xb0, hwn)]
    b.exterior(V, [3, 2, 3, 3, 3, 3, 2, 3])
    for s in (1, -1):
        for xx in (x_eje - sep, x_eje + sep):
            y1 = s*(D['ranura_y'][0] + D['m2_ranura']/2); y2 = s*(D['ranura_y'][1] - D['m2_ranura']/2)
            b.ranura((xx, min(y1, y2)), (xx, max(y1, y2)), D['m2_ranura'], f'soporte motor {"izq" if s > 0 else "der"} x={xx:.2f}')
    cw, cl = D['cincho']
    for xx in (x_cincho_t, x_cincho_d):
        for s in (1, -1):
            yc = s*14.0
            b.ventana(rect(xx - cw/2, yc - cl/2, xx + cw/2, yc + cl/2), [1.0]*4, f'cincho batería x={xx:.2f}')
    b.agujero(x_vent, 0.0, v('vent_toma_d'), 'toma del ventilador')
    for sx in (1, -1):
        for sy in (1, -1):
            b.agujero(x_vent + sx*vsep, sy*vsep, v('vent_agujeros')[1], 'ventilador M3')
    for k, (x, y) in sb.items():
        b.agujero(x, y, d3, f'separador base-tapa {k}')
    piezas['base'] = b

    # ------------------------------------------------ TAPA
    tp = Pieza('tapa', comp)
    tp.exterior(rect(x_tapa0, -hw, x_tapa_fin, hw), [3]*4)
    for k, (x, y) in hp.items():
        tp.agujero(x, y, d3, f'separador PCB principal {k}')
    for k, (x, y) in sb.items():
        tp.agujero(x, y, d3, f'separador base-tapa {k}')
    tp.agujero(*j0, d3, 'unión tapa-brazo J0')
    xc0 = D['x_pcb_principal'] + 44.0
    tp.ventana(rect(xc0, 37.0, xc0 + 14, 43.0), [2.0]*4, 'paso de cables izq (batería, interruptor)')
    tp.ventana(rect(xc0, -43.0, xc0 + 14, -37.0), [2.0]*4, 'paso de cables der (motores, ventilador)')
    piezas['tapa'] = tp

    # ------------------------------------------------ BRAZO
    br = Pieza('brazo_sensores', comp)
    br.exterior(rect(x_brazo0, -hwb, x_brazo_fin, hwb), [3]*4)
    for k in ('B3', 'B4'):
        br.agujero(*sb[k], d3, f'unión tapa-brazo {k}')
    br.agujero(*j0, d3, 'unión tapa-brazo J0')
    for k, (x, y) in hs.items():
        br.agujero(x, y, d3, f'separador placa sensores {k}')
    for s in (1, -1):
        y1, y2 = s*6.0, s*9.0
        br.ranura((x_loca, min(y1, y2)), (x_loca, max(y1, y2)), d3, 'rueda loca (ranura: separación ~15 y Ø sin medir)')
    br.ventana(rect(x_kcd - kcd[0]/2, y_kcd - kcd[1]/2, x_kcd + kcd[0]/2, y_kcd + kcd[1]/2), [0.5]*4, 'interruptor KCD1 (18.8 x 6.7 nominal)')
    xw1 = hs['S2'][0] - 3.18 - 3.3
    br.ventana(rect(xw1 - 12.0, -hwb + 4.0, xw1, -20.0), [2.0]*4, 'paso del cable de 9 hilos a J1')
    piezas['brazo_sensores'] = br

    # ------------------------------------------------ PRUEBA DE KERF
    pk = Pieza('prueba_kerf', comp)
    pk.exterior(rect(0, 0, 60.0, 30.0), [0]*4)
    pk.ventana(rect(5.0, 5.0, 15.0, 15.0), [0]*4, 'cuadro 10.00 x 10.00')
    pk.agujero(22.0, 10.0, 3.2, 'Ø3.2 (M3)')
    pk.agujero(22.0, 21.0, 2.4, 'Ø2.4 (M2)')
    pk.ranura((30.0, 7.0), (30.0, 13.0), 3.2, 'ranura 3.2 (rueda loca)')
    pk.ventana(rect(36.0, 4.0, 39.0, 16.0), [1.0]*4, 'cincho 3 x 12')
    pk.ventana(rect(36.0, 20.0, 36.0 + kcd[0], 20.0 + kcd[1]), [0.5]*4, 'KCD1 18.8 x 6.7')
    piezas['prueba_kerf'] = pk

    # ------------------------------------------------ grabados (marcas de orientación)
    def flecha(p, x, y, txt, h=3.0):
        p.grabados.append(dict(tipo='linea', pts=[(x, y), (x + 14, y)]))
        p.grabados.append(dict(tipo='linea', pts=[(x + 10, y + 2.5), (x + 14, y), (x + 10, y - 2.5)]))
        p.grabados.append(dict(tipo='texto', x=x, y=y + 2.5, h=h, txt=txt.replace(' - ', ' ')))
    flecha(b, 36.0, -34.0, 'BASE - ARRIBA - FRENTE')
    flecha(tp, 22.0, 4.0, 'TAPA - ARRIBA - FRENTE')
    for xx in (D['x_pcb_principal'], D['x_pcb_principal'] + L_p):   # bordes trasero y delantero de la PCB principal
        tp.grabados.append(dict(tipo='linea', pts=[(xx, -hw + 2.0), (xx, hw - 2.0)]))
    flecha(br, 88.0, -34.0, 'BRAZO - ARRIBA - FRENTE', h=2.5)
    br.grabados.append(dict(tipo='linea', pts=[(x_sens_tras, -18.0), (x_sens_tras, hwb - 2.0)]))   # borde trasero de la placa de sensores
    pk.grabados.append(dict(tipo='texto', x=42.0, y=4.0, h=3.0, txt='KERF'))

    # ------------------------------------------------ ensamble (sólidos simplificados)
    G = 4.0; gap = 0.5      # ESTIMADOS solo para dibujar; el ancho real depende de V2 (P-V2-34)
    y_in = G/2 + v('motor_largo') + gap; y_out = y_in + v('rin_ancho')
    sol = []
    def caja(n, x0, x1, y0, y1, z0, z1, grupo, nota=''):
        sol.append(dict(n=n, tipo='caja', x=(x0, x1), y=(y0, y1), z=(z0, z1), grupo=grupo, nota=nota))
    def cil_z(n, x, y, r, z0, z1, grupo, nota=''):
        sol.append(dict(n=n, tipo='cil_z', c=(x, y), r=r, z=(z0, z1), grupo=grupo, nota=nota))
    for s, ld in ((1, 'izq'), (-1, 'der')):
        sol.append(dict(n=f'rueda {ld}', tipo='rueda', c=(x_eje, R), r=R, y=tuple(sorted((s*y_in, s*y_out))), grupo='rueda',
                        nota='cara interior/exterior ESTIMADAS (G=4, hueco 0.5); medir V2'))
        caja(f'motor {ld}', x_eje - 6, x_eje + 6, *sorted((s*G/2, s*(G/2 + v('motor_largo')))), z_base_sup, z_base_sup + 10, 'motor')
        caja(f'soporte {ld}', x_eje - 12.5, x_eje + 12.5, *sorted((s*(G/2 + 8), s*(G/2 + 22))), z_base_sup, z_base_sup + 11, 'motor', 'largo y posición sin medir')
    sol.append(dict(n='base', tipo='placa', pieza='base', z=(z_base_inf, z_base_sup), grupo='acrilico'))
    sol.append(dict(n='tapa', tipo='placa', pieza='tapa', z=(z_tapa_inf, z_tapa_sup), grupo='acrilico'))
    sol.append(dict(n='brazo_sensores', tipo='placa', pieza='brazo_sensores', z=(z_brazo_inf, z_brazo_sup), grupo='acrilico'))
    caja('batería (envolvente máx.)', x_bat0, x_bat1, -32, 32, z_base_sup, z_tapa_inf - 1.0, 'bateria', 'LiPo sin comprar: máximo 64 x 20 x 19 mm')
    caja('ventilador', x_vent - 20, x_vent + 20, -20, 20, z_base_sup, z_base_sup + vent[2], 'ventilador')
    hx = v('separador_hex') / 2 / math.cos(math.radians(30)); tu = v('tuerca_m3'); hc = v('cabeza_m3_alto')
    for k, (x, y) in sb.items():
        cil_z(f'separador {k}', x, y, hx, z_base_sup, z_tapa_inf, 'herraje')
        cil_z(f'tuerca {k}', x, y, hx, z_base_inf - tu[1], z_base_inf, 'herraje')
        ztop = z_brazo_sup if k in ('B3', 'B4') else z_tapa_sup
        cil_z(f'cabeza {k}', x, y, 2.75, ztop, ztop + hc, 'herraje')
    cil_z('tuerca J0', *j0, hx, z_tapa_inf - tu[1], z_tapa_inf, 'herraje')
    cil_z('cabeza J0', *j0, 2.75, z_brazo_sup, z_brazo_sup + hc, 'herraje')
    for k, (x, y) in hp.items():
        cil_z(f'separador {k}', x, y, hx, z_tapa_sup, z_pcb_inf, 'herraje')
        cil_z(f'tuerca {k}', x, y, hx, z_tapa_inf - tu[1], z_tapa_inf, 'herraje')
    caja('PCB principal', D['x_pcb_principal'], D['x_pcb_principal'] + L_p, -W_p/2, W_p/2, z_pcb_inf, z_pcb_inf + esp_pcb, 'pcb')
    for k, (x, y) in hs.items():
        cil_z(f'separador {k}', x, y, hx, z_sens_sup, z_brazo_inf, 'herraje')
        cil_z(f'cabeza {k} (bajo la placa)', x, y, 2.75, z_sens_inf - hc, z_sens_inf, 'herraje')
        cil_z(f'cabeza {k} (sobre el brazo)', x, y, 2.75, z_brazo_sup, z_brazo_sup + hc, 'herraje')
    caja('placa de sensores', x_sens_tras, D['x_frente_sensores'], -W_p/2, W_p/2, z_sens_inf, z_sens_sup, 'pcb', 'frente en arco')
    for ref, (kx, ky, r_, capa, lib) in ps.huellas.items():
        if ref.startswith('OP'):
            x, y = ms(kx, ky)
            caja(f'TCRT5000 {ref}', x - 3.5, x + 3.5, y - 3.5, y + 3.5, z_lente, z_sens_inf, 'sensor')
    caja('rueda loca', x_loca - loca[1]/2, x_loca + loca[1]/2, -loca[0]/2, loca[0]/2, 0.0, v('loca_h_montaje'), 'loca', 'altura de montaje sin medir (R03)')
    for s in (1, -1):
        cil_z(f'espaciador rueda loca {s:+d}', x_loca, s*7.5, hx, v('loca_h_montaje'), z_brazo_inf, 'herraje')
    caja('interruptor KCD1', x_kcd - kcd[0]/2 + 0.2, x_kcd + kcd[0]/2 - 0.2, y_kcd - kcd[1]/2 + 0.2, y_kcd + kcd[1]/2 - 0.2, z_brazo_sup - kcd[3], z_brazo_sup, 'kcd1',
         'cuerpo bajo el bisel dentro del recorte; el ajuste real se prueba en prueba_kerf.dxf')
    # zonas que deben quedar libres por encima (accesibilidad)
    acceso = {}
    for ref, nom in (('SW2', 'START'), ('SW3', 'CAL'), ('SW4', 'RESET')):
        c = [cc for cc in pp.cuerpos if cc[0] == ref][0]
        p1 = mp(c[2], c[3]); p2 = mp(c[4], c[5])
        acceso[nom] = dict(x=(min(p1[0], p2[0]), max(p1[0], p2[0])), y=(min(p1[1], p2[1]), max(p1[1], p2[1])), z0=z_pcb_inf + esp_pcb)
    acceso['USB-C (enchufe, 30 mm hacia atrás)'] = dict(x=(D['x_pcb_principal'] - 30, D['x_pcb_principal']), y=(-6, 6), z0=z_pcb_inf + esp_pcb)
    acceso['KCD1'] = dict(x=(x_kcd - kcd[0]/2, x_kcd + kcd[0]/2), y=(y_kcd - kcd[1]/2, y_kcd + kcd[1]/2), z0=z_brazo_sup)

    alturas = dict(z_base_inf=z_base_inf, z_base_sup=z_base_sup, z_tapa_inf=z_tapa_inf, z_tapa_sup=z_tapa_sup,
                   z_pcb_principal_inf=z_pcb_inf, z_brazo_inf=z_brazo_inf, z_brazo_sup=z_brazo_sup,
                   z_sensores_sup=z_sens_sup, z_sensores_inf=z_sens_inf, z_lente_tcrt=z_lente,
                   espaciador_rueda_loca=z_brazo_inf - v('loca_h_montaje'), tope_rueda=2*R, holgura_tapa_rueda=z_tapa_inf - 2*R)
    pos = dict(x_eje=x_eje, x_muesca=x_muesca, x_ventilador=x_vent, x_rueda_loca=x_loca, x_sensores_trasero=x_sens_tras,
               x_kcd1=(x_kcd, y_kcd), bateria=(x_bat0, x_bat1), separadores_base_tapa=sb, union_J0=j0,
               agujeros_pcb_principal=hp, agujeros_pcb_sensores=hs, J1_sensores=j1, y_rueda_interior=y_in, y_rueda_exterior=y_out)
    info = dict(pp=pp, ps=ps, mp=mp, ms=ms, L_p=L_p, W_p=W_p, L_s=L_s, alturas=alturas, pos=pos, solidos=sol, acceso=acceso)
    return piezas, info

# --------------------------------------------------------------------------------------------- salida
def commit_base():
    try:
        h = subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip()
        b = subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', '--abbrev-ref', 'HEAD'], text=True).strip()
        return h, b
    except Exception:
        return 'desconocido', 'desconocida'

def texto_a_trazos(msp, txt, x, y, h, capa):
    try:
        from ezdxf.addons import text2path
        from ezdxf.fonts import fonts
        from ezdxf.math import Matrix44
        paths = text2path.make_paths_from_str(txt, fonts.FontFace(family='DejaVu Sans'), size=h)
        paths = [p.transform(Matrix44.translate(x, y, 0)) for p in paths]
        ezdxf.path.render_lwpolylines(msp, paths, distance=0.05, dxfattribs={'layer': capa})
        return 'trazos'
    except Exception:
        msp.add_text(txt, height=h, dxfattribs={'layer': capa}).set_placement((x, y))
        return 'TEXT'

def escribir_dxf(p, ruta, meta):
    doc = ezdxf.new('R2010', setup=True)
    doc.units = units.MM
    doc.header['$INSUNITS'] = 4; doc.header['$MEASUREMENT'] = 1; doc.header['$LUNITS'] = 2
    doc.layers.add('CORTE', color=1); doc.layers.add('GRABADO', color=5)
    for k, val in meta.items():
        doc.header.custom_vars.append(k, str(val))
    msp = doc.modelspace()
    for c in p.cortes:
        if c['tipo'] == 'circle':
            msp.add_circle(c['c'], c['r'], dxfattribs={'layer': 'CORTE'})
        else:
            msp.add_lwpolyline(c['pts'], format='xyb', close=True, dxfattribs={'layer': 'CORTE'})
    for g in p.grabados:
        if g['tipo'] == 'linea':
            msp.add_lwpolyline(g['pts'], dxfattribs={'layer': 'GRABADO'})
        elif g['tipo'] == 'poly':
            msp.add_lwpolyline(g['pts'], close=True, dxfattribs={'layer': 'GRABADO'})
        else:
            texto_a_trazos(msp, g['txt'], g['x'], g['y'], g['h'], 'GRABADO')
    doc.saveas(ruta)

def dibujar_pieza(ax, p, color='tab:red', grab='tab:blue', etiquetas=True, alpha=1.0):
    for c in p.cortes:
        if c['tipo'] == 'circle':
            ax.add_patch(Circle(c['c'], c['r'], fill=False, ec=color, lw=0.9, alpha=alpha))
        else:
            P = muestrear(c['pts'])
            ax.add_patch(MPoly(P, closed=True, fill=False, ec=color, lw=1.1 if c.get('exterior') else 0.9, alpha=alpha))
    for g in p.grabados:
        if g['tipo'] in ('linea', 'poly'):
            xs = [q[0] for q in g['pts']]; ys = [q[1] for q in g['pts']]
            if g['tipo'] == 'poly': xs.append(xs[0]); ys.append(ys[0])
            ax.plot(xs, ys, color=grab, lw=0.7, ls='--' if g['tipo'] == 'poly' else '-', alpha=alpha)
        else:
            ax.text(g['x'], g['y'], g['txt'], fontsize=6, color=grab, alpha=alpha)

def vista_pieza(p, ruta, titulo, estado):
    xs, ys = [], []
    for c in p.cortes:
        if c.get('exterior'):
            P = muestrear(c['pts']); xs += [q[0] for q in P]; ys += [q[1] for q in P]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    fig, ax = plt.subplots(figsize=(10, 10 * (y1 - y0 + 40) / (x1 - x0 + 60)))
    dibujar_pieza(ax, p)
    ax.annotate('', (x0, y0 - 8), (x1, y0 - 8), arrowprops=dict(arrowstyle='<->', lw=0.8))
    ax.text((x0 + x1)/2, y0 - 12, f'{x1 - x0:.2f} mm', ha='center', fontsize=9)
    ax.annotate('', (x1 + 8, y0), (x1 + 8, y1), arrowprops=dict(arrowstyle='<->', lw=0.8))
    ax.text(x1 + 10, (y0 + y1)/2, f'{y1 - y0:.2f} mm', va='center', rotation=90, fontsize=9)
    n = 1
    for c in p.cortes:
        if c.get('exterior'):
            continue
        if c['tipo'] == 'circle':
            x, y = c['c']
        else:
            P = muestrear(c['pts']); x = sum(q[0] for q in P)/len(P); y = sum(q[1] for q in P)/len(P)
        ax.text(x + 1.8, y + 1.8, str(n), fontsize=6.5, color='k')
        n += 1
    ax.set_xlim(x0 - 15, x1 + 25); ax.set_ylim(y0 - 20, y1 + 12); ax.set_aspect('equal')
    ax.grid(True, lw=0.3, alpha=0.4)
    ax.set_title(f'{titulo} — {estado}\nrojo = CORTE, azul = GRABADO; coordenadas del robot (X al frente, Y a la izquierda), mm', fontsize=9)
    fig.tight_layout(); fig.savefig(ruta, dpi=160); plt.close(fig)

def vistas_ensamble(piezas, info, ruta_sup, ruta_lat):
    a = info['alturas']; pos = info['pos']
    fig, ax = plt.subplots(figsize=(13, 7.5))
    ax.add_patch(Rectangle((0, -50), 200, 100, fill=False, ec='k', lw=1.4, ls='--'))
    ax.text(1, 51, 'caja del reglamento 200 x 100 mm', fontsize=8)
    colores = dict(base='tab:red', tapa='tab:green', brazo_sensores='tab:purple')
    for k in ('base', 'tapa', 'brazo_sensores'):
        dibujar_pieza(ax, piezas[k], color=colores[k], grab=colores[k], alpha=0.85)
    for s in info['solidos']:
        if s['tipo'] == 'rueda':
            ax.add_patch(Rectangle((s['c'][0] - s['r'], s['y'][0]), 2*s['r'], s['y'][1] - s['y'][0], fc='0.3', alpha=0.35))
        elif s['tipo'] == 'caja' and s['grupo'] in ('motor', 'bateria', 'ventilador', 'loca', 'kcd1', 'sensor'):
            c = dict(motor='tab:brown', bateria='gold', ventilador='tab:cyan', pcb='tab:olive', loca='k', kcd1='tab:orange', sensor='tab:gray')[s['grupo']]
            ax.add_patch(Rectangle((s['x'][0], s['y'][0]), s['x'][1] - s['x'][0], s['y'][1] - s['y'][0], fill=s['grupo'] != 'pcb', fc=c, ec=c, alpha=0.25 if s['grupo'] != 'pcb' else 0.9, lw=0.8))
    for pcb, mapf, col in ((info['pp'], info['mp'], 'olive'), (info['ps'], info['ms'], 'olive')):
        for tipo, d in pcb.borde:
            if tipo == 'gr_rect':
                (a1, b1), (a2, b2) = d['start'], d['end']
                P = [mapf(a1, b1), mapf(a2, b1), mapf(a2, b2), mapf(a1, b2), mapf(a1, b1)]
                ax.plot([q[0] for q in P], [q[1] for q in P], color=col, lw=1.3)
            elif tipo == 'gr_line':
                P = [mapf(*d['start']), mapf(*d['end'])]; ax.plot([q[0] for q in P], [q[1] for q in P], color=col, lw=1.3)
            elif tipo == 'gr_arc':
                P = [mapf(*d['start']), mapf(*d['mid']), mapf(*d['end'])]
                ax.plot([q[0] for q in P], [q[1] for q in P], color=col, lw=1.3, ls=':')
    for nom, z in info['acceso'].items():
        ax.add_patch(Rectangle((z['x'][0], z['y'][0]), z['x'][1] - z['x'][0], z['y'][1] - z['y'][0], fill=False, ec='tab:blue', lw=1.2))
        ax.text(z['x'][0], z['y'][1] + 0.8, nom, fontsize=6.5, color='tab:blue')
    ax.set_xlim(-35, 205); ax.set_ylim(-56, 58); ax.set_aspect('equal'); ax.grid(True, lw=0.3, alpha=0.4)
    ax.set_title('Ensamble, vista superior (rojo base, verde tapa, morado brazo; olivo PCB; gris ruedas con ancho ESTIMADO)', fontsize=9)
    fig.tight_layout(); fig.savefig(ruta_sup, dpi=150); plt.close(fig)

    fig, ax = plt.subplots(figsize=(13, 5.2))
    ax.axhline(0, color='k', lw=1.2); ax.text(1, -2.5, 'piso', fontsize=8)
    for s in info['solidos']:
        if s['tipo'] == 'rueda' and s['y'][0] > 0:
            ax.add_patch(Circle(s['c'], s['r'], fc='0.3', alpha=0.35, ec='k'))
        elif s['tipo'] == 'placa':
            P = [q for c in piezas[s['pieza']].cortes if c.get('exterior') for q in muestrear(c['pts'])]
            x0, x1 = min(q[0] for q in P), max(q[0] for q in P)
            col = colores[s['pieza']]
            ax.add_patch(Rectangle((x0, s['z'][0]), x1 - x0, s['z'][1] - s['z'][0], fc=col, alpha=0.5))
            ax.text(x0 + 1, s['z'][1] + 0.6, s['n'], fontsize=7, color=col)
        elif s['tipo'] == 'caja' and (s['y'][1] > 0 or s['grupo'] in ('pcb', 'loca', 'ventilador', 'bateria')):
            c = dict(motor='tab:brown', bateria='gold', ventilador='tab:cyan', pcb='tab:olive', loca='k', kcd1='tab:orange', sensor='tab:gray').get(s['grupo'], '0.5')
            ax.add_patch(Rectangle((s['x'][0], s['z'][0]), s['x'][1] - s['x'][0], s['z'][1] - s['z'][0], fc=c, alpha=0.35, ec=c, lw=0.6))
        elif s['tipo'] == 'cil_z' and (s['c'][1] >= 0):
            ax.add_patch(Rectangle((s['c'][0] - s['r'], s['z'][0]), 2*s['r'], s['z'][1] - s['z'][0], fc='goldenrod', alpha=0.6))
    for k, val in (('base', a['z_base_inf']), ('tapa', a['z_tapa_inf']), ('PCB princ.', a['z_pcb_principal_inf']), ('lente TCRT', a['z_lente_tcrt'])):
        ax.text(-33, val, f'{k}: z={val:.2f}', fontsize=7, va='center')
    ax.set_xlim(-35, 205); ax.set_ylim(-4, 50); ax.set_aspect('equal'); ax.grid(True, lw=0.3, alpha=0.4)
    ax.set_title('Ensamble, vista lateral desde la izquierda (alturas con h_eje ESTIMADO = 5.0 mm; la PCB principal no muestra sus componentes)', fontsize=9)
    fig.tight_layout(); fig.savefig(ruta_lat, dpi=150); plt.close(fig)

def plantilla_taladro(info, ruta):
    """PDF A4 1:1 visto desde la cara de componentes, con las pistas para alinear y los agujeros nuevos."""
    from matplotlib.backends.backend_pdf import PdfPages
    W, H = 210.0, 297.0
    fig = plt.figure(figsize=(W/25.4, H/25.4)); ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W); ax.set_ylim(0, H); ax.set_aspect('equal'); ax.axis('off')
    bloques = [(info['pp'], AGUJEROS_PRINCIPAL, 'PCB PRINCIPAL (96 x 74) - vista desde la cara de componentes', 285.0),
               (info['ps'], AGUJEROS_SENSORES, 'PCB DE SENSORES (96 x 59) - vista desde la cara de componentes (los TCRT van abajo)', 165.0)]
    for pcb, ag, titulo, ytop in bloques:
        x0k, y0k, x1k, y1k = pcb.bbox
        ox = (W - (x1k - x0k)) / 2
        T = lambda kx, ky: (ox + (kx - x0k), ytop - 12 - (ky - y0k))
        ax.text(ox, ytop - 4, titulo, fontsize=7.5, weight='bold')
        for tipo, d in pcb.borde:
            if tipo == 'gr_rect':
                (a1, b1), (a2, b2) = d['start'], d['end']
                p1 = T(a1, b1); p2 = T(a2, b2)
                ax.add_patch(Rectangle((min(p1[0], p2[0]), min(p1[1], p2[1])), abs(p2[0]-p1[0]), abs(p2[1]-p1[1]), fill=False, lw=0.5, ec='k'))
            elif tipo == 'gr_line':
                p1 = T(*d['start']); p2 = T(*d['end']); ax.plot([p1[0], p2[0]], [p1[1], p2[1]], 'k', lw=0.5)
            elif tipo == 'gr_arc':
                pts = [T(*d['start']), T(*d['mid']), T(*d['end'])]
                (xa, ya), (xb, yb), (xc, yc) = pts
                den = 2*(xa*(yb-yc) + xb*(yc-ya) + xc*(ya-yb))
                ux = ((xa**2+ya**2)*(yb-yc) + (xb**2+yb**2)*(yc-ya) + (xc**2+yc**2)*(ya-yb)) / den
                uy = ((xa**2+ya**2)*(xc-xb) + (xb**2+yb**2)*(xa-xc) + (xc**2+yc**2)*(xb-xa)) / den
                rr = math.hypot(xa-ux, ya-uy)
                a0 = math.atan2(ya-uy, xa-ux); a2 = math.atan2(yc-uy, xc-ux)
                if a2 < a0: a2 += 2*math.pi
                am = math.atan2(yb-uy, xb-ux)
                if am < a0: am += 2*math.pi
                if not (a0 <= am <= a2): a0, a2 = a2, a0 + 2*math.pi
                ts = [a0 + (a2-a0)*i/80 for i in range(81)]
                ax.plot([ux + rr*math.cos(q) for q in ts], [uy + rr*math.sin(q) for q in ts], 'k', lw=0.5)
        for s in pcb.segs:
            p1 = T(s[0], s[1]); p2 = T(s[2], s[3])
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color='0.25' if s[5] == 'F.Cu' else '0.7', lw=max(0.3, 2*s[4]*2.835*0.35), solid_capstyle='round')
        for bx, by, br, ref, tipo in pcb.pads:
            if tipo != 'np_thru_hole':
                c = T(bx, by); ax.add_patch(Circle(c, br*0.8, fc='0.45', ec='none'))
        for k, (kx, ky) in ag.items():
            c = T(kx, ky)
            ax.add_patch(Circle(c, 1.6, fill=False, ec='red', lw=0.6))
            ax.add_patch(Circle(c, 3.7, fill=False, ec='red', lw=0.35, ls='--'))
            ax.plot([c[0]-5, c[0]+5], [c[1], c[1]], 'r', lw=0.3); ax.plot([c[0], c[0]], [c[1]-5, c[1]+5], 'r', lw=0.3)
            dxl = kx - x0k; dyt = ky - y0k
            ax.text(c[0] + 4.2, c[1] + 1.0, f'{k}', fontsize=6.5, color='red', weight='bold')
            ax.text(c[0] + 4.2, c[1] - 2.2, f'{dxl:.2f} del borde izq., {dyt:.2f} del borde sup.', fontsize=4.8, color='red')
    ax.plot([20, 70], [12, 12], 'k', lw=1.0); ax.plot([20, 20], [10, 14], 'k', lw=1.0); ax.plot([70, 70], [10, 14], 'k', lw=1.0)
    ax.text(20, 15, 'Comprobar: esta barra mide 50.0 mm. Imprimir al 100 % (sin "ajustar a la página").', fontsize=6.5)
    ax.text(20, 5, 'Círculo rojo = broca 3.2 mm (M3). Círculo punteado = zona que debe quedar sin cobre (r 3.7 mm) en las dos caras.', fontsize=6)
    ax.text(20, 1.5, 'Gris oscuro = cobre de arriba; gris claro = cobre de abajo (visto a través). Punzonar en la cruz, broca piloto 1.5 mm y luego 3.2 mm.', fontsize=6)
    with PdfPages(ruta) as pdf:
        pdf.savefig(fig)
    plt.close(fig)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--kerf', type=float, default=None)
    a = ap.parse_args()
    piezas, info = construir(a.kerf)
    h, rama = commit_base()
    estado_kerf = 'PENDIENTE DE KERF (geometría nominal)' if a.kerf is None else f'compensado para kerf {a.kerf:.3f} mm'
    estados = {'base': 'PROVISIONAL', 'tapa': 'PROVISIONAL', 'brazo_sensores': 'PROVISIONAL', 'prueba_kerf': 'PRUEBA'}
    (CF / 'vistas').mkdir(exist_ok=True); (CF / 'plantillas').mkdir(exist_ok=True)
    nombres = {'base': 'base.dxf', 'tapa': 'tapa.dxf', 'brazo_sensores': 'brazo_sensores.dxf', 'prueba_kerf': 'prueba_kerf.dxf'}
    for k, p in piezas.items():
        meta = dict(PIEZA=k, ESTADO=f'{estados[k]} - {estado_kerf}', UNIDADES='mm, escala 1:1', MATERIAL='acrilico 3 mm',
                    RAMA=rama, COMMIT_BASE=h, PCB_PRINCIPAL_MD5=info['pp'].md5, PCB_SENSORES_MD5=info['ps'].md5,
                    GENERADO=datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), GENERADOR='mecanica/chasis_final/herramientas/generar_chasis.py')
        escribir_dxf(p, CF / nombres[k], meta)
        vista_pieza(p, CF / 'vistas' / f'{k}.png', nombres[k], f'{estados[k]} · {estado_kerf}')
    vistas_ensamble(piezas, info, CF / 'vistas' / 'ensamble_superior.png', CF / 'vistas' / 'ensamble_lateral.png')
    plantilla_taladro(info, CF / 'plantillas' / 'plantilla_taladro_pcb_1a1.pdf')
    # modelo para el verificador
    modelo = dict(commit_base=h, rama=rama, kerf=a.kerf, pcb_md5=dict(principal=info['pp'].md5, sensores=info['ps'].md5),
                  alturas=info['alturas'], pos={k: (v_ if not isinstance(v_, dict) else v_) for k, v_ in info['pos'].items()},
                  solidos=info['solidos'], acceso=info['acceso'], diseno=D,
                  agujeros_kicad=dict(principal=AGUJEROS_PRINCIPAL, sensores=AGUJEROS_SENSORES),
                  piezas={k: dict(cortes=[{kk: vv for kk, vv in c.items()} for c in p.cortes]) for k, p in piezas.items()})
    (CF / 'herramientas' / 'modelo.json').write_text(json.dumps(modelo, indent=1, ensure_ascii=False))
    # tabla de medidas
    filas = ['| Clave | Valor | Clase | Fuente |', '|---|---|---|---|']
    for k, m in M.items():
        val = m['valor']; val = '—' if val is None else (' x '.join(str(q) for q in val) if isinstance(val, tuple) else str(val))
        filas.append(f"| `{k}` | {val} | **{m['clase']}** | {m['fuente']} |")
    (CF / 'medidas.md').write_text('# Medidas usadas por el chasis (generado por generar_chasis.py; no editar a mano)\n\n'
                                   f'Rama `{rama}`, commit base `{h}`. Editar `herramientas/parametros.py` y regenerar.\n\n' + '\n'.join(filas) + '\n')
    print('commit base:', h, 'rama:', rama)
    print('alturas:', {k: round(x, 2) for k, x in info['alturas'].items()})
    print('posiciones:', json.dumps(info['pos'], ensure_ascii=False, default=lambda o: round(o, 2) if isinstance(o, float) else o)[:1500])

if __name__ == '__main__':
    main()
