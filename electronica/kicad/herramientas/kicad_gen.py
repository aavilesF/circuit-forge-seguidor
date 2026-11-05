#!/usr/bin/env python3
"""Generador de esquemáticos de KiCad 7 (formato .kicad_sch) a partir de una descripción en Python.

Idea (de la skill proyectos-electronicos-kicad): los diagramas se GENERAN desde una sola fuente de verdad
(los scripts generar_*.py y pines_robot_casero.h); nunca se editan a mano.

Cada pin de cada pieza lleva un tramo corto de cable que termina en una etiqueta de red (o en un símbolo de
alimentación). Así dos pines con la misma etiqueta quedan en la misma red. Los símbolos salen de las
bibliotecas oficiales de KiCad (/usr/share/kicad/symbols) o de la biblioteca propia robot_casero.
"""
import re
import uuid
from pathlib import Path

SYM_DIR = Path("/usr/share/kicad/symbols")
NS = uuid.UUID("0b0a5b4e-6a54-4f57-9d8e-5d1f2c3a4b5c")  # espacio de nombres fijo: UUID estables entre corridas


def uid(*parts):
    return str(uuid.uuid5(NS, "/".join(str(p) for p in parts)))


# ---------------------------------------------------------------- s-expresiones
def parse_sexp(text):
    tokens = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+', text)
    stack = [[]]
    for t in tokens:
        if t == "(":
            stack.append([])
        elif t == ")":
            x = stack.pop()
            stack[-1].append(x)
        else:
            stack[-1].append(t)
    return stack[0]


def unq(s):
    return s[1:-1] if isinstance(s, str) and s.startswith('"') else s


def extract_symbol_text(lib, name):
    """Devuelve el texto del símbolo `name` de la biblioteca `lib` (equilibrando paréntesis)."""
    txt = (SYM_DIR / f"{lib}.kicad_sym").read_text()
    m = re.search(r'\n\s*\(symbol "' + re.escape(name) + r'"', txt)
    if not m:
        raise KeyError(f"{lib}:{name} no existe en la biblioteca")
    start = m.start() + 1
    while txt[start] in " \t\n":
        start += 1
    depth, i, in_str = 0, start, False
    while True:
        c = txt[i]
        if in_str:
            if c == "\\":
                i += 1
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    return txt[start:i + 1]
        i += 1


def symbol_pins(sym_text):
    """Lista de pines: dict(number, name, type, x, y, angle)."""
    tree = parse_sexp(sym_text)[0]
    pins = []

    def walk(node):
        if isinstance(node, list) and node and node[0] == "pin" and len(node) > 4:
            at = next(n for n in node if isinstance(n, list) and n and n[0] == "at")
            nm = next(n for n in node if isinstance(n, list) and n and n[0] == "name")
            nu = next(n for n in node if isinstance(n, list) and n and n[0] == "number")
            pins.append(dict(number=unq(nu[1]), name=unq(nm[1]), type=node[1],
                             x=float(at[1]), y=float(at[2]), angle=int(float(at[3]))))
            return
        if isinstance(node, list):
            for n in node:
                walk(n)

    walk(tree)
    return pins


def rotate(px, py, r):
    if r == 0:
        return px, py
    if r == 90:
        return -py, px
    if r == 180:
        return -px, -py
    if r == 270:
        return py, -px
    raise ValueError(r)


def fmt(v):
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


# ---------------------------------------------------------------- símbolos propios
def make_custom_symbol(name, ref, value, left, right, half_width=12.7, desc="", pin_type="passive"):
    """Crea un símbolo funcional rectangular. left/right: listas de (numero, nombre[, tipo])."""
    n = max(len(left), len(right))
    top = (n - 1) * 2.54 / 2 + 2.54
    bot = -top
    lines = [f'(symbol "{name}" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)',
             f'  (property "Reference" "{ref}" (at 0 {fmt(top + 2.54)} 0) (effects (font (size 1.27 1.27))))',
             f'  (property "Value" "{value}" (at 0 {fmt(bot - 2.54)} 0) (effects (font (size 1.27 1.27))))',
             '  (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
             '  (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
             f'  (property "ki_description" "{desc}" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
             f'  (symbol "{name}_0_1"',
             f'    (rectangle (start {fmt(-half_width)} {fmt(top)}) (end {fmt(half_width)} {fmt(bot)})'
             ' (stroke (width 0.254) (type default)) (fill (type background)))',
             "  )",
             f'  (symbol "{name}_1_1"']
    for side, pins in (("L", left), ("R", right)):
        for i, p in enumerate(pins):
            num, nm = p[0], p[1]
            typ = p[2] if len(p) > 2 else pin_type
            y = top - 2.54 - i * 2.54 + 0.0
            y = (n - 1) * 2.54 / 2 - i * 2.54
            x = -(half_width + 2.54) if side == "L" else (half_width + 2.54)
            ang = 0 if side == "L" else 180
            lines.append(f'    (pin {typ} line (at {fmt(x)} {fmt(y)} {ang}) (length 2.54)'
                         f' (name "{nm}" (effects (font (size 1.016 1.016))))'
                         f' (number "{num}" (effects (font (size 1.016 1.016)))))')
    lines.append("  )")
    lines.append(")")
    return "\n".join(lines)


# ---------------------------------------------------------------- esquemático
POWER_SYMS = {"GND": "GND", "+3V3": "+3V3", "+5V": "+5V"}


class Esquematico:
    def __init__(self, proyecto, titulo, revision, comentarios=(), papel="A3"):
        self.proyecto = proyecto
        self.titulo = titulo
        self.revision = revision
        self.comentarios = list(comentarios)
        self.papel = papel
        self.root = uid(proyecto, "root")
        self.libsyms = {}   # lib_id -> texto con nombre calificado
        self.pins_cache = {}
        self.items = []
        self.contador = {}
        self.conexiones = []  # (ref, pin_num, pin_name, pin_type, net)  -> lista esperada de redes
        self.nc = []          # (ref, pin_num)
        self.pwr_n = 0
        self.flg_n = 0
        self.textos = []

    # --- bibliotecas
    def usar_oficial(self, lib_id):
        if lib_id in self.libsyms:
            return
        lib, name = lib_id.split(":")
        txt = extract_symbol_text(lib, name)
        txt = txt.replace(f'(symbol "{name}"', f'(symbol "{lib_id}"', 1)
        self.libsyms[lib_id] = txt
        self.pins_cache[lib_id] = symbol_pins(txt)

    def usar_propio(self, lib_id, texto):
        """texto: símbolo creado con make_custom_symbol (sin prefijo de biblioteca)."""
        name = lib_id.split(":")[1]
        txt = texto.replace(f'(symbol "{name}"', f'(symbol "{lib_id}"', 1)
        self.libsyms[lib_id] = txt
        self.pins_cache[lib_id] = symbol_pins(txt)

    # --- colocación
    def _pin_pos(self, lib_id, x, y, rot, pin):
        rx, ry = rotate(pin["x"], pin["y"], rot)
        return x + rx, y - ry, (pin["angle"] + rot) % 360

    def _stub(self, px, py, ang, largo):
        import math
        a = math.radians(ang)
        dx = round(-math.cos(a), 6)
        dy = round(math.sin(a), 6)   # coordenadas de pantalla: y hacia abajo
        ex, ey = px + dx * largo, py + dy * largo
        if abs(dx) > abs(dy):
            lab = 180 if dx < 0 else 0
        else:
            lab = 90 if dy < 0 else 270
        return ex, ey, lab

    def _wire(self, x1, y1, x2, y2, k):
        self.items.append(f'  (wire (pts (xy {fmt(x1)} {fmt(y1)}) (xy {fmt(x2)} {fmt(y2)}))'
                          f' (stroke (width 0) (type default)) (uuid "{uid(self.proyecto, "w", k)}"))')

    def _label(self, net, x, y, ang, k):
        just = "right bottom" if ang == 180 else "left bottom"
        self.items.append(f'  (label "{net}" (at {fmt(x)} {fmt(y)} {ang})'
                          f' (effects (font (size 1.27 1.27)) (justify {just})) (uuid "{uid(self.proyecto, "l", k)}"))')

    def _power_symbol(self, net, x, y, ang):
        sym = POWER_SYMS[net]
        lib_id = f"power:{sym}"
        self.usar_oficial(lib_id)
        self.pwr_n += 1
        ref = f"#PWR{self.pwr_n:02d}"
        # El símbolo de tierra "cuelga" hacia abajo y los de +V "salen" hacia arriba: se gira para que quede
        # en la dirección del cable y no se encime con las etiquetas de los pines vecinos.
        if net == "GND":
            rot = {270: 0, 0: 90, 180: 270, 90: 180}[ang]
        else:
            rot = {90: 0, 0: 270, 180: 90, 270: 180}[ang]
        self.items.append(self._symbol_text(lib_id, ref, sym, "", x, y, rot, power=True))
        # no hay pines extra que anotar: el pin de la alimentación queda en (x, y)

    def _symbol_text(self, lib_id, ref, value, footprint, x, y, rot, power=False, extra_props=()):
        pins = self.pins_cache[lib_id]
        top = min(-(rotate(p["x"], p["y"], rot)[1]) for p in pins) if pins else 0
        bot = max(-(rotate(p["x"], p["y"], rot)[1]) for p in pins) if pins else 0
        hide = " hide" if power else ""
        props = [
            f'    (property "Reference" "{ref}" (at {fmt(x)} {fmt(y + top - 2.54)} 0)'
            f' (effects (font (size 1.27 1.27)){hide}))',
            f'    (property "Value" "{value}" (at {fmt(x)} {fmt(y + bot + 2.54)} 0)'
            f' (effects (font (size 1.27 1.27)){hide}))',
            f'    (property "Footprint" "{footprint}" (at {fmt(x)} {fmt(y)} 0)'
            ' (effects (font (size 1.27 1.27)) hide))',
            f'    (property "Datasheet" "" (at {fmt(x)} {fmt(y)} 0) (effects (font (size 1.27 1.27)) hide))',
        ]
        for k, v in extra_props:
            props.append(f'    (property "{k}" "{v}" (at {fmt(x)} {fmt(y)} 0)'
                         ' (effects (font (size 1.27 1.27)) hide))')
        pin_lines = "\n".join(f'    (pin "{p["number"]}" (uuid "{uid(self.proyecto, ref, "pin", p["number"])}"))'
                              for p in pins)
        return (f'  (symbol (lib_id "{lib_id}") (at {fmt(x)} {fmt(y)} {rot}) (unit 1)'
                f' (in_bom {"no" if power else "yes"}) (on_board {"no" if power else "yes"}) (dnp no)'
                f' (uuid "{uid(self.proyecto, ref, "sym")}")\n' + "\n".join(props) + "\n" + pin_lines + "\n"
                f'    (instances (project "{self.proyecto}" (path "/{self.root}"'
                f' (reference "{ref}") (unit 1))))\n  )')

    def pieza(self, ref, lib_id, value, footprint, x, y, rot=0, redes=None, nc=(), largo=5.08, extra_props=()):
        """Coloca una pieza. redes: {pin(numero o nombre): red}. nc: pines sin conexión (numero o nombre)."""
        if lib_id not in self.libsyms:
            self.usar_oficial(lib_id)
        pins = self.pins_cache[lib_id]
        redes = dict(redes or {})
        nc = set(nc)
        self.items.append(self._symbol_text(lib_id, ref, value, footprint, x, y, rot, extra_props=extra_props))
        usados = set()
        for p in pins:
            clave = p["number"] if p["number"] in redes else (p["name"] if p["name"] in redes else None)
            es_nc = p["number"] in nc or p["name"] in nc
            if clave is None and not es_nc:
                raise ValueError(f"{ref}: el pin {p['number']} ({p['name']}) no tiene red ni está marcado NC")
            px, py, ang = self._pin_pos(lib_id, x, y, rot, p)
            if es_nc and clave is None:
                self.items.append(f'  (no_connect (at {fmt(px)} {fmt(py)}) (uuid "{uid(self.proyecto, ref, "nc", p["number"])}"))')
                self.nc.append((ref, p["number"], p["name"]))
                continue
            usados.add(clave)
            red = redes[clave]
            ex, ey, lab = self._stub(px, py, ang, largo)
            k = f"{ref}-{p['number']}"
            self._wire(px, py, ex, ey, k)
            if red in POWER_SYMS:
                self._power_symbol(red, ex, ey, lab)
            else:
                self._label(red, ex, ey, lab, k)
            self.conexiones.append((ref, p["number"], p["name"], p["type"], red))
        sobran = set(redes) - usados
        if sobran:
            raise ValueError(f"{ref}: pines inexistentes en {lib_id}: {sorted(sobran)}")

    def pwr_flag(self, red, x, y):
        """PWR_FLAG sobre una red de alimentación (necesario para el ERC de KiCad)."""
        self.usar_oficial("power:PWR_FLAG")
        self.flg_n += 1
        ref = f"#FLG{self.flg_n:02d}"
        self.items.append(self._symbol_text("power:PWR_FLAG", ref, "PWR_FLAG", "", x, y, 0, power=True))
        # el pin del PWR_FLAG está en el origen: se conecta con un cable corto a un símbolo de alimentación
        if red in POWER_SYMS:
            self._wire(x, y, x, y + (-2.54 if red != "GND" else 2.54), f"flg{self.flg_n}")
            self._power_symbol(red, x, y + (-2.54 if red != "GND" else 2.54), 270 if red == "GND" else 90)
        else:
            self._wire(x, y, x, y - 2.54, f"flg{self.flg_n}")
            self._label(red, x, y - 2.54, 90, f"flg{self.flg_n}")
        self.conexiones.append((ref, "1", "pwr", "power_out", red))

    def texto(self, s, x, y, tam=1.27, negrita=False):
        s = s.replace('"', "'")
        self.items.append(f'  (text "{s}" (at {fmt(x)} {fmt(y)} 0)'
                          f' (effects (font (size {tam} {tam}){" bold" if negrita else ""}) (justify left bottom))'
                          f' (uuid "{uid(self.proyecto, "t", len(self.items))}"))')

    def escribir(self, ruta):
        cab = [f'(kicad_sch (version 20230121) (generator robot_casero_gen)',
               f'  (uuid "{self.root}")',
               f'  (paper "{self.papel}")',
               '  (title_block',
               f'    (title "{self.titulo}")',
               '    (date "2026-11-05")',
               f'    (rev "{self.revision}")',
               '    (company "Circuit Forge")']
        for i, c in enumerate(self.comentarios[:9], 1):
            cab.append(f'    (comment {i} "{c}")')
        cab.append("  )")
        libs = ["  (lib_symbols"] + ["    " + t.replace("\n", "\n    ") for t in self.libsyms.values()] + ["  )"]
        cola = ['  (sheet_instances (path "/" (page "1")))', ")"]
        Path(ruta).write_text("\n".join(cab + libs + self.items + cola) + "\n")
