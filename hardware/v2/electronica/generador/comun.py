"""V2 · Electrónica — piezas comunes de los generadores (barra de sensores y PCB principal).

Modelo de datos (una `Parte` por componente, con sus pines -> redes), catálogo de pasivos ya verificados en V1
(nomenclatura YAGEO RC / Murata GRM), escritor del esquemático KiCad 9 (jerárquico, una etiqueta por pin, adaptado
de hardware/electronics/generador/esquematico.py de V1), comprobación de conectividad contra la netlist que exporta
kicad-cli, y BOM/CPL para el fabricante.

Coordenadas de colocación en el marco del ROBOT (mm): x hacia adelante desde el eje de ruedas, y a la izquierda.
En KiCad: X = x, Y = Y0 - y (Y0 = 100)."""
from __future__ import annotations

import csv
import json
import math
import os
import subprocess
import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

import sexpr
from sexpr import Sym

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))
V2E = os.path.abspath(os.path.join(AQUI, ".."))
KICAD = os.environ.get("KICAD_SHARE", "/opt/resolute/usr/share/kicad")
KCLI = os.path.join(RAIZ, "hardware", "electronics", "herramientas", "kicad.sh")
LIB_PROPIA = "circuitforge_v2"
Y0 = 100.0

DS = {
    "QRE1113": "https://www.onsemi.com/pdf/datasheet/qre1113-d.pdf",
    "74HC4051": "https://assets.nexperia.com/documents/data-sheet/74HC_HCT4051.pdf",
    "AO3400A": "https://www.aosmd.com/res/datasheets/AO3400A.pdf",
    "BM0xB": "https://www.jst-mfg.com/product/pdf/eng/eSH.pdf",
    "GRM": "https://www.murata.com/en-us/products/capacitor/ceramiccapacitor",
    "RC_YAGEO": "https://www.yageo.com/upload/media/product/productsearch/datasheet/rchip/PYu-RC_Group_51_RoHS_L_12.pdf",
    "DRV8874": "https://www.ti.com/lit/ds/symlink/drv8874.pdf",
    "TPS563200": "https://www.ti.com/lit/ds/symlink/tps563200.pdf",
    "ISM330DHCX": "https://www.st.com/resource/en/datasheet/ism330dhcx.pdf",
    "LPS22DF": "https://www.st.com/resource/en/datasheet/lps22df.pdf",
    "PKLCS1212E": "https://www.murata.com/en-us/products/productdetail?partno=PKLCS1212E4001-R1",
    "DMP3013SFV": "https://www.diodes.com/part/view/DMP3013SFV",
    "MBR0540": "https://www.onsemi.com/pdf/datasheet/mbr0540t1-d.pdf",
    "0297": "https://www.littelfuse.com/products/fuses/automotive-passenger-car/blade-fuses/297",
    "SMAJ": "https://www.littelfuse.com/assetdocs/littelfuse-tvs-diode-smaj-datasheet",
    "XT30UPB": "https://www.tme.eu/Document/e5863b891432488e7531b3c4468225ac/XT30PB-M.pdf",
    "OS102011": "https://www.ckswitches.com/media/1428/os.pdf",
    "B3FS": "https://omronfs.omron.com/en_US/ecb/products/pdf/en-b3fs.pdf",
    "B3U": "https://omronfs.omron.com/en_US/ecb/products/pdf/en-b3u.pdf",
    "APT1608": "https://www.kingbrightusa.com/images/catalog/SPEC/APT1608SGC.pdf",
    "MAPI": "https://www.we-online.com/components/products/datasheet/74438357022.pdf",
    "WEACT": "https://github.com/WeActStudio/WeActStudio.STM32G474CoreBoard",
}

# Pasivos con la nomenclatura de catálogo ya usada en V1 (docs/BOM_FINAL.csv). Valores nuevos de V2 marcados [N]:
# siguen la misma nomenclatura del fabricante y se confirman al comprar.
RES = {("100k", "0402"): "RC0402FR-07100KL", ("10k", "0402"): "RC0402FR-0710KL", ("33k", "0402"): "RC0402FR-0733KL",
       ("33.2k", "0402"): "RC0402FR-0733K2L", ("1k", "0402"): "RC0402FR-071KL", ("100", "0402"): "RC0402FR-07100RL",
       ("75", "0603"): "RC0603FR-0775RL", ("1.5k", "0402"): "RC0402FR-071K5L", ("2.2k", "0402"): "RC0402FR-072K2L",
       ("0", "0402"): "RC0402JR-070RL", ("4.7k", "0402"): "RC0402FR-074K7L"}
CAP = {("100n", "0402"): ("GRM155R71C104KA88D", "16 V X7R"), ("10n", "0402"): ("GRM155R71H103KA88D", "50 V X7R"),
       ("1n", "0402"): ("GRM155R71H102KA01D", "50 V X7R"), ("1u", "0402"): ("GRM155R61A105KE15D", "10 V X5R"),
       ("2.2u", "0402"): ("GRM155R60J225ME15D", "6.3 V X5R"), ("4.7u", "0603"): ("GRM188R61A475KE15D", "10 V X5R"),
       ("10u", "0805"): ("GRM21BR61E106KA73L", "25 V X5R"), ("22u", "0805"): ("GRM21BR61E226ME44L", "25 V X5R"),
       ("22n", "0402"): ("GRM155R71H223KA12D", "50 V X7R"), ("100n50", "0402"): ("GRM155R71H104KE14D", "50 V X7R")}
NUEVOS = {"RC0402FR-071K5L", "RC0402FR-072K2L", "RC0402JR-070RL", "RC0402FR-074K7L", "GRM155R71H223KA12D",
          "GRM155R71H104KE14D"}
HUELLA_RC = {"0402": "Resistor_SMD:R_0402_1005Metric", "0603": "Resistor_SMD:R_0603_1608Metric"}
HUELLA_C = {"0402": "Capacitor_SMD:C_0402_1005Metric", "0603": "Capacitor_SMD:C_0603_1608Metric",
            "0805": "Capacitor_SMD:C_0805_2012Metric"}
ROT90 = ("Device:R", "Device:C", "Device:L", "Device:LED", "Device:Fuse", "Diode:SMAJ9.0A", "Diode:MBR0540")


@dataclass
class Parte:
    ref: str
    lib_id: str
    valor: str
    huella: str
    fabricante: str
    mpn: str
    descripcion: str
    hoja: str
    pines: dict
    x: float = 0.0
    y: float = 0.0
    rot: float = 0.0
    lado: str = "F"
    datasheet: str = ""
    en_bom: bool = True
    nc: tuple = ()
    extra: dict = field(default_factory=dict)


class Diseno:
    """Contenedor de un proyecto: partes, hojas y nombre."""

    def __init__(self, proy, titulo, hojas, papel=None, banderas=None, power=None):
        self.proy, self.titulo, self.hojas = proy, titulo, hojas
        self.papel = papel or {}
        self.banderas = banderas or {}
        self.power = power or {"+3V3": "power:+3V3", "GND": "power:GND"}
        self.partes: list[Parte] = []
        self.dir = os.path.join(V2E, "kicad", proy)
        self.simbolos_propios = []          # S-expresiones de símbolos para la biblioteca propia

    def P(self, **kw):
        p = Parte(**kw)
        if any(q.ref == p.ref for q in self.partes):
            raise ValueError("referencia repetida " + p.ref)
        self.partes.append(p)
        return p

    def R(self, ref, valor, a, b, hoja, enc="0402", **kw):
        mpn = RES[(valor, enc)]
        return self.P(ref=ref, lib_id="Device:R", valor=valor + ("Ω" if valor[-1].isdigit() else ""), huella=HUELLA_RC[enc],
                      fabricante="YAGEO", mpn=mpn, descripcion=f"Resistencia {valor}Ω {'5' if 'JR' in mpn else '1'} % {enc}",
                      hoja=hoja, pines={"1": a, "2": b}, datasheet=DS["RC_YAGEO"], **kw)

    def C(self, ref, valor, a, b, hoja, enc="0402", **kw):
        mpn, tipo = CAP[(valor, enc)]
        v = valor.replace("100n50", "100n")
        return self.P(ref=ref, lib_id="Device:C", valor=v.replace("u", "µ") + "F", huella=HUELLA_C[enc], fabricante="Murata",
                      mpn=mpn, descripcion=f"Condensador cerámico {v.replace('u', 'µ')}F {tipo} {enc}", hoja=hoja,
                      pines={"1": a, "2": b}, datasheet=DS["GRM"], **kw)

    def por_ref(self):
        return {p.ref: p for p in self.partes}

    def redes(self):
        r = {}
        for p in self.partes:
            for pin, red in p.pines.items():
                if pin not in p.nc:
                    r.setdefault(red, set()).add((p.ref, pin))
        return r

    def verificar(self):
        err = []
        for red, nodos in self.redes().items():
            if len(nodos) < 2 and not red.startswith("NC_"):
                err.append(f"red {red} con un solo nodo {sorted(nodos)}")
        return err


# =============================================================================== esquemático (KiCad 9)
NS = uuid.UUID("0b8e6a52-1d9c-4c2f-a1a4-6a0f1e2b7c33")
TAM = {"A4": (297, 210), "A3": (420, 297), "A2": (594, 420)}


def q(v):
    return round(round(v / 1.27) * 1.27, 4)


class _Libs:
    def __init__(self, D: Diseno):
        self.D, self.cache = D, {}

    def lib(self, nombre):
        if nombre not in self.cache:
            ruta = (os.path.join(self.D.dir, f"{LIB_PROPIA}.kicad_sym") if nombre == LIB_PROPIA
                    else os.path.join(KICAD, "symbols", f"{nombre}.kicad_sym"))
            self.cache[nombre] = sexpr.parse(open(ruta, encoding="utf-8").read())
        return self.cache[nombre]

    def simbolo(self, lib_id):
        ln, nm = lib_id.split(":")
        L = self.lib(ln)
        tabla = {s[1]: s for s in sexpr.hijos(L, "symbol")}
        s = tabla[nm]
        ext = sexpr.hijo(s, "extends")
        if ext:
            base = self.simbolo(f"{ln}:{ext[1]}")
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
        return [Sym("symbol"), lib_id] + [h for h in s[2:]]


def pines_simbolo(sym):
    pins = []
    for u in sexpr.hijos(sym, "symbol"):
        for p in sexpr.hijos(u, "pin"):
            at = sexpr.hijo(p, "at")
            pins.append(dict(num=sexpr.hijo(p, "number")[1], nombre=sexpr.hijo(p, "name")[1], tipo=str(p[1]),
                             x=float(at[1]), y=float(at[2]), ang=float(at[3]) if len(at) > 3 else 0.0))
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


def _rot(x, y, ang):
    a = math.radians(ang)
    return x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)


def efectos(oculto=False, justif=None, tam=1.27):
    e = [Sym("effects"), [Sym("font"), [Sym("size"), tam, tam]]]
    if justif:
        e.append([Sym("justify")] + [Sym(j) for j in justif.split()])
    if oculto:
        e.append([Sym("hide"), Sym("yes")])
    return e


def propiedad(nombre, valor, x, y, ang=0, oculto=False, justif=None):
    return [Sym("property"), nombre, valor, [Sym("at"), x, y, ang], efectos(oculto, justif)]


class _Hoja:
    def __init__(self, D, libs, nombre, titulo, raiz_uuid, hoja_uuid):
        self.D, self.libs_, self.nombre, self.titulo = D, libs, nombre, titulo
        self.raiz, self.uuid = raiz_uuid, hoja_uuid
        self.elems, self.libs, self.n_pwr = [], {}, 0
        self.ruta = f"/{raiz_uuid}/{hoja_uuid}"

    def uid(self, *p):
        return str(uuid.uuid5(NS, self.D.proy + "/" + "/".join(str(x) for x in p)))

    def poner(self, lib_id, ref, valor, x, y, ang=0, props=None, en_bom=True, en_placa=True, clave=None):
        sym = self.libs.setdefault(lib_id, self.libs_.simbolo(lib_id))
        clave = clave or ref
        fa = ang % 180
        dy = 2.54 if ang % 180 else 3.81
        ps = [propiedad("Reference", ref, x, y - dy, fa, ref.startswith("#")),
              propiedad("Value", valor, x, y + dy, fa, ref.startswith("#"))]
        for k, v in (props or {}).items():
            ps.append(propiedad(k, v, x, y, fa, True))
        nodo = [Sym("symbol"), [Sym("lib_id"), lib_id], [Sym("at"), x, y, ang], [Sym("unit"), 1],
                [Sym("exclude_from_sim"), Sym("no")], [Sym("in_bom"), Sym("yes" if en_bom else "no")],
                [Sym("on_board"), Sym("yes" if en_placa else "no")], [Sym("dnp"), Sym("no")],
                [Sym("uuid"), self.uid("s", self.nombre, clave)]] + ps
        for pin in pines_simbolo(sym):
            nodo.append([Sym("pin"), pin["num"], [Sym("uuid"), self.uid("p", self.nombre, clave, pin["num"])]])
        nodo.append([Sym("instances"), [Sym("project"), self.D.proy, [Sym("path"), self.ruta, [Sym("reference"), ref],
                                                                       [Sym("unit"), 1]]]])
        self.elems.append(nodo)
        return sym

    def cable(self, x1, y1, x2, y2, clave):
        self.elems.append([Sym("wire"), [Sym("pts"), [Sym("xy"), x1, y1], [Sym("xy"), x2, y2]],
                           [Sym("stroke"), [Sym("width"), 0], [Sym("type"), Sym("default")]], [Sym("uuid"), self.uid("w", clave)]])

    def etiqueta(self, red, x, y, ang, glob, clave):
        just = "right" if ang in (180, 270) else "left"
        if glob:
            self.elems.append([Sym("global_label"), red, [Sym("shape"), Sym("passive")], [Sym("at"), x, y, ang],
                               [Sym("fields_autoplaced"), Sym("yes")], efectos(justif=just), [Sym("uuid"), self.uid("gl", clave)],
                               [Sym("property"), "Intersheetrefs", "${INTERSHEET_REFS}", [Sym("at"), x, y, 0], efectos(oculto=True)]])
        else:
            self.elems.append([Sym("label"), red, [Sym("at"), x, y, ang], [Sym("fields_autoplaced"), Sym("yes")],
                               efectos(justif=just + " bottom"), [Sym("uuid"), self.uid("l", clave)]])

    def texto(self, t, x, y, tam=2.54):
        self.elems.append([Sym("text"), t, [Sym("exclude_from_sim"), Sym("no")], [Sym("at"), x, y, 0],
                           efectos(tam=tam, justif="left"), [Sym("uuid"), self.uid("t", self.nombre, t[:40], x, y)]])

    def archivo(self, papel, raiz=False, hojas=None):
        cab = [Sym("kicad_sch"), [Sym("version"), 20250114], [Sym("generator"), "eeschema"], [Sym("generator_version"), "9.0"],
               [Sym("uuid"), self.raiz if raiz else self.uuid], [Sym("paper"), papel],
               [Sym("title_block"), [Sym("title"), f"{self.D.titulo} — {self.titulo}"], [Sym("date"), "2026-11-04"],
                [Sym("rev"), "V2-A"], [Sym("company"), "Circuit Forge — Robolympics RMX2026"],
                [Sym("comment"), 1, "Generado por hardware/v2/electronica/generador (no editar a mano)"]],
               [Sym("lib_symbols")] + list(self.libs.values())] + self.elems
        if raiz:
            cab += hojas
            cab.append([Sym("sheet_instances"), [Sym("path"), "/", [Sym("page"), "1"]]])
        cab.append([Sym("embedded_fonts"), Sym("no")])
        return sexpr.dump(cab) + "\n"


def _redes_globales(D):
    hojas_de = {}
    for p in D.partes:
        for pin, red in p.pines.items():
            if pin not in p.nc:
                hojas_de.setdefault(red, set()).add(p.hoja)
    return {r for r, h in hojas_de.items() if len(h) > 1}


def _dibujar(h: _Hoja, p: Parte, X, Y, glob, ya_bandera):
    ang = 90 if p.lib_id in ROT90 else 0
    props = {"Footprint": p.huella, "Datasheet": p.datasheet, "Description": p.descripcion, "Fabricante": p.fabricante,
             "MPN": p.mpn}
    sym = h.poner(p.lib_id, p.ref, p.valor, X, Y, ang, props, en_bom=p.en_bom, en_placa=not p.extra.get("solo_bom"))
    for pin in pines_simbolo(sym):
        num = pin["num"]
        if num not in p.pines and num not in p.nc:
            raise ValueError(f"{p.ref} pin {num} ({pin['nombre']}) sin asignar")
        px, py = _rot(pin["x"], pin["y"], ang)
        sx, sy = round(X + px, 4), round(Y - py, 4)
        d = (pin["ang"] + ang + 180) % 360
        dx, dy = round(math.cos(math.radians(d))), -round(math.sin(math.radians(d)))
        clave = f"{p.ref}.{num}"
        if num in p.nc:
            h.elems.append([Sym("no_connect"), [Sym("at"), sx, sy], [Sym("uuid"), h.uid("nc", clave)]])
            continue
        red = p.pines[num]
        ex, ey = round(sx + dx * 2.54, 4), round(sy + dy * 2.54, 4)
        h.cable(sx, sy, ex, ey, clave)
        if red in h.D.power:
            if red == "GND":
                a = {(0, -1): 180, (0, 1): 0, (-1, 0): 270, (1, 0): 90}[(dx, dy)]
            else:
                a = {(0, -1): 0, (0, 1): 180, (-1, 0): 90, (1, 0): 270}[(dx, dy)]
            h.n_pwr += 1
            ref = f"#PWR_{h.nombre[:3].upper()}{h.n_pwr:03d}"
            h.poner(h.D.power[red], ref, red, ex, ey, a, en_bom=False, en_placa=False, clave=ref)
        else:
            h.etiqueta(red, ex, ey, {(1, 0): 0, (-1, 0): 180, (0, -1): 90, (0, 1): 270}[(dx, dy)], red in glob, clave)
        if h.D.banderas.get(red) == h.nombre and red not in ya_bandera:
            ya_bandera.add(red)
            fx, fy = round(ex + dx * 2.54, 4), round(ey + dy * 2.54, 4)
            h.cable(ex, ey, fx, fy, clave + "f")
            h.n_pwr += 1
            ref = f"#FLG_{h.nombre[:3].upper()}{h.n_pwr:03d}"
            h.poner("power:PWR_FLAG", ref, "PWR_FLAG", fx, fy, {(0, -1): 0, (0, 1): 180, (-1, 0): 90, (1, 0): 270}[(dx, dy)],
                    en_bom=False, en_placa=False, clave=ref)


def _disponer(h, partes, glob, ya_bandera, ancho, x0=25.4, y0=38.1):
    x, y, alto = x0, y0, 0.0
    for p in partes:
        sym = h.libs_.simbolo(p.lib_id)
        ang = 90 if p.lib_id in ROT90 else 0
        a0, b0, a1, b1 = caja_simbolo(sym)
        if ang == 90:
            a0, b0, a1, b1 = -b1, a0, -b0, a1
        mx = 24.0
        w = (a1 - a0) + 2 * mx
        hg = (b1 - b0) + 16.0
        if x + w > ancho:
            x = x0; y += alto; alto = 0.0
        _dibujar(h, p, q(x + mx - a0), q(y + 8.0 + b1), glob, ya_bandera)
        x += w; alto = max(alto, hg)


def escribir_esquematico(D: Diseno, notas=None):
    """notas: {hoja: [texto, ...]} se escriben al pie de cada hoja."""
    os.makedirs(D.dir, exist_ok=True)
    escribir_lib_propia(D)
    libs = _Libs(D)
    raiz_uuid = str(uuid.uuid5(NS, D.proy + "/raiz"))
    glob = _redes_globales(D)
    ya, hojas_sexpr = set(), []
    for i, (nombre, titulo) in enumerate(D.hojas):
        hu = str(uuid.uuid5(NS, D.proy + "/hoja/" + nombre))
        h = _Hoja(D, libs, nombre, titulo, raiz_uuid, hu)
        papel = D.papel.get(nombre, "A3")
        h.texto(titulo, 25.4, 25.4, 3.0)
        _disponer(h, [p for p in D.partes if p.hoja == nombre], glob, ya, TAM[papel][0] - 20)
        for k, t in enumerate((notas or {}).get(nombre, [])):
            h.texto(t, 25.4, TAM[papel][1] - 40 + 4.0 * k, 1.8)
        with open(os.path.join(D.dir, f"{nombre}.kicad_sch"), "w", encoding="utf-8") as f:
            f.write(h.archivo(papel))
        x, y = 25.4 + 60 * (i % 4), 50.8 + 40 * (i // 4)
        hojas_sexpr.append([Sym("sheet"), [Sym("at"), x, y], [Sym("size"), 50.8, 25.4],
                            [Sym("exclude_from_sim"), Sym("no")], [Sym("in_bom"), Sym("yes")], [Sym("on_board"), Sym("yes")],
                            [Sym("dnp"), Sym("no")], [Sym("fields_autoplaced"), Sym("yes")],
                            [Sym("stroke"), [Sym("width"), 0.1524], [Sym("type"), Sym("solid")]],
                            [Sym("fill"), [Sym("color"), 0, 0, 0, 0.0]], [Sym("uuid"), hu],
                            [Sym("property"), "Sheetname", titulo, [Sym("at"), x, y - 0.7, 0], efectos(justif="left bottom")],
                            [Sym("property"), "Sheetfile", f"{nombre}.kicad_sch", [Sym("at"), x, y + 26.0, 0],
                             efectos(justif="left top")],
                            [Sym("instances"), [Sym("project"), D.proy, [Sym("path"), f"/{raiz_uuid}", [Sym("page"), str(i + 2)]]]]])
    raiz = _Hoja(D, libs, "raiz", "Hoja principal", raiz_uuid, raiz_uuid)
    raiz.texto(f"{D.titulo}. Diseño fuente: hardware/v2/electronica/generador/", 25.4, 25.4, 2.54)
    for k, t in enumerate((notas or {}).get("raiz", [])):
        raiz.texto(t, 25.4, 100 + 5.0 * k, 2.0)
    with open(os.path.join(D.dir, f"{D.proy}.kicad_sch"), "w", encoding="utf-8") as f:
        f.write(raiz.archivo("A3", raiz=True, hojas=hojas_sexpr))
    pro = {"meta": {"filename": f"{D.proy}.kicad_pro", "version": 3}, "board": {},
           "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
           "sheets": [[raiz_uuid, "Root"]] + [[str(uuid.uuid5(NS, D.proy + "/hoja/" + n)), t] for n, t in D.hojas],
           "text_variables": {}, "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []}}
    json.dump(pro, open(os.path.join(D.dir, f"{D.proy}.kicad_pro"), "w"), indent=2)
    with open(os.path.join(D.dir, "sym-lib-table"), "w") as f:
        f.write(f'(sym_lib_table\n  (version 7)\n  (lib (name "{LIB_PROPIA}")(type "KiCad")(uri "${{KIPRJMOD}}/{LIB_PROPIA}.kicad_sym")(options "")(descr "Símbolos propios Circuit Forge V2"))\n)\n')
    with open(os.path.join(D.dir, "fp-lib-table"), "w") as f:
        f.write(f'(fp_lib_table\n  (version 7)\n  (lib (name "{LIB_PROPIA}")(type "KiCad")(uri "${{KIPRJMOD}}/{LIB_PROPIA}.pretty")(options "")(descr "Huellas propias Circuit Forge V2"))\n)\n')
    print(f"esquemático {D.proy}: {len(D.partes)} partes, {len(D.hojas)} hojas -> {os.path.relpath(D.dir, RAIZ)}")


# ------------------------------------------------------------------------- símbolos propios (rectángulo con pines)
def simbolo_rect(nombre, pines_izq, pines_der, ref="U", descr="", huella="", ancho=15.24, tipo_por_nombre=None):
    """Símbolo rectangular: pines_* = [(número, nombre), ...] de arriba abajo (None deja un hueco)."""
    def pin(tipo, num, nom, x, y, ang):
        return [Sym("pin"), Sym(tipo), Sym("line"), [Sym("at"), x, y, ang], [Sym("length"), 2.54],
                [Sym("name"), nom, efectos()], [Sym("number"), num, efectos()]]
    n = max(len(pines_izq), len(pines_der))
    alto = (n + 1) * 2.54
    y0 = alto / 2
    cuerpo = [Sym("symbol"), f"{nombre}_0_1",
              [Sym("rectangle"), [Sym("start"), -ancho / 2, y0], [Sym("end"), ancho / 2, -y0],
               [Sym("stroke"), [Sym("width"), 0.254], [Sym("type"), Sym("default")]], [Sym("fill"), [Sym("type"), Sym("background")]]]]
    pins = [Sym("symbol"), f"{nombre}_1_1"]
    tp = tipo_por_nombre or (lambda nom: "power_in" if nom in ("GND", "3V3", "VCC", "+3V3") else "passive")
    for lado, lista in ((0, pines_izq), (1, pines_der)):
        for i, pn in enumerate(lista):
            if pn is None:
                continue
            num, nom = pn
            y = q(y0 - 2.54 * (i + 1))
            x = -ancho / 2 - 2.54 if lado == 0 else ancho / 2 + 2.54
            pins.append(pin(tp(nom), num, nom, x, y, 0 if lado == 0 else 180))
    return [Sym("symbol"), nombre, [Sym("exclude_from_sim"), Sym("no")], [Sym("in_bom"), Sym("yes")], [Sym("on_board"), Sym("yes")],
            propiedad("Reference", ref, 0, y0 + 2.54), propiedad("Value", nombre, 0, -y0 - 2.54),
            propiedad("Footprint", huella, 0, -y0 - 5.08, 0, True), propiedad("Datasheet", "", 0, 0, 0, True),
            propiedad("Description", descr, 0, 0, 0, True), cuerpo, pins, [Sym("embedded_fonts"), Sym("no")]]


def escribir_lib_propia(D: Diseno):
    libro = [Sym("kicad_symbol_lib"), [Sym("version"), 20241209], [Sym("generator"), "circuitforge"],
             [Sym("generator_version"), "9.0"]] + D.simbolos_propios
    with open(os.path.join(D.dir, f"{LIB_PROPIA}.kicad_sym"), "w", encoding="utf-8") as f:
        f.write(sexpr.dump(libro) + "\n")


# =============================================================================== verificación con kicad-cli
def netlist(D: Diseno, vdir):
    os.makedirs(vdir, exist_ok=True)
    salida = os.path.join(vdir, "netlist_esquematico.xml")
    subprocess.run([KCLI, "sch", "export", "netlist", "--format", "kicadxml", "-o", salida, f"{D.proy}.kicad_sch"],
                   cwd=D.dir, check=True, capture_output=True)
    redes = {}
    for n in ET.parse(salida).getroot().iter("net"):
        nodos = {(x.get("ref"), x.get("pin")) for x in n.iter("node") if not x.get("ref").startswith("#")}
        if nodos:
            redes[n.get("name").split("/")[-1]] = nodos
    return redes


def verificar_conectividad(D: Diseno, vdir, pads_pcb=None):
    esperado = {r: set(v) for r, v in D.redes().items()}
    obt = {r: v for r, v in netlist(D, vdir).items() if not r.startswith("unconnected-")}
    err = []
    for red, nodos in esperado.items():
        if red not in obt:
            err.append(f"falta la red {red} en el esquemático")
        elif obt[red] != nodos:
            err.append(f"red {red}: sobran {sorted(obt[red] - nodos)} faltan {sorted(nodos - obt[red])}")
    for red in obt:
        if red not in esperado:
            err.append(f"red inesperada {red}: {sorted(obt[red])}")
    n = 0
    if pads_pcb is not None:
        por_pin = {(r, p): red for red, nodos in esperado.items() for (r, p) in nodos}
        vistos = set()
        for it in pads_pcb:
            k = (it["ref"], it["pad"])
            vistos.add(k)
            if k in por_pin:
                n += 1
                if it["red"] != por_pin[k]:
                    err.append(f"PCB {k}: red {it['red']} en lugar de {por_pin[k]}")
            elif it["red"] not in ("", None) and not it["red"].startswith("unconnected-"):
                err.append(f"PCB {k}: pad con red {it['red']} que el diseño no conecta")
        for k in sorted(set(por_pin) - vistos):
            err.append(f"PCB: falta el pad {k}")
    print(f"  {D.proy}: diseño {len(esperado)} redes / {sum(len(v) for v in esperado.values())} conexiones; "
          f"esquemático {len(obt)} redes" + (f"; PCB {n} pads comprobados" if pads_pcb is not None else ""))
    for e in err:
        print("   ERROR:", e)
    return err


def erc(D: Diseno, vdir):
    os.makedirs(vdir, exist_ok=True)
    rj = os.path.join(vdir, "erc.json")
    subprocess.run([KCLI, "sch", "erc", "--format", "json", "--severity-all", "-o", rj, f"{D.proy}.kicad_sch"],
                   cwd=D.dir, check=True, capture_output=True)
    subprocess.run([KCLI, "sch", "erc", "--format", "report", "--severity-all", "-o", os.path.join(vdir, "erc.rpt"),
                    f"{D.proy}.kicad_sch"], cwd=D.dir, check=True, capture_output=True)
    datos = json.load(open(rj))
    viol = [v for s in datos.get("sheets", []) for v in s.get("violations", [])]
    return viol


def bom(D: Diseno, ruta, lcsc=None):
    """BOM agrupada: valor + MPN. lcsc: no se usa (sin búsqueda de tiendas)."""
    grupos = {}
    for p in D.partes:
        if not p.en_bom:
            continue
        k = (p.fabricante, p.mpn, p.huella, p.valor)
        grupos.setdefault(k, []).append(p)
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "Quantity", "Manufacturer", "MPN", "Description", "Side",
                    "Datasheet", "Nota"])
        for (fab, mpn, huella, valor), ps in sorted(grupos.items(), key=lambda kv: kv[1][0].ref):
            refs = sorted((p.ref for p in ps), key=lambda r: (r.rstrip("0123456789"), int("0" + "".join(c for c in r if c.isdigit()))))
            lados = sorted({p.lado for p in ps})
            nota = "nomenclatura del fabricante, confirmar al comprar" if mpn in NUEVOS else ps[0].extra.get("nota", "")
            w.writerow([valor, " ".join(refs), huella.split(":")[-1], len(ps), fab, mpn, ps[0].descripcion,
                        "/".join({"F": "superior", "B": "inferior"}[l] for l in lados), ps[0].datasheet, nota])
