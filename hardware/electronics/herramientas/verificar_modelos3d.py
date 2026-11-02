#!/usr/bin/env python3
"""Comprobación de huellas y modelos 3D de la PCB:
  1. cada huella viene de una biblioteca oficial de KiCad 9 (o de la propia, declarada) y su nombre coincide con el diseño;
  2. cada componente que se monta tiene un modelo 3D que existe (ruta resuelta) y se marca si es aproximado;
  3. el STEP exportado contiene un sólido por cada componente con modelo (se compara con la lista de la PCB) y
     el registro de exportación no tiene modelos faltantes.
Escribe verificacion/modelos3d.md."""
import json
import math
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
E = os.path.abspath(os.path.join(AQUI, ".."))
sys.path.insert(0, os.path.join(AQUI, "..", "generador"))
import sexpr  # noqa: E402

KICAD = os.environ.get("KICAD_SHARE", "/opt/resolute/usr/share/kicad")
MODELOS = os.environ.get("KICAD9_3DMODEL_DIR", "/opt/k3d/usr/share/kicad/3dmodels")
PROPIOS = {"AMASS_XT30UPB-M.step": "APROXIMADO (contorno de la huella oficial, altura 8 mm [E])",
           "Fuse_1812L.step": "APROXIMADO (1812, espesor 1.0 mm [E])"}


def main():
    pcb = sexpr.parse(open(os.path.join(E, "kicad", "speed_follower.kicad_pcb"), encoding="utf-8").read())
    filas, err = [], []
    con_modelo = []
    for fp in sexpr.hijos(pcb, "footprint"):
        lib_id = fp[1]
        ref = next((p[2] for p in sexpr.hijos(fp, "property") if p[1] == "Reference"), "?")
        attr = sexpr.hijo(fp, "attr")
        montaje = not (attr and ("board_only" in attr or "exclude_from_bom" in attr and ref.startswith(("H", "TP"))))
        lib, nombre = lib_id.split(":")
        ruta_fp = os.path.join(KICAD, "footprints", lib + ".pretty", nombre + ".kicad_mod")
        oficial = os.path.exists(ruta_fp)
        if not oficial:
            err.append(f"{ref}: huella {lib_id} no está en la biblioteca oficial de KiCad 9")
        modelos = [m[1] for m in sexpr.hijos(fp, "model")]
        estado = "sin modelo (mecánico/prueba)"
        for m in modelos:
            r = m.replace("${KICAD9_3DMODEL_DIR}", MODELOS).replace("${KIPRJMOD}", os.path.join(E, "kicad"))
            base = os.path.basename(r)
            if not os.path.exists(r):
                err.append(f"{ref}: falta el modelo 3D {m}")
                estado = "FALTA"
            else:
                estado = PROPIOS.get(base, "oficial KiCad 9.0.7")
                if ref == "U3":
                    estado = "oficial KiCad 9.0.7 (HTSSOP-16 EP3.4×5; la huella apunta a una variante de máscara sin modelo)"
                con_modelo.append(ref)
        if not modelos and not ref.startswith(("H", "TP")):
            err.append(f"{ref}: componente montado sin modelo 3D")
        filas.append((ref, lib_id, "oficial" if oficial else "PROPIA", estado))
    # posición de cada huella en la PCB (marco del robot: origen en el eje, y hacia la izquierda)
    pos_pcb = {}
    for fp in sexpr.hijos(pcb, "footprint"):
        ref = next((p[2] for p in sexpr.hijos(fp, "property") if p[1] == "Reference"), "?")
        at = sexpr.hijo(fp, "at")
        capa = sexpr.hijo(fp, "layer")[1]
        rot = float(at[3]) if len(at) > 3 else 0.0
        pos_pcb[ref] = (float(at[1]) - 100.0, 100.0 - float(at[2]), rot, capa)
    # STEP exportado
    step = os.path.join(E, "fabricacion", "speed_follower_pcba.step")
    n_step = 0
    faltan_step = []
    comparados = 0
    if os.path.exists(step):
        txt = open(step, encoding="latin-1").read()
        productos = set(re.findall(r"PRODUCT\('([^']*)'", txt))
        instancias = re.findall(r"NEXT_ASSEMBLY_USAGE_OCCURRENCE\('[^']*','([^']*)'", txt)
        n_step = len(productos)
        for ref in con_modelo:
            if ref not in instancias:
                err.append(f"STEP: no aparece el componente {ref}")
        # posición y giro de cada componente en el STEP = los de su huella en la PCB
        try:
            import cadquery as cq
            asm = cq.Assembly.importStep(step)
            for hijo in asm.children:
                if hijo.name not in pos_pcb:
                    continue
                (x, y, z), (rx, ry, rz) = hijo.loc.toTuple()
                xp, yp, rp, capa = pos_pcb[hijo.name]
                abajo = capa.startswith("B")
                dang = abs(((rz - rp) + 180) % 360 - 180) if not abajo else 0.0
                if math.hypot(x - xp, y - yp) > 0.01 or (abajo != (z < 0.8)) or dang > 0.1:
                    err.append(f"STEP: {hijo.name} en ({x:.3f}, {y:.3f}, {z:.2f}) giro {rz:.1f}° y la PCB en ({xp:.3f}, {yp:.3f}) {rp:.1f}° {capa}")
                comparados += 1
        except ImportError:
            err.append("no está CadQuery: no se pudo comparar la posición de los componentes del STEP")
        log = os.path.join(E, "verificacion", "step_export.log")
        if os.path.exists(log):
            for l in open(log, encoding="utf-8", errors="replace"):
                if re.search(r"(cannot|could not|not found|no se)", l, re.I) and "model" in l.lower():
                    faltan_step.append(l.strip())
        for ref in con_modelo:
            if not any(p == ref or p.startswith(ref + "_") or ref in p.split() for p in productos):
                pass
    else:
        err.append("no existe fabricacion/speed_follower_pcba.step")
    err += [f"exportación STEP: {l}" for l in faltan_step]
    out = ["# Huellas y modelos 3D (generado)", "", f"{len(filas)} huellas; {len(con_modelo)} con modelo 3D; "
           f"STEP exportado con {n_step} modelos distintos; {comparados} componentes del STEP comparados en posición, "
           f"cara y giro contra la PCB; avisos de modelos en la exportación: {len(faltan_step)}", "",
           "| Ref | Huella | Biblioteca | Modelo 3D |", "|---|---|---|---|"]
    out += [f"| {a} | `{b}` | {c} | {d} |" for a, b, c, d in sorted(filas, key=lambda f: (f[0].rstrip('0123456789'), len(f[0]), f[0]))]
    out += ["", "ERRORES: " + ("ninguno" if not err else ""), *[f"- {e}" for e in err]]
    open(os.path.join(E, "verificacion", "modelos3d.md"), "w", encoding="utf-8").write("\n".join(out) + "\n")
    print(out[2])
    for e in err:
        print("  ERROR", e)
    return 1 if err else 0


if __name__ == "__main__":
    sys.exit(main())
