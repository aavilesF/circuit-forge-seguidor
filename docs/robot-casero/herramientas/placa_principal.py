#!/usr/bin/env python3
"""HISTÓRICO (11 nov 2026): plan B sustituido por las PCB de doble cara de electronica/kicad (D18, D20). No usar para fabricar.

Robot casero · placa principal en placa fenólica de UNA cara, rejilla de 2.54 mm.

Este script es la única fuente del layout: de aquí salen los dibujos y la tabla de conexiones,
y antes de dibujar se COMPRUEBA que:
  1. cada red (GND, VBAT, AIN1, ...) queda unida por pistas de cobre, sin depender de la suerte;
  2. ninguna pista pasa por un agujero o pista de otra red (en una cara no se pueden cruzar);
  3. ningún componente alto choca con otro.
Si algo falla, el script se detiene y dice qué y dónde. Ejecutar:  python3 placa_principal.py

Coordenadas: (x, y) en agujeros de la rejilla, x hacia la derecha y y hacia abajo, VISTO DESDE EL LADO
DE LOS COMPONENTES. El agujero (0, 0) está arriba a la izquierda.
"""
import os, sys, math, json
from collections import defaultdict

PASO = 2.54                      # mm entre agujeros
NX, NY = 34, 32                  # agujeros usados: x 0..33, y 0..31
ML, MT, MR, MB = 4.0, 4.0, 3.0, 3.0   # márgenes (mm) del contorno a los agujeros de las orillas
ANCHO = ML + (NX - 1) * PASO + MR
ALTO = MT + (NY - 1) * PASO + MB
PAD = 2.0                        # diámetro de pad normal (mm)
PAD_GRANDE = 3.0                 # pads de cables de batería y motores
BROCA = 0.8

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.normpath(os.path.join(AQUI, '..', 'placa'))

# ----------------------------------------------------------------------------------------------
# Componentes
# ----------------------------------------------------------------------------------------------
# cuerpo: rectángulo (x0, y0, x1, y1) en unidades de rejilla o ('c', cx, cy, r) círculo
# alto: mm sobre la placa; base: mm a los que empieza el cuerpo (módulos en headers hembra ≈ 8.5)
COMP = {}


def comp(ref, nombre, pads, cuerpo, alto, base=0.0, nota='', etiqueta_en=None, color='#d9e6f2'):
    COMP[ref] = dict(ref=ref, nombre=nombre, pads=pads, cuerpo=cuerpo, alto=alto, base=base, nota=nota,
                     etiqueta_en=etiqueta_en, color=color)


# --- U1 · ESP32 DevKit de 30 pines, USB-C hacia ARRIBA (filas a 25.4 mm). Orden de pines de la
#     serigrafía (especificaciones-componentes.md, M03). Va en 2 tiras de header hembra 1×15.
ESP_IZQ = ['3V3', 'GND', 'D15', 'D2', 'D4', 'D16', 'D17', 'D5', 'D18', 'D19', 'D21', 'RX0', 'TX0', 'D22', 'D23']
ESP_DER = ['VIN', 'GND', 'D13', 'D12', 'D14', 'D27', 'D26', 'D25', 'D33', 'D32', 'D35', 'D34', 'VN', 'VP', 'EN']
RED_ESP = {
    '3V3': '3V3', 'GND': 'GND', 'D15': 'NFAULT_ESP', 'D4': 'ZUMB', 'D16': 'NSLEEP', 'D18': 'START',
    'D19': 'AIN1', 'D21': 'AIN2', 'D22': 'BIN1', 'D23': 'BIN2',
    'VIN': 'VIN_ESP', 'D13': 'EMIS', 'D14': 'CAL', 'D27': 'A1', 'D26': 'A2', 'D25': 'A3', 'D33': 'A4',
    'D32': 'A5', 'D35': 'A6', 'D34': 'A7', 'VN': 'A8', 'VP': 'VBAT_ADC',
}
EXI, EXD, EY0 = 14, 24, 4
pads = []
for i, p in enumerate(ESP_IZQ):
    pads.append((p, EXI, EY0 + i, RED_ESP.get(p)))
for i, p in enumerate(ESP_DER):
    pads.append((p + ' ', EXD, EY0 + i, RED_ESP.get(p)))   # espacio: GND aparece en ambos lados
# cuerpo del DevKit 51 × 28 mm (54 con USB-C): ~6 mm de vuelo arriba (USB) y ~9 mm abajo (antena) [estimado]
comp('U1', 'ESP32 DevKit 30 pines (USB-C arriba)', pads,
     (EXI - 0.55, EY0 - 2.4, EXD + 0.55, EY0 + 14 + 3.5), alto=13.0, base=8.5,
     nota='Va en 2 tiras de header hembra 1×15. NO soldar el DevKit directo.', color='#cfe3cf')

# --- U4 · módulo DRV8833 girado 180° respecto a la foto: fila de entradas a la derecha (mira al ESP32).
#     Foto (M10): izq. IN4 IN3 GND VCC IN2 IN1 / der. EEP OUT1 OUT2 OUT3 OUT4 ULT, de arriba abajo.
DRV_IN = [('IN1', 'AIN1'), ('IN2', 'AIN2'), ('VCC', 'VM'), ('GND', 'GND'), ('IN3', 'BIN1'), ('IN4', 'BIN2')]
DRV_OUT = [('ULT', 'NFAULT'), ('OUT4', 'MD_B'), ('OUT3', 'MD_A'), ('OUT2', 'MI_B'), ('OUT1', 'MI_A'), ('EEP', 'NSLEEP')]
DXO, DXI, DY0 = 5, 11, 13
pads = [(n, DXI, DY0 + i, r) for i, (n, r) in enumerate(DRV_IN)] + \
       [(n, DXO, DY0 + i, r) for i, (n, r) in enumerate(DRV_OUT)]
comp('U4', 'Módulo DRV8833 (girado: entradas hacia el ESP32)', pads,
     (DXO - 0.55, DY0 - 0.55, DXI + 0.55, DY0 + 5.55), alto=13.0, base=8.5,
     nota='Va en 2 tiras de header hembra 1×6. Puente J1 SIN soldar (D14).', color='#f2dcdc')

# --- U2 · MP1584 #1 (sale 5.0 V) y U3 · MP1584 #2 (sale 6.0 V, motores). 22 × 17 mm.
#     Se pegan con cinta doble cara y cada terminal se une a su pad con un trozo de alambre (pata de resistencia).
def mp1584(ref, x0, y0, nombre, red_out):
    # girado 180° respecto a la foto (M13): IN a la izquierda, OUT a la derecha
    comp(ref, nombre, [('IN+', x0, y0, 'VBAT'), ('IN-', x0, y0 + 6, 'GND'),
                       ('OUT+', x0 + 8, y0, red_out), ('OUT-', x0 + 8, y0 + 6, 'GND')],
         (x0 - 0.35, y0 - 0.35, x0 + 8.35, y0 + 6.35), alto=4.5,
         nota='Ajustar el voltaje ANTES de soldarlo. Patas de alambre a los 4 pads.', color='#dcd9f2')


mp1584('U2', 1, 0, 'MP1584 #1 → 5.0 V (lógica)', '5V')
mp1584('U3', 1, 24, 'MP1584 #2 → 6.0 V (motores)', 'VM')

# --- Diodo D2 1N5822: 5 V del MP1584 → VIN del ESP32 (evita que el USB alimente el 5 V y viceversa)
comp('D2', '1N5822 (5V → VIN)', [('A', 11, 0, '5V'), ('K', 17, 0, 'VIN_ESP')],
     (12.1, -0.55, 15.9, 0.55), alto=5.5, nota='Franja (cátodo) hacia la DERECHA. Agujeros de 1.3–1.5 mm.')
# D1 1N5822 de polaridad: va EN EL CABLE de la batería, no en la placa (ver CONEXIONES.md)

# --- Capacitores
comp('C1', '470 µF 16 V (VBAT)', [('+', 0, 10, 'VBAT'), ('-', 2, 10, 'GND')], ('c', 1, 10, 1.58), alto=13,
     nota='Electrolítico: la franja (−) hacia la DERECHA.')
comp('C2', '100 nF (VBAT)', [('1', 0, 12, 'VBAT'), ('2', 2, 12, 'GND')], (-0.2, 11.6, 2.2, 12.4), alto=6)
comp('C4', '470 µF 16 V (VM)', [('+', 8, 22, 'VM'), ('-', 10, 22, 'GND')], ('c', 9, 22, 1.58), alto=13,
     nota='Franja (−) hacia la DERECHA.')
comp('C5', '100 nF (VM)', [('1', 8, 20, 'VM'), ('2', 10, 20, 'GND')], (7.9, 19.6, 10.1, 20.4), alto=6)
comp('C6', '100 nF (filtro ADC)', [('1', 26, 17, 'VBAT_ADC'), ('2', 26, 18, 'GND')], (25.6, 16.9, 26.4, 18.1), alto=6)

# --- Resistencias (1/4 W acostadas = 4 agujeros; paradas = 1 agujero)
comp('R1', '100 kΩ (divisor batería)', [('1', 0, 31, 'VBAT'), ('2', 4, 31, 'VBAT_ADC')], (0.7, 30.6, 3.3, 31.4), alto=2.5)
comp('R2', '33 kΩ parada (divisor)', [('1', 11, 31, 'VBAT_ADC'), ('2', 11, 30, 'GND')], (10.6, 29.6, 11.4, 31.4), alto=10)
comp('R4', '1 kΩ parada (base Q1)', [('1', 29, 6, 'EMIS'), ('2', 30, 6, 'Q1B')], (28.6, 5.6, 30.4, 6.4), alto=10)
comp('R5', '1 kΩ (base Q2)', [('1', 16, 21, 'ZUMB'), ('2', 16, 25, 'Q2B')], (15.6, 21.7, 16.4, 24.3), alto=2.5)

# --- Transistores 2N2222 (TO-92). E-B-C en el orden de los pads; el orden de patas del tuyo se mide (P05)
comp('Q1', '2N2222 (emisores IR)', [('E', 31, 5, 'GND'), ('B', 31, 6, 'Q1B'), ('C', 31, 7, 'EMIT_K')],
     (30.4, 4.5, 31.9, 7.5), alto=8, nota='Medir E-B-C antes (P05). La pata del centro siempre es B.')
comp('Q2', '2N2222 (zumbador)', [('C', 18, 24, 'ZUMB_K'), ('B', 18, 25, 'Q2B'), ('E', 18, 26, 'GND')],
     (17.4, 23.5, 18.9, 26.5), alto=8, nota='Medir E-B-C antes (P05).')

# --- Botones de 4 patas (6×6): se usan 2 patas en DIAGONAL (siempre quedan en contactos distintos)
def boton(ref, x, y, red, nombre):
    comp(ref, nombre, [('sig', x + 2, y, red), ('nc1', x, y, None), ('nc2', x + 2, y + 2, None), ('gnd', x, y + 2, 'GND')],
         (x - 0.2, y - 0.2, x + 2.2, y + 2.2), alto=5, nota='Solo se conectan 2 patas en diagonal.')


boton('SW2', 13, 24, 'START', 'START (botón 6×6)')
comp('SW3', 'CAL (botón 6×6)', [('sig', 23, 24, 'CAL'), ('nc1', 25, 24, None), ('nc2', 23, 26, None), ('gnd', 25, 26, 'GND')],
     (22.8, 23.8, 25.2, 26.2), alto=5, nota='Solo se conectan 2 patas en diagonal.')

# --- Conectores (header macho 2.54 o cables soldados)
comp('J1', 'BAT+ (del interruptor y D1)', [('+', 0, 7, 'VBAT')], (-0.6, 6.4, 0.6, 7.6), alto=0, nota='Cable 18 AWG')
comp('J2', 'BAT− (GND)', [('-', 2, 7, 'GND')], (1.4, 6.4, 2.6, 7.6), alto=0, nota='Cable 18 AWG')
comp('J3', 'Motor DERECHO', [('OUT4', 3, 14, 'MD_B'), ('OUT3', 3, 15, 'MD_A')], (2.5, 13.5, 3.5, 15.5), alto=0)
comp('J4', 'Motor IZQUIERDO', [('OUT2', 3, 16, 'MI_B'), ('OUT1', 3, 17, 'MI_A')], (2.5, 15.5, 3.5, 17.5), alto=0)
comp('J5', 'Sensores: alimentación (1×5)', [('3V3', 28, 3, '3V3'), ('5V', 28, 4, 'VIN_ESP'), ('GND', 28, 5, 'GND'),
                                            ('LED_ON', 28, 6, 'EMIS'), ('EMIT−', 28, 7, 'EMIT_K')],
     (27.5, 2.5, 28.5, 7.5), alto=8.5)
comp('J6', 'Sensores: salidas analógicas (1×8)',
     [(f'A{i + 1}', 28, 9 + i, f'A{i + 1}') for i in range(8)], (27.5, 8.5, 28.5, 16.5), alto=8.5)
comp('J7', 'Zumbador (+ / −)', [('+', 21, 23, 'VIN_ESP'), ('-', 21, 24, 'ZUMB_K')], (20.5, 22.5, 21.5, 24.5), alto=8.5)

# --- Puente de soldadura JP1: nFAULT del DRV8833 → GPIO15. Se cierra SOLO después de medir (MANUAL, etapa 5)
comp('JP1', 'JP1 nFAULT (abierto)', [('a', 5, 11, 'NFAULT'), ('b', 5, 10, 'NFAULT_ESP')], (4.5, 9.5, 5.5, 11.5), alto=0,
     nota='Abierto de fábrica. Se une con una gota de soldadura tras medir ULT ≤ 3.3 V.')

# Conexiones internas de los módulos (no son pistas): el DevKit une sus 2 GND; el MP1584 une IN− con OUT−.
INTERNAS = [(('U1', 'GND'), ('U1', 'GND ')), (('U2', 'IN-'), ('U2', 'OUT-')), (('U3', 'IN-'), ('U3', 'OUT-'))]
# Redes que se aceptan unidas SOLO por dentro de un módulo (se avisa en el reporte)
SOLO_INTERNA_OK = {'GND'}

# ----------------------------------------------------------------------------------------------
# Pistas (lado cobre). w = ancho en mm. Solo tramos horizontales o verticales.
# ----------------------------------------------------------------------------------------------
PIST = []
SENAL, POT, MOT = 1.0, 1.5, 1.5


def pista(red, pts, w=SENAL):
    PIST.append(dict(red=red, pts=pts, w=w))


# Potencia
pista('VBAT', [(0, 0), (0, 31)], POT)                       # orilla izquierda: VBAT de arriba abajo
pista('VBAT', [(0, 0), (1, 0)], POT)                        # → U2 IN+
pista('VBAT', [(0, 24), (1, 24)], POT)                      # → U3 IN+
pista('GND', [(1, 6), (2, 6), (2, 30), (31, 30)], POT)     # columna GND (separada 2 agujeros de VBAT) + bus inferior
pista('GND', [(1, 6), (9, 6), (9, 5), (13, 5), (14, 5)], POT)     # U2 IN−/OUT− → GND del ESP32
pista('GND', [(1, 30), (2, 30)], POT)                       # U3 IN−
pista('GND', [(11, 16), (10, 16), (10, 30)], POT)           # GND del DRV8833 → bus
pista('VM', [(11, 15), (8, 15), (8, 23), (9, 23), (9, 24)], POT)  # VCC del DRV8833 ← U3 OUT+
pista('5V', [(9, 0), (11, 0)], POT)                         # U2 OUT+ → D2
pista('VIN_ESP', [(17, 0), (30, 0), (30, 4), (22, 4), (22, 23), (21, 23)], POT)  # D2 → J5 5V → VIN → zumbador
# Motores
pista('MD_B', [(5, 14), (3, 14)], MOT)
pista('MD_A', [(5, 15), (3, 15)], MOT)
pista('MI_B', [(5, 16), (3, 16)], MOT)
pista('MI_A', [(5, 17), (3, 17)], MOT)
# Control del DRV8833 (rectas al ESP32)
for red, y in (('AIN1', 13), ('AIN2', 14), ('BIN1', 17), ('BIN2', 18)):
    pista(red, [(DXI, y), (EXI, y)])
pista('NSLEEP', [(5, 18), (6, 18), (6, 9), (14, 9)])
pista('NFAULT', [(5, 13), (5, 11)])
pista('NFAULT_ESP', [(5, 10), (5, 7), (13, 7), (13, 6), (14, 6)])
# Sensores
pista('3V3', [(14, 4), (14, 2), (28, 2), (28, 3)])
pista('GND', [(24, 5), (31, 5)])
pista('EMIS', [(24, 6), (29, 6)])
pista('Q1B', [(30, 6), (31, 6)])
pista('EMIT_K', [(31, 7), (28, 7)])
for i in range(8):
    pista(f'A{i + 1}', [(EXD, 9 + i), (28, 9 + i)])
# Batería al ADC (divisor 100k/33k abajo a la izquierda; C6 junto al pin)
pista('VBAT_ADC', [(4, 31), (32, 31), (32, 17), (24, 17)])
pista('GND', [(26, 18), (26, 30)])
# Botones y zumbador
pista('START', [(14, 12), (15, 12), (15, 24)])
pista('GND', [(13, 26), (13, 30)])
pista('CAL', [(24, 8), (23, 8), (23, 24)])
pista('GND', [(25, 26), (25, 30)])
pista('ZUMB', [(14, 8), (16, 8), (16, 21)])
pista('Q2B', [(16, 25), (18, 25)])
pista('ZUMB_K', [(18, 24), (21, 24)])
pista('GND', [(18, 26), (18, 30)])

# Puentes de alambre por el lado de componentes (cruces). Ideal: ninguno.
PUENTES = []

# ----------------------------------------------------------------------------------------------
# Comprobaciones
# ----------------------------------------------------------------------------------------------
errores, avisos = [], []


def celdas(pts):
    out = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 != x1 and y0 != y1:
            raise SystemExit(f'Tramo diagonal no permitido: {(x0, y0)}→{(x1, y1)}')
        dx = (x1 > x0) - (x1 < x0)
        dy = (y1 > y0) - (y1 < y0)
        x, y = x0, y0
        out.append((x, y))
        while (x, y) != (x1, y1):
            x += dx
            y += dy
            out.append((x, y))
    return out


pad_en = {}            # (x, y) -> (ref, pin, red)
for c in COMP.values():
    for (pin, x, y, red) in c['pads']:
        if not (0 <= x < NX and 0 <= y < NY):
            errores.append(f'{c["ref"]}.{pin} fuera de la rejilla en {(x, y)}')
        if (x, y) in pad_en:
            errores.append(f'Dos pads en {(x, y)}: {pad_en[(x, y)][:2]} y {(c["ref"], pin)}')
        pad_en[(x, y)] = (c['ref'], pin, red)

cobre = {}             # (x, y) -> red de la pista
for t in PIST:
    for xy in celdas(t['pts']):
        if not (0 <= xy[0] < NX and 0 <= xy[1] < NY):
            errores.append(f'Pista {t["red"]} fuera de la rejilla en {xy}')
        if xy in pad_en and pad_en[xy][2] != t['red']:
            errores.append(f'Pista {t["red"]} pasa por el pad {pad_en[xy][0]}.{pad_en[xy][1]} ({pad_en[xy][2]}) en {xy}')
        if xy in cobre and cobre[xy] != t['red']:
            errores.append(f'Cruce: pista {t["red"]} con {cobre[xy]} en {xy}')
        cobre[xy] = t['red']

# separación: pista ancha (≥1.5 mm) junto a pad de otra red → 2.54 − 0.75 − 1.0 = 0.79 mm (aceptable, se avisa
# solo si el pad es grande)
for t in PIST:
    if t['w'] < 1.5:
        continue
    for (x, y) in celdas(t['pts']):
        for (ax, ay) in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            p = pad_en.get((ax, ay))
            if p and p[2] != t['red'] and p[0] in ('J1', 'J2'):
                avisos.append(f'Pista ancha {t["red"]} junto al pad grande {p[0]} en {(ax, ay)}')

# conectividad (unión-búsqueda sobre agujeros)
padre = {}


def raiz(a):
    padre.setdefault(a, a)
    while padre[a] != a:
        padre[a] = padre[padre[a]]
        a = padre[a]
    return a


def unir(a, b):
    padre[raiz(a)] = raiz(b)


for t in PIST:
    cs = celdas(t['pts'])
    for a, b in zip(cs, cs[1:]):
        unir(a, b)
for (red, a, b) in PUENTES:
    unir(a, b)
for xy in pad_en:
    raiz(xy)


def pos(ref, pin):
    for (p, x, y, r) in COMP[ref]['pads']:
        if p == pin:
            return (x, y)
    raise KeyError((ref, pin))


def grupos_por_red(con_internas):
    if con_internas:
        guard = dict(padre)
        for a, b in INTERNAS:
            unir(pos(*a), pos(*b))
    g = defaultdict(set)
    for xy, (ref, pin, red) in pad_en.items():
        if red:
            g[red].add(raiz(xy))
    mezcla = defaultdict(set)
    for xy, (ref, pin, red) in pad_en.items():
        if red:
            mezcla[raiz(xy)].add(red)
    if con_internas:
        padre.clear()
        padre.update(guard)
    return g, mezcla


g_placa, _ = grupos_por_red(False)
g_total, mezcla = grupos_por_red(True)
for raiz_, redes in mezcla.items():
    if len(redes) > 1:
        errores.append(f'Redes en corto entre sí: {sorted(redes)}')
for red, gs in g_total.items():
    if len(gs) > 1:
        sueltos = [f'{r}.{p}' for xy, (r, p, rr) in pad_en.items() if rr == red]
        errores.append(f'Red {red} partida en {len(gs)} pedazos: {sueltos}')
for red, gs in g_placa.items():
    if len(gs) > 1 and len(g_total[red]) == 1:
        trozos = defaultdict(list)
        for xy, (r, p, rr) in pad_en.items():
            if rr == red:
                trozos[raiz(xy)].append(f'{r}.{p.strip()}')
        menor = min(trozos.values(), key=len)
        (avisos if red in SOLO_INTERNA_OK else errores).append(
            f'Red {red}: {menor} se une al resto solo por dentro de un módulo')

# pistas que no tocan ningún pad de su red (pedazos de cobre inútiles)
for t in PIST:
    if not any(pad_en.get(xy, (0, 0, None))[2] == t['red'] for xy in celdas(t['pts'])) and \
            not any(raiz(xy) == raiz(pxy) for xy in celdas(t['pts'])[:1] for pxy, v in pad_en.items() if v[2] == t['red']):
        errores.append(f'Pista {t["red"]} {t["pts"]} no llega a ningún pad')

# choques de cuerpos (proyección en planta, por alturas)
def rect(c):
    b = c['cuerpo']
    if b[0] == 'c':
        _, cx, cy, r = b
        return (cx - r, cy - r, cx + r, cy + r)
    return b


refs = list(COMP)
for i, a in enumerate(refs):
    for b in refs[i + 1:]:
        A, B = COMP[a], COMP[b]
        if A['alto'] == 0 or B['alto'] == 0:
            continue
        ra, rb = rect(A), rect(B)
        sx = min(ra[2], rb[2]) - max(ra[0], rb[0])
        sy = min(ra[3], rb[3]) - max(ra[1], rb[1])
        if sx > 0.05 and sy > 0.05:
            # ¿uno queda por encima del otro? (módulos en headers hembra)
            if A['base'] >= B['alto'] - 0.5 or B['base'] >= A['alto'] - 0.5:
                continue
            if sx * sy > 0.15:
                errores.append(f'Choque de cuerpos {a} y {b} ({sx * PASO:.1f} × {sy * PASO:.1f} mm)')
            else:
                avisos.append(f'Cuerpos {a} y {b} se tocan apenas ({sx * PASO:.1f} × {sy * PASO:.1f} mm): inclinar uno')

# ----------------------------------------------------------------------------------------------
# Dibujo
# ----------------------------------------------------------------------------------------------
COLOR_RED = {'GND': '#1f1f1f', 'VBAT': '#c0392b', 'VM': '#d35400', '5V': '#e67e22', 'VIN_ESP': '#e67e22',
             '3V3': '#8e44ad'}
CARTA_W, CARTA_H = 215.9, 279.4
OX, OY = (CARTA_W - ANCHO) / 2, 28.0          # posición de la placa en la hoja


def mm(x, y, espejo=False):
    X = ML + x * PASO
    Y = MT + y * PASO
    if espejo:
        X = ANCHO - X
    return OX + X, OY + Y


def esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def texto(x, y, s, t=2.2, anc='middle', col='#222', peso='normal', rot=0):
    r = f' transform="rotate({rot} {x:.2f} {y:.2f})"' if rot else ''
    base = (f'<text x="{x:.2f}" y="{y:.2f}" font-family="DejaVu Sans, Arial" font-size="{t}" text-anchor="{anc}" '
            f'font-weight="{peso}"{r}')
    # halo blanco dibujado debajo (cairosvg no soporta paint-order)
    return (base + f' fill="none" stroke="#fff" stroke-width="{t * 0.28:.2f}" stroke-linejoin="round">{esc(s)}</text>'
            + base + f' fill="{col}">{esc(s)}</text>')


def regla(x, y):
    s = [f'<rect x="{x}" y="{y}" width="50" height="2.5" fill="none" stroke="#000" stroke-width="0.3"/>']
    for i in range(0, 51, 10):
        s.append(f'<line x1="{x + i}" y1="{y}" x2="{x + i}" y2="{y + 4}" stroke="#000" stroke-width="0.3"/>')
    s.append(texto(x + 25, y + 7.5, 'Esta barra debe medir 50 mm exactos al imprimir', 2.6))
    return '\n'.join(s)


def pistas_svg(espejo, negro):
    s = []
    for t in PIST:
        pts = ' '.join('%.2f,%.2f' % mm(x, y, espejo) for x, y in t['pts'])
        col = '#000' if negro else '#b87333'
        op = '1' if negro else '0.55'
        s.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-opacity="{op}" stroke-width="{t["w"]}" '
                 f'stroke-linecap="round" stroke-linejoin="round"/>')
    return s


def pads_svg(espejo, negro, agujero=True):
    s = []
    for (x, y), (ref, pin, red) in pad_en.items():
        X, Y = mm(x, y, espejo)
        d = PAD_GRANDE if ref in ('J1', 'J2') else PAD
        if ref in ('D2',):
            d = 2.6
        col = '#000' if negro else '#b87333'
        s.append(f'<circle cx="{X:.2f}" cy="{Y:.2f}" r="{d / 2}" fill="{col}"/>')
        if agujero:
            s.append(f'<circle cx="{X:.2f}" cy="{Y:.2f}" r="{BROCA / 2}" fill="#fff"/>')
    return s


def hoja(titulo, subtitulo, cuerpo, notas, escala=1.0):
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{CARTA_W}mm" height="{CARTA_H}mm" '
         f'viewBox="0 0 {CARTA_W} {CARTA_H}">', f'<rect width="{CARTA_W}" height="{CARTA_H}" fill="#fff"/>',
         texto(CARTA_W / 2, 12, titulo, 5.2, peso='bold'), texto(CARTA_W / 2, 19, subtitulo, 3.0, col='#444')]
    if escala == 1.0:
        s += cuerpo
        y = OY + ALTO + 12
        s.append(regla(CARTA_W / 2 - 25, y))
        y += 16
    else:
        ox2 = (CARTA_W - ANCHO * escala) / 2
        oy2 = 30.0
        s.append(f'<g transform="translate({ox2:.2f} {oy2:.2f}) scale({escala}) translate({-OX:.2f} {-OY:.2f})">')
        s += cuerpo
        s.append('</g>')
        y = oy2 + ALTO * escala + 9
        s.append(texto(CARTA_W / 2, y, f'ESCALA {escala:g}:1 — solo para leer y armar. NO usar esta hoja para taladrar.',
                       3.2, peso='bold', col='#a00'))
        y += 9
    for n in notas:
        s.append(texto(16, y, n, 3.0, anc='start'))
        y += 5.2
    s.append('</svg>')
    return '\n'.join(s)


def contorno(relleno):
    x, y = OX, OY
    return f'<rect x="{x:.2f}" y="{y:.2f}" width="{ANCHO:.2f}" height="{ALTO:.2f}" fill="{relleno}" stroke="#000" stroke-width="0.35"/>'


def vista_componentes():
    s = [contorno('#f6efe0')]
    for xx in range(NX):            # rejilla tenue (referencia para contar agujeros)
        for yy in range(NY):
            X, Y = mm(xx, yy)
            s.append(f'<circle cx="{X:.2f}" cy="{Y:.2f}" r="0.18" fill="#c8bfae"/>')
    s += pistas_svg(False, False)
    for c in COMP.values():
        b = c['cuerpo']
        if b[0] == 'c':
            _, cx, cy, r = b
            X, Y = mm(cx, cy)
            s.append(f'<circle cx="{X:.2f}" cy="{Y:.2f}" r="{r * PASO:.2f}" fill="{c["color"]}" fill-opacity="0.55" '
                     f'stroke="#333" stroke-width="0.25"/>')
        else:
            X0, Y0 = mm(b[0], b[1])
            X1, Y1 = mm(b[2], b[3])
            s.append(f'<rect x="{X0:.2f}" y="{Y0:.2f}" width="{X1 - X0:.2f}" height="{Y1 - Y0:.2f}" fill="{c["color"]}" '
                     f'fill-opacity="{0.35 if c["base"] > 0 else 0.6}" stroke="#333" stroke-width="0.25" '
                     f'stroke-dasharray="{"1.2,0.8" if c["base"] > 0 else "none"}"/>')
    s += pads_svg(False, False)
    # etiquetas de pines
    for c in COMP.values():
        for (pin, x, y, red) in c['pads']:
            X, Y = mm(x, y)
            p = pin.strip()
            if c['ref'] == 'U1':
                dx = 1.5 if x == EXI else -1.5
                s.append(texto(X + dx, Y + 0.55, p, 1.45, 'start' if x == EXI else 'end', '#145214', 'bold'))
            elif c['ref'] == 'U4':
                dx = 1.4 if x == DXO else -1.4
                s.append(texto(X + dx, Y + 0.55, p, 1.35, 'start' if x == DXO else 'end', '#8b1a1a', 'bold'))
            elif c['ref'] in ('J5', 'J6'):
                s.append(texto(X - 1.4, Y + 0.55, p, 1.35, 'end', '#0b3d91', 'bold'))
            elif c['ref'] in ('U2', 'U3'):
                s.append(texto(X + (1.4 if pin.startswith('IN') else -1.4), Y + (2.4 if y in (0, 24) else -1.4),
                               p, 1.6, 'start' if pin.startswith('IN') else 'end', '#3b2f8f'))
            elif c['ref'] in ('Q1', 'Q2', 'C1', 'C4'):
                s.append(texto(X + 1.4, Y + 0.6, p, 1.5, 'start', '#333'))
            elif c['ref'] in ('J7',):
                s.append(texto(X + 1.6, Y + 0.6, p, 1.4, 'start', '#333'))
    # nombres de componentes
    pos_txt = {'U1': (19, 19.9, 'U1 ESP32 DevKit (USB-C arriba)'), 'U4': (8.4, 11.75, 'U4 DRV8833'),
               'U2': (5, 3, 'U2 MP1584 #1\n→ 5.0 V'), 'U3': (5, 27, 'U3 MP1584 #2\n→ 6.0 V'),
               'D2': (14, -0.95, 'D2 1N5822 (franja →)'), 'C1': (1, 8.0, 'C1'), 'C2': (3.2, 12.4, 'C2'),
               'C4': (9, 22.5, 'C4'), 'C5': (11.3, 20.5, 'C5'), 'C6': (27.0, 18.6, 'C6'),
               'R1': (2, 32.1, 'R1 100k'), 'R2': (12.4, 31.2, 'R2'), 'R4': (29.5, 9.1, ''), 'R5': (17.2, 22.6, 'R5 1k'),
               'Q1': (32.6, 4.4, 'Q1'), 'Q2': (19.6, 27.3, 'Q2'), 'SW2': (14, 28.3, 'SW2 START'),
               'SW3': (24, 28.3, 'SW3 CAL'), 'J2': (3.1, 7.3, 'J2 BAT−'),
               'U4b': (8, 11.2, ''),
               'J5': (31.2, 1.6, 'J5 sensores'), 'J6': (30.6, 12.5, 'J6\nanalógicas\nA1…A8'),
               'J7': (21, 21.9, 'J7 zumb.'), 'JP1': (3.8, 10.9, 'JP1')}
    for ref, (x, y, t) in pos_txt.items():
        X, Y = mm(x, y)
        for k, linea in enumerate(t.split('\n')):
            s.append(texto(X, Y + k * 2.6, linea, 2.1, 'middle', '#000', 'bold'))
    for (y, t) in ((7, 'J1 BAT+'), (14.5, 'DER'), (16.5, 'IZQ')):
        X, Y = mm(-1.05, y)
        s.append(texto(X, Y, t, 1.5, 'middle', '#000', 'bold', rot=-90))
    s.append(texto(OX + ANCHO / 2, OY - 2.2, 'ARRIBA = lado del USB-C del ESP32', 2.4, col='#555'))
    return s


def vista_cobre(espejo=True, con_texto=True):
    s = [contorno('#ffffff')]
    s += pistas_svg(espejo, True)
    s += pads_svg(espejo, True)
    if con_texto:
        for ref, (x, y) in {'U1': (19, 11), 'U4': (8, 12), 'U2': (5, 3), 'U3': (5, 27), 'J6': (30, 12.5),
                            'J5': (30.4, 1.5), 'D2': (14, 1.6), 'SW2': (14, 28.2), 'SW3': (24, 28.2)}.items():
            X, Y = mm(x, y, espejo)
            s.append(texto(X, Y, ref, 2.2, col='#777'))
        s.append(texto(OX + ANCHO / 2, OY - 2.2, 'VISTO DESDE EL COBRE (espejo). Arriba = lado del USB-C', 2.4, col='#555'))
    return s


def vista_taladro():
    s = [contorno('#ffffff')]
    for (x, y), (ref, pin, red) in pad_en.items():
        X, Y = mm(x, y, True)
        big = ref in ('D2',)
        s.append(f'<circle cx="{X:.2f}" cy="{Y:.2f}" r="{1.0 if big else 0.6}" fill="none" stroke="#000" stroke-width="0.25"/>')
        s.append(f'<line x1="{X - 0.9:.2f}" y1="{Y:.2f}" x2="{X + 0.9:.2f}" y2="{Y:.2f}" stroke="#000" stroke-width="0.15"/>')
        s.append(f'<line x1="{X:.2f}" y1="{Y - 0.9:.2f}" x2="{X:.2f}" y2="{Y + 0.9:.2f}" stroke="#000" stroke-width="0.15"/>')
    return s


def guardar(nombre, svg):
    import cairosvg
    os.makedirs(SALIDA, exist_ok=True)
    with open(os.path.join(SALIDA, nombre + '.svg'), 'w', encoding='utf-8') as f:
        f.write(svg)
    cairosvg.svg2pdf(bytestring=svg.encode(), write_to=os.path.join(SALIDA, nombre + '.pdf'))
    cairosvg.svg2png(bytestring=svg.encode(), write_to=os.path.join(SALIDA, nombre + '.png'), output_width=1700)


def tabla_redes():
    filas = defaultdict(list)
    for c in COMP.values():
        for (pin, x, y, red) in c['pads']:
            if red:
                filas[red].append(f'{c["ref"]}.{pin.strip()}')
    return dict(sorted(filas.items()))


def main():
    print(f'Placa {ANCHO:.1f} × {ALTO:.1f} mm, {len(pad_en)} agujeros, {len(PIST)} pistas, {len(PUENTES)} puentes')
    for a in avisos:
        print('AVISO:', a)
    if errores:
        for e in errores:
            print('ERROR:', e)
        sys.exit(1)
    print('Comprobación OK: todas las redes unidas, sin cruces ni pistas sobre pads ajenos.')
    n_agujeros = len(pad_en)
    gruesos = sum(1 for v in pad_en.values() if v[0] == 'D2')
    notas_c = [
        'Hoja 1/3 · VISTA DESDE EL LADO DE COMPONENTES. Cobre en color tenue = pistas por debajo (rayos X).',
        'Rectángulos punteados = módulos en header hembra (ESP32 y DRV8833): quedan elevados ~8.5 mm.',
        'D1 (1N5822 de polaridad), el fusible y el interruptor SW-104S van en el CABLE de la batería, no en la placa.',
        'J3 (DER) = motor derecho en OUT3/OUT4 · J4 (IZQ) = motor izquierdo en OUT1/OUT2 · J1/J2 = cables de la batería.',
        'JP1 queda ABIERTO hasta medir ULT del DRV8833 (manual, etapa 5). Hojas 2 y 3: imprimir al 100 % (sin "ajustar").',
    ]
    notas_k = [
        'Hoja 2/3 · LADO COBRE visto de frente (ya está en espejo): cópienlo así sobre el cobre con plumón',
        'permanente (pistas de 1 mm y 1.5 mm, pads de 2 mm). Luego cloruro férrico. Texto gris = no se dibuja.',
        f'Agujeros: {n_agujeros} en total; {n_agujeros - gruesos} con broca de 0.8 mm y {gruesos} del diodo D2 a 1.3–1.5 mm.',
        'Los pines de header (0.64 mm cuadrados) entran justos en 0.8 mm: agranden girando la broca a mano si no entran.',
    ]
    notas_t = [
        'Hoja 3/3 · PARA TRANSFERENCIA DE TÓNER (impresora láser, papel couché): planchar con la tinta contra el cobre.',
        'Ya viene invertida para que al transferir quede igual que la hoja 2. Si dibujan a mano, NO usen esta hoja.',
        'Plantilla de taladrado: las cruces de la hoja 2 marcan el centro de cada agujero (pegar la hoja con cinta y',
        'marcar con un punzón o clavo antes de taladrar).',
    ]
    guardar('placa_1_componentes', hoja('Robot casero · placa principal (lado componentes)',
                                         f'Placa fenólica de una cara · {ANCHO:.0f} × {ALTO:.0f} mm · rejilla 2.54 mm',
                                         vista_componentes(), notas_c, escala=2.0))
    guardar('placa_2_cobre', hoja('Robot casero · placa principal (lado COBRE, espejo)',
                                   'Dibujar tal cual sobre el cobre · cruces = centro de agujero',
                                   vista_cobre(True) + vista_taladro()[1:], notas_k))
    guardar('placa_3_toner', hoja('Robot casero · placa principal (para transferencia de tóner)',
                                   'NO dibujar a mano desde esta hoja', vista_cobre(False, False), notas_t))
    from pypdf import PdfWriter
    w = PdfWriter()
    for n in ('placa_1_componentes', 'placa_2_cobre', 'placa_3_toner'):
        w.append(os.path.join(SALIDA, n + '.pdf'))
    w.write(os.path.join(SALIDA, 'PLANTILLA_PLACA_1a1.pdf'))
    for n in ('placa_1_componentes', 'placa_2_cobre', 'placa_3_toner'):
        os.remove(os.path.join(SALIDA, n + '.pdf'))
    with open(os.path.join(SALIDA, 'redes.json'), 'w', encoding='utf-8') as f:
        json.dump(dict(placa_mm=[round(ANCHO, 1), round(ALTO, 1)], agujeros=n_agujeros, redes=tabla_redes(),
                       avisos=avisos), f, ensure_ascii=False, indent=1)
    print('Salida en', SALIDA)


if __name__ == '__main__':
    main()
