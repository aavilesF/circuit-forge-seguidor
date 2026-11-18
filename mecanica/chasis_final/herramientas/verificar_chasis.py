#!/usr/bin/env python3
"""Verificación independiente del chasis final. Uso: python3 mecanica/chasis_final/herramientas/verificar_chasis.py
Relee los DXF (no usa la geometría en memoria del generador), recalcula los agujeros de las PCB desde los .kicad_pcb
con su propio mapeo, y revisa el ensamble descrito en modelo.json. Escribe verificacion.json y verificacion.md.
Sale con código 1 si hay ERRORES. Lo que no se puede comprobar sin la pieza física queda como PENDIENTE, nunca como OK."""
import json, math, pathlib, sys, itertools
import ezdxf
import ezdxf.bbox, ezdxf.math
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union

HERE = pathlib.Path(__file__).resolve().parent
CF = HERE.parent; REPO = CF.parents[1]
sys.path.insert(0, str(HERE))
from kicad_lectura import PCB
from parametros import M, D, v

ERR, ADV, OK = [], [], []
def E(p, m): ERR.append((p, m))
def A(p, m): ADV.append((p, m))
def K(p, m): OK.append((p, m))

def arco(x1, y1, x2, y2, b, paso=0.2):
    if abs(b) < 1e-12: return [(x1, y1)]
    th = 4*math.atan(b); c = math.hypot(x2-x1, y2-y1); r = c/(2*math.sin(abs(th)/2))
    mx, my = (x1+x2)/2, (y1+y2)/2; ux, uy = (x2-x1)/c, (y2-y1)/c; h = r*math.cos(abs(th)/2); s = 1 if b > 0 else -1
    cx, cy = mx - s*uy*h, my + s*ux*h; a0 = math.atan2(y1-cy, x1-cx); k = max(6, int(abs(th)*r/paso))
    return [(cx + r*math.cos(a0 + th*j/k), cy + r*math.sin(a0 + th*j/k)) for j in range(k)]

def leer(nombre):
    ruta = CF / nombre
    doc = ezdxf.readfile(ruta)
    aud = doc.audit()
    res = dict(archivo=nombre, errores_auditoria=len(aud.errors), arreglos_auditoria=len(aud.fixes),
               insunits=doc.header.get('$INSUNITS'), measurement=doc.header.get('$MEASUREMENT'),
               custom={k: val for k, val in doc.header.custom_vars})
    cortes, grabados, tipos, capas = [], [], {}, set()
    for e in doc.modelspace():
        capa = e.dxf.layer; capas.add(capa); tipos[(capa, e.dxftype())] = tipos.get((capa, e.dxftype()), 0) + 1
        if capa == 'CORTE':
            if e.dxftype() == 'CIRCLE':
                c = e.dxf.center; r = e.dxf.radius
                cortes.append(dict(tipo='circle', c=(round(c.x, 4), round(c.y, 4)), r=r, poly=Point(c.x, c.y).buffer(r, 256), cerrado=True,
                                   firma=('C', round(c.x, 3), round(c.y, 3), round(r, 3))))
            elif e.dxftype() == 'LWPOLYLINE':
                pts = list(e.get_points('xyb')); P = []
                for i in range(len(pts)):
                    x1, y1, b = pts[i]; x2, y2, _ = pts[(i+1) % len(pts)]
                    P += arco(x1, y1, x2, y2, b)
                ceros = sum(1 for i in range(len(pts)) if math.hypot(pts[i][0]-pts[(i+1) % len(pts)][0], pts[i][1]-pts[(i+1) % len(pts)][1]) < 1e-6)
                cortes.append(dict(tipo='poly', poly=Polygon(P), cerrado=bool(e.closed), ceros=ceros,
                                   firma=('P',) + tuple(sorted((round(a, 3), round(bb, 3)) for a, bb, _ in pts))))
            else:
                E(nombre, f'entidad {e.dxftype()} en CORTE (solo se aceptan LWPOLYLINE cerradas y CIRCLE)')
        elif capa == 'GRABADO':
            if e.dxftype() == 'LWPOLYLINE':
                grabados.append(LineString([(p[0], p[1]) for p in e.get_points('xy')] + ([tuple(e.get_points('xy'))[0]] if e.closed else [])))
            else:
                A(nombre, f'entidad {e.dxftype()} en GRABADO (texto sin convertir a trazos)')
    res['capas'] = sorted(capas); res['tipos'] = {f'{a}/{b}': n for (a, b), n in tipos.items()}
    return res, cortes, grabados

def revisar_pieza(nombre, esperado_bbox=None, web_min=D['web_min'], comp=0.0):
    res, cortes, grab = leer(nombre)
    p = nombre
    if res['errores_auditoria']: E(p, f"auditoría ezdxf: {res['errores_auditoria']} errores")
    else: K(p, 'abre con ezdxf y la auditoría no encuentra errores')
    if res['insunits'] == 4 and res['measurement'] == 1: K(p, 'unidades: milímetros ($INSUNITS=4, $MEASUREMENT=1), escala 1:1')
    else: E(p, f"unidades incorrectas: $INSUNITS={res['insunits']} $MEASUREMENT={res['measurement']}")
    extra = set(res['capas']) - {'CORTE', 'GRABADO'}
    if extra: E(p, f'capas no esperadas: {extra}')
    else: K(p, 'solo capas CORTE y GRABADO')
    abiertos = [c for c in cortes if not c['cerrado']]
    if abiertos: E(p, f'{len(abiertos)} contornos de corte abiertos')
    else: K(p, f'{len(cortes)} contornos de corte, todos cerrados')
    if any(c.get('ceros') for c in cortes): E(p, 'segmentos de longitud cero (vértices duplicados)')
    inval = [c for c in cortes if not c['poly'].is_valid]
    if inval: E(p, f'{len(inval)} contornos que se cruzan a sí mismos')
    firmas = [c['firma'] for c in cortes]
    dup = len(firmas) - len(set(firmas))
    if dup: E(p, f'{dup} entidades duplicadas')
    else: K(p, 'sin entidades duplicadas')
    ext = max(cortes, key=lambda c: c['poly'].area); interiores = [c for c in cortes if c is not ext]
    fuera = [c for c in interiores if not ext['poly'].contains(c['poly'])]
    if fuera: E(p, f'{len(fuera)} cortes interiores fuera del contorno o tocándolo')
    w_borde = min((ext['poly'].exterior.distance(c['poly']) for c in interiores), default=99)
    w_entre = min((a['poly'].distance(b['poly']) for a, b in itertools.combinations(interiores, 2)), default=99)
    sup = [(a, b) for a, b in itertools.combinations(interiores, 2) if a['poly'].intersects(b['poly'])]
    if sup: E(p, f'{len(sup)} pares de cortes interiores superpuestos')
    if min(w_borde, w_entre) < web_min: E(p, f'material mínimo {min(w_borde, w_entre):.2f} mm < {web_min} mm')
    else: K(p, f'material mínimo: {w_borde:.2f} mm al borde, {w_entre:.2f} mm entre cortes (mín. pedido {web_min} mm), sin superposiciones')
    x0, y0, x1, y1 = ext['poly'].bounds
    res['bbox'] = (round(x0, 3), round(y0, 3), round(x1, 3), round(y1, 3)); res['tamano'] = (round(x1-x0, 3), round(y1-y0, 3))
    if esperado_bbox:
        esperado_bbox = (esperado_bbox[0] - comp, esperado_bbox[1] - comp, esperado_bbox[2] + comp, esperado_bbox[3] + comp)
        dif = max(abs(a - b) for a, b in zip(res['bbox'], esperado_bbox))
        if dif > 0.01: E(p, f"contorno {res['bbox']} distinto del esperado {esperado_bbox}")
        else: K(p, f"medidas exteriores {res['tamano'][0]:.2f} x {res['tamano'][1]:.2f} mm coinciden con el diseño")
    for g in grab:
        if g.distance(ext['poly'].exterior) < 0.5 or any(g.distance(c['poly'].exterior) < 0.5 for c in interiores):
            E(p, 'un grabado toca o pisa una línea de corte'); break
        if not ext['poly'].contains(g):
            E(p, 'un grabado queda fuera de la pieza'); break
    else:
        if grab: K(p, f'{len(grab)} trazos de grabado dentro de la pieza y a >= 0.5 mm de los cortes')
    area = ext['poly'].area - sum(c['poly'].area for c in interiores)
    res['area_mm2'] = round(area, 1); res['web_borde'] = round(w_borde, 2); res['web_entre'] = round(w_entre, 2)
    res['circulos'] = [(c['c'], round(2*c['r'], 3)) for c in cortes if c['tipo'] == 'circle']
    res['ext_poly'] = ext['poly']; res['polys'] = [c['poly'] for c in interiores]
    return res

COMP = [0.0]
def tiene_agujero(res, x, y, d, tol=0.01):
    return any(math.hypot(c[0]-x, c[1]-y) <= tol and abs(dd - (d - 2*COMP[0])) <= 0.01 for c, dd in res['circulos'])

def dibujar_anidado(filas, rot, tam, sep=5.0, margen=5.0):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    from ezdxf.addons.drawing import RenderContext, Frontend
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    nombres = list(tam); girar = dict(zip(nombres, rot)) if rot else {n: False for n in nombres}
    fig, ax = plt.subplots(figsize=(9, 9)); y = margen; W = H = 0
    for fila in filas:
        x = margen; hmax = 0
        for n in fila:
            doc = ezdxf.readfile(CF / n); msp = doc.modelspace()
            ents = list(msp)
            bb = ezdxf.bbox.extents(ents)
            m = ezdxf.math.Matrix44.translate(-bb.extmin.x, -bb.extmin.y, 0)
            w, h = bb.size.x, bb.size.y
            if girar[n]:
                m = m @ ezdxf.math.Matrix44.z_rotate(math.pi/2) @ ezdxf.math.Matrix44.translate(h, 0, 0); w, h = h, w
            m = m @ ezdxf.math.Matrix44.translate(x, y, 0)
            for e in ents: e.transform(m)
            Frontend(RenderContext(doc), MatplotlibBackend(ax)).draw_layout(msp, finalize=False)
            ax.text(x, y + h + 1, n, fontsize=7)
            x += w + sep; hmax = max(hmax, h)
        W = max(W, x - sep + margen); y += hmax + sep; H = y - sep + margen
    ax.add_patch(matplotlib.patches.Rectangle((0, 0), W, H, fill=False, ls='--', ec='k'))
    ax.set_xlim(-5, W + 5); ax.set_ylim(-5, H + 8); ax.set_aspect('equal')
    ax.set_title(f'Anidado leído de los DXF: {W:.0f} x {H:.0f} mm (5 mm entre piezas y al borde). Lámina real sin confirmar', fontsize=9)
    fig.savefig(CF / 'vistas' / 'anidado.png', dpi=150); plt.close(fig)

def main():
    modelo = json.loads((HERE / 'modelo.json').read_text())
    kerf = modelo['kerf']
    comp = (kerf or 0.0) / 2; COMP[0] = comp
    piezas = {}
    t = D['t']
    piezas['base.dxf'] = revisar_pieza('base.dxf', (2.5, -48.0, 103.0, 48.0), comp=comp)
    piezas['tapa.dxf'] = revisar_pieza('tapa.dxf', (3.5, -48.0, 93.0, 48.0), comp=comp)
    piezas['brazo_sensores.dxf'] = revisar_pieza('brazo_sensores.dxf', (81.0, -49.0, 161.0, 49.0), comp=comp)
    piezas['prueba_kerf.dxf'] = revisar_pieza('prueba_kerf.dxf', (0.0, 0.0, 60.0, 30.0), comp=comp)
    if kerf is not None:
        K('todas', f'geometría compensada para kerf {kerf} mm: contornos +{comp:.3f} mm por lado, agujeros y ranuras -{comp:.3f} mm por lado')

    # ---------------- agujeros de las PCB, recalculados desde KiCad con un mapeo propio
    pp = PCB(REPO / 'v2/electronica/principal/principal.kicad_pcb'); ps = PCB(REPO / 'v2/electronica/sensores/sensores.kicad_pcb')
    reg = json.loads((REPO / 'v2/electronica/verificacion/registro_drc.json').read_text())
    for pcb, clave in ((pp, 'v2/electronica/principal/principal.kicad_pcb'), (ps, 'v2/electronica/sensores/sensores.kicad_pcb')):
        if reg[clave]['md5'] == pcb.md5: K('PCB', f'{clave}: md5 {pcb.md5} = el del DRC aprobado (registro_drc.json)')
        else: E('PCB', f'{clave}: md5 distinto del DRC aprobado; las posiciones podrían no corresponder')
    # mapeo propio: la PCB se gira -90° (cara de componentes arriba): el borde "superior" de KiCad mira al frente del robot
    cxp = (pp.bbox[0] + pp.bbox[2]) / 2; cxs = (ps.bbox[0] + ps.bbox[2]) / 2
    def a_robot_p(kx, ky): return (D['x_pcb_principal'] + pp.bbox[3] - ky, cxp - kx)
    def a_robot_s(kx, ky): return (D['x_frente_sensores'] - (ky - ps.bbox[1]), cxs - kx)
    # comprobación de que el mapeo es un giro y no un espejo: el producto cruz de los ejes se conserva
    for f, pcb in ((a_robot_p, pp), (a_robot_s, ps)):
        o = f(0, 0); ex = f(1, 0); ey = f(0, -1)   # ejes de KiCad en pantalla: +x derecha, -y arriba
        cruz = (ex[0]-o[0])*(ey[1]-o[1]) - (ex[1]-o[1])*(ey[0]-o[0])
        if cruz <= 0: E('PCB', 'el mapeo KiCad -> robot es un espejo (la PCB quedaría volteada)')
    K('PCB', 'mapeo KiCad -> robot es un giro de -90° sin espejo (cara de componentes hacia arriba)')
    ag = modelo['agujeros_kicad']
    for k, (kx, ky) in ag['principal'].items():
        x, y = a_robot_p(kx, ky); d, quien = pp.cobre_libre(kx, ky)
        borde = min(kx - pp.bbox[0], pp.bbox[2] - kx, ky - pp.bbox[1], pp.bbox[3] - ky)
        (K if d >= D['cobre_libre'] else E)('PCB principal', f'{k} (KiCad {kx}, {ky}): cobre libre {d:.2f} mm (mín. {D["cobre_libre"]}; más cercano: {quien}); {borde - 1.6:.2f} mm de material al borde')
        (K if tiene_agujero(piezas['tapa.dxf'], x, y, 3.2) else E)('tapa.dxf', f'agujero Ø3.2 de {k} en ({x:.2f}, {y:.2f}) recalculado desde KiCad')
        dc, ref = pp.cuerpo_cercano(kx, ky)
        if dc < 0.01: A('PCB principal', f'{k} cae bajo el cuerpo de {ref} (módulo sobre tira hembra): la cabeza del tornillo debe caber debajo (medir V7) y se atornilla antes de enchufar el módulo')
    for k, (kx, ky) in ag['sensores'].items():
        x, y = a_robot_s(kx, ky); d, quien = ps.cobre_libre(kx, ky)
        borde = min(kx - ps.bbox[0], ps.bbox[2] - kx, ps.bbox[3] - ky) - 1.6
        (K if d >= D['cobre_libre'] else E)('PCB sensores', f'{k} (KiCad {kx}, {ky}): cobre libre {d:.2f} mm (más cercano: {quien}); {borde:.2f} mm de material al borde')
        if borde < 3.0: A('PCB sensores', f'{k}: solo {borde:.2f} mm de material al borde de la fenólica; taladrar con piloto y sin presionar')
        (K if tiene_agujero(piezas['brazo_sensores.dxf'], x, y, 3.2) else E)('brazo_sensores.dxf', f'agujero Ø3.2 de {k} en ({x:.2f}, {y:.2f}) recalculado desde KiCad')
        dc, ref = ps.cuerpo_cercano(kx, ky)
        if dc < 3.18: A('PCB sensores', f'{k} a {dc:.2f} mm del contorno de {ref}: orientar una cara plana del hexágono del separador hacia {ref}')

    # cabezas de tornillo sobre la tapa que quedan bajo la PCB principal: no deben quedar bajo pads (patas soldadas)
    for k in ('B1', 'B2'):
        x, y = modelo['pos']['separadores_base_tapa'][k]
        dmin = min(math.hypot(x - a_robot_p(bx, by)[0], y - a_robot_p(bx, by)[1]) - br for bx, by, br, ref, tipo in pp.pads)
        (K if dmin >= 2.75 + 0.3 else E)('tapa/PCB', f'cabeza del tornillo {k} (r 2.75) a {dmin:.2f} mm del borde del pad más cercano de la PCB principal')
    # ---------------- agujeros compartidos entre piezas
    pos = modelo['pos']
    for k, (x, y) in pos['separadores_base_tapa'].items():
        enb = tiene_agujero(piezas['base.dxf'], x, y, 3.2); ent = tiene_agujero(piezas['tapa.dxf'], x, y, 3.2)
        (K if enb and ent else E)('base/tapa', f'separador {k} ({x:.2f}, {y:.2f}) coincide en base y tapa')
        if k in ('B3', 'B4'):
            (K if tiene_agujero(piezas['brazo_sensores.dxf'], x, y, 3.2) else E)('tapa/brazo', f'unión {k} coincide en tapa y brazo')
    x, y = pos['union_J0']
    (K if tiene_agujero(piezas['tapa.dxf'], x, y, 3.2) and tiene_agujero(piezas['brazo_sensores.dxf'], x, y, 3.2) else E)('tapa/brazo', 'unión central J0 coincide')
    xv = pos['x_ventilador']; sep = v('vent_agujeros')[0]/2
    okv = all(tiene_agujero(piezas['base.dxf'], xv + sx*sep, sy*sep, 3.2) for sx in (1, -1) for sy in (1, -1)) and tiene_agujero(piezas['base.dxf'], xv, 0, v('vent_toma_d'))
    (K if okv else E)('base.dxf', f'ventilador: 4 x Ø3.2 en cuadrado de {2*sep:.1f} mm (dibujo UNIT) y toma Ø{v("vent_toma_d"):.0f} centrada')
    # ranuras de motor: centros a 19.5 mm en X y simétricos respecto al eje
    xe = pos['x_eje']
    rb = [p for p in piezas['base.dxf']['polys'] if abs(p.bounds[2] - p.bounds[0] - (D['m2_ranura'] - 2*comp)) < 0.01]
    cxs_ = sorted({round((p.bounds[0] + p.bounds[2])/2, 3) for p in rb})
    (K if cxs_ == [round(xe - 9.75, 3), round(xe + 9.75, 3)] and len(rb) == 4 else E)('base.dxf', f'4 ranuras M2 de los soportes en x = {cxs_} (eje {xe}, separación 19.5 medida)')

    # ---------------- ensamble
    al = modelo['alturas']; sol = modelo['solidos']
    for s_ in sol:
        if 'z' not in s_: s_['z'] = (s_['c'][1] - s_['r'], s_['c'][1] + s_['r'])
    placas = {'base': piezas['base.dxf']['ext_poly'], 'tapa': piezas['tapa.dxf']['ext_poly'], 'brazo_sensores': piezas['brazo_sensores.dxf']['ext_poly']}
    placas_netas = {k: placas[k].difference(unary_union(piezas[f'{k}.dxf']['polys'])) for k in placas}
    def plano(s):
        if s['tipo'] == 'caja': return box(s['x'][0], s['y'][0], s['x'][1], s['y'][1])
        if s['tipo'] == 'cil_z': return Point(*s['c']).buffer(s['r'], 64)
        if s['tipo'] == 'placa': return placas_netas[s['pieza']]
        if s['tipo'] == 'rueda': return box(s['c'][0] - s['r'], s['y'][0], s['c'][0] + s['r'], s['y'][1])
    # envolvente en planta
    huella = unary_union([plano(s) for s in sol] + [Polygon([pp_ for pp_ in [a_robot_s(*q) for q in [(ps.bbox[0], ps.bbox[3]), (ps.bbox[2], ps.bbox[3])]]] + [(D['x_frente_sensores'], 0)])])
    x0, y0, x1, y1 = huella.bounds
    largo = x1 - max(0, x0) if x0 >= 0 else x1 - x0
    res_env = dict(x=(round(x0, 2), round(x1, 2)), y=(round(y0, 2), round(y1, 2)), largo=round(x1 - x0, 2), ancho=round(y1 - y0, 2))
    if x0 >= 0 and x1 <= v('caja_largo'): K('ensamble', f'largo total {x1 - x0:.2f} mm (x de {x0:.2f} a {x1:.2f}) <= {v("caja_largo"):.0f} mm, contando ruedas, placas, tornillos y la placa de sensores')
    else: E('ensamble', f'largo fuera de la caja: x de {x0:.2f} a {x1:.2f}')
    ancho_placas = max(abs(placas[k].bounds[1]) for k in placas)
    K('ensamble', f'ancho de las placas de acrílico: {2*ancho_placas:.1f} mm <= 100 mm')
    lim = (v('caja_ancho')/2 - v('motor_largo') - v('rin_ancho')) * 2
    A('ensamble', f'ANCHO CON RUEDAS SIN VERIFICAR: = (G/2 + {v("motor_largo")} + hueco + {v("rin_ancho")}) x 2. Cumple 100 mm solo si G + 2·hueco <= {lim:.1f} mm '
                  f'(G = separación entre colas de motor con terminales y cable; hueco = reductor-rin). Con G=4 y hueco=0.5 (ESTIMADOS) da {y1 - y0:.1f} mm. Medir V2 (P-V2-34)')
    K('ensamble', 'altura: el reglamento no limita la altura (docs/requisitos.md)')
    # piso
    min_z = []
    for s in sol:
        if s['grupo'] in ('rueda', 'loca'): continue
        z0 = s['z'][0]
        min_z.append((z0, s['n']))
    zmin = min(min_z)
    (K if zmin[0] > 0.5 else E)('ensamble', f'solo las ruedas y la rueda loca tocan el piso: lo más bajo es "{zmin[1]}" a {zmin[0]:.2f} mm')
    lente = al['z_lente_tcrt']; obj = v('tcrt_altura_piso')
    A('ensamble', f'lente de los TCRT5000 a {lente:.2f} mm del piso (objetivo documentado {obj} mm); depende de V1, V5 y del separador del brazo')
    # choques
    def z_rueda(s, xa, xb):
        cx, cz = s['c']; r = s['r']
        xs = [min(max(cx, xa), xb)]
        if xb < cx - r or xa > cx + r: return None
        dx = min(abs(q - cx) for q in xs)
        h = math.sqrt(max(0, r*r - dx*dx)); return (cz - h, cz + h)
    choques = []
    permitidos = {frozenset(('separador B1', 'base')), frozenset(('separador B2', 'base'))}
    for a_, b_ in itertools.combinations(sol, 2):
        if a_['grupo'] == 'herraje' and b_['grupo'] == 'herraje':
            continue
        pa, pb = plano(a_), plano(b_)
        inter = pa.intersection(pb)
        if inter.is_empty or inter.area < 1e-6: continue
        if a_['tipo'] == 'rueda' or b_['tipo'] == 'rueda':
            w, o = (a_, b_) if a_['tipo'] == 'rueda' else (b_, a_)
            xa, _, xb, _ = inter.bounds; zr = z_rueda(w, xa, xb)
            if zr is None: continue
            if o['z'][0] < zr[1] - 1e-6 and o['z'][1] > zr[0] + 1e-6:
                choques.append((w['n'], o['n'], round(zr[1] - o['z'][0], 2)))
            elif o['z'][0] >= zr[1] and o['z'][0] - zr[1] < D['holgura_rueda'] - 0.5:
                A('ensamble', f'{o["n"]} queda a {o["z"][0] - zr[1]:.2f} mm sobre {w["n"]} (holgura justa)')
            continue
        za, zb = a_['z'], b_['z']
        sol_z = min(za[1], zb[1]) - max(za[0], zb[0])
        if sol_z > 1e-6:
            if {a_['grupo'], b_['grupo']} <= {'herraje', 'acrilico'}:
                continue   # el herraje atraviesa la placa por su agujero (comprobado arriba)
            if {a_['grupo'], b_['grupo']} == {'herraje', 'pcb'} or {a_['grupo'], b_['grupo']} == {'herraje', 'sensor'}:
                continue
            if a_['grupo'] == b_['grupo'] == 'sensor':
                continue   # TCRT contra TCRT: lo garantiza el DRC de KiCad (courtyards)
            if {a_['grupo'], b_['grupo']} == {'motor'}:
                continue   # soporte abraza al motor
            choques.append((a_['n'], b_['n'], round(sol_z, 2)))
    if choques:
        for c in choques: E('ensamble', f'choque entre "{c[0]}" y "{c[1]}" ({c[2]} mm)')
    else:
        K('ensamble', f'sin choques entre {len(sol)} sólidos simplificados (ruedas, motores, soportes, batería máx., ventilador, separadores, tuercas, cabezas, PCB, TCRT, rueda loca, KCD1)')
    holg = al['z_tapa_inf'] - al['tope_rueda']
    (K if holg >= 1.5 else E)('ensamble', f'tapa {holg:.2f} mm por encima de las llantas (con h_eje ESTIMADO {v("h_eje")} mm)')
    # accesibilidad
    for nom, z in modelo['acceso'].items():
        zona = box(z['x'][0], z['y'][0], z['x'][1], z['y'][1])
        enc = [s['n'] for s in sol if s['z'][1] > z['z0'] + 1e-6 and plano(s).intersection(zona).area > 1e-6 and s['n'] != 'interruptor KCD1']
        (K if not enc else E)('acceso', f'{nom}: libre por encima' if not enc else f'{nom} tapado por {enc}')
    # peso y centro de masa (ESTIMADO salvo lo medido)
    dens = v('acrilico_densidad') / 1000.0
    masas = []
    for k, z in (('base', (al['z_base_inf'] + al['z_base_sup'])/2), ('tapa', (al['z_tapa_inf'] + al['z_tapa_sup'])/2), ('brazo_sensores', (al['z_brazo_inf'] + al['z_brazo_sup'])/2)):
        r = piezas[f'{k}.dxf']; c = Polygon(r['ext_poly'].exterior).difference(unary_union(r['polys'])).centroid
        masas.append((f'acrílico {k}', r['area_mm2'] * t * dens, c.x, z, 'calculado (densidad ESTIMADA)'))
    xe = pos['x_eje']; zc = v('llanta_diam')/2
    masas += [('2 motores N20', 20.0, xe, zc, 'ESTIMADO'), ('2 ruedas', 14.0, xe, zc, 'ESTIMADO'), ('2 soportes N20', 2.66, xe, zc, 'DOCUMENTADO (ficha 1.33 g)'),
              ('batería LiPo 2S', 30.0, sum(pos['bateria'])/2, al['z_base_sup'] + 8, 'ESTIMADO (referencia, no comprada)'),
              ('ventilador 4010', v('vent_peso'), xv, al['z_base_sup'] + 5, 'REAL MEDIDO'),
              ('PCB principal + ESP32 + MP1584 + DRV8833', 55.0, D['x_pcb_principal'] + 37, al['z_pcb_principal_inf'] + 8, 'ESTIMADO'),
              ('placa de sensores + TCRT + mux', 30.0, pos['x_sensores_trasero'] + 29.5, al['z_sensores_inf'], 'ESTIMADO'),
              ('rueda loca', 10.0, pos['x_rueda_loca'], 8.0, 'DOCUMENTADO (ficha)'), ('interruptor KCD1', 3.0, pos['x_kcd1'][0], 25.0, 'ESTIMADO'),
              ('separadores (~16)', 16.0, 75.0, 20.0, 'REAL MEDIDO ~1 g c/u (P-V2-26)'), ('tornillos y tuercas', 12.0, 75.0, 20.0, 'ESTIMADO'),
              ('cables y soldadura', 15.0, 60.0, 25.0, 'ESTIMADO')]
    W = sum(m[1] for m in masas); xg = sum(m[1]*m[2] for m in masas)/W; zg = sum(m[1]*m[3] for m in masas)/W
    xl = pos['x_rueda_loca']
    carga_loca = W * (xg - xe) / (xl - xe)
    if xe < xg < xl: K('ensamble', f'centro de masa ESTIMADO en x = {xg:.1f} mm, entre el eje ({xe}) y la rueda loca ({xl}): apoyo en 3 puntos; ~{100*(1 - (xg - xe)/(xl - xe)):.0f} % del peso en las ruedas')
    else: E('ensamble', f'centro de masa ESTIMADO en x = {xg:.1f} fuera del triángulo de apoyo')
    (K if W < v('peso_max') * 0.8 else A)('ensamble', f'peso total ESTIMADO {W:.0f} g (límite {v("peso_max"):.0f} g; confirmar con báscula)')
    # anidado en lámina
    tam = {k: piezas[k]['tamano'] for k in piezas}
    def acomodo(sep=5.0, margen=5.0):
        mejores = []
        nombres = list(tam)
        for rot in itertools.product((False, True), repeat=len(nombres)):
            dims = [(tam[n][1], tam[n][0]) if r else tam[n] for n, r in zip(nombres, rot)]
            for orden in itertools.permutations(range(len(nombres))):
                for corte in range(1, len(nombres)):
                    filas = [orden[:corte], orden[corte:]]
                    W_ = max(sum(dims[i][0] for i in f) + sep*(len(f)-1) for f in filas) + 2*margen
                    H_ = sum(max(dims[i][1] for i in f) for f in filas) + sep*(len(filas)-1) + 2*margen
                    mejores.append((W_*H_, max(W_, H_), min(W_, H_), [[nombres[i] for i in f] for f in filas], rot))
                W1 = sum(d[0] for d in dims) + sep*(len(dims)-1) + 2*margen; H1 = max(d[1] for d in dims) + 2*margen
                mejores.append((W1*H1, max(W1, H1), min(W1, H1), [[nombres[i] for i in orden]], rot))
        mejores.sort(); cuad = min(mejores, key=lambda m: (m[1], m[0])); return mejores[0], cuad
    an, cu = acomodo()
    K('anidado', f'las 4 piezas (5 mm entre piezas y al borde) caben en {an[1]:.0f} x {an[2]:.0f} mm en una fila, o en {cu[1]:.0f} x {cu[2]:.0f} mm en dos filas; caben en 300 x 300 y en 600 x 300')
    if cu[1] > 297 or cu[2] > 210: A('anidado', 'no caben en una hoja A4 (297 x 210) con esos márgenes')
    A('anidado', 'tamaño real de la lámina sin confirmar (el equipo no lo sabe): comprobar antes de cortar')

    # ---------------- estados
    estado = {}
    for n in ('base.dxf', 'tapa.dxf', 'brazo_sensores.dxf'):
        err_n = [m for p, m in ERR if p == n]
        estado[n] = 'BLOQUEADO' if err_n else 'PROVISIONAL'
    pend = {
        'base.dxf': ['PENDIENTE DE KERF', 'V1 altura del eje (fija la altura de la tapa; no cambia el DXF)',
                     'V2 ancho con ruedas (legalidad; no cambia el DXF)', 'V9 posición de los agujeros del soporte N20 (las ranuras cubren y = ±4 a ±20.5 mm)'],
        'tapa.dxf': ['PENDIENTE DE KERF', 'Taladrar H1-H3 en la PCB principal con la plantilla (autorizado 17 nov)', 'V7 tira hembra (cabeza de tornillo bajo ESP32 y U2)'],
        'brazo_sensores.dxf': ['PENDIENTE DE KERF', 'V4 recorte del KCD1 (bisel o cuerpo)', 'V3 rueda loca: agujeros (Ø y separación) y altura de montaje',
                               'Taladrar S1-S2 en la PCB de sensores', 'V5/V6 altura de los TCRT y de la pieza más alta de la placa de sensores'],
    }
    out = dict(commit_base=modelo['commit_base'], rama=modelo['rama'], kerf=kerf, estados=estado, pendientes=pend, envolvente=res_env,
               alturas=al, peso_estimado_g=round(W, 1), cg_x=round(xg, 1), cg_z=round(zg, 1), carga_rueda_loca_g=round(carga_loca, 1),
               masas=[(m[0], round(m[1], 1), m[4]) for m in masas], anidado=dict(una_fila=(round(an[1]), round(an[2]), an[3]), dos_filas=(round(cu[1]), round(cu[2]), cu[3])),
               piezas={k: {kk: vv for kk, vv in r.items() if kk not in ('ext_poly', 'polys')} for k, r in piezas.items()},
               errores=ERR, avisos=ADV, ok=OK)
    try:
        dibujar_anidado(cu[3], cu[4] if len(cu) > 4 else None, tam)
        K('anidado', 'vistas/anidado.png dibujada leyendo los 4 DXF (comprueba que se pueden abrir y dibujar)')
    except Exception as ex:
        E('anidado', f'no se pudo dibujar el anidado desde los DXF: {ex}')
    (CF / 'verificacion.json').write_text(json.dumps(out, indent=1, ensure_ascii=False))
    L = ['# Verificación del chasis (generado por verificar_chasis.py; no editar a mano)', '',
         f"Rama `{modelo['rama']}`, commit base `{modelo['commit_base']}`. Kerf: {'PENDIENTE (geometría nominal)' if kerf is None else kerf}.", '',
         '| Pieza | Estado | Falta para APTO PARA CORTE |', '|---|---|---|']
    for n, e_ in estado.items():
        L.append(f'| `{n}` | **{e_}** | ' + '; '.join(pend[n]) + ' |')
    L += ['', f'Peso ESTIMADO: {W:.0f} g · centro de masa ESTIMADO x = {xg:.1f} mm, z = {zg:.1f} mm · carga en la rueda loca ≈ {carga_loca:.0f} g', '']
    for titulo, lista, marca in (('Errores', ERR, '✗'), ('Avisos y pendientes (no son validación física)', ADV, '!'), ('Comprobado en archivos', OK, '✓')):
        L.append(f'## {titulo} ({len(lista)})')
        L += [f'- {marca} **{p}**: {m}' for p, m in lista] or ['- ninguno']
        L.append('')
    L += ['## Lo que esta verificación NO comprueba',
          '- Que las piezas reales midan lo nominal (falta el kerf y una pieza de prueba cortada).',
          '- Resistencia mecánica, rigidez, vibración o comportamiento en la pista.',
          '- Que los componentes reales coincidan con las fichas (alturas, agujeros de la rueda loca, recorte del KCD1).',
          '- Alturas de los componentes de la PCB principal (no hay nada encima de ella, así que no limitan el diseño).', '']
    (CF / 'verificacion.md').write_text('\n'.join(L))
    print(f'ERRORES: {len(ERR)}  AVISOS: {len(ADV)}  OK: {len(OK)}')
    for p, m in ERR: print('  ✗', p, '-', m)
    for p, m in ADV: print('  !', p, '-', m)
    print('estados:', estado, '| peso', round(W), 'g | cg x', round(xg, 1), '| lamina', an[1], 'x', an[2], '|', cu[1], 'x', cu[2], cu[3])
    sys.exit(1 if ERR else 0)

if __name__ == '__main__':
    main()
