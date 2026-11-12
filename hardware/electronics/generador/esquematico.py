#!/usr/bin/env python3
"""Genera el esquemático KiCad 9 (jerárquico) desde diseno.py.

Cada pin conectado recibe un tramo de cable y una etiqueta con el nombre de su red (etiqueta global si la red
cruza hojas, local si no) o un símbolo de alimentación (+3V3, +3.3VA, GND). Los pines sin uso llevan bandera de
no conexión. Salida: hardware/electronics/kicad/*.kicad_sch y la biblioteca propia circuitforge.kicad_sym."""
from __future__ import annotations

import math
import os
import sys
import uuid

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import diseno as D  # noqa: E402
import sexpr  # noqa: E402
from sexpr import Sym  # noqa: E402

PROY = "speed_follower"
DIR = os.path.join(D.RAIZ, "hardware", "electronics", "kicad")
NS = uuid.UUID("6f1c2b1e-7d1f-4b9a-9b54-2f6c0e0a5a11")
POWER = {"+3V3": "power:+3V3", "+3V3A": "power:+3.3VA", "GND": "power:GND"}
HOJAS = [("alimentacion", "Alimentación y protecciones"), ("mcu", "MCU, programación e interfaz"),
         ("motores", "Puente H y encoders"), ("sensores", "Barra de 16 sensores"), ("mecanica", "Agujeros y puntos de prueba")]
PAPEL = {"alimentacion": "A3", "mcu": "A3", "motores": "A3", "sensores": "A2", "mecanica": "A4"}
TAM = {"A4": (297, 210), "A3": (420, 297), "A2": (594, 420)}


def uid(*partes):
    return str(uuid.uuid5(NS, "/".join(str(p) for p in partes)))


def q(v):
    """Redondeo a la rejilla de 1.27 mm."""
    return round(round(v / 1.27) * 1.27, 4)


# ------------------------------------------------------------------------------------- bibliotecas de símbolos
_LIBS = {}


def lib(nombre):
    if nombre not in _LIBS:
        ruta = (os.path.join(DIR, f"{D.LIB_PROPIA}.kicad_sym") if nombre == D.LIB_PROPIA
                else os.path.join(D.KICAD, "symbols", f"{nombre}.kicad_sym"))
        _LIBS[nombre] = sexpr.parse(open(ruta, encoding="utf-8").read())
    return _LIBS[nombre]


def simbolo_plano(lib_id):
    """Símbolo de biblioteca aplanado (resuelve 'extends') con el nombre completo lib:nombre."""
    ln, nm = lib_id.split(":")
    L = lib(ln)
    tabla = {s[1]: s for s in sexpr.hijos(L, "symbol")}
    s = tabla[nm]
    ext = sexpr.hijo(s, "extends")
    if ext:
        base = simbolo_plano(f"{ln}:{ext[1]}")
        props_hijo = {p[1]: p for p in sexpr.hijos(s, "property")}
        nuevo = [Sym("symbol"), lib_id]
        for h in base[2:]:
            if isinstance(h, list) and h[0] == "property" and h[1] in props_hijo:
                nuevo.append(props_hijo.pop(h[1]))
            elif isinstance(h, list) and h[0] == "symbol":
                sub = list(h)
                sub[1] = h[1].replace(base[1].split(":")[1], nm)
                nuevo.append(sub)
            else:
                nuevo.append(h)
        for p in props_hijo.values():
            nuevo.insert(2, p)
        return nuevo
    out = [Sym("symbol"), lib_id] + [h for h in s[2:]]
    return out


def pines_simbolo(sym):
    pins = []
    for u in sexpr.hijos(sym, "symbol"):
        for p in sexpr.hijos(u, "pin"):
            at = sexpr.hijo(p, "at")
            pins.append(dict(num=sexpr.hijo(p, "number")[1], nombre=sexpr.hijo(p, "name")[1], tipo=str(p[1]),
                             x=float(at[1]), y=float(at[2]), ang=float(at[3]) if len(at) > 3 else 0.0,
                             largo=float(sexpr.hijo(p, "length")[1])))
    return pins


def caja_simbolo(sym):
    xs, ys = [], []
    for pin in pines_simbolo(sym):
        xs.append(pin["x"]); ys.append(pin["y"])
    for u in sexpr.hijos(sym, "symbol"):
        for r in sexpr.hijos(u, "rectangle"):
            for k in ("start", "end"):
                c = sexpr.hijo(r, k); xs.append(float(c[1])); ys.append(float(c[2]))
    if not xs:
        return -2.54, -2.54, 2.54, 2.54
    return min(xs), min(ys), max(xs), max(ys)


def rot(x, y, ang):
    a = math.radians(ang)
    return x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)


# ------------------------------------------------------------------------------------- piezas de S-expresión
def efectos(oculto=False, justif=None, tam=1.27):
    e = [Sym("effects"), [Sym("font"), [Sym("size"), tam, tam]]]
    if justif:
        e.append([Sym("justify")] + [Sym(j) for j in justif.split()])
    if oculto:
        e.append([Sym("hide"), Sym("yes")])
    return e


def propiedad(nombre, valor, x, y, ang=0, oculto=False, justif=None):
    return [Sym("property"), nombre, valor, [Sym("at"), x, y, ang], efectos(oculto, justif)]


def cable(x1, y1, x2, y2, clave):
    return [Sym("wire"), [Sym("pts"), [Sym("xy"), x1, y1], [Sym("xy"), x2, y2]],
            [Sym("stroke"), [Sym("width"), 0], [Sym("type"), Sym("default")]], [Sym("uuid"), uid("w", clave)]]


def etiqueta(red, x, y, ang, glob, clave):
    just = "right" if ang in (180, 270) else "left"
    if glob:
        return [Sym("global_label"), red, [Sym("shape"), Sym("passive")], [Sym("at"), x, y, ang],
                [Sym("fields_autoplaced"), Sym("yes")], efectos(justif=just), [Sym("uuid"), uid("gl", clave)],
                [Sym("property"), "Intersheetrefs", "${INTERSHEET_REFS}", [Sym("at"), x, y, 0], efectos(oculto=True)]]
    return [Sym("label"), red, [Sym("at"), x, y, ang], [Sym("fields_autoplaced"), Sym("yes")],
            efectos(justif=just + " bottom"), [Sym("uuid"), uid("l", clave)]]


def sin_conexion(x, y, clave):
    return [Sym("no_connect"), [Sym("at"), x, y], [Sym("uuid"), uid("nc", clave)]]


def texto(t, x, y, tam=2.54, clave=""):
    return [Sym("text"), t, [Sym("exclude_from_sim"), Sym("no")], [Sym("at"), x, y, 0],
            efectos(tam=tam, justif="left"), [Sym("uuid"), uid("t", clave, t)]]


class Hoja:
    def __init__(self, nombre, titulo, raiz_uuid, hoja_uuid, pagina):
        self.nombre, self.titulo = nombre, titulo
        self.raiz, self.uuid, self.pagina = raiz_uuid, hoja_uuid, pagina
        self.elems, self.libs = [], {}
        self.n_pwr = 0
        self.ruta = f"/{raiz_uuid}/{hoja_uuid}"

    def instancia(self, ref, unidad=1):
        return [Sym("instances"), [Sym("project"), PROY, [Sym("path"), self.ruta, [Sym("reference"), ref], [Sym("unit"), unidad]]]]

    def poner(self, lib_id, ref, valor, x, y, ang=0, props=None, en_bom=True, en_placa=True, clave=None):
        sym = self.libs.setdefault(lib_id, simbolo_plano(lib_id))
        clave = clave or ref
        fa = ang % 180          # el ángulo de los campos es relativo al símbolo: así quedan horizontales
        dy_txt = 2.54 if ang % 180 else 3.81
        ps = [propiedad("Reference", ref, x, y - dy_txt, fa, ref.startswith("#")),
              propiedad("Value", valor, x, y + dy_txt, fa, ref.startswith("#"))]
        for k, v in (props or {}).items():
            ps.append(propiedad(k, v, x, y, fa, True))
        nodo = [Sym("symbol"), [Sym("lib_id"), lib_id], [Sym("at"), x, y, ang], [Sym("unit"), 1],
                [Sym("exclude_from_sim"), Sym("no")], [Sym("in_bom"), Sym("yes" if en_bom else "no")],
                [Sym("on_board"), Sym("yes" if en_placa else "no")], [Sym("dnp"), Sym("no")],
                [Sym("uuid"), uid("s", self.nombre, clave)]] + ps
        for pin in pines_simbolo(sym):
            nodo.append([Sym("pin"), pin["num"], [Sym("uuid"), uid("p", self.nombre, clave, pin["num"])]])
        nodo.append(self.instancia(ref))
        self.elems.append(nodo)
        return sym

    def potencia(self, red, x, y, ang):
        self.n_pwr += 1
        ref = f"#PWR_{self.nombre[:3].upper()}{self.n_pwr:03d}"
        self.poner(POWER[red], ref, red, x, y, ang, en_bom=False, en_placa=False, clave=ref)

    def bandera(self, x, y, ang, clave):
        self.n_pwr += 1
        ref = f"#FLG_{self.nombre[:3].upper()}{self.n_pwr:03d}"
        self.poner("power:PWR_FLAG", ref, "PWR_FLAG", x, y, ang, en_bom=False, en_placa=False, clave=ref)

    def archivo(self, raiz=False, hojas=None):
        papel = PAPEL.get(self.nombre, "A3")
        cab = [Sym("kicad_sch"), [Sym("version"), 20250114], [Sym("generator"), "eeschema"], [Sym("generator_version"), "9.0"],
               [Sym("uuid"), self.uuid if not raiz else self.raiz], [Sym("paper"), papel],
               [Sym("title_block"), [Sym("title"), f"Speed Follower — {self.titulo}"], [Sym("date"), "2026-11-01"],
                [Sym("rev"), "1.0"], [Sym("company"), "Circuit Forge — Robolympics RMX2026"],
                [Sym("comment"), 1, "Generado por hardware/electronics/generador/esquematico.py desde diseno.py"]],
               [Sym("lib_symbols")] + list(self.libs.values())]
        cab += self.elems
        if raiz:
            cab += hojas
            cab.append([Sym("sheet_instances"), [Sym("path"), "/", [Sym("page"), "1"]]])
        cab.append([Sym("embedded_fonts"), Sym("no")])
        return sexpr.dump(cab) + "\n"


# ------------------------------------------------------------------------------------- colocación por hoja
def redes_globales():
    hojas_de = {}
    for p in D.PARTES:
        for pin, red in p.pines.items():
            if pin not in p.nc:
                hojas_de.setdefault(red, set()).add(p.hoja)
    return {r for r, h in hojas_de.items() if len(h) > 1}


BANDERAS = {"VBAT_IN": "alimentacion", "VBAT_SW": "alimentacion", "+3V3": "alimentacion", "GND": "alimentacion",
            "+3V3A": "mcu", "DRV_VINT": "motores"}


def dibujar_parte(h, p, X, Y, glob, ya_bandera):
    """Coloca la parte p con su origen en (X, Y) y le pone tramos, etiquetas y no-conexiones."""
    ang = 90 if p.lib_id in ("Device:R", "Device:C", "Device:L", "Device:Polyfuse", "Device:FerriteBead_Small",
                             "Device:LED", "Diode:SMAJ9.0A") else 0
    props = {"Footprint": p.huella, "Datasheet": p.datasheet, "Description": p.descripcion,
             "Fabricante": p.fabricante, "MPN": p.mpn}
    sym = h.poner(p.lib_id, p.ref, p.valor, X, Y, ang, props, en_bom=p.en_bom)
    for pin in pines_simbolo(sym):
        num = pin["num"]
        if num not in p.pines and num not in p.nc:
            raise ValueError(f"{p.ref} pin {num} ({pin['nombre']}) sin asignar")
        px, py = rot(pin["x"], pin["y"], ang)
        sx, sy = X + px, Y - py                                   # extremo del pin en la hoja (y hacia abajo)
        d = (pin["ang"] + ang + 180) % 360                       # dirección hacia afuera del símbolo
        dx, dy = round(math.cos(math.radians(d))), -round(math.sin(math.radians(d)))
        clave = f"{p.ref}.{num}"
        if num in p.nc:
            h.elems.append(sin_conexion(round(sx, 4), round(sy, 4), clave))
            continue
        red = p.pines[num]
        L = 2.54
        ex, ey = round(sx + dx * L, 4), round(sy + dy * L, 4)
        h.elems.append(cable(round(sx, 4), round(sy, 4), ex, ey, clave))
        if red in POWER:
            a_pwr = {(0, -1): 0, (0, 1): 180, (-1, 0): 90, (1, 0): 270}[(dx, dy)] if red != "GND" else \
                {(0, -1): 180, (0, 1): 0, (-1, 0): 270, (1, 0): 90}[(dx, dy)]
            h.potencia(red, ex, ey, a_pwr)
        else:
            a_lab = {(1, 0): 0, (-1, 0): 180, (0, -1): 90, (0, 1): 270}[(dx, dy)]
            h.elems.append(etiqueta(red, ex, ey, a_lab, red in glob, clave))
        if red in BANDERAS and BANDERAS[red] == h.nombre and red not in ya_bandera:
            ya_bandera.add(red)
            # bandera PWR_FLAG en el mismo nodo (tramo extra hacia afuera)
            fx, fy = round(ex + dx * 2.54, 4), round(ey + dy * 2.54, 4)
            h.elems.append(cable(ex, ey, fx, fy, clave + "f"))
            h.bandera(fx, fy, {(0, -1): 0, (0, 1): 180, (-1, 0): 90, (1, 0): 270}[(dx, dy)], clave)


def disponer(h, partes, glob, ya_bandera, x0=25.4, y0=38.1, ancho_hoja=400.0):
    """Estantes: cada parte ocupa su caja más un margen para las etiquetas."""
    x, y, alto_fila = x0, y0, 0.0
    for p in partes:
        sym = simbolo_plano(p.lib_id)
        ang = 90 if p.lib_id in ("Device:R", "Device:C", "Device:L", "Device:Polyfuse", "Device:FerriteBead_Small",
                                 "Device:LED", "Diode:SMAJ9.0A") else 0
        x0b, y0b, x1b, y1b = caja_simbolo(sym)
        if ang == 90:
            x0b, y0b, x1b, y1b = -y1b, x0b, -y0b, x1b
        mx = 24.0 if max(len(r) for r in list(p.pines.values()) + [""]) > 0 else 6
        w = (x1b - x0b) + 2 * mx
        hgt = (y1b - y0b) + 16.0
        if x + w > ancho_hoja:
            x = x0; y += alto_fila; alto_fila = 0.0
        X = q(x + mx - x0b); Y = q(y + 8.0 + y1b)
        dibujar_parte(h, p, X, Y, glob, ya_bandera)
        x += w; alto_fila = max(alto_fila, hgt)
    return y + alto_fila


def generar():
    os.makedirs(DIR, exist_ok=True)
    escribir_lib_propia()
    raiz_uuid = uid("raiz")
    glob = redes_globales()
    ya_bandera = set()
    hojas_sexpr = []
    for i, (nombre, titulo) in enumerate(HOJAS):
        hu = uid("hoja", nombre)
        h = Hoja(nombre, titulo, raiz_uuid, hu, str(i + 2))
        partes = [p for p in D.PARTES if p.hoja == nombre]
        ancho = TAM[PAPEL[nombre]][0] - 20
        h.elems.append(texto(titulo, 25.4, 25.4, 3.0, nombre))
        disponer(h, partes, glob, ya_bandera, ancho_hoja=ancho)
        with open(os.path.join(DIR, f"{nombre}.kicad_sch"), "w", encoding="utf-8") as f:
            f.write(h.archivo())
        x, y = 25.4 + 60 * (i % 4), 50.8 + 40 * (i // 4)
        hojas_sexpr.append([Sym("sheet"), [Sym("at"), x, y], [Sym("size"), 50.8, 25.4],
                            [Sym("exclude_from_sim"), Sym("no")], [Sym("in_bom"), Sym("yes")], [Sym("on_board"), Sym("yes")],
                            [Sym("dnp"), Sym("no")], [Sym("fields_autoplaced"), Sym("yes")],
                            [Sym("stroke"), [Sym("width"), 0.1524], [Sym("type"), Sym("solid")]],
                            [Sym("fill"), [Sym("color"), 0, 0, 0, 0.0]], [Sym("uuid"), hu],
                            [Sym("property"), "Sheetname", titulo, [Sym("at"), x, y - 0.7, 0], efectos(justif="left bottom")],
                            [Sym("property"), "Sheetfile", f"{nombre}.kicad_sch", [Sym("at"), x, y + 26.0, 0],
                             efectos(justif="left top")],
                            [Sym("instances"), [Sym("project"), PROY, [Sym("path"), f"/{raiz_uuid}", [Sym("page"), str(i + 2)]]]]])
    raiz = Hoja("raiz", "Hoja principal", raiz_uuid, raiz_uuid, "1")
    raiz.elems.append(texto("Speed Follower Circuit Forge — PCB-chasis. Diseño fuente: hardware/electronics/generador/diseno.py",
                            25.4, 25.4, 2.54, "raiz"))
    with open(os.path.join(DIR, f"{PROY}.kicad_sch"), "w", encoding="utf-8") as f:
        f.write(raiz.archivo(raiz=True, hojas=hojas_sexpr))
    escribir_proyecto()
    print(f"esquemático: {len(D.PARTES)} partes en {len(HOJAS)} hojas -> {os.path.relpath(DIR, D.RAIZ)}")


def escribir_lib_propia():
    """Símbolo QRE1113GR (onsemi): 1 ánodo, 2 cátodo, 3 colector, 4 emisor (hoja de datos QRE1113/D)."""
    def pin(tipo, num, nombre, x, y, ang):
        return [Sym("pin"), Sym(tipo), Sym("line"), [Sym("at"), x, y, ang], [Sym("length"), 2.54],
                [Sym("name"), nombre, efectos()], [Sym("number"), num, efectos()]]
    s = [Sym("symbol"), "QRE1113GR", [Sym("exclude_from_sim"), Sym("no")], [Sym("in_bom"), Sym("yes")], [Sym("on_board"), Sym("yes")],
         propiedad("Reference", "U", 0, 6.35), propiedad("Value", "QRE1113GR", 0, -6.35),
         propiedad("Footprint", "OptoDevice:OnSemi_CASE100CY", 0, -8.89, 0, True),
         propiedad("Datasheet", D.DS["QRE1113"], 0, -11.43, 0, True),
         propiedad("Description", "Sensor reflectivo IR onsemi QRE1113GR (LED + fototransistor), CASE 100CY", 0, 0, 0, True),
         [Sym("symbol"), "QRE1113GR_0_1",
          [Sym("rectangle"), [Sym("start"), -5.08, 3.81], [Sym("end"), 5.08, -3.81],
           [Sym("stroke"), [Sym("width"), 0.254], [Sym("type"), Sym("default")]], [Sym("fill"), [Sym("type"), Sym("background")]]],
          [Sym("polyline"), [Sym("pts"), [Sym("xy"), -2.54, 1.27], [Sym("xy"), -1.27, -1.27], [Sym("xy"), -3.81, -1.27], [Sym("xy"), -2.54, 1.27]],
           [Sym("stroke"), [Sym("width"), 0.254], [Sym("type"), Sym("default")]], [Sym("fill"), [Sym("type"), Sym("none")]]],
          [Sym("polyline"), [Sym("pts"), [Sym("xy"), 2.54, 1.27], [Sym("xy"), 2.54, -1.27]],
           [Sym("stroke"), [Sym("width"), 0.254], [Sym("type"), Sym("default")]], [Sym("fill"), [Sym("type"), Sym("none")]]]],
         [Sym("symbol"), "QRE1113GR_1_1",
          pin("passive", "1", "A", -7.62, 2.54, 0), pin("passive", "2", "K", -7.62, -2.54, 0),
          pin("passive", "3", "C", 7.62, 2.54, 180), pin("passive", "4", "E", 7.62, -2.54, 180)],
         [Sym("embedded_fonts"), Sym("no")]]
    libro = [Sym("kicad_symbol_lib"), [Sym("version"), 20241209], [Sym("generator"), "circuitforge"], [Sym("generator_version"), "9.0"], s]
    with open(os.path.join(DIR, f"{D.LIB_PROPIA}.kicad_sym"), "w", encoding="utf-8") as f:
        f.write(sexpr.dump(libro) + "\n")
    _LIBS.pop(D.LIB_PROPIA, None)


def escribir_proyecto():
    import json
    pro = {"meta": {"filename": f"{PROY}.kicad_pro", "version": 3}, "board": {}, "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
           "sheets": [[uid("raiz"), "Root"]] + [[uid("hoja", n), t] for n, t in HOJAS],
           "text_variables": {}, "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []}}
    ruta = os.path.join(DIR, f"{PROY}.kicad_pro")
    if os.path.exists(ruta):
        try:
            viejo = json.load(open(ruta))
            viejo.update({k: v for k, v in pro.items() if k in ("meta", "sheets")})
            pro = viejo
        except Exception:
            pass
    json.dump(pro, open(ruta, "w"), indent=2)
    with open(os.path.join(DIR, "sym-lib-table"), "w") as f:
        f.write(f'(sym_lib_table\n  (version 7)\n  (lib (name "{D.LIB_PROPIA}")(type "KiCad")(uri "${{KIPRJMOD}}/{D.LIB_PROPIA}.kicad_sym")(options "")(descr "Símbolos propios Circuit Forge"))\n)\n')
    with open(os.path.join(DIR, "fp-lib-table"), "w") as f:
        f.write(f'(fp_lib_table\n  (version 7)\n  (lib (name "{D.LIB_PROPIA}")(type "KiCad")(uri "${{KIPRJMOD}}/{D.LIB_PROPIA}.pretty")(options "")(descr "Huellas propias Circuit Forge"))\n)\n')


if __name__ == "__main__":
    generar()
