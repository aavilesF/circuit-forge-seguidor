#!/usr/bin/env python3
"""V2 · Quita del DSN (Specctra) las redes que se conectan con planos (GND) para que Freerouting no las enrute.
Freerouting 2.1 no respeta su opción -inc (ignorar clases) al correr sin interfaz; esto hace lo mismo:
  - borra la red de (network (net ...)) y de las listas de las clases;
  - deja las vías y pistas de abanico ya puestas como cableado fijo sin red: Freerouting las respeta como obstáculos.
Después de importar el SES, los pads y las vías conservan su red en KiCad (la red sale de la placa, no del SES) y los
planos de las dos caras las conectan. Uso: python3 dsn_sin_red.py placa.dsn GND [OTRA ...]"""
import re
import sys


def quitar(texto, red):
    # bloque "(net RED (pins ...))" de la sección network
    i = texto.find(f"\n    (net {red}\n")
    if i < 0:
        i = texto.find(f'\n    (net "{red}"\n')
    if i >= 0:
        prof, j = 0, i + 1
        while True:
            c = texto[j]
            if c == "(":
                prof += 1
            elif c == ")":
                prof -= 1
                if prof == 0:
                    break
            j += 1
        texto = texto[:i] + texto[j + 1:]
    # miembros de las clases
    texto = re.sub(rf"(\(class [^\n]*?) {re.escape(red)}(?=[\s)])", r"\1", texto)
    # cableado fijo: sin red
    texto = texto.replace(f"(net {red})", "")
    # clases que quedaron sin redes
    while True:
        m = re.search(r"\n\s*\(class \S+\s*\n\s*\(circuit", texto)
        if not m:
            break
        i, prof, j = m.start(), 0, m.start() + 1
        while True:
            c = texto[j]
            if c == "(":
                prof += 1
            elif c == ")":
                prof -= 1
                if prof == 0:
                    break
            j += 1
        texto = texto[:i] + texto[j + 1:]
    return texto


if __name__ == "__main__":
    ruta = sys.argv[1]
    t = open(ruta, encoding="utf-8").read()
    for r in sys.argv[2:]:
        t = quitar(t, r)
    # Freerouting avisa con una ventana (y se detiene sin interfaz) por caracteres fuera de Latin-1: solo aparecen en
    # los valores de las piezas (p. ej. "0 Ω"), nunca en los nombres de red, así que se pueden reemplazar.
    t = t.replace("Ω", "ohm").replace("µ", "u").replace("·", ".").replace("×", "x")
    open(ruta, "w", encoding="utf-8").write(t)
    print("DSN sin las redes:", " ".join(sys.argv[2:]))
