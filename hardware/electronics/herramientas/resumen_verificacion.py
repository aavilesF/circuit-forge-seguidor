#!/usr/bin/env python3
"""Resume los informes de ERC y DRC de KiCad 9 (verificacion/erc.json, drc.json) en verificacion/RESUMEN.md.
Falla (código 1) si hay errores, o avisos que no estén en la lista de excepciones justificadas de abajo."""
import json
import os
import sys
from collections import Counter

V = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "verificacion")

# Avisos aceptados, con su justificación técnica (tipo, texto que debe aparecer en la descripción o en un ítem)
EXCEPCIONES = [
    ("pin_to_pin", "AISEN", "DRV8833: AISEN/BISEN (bidireccionales) a GND, como indica la hoja de datos cuando no se usa "
                            "la regulación de corriente; KiCad avisa porque GND tiene una bandera PWR_FLAG (salida de potencia)."),
    ("pin_to_pin", "BISEN", "Ídem para el puente B."),
]


def cargar(nombre):
    ruta = os.path.join(V, nombre)
    return json.load(open(ruta)) if os.path.exists(ruta) else None


def justificado(v):
    texto = json.dumps(v, ensure_ascii=False)
    for tipo, clave, motivo in EXCEPCIONES:
        if v.get("type") == tipo and clave in texto:
            return motivo
    return None


def main():
    lineas = ["# Resumen de verificaciones de KiCad 9 (generado)", ""]
    falla = False
    erc = cargar("erc.json")
    if erc is None:
        print("falta erc.json"); return 1
    viol = [v for s in erc.get("sheets", []) for v in s.get("violations", [])]
    c = Counter((v["severity"], v["type"]) for v in viol)
    lineas.append(f"## ERC — {len(viol)} hallazgos")
    for (sev, tipo), n in sorted(c.items()):
        lineas.append(f"- {sev} `{tipo}`: {n}")
    for v in viol:
        j = justificado(v)
        if v["severity"] == "error" or not j:
            falla = True
            lineas.append(f"  - **SIN JUSTIFICAR** {v['severity']} {v['type']}: {v['description']}")
        else:
            lineas.append(f"  - aceptado: {v['type']} — {j}")
    drc = cargar("drc.json")
    if drc is None:
        print("falta drc.json"); return 1
    lineas.append("")
    for clave, titulo in (("violations", "Violaciones de reglas"), ("unconnected_items", "Elementos sin conectar"),
                          ("schematic_parity", "Paridad esquemático-PCB")):
        items = drc.get(clave, [])
        c = Counter((v["severity"], v["type"]) for v in items)
        lineas.append(f"## DRC — {titulo}: {len(items)}")
        for (sev, tipo), n in sorted(c.items()):
            lineas.append(f"- {sev} `{tipo}`: {n}")
        for v in items:
            j = justificado(v)
            if j:
                lineas.append(f"  - aceptado: {v['type']} — {j}")
            else:
                falla = True
                desc = v["description"] + " | " + "; ".join(i.get("description", "") for i in v.get("items", []))
                lineas.append(f"  - **{v['severity']}** {v['type']}: {desc}")
    lineas.append("")
    lineas.append("RESULTADO: " + ("FALLA" if falla else "SIN ERRORES (solo avisos justificados)"))
    open(os.path.join(V, "RESUMEN.md"), "w", encoding="utf-8").write("\n".join(lineas) + "\n")
    print("\n".join(l for l in lineas if not l.startswith("  - aceptado")))
    return 1 if falla else 0


if __name__ == "__main__":
    sys.exit(main())
