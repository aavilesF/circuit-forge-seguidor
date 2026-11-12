"""Lector/escritor mínimo de expresiones S de KiCad (sin dependencias)."""
import re

_TOK = re.compile(r'\s*(?:(\()|(\))|("(?:[^"\\]|\\.)*")|([^\s()"]+))', re.S)


class Sym(str):
    """Átomo sin comillas (palabra clave o número)."""


def parse(texto):
    pila, actual = [], []
    pos, n = 0, len(texto)
    while pos < n:
        m = _TOK.match(texto, pos)
        if not m:
            if texto[pos:].strip() == "":
                break
            raise ValueError("token inválido en %d" % pos)
        pos = m.end()
        if m.group(1):
            pila.append(actual)
            actual = []
        elif m.group(2):
            hecho = actual
            actual = pila.pop()
            actual.append(hecho)
        elif m.group(3) is not None:
            actual.append(m.group(3)[1:-1].replace('\\"', '"').replace("\\\\", "\\"))
        else:
            actual.append(Sym(m.group(4)))
    return actual[0] if len(actual) == 1 else actual


def hijos(nodo, clave):
    return [h for h in nodo if isinstance(h, list) and h and h[0] == clave]


def hijo(nodo, clave):
    for h in nodo:
        if isinstance(h, list) and h and h[0] == clave:
            return h
    return None


def _fmt_atomo(a):
    if isinstance(a, Sym):
        return str(a)
    if isinstance(a, bool):
        return "yes" if a else "no"
    if isinstance(a, int):
        return str(a)
    if isinstance(a, float):
        t = ("%.6f" % a).rstrip("0").rstrip(".")
        return "0" if t in ("-0", "") else t
    s = str(a).replace("\\", "\\\\").replace('"', '\\"')
    return '"%s"' % s


def dump(nodo, nivel=0):
    """Serializa con sangría de tabuladores al estilo KiCad."""
    if not isinstance(nodo, list):
        return _fmt_atomo(nodo)
    if all(not isinstance(h, list) for h in nodo):
        return "(" + " ".join(_fmt_atomo(h) for h in nodo) + ")"
    cab = []
    i = 0
    while i < len(nodo) and not isinstance(nodo[i], list):
        cab.append(_fmt_atomo(nodo[i]))
        i += 1
    s = "(" + " ".join(cab)
    for h in nodo[i:]:
        if isinstance(h, list):
            s += "\n" + "\t" * (nivel + 1) + dump(h, nivel + 1)
        else:
            s += " " + _fmt_atomo(h)
    s += "\n" + "\t" * nivel + ")"
    return s
