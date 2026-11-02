#!/usr/bin/env python3
"""Genera la versión CABLEADA del esquemático de KiCad del seguidor de línea.

A diferencia de generar_kicad.py (que une los pines con etiquetas de red), aquí cada conexión es un
cable dibujado entre los pines, con puntos de unión donde se bifurca. Es la misma lista de conexiones
(se toma de generar_kicad.py) y los mismos pines de firmware/seguidor/pines.h.

Los cables los traza un enrutador ortogonal sobre la rejilla de 1.27 mm: no atraviesa los cuerpos de
los símbolos, solo cruza cables de otra red en perpendicular y nunca los toca. Al terminar, el script
vuelve a leer lo escrito y comprueba que cada red quede conectada SOLO con cables (sin etiquetas).

Salida en docs/diagramas/kicad_cableado/: seguidor_cableado.kicad_pro, .kicad_sch, seguidor.kicad_sym, sym-lib-table
Uso: python3 herramientas/generar_kicad_cableado.py
"""
import heapq
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generar_kicad as base  # noqa: E402  (lee y valida pines.h al importarse)

SALIDA = base.RAIZ / "docs" / "diagramas" / "kicad_cableado"
NOMBRE = "seguidor_cableado"
G = 1.27
DIRS = [(1, 0), (0, 1), (-1, 0), (0, -1)]          # E, S, W, N (en pantalla y crece hacia abajo)
OPUESTA = {0: 2, 1: 3, 2: 0, 3: 1}


# ------------------------------------------------------------------ símbolos (variantes para cablear)
class Sym2(base.Sym):
    """Símbolo con posición propia para Reference/Value (los verticales los llevan a un lado)."""

    def __init__(self, *a, off_ref=None, off_val=None, **k):
        super().__init__(*a, **k)
        self.off_ref, self.off_val = off_ref, off_val

    def lib(self, con_nick):
        nodo = super().lib(con_nick)
        if self.off_ref:
            for h in nodo:
                if isinstance(h, list) and h[0] == "property" and h[1] == "Reference":
                    h[3] = ["at", self.off_ref[0], self.off_ref[1], 0]
                    h[4] = base.efectos(justif=("left",))
                if isinstance(h, list) and h[0] == "property" and h[1] == "Value":
                    h[3] = ["at", self.off_val[0], self.off_val[1], 0]
                    h[4] = base.efectos(justif=("left",))
        return nodo


def vertical(nombre, ref, valor, graficos, nom1="1", nom2="2", len1=2.54, len2=2.54):
    pines = [dict(num="1", name=nom1, x=0.0, y=5.08, ang=270, len=len1),
             dict(num="2", name=nom2, x=0.0, y=-5.08, ang=90, len=len2)]
    return Sym2(nombre, ref, valor, graficos, pines, 5.08, ocultar_nombres=True, off_ref=(3.2, 1.3), off_val=(3.2, -1.3))


S_RV = vertical("R_V", "R", "R", [base.g_rect(-1.016, 2.54, 1.016, -2.54, "none")])
S_CV = vertical("C_V", "C", "C", [base.g_poly([(-2.032, 0.762), (2.032, 0.762)]), base.g_poly([(-2.032, -0.762), (2.032, -0.762)])],
                len1=4.318, len2=4.318)
S_CPV = vertical("CP_V", "C", "CP", [base.g_poly([(-2.032, 0.762), (2.032, 0.762)]), base.g_poly([(-2.032, -0.762), (2.032, -0.762)]),
                                     base.g_text("+", -3.4, 2.0)], "+", "-", len1=4.318, len2=4.318)


def pulsador_espejo():
    """Pulsador con el pin 1 a la derecha (lado del ESP32) y el 2 a la izquierda."""
    pines = [dict(num="1", name="1", x=5.08, y=0.0, ang=180, len=2.54), dict(num="2", name="2", x=-5.08, y=0.0, ang=0, len=2.54)]
    return base.Sym("SW_PUSH_ESP", "SW", "SW_Push", base.S_PUSH.graficos, pines, 3.81, ocultar_nombres=True)


S_PUSH2 = pulsador_espejo()

SENAL = {v: k[4:] for k, v in base.PIN.items()}      # gpio -> nombre de la señal en pines.h


def nombre_u1(gpio):
    return f"GPIO{gpio} {SENAL[gpio]}"


def simbolo_esp32():
    izq = [("VIN", "VIN"), ("3V3", "3V3")]
    for k in ["PIN_BATERIA", "PIN_PERFIL", "PIN_START", "PIN_CAL", "PIN_LED"]:
        izq.append((str(base.PIN[k]), nombre_u1(base.PIN[k])))
    izq.append(("GND", "GND"))
    der = []
    for k in ["PIN_PWMA", "PIN_AIN1", "PIN_AIN2", "PIN_STBY", "PIN_PWMB", "PIN_BIN1", "PIN_BIN2",
              "PIN_MUX_S0", "PIN_MUX_S1", "PIN_MUX_S2", "PIN_MUX_S3", "PIN_MUX_SIG1", "PIN_EMISORES", "PIN_MUX_SIG2"]:
        der.append((str(base.PIN[k]), nombre_u1(base.PIN[k])))
    return base.caja("ESP32_DEVKIT_38", "U", "ESP32 DevKit (WROOM-32)", izq, der, 20.32)


S_ESP = simbolo_esp32()
S_TB = base.caja("TB6612FNG_MODULO", "U", "TB6612FNG",
                 [("1", "VM"), ("2", "VCC"), ("4", "PWMA"), ("5", "AIN1"), ("6", "AIN2"), ("7", "STBY"), ("8", "PWMB"),
                  ("9", "BIN1"), ("10", "BIN2"), ("3", "GND")],
                 [("11", "AO1"), ("12", "AO2"), None, None, None, None, ("13", "BO1"), ("14", "BO2")])
S_MUX = base.caja("CD74HC4067_MODULO", "U", "CD74HC4067",
                  [("7", "VCC"), ("1", "S0"), ("2", "S1"), ("3", "S2"), ("4", "S3"), ("6", "SIG"), ("5", "E"), ("8", "GND")],
                  [(str(9 + i), f"I{i}") for i in range(16)])
S_QTR = base.caja("QTR_8A", "U", "QTR-8A", [(str(1 + i), f"OUT{i + 1}") for i in range(8)],
                  [("9", "VCC"), ("11", "EMIT_RTN"), None, None, None, None, None, ("10", "GND")])
def nmos_sot23():
    """El MOSFET con la numeracion del TO-92 tipo 2N7000: 1 = S, 2 = G, 3 = D (los pines no se mueven)."""
    import copy
    q = copy.deepcopy(base.S_NMOS)
    q.nombre = "NMOS_TO92"
    for pin in q.pines:
        pin["num"] = {"S": "1", "G": "2", "D": "3"}[pin["name"]]
    return q


S_NMOS2 = nmos_sot23()
HUELLAS_ESQ = {}      # ref -> "biblioteca:huella"; lo llena generar_kicad_pcb.py para que el esquema apunte a las huellas de la PCB
S_POT = base.caja("POT", "RV", "POT", [("1", "A"), ("2", "B")], [("3", "W")], 10.16)


# ------------------------------------------------------------------ documento con propiedades laterales
class Doc2(base.Doc):
    def colocar(self, sym, ref, valor, x, y):
        super().colocar(sym, ref, valor, x, y)
        inst = self.items[-1]
        if ref in HUELLAS_ESQ:
            for h in inst:
                if isinstance(h, list) and h[0] == "property" and h[1] == "Footprint":
                    h[2] = base.Q(HUELLAS_ESQ[ref])
        if getattr(sym, "off_ref", None):
            for h in inst:
                if isinstance(h, list) and h[0] == "property" and h[1] == "Reference":
                    h[3] = ["at", round(x + sym.off_ref[0], 4), round(y - sym.off_ref[1], 4), 0]
                    h[4] = base.efectos(justif=("left",))
                if isinstance(h, list) and h[0] == "property" and h[1] == "Value":
                    h[3] = ["at", round(x + sym.off_val[0], 4), round(y - sym.off_val[1], 4), 0]
                    h[4] = base.efectos(justif=("left",))
        self.textos_prop = getattr(self, "textos_prop", [])
        for h in inst:
            if isinstance(h, list) and h[0] == "property" and h[1] in ("Reference", "Value"):
                at = h[3]
                izq = len(h) > 4 and "justify" in str(h[4])
                n = len(str(h[2]))
                ancho = n * 1.05
                x0 = at[1] if izq else at[1] - ancho / 2
                self.textos_prop.append((x0, at[2] - 0.9, x0 + ancho, at[2] + 0.9))

    def junction(self, pt):
        self.items.append(["junction", ["at", pt[0], pt[1]], ["diameter", 0], ["color", 0, 0, 0, 0], ["uuid", self.uid("j")]])


def bbox(sym):
    xs, ys = [], []
    for p in sym.pines:
        xs += [p["x"]]
        ys += [p["y"]]
    for g in sym.graficos:
        if g[0] == "rectangle":
            xs += [g[1][1], g[2][1]]
            ys += [g[1][2], g[2][2]]
        elif g[0] == "polyline":
            for pt in g[1][1:]:
                xs.append(pt[1])
                ys.append(pt[2])
        elif g[0] == "circle":
            r = g[2][1]
            xs += [g[1][1] - r, g[1][1] + r]
            ys += [g[1][2] - r, g[1][2] + r]
    ys += [sym.top, -sym.top] if not getattr(sym, "off_ref", None) else []
    return min(xs), max(xs), min(ys), max(ys)


# ------------------------------------------------------------------ enrutador
def ci(v):
    return int(round(v / G))


def pt(c):
    return (round(c[0] * G, 4), round(c[1] * G, 4))


class Enrutador:
    GIRO = 6.0
    CRUCE = 22.0
    TEXTO = 14.0
    VECINO = 2.5

    def __init__(self, nx, ny):
        self.nx, self.ny = nx, ny
        self.bloq = set()
        self.nocruzar = set()
        self.suave = {}
        self.occ = {}                  # celda -> {red: {dirs}}
        self.aristas = {}              # red -> set de (a, b) con a < b
        self.halo = {}                 # celda -> set de redes vecinas

    def bloquear_rect(self, x0, y0, x1, y1):
        for ix in range(ci(x0), ci(x1) + 1):
            for iy in range(ci(y0), ci(y1) + 1):
                self.bloq.add((ix, iy))

    def suave_rect(self, x0, y0, x1, y1, c):
        for ix in range(ci(x0), ci(x1) + 1):
            for iy in range(ci(y0), ci(y1) + 1):
                self.suave[(ix, iy)] = self.suave.get((ix, iy), 0) + c

    def marcar_arista(self, red, a, b):
        if a > b:
            a, b = b, a
        if (a, b) in self.aristas.setdefault(red, set()):
            return
        self.aristas[red].add((a, b))
        d = DIRS.index((b[0] - a[0], b[1] - a[1]))
        self.occ.setdefault(a, {}).setdefault(red, set()).add(d)
        self.occ.setdefault(b, {}).setdefault(red, set()).add(OPUESTA[d])

    def celdas_red(self, red):
        return {c for c, v in self.occ.items() if red in v}

    def paso(self, red, nxt, nd, meta):
        if nxt[0] < 0 or nxt[1] < 0 or nxt[0] >= self.nx or nxt[1] >= self.ny:
            return None
        if nxt in self.bloq and nxt != meta:
            return None
        coste = 1.0 + self.suave.get(nxt, 0)
        otros = {n: ds for n, ds in self.occ.get(nxt, {}).items() if n != red}
        if otros:
            if len(otros) != 1 or nxt in self.nocruzar:
                return None
            ds = next(iter(otros.values()))
            if ds != {(nd + 1) % 4, (nd + 3) % 4}:
                return None
            coste += self.CRUCE
        vec = self.halo.get(nxt)
        if vec and (vec - {red}):
            coste += self.VECINO
        return coste

    def libre_giro(self, c, red):
        return not any(n != red for n in self.occ.get(c, {}))

    def componente(self, red, ini):
        adj = {}
        for a, b in self.aristas.get(red, ()):
            adj.setdefault(a, []).append(b)
            adj.setdefault(b, []).append(a)
        visto, pila = {ini}, [ini]
        while pila:
            c = pila.pop()
            for v in adj.get(c, ()):
                if v not in visto:
                    visto.add(v)
                    pila.append(v)
        return visto

    def ruta(self, red, meta, comp):
        fuentes = [c for c in comp if self.libre_giro(c, red)]
        h = lambda c: abs(c[0] - meta[0]) + abs(c[1] - meta[1])
        abierto, mejor, padre, n = [], {}, {}, 0
        for s in fuentes:
            mejor[(s, None)] = 0.0
            heapq.heappush(abierto, (h(s), 0.0, n, (s, None)))
            n += 1
        while abierto:
            _, g, _, est = heapq.heappop(abierto)
            if mejor.get(est, 1e18) < g - 1e-9:
                continue
            c, d = est
            if c == meta:
                camino = [c]
                while est in padre:
                    est = padre[est]
                    camino.append(est[0])
                return camino[::-1]
            for nd in range(4):
                if d is not None and nd == OPUESTA[d]:
                    continue
                giro = d is not None and nd != d
                if giro and not self.libre_giro(c, red):
                    continue
                nxt = (c[0] + DIRS[nd][0], c[1] + DIRS[nd][1])
                coste = self.paso(red, nxt, nd, meta)
                if coste is None:
                    continue
                ng = g + coste + (self.GIRO if giro else 0.0)
                e2 = (nxt, nd)
                if ng < mejor.get(e2, 1e18) - 1e-9:
                    mejor[e2] = ng
                    padre[e2] = est
                    n += 1
                    heapq.heappush(abierto, (ng + h(nxt), ng, n, e2))
        return None

    def anadir_camino(self, red, camino):
        for a, b in zip(camino, camino[1:]):
            self.marcar_arista(red, a, b)
        for c in camino:
            for dx, dy in DIRS:
                v = (c[0] + dx, c[1] + dy)
                self.halo.setdefault(v, set()).add(red)


# ------------------------------------------------------------------ construcción
def p2(x, y):
    return base.p(x, y)


def construir():
    d0 = base.construir()                  # solo para tomar la lista de conexiones (spec) y los pines sin conexión
    renombra = {("U1", f"GPIO{g}"): ("U1", nombre_u1(g)) for g in SENAL}
    spec = {red: [renombra.get(x, x) for x in pins] for red, pins in d0.spec.items()}
    nc = [renombra.get(x, x) for x in d0.nc]

    d = Doc2()
    # ---- colocación (mm). Las piezas se alinean para que los cables salgan cortos y rectos.
    d.colocar(base.S_BAT, "BT1", "LiPo 2S 7.4 V", *p2(30, 36))
    a = d.pos("BT1", "+")
    d.colocar_en_pin(base.S_FUSE, "F1", "Fusible reseteable", "1", (a[0] + 25.4, a[1]))
    b = d.pos("F1", "2")
    d.colocar_en_pin(base.S_SPST, "SW1", "Interruptor general", "1", (b[0] + 25.4, b[1]))
    c = d.pos("SW1", "2")
    d.colocar_en_pin(base.S_BUCK, "U2", "Buck 6 V (>= 2 A): motores", "IN+", (c[0] + 33.02, c[1]))
    d.colocar(base.S_BUCK, "U3", "Buck 5 V (>= 1 A): ESP32", *p2(152, 62))
    d.colocar(S_RV, "R1", "100k", *p2(118, 76))
    a = d.pos("R1", "2")
    d.colocar_en_pin(S_RV, "R2", "47k", "1", (a[0], a[1] + 7.62))

    d.colocar(S_ESP, "U1", "ESP32 DevKit 38 pines (WROOM-32)", *p2(190, 132))
    d.colocar(S_PUSH2, "SW2", "START", *p2(116, 118))
    d.colocar(S_PUSH2, "SW3", "CAL", *p2(116, 138))
    d.colocar(S_POT, "RV1", "Perilla de perfil", *p2(116, 160))

    d.colocar(S_TB, "U4", "TB6612FNG (modulo)", *p2(310, 70))
    a = d.pos("U4", "AO1")
    d.colocar_en_pin(base.S_MOTOR, "M1", "N20 6 V (rueda izq., canal A)", "1", (a[0] + 20.32, a[1]))
    a = d.pos("U4", "BO1")
    d.colocar_en_pin(base.S_MOTOR, "M2", "N20 6 V (rueda der., canal B)", "1", (a[0] + 20.32, a[1]))
    d.colocar(S_CPV, "C1", "100-470uF (VM)", *p2(256, 42))
    d.colocar(S_CV, "C2", "100nF (VCC)", *p2(284, 42))

    d.colocar(S_MUX, "U5", "CD74HC4067 (modulo)", *p2(278, 204))
    a = d.pos("U5", "I0")
    d.colocar_en_pin(S_QTR, "U6", "QTR-8A (1 + repuesto)", "OUT1", (a[0] + 25.4, a[1]))
    d.colocar(S_CV, "C3", "100nF (mux)", *p2(250, 172))
    d.colocar(S_CV, "C4", "100nF (sensor)", *p2(372, 170))
    d.colocar(base.S_R, "R3", "100", *p2(300, 246))
    d.colocar(S_RV, "R4", "100k", *p2(338, 232))
    d.colocar(S_NMOS2, "Q1", "MOSFET nivel logico", *p2(368, 236))

    # ---- obstáculos
    ancho_hoja, alto_hoja = 420.0, 297.0
    r = Enrutador(ci(ancho_hoja) + 1, ci(alto_hoja) + 1)
    for ix in range(r.nx):
        for iy in range(r.ny):
            if ix < ci(13) or ix > ci(408) or iy < ci(13) or iy > ci(284):
                r.bloq.add((ix, iy))
    r.bloquear_rect(296, 252, 420, 297)         # bloque de título de KiCad
    cuerpos = []
    for ref, i in d.inst.items():
        x0, x1, y0, y1 = bbox(i["sym"])
        caja_ = (round(i["x"] + x0, 4), round(i["y"] - y1, 4), round(i["x"] + x1, 4), round(i["y"] - y0, 4))
        for (rx0, ry0, rx1, ry1) in cuerpos:
            if caja_[0] < rx1 + 2.5 and caja_[2] > rx0 - 2.5 and caja_[1] < ry1 + 2.5 and caja_[3] > ry0 - 2.5:
                sys.exit(f"{ref} se encima con otra pieza")
        cuerpos.append(caja_)
        r.bloquear_rect(*caja_)
    for (x0, y0, x1, y1) in d.textos_prop:
        r.suave_rect(x0, y0, x1, y1, Enrutador.TEXTO)

    # ---- notas (también son obstáculo)
    notas1 = ("NOTAS DE DISENO (de docs/electronica.md y docs/plan.md)\n"
              "1. Todo lo que toca un pin del ESP32 trabaja a 3.3 V (sensor, mux, logica del TB6612, botones).\n"
              "2. Motores desde su propio buck de 6 V; ESP32 por VIN desde otro buck de 5 V.\n"
              "    Nunca alimentar los motores del regulador del ESP32.\n"
              "3. Una sola union de tierras (estrella) cerca de la bateria; cables de motor lejos de los sensores.\n"
              "4. Capacitor de 100-470 uF en VM del TB6612 y 100 nF en cada modulo.\n"
              "5. Fusible reseteable en serie con el positivo de la bateria.\n"
              "6. Sin WiFi ni Bluetooth (el reglamento los prohibe en competencia).\n"
              "7. Cargar la LiPo solo con cargador balanceado y bolsa o caja para LiPo.")
    notas2 = ("POR VERIFICAR (todavia no hay piezas reales; nada de esto esta aprobado por el equipo)\n"
              "- Pinout real del ESP32 DevKit: aqui el numero de pin es el GPIO, no la posicion fisica.\n"
              "- QTR-8A: orden de salidas, sentido del voltaje sobre negro (ALTO_ES_NEGRO) y si trae pin LEDON.\n"
              "  Q1 conmuta el retorno de los LED IR (EMIT_RTN). El QTR-8A no expone ese retorno:\n"
              "  si se usa su pin LEDON, GPIO13 iria directo a LEDON y se retiran Q1, R3 y R4\n"
              "  (revisar la logica en la ficha; con Q1 la logica quedaria invertida).\n"
              "- Consumo del sensor sobre el 3V3 de la placa y tiempo de lectura del mux a 3.3 V.\n"
              "- Nombres y orden de pines de los modulos reales (TB6612, CD74HC4067, bucks).\n"
              "- Perfil de 24 canales: 2.o CD74HC4067 en MUX_SIG2 (GPIO35) con S0-S3 compartidos.\n"
              "- Los simbolos son funcionales y sin huella (footprint) todavia.")
    d.texto(15, 196, notas1, 1.1)
    r.bloquear_rect(14, 196, 118, 226)
    d.texto(15, 232, notas2, 1.1)
    r.bloquear_rect(14, 232, 112, 262)
    d.texto(14, 20, "VERSION CABLEADA: cada conexion es un cable entre pines (ver seguidor.kicad_sch para la version con etiquetas).", 1.4)
    r.bloquear_rect(14, 19, 190, 23)

    # ---- cables cortos de salida de cada pin (2 celdas hacia afuera)
    salida_pin = {}
    for ref, i in d.inst.items():
        for p in i["sym"].pines:
            ang = p["ang"]
            nd = {0: 2, 180: 0, 270: 3, 90: 1}[ang]
            a = d.pos(ref, p["name"])
            ca = (ci(a[0]), ci(a[1]))
            salida_pin[(ref, p["name"])] = (ca, nd)
    for (ref, pin), (ca, nd) in salida_pin.items():
        if (ref, pin) in set(nc):
            continue
        c1 = (ca[0] + DIRS[nd][0], ca[1] + DIRS[nd][1])
        c2 = (ca[0] + 2 * DIRS[nd][0], ca[1] + 2 * DIRS[nd][1])
        for c_, red_ in ((ca, ("pin", ref, pin)),):
            pass
    # las redes reales se asignan abajo; aquí solo se reservan las celdas de la salida
    red_de_pin = {}
    for red, pins in spec.items():
        for x in pins:
            red_de_pin[x] = red
    for (ref, pin), (ca, nd) in salida_pin.items():
        if (ref, pin) in set(nc):
            continue
        red = red_de_pin[(ref, pin)]
        c1 = (ca[0] + DIRS[nd][0], ca[1] + DIRS[nd][1])
        c2 = (ca[0] + 2 * DIRS[nd][0], ca[1] + 2 * DIRS[nd][1])
        r.marcar_arista(red, ca, c1)
        r.marcar_arista(red, c1, c2)
        r.nocruzar.update([ca, c1, c2])
    for pin in nc:
        r.nocruzar.add(salida_pin[pin][0])

    # ---- enrutado: primero las redes cortas, al final las de alimentación
    def largo(red):
        cs = [salida_pin[x][0] for x in spec[red]]
        return sum(abs(c[0] - cs[0][0]) + abs(c[1] - cs[0][1]) for c in cs)

    grandes = {"GND", "+3V3"}
    orden = sorted([x for x in spec if x not in grandes], key=lambda x: (len(spec[x]), largo(x))) + ["+3V3", "GND"]
    fallos = []
    for red in orden:
        pins = spec[red]
        pendientes = [x for x in pins]
        # se conecta cada pin al árbol existente, empezando por el más cercano al primero
        base_pin = pendientes.pop(0)
        while pendientes:
            cs0 = salida_pin[base_pin][0]
            pendientes.sort(key=lambda x: abs(salida_pin[x][0][0] - cs0[0]) + abs(salida_pin[x][0][1] - cs0[1]))
            destino = pendientes.pop(0)
            ca, nd = salida_pin[destino]
            meta = (ca[0] + 2 * DIRS[nd][0], ca[1] + 2 * DIRS[nd][1])
            if meta in r.celdas_red(red) and any(meta == c for c in r.celdas_red(red)) and \
               any(salida_pin[x][0] != ca and meta in r.celdas_red(red) for x in []):
                pass
            comp = r.componente(red, salida_pin[base_pin][0])
            if meta in comp:
                continue
            camino = r.ruta(red, meta, comp)
            if camino is None:
                fallos.append((red, destino))
                continue
            r.anadir_camino(red, camino)
    if fallos:
        sys.exit(f"no se pudo enrutar: {fallos}")

    # ---- a cables y uniones
    for red, aristas in r.aristas.items():
        grado = {}
        for a_, b_ in aristas:
            grado.setdefault(a_, []).append(b_)
            grado.setdefault(b_, []).append(a_)
        vistos = set()
        for a_, b_ in sorted(aristas):
            if (a_, b_) in vistos:
                continue
            vistos.add((a_, b_))
            dx, dy = b_[0] - a_[0], b_[1] - a_[1]
            ini, fin = a_, b_
            # extender hacia atrás y hacia adelante mientras el nodo sea de paso recto (grado 2, sin unión)
            while True:
                nx_ = (fin[0] + dx, fin[1] + dy)
                if len(grado[fin]) == 2 and nx_ in grado[fin] and (min(fin, nx_), max(fin, nx_)) not in vistos:
                    vistos.add((min(fin, nx_), max(fin, nx_)))
                    fin = nx_
                else:
                    break
            while True:
                pv = (ini[0] - dx, ini[1] - dy)
                if len(grado[ini]) == 2 and pv in grado[ini] and (min(ini, pv), max(ini, pv)) not in vistos:
                    vistos.add((min(ini, pv), max(ini, pv)))
                    ini = pv
                else:
                    break
            d.cable(pt(ini), pt(fin))
        for c_, vec in grado.items():
            if len(vec) >= 3:
                d.junction(pt(c_))
    for pin in nc:
        d.sin_conexion(*pin)
    d.spec, d.nc = spec, nc
    # una etiqueta por riel (una sola por nombre: no unen nada, solo identifican)
    for red in ["GND", "+3V3", "+5V", "+6V", "VBAT"]:
        c_ = min(r.celdas_red(red), key=lambda c: (c[1], c[0]))
        d.etiqueta(red, pt(c_), 0)
    return d, r


def escribir_y_verificar(d):
    base.SALIDA = SALIDA
    base.PROYECTO = NOMBRE
    base.ARCHIVO = NOMBRE
    base.TITULO = "Seguidor de linea - esquema CABLEADO"
    base.UUID_RAIZ = str(uuid.uuid5(base.NS, "raiz-cableado"))
    base.escribir(d)
    arbol = base.leer_sexp((SALIDA / f"{NOMBRE}.kicad_sch").read_text(encoding="utf-8"))
    libs = {}
    for s in base.hijos(base.hijo(arbol, "lib_symbols"), "symbol"):
        pines = {}
        for sub in base.hijos(s, "symbol"):
            for pn in base.hijos(sub, "pin"):
                at = base.hijo(pn, "at")
                pines[base.hijo(pn, "number")[1]] = (float(at[1]), float(at[2]), base.hijo(pn, "name")[1])
        libs[s[1]] = pines
    clave = lambda x, y: (round(float(x), 2), round(float(y), 2))
    pin_en, refs = {}, []
    for s in base.hijos(arbol, "symbol"):
        ref = [pr[2] for pr in base.hijos(s, "property") if pr[1] == "Reference"][0]
        refs.append(ref)
        at = base.hijo(s, "at")
        for _, (px, py, nombre) in libs[base.hijo(s, "lib_id")[1]].items():
            pin_en.setdefault(clave(float(at[1]) + px, float(at[2]) - py), []).append((ref, nombre))
    padre = {}

    def raiz(k):
        padre.setdefault(k, k)
        while padre[k] != k:
            padre[k] = padre[padre[k]]
            k = padre[k]
        return k

    for w in base.hijos(arbol, "wire"):
        xy = base.hijos(base.hijo(w, "pts"), "xy")
        padre[raiz(clave(xy[0][1], xy[0][2]))] = raiz(clave(xy[1][1], xy[1][2]))
    grupos = {}
    for k, lista in pin_en.items():
        grupos.setdefault(raiz(k), set()).update(lista)
    ncs = {clave(base.hijo(n, "at")[1], base.hijo(n, "at")[2]) for n in base.hijos(arbol, "no_connect")}
    solos = set()
    for k, lista in pin_en.items():
        if k in ncs:
            assert len(grupos[raiz(k)]) == 1, f"pin sin conexion unido a algo: {lista}"
            solos.update(lista)
    reales = {frozenset(g) for g in grupos.values() if not g <= solos}
    esperado = {frozenset(v) for v in d.spec.values()}
    if reales != esperado:
        sys.exit("CONECTIVIDAD CON SOLO CABLES DISTINTA\n sobra: %s\n falta: %s" %
                 ([sorted(g) for g in reales - esperado][:3], [sorted(g) for g in esperado - reales][:3]))
    assert solos == set(d.nc)
    return len(refs), len(reales), len(solos), len(base.hijos(arbol, "wire")), len(base.hijos(arbol, "junction"))


def main():
    d, _ = construir()
    piezas, redes, nc, cables, uniones = escribir_y_verificar(d)
    print(f"ok: {piezas} piezas, {redes} redes (solo cables), {nc} pines sin conexion, "
          f"{cables} cables, {uniones} uniones -> {SALIDA.relative_to(base.RAIZ)}")


if __name__ == "__main__":
    main()
