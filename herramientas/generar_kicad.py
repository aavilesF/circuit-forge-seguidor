#!/usr/bin/env python3
"""Genera el proyecto de KiCad (esquemático de conexiones) del seguidor de línea.

Fuente de verdad de los pines: firmware/seguidor/pines.h (se lee con regex, igual que generar_diagramas.py).
Salida en docs/diagramas/kicad/: seguidor.kicad_pro, seguidor.kicad_sch, seguidor.kicad_sym, sym-lib-table
Formato: KiCad 7 (versión 20230121). Se abre en KiCad 7, 8, 9 y posteriores (los nuevos lo actualizan al guardar).

Los símbolos son FUNCIONALES (módulos como cajas con sus pines); no traen huellas (footprints) todavía.
Si cambias un pin, cámbialo solo en pines.h y vuelve a correr este script: el esquemático se regenera.
Los cambios hechos a mano en el .kicad_sch se pierden al regenerar.

Uso: python3 herramientas/generar_kicad.py
Al terminar vuelve a leer los archivos escritos y comprueba la conectividad contra la lista de conexiones
(cada pin conectado o marcado sin conexión, ninguna red cruzada) y contra pines.h.
"""
import json
import re
import sys
import uuid
from math import ceil
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "docs" / "diagramas" / "kicad"
PROYECTO = "seguidor"
NICK = "seguidor"          # nombre de la biblioteca de símbolos del proyecto
REVISION = "A"
FECHA = "2026-11-02"       # se actualiza a mano al regenerar con cambios de fondo

NS = uuid.UUID("6f1f0c5e-3b7a-4a55-9d57-5e9c1f0a7c11")   # UUID estables: regenerar no ensucia el diff
UUID_RAIZ = str(uuid.uuid5(NS, "raiz"))


# ------------------------------------------------------------------ pines (desde pines.h)
txt = (RAIZ / "firmware/seguidor/pines.h").read_text(encoding="utf-8")
PIN = {m.group(1): int(m.group(2)) for m in re.finditer(r"constexpr int\s+(PIN_\w+)\s*=\s*(\d+)", txt)}
NECESARIOS = ["PIN_MUX_S0", "PIN_MUX_S1", "PIN_MUX_S2", "PIN_MUX_S3", "PIN_MUX_SIG1", "PIN_MUX_SIG2",
              "PIN_EMISORES", "PIN_PWMA", "PIN_AIN1", "PIN_AIN2", "PIN_PWMB", "PIN_BIN1", "PIN_BIN2",
              "PIN_STBY", "PIN_START", "PIN_CAL", "PIN_LED", "PIN_PERFIL", "PIN_BATERIA"]
faltan = [k for k in NECESARIOS if k not in PIN]
if faltan:
    sys.exit(f"pines.h no define: {faltan}")
usados = [PIN[k] for k in NECESARIOS]
dup = sorted({p for p in usados if usados.count(p) > 1})
if dup:
    sys.exit(f"GPIO repetidos en pines.h: {dup}")
SOLO_ENTRADA = {34, 35, 36, 39}
ENTRADAS = {"PIN_MUX_SIG1", "PIN_MUX_SIG2", "PIN_BATERIA", "PIN_PERFIL"}
for k in NECESARIOS:
    p = PIN[k]
    if p in {6, 7, 8, 9, 10, 11}:
        sys.exit(f"{k}=GPIO{p} esta conectado a la flash")
    if p in {0, 5, 12, 15}:
        sys.exit(f"{k}=GPIO{p} es pin de arranque delicado")
    if p in SOLO_ENTRADA and k not in ENTRADAS:
        sys.exit(f"{k}=GPIO{p} es solo entrada y se usa como salida")
    if k in ENTRADAS and p not in {32, 33, 34, 35, 36, 39}:
        sys.exit(f"{k}=GPIO{p} debe ser ADC1 (GPIO 32-39)")


# ------------------------------------------------------------------ s-expresiones
class Q(str):
    """Cadena que se escribe entre comillas."""


def num(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def esc(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def atomo(a):
    if isinstance(a, Q):
        return esc(a)
    if isinstance(a, float):
        return num(a)
    return str(a)


def sx(nodo, ind=0):
    """Serializa una lista anidada a s-expresión legible (una línea si es corta)."""
    if not isinstance(nodo, list):
        return atomo(nodo)
    partes = [sx(h, ind + 1) for h in nodo]
    una = "(" + " ".join(partes) + ")"
    if "\n" not in una and len(una) <= 96:
        return una
    cabeza = []
    resto = []
    for h in nodo:
        if resto or isinstance(h, list):
            resto.append(h)
        else:
            cabeza.append(h)
    pad = "  " * (ind + 1)
    salida = "(" + " ".join(atomo(h) for h in cabeza)
    for h in resto:
        salida += "\n" + pad + sx(h, ind + 1)
    return salida + "\n" + "  " * ind + ")"


def efectos(tam=1.27, oculto=False, justif=None):
    e = ["effects", ["font", ["size", tam, tam]]]
    if justif:
        e.append(["justify", *justif])
    if oculto:
        e.append("hide")
    return e


# ------------------------------------------------------------------ símbolos
def g_rect(x1, y1, x2, y2, relleno="background"):
    return ["rectangle", ["start", x1, y1], ["end", x2, y2], ["stroke", ["width", 0.254], ["type", "default"]],
            ["fill", ["type", relleno]]]


def g_poly(pts, relleno="none"):
    return ["polyline", ["pts", *[["xy", a, b] for a, b in pts]], ["stroke", ["width", 0.254], ["type", "default"]],
            ["fill", ["type", relleno]]]


def g_circ(cx, cy, r, relleno="none"):
    return ["circle", ["center", cx, cy], ["radius", r], ["stroke", ["width", 0.254], ["type", "default"]],
            ["fill", ["type", relleno]]]


def g_text(s, x, y, tam=1.27):
    return ["text", Q(s), ["at", x, y, 0], efectos(tam)]


class Sym:
    def __init__(self, nombre, ref, valor, graficos, pines, top, ocultar_nombres=False):
        self.nombre, self.ref, self.valor = nombre, ref, valor
        self.graficos, self.pines, self.top = graficos, pines, top
        self.ocultar_nombres = ocultar_nombres
        nombres = [p["name"] for p in pines]
        assert len(set(nombres)) == len(nombres), f"{nombre}: nombres de pin repetidos"
        assert len({p["num"] for p in pines}) == len(pines), f"{nombre}: números de pin repetidos"

    def pin(self, nombre):
        for p in self.pines:
            if p["name"] == nombre:
                return p
        raise KeyError(f"{self.nombre} no tiene el pin {nombre}")

    def lib(self, con_nick):
        nm = f"{NICK}:{self.nombre}" if con_nick else self.nombre
        sub0 = ["symbol", Q(f"{self.nombre}_0_1"), *self.graficos]
        sub1 = ["symbol", Q(f"{self.nombre}_1_1")]
        for p in self.pines:
            sub1.append(["pin", "passive", "line", ["at", p["x"], p["y"], p["ang"]], ["length", p["len"]],
                         ["name", Q(p["name"]), efectos()], ["number", Q(p["num"]), efectos()]])
        nodo = ["symbol", Q(nm), ["pin_numbers", "hide"],
                ["pin_names", ["offset", 1.016]] + (["hide"] if self.ocultar_nombres else []),
                ["in_bom", "yes"], ["on_board", "yes"],
                ["property", Q("Reference"), Q(self.ref), ["at", 0.0, self.top + 1.27, 0], efectos()],
                ["property", Q("Value"), Q(self.valor), ["at", 0.0, -(self.top + 1.27), 0], efectos()],
                ["property", Q("Footprint"), Q(""), ["at", 0.0, 0.0, 0], efectos(oculto=True)],
                ["property", Q("Datasheet"), Q("~"), ["at", 0.0, 0.0, 0], efectos(oculto=True)],
                sub0, sub1]
        return nodo


def caja(nombre, ref, valor, izq, der, ancho_min=15.24, extra=()):
    """Módulo como caja. izq/der: lista de (numero, nombre) o None (fila vacía). Pines de 5.08 mm."""
    n = max(len(izq), len(der))
    alto = (n + 1) * 2.54
    maxl = max([len(e[1]) for e in izq if e] or [0])
    maxr = max([len(e[1]) for e in der if e] or [0])
    ancho = max(ancho_min, ceil(((maxl + maxr) * 1.3 + 2.54) / 2.54) * 2.54)
    pines = []
    for i, e in enumerate(izq):
        if e:
            pines.append(dict(num=e[0], name=e[1], x=-(ancho / 2 + 5.08), y=(n - 1) * 1.27 - 2.54 * i, ang=0, len=5.08))
    for i, e in enumerate(der):
        if e:
            pines.append(dict(num=e[0], name=e[1], x=ancho / 2 + 5.08, y=(n - 1) * 1.27 - 2.54 * i, ang=180, len=5.08))
    return Sym(nombre, ref, valor, [g_rect(-ancho / 2, alto / 2, ancho / 2, -alto / 2), *extra], pines, alto / 2)


def dos_pines(nombre, ref, valor, graficos, top, nom1="1", nom2="2", len1=2.54, len2=2.54):
    pines = [dict(num="1", name=nom1, x=-5.08, y=0.0, ang=0, len=len1),
             dict(num="2", name=nom2, x=5.08, y=0.0, ang=180, len=len2)]
    return Sym(nombre, ref, valor, graficos, pines, top, ocultar_nombres=True)


S_R = dos_pines("R_H", "R", "R", [g_rect(-2.54, 1.016, 2.54, -1.016, "none")], 2.54)
S_C = dos_pines("C_H", "C", "C", [g_poly([(-0.762, -2.032), (-0.762, 2.032)]), g_poly([(0.762, -2.032), (0.762, 2.032)])],
                2.54, len1=4.318, len2=4.318)
S_CP = dos_pines("CP_H", "C", "CP", [g_poly([(-0.762, -2.032), (-0.762, 2.032)]), g_poly([(0.762, -2.032), (0.762, 2.032)]),
                                     g_text("+", -2.9, 2.2)], 2.54, "+", "-", len1=4.318, len2=4.318)
S_FUSE = dos_pines("FUSE_H", "F", "Fuse", [g_rect(-2.54, 1.016, 2.54, -1.016, "none"), g_poly([(-2.54, 0), (2.54, 0)])], 2.54)
S_PUSH = dos_pines("SW_PUSH_H", "SW", "SW_Push", [g_circ(-2.032, 0, 0.508), g_circ(2.032, 0, 0.508),
                                                  g_poly([(-2.54, 1.905), (2.54, 1.905)]), g_poly([(0, 1.905), (0, 3.175)])], 3.81)
S_SPST = dos_pines("SW_SPST_H", "SW", "SW_SPST", [g_circ(-2.032, 0, 0.508), g_circ(2.032, 0, 0.508),
                                                  g_poly([(-1.778, 0.254), (1.778, 1.905)])], 2.54)
S_BAT = dos_pines("BAT_2S_H", "BT", "Battery", [g_poly([(-2.54, -1.016), (-2.54, 1.016)]), g_poly([(-1.27, -2.032), (-1.27, 2.032)]),
                                                g_poly([(0, -1.016), (0, 1.016)]), g_poly([(1.27, -2.032), (1.27, 2.032)]),
                                                g_text("2S", 0, 3.4)], 4.0, "-", "+", len1=2.54, len2=3.81)
S_MOTOR = Sym("MOTOR_DC", "M", "Motor",
              [g_rect(-3.81, 3.81, 3.81, -3.81, "none"), g_circ(0, 0, 2.54), g_text("M", 0, 0, 2.54)],
              [dict(num="1", name="1", x=-7.62, y=1.27, ang=0, len=3.81), dict(num="2", name="2", x=-7.62, y=-1.27, ang=0, len=3.81)],
              3.81, ocultar_nombres=True)
S_BUCK = caja("BUCK_MODULE", "U", "Buck", [("1", "IN+"), ("2", "IN-")], [("3", "OUT+"), ("4", "OUT-")])
S_NMOS = caja("NMOS_LOGICO", "Q", "NMOS", [None, ("1", "G"), None], [("2", "D"), None, ("3", "S")], 10.16,
              [g_text("NMOS", 0, 0)])
S_POT = caja("POT", "RV", "POT", [("1", "A"), ("2", "B")], [("3", "W")], 10.16)
S_TB = caja("TB6612FNG_MODULO", "U", "TB6612FNG",
            [("1", "VM"), ("2", "VCC"), ("3", "GND"), ("4", "PWMA"), ("5", "AIN1"), ("6", "AIN2"), ("7", "STBY"),
             ("8", "PWMB"), ("9", "BIN1"), ("10", "BIN2")],
            [("11", "AO1"), ("12", "AO2"), None, None, None, None, ("13", "BO1"), ("14", "BO2")])
S_MUX = caja("CD74HC4067_MODULO", "U", "CD74HC4067",
             [("1", "S0"), ("2", "S1"), ("3", "S2"), ("4", "S3"), ("5", "E"), ("6", "SIG"), ("7", "VCC"), ("8", "GND")],
             [(str(9 + i), f"I{i}") for i in range(16)])
S_QTR = caja("QTR_8A", "U", "QTR-8A",
             [(str(1 + i), f"OUT{i + 1}") for i in range(8)],
             [("9", "VCC"), ("10", "GND"), ("11", "EMIT_RTN")])


def simbolo_esp32():
    izq = [("VIN", "VIN", "+5V"), ("3V3", "3V3", "+3V3"), ("GND", "GND", "GND")]
    for clave in ["PIN_BATERIA", "PIN_PERFIL", "PIN_MUX_SIG1", "PIN_MUX_SIG2", "PIN_START", "PIN_CAL", "PIN_LED"]:
        izq.append((str(PIN[clave]), f"GPIO{PIN[clave]}", clave[4:]))
    der = []
    for clave in ["PIN_MUX_S0", "PIN_MUX_S1", "PIN_MUX_S2", "PIN_MUX_S3", "PIN_EMISORES", "PIN_PWMA", "PIN_AIN1",
                  "PIN_AIN2", "PIN_PWMB", "PIN_BIN1", "PIN_BIN2", "PIN_STBY"]:
        der.append((str(PIN[clave]), f"GPIO{PIN[clave]}", clave[4:]))
    sym = caja("ESP32_DEVKIT_38", "U", "ESP32 DevKit (WROOM-32)", [(a, b) for a, b, _ in izq], [(a, b) for a, b, _ in der])
    return sym, izq, der


# ------------------------------------------------------------------ documento
class Doc:
    def __init__(self):
        self.items = []
        self.syms = {}
        self.inst = {}
        self.spec = {}      # red -> [(ref, pin)]
        self.nc = []        # [(ref, pin)]
        self.n = 0

    def uid(self, tag):
        self.n += 1
        return Q(str(uuid.uuid5(NS, f"{self.n}:{tag}")))

    def pos(self, ref, pin):
        i = self.inst[ref]
        p = i["sym"].pin(pin)
        return (round(i["x"] + p["x"], 4), round(i["y"] - p["y"], 4))

    def colocar(self, sym, ref, valor, x, y):
        x, y = round(x, 4), round(y, 4)
        assert ref not in self.inst, ref
        self.syms[sym.nombre] = sym
        self.inst[ref] = dict(sym=sym, x=x, y=y)
        for p in sym.pines:
            px, py = x + p["x"], y - p["y"]
            for v in (px, py):
                assert abs(v / 1.27 - round(v / 1.27)) < 1e-3, f"{ref}.{p['name']} fuera de la rejilla de 1.27 mm ({px},{py})"
        pins = [["pin", Q(p["num"]), ["uuid", self.uid(f"{ref}.{p['num']}")]] for p in sym.pines]
        self.items.append(["symbol", ["lib_id", Q(f"{NICK}:{sym.nombre}")], ["at", x, y, 0], ["unit", 1],
                           ["in_bom", "yes"], ["on_board", "yes"], ["dnp", "no"], ["uuid", self.uid(ref)],
                           ["property", Q("Reference"), Q(ref), ["at", x, round(y - sym.top - 1.27, 4), 0], efectos()],
                           ["property", Q("Value"), Q(valor), ["at", x, round(y + sym.top + 1.27, 4), 0], efectos()],
                           ["property", Q("Footprint"), Q(""), ["at", x, y, 0], efectos(oculto=True)],
                           ["property", Q("Datasheet"), Q("~"), ["at", x, y, 0], efectos(oculto=True)],
                           *pins,
                           ["instances", ["project", Q(PROYECTO), ["path", Q("/" + UUID_RAIZ),
                                                                 ["reference", Q(ref)], ["unit", 1]]]]])

    def colocar_en_pin(self, sym, ref, valor, pin, destino):
        p = sym.pin(pin)
        self.colocar(sym, ref, valor, destino[0] - p["x"], destino[1] + p["y"])

    def cable(self, a, b):
        self.items.append(["wire", ["pts", ["xy", a[0], a[1]], ["xy", b[0], b[1]]],
                           ["stroke", ["width", 0], ["type", "default"]], ["uuid", self.uid("w")]])

    def etiqueta(self, red, pt, ang):
        self.items.append(["label", Q(red), ["at", pt[0], pt[1], ang],
                           efectos(justif=("right", "bottom") if ang == 180 else ("left", "bottom")),
                           ["uuid", self.uid("l:" + red)]])

    def spec_add(self, red, ref, pin):
        self.spec.setdefault(red, []).append((ref, pin))

    def conectar(self, ref, pin, red, largo=2.54):
        """Cable corto + etiqueta de red en el pin."""
        a = self.pos(ref, pin)
        saliente = -1 if self.inst[ref]["sym"].pin(pin)["ang"] == 0 else 1
        b = (round(a[0] + saliente * largo, 4), a[1])
        self.cable(a, b)
        self.etiqueta(red, b, 180 if saliente < 0 else 0)
        self.spec_add(red, ref, pin)

    def unir(self, r1, p1, r2, p2, red):
        a, b = self.pos(r1, p1), self.pos(r2, p2)
        assert abs(a[1] - b[1]) < 1e-6, f"{r1}.{p1} y {r2}.{p2} no están alineados"
        self.cable(a, b)
        self.spec_add(red, r1, p1)
        self.spec_add(red, r2, p2)

    def sin_conexion(self, ref, pin):
        a = self.pos(ref, pin)
        self.items.append(["no_connect", ["at", a[0], a[1]], ["uuid", self.uid("nc")]])
        self.nc.append((ref, pin))

    def texto(self, x, y, s, tam=1.27):
        self.items.append(["text", Q(s), ["at", x, y, 0], efectos(tam, justif=("left", "top")), ["uuid", self.uid("t")]])

    def marco(self, x1, y1, x2, y2, titulo):
        self.items.append(["rectangle", ["start", x1, y1], ["end", x2, y2],
                           ["stroke", ["width", 0.2], ["type", "dash"]], ["fill", ["type", "none"]],
                           ["uuid", self.uid("m")]])
        self.texto(x1 + 2, y1 + 2, titulo, 2.0)


def p(x, y):
    """Ajusta a la rejilla de 2.54 mm."""
    return round(round(x / 2.54) * 2.54, 4), round(round(y / 2.54) * 2.54, 4)


def construir():
    d = Doc()
    esp, esp_izq, esp_der = simbolo_esp32()

    # ---------------- Alimentación
    d.marco(12, 24, 150, 176, "ALIMENTACION")
    d.colocar(S_BAT, "BT1", "LiPo 2S 7.4 V", *p(30, 46))
    a = d.pos("BT1", "+")
    d.colocar_en_pin(S_FUSE, "F1", "Fusible reseteable", "1", (a[0] + 25.4, a[1]))
    d.unir("BT1", "+", "F1", "1", "VBAT_BAT")
    b = d.pos("F1", "2")
    d.colocar_en_pin(S_SPST, "SW1", "Interruptor general", "1", (b[0] + 25.4, b[1]))
    d.unir("F1", "2", "SW1", "1", "VBAT_FUS")
    d.conectar("BT1", "-", "GND")
    d.conectar("SW1", "2", "VBAT")
    d.colocar(S_BUCK, "U2", "Buck 6 V (>= 2 A): motores", *p(62, 88))
    d.conectar("U2", "IN+", "VBAT"); d.conectar("U2", "IN-", "GND")
    d.conectar("U2", "OUT+", "+6V"); d.conectar("U2", "OUT-", "GND")
    d.colocar(S_BUCK, "U3", "Buck 5 V (>= 1 A): ESP32", *p(62, 118))
    d.conectar("U3", "IN+", "VBAT"); d.conectar("U3", "IN-", "GND")
    d.conectar("U3", "OUT+", "+5V"); d.conectar("U3", "OUT-", "GND")
    d.texto(18, 138, "Divisor de bateria: 8.4 V -> 2.7 V en GPIO36")
    d.colocar(S_R, "R1", "100k", *p(30, 152))
    d.conectar("R1", "1", "VBAT"); d.conectar("R1", "2", "BATERIA")
    d.colocar(S_R, "R2", "47k", *p(78, 152))
    d.conectar("R2", "1", "BATERIA"); d.conectar("R2", "2", "GND")

    # ---------------- Microcontrolador
    d.marco(160, 62, 250, 126, "MICROCONTROLADOR")
    d.colocar(esp, "U1", "ESP32 DevKit 38 pines (WROOM-32)", *p(205, 96))
    for nombre_pin, _, red in esp_izq:
        pin = [x for x in esp.pines if x["num"] == nombre_pin][0]["name"]
        if red in ("MUX_SIG2", "LED"):
            d.sin_conexion("U1", pin)
        else:
            d.conectar("U1", pin, red)
    for nombre_pin, _, red in esp_der:
        pin = [x for x in esp.pines if x["num"] == nombre_pin][0]["name"]
        d.conectar("U1", pin, red)
    d.texto(164, 116, "GPIO35 reservado: perfil de 24 canales (2.o mux).\nGPIO2: LED azul de la placa, sin componente externo.", 1.0)

    # ---------------- Motores
    d.marco(256, 20, 408, 108, "DRIVER Y MOTORES")
    d.colocar(S_TB, "U4", "TB6612FNG (modulo)", *p(318, 68))
    for pin, red in [("VM", "+6V"), ("VCC", "+3V3"), ("GND", "GND"), ("PWMA", "PWMA"), ("AIN1", "AIN1"), ("AIN2", "AIN2"),
                     ("STBY", "STBY"), ("PWMB", "PWMB"), ("BIN1", "BIN1"), ("BIN2", "BIN2")]:
        d.conectar("U4", pin, red)
    a = d.pos("U4", "AO1")
    d.colocar_en_pin(S_MOTOR, "M1", "N20 6 V (rueda izq., canal A)", "1", (a[0] + 20.32, a[1]))
    d.unir("U4", "AO1", "M1", "1", "MOT_IZQ_1"); d.unir("U4", "AO2", "M1", "2", "MOT_IZQ_2")
    a = d.pos("U4", "BO1")
    d.colocar_en_pin(S_MOTOR, "M2", "N20 6 V (rueda der., canal B)", "1", (a[0] + 20.32, a[1]))
    d.unir("U4", "BO1", "M2", "1", "MOT_DER_1"); d.unir("U4", "BO2", "M2", "2", "MOT_DER_2")
    d.colocar(S_CP, "C1", "100-470uF (VM)", *p(292, 36))
    d.conectar("C1", "+", "+6V"); d.conectar("C1", "-", "GND")
    d.colocar(S_C, "C2", "100nF (VCC)", *p(352, 36))
    d.conectar("C2", "1", "+3V3"); d.conectar("C2", "2", "GND")

    # ---------------- Sensores
    d.marco(256, 116, 408, 250, "SENSORES (perfil QTR-8A, 8 canales)")
    d.colocar(S_MUX, "U5", "CD74HC4067 (modulo)", *p(296, 170))
    for pin, red in [("S0", "MUX_S0"), ("S1", "MUX_S1"), ("S2", "MUX_S2"), ("S3", "MUX_S3"), ("E", "GND"),
                     ("SIG", "MUX_SIG1"), ("VCC", "+3V3"), ("GND", "GND")]:
        d.conectar("U5", pin, red)
    a = d.pos("U5", "I0")
    d.colocar_en_pin(S_QTR, "U6", "QTR-8A (1 + repuesto)", "OUT1", (a[0] + 25.4, a[1]))
    for i in range(8):
        d.unir("U5", f"I{i}", "U6", f"OUT{i + 1}", f"SENS{i + 1}")
    for i in range(8, 16):
        d.sin_conexion("U5", f"I{i}")
    d.conectar("U6", "VCC", "+3V3"); d.conectar("U6", "GND", "GND"); d.conectar("U6", "EMIT_RTN", "EMIT_RTN")
    d.colocar(S_C, "C3", "100nF (mux)", *p(296, 208))
    d.conectar("C3", "1", "+3V3"); d.conectar("C3", "2", "GND")
    d.colocar(S_C, "C4", "100nF (sensor)", *p(386, 132))
    d.conectar("C4", "1", "+3V3"); d.conectar("C4", "2", "GND")
    d.texto(318, 138, "OUT1 = extremo izq. de la barra (VERIFICAR)", 1.0)
    d.colocar(S_R, "R3", "100", *p(322, 222))
    d.conectar("R3", "1", "EMISORES"); d.conectar("R3", "2", "Q1_G")
    d.colocar(S_R, "R4", "100k", *p(322, 238))
    d.conectar("R4", "1", "Q1_G"); d.conectar("R4", "2", "GND")
    d.colocar(S_NMOS, "Q1", "MOSFET nivel logico", *p(380, 230))
    d.conectar("Q1", "G", "Q1_G"); d.conectar("Q1", "D", "EMIT_RTN"); d.conectar("Q1", "S", "GND")

    # ---------------- Interfaz
    d.marco(160, 132, 250, 226, "INTERFAZ")
    d.colocar(S_PUSH, "SW2", "START", *p(192, 154))
    d.conectar("SW2", "1", "START"); d.conectar("SW2", "2", "GND")
    d.colocar(S_PUSH, "SW3", "CAL", *p(192, 172))
    d.conectar("SW3", "1", "CAL"); d.conectar("SW3", "2", "GND")
    d.colocar(S_POT, "RV1", "Perilla de perfil de velocidad", *p(192, 196))
    d.conectar("RV1", "A", "+3V3"); d.conectar("RV1", "B", "GND"); d.conectar("RV1", "W", "PERFIL")
    d.texto(164, 212, "START y CAL: pull-up interno del ESP32, botones a GND.", 1.0)

    # ---------------- Notas
    d.texto(15, 182,
            "NOTAS DE DISENO (de docs/electronica.md y docs/plan.md)\n"
            "1. Todo lo que toca un pin del ESP32 trabaja a 3.3 V (sensor, mux, logica del TB6612, botones).\n"
            "2. Motores desde su propio buck de 6 V; ESP32 por VIN desde otro buck de 5 V.\n"
            "    Nunca alimentar los motores del regulador del ESP32.\n"
            "3. Una sola union de tierras (estrella) cerca de la bateria; cables de motor lejos de los sensores.\n"
            "4. Capacitor de 100-470 uF en VM del TB6612 y 100 nF en cada modulo.\n"
            "5. Fusible reseteable en serie con el positivo de la bateria.\n"
            "6. Sin WiFi ni Bluetooth (el reglamento los prohibe en competencia).\n"
            "7. Cargar la LiPo solo con cargador balanceado y bolsa o caja para LiPo.", 1.1)
    d.texto(15, 222,
            "POR VERIFICAR (todavia no hay piezas reales; nada de esto esta aprobado por el equipo)\n"
            "- Pinout real del ESP32 DevKit: aqui el numero de pin es el GPIO, no la posicion fisica.\n"
            "- QTR-8A: orden de salidas, sentido del voltaje sobre negro (ALTO_ES_NEGRO) y si trae pin LEDON.\n"
            "  Q1 conmuta el retorno de los LED IR (red EMIT_RTN). El QTR-8A no expone ese retorno:\n"
            "  si se usa su pin LEDON, GPIO13 iria directo a LEDON y se retiran Q1, R3 y R4\n"
            "  (revisar la logica en la ficha; con Q1 la logica quedaria invertida).\n"
            "- Consumo del sensor sobre el 3V3 de la placa y tiempo de lectura del mux a 3.3 V.\n"
            "- Nombres y orden de pines de los modulos reales (TB6612, CD74HC4067, bucks).\n"
            "- Perfil de 24 canales: 2.o CD74HC4067 en MUX_SIG2 (GPIO35) con S0-S3 compartidos.\n"
            "- Los simbolos son funcionales y sin huella (footprint) todavia.", 1.1)
    return d


# ------------------------------------------------------------------ escritura
def escribir(d):
    SALIDA.mkdir(parents=True, exist_ok=True)
    simbolos = [d.syms[k] for k in sorted(d.syms)]
    sch = ["kicad_sch", ["version", 20230121], ["generator", "eeschema"], ["uuid", Q(UUID_RAIZ)], ["paper", Q("A3")],
           ["title_block", ["title", Q("Seguidor de linea - esquema de conexiones")], ["date", Q(FECHA)],
            ["rev", Q(REVISION)], ["company", Q("Circuit Forge")],
            ["comment", 1, Q("Generado por herramientas/generar_kicad.py desde firmware/seguidor/pines.h")],
            ["comment", 2, Q("Propuesta: nada aprobado por el equipo (ver docs/decisiones.md)")],
            ["comment", 3, Q("Simbolos funcionales: numero de pin = GPIO o secuencial, no posicion fisica")]],
           ["lib_symbols", *[s.lib(True) for s in simbolos]],
           *d.items,
           ["sheet_instances", ["path", Q("/"), ["page", Q("1")]]]]
    (SALIDA / "seguidor.kicad_sch").write_text(sx(sch) + "\n", encoding="utf-8")
    lib = ["kicad_symbol_lib", ["version", 20220914], ["generator", "kicad_symbol_editor"], *[s.lib(False) for s in simbolos]]
    (SALIDA / "seguidor.kicad_sym").write_text(sx(lib) + "\n", encoding="utf-8")
    (SALIDA / "sym-lib-table").write_text(
        "(sym_lib_table\n  (version 7)\n"
        f'  (lib (name "{NICK}")(type "KiCad")(uri "${{KIPRJMOD}}/seguidor.kicad_sym")(options "")'
        '(descr "Simbolos funcionales del seguidor de linea"))\n)\n', encoding="utf-8")
    (SALIDA / "seguidor.kicad_pro").write_text(
        json.dumps({"meta": {"filename": "seguidor.kicad_pro", "version": 1}}, indent=2) + "\n", encoding="utf-8")


# ------------------------------------------------------------------ verificación (lee lo escrito)
def leer_sexp(s):
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|\(|\)|[^\s()"]+', s)

    def rd(i):
        if tokens[i] == "(":
            lst = []
            i += 1
            while tokens[i] != ")":
                v, i = rd(i)
                lst.append(v)
            return lst, i + 1
        t = tokens[i]
        if t.startswith('"'):
            t = t[1:-1].replace('\\"', '"').replace("\\n", "\n").replace("\\\\", "\\")
        return t, i + 1

    arbol, fin = rd(0)
    assert fin == len(tokens), "sobran tokens al final del archivo"
    return arbol


def hijo(nodo, cab):
    for h in nodo:
        if isinstance(h, list) and h and h[0] == cab:
            return h
    return None


def hijos(nodo, cab):
    return [h for h in nodo if isinstance(h, list) and h and h[0] == cab]


def verificar(d):
    arbol = leer_sexp((SALIDA / "seguidor.kicad_sch").read_text(encoding="utf-8"))
    libs = {}
    for s in hijos(hijo(arbol, "lib_symbols"), "symbol"):
        pines = {}
        for sub in hijos(s, "symbol"):
            for pn in hijos(sub, "pin"):
                at = hijo(pn, "at")
                pines[hijo(pn, "number")[1]] = (float(at[1]), float(at[2]), hijo(pn, "name")[1])
        libs[s[1]] = pines
    clave = lambda x, y: (round(float(x), 2), round(float(y), 2))
    pin_en = {}          # punto -> [(ref, nombre)]
    refs = []
    for s in hijos(arbol, "symbol"):
        ref = [pr[2] for pr in hijos(s, "property") if pr[1] == "Reference"][0]
        refs.append(ref)
        at = hijo(s, "at")
        for num_pin, (px, py, nombre) in libs[hijo(s, "lib_id")[1]].items():
            pin_en.setdefault(clave(float(at[1]) + px, float(at[2]) - py), []).append((ref, nombre))
    padre = {}

    def raiz(k):
        padre.setdefault(k, k)
        while padre[k] != k:
            padre[k] = padre[padre[k]]
            k = padre[k]
        return k

    def unir(a, b):
        padre[raiz(a)] = raiz(b)

    puntos = set(pin_en)
    for w in hijos(arbol, "wire"):
        xy = hijos(hijo(w, "pts"), "xy")
        a, b = clave(xy[0][1], xy[0][2]), clave(xy[1][1], xy[1][2])
        puntos.update([a, b])
        unir(a, b)
    por_nombre = {}
    nombres_en = {}
    for lb in hijos(arbol, "label"):
        at = hijo(lb, "at")
        k = clave(at[1], at[2])
        assert k in puntos, f"etiqueta {lb[1]} flotante en {k}"
        por_nombre.setdefault(lb[1], []).append(k)
        nombres_en[k] = lb[1]
    for nombre, ks in por_nombre.items():
        for k in ks[1:]:
            unir(ks[0], k)
    ncs = {clave(hijo(n, "at")[1], hijo(n, "at")[2]) for n in hijos(arbol, "no_connect")}
    grupos = {}
    for k, lista in pin_en.items():
        grupos.setdefault(raiz(k), set()).update(lista)
    reales_nc = set()
    reales = set()
    for k, lista in pin_en.items():
        if k in ncs:
            assert len(lista) == 1 and len(grupos[raiz(k)]) == 1, f"pin sin conexion {lista} conectado a algo"
            reales_nc.update(lista)
    for g in grupos.values():
        if not g <= reales_nc:
            reales.add(frozenset(g))
    esperado = {frozenset(v) for v in d.spec.values()}
    assert all(len(v) >= 2 for v in d.spec.values()), "hay una red con un solo pin"
    assert reales_nc == set(d.nc), f"pines sin conexion distintos: {reales_nc ^ set(d.nc)}"
    if reales != esperado:
        sobra = [sorted(g) for g in reales - esperado][:3]
        falta = [sorted(g) for g in esperado - reales][:3]
        sys.exit(f"CONECTIVIDAD DISTINTA.\n sobra: {sobra}\n falta: {falta}")
    total = sum(len(l) for l in pin_en.values())
    cubiertos = sum(len(g) for g in reales) + len(reales_nc)
    assert total == cubiertos, f"hay pines sin cubrir: {total - cubiertos}"
    for g in grupos.values():
        pass
    # un nombre de red por grupo (sin cortos entre redes con etiqueta)
    for g_raiz in {raiz(k) for k in puntos}:
        nombres = {nombres_en[k] for k in puntos if raiz(k) == g_raiz and k in nombres_en}
        assert len(nombres) <= 1, f"cortocircuito entre redes {nombres}"
    # contra pines.h
    por_pin = {}
    for g in reales:
        for r, n in g:
            por_pin[(r, n)] = g
    esperado_h = {
        "PIN_MUX_S0": ("U5", "S0"), "PIN_MUX_S1": ("U5", "S1"), "PIN_MUX_S2": ("U5", "S2"), "PIN_MUX_S3": ("U5", "S3"),
        "PIN_MUX_SIG1": ("U5", "SIG"), "PIN_EMISORES": ("R3", "1"), "PIN_PWMA": ("U4", "PWMA"), "PIN_AIN1": ("U4", "AIN1"),
        "PIN_AIN2": ("U4", "AIN2"), "PIN_PWMB": ("U4", "PWMB"), "PIN_BIN1": ("U4", "BIN1"), "PIN_BIN2": ("U4", "BIN2"),
        "PIN_STBY": ("U4", "STBY"), "PIN_START": ("SW2", "1"), "PIN_CAL": ("SW3", "1"), "PIN_PERFIL": ("RV1", "W"),
        "PIN_BATERIA": ("R1", "2")}
    for clave_h, destino in esperado_h.items():
        g = por_pin[("U1", f"GPIO{PIN[clave_h]}")]
        assert destino in g and len(g) == 2 + (clave_h == "PIN_BATERIA"), f"{clave_h}: GPIO{PIN[clave_h]} no llega a {destino}: {sorted(g)}"
    assert ("U1", f"GPIO{PIN['PIN_LED']}") in reales_nc and ("U1", f"GPIO{PIN['PIN_MUX_SIG2']}") in reales_nc
    return len(refs), len(reales), len(reales_nc)


def main():
    d = construir()
    escribir(d)
    piezas, redes, nc = verificar(d)
    print(f"ok: {piezas} piezas, {redes} redes, {nc} pines sin conexion marcados -> {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
