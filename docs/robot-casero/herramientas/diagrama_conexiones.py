#!/usr/bin/env python3
"""Robot casero · diagrama de conexiones (esquema con etiquetas de red).

Dos pines con la MISMA etiqueta de color van unidos (en la placa ya lo están por las pistas).
Genera docs/robot-casero/diagrama_conexiones.{svg,png,pdf}. Los nombres de red son los mismos de
placa_principal.py; al final se comprueba que cada pin del ESP32 dibujado aquí coincide con la placa.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import placa_principal as P   # noqa: E402  (reusa la tabla de redes y la comprobación de la placa)

W, H = 400.0, 290.0
SAL = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
COL = {'VBAT': '#c0392b', 'GND': '#111', '5V': '#e67e22', 'VIN_ESP': '#e67e22', 'VM': '#a04000', '3V3': '#7d3c98',
       'BAT_IN': '#c0392b', 'BAT_SW': '#c0392b', 'BAT_F': '#c0392b'}
S = []


def esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def t(x, y, s, sz=3.0, anc='start', col='#222', peso='normal'):
    S.append(f'<text x="{x:.1f}" y="{y:.1f}" font-family="DejaVu Sans, Arial" font-size="{sz}" text-anchor="{anc}" '
             f'fill="{col}" font-weight="{peso}">{esc(s)}</text>')


def caja(x, y, w, h, titulo, sub='', fondo='#eef3f8'):
    S.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="1.5" fill="{fondo}" stroke="#333" stroke-width="0.4"/>')
    t(x + w / 2, y + 5, titulo, 3.4, 'middle', '#000', 'bold')
    if sub:
        t(x + w / 2, y + 9.2, sub, 2.4, 'middle', '#444')


def linea(pts, red='', w=0.5):
    col = COL.get(red, '#1f4e9c')
    d = ' '.join(f'{a:.1f},{b:.1f}' for a, b in pts)
    S.append(f'<polyline points="{d}" fill="none" stroke="{col}" stroke-width="{w}" stroke-linejoin="round"/>')


def punto(x, y, red=''):
    S.append(f'<circle cx="{x}" cy="{y}" r="0.9" fill="{COL.get(red, "#1f4e9c")}"/>')


def etiqueta(x, y, red, lado='der'):
    """Bandera con el nombre de la red al final de un cable."""
    col = COL.get(red, '#1f4e9c')
    ancho = 2.2 + 1.85 * len(red)
    x0 = x if lado == 'der' else x - ancho
    S.append(f'<rect x="{x0:.1f}" y="{y - 2.2:.1f}" width="{ancho:.1f}" height="4.4" rx="1" fill="#fff" stroke="{col}" '
             f'stroke-width="0.45"/>')
    t(x0 + ancho / 2, y + 1.1, red, 2.6, 'middle', col, 'bold')


def pin(x, y, nombre, red, lado='der', largo=9):
    """Pin de un bloque: nombre dentro de la caja, cable corto y etiqueta de red."""
    if lado == 'der':
        t(x - 1.2, y + 1, nombre, 2.5, 'end', '#000')
        linea([(x, y), (x + largo, y)], red)
        etiqueta(x + largo, y, red, 'der')
    else:
        t(x + 1.2, y + 1, nombre, 2.5, 'start', '#000')
        linea([(x, y), (x - largo, y)], red)
        etiqueta(x - largo, y, red, 'izq')


def gnd(x, y):
    linea([(x, y), (x, y + 2.5)], 'GND')
    for i, a in enumerate((3.0, 2.0, 1.0)):
        S.append(f'<line x1="{x - a:.1f}" y1="{y + 2.5 + i * 0.9:.1f}" x2="{x + a:.1f}" y2="{y + 2.5 + i * 0.9:.1f}" '
                 f'stroke="#111" stroke-width="0.45"/>')


def resistor(x, y, valor, vertical=True, red_arriba='', red_abajo=''):
    if vertical:
        S.append(f'<rect x="{x - 1.4}" y="{y}" width="2.8" height="8" fill="#fff" stroke="#000" stroke-width="0.4"/>')
        t(x + 2.4, y + 5, valor, 2.4)
    else:
        S.append(f'<rect x="{x}" y="{y - 1.4}" width="8" height="2.8" fill="#fff" stroke="#000" stroke-width="0.4"/>')
        t(x + 4, y - 2.4, valor, 2.4, 'middle')


def diodo(x, y, nombre, abajo=False):
    # ánodo a la izquierda, cátodo (franja) a la derecha
    S.append(f'<polygon points="{x},{y - 2.2} {x},{y + 2.2} {x + 4},{y}" fill="#000"/>')
    S.append(f'<line x1="{x + 4}" y1="{y - 2.4}" x2="{x + 4}" y2="{y + 2.4}" stroke="#000" stroke-width="0.6"/>')
    t(x + 2, y + 5.6 if abajo else y - 3.6, nombre, 2.4, 'middle')


def capacitor(x, y, valor, polar=False):
    # vertical: arriba +, abajo −
    S.append(f'<line x1="{x - 2.6}" y1="{y}" x2="{x + 2.6}" y2="{y}" stroke="#000" stroke-width="0.6"/>')
    S.append(f'<line x1="{x - 2.6}" y1="{y + 1.6}" x2="{x + 2.6}" y2="{y + 1.6}" stroke="#000" stroke-width="0.6"/>')
    if polar:
        t(x - 3.4, y - 0.6, '+', 2.6, 'middle')
    t(x + 3.4, y + 1.6, valor, 2.3)


def npn(x, y, nombre):
    """2N2222: base a la izquierda (x, y), colector arriba, emisor abajo."""
    S.append(f'<circle cx="{x + 4}" cy="{y}" r="4" fill="#fff" stroke="#000" stroke-width="0.4"/>')
    S.append(f'<line x1="{x}" y1="{y}" x2="{x + 2.6}" y2="{y}" stroke="#000" stroke-width="0.5"/>')
    S.append(f'<line x1="{x + 2.6}" y1="{y - 2.4}" x2="{x + 2.6}" y2="{y + 2.4}" stroke="#000" stroke-width="0.7"/>')
    S.append(f'<line x1="{x + 2.6}" y1="{y - 1}" x2="{x + 5}" y2="{y - 3.6}" stroke="#000" stroke-width="0.5"/>')
    S.append(f'<line x1="{x + 2.6}" y1="{y + 1}" x2="{x + 5}" y2="{y + 3.6}" stroke="#000" stroke-width="0.5"/>')
    S.append(f'<polygon points="{x + 5},{y + 3.6} {x + 3.4},{y + 3.3} {x + 4.4},{y + 2.2}" fill="#000"/>')
    t(x + 9, y + 1, nombre, 2.6, 'start', '#000', 'bold')
    return (x + 5, y - 3.6), (x + 5, y + 3.6)   # colector, emisor


S.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">')
S.append(f'<rect width="{W}" height="{H}" fill="#fff"/>')
t(W / 2, 10, 'Robot casero · diagrama de conexiones (ESP32 + DRV8833 + 2 × MP1584)', 6, 'middle', '#000', 'bold')
t(W / 2, 16.5, 'Las etiquetas del mismo nombre y color van unidas. Nombres = los de la placa (placa_principal.py). '
  'D1, fusible e interruptor van en el cable de la batería.', 3.0, 'middle', '#444')

# ------------------------------------------------------------------ 1. Alimentación (arriba a la izquierda)
caja(8, 24, 150, 96, '1 · Alimentación', 'batería 2S → protección → dos reductores', '#fbf3ee')
# batería
S.append('<rect x="14" y="40" width="16" height="26" rx="1.5" fill="#fff" stroke="#000" stroke-width="0.5"/>')
t(22, 50, 'LiPo', 3, 'middle', '#000', 'bold'); t(22, 55, '2S', 3, 'middle'); t(22, 60, '7.4–8.4 V', 2.4, 'middle')
t(22, 70, 'conector JST/XT', 2.2, 'middle', '#555')
linea([(30, 44), (36, 44)], 'VBAT', 0.8)
S.append('<rect x="36" y="41.5" width="10" height="5" fill="#fff" stroke="#000" stroke-width="0.4"/>')
t(41, 45.2, 'F 2 A', 2.3, 'middle'); t(41, 39.5, 'fusible', 2.2, 'middle', '#555')
linea([(46, 44), (52, 44)], 'VBAT', 0.8)
S.append('<circle cx="53" cy="44" r="0.8" fill="#000"/><circle cx="60" cy="44" r="0.8" fill="#000"/>')
S.append('<line x1="53" y1="44" x2="59.5" y2="40.5" stroke="#000" stroke-width="0.5"/>')
t(56.5, 38.5, 'SW-104S', 2.3, 'middle'); t(56.5, 49, 'encendido', 2.2, 'middle', '#555')
linea([(60, 44), (66, 44)], 'VBAT', 0.8)
diodo(66, 44, 'D1 1N5822')
t(68, 50, 'polaridad', 2.2, 'middle', '#555')
linea([(70, 44), (82, 44)], 'VBAT', 0.8)
t(77, 48.5, 'J1', 2.4, 'middle', '#000', 'bold')
linea([(30, 62), (82, 62)], 'GND', 0.8)
t(56, 60.5, 'J2 (BAT−)', 2.4, 'middle', '#000', 'bold')
# bus VBAT y GND
linea([(82, 44), (82, 30), (150, 30)], 'VBAT', 0.8)
linea([(82, 62), (82, 112), (150, 112)], 'GND', 0.8)
etiqueta(150, 30, 'VBAT'); etiqueta(150, 112, 'GND')
# C1 C2
for cx, val, pol in ((88, 'C1 470 µF', True), (100, 'C2 100 nF', False)):
    linea([(cx, 30), (cx, 70)], 'VBAT'); capacitor(cx, 70, '', pol); linea([(cx, 71.6), (cx, 112)], 'GND')
    t(cx, 79, val.split()[0], 2.4, 'middle', '#000', 'bold'); t(cx, 82.5, ' '.join(val.split()[1:]), 2.2, 'middle')
    punto(cx, 30, 'VBAT'); punto(cx, 112, 'GND')
# MP1584 #1
for yy, nombre, sal, red in ((36, 'U2 MP1584 #1', '5.0 V', '5V'), (74, 'U3 MP1584 #2', '6.0 V', 'VM')):
    S.append(f'<rect x="110" y="{yy}" width="26" height="22" rx="1" fill="#e9e6f8" stroke="#000" stroke-width="0.4"/>')
    t(123, yy + 6, nombre, 2.4, 'middle', '#000', 'bold'); t(123, yy + 11, f'ajustar a {sal}', 2.3, 'middle', '#a00', 'bold')
    t(111, yy + 16, 'IN+', 2.2); t(111, yy + 20.5, 'IN−', 2.2); t(135, yy + 16, 'OUT+', 2.2, 'end'); t(135, yy + 20.5, 'OUT−', 2.2, 'end')
    linea([(106, yy + 15), (110, yy + 15)], 'VBAT'); linea([(106, 30), (106, yy + 15)], 'VBAT'); punto(106, 30, 'VBAT')
    linea([(108, yy + 19.5), (110, yy + 19.5)], 'GND'); linea([(108, yy + 19.5), (108, 112)], 'GND'); punto(108, 112, 'GND')
    linea([(136, yy + 15), (140, yy + 15)], red, 0.7)
    linea([(136, yy + 19.5), (138, yy + 19.5), (138, 112)], 'GND'); punto(138, 112, 'GND')
# 5 V → D2 → VIN_ESP
diodo(140, 51, 'D2 1N5822')
t(142, 57, 'aísla USB', 2.1, 'middle', '#555')
etiqueta(144.5, 51, 'VIN_ESP')
# VM con C4 C5
etiqueta(140, 89, 'VM')
for cx, val, pol in ((116, 'C4 470µF', True), (128, 'C5 100nF', False)):
    linea([(cx, 96), (cx, 99)], 'VM'); capacitor(cx, 99, '', pol); linea([(cx, 100.6), (cx, 112)], 'GND')
    t(cx, 106.5, val, 2.1, 'middle'); punto(cx, 112, 'GND')
linea([(116, 96), (140, 96), (140, 89)], 'VM'); linea([(128, 96), (128, 96)], 'VM')
t(14, 88, 'D1 en serie: si la batería se conecta', 2.4); t(14, 92, 'al revés, no pasa corriente (caída ≈0.4 V).', 2.4)
t(14, 98, 'D2: el 5 V del MP1584 entra al VIN del', 2.4); t(14, 102, 'ESP32 sin regresar a la PC cuando hay USB.', 2.4)
t(14, 108, 'Fusible: lo pide el BOM (pendiente). No', 2.4); t(14, 112, 'conecten la LiPo sin él.', 2.4, 'start', '#a00', 'bold')
linea([(56, 112), (82, 112)], 'GND', 0)

# ------------------------------------------------------------------ 2. ESP32 (centro)
EX, EY, EW, EH = 196, 24, 60, 150
caja(EX, EY, EW, EH, 'U1 · ESP32 DevKit 30 pines', 'USB-C arriba · radio apagado', '#eaf4ea')
izq = [('3V3', '3V3'), ('GND', 'GND'), ('GPIO15 (D15)', 'NFAULT_ESP'), ('GPIO2 (D2) LED', ''), ('GPIO4 (D4)', 'ZUMB'),
       ('GPIO16 (D16)', 'NSLEEP'), ('GPIO17 (D17)', ''), ('GPIO5 (D5)', ''), ('GPIO18 (D18)', 'START'),
       ('GPIO19 (D19)', 'AIN1'), ('GPIO21 (D21)', 'AIN2'), ('RX0', ''), ('TX0', ''), ('GPIO22 (D22)', 'BIN1'),
       ('GPIO23 (D23)', 'BIN2')]
der = [('VIN', 'VIN_ESP'), ('GND', 'GND'), ('GPIO13 (D13)', 'EMIS'), ('GPIO12 (D12)', ''), ('GPIO14 (D14)', 'CAL'),
       ('GPIO27 (D27)', 'A1'), ('GPIO26 (D26)', 'A2'), ('GPIO25 (D25)', 'A3'), ('GPIO33 (D33)', 'A4'),
       ('GPIO32 (D32)', 'A5'), ('GPIO35 (D35)', 'A6'), ('GPIO34 (D34)', 'A7'), ('GPIO39 (VN)', 'A8'),
       ('GPIO36 (VP)', 'VBAT_ADC'), ('EN', '')]
for i, (n, r) in enumerate(izq):
    y = EY + 16 + i * 8.9
    if r:
        pin(EX, y, n, r, 'izq', 10)
    else:
        t(EX + 1.2, y + 1, n + ('  (libre)' if 'LED' not in n else ''), 2.4, 'start', '#999')
for i, (n, r) in enumerate(der):
    y = EY + 16 + i * 8.9
    if r:
        pin(EX + EW, y, n, r, 'der', 10)
    else:
        t(EX + EW - 1.2, y + 1, n + ('  (libre)' if n != 'EN' else ' (botón del DevKit)'), 2.4, 'end', '#999')

# ------------------------------------------------------------------ 3. DRV8833 y motores (izquierda, abajo)
caja(8, 126, 150, 82, '2 · Puente H DRV8833 (módulo) y motores N20', 'J1 del módulo SIN soldar · VCC = 6 V del MP1584 #2', '#fbeeee')
DX = 62
S.append(f'<rect x="{DX}" y="146" width="34" height="56" fill="#fff" stroke="#000" stroke-width="0.4"/>')
for i, (n, r) in enumerate([('IN1', 'AIN1'), ('IN2', 'AIN2'), ('IN3', 'BIN1'), ('IN4', 'BIN2'), ('EEP', 'NSLEEP'),
                            ('VCC', 'VM'), ('GND', 'GND')]):
    pin(DX, 151 + i * 7.6, n, r, 'izq', 9)
for i, (n, r) in enumerate([('OUT1', 'MI_A'), ('OUT2', 'MI_B'), ('OUT3', 'MD_A'), ('OUT4', 'MD_B')]):
    t(DX + 32.8, 152 + i * 7.6, n, 2.5, 'end')
    linea([(DX + 34, 151 + i * 7.6), (DX + 44, 151 + i * 7.6)], 'MOT')
t(DX + 32.8, 194, 'ULT', 2.5, 'end')
linea([(DX + 34, 193), (DX + 40, 193)], 'NFAULT')
S.append(f'<rect x="{DX + 40}" y="191.4" width="5" height="3.2" fill="none" stroke="#000" stroke-width="0.35" stroke-dasharray="0.8,0.6"/>')
t(DX + 42.5, 199, 'JP1 abierto', 2.1, 'middle', '#a00')
linea([(DX + 45, 193), (DX + 49, 193)], 'NFAULT_ESP'); etiqueta(DX + 49, 193, 'NFAULT_ESP')
for i, (nom, y0) in enumerate((('Motor IZQ (J4)', 151), ('Motor DER (J3)', 166.2))):
    S.append(f'<circle cx="{DX + 52}" cy="{y0 + 3.8}" r="5.2" fill="#fff" stroke="#000" stroke-width="0.45"/>')
    t(DX + 52, y0 + 5, 'M', 3.4, 'middle', '#000', 'bold')
    linea([(DX + 44, y0), (DX + 47.5, y0 + 1.5)], 'MOT'); linea([(DX + 44, y0 + 7.6), (DX + 47.5, y0 + 6.1)], 'MOT')
    t(DX + 59, y0 + 5, nom, 2.6, 'start', '#000', 'bold')
t(DX + 52, 180, 'Control ("slow decay"):', 2.4, 'start', '#000', 'bold')
t(DX + 52, 184, 'adelante: IN1=1, IN2=PWM(1−d)', 2.3); t(DX + 52, 188, 'atrás: IN1=PWM(1−d), IN2=1', 2.3)
t(DX + 52, 202, 'freno: 1,1 · libre: 0,0 · EEP=0 duerme', 2.3)
t(14, 140, 'Pull-down internos (TI): IN1…IN4 150 kΩ, EEP 500 kΩ;', 2.2, 'start', '#555')
t(14, 143.6, 'los motores no se mueven mientras arranca el ESP32.', 2.2, 'start', '#555')

# ------------------------------------------------------------------ 4. Sensores (derecha)
SX = 290
caja(SX, 24, 104, 150, '3 · Sensores (conectores J5 y J6)', 'opción A: QTR-8A · opción B: 8 × TCRT5000', '#eef2fb')
t(SX + 4, 42, 'J5 (1×5)', 2.8, 'start', '#000', 'bold')
for i, r in enumerate(['3V3', 'VIN_ESP', 'GND', 'EMIS', 'EMIT_K']):
    etiqueta(SX + 4, 47 + i * 6, r)
t(SX + 30, 47.8, '3.3 V para pull-ups / QTR', 2.3); t(SX + 30, 53.8, '5 V para los LED IR', 2.3)
t(SX + 30, 65.8, 'GPIO13 directo (LEDON de la QTR)', 2.3); t(SX + 30, 71.8, 'colector de Q1 (cátodos de los LED)', 2.3)
t(SX + 4, 84, 'J6 (1×8): A1…A8 = GPIO 27, 26, 25, 33, 32, 35, 34, 39', 2.5, 'start', '#000', 'bold')
t(SX + 4, 88.5, 'A1 = sensor de la IZQUIERDA del robot … A8 = derecha', 2.3)
# opción A
t(SX + 4, 97, 'A · QTR-8A:', 2.8, 'start', '#000', 'bold')
t(SX + 4, 101.5, 'VCC→3V3 (¡no a 5 V!), GND, LEDON→EMIS, OUT1…8→A1…A8.', 2.3)
t(SX + 4, 105.5, 'Puentear "3.3V BYPASS" (Pololu: solo con VCC 3.3 V).', 2.3)
t(SX + 4, 109.5, 'Salida alta = negro. Q1 y J5.EMIT− no se usan.', 2.3)
# opción B: un canal
t(SX + 4, 118, 'B · cada TCRT5000 (se repite 8 veces):', 2.8, 'start', '#000', 'bold')
bx, by = SX + 8, 124
etiqueta(bx - 2, by, 'VIN_ESP', 'der')
linea([(bx + 14, by), (bx + 20, by)], 'VIN_ESP'); resistor(bx + 20, by, '330 Ω', False); linea([(bx + 28, by), (bx + 33, by)], 'VIN_ESP')
diodo(bx + 33, by, 'LED IR (A→K)', abajo=True)
linea([(bx + 37, by), (bx + 41, by)], 'EMIT_K'); etiqueta(bx + 41, by, 'EMIT_K')
etiqueta(bx - 2, by + 16, '3V3')
linea([(bx + 6, by + 16), (bx + 20, by + 16)], '3V3'); resistor(bx + 20, by + 16, '10 kΩ', False)
linea([(bx + 28, by + 16), (bx + 40, by + 16)], 'A1'); punto(bx + 36, by + 16, 'A1'); etiqueta(bx + 40, by + 16, 'Ai')
linea([(bx + 36, by + 16), (bx + 36, by + 21)], 'A1')
S.append(f'<rect x="{bx + 33}" y="{by + 21}" width="6" height="7" fill="#fff" stroke="#000" stroke-width="0.4"/>')
t(bx + 41, by + 25.5, 'fototransistor C→E', 2.3)
linea([(bx + 36, by + 28), (bx + 36, by + 31)], 'GND'); gnd(bx + 36, by + 31)
t(SX + 4, by + 42, 'C del sensor = Ai (con 10 kΩ a 3V3) · E = GND. Salida alta = negro.', 2.3)
t(SX + 4, by + 46, 'Corriente LED ≈ (5 − 1.25)/330 ≈ 11 mA (máx. 60 mA, Vishay).', 2.3)

# ------------------------------------------------------------------ 5. Q1, Q2, botones, batería al ADC (abajo)
caja(164, 180, 230, 104, '4 · Transistores 2N2222, botones, zumbador y medición de batería', '', '#f6f6f6')
# Q1
Y4 = 212
etiqueta(170, Y4, 'EMIS'); linea([(180, Y4), (184, Y4)], 'EMIS'); resistor(184, Y4, 'R4 1 kΩ', False)
linea([(192, Y4), (196, Y4)], 'Q1B')
c, e = npn(196, Y4, 'Q1')
linea([c, (c[0], Y4 - 9)], 'EMIT_K'); etiqueta(c[0] + 1, Y4 - 9, 'EMIT_K', 'der')
linea([e, (e[0], Y4 + 6)], 'GND'); gnd(e[0], Y4 + 6)
t(170, 228, 'Q1 apaga/enciende los LED IR para restar', 2.3); t(170, 232, 'la luz ambiente. Base: (3.3−0.7)/1k ≈ 2.6 mA', 2.3)
t(170, 236, '→ satura con hasta ~130 mA de LED.', 2.3)
# Q2
etiqueta(234, Y4, 'ZUMB'); linea([(244, Y4), (248, Y4)], 'ZUMB'); resistor(248, Y4, 'R5 1 kΩ', False)
linea([(256, Y4), (260, Y4)], 'Q2B')
c, e = npn(260, Y4, 'Q2')
linea([c, (c[0], Y4 - 9)], 'ZUMB_K')
S.append(f'<rect x="{c[0] - 3}" y="{Y4 - 17}" width="6" height="8" fill="#fff" stroke="#000" stroke-width="0.4"/>')
t(c[0] + 4, Y4 - 12, 'zumbador (J7)', 2.3)
linea([(c[0], Y4 - 17), (c[0], Y4 - 20)], 'VIN_ESP'); etiqueta(c[0] + 1, Y4 - 21, 'VIN_ESP', 'der')
linea([e, (e[0], Y4 + 6)], 'GND'); gnd(e[0], Y4 + 6)
t(234, 228, 'Q2 maneja el zumbador (5 V, ~30 mA) que el', 2.3); t(234, 232, 'pin del ESP32 no puede alimentar solo.', 2.3)
t(234, 236, 'Si es pasivo y de bobina: diodo en paralelo.', 2.3)
# botones
for i, (red, nom) in enumerate((('START', 'SW2 START'), ('CAL', 'SW3 CAL'))):
    x0 = 300 + i * 44
    etiqueta(x0, Y4 - 4, red)
    xf = x0 + 2.2 + 1.85 * len(red)
    linea([(xf, Y4 - 4), (x0 + 24, Y4 - 4)], red)
    S.append(f'<circle cx="{x0 + 24}" cy="{Y4 - 4}" r="0.8" fill="#000"/><circle cx="{x0 + 24}" cy="{Y4 + 3}" r="0.8" fill="#000"/>')
    S.append(f'<line x1="{x0 + 21.5}" y1="{Y4 - 3.5}" x2="{x0 + 21.5}" y2="{Y4 + 2.5}" stroke="#000" stroke-width="0.5"/>')
    S.append(f'<line x1="{x0 + 21.5}" y1="{Y4 - 0.5}" x2="{x0 + 19}" y2="{Y4 - 0.5}" stroke="#000" stroke-width="0.5"/>')
    linea([(x0 + 24, Y4 + 3), (x0 + 24, Y4 + 6)], 'GND'); gnd(x0 + 24, Y4 + 6)
    t(x0 + 14, 228, nom, 2.4, 'middle', '#000', 'bold')
t(300, 234, 'Pull-up interno del ESP32: suelto = 1, oprimido = 0.', 2.3)
t(300, 238, 'Botón de 4 patas: usar 2 patas en DIAGONAL.', 2.3)
# divisor
etiqueta(170, 246, 'VBAT'); linea([(178, 246), (184, 246)], 'VBAT'); resistor(184, 246, 'R1 100 kΩ', False)
linea([(192, 246), (206, 246)], 'VBAT_ADC'); punto(198, 246, 'VBAT_ADC'); etiqueta(206, 246, 'VBAT_ADC')
linea([(198, 246), (198, 250)], 'VBAT_ADC'); resistor(198, 250, 'R2 33 kΩ'); linea([(198, 258), (198, 262)], 'GND'); gnd(198, 262)
linea([(232, 248), (232, 251)], 'VBAT_ADC'); capacitor(232, 251, 'C6 100 nF (junto al pin)'); linea([(232, 252.6), (232, 256)], 'GND'); gnd(232, 256)
etiqueta(224, 246, 'VBAT_ADC')
t(170, 272, '8.4 V × 33/133 = 2.08 V en GPIO36 (dentro del rango de 2.45 V con atenuación de 11 dB).', 2.4)
t(170, 276.5, 'Sirve para avisar batería baja (< 6.8 V = 3.4 V por celda) y para escalar el PWM si VM sale de VBAT.', 2.4)
t(300, 246, 'LED: el azul del DevKit (GPIO2).', 2.4, 'start', '#000', 'bold')
t(300, 250.5, 'Un LED externo opcional va en J7 junto', 2.3); t(300, 254.5, 'al zumbador, con su resistencia de 330 Ω.', 2.3)
t(300, 263, 'Ventilador: reservado GPIO17 (no se arma aún).', 2.3, 'start', '#555')

t(8, 288, 'Fuentes: TI DRV8833 (SLVSAR1), MPS MP1584, Pololu QTR-8A (0J12), Vishay TCRT5000, Espressif ESP32 (ADC y pines de arranque). '
  'Pines del DevKit y del módulo DRV8833: serigrafía (M03, M10).', 2.3, 'start', '#666')
S.append('</svg>')

# --------------------------------------------------------------- comprobación contra la placa
placa = {}
for (pinn, x, y, red) in P.COMP['U1']['pads']:
    placa[pinn.strip() + ('_d' if x == P.EXD else '_i')] = red or ''
dib = {}
for n, r in izq:
    dib[n.split(' ')[0].replace('GPIO', 'D') if n.startswith('GPIO') else n] = r
mal = []
for i, (n, r) in enumerate(izq):
    clave = P.ESP_IZQ[i] + '_i'
    if (r or '') != placa[clave] and not (r == '' and placa[clave] == ''):
        mal.append((P.ESP_IZQ[i], r, placa[clave]))
for i, (n, r) in enumerate(der):
    clave = P.ESP_DER[i] + '_d'
    if (r or '') != placa[clave]:
        mal.append((P.ESP_DER[i], r, placa[clave]))
if mal:
    print('ERROR: el diagrama no coincide con la placa:', mal)
    sys.exit(1)
svg = '\n'.join(S)
with open(os.path.join(SAL, 'diagrama_conexiones.svg'), 'w', encoding='utf-8') as f:
    f.write(svg)
import cairosvg  # noqa: E402
cairosvg.svg2png(bytestring=svg.encode(), write_to=os.path.join(SAL, 'diagrama_conexiones.png'), output_width=2400)
cairosvg.svg2pdf(bytestring=svg.encode(), write_to=os.path.join(SAL, 'diagrama_conexiones.pdf'))
print('Diagrama OK (pines del ESP32 iguales a la placa) →', SAL)
