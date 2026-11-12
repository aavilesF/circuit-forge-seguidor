#!/usr/bin/env python3
"""Verificación mecánica del CAD (resultado de hardware/mechanical/cad/generar_cad.py) contra el reglamento y contra el
modelo del simulador (config/robot_maestro.yaml, sección componentes):
  1. sin interferencias entre piezas ni con la PCBA;
  2. huella dentro de la caja del reglamento (R01: 200 × 100 mm; diseño: ≤ 192 × 92 mm);
  3. altura: partes rígidas a ≥ 2 mm del piso (R11), salvo llantas, bola y la carcasa de la bola;
  4. masa total ≤ 450 g (límite de diseño; R03: 500 g);
  5. masa y CG del CAD = los del simulador (±3 % y ±2 mm): si no, el simulador estaría optimizando otro robot;
  6. botones, conectores y LEDs accesibles (no quedan bajo la batería ni bajo los soportes).
Escribe hardware/mechanical/VERIFICACION_MECANICA.md. Código 1 si algo falla.
Con --actualizar-yaml reescribe masa y posición de cada categoría de `componentes` con los valores del CAD
(conserva comentarios y orígenes) y termina.
Uso: python3 hardware/mechanical/verificar_mecanica.py [--actualizar-yaml]"""
from __future__ import annotations

import json
import os
import re
import sys

MEC = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(MEC, "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "sim"))
import config as CF  # noqa: E402

YAML = os.path.join(RAIZ, "config", "robot_maestro.yaml")
# Exentos: lo que toca el piso a propósito (llantas, bola) y la carcasa de la bola, cuyo fondo queda a 1.6 mm del piso
# alrededor del punto de apoyo; los tornillos de la rueda loca van metidos en su caja, por encima del fondo de la carcasa.
EXENTOS_ALTURA = ("APROX_llanta", "APROX_bola", "rueda_loca_carcasa", "tornillo_M2x8_rl")


def actualizar_yaml(cats):
    txt = open(YAML, encoding="utf-8").read()
    for cat, v in cats.items():
        patron = re.compile(r"^(  " + re.escape(cat) + r":\s*\{)masa: [0-9.eE+-]+, x: [0-9.eE+-]+, y: [0-9.eE+-]+, z: [0-9.eE+-]+",
                            re.M)
        if not patron.search(txt):
            raise SystemExit(f"no encontré la categoría {cat} en componentes")
        txt = patron.sub(lambda mt: f"{mt.group(1)}masa: {v['masa_kg']:.4f}, x: {v['x_m']:.4f}, y: {v['y_abs_m']:.4f}, "
                                    f"z: {v['z_m']:.4f}", txt)
    open(YAML, "w", encoding="utf-8").write(txt)
    print("componentes del YAML actualizados con el CAD:", ", ".join(cats))


def main():
    rep = json.load(open(os.path.join(MEC, "verificacion_mecanica.json"), encoding="utf-8"))
    if "--actualizar-yaml" in sys.argv:
        actualizar_yaml(rep["masa"]["categorias_yaml"])
        return 0
    cfg = CF.cargar()
    arq = cfg["arquitectura"]
    m_sim, x_sim, z_sim, iz_sim = CF.masa_y_cg(cfg, False, arq["motor"], arq["barra"])
    falla = []
    L = ["# Verificación mecánica del CAD (generado por hardware/mechanical/verificar_mecanica.py)", "",
         "Validación **CAD**: geometría, masas de ficha y volúmenes. No sustituye pesar y medir el robot armado (M2, M5).", ""]
    # 1. interferencias
    malas = [i for i in rep["interferencias"] if not i["ok"]]
    L += [f"## 1. Interferencias: {len(rep['interferencias'])} pares revisados, {len(malas)} con interferencia", ""]
    L += ["| A | B | Volumen común (mm³) | OK |", "|---|---|---|---|"]
    L += [f"| {i['a']} | {i['b']} | {i['volumen_mm3']} | {'sí' if i['ok'] else '**NO**'} |" for i in rep["interferencias"]]
    if malas:
        falla.append(f"{len(malas)} interferencias")
    # 2. caja
    c = rep["caja"]
    ok_caja = c["largo_x"] <= 192.0 and c["ancho_y"] <= 92.0 + 1e-6
    L += ["", f"## 2. Huella: {c['largo_x']:.2f} × {c['ancho_y']:.2f} mm, alto {c['alto_z']:.2f} mm "
              f"(reglamento R01: 200 × 100 mm; límite de diseño 192 × 92 mm) → {'cumple' if ok_caja else '**NO CUMPLE**'}"]
    if not ok_caja:
        falla.append("huella fuera del límite de diseño")
    # 3. alturas
    bajas = [a for a in rep["alturas"]["piezas"] if a["z_min_mm"] < 2.0 and not a["pieza"].startswith(EXENTOS_ALTURA)]
    zp = rep["alturas"]["z_min_pcba_mm"]
    L += ["", f"## 3. Altura sobre el piso (R11): punto más bajo de la PCBA {zp:.2f} mm (caras de los sensores); "
              f"piezas rígidas bajo 2 mm (sin contar llantas, bola y carcasa de la bola): {len(bajas)}"]
    carc = [a for a in rep["alturas"]["piezas"] if a["pieza"] == "rueda_loca_carcasa"]
    if carc:
        L.append(f"- Carcasa de la rueda loca: {carc[0]['z_min_mm']:.2f} mm sobre el piso, alrededor del punto de apoyo de la bola (≤ 8 mm del contacto)")
    trl = [a for a in rep["alturas"]["piezas"] if a["pieza"].startswith("tornillo_M2x8_rl")]
    if trl and carc:
        ok_rl = all(a["z_min_mm"] >= carc[0]["z_min_mm"] for a in trl)
        L.append(f"- Cabezas de los tornillos de la rueda loca: {min(a['z_min_mm'] for a in trl):.2f} mm, dentro de la caja de la carcasa "
                 f"({'no sobresalen' if ok_rl else '**SOBRESALEN**'} del fondo)")
        if not ok_rl:
            falla.append("tornillos de la rueda loca bajo la carcasa")
    if bajas or zp < 2.0:
        falla.append("partes a menos de 2 mm del piso")
    # 4-5. masa y CG
    mm = rep["masa"]
    m_cad = mm["total_g"]; x_cad, y_cad, z_cad = mm["cg_mm"]
    dm = (m_cad - m_sim * 1000) / (m_sim * 1000) * 100
    dx = x_cad - x_sim * 1000
    L += ["", "## 4-5. Masa y centro de gravedad", "",
          "| | CAD | Simulador (YAML) | Diferencia | Criterio |", "|---|---|---|---|---|",
          f"| Masa | {m_cad:.1f} g | {m_sim * 1000:.1f} g | {dm:+.1f} % | ±3 %; ≤ 450 g |",
          f"| x del CG (adelante del eje) | {x_cad:.1f} mm | {x_sim * 1000:.1f} mm | {dx:+.1f} mm | ±2 mm |",
          f"| y del CG | {y_cad:.2f} mm | 0 | | simétrico |",
          f"| z del CG | {z_cad:.1f} mm | {z_sim * 1000:.1f} mm | {z_cad - z_sim * 1000:+.1f} mm | informativo |", "",
          "Desglose del CAD:", "", "| Pieza | Masa (g) | CG (mm) |", "|---|---|---|"]
    L += [f"| {p['nombre']} | {p['masa_g']} | {p['cg_mm']} |" for p in mm["partes"]]
    if abs(dm) > 3.0 or abs(dx) > 2.0:
        falla.append("masa/CG del CAD distintos del simulador (correr --actualizar-yaml y revalidar la simulación)")
    if m_cad > 450:
        falla.append("masa > 450 g")
    # 6. accesibilidad
    tap = [a for a in rep["accesibilidad"] if not a["libre"]]
    L += ["", f"## 6. Accesibilidad: {len(rep['accesibilidad'])} elementos, {len(tap)} tapados", "",
          "| Ref | Uso | Posición (x, y) mm | Cara | Libre |", "|---|---|---|---|---|"]
    L += [f"| {a['ref']} | {a['uso']} | ({a['x_mm']}, {a['y_mm']}) | {a['cara']} | "
          f"{'sí' if a['libre'] else '**NO** (' + ', '.join(a['tapado_por']) + ')'} |" for a in rep["accesibilidad"]]
    if tap:
        falla.append("elementos tapados")
    L += ["", "RESULTADO: " + ("FALLA: " + "; ".join(falla) if falla else "CUMPLE (validación CAD)")]
    open(os.path.join(MEC, "VERIFICACION_MECANICA.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"masa CAD {m_cad:.1f} g vs sim {m_sim * 1000:.1f} g ({dm:+.1f} %); x_CG {x_cad:.1f} vs {x_sim * 1000:.1f} mm ({dx:+.1f}); "
          f"huella {c['largo_x']:.1f} × {c['ancho_y']:.1f} mm; interferencias {len(malas)}; tapados {len(tap)}")
    print("RESULTADO:", "FALLA: " + "; ".join(falla) if falla else "CUMPLE (validación CAD)")
    return 1 if falla else 0


if __name__ == "__main__":
    sys.exit(main())
