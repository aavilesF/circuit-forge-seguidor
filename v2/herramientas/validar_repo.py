#!/usr/bin/env python3
"""Validador de coherencia del repositorio (V2). Uso: python3 v2/herramientas/validar_repo.py
Sale con código 1 si hay errores. No modifica nada.
Revisa: (1) inventario vs esquemas, (2) términos obsoletos en archivos vigentes,
(3) IDs citados vs tabla de pendientes, (4) tabla de estado de documentos,
(5) huella (hash) del DRC contra el .kicad_pcb vigente."""
import csv, re, sys, hashlib, json, subprocess, pathlib
R = pathlib.Path(__file__).resolve().parents[2]
err, adv = [], []
def E(m): err.append(m)
def A(m): adv.append(m)

# 1. inventario vs esquemas
def simbolos(b):
    t = (R/f'v2/electronica/{b}/{b}.kicad_sch').read_text()
    out = []
    for m in re.finditer(r'\(symbol \(lib_id "[^"]+"\).*?\(property "Reference" "([^"]+)".*?\(property "Value" "([^"]*)"', t, re.S):
        if not m.group(1).startswith('#'): out.append((m.group(1), m.group(2)))
    return out
sims = simbolos('principal') + simbolos('sensores')
inv = list(csv.DictReader(open(R/'v2/inventario.csv', encoding='utf-8')))
for f in inv:
    c = f['comprada']; u = f['usada']
    if f['patron_valor'] or f['patron_ref']:
        n = 0
        for ref, val in sims:
            if f['patron_valor'] and re.search(f['patron_valor'], val) and not ref.startswith(('BT','M','SW1')): n += 1
            elif f['patron_ref'] and re.search(f['patron_ref'], ref): n += 1
        if f['clave'] == 'headers_cable': n = 28 if n == 7 else n  # J1-J5 (2 pines) + J6 y J1 sensores (9 pines)
        if u.isdigit() and int(u) != n: E(f"inventario: {f['clave']} dice usada={u} pero los esquemas tienen {n}")
    if c.isdigit() and u.isdigit() and int(c) < int(u) and f['recepcion'] != 'por_comprar':
        E(f"inventario: {f['clave']} usa {u} pero solo compró {c}")
    if c.isdigit() and int(c) == 0 and f['recepcion'] != 'por_comprar': E(f"inventario: {f['clave']} sin compra debe estar por_comprar")
    if f['recepcion'] not in ('confirmada', 'sin_confirmar', 'por_comprar'): E(f"inventario: estado raro en {f['clave']}")
    if '?' in (c, u): A(f"inventario: {f['clave']} tiene cantidad desconocida (?): ver su ID en pendientes")
# pines de tira hembra necesarios
def pads(p):
    # pines físicos = números de pad únicos con taladro metalizado (excluye agujeros de montaje y pads duplicados)
    return len({n for n, k in re.findall(r'\(pad "([^"]+)" (thru_hole)', (R/p).read_text())})
need = pads('v2/electronica/bibliotecas/ESP32.pretty/ESP32-DevKit-USB-C.kicad_mod') + 2*pads('v2/electronica/bibliotecas/MP1584.pretty/MP1584module.kicad_mod') + pads('v2/electronica/bibliotecas/DRV8833.pretty/DRV8833.kicad_mod') + pads('v2/electronica/bibliotecas/HC4067.pretty/ANALOG_MUX_BREAKOUT_HC4067.kicad_mod')
for f in inv:
    if f['clave'] == 'tira_hembra':
        if int(f['comprada']) < need: E(f"inventario: tira hembra necesaria {need} pines (según las huellas) y comprada {f['comprada']}")
        else: A(f"tira hembra: necesarias {need} pines, compradas {f['comprada']} (si se cortan bien; ver P-V2-41)")

# 2. términos obsoletos en archivos vigentes
VIG = ['v2/README.md', 'v2/docs/*.md', 'docs/pendientes-por-confirmar.md', 'CLAUDE.md']
tabla = [l.split(' => ') for l in (R/'v2/herramientas/terminos_obsoletos.txt').read_text().splitlines() if l.strip() and not l.startswith('#')]
for pat in VIG:
    for p in R.glob(pat):
        txt = p.read_text().splitlines()
        for i, l in enumerate(txt, 1):
            for rx, motivo in ((t[0], t[1]) for t in tabla):
                if re.search(rx, l) and not re.search(r'obsoleto|antes|anterior|hist|corregid|sustituy|ya no|decía|dice|pasó|cambi', l, re.I):
                    E(f"{p.relative_to(R)}:{i}: término obsoleto /{rx}/ ({motivo})")

# 3. IDs citados vs pendientes
pend = (R/'docs/pendientes-por-confirmar.md').read_text()
ids_pend = set(re.findall(r'^\| (P-V2-\d+|[MCERPVD]\d{2}) \|', pend, re.M)) | set(re.findall(r'\b(P-V2-\d+)\b', pend))
for p in list(R.glob('v2/docs/*.md')) + [R/'v2/README.md', R/'v2/inventario.csv']:
    for i in set(re.findall(r'\bP-V2-\d+\b', p.read_text())):
        if i not in ids_pend: E(f"{p.relative_to(R)}: cita {i} que no existe en pendientes")
filas = re.findall(r'^\| (P-V2-\d+) \|', pend, re.M)
for i in set(filas):
    if filas.count(i) > 1: E(f"pendientes: ID {i} duplicado en tablas (A y B a la vez)")
ant = R/'docs/historial'
allid = set()
for p in ant.glob('pendientes-v*.md'): allid |= set(re.findall(r'^\| ([MCERPV]\d{2}|P-V2-\d+) \|', p.read_text(), re.M))
falt = allid - set(re.findall(r'\b([MCERPV]\d{2}|P-V2-\d+)\b', pend))
for i in sorted(falt): E(f"pendientes: falta el ID {i} que existe en el historial")
# duplicados dentro de la misma sección
for sec in re.split(r'^## ', pend, flags=re.M):
    nombres = re.findall(r'^\| ([MCERPV]\d{2}|P-V2-\d+) \|', sec, re.M)
    for i in set(nombres):
        if nombres.count(i) > 1: E(f"pendientes: ID {i} repetido en la misma sección")

# 4. tabla de estado de documentos
est = (R/'v2/docs/ESTADO-DOCUMENTOS.md').read_text()
listados = set(re.findall(r'`([^`]+)`', est))
for p in list(R.glob('v2/docs/*.md')) + [R/'v2/README.md', R/'v2/inventario.csv']:
    if str(p.relative_to(R)) not in listados: E(f"ESTADO-DOCUMENTOS.md no lista {p.relative_to(R)}")

# 5. DRC vigente corresponde al PCB vigente
reg = R/'v2/electronica/verificacion/registro_drc.json'
if reg.exists():
    for k, v in json.load(open(reg)).items():
        h = hashlib.md5((R/k).read_bytes()).hexdigest()
        if h != v['md5']: E(f"DRC desactualizado: {k} cambió (md5 {h[:8]} != registro {v['md5'][:8]}); volver a correr el DRC")
else: E('falta v2/electronica/verificacion/registro_drc.json')

print('ERRORES:', len(err)); [print(' -', e) for e in err]
print('AVISOS:', len(adv)); [print(' ·', a) for a in adv]
sys.exit(1 if err else 0)
