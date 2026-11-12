#!/usr/bin/env python3
"""Genera la lista de compra definitiva (docs/BOM_FINAL.csv), la BOM de ensamblaje de la PCB
(hardware/electronics/fabricacion/bom_ensamblaje.csv) y la masa de los componentes de la PCBA
(hardware/electronics/verificacion/masa_componentes.json).

Las partes de la PCB salen de hardware/electronics/generador/diseno.py (las mismas del esquemático y la PCB);
las mecánicas y de cableado, del catálogo de abajo. Cada fila indica cómo se verificó el número de parte.
Uso: python3 herramientas/generar_bom.py [--verificar]"""
from __future__ import annotations

import csv
import io
import json
import os
import sys
from collections import OrderedDict

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(RAIZ, "hardware", "electronics", "generador"))
import diseno as D  # noqa: E402

_CONT = D.G.contorno_pcb()[0]                 # contorno real de la PCB (mm, marco del robot)
_PCB_L = max(p[0] for p in _CONT) - min(p[0] for p in _CONT)
_PCB_W = max(p[1] for p in _CONT) - min(p[1] for p in _CONT)
_PCB_M = round((D.G.area_pcb_mm2() - 3.141592653589793 * 3.2 ** 2) / 100.0 * 0.39, 1)   # [E] 0.39 g/cm², 4 capas 1.6 mm

# MPN -> (categoría, tensión, corriente, dimensiones, masa unitaria g [E salvo indicación], encapsulado, función,
#         observaciones de montaje, verificación)
CAT = {
    "STM32G431CBT6": ("A", "1.71-3.6 V", "≈ 30 mA a 170 MHz", "7 × 7 × 1.4 mm", 0.20, "LQFP-48", "Microcontrolador (control, ADC, PWM, encoders)", "Pin 1 marcado en la serigrafía; soldar con flux, revisar puentes entre pines", "ficha y pines: st.com; funciones alternas: STM32_open_pin_data (ST)"),
    "DRV8833PWPR": ("A", "VM 2.7-10.8 V", "1.5 A RMS / 2 A pico por canal", "5.0 × 4.4 × 1.2 mm", 0.06, "HTSSOP-16 PowerPAD", "Puente H doble de los motores", "La almohadilla térmica DEBE soldarse (vías térmicas en la huella)", "tabla de pines: ti.com (SLVSAR1E)"),
    "TPS563200DDCR": ("A", "VIN 4.5-17 V", "3 A", "2.9 × 1.6 × 1.1 mm", 0.02, "SOT-23-6", "Reductor 3.3 V", "R6/R7 fijan 3.30 V (VFB 0.765 V)", "pines y tabla de componentes: hoja de datos TI (chipdip.ru DOC003725965)"),
    "AO3401A": ("A", "VDS −30 V, VGS ±12 V", "−4 A", "2.9 × 1.3 × 1.1 mm", 0.008, "SOT-23", "MOSFET P: inversión de polaridad y encendido", "Q1 y Q2 espalda con espalda (fuentes unidas)", "aosmd.com / distribuidores"),
    "AO3400A": ("A", "VDS 30 V", "5.7 A", "2.9 × 1.3 × 1.1 mm", 0.008, "SOT-23", "MOSFET N: conmuta los 16 emisores", "", "aosmd.com / distribuidores"),
    "SMAJ9.0A": ("A", "VRWM 9.0 V, Vc 15.4 V", "26 A pico", "4.3 × 2.6 × 2.2 mm", 0.07, "DO-214AC (SMA)", "TVS de la alimentación del motor", "Cátodo (banda) hacia VBAT_SW", "digikey.com SMAJ9-0A (Littelfuse)"),
    "1812L150/12DR": ("A", "12 V máx", "Ihold 1.5 A", "4.5 × 3.2 mm", 0.05, "1812", "Fusible reajustable de la batería", "", "digikey.com 1812L150-12DR"),
    "74438357022": ("A", "—", "IR 7.1 A, Isat 9.2 A", "4.1 × 4.1 × 3.1 mm", 0.25, "WE-MAPI 4030", "Inductor del reductor", "", "digikey.com / flux.ai (WE-MAPI 4030, 2.2 µH, 26 mΩ)"),
    "BLM18PG221SN1D": ("A", "—", "1.4 A", "1.6 × 0.8 × 0.8 mm", 0.003, "0603", "Ferrita de VDDA", "", "digikey.com / rs-online"),
    "XT30UPB-M": ("A", "500 V", "15 A (30 A pico)", "10.2 × 5.2 × 8 mm (APROX)", 1.5, "THT vertical", "Conector de batería (macho)", "Verificar que el paquete Tattu traiga XT30 hembra (XT30U-F) antes de soldar", "lcsc.com C428721; huella oficial KiCad AMASS"),
    "BM06B-SRSS-TB": ("A", "50 V", "1 A por contacto", "8.0 × 4.3 × 3.6 mm", 0.15, "JST SH 1.0 mm vertical", "Conector motor + encoder", "Pestañas laterales soldadas a GND", "jst-mfg.com (serie SH); huella oficial KiCad"),
    "M50-3500742": ("A", "—", "—", "2×7, paso 1.27 mm", 0.5, "THT 1.27 mm", "Conector STDC14 para el STLINK-V3MINIE (SWD + serie)", "Marcar el pin 1 del cable plano (rojo) con el '1' de la serigrafía", "digikey.com M50-3500742 (Harwin)"),
    "OS102011MA1QN1": ("A", "12 V DC", "100 mA", "8.6 × 4.4 mm (cuerpo)", 0.5, "THT ángulo recto", "Interruptor de encendido (conmuta la compuerta de Q1/Q2)", "Actuador hacia el borde derecho", "rs-online 7874855; digikey OS102011MA1QN1"),
    "B3FS-1000P": ("A", "24 V DC", "50 mA", "6 × 6 × 3.1 mm", 0.25, "SMD", "Botones START y CAL", "", "lcsc C271750; omron.com"),
    "B3U-1000P": ("A", "12 V DC", "50 mA", "3.0 × 2.5 × 1.6 mm", 0.03, "SMD", "Botón RESET", "", "lcsc C231329; omron.com"),
    "APT1608SGC": ("A", "VF ≈ 2.2 V", "20 mA máx", "1.6 × 0.8 mm", 0.002, "0603", "LED verde (3.3 V y estado)", "Cátodo: marca verde/raya de la huella", "digikey APT1608SGC (Kingbright)"),
    "APT1608EC": ("A", "VF ≈ 2.0 V", "20 mA máx", "1.6 × 0.8 mm", 0.002, "0603", "LED rojo (falla)", "", "digikey APT1608EC (Kingbright)"),
    "QRE1113GR": ("C", "VF 1.2 V (LED)", "IF 50 mA máx; IC(ON) 0.1-0.9 mA", "3.2 × 2.6 × 1.45 mm", 0.04, "CASE 100CY (SMD 4 pines)", "Sensor reflectivo de línea (16 en arco)", "CARA INFERIOR, ventana óptica hacia el piso; pin 1 (ánodo) hacia afuera del arco", "onsemi QRE1113/D; huella oficial KiCad OnSemi_CASE100CY"),
}
PASIVOS_MASA = {"0402": 0.0006, "0603": 0.002, "0805": 0.008}

# Fuera de la PCB: (categoría, fabricante, modelo, número de parte, descripción, cantidad, tensión, corriente,
#                  dimensiones, masa g, encapsulado, footprint, función, datasheet, observaciones, verificación)
EXTERNAS = [
    ("B", "Pololu", "10:1 Micro Metal Gearmotor HPCB 12V with Extended Motor Shaft", "3048", "Motorreductor 12 V, 9.96:1, 3400 rpm, escobillas de carbón, eje trasero extendido para encoder", 2,
     "12 V nominal (se usa a 2S, 6.4-8.4 V)", "0.08 A vacío / 0.75 A bloqueo a 12 V", "10 × 12 × 25 mm + eje 9 mm", 9.5, "—", "—", "Tracción", "https://www.pololu.com/product/3048", "Elegido por simulación (sim/resultados/final, etapas Z y R). Soldar la tarjeta del encoder a las terminales ANTES de montarlo", "pololu.com/product/3048/specs"),
    ("B", "Pololu", "Pololu Wheel 32×7mm Pair - Black", "1087", "Par de llantas Ø32 × 7 mm, silicón, ajuste a presión en eje D de 3 mm", 1,
     "—", "—", "Ø32 × 7 mm", 6.24, "—", "—", "Llantas motrices", "https://www.pololu.com/product/1087", "Presionar hasta que la cara exterior quede al ras del extremo del eje (2 mm libres contra la reductora)", "pololu.com/product/1087/specs"),
    ("C", "Pololu", "Magnetic Encoder Pair Kit with Top-Entry Connector for Micro Metal Gearmotors, 12 CPR, 2.7-18V", "4760", "Par de encoders magnéticos de cuadratura 12 CPR con conector JST SH de entrada superior", 1,
     "2.7-18 V (se usa 3.3 V)", "—", "11.6 × 14.2 mm", 1.5, "—", "—", "Velocidad de cada rueda", "https://www.pololu.com/product/4760", "La tarjeta sobresale 2.8 mm de la sección del motor: esa parte va HACIA ABAJO; conector hacia el centro del robot", "pololu.com/blog/860 (familia 4760/4761) y pololu.com/product/4761 (pinout)"),
    ("D", "Tattu (Grepow)", "Tattu 450mAh 2S 75C 7.4V Lipo Battery Pack with XT30 Plug - Long Size", "TA-75C-450-2S1P-L-XT30 (SKU TAA4502S75X3L)", "LiPo 2S 450 mAh 75C, conector XT30, balanceo JST-XH 3P", 1,
     "7.4 V nominal, 8.4 V lleno", "75C continuo", "61 × 16 × 15 mm", 28.4, "—", "—", "Alimentación", "https://www.genstattu.com/tattu-450mah-7-4v-75c-2s1p-lipo-battery-pack-with-xt30-plug-long-size-for-h-frame.html", "Se fija sobre las tapas de los soportes con Dual Lock; cables por el lado derecho al XT30. Comprar 2 si se quiere cargar una mientras se compite", "genstattu.com (ficha del producto)"),
    ("E", "—", "Bola de acero al cromo Ø 6.35 mm (1/4 in), grado G25", "ISO 3290-1 G25, AISI 52100, Ø 6.35 mm", "Bola de la rueda loca impresa", 1,
     "—", "—", "Ø 6.35 mm", 1.05, "—", "—", "Apoyo delantero", "https://www.iso.org/standard/54996.html", "Se coloca en la carcasa antes de atornillar la tapa", "norma ISO 3290-1 (pieza estándar)"),
    ("E", "3M", "3M Dual Lock Reclosable Fastener SJ3550, negro, 25.4 mm", "SJ3550", "Sujetador reabrible para la batería (2 tramos de 16 × 16 mm por cara)", 1,
     "—", "—", "25.4 mm de ancho", 0.6, "—", "—", "Sujeción de la batería", "https://www.3m.com/3M/en_US/p/d/b00018446/", "Pegar sobre las tapas de los soportes y en la cara inferior de la batería", "3m.com (familia Dual Lock SJ3550)"),
    ("F", "Pololu", "JST SH-Style Cable for Micro Metal Gearmotor Encoders, 6-Pin, Female-Female, 10cm", "4765", "Cable 6 hilos 28 AWG, JST SH hembra en ambos extremos", 2,
     "—", "1 A por contacto (JST SH)", "10 cm", 1.0, "—", "—", "Motor + encoder a la PCB (J2, J3)", "https://www.pololu.com/product/4765", "Verificar continuidad pin 1 (verde) a pin 1 antes de conectar; sobrante enrollado y amarrado", "pololu.com/product/4765"),
    ("F", "—", "Tornillo M2 × 12 cabeza de botón hexagonal interior, acero inoxidable A2", "ISO 7380-1 M2×12 A2", "Fija PCB + base + tapa de cada soporte de motor", 8,
     "—", "—", "M2 × 12", 0.40, "—", "—", "Sujeción de motores", "https://www.iso.org/standard/50467.html", "Cabeza por la cara inferior de la PCB, tuerca arriba de la pestaña de la tapa", "norma ISO 7380-1"),
    ("F", "—", "Tornillo M2 × 8 cabeza de botón hexagonal interior, acero inoxidable A2", "ISO 7380-1 M2×8 A2", "Une carcasa, PCB y tapa de la rueda loca", 2,
     "—", "—", "M2 × 8", 0.28, "—", "—", "Rueda loca", "https://www.iso.org/standard/50467.html", "Desde abajo: la cabeza entra en la caja de la carcasa y queda al ras (nada sobresale hacia el piso); tuerca sobre la tapa", "norma ISO 7380-1"),
    ("F", "—", "Tuerca hexagonal M2, acero inoxidable A2", "ISO 4032 M2 A2", "Tuercas de los soportes y la rueda loca", 10,
     "—", "—", "4 mm entre caras × 1.6 mm", 0.11, "—", "—", "Sujeción", "https://www.iso.org/standard/72441.html", "", "norma ISO 4032"),
    ("F", "STMicroelectronics", "STLINK-V3MINIE", "STLINK-V3MINIE", "Programador/depurador SWD con puerto serie virtual; incluye cable plano STDC14-STDC14", 1,
     "1.65-3.6 V (detecta T_VCC)", "No alimenta la placa", "—", 0.0, "—", "—", "Programar y usar la consola", "https://www.st.com/en/development-tools/stlink-v3minie.html", "Herramienta (no va en el robot). Cable USB-C a USB-A/C no incluido", "UM2910 (st.com)"),
    ("G", "Servicio de fabricación de PCB", "PCB 4 capas FR-4 TG155, 1.6 mm, cobre exterior 1 oz / interior 0.5 oz, ENIG, máscara negra, serigrafía blanca", "hardware/electronics/fabricacion/gerber/ (speed_follower)", f"PCB-chasis de {_PCB_L:.0f} × {_PCB_W:.0f} mm con contorno fresado y agujero de la bola", 1,
     "—", "—", f"{_PCB_L:.0f} × {_PCB_W:.0f} × 1.6 mm", _PCB_M, "—", "—", "Chasis y electrónica", "hardware/electronics/fabricacion/LEEME.md", f"Pedir con ensamblaje en AMBAS caras (16 sensores, 32 R de sensores y {len(D.LADO_INFERIOR)} pasivos abajo) o soldar a mano", "regla de diseño 0.15/0.2 mm, vías 0.55/0.25 mm: dentro de la capacidad estándar de 4 capas"),
    ("G", "Servicio de impresión 3D (MJF)", "HP 3D High Reusability PA 12 (Multi Jet Fusion), color gris natural o negro teñido", "hardware/mechanical/stl/*.stl (6 piezas)", "Soportes de motor (2 bases + 2 tapas) y rueda loca (carcasa + tapa)", 1,
     "—", "—", "ver planos", 9.0, "—", "—", "Piezas mecánicas", "hardware/mechanical/planos/", "Agujeros M2 a Ø2.3 mm: repasar con broca de 2.3 si quedan estrechos", "material: ficha HP 3D HR PA 12"),
]


def filas_pcb(por_lado=False):
    grupos = OrderedDict()
    for p in D.PARTES:
        if not p.en_bom:
            continue
        clave = (p.mpn, p.lado) if por_lado else p.mpn
        g = grupos.setdefault(clave, dict(p=p, refs=[]))
        g["refs"].append(p.ref)
    filas = []
    for clave, g in grupos.items():
        p = g["p"]
        mpn = p.mpn
        enc = p.huella.split(":")[1]
        if mpn in CAT:
            cat, v, i, dim, masa, encap, fun, obs, ver = CAT[mpn]
        else:   # pasivos
            tam = "0402" if "0402" in enc else "0603" if "0603" in enc else "0805"
            cat, v, i, masa, encap = "A", "", "", PASIVOS_MASA[tam], tam
            dim = {"0402": "1.0 × 0.5 mm", "0603": "1.6 × 0.8 mm", "0805": "2.0 × 1.25 mm"}[tam]
            if p.lib_id == "Device:R":
                v = "50 V" if tam == "0402" else "75 V"
                i = "1/16 W" if tam == "0402" else "1/10 W"
                fun = "Resistencia"
                ver = "nomenclatura de catálogo YAGEO RC (RC0402FR-07xxxL / RC0603FR-07xxxL)"
            else:
                v = p.descripcion.split("F ")[1].split(" ")[0] + " V" if "F " in p.descripcion else ""
                fun = "Condensador"
                ver = "distribuidores (Murata GRM)"
            obs = ""
        refs = sorted(g["refs"], key=lambda r: (r.rstrip("0123456789"), int("".join(c for c in r if c.isdigit()) or 0)))
        filas.append(dict(categoria=cat, fabricante=p.fabricante, modelo=p.valor, numero_parte=mpn, descripcion=p.descripcion
                          if len(refs) == 1 else p.descripcion.split(", canal")[0], cantidad=len(refs), tension=v, corriente=i,
                          dimensiones=dim, masa_unitaria_g=masa, encapsulado=encap, footprint=p.huella, funcion=fun,
                          datasheet=p.datasheet, observaciones_montaje=obs, referencias=" ".join(refs), verificado=ver,
                          lado=("inferior" if p.lado == "B" else "superior") if por_lado else
                          " / ".join(sorted({"inferior" if D.por_ref()[r].lado == "B" else "superior" for r in refs}))))
    return filas


def generar():
    pcb = filas_pcb()
    ext = [dict(categoria=e[0], fabricante=e[1], modelo=e[2], numero_parte=e[3], descripcion=e[4], cantidad=e[5],
                tension=e[6], corriente=e[7], dimensiones=e[8], masa_unitaria_g=e[9], encapsulado=e[10], footprint=e[11],
                funcion=e[12], datasheet=e[13], observaciones_montaje=e[14], referencias="", verificado=e[15], lado="")
           for e in EXTERNAS]
    todas = sorted(pcb + ext, key=lambda f: f["categoria"])
    campos = ["categoria", "fabricante", "modelo", "numero_parte", "descripcion", "cantidad", "tension", "corriente",
              "dimensiones", "masa_unitaria_g", "encapsulado", "footprint", "funcion", "datasheet", "observaciones_montaje",
              "referencias", "lado", "verificado"]
    s1 = io.StringIO()
    w = csv.DictWriter(s1, fieldnames=campos, lineterminator="\n")
    w.writeheader(); w.writerows(todas)
    # BOM de ensamblaje (formato de servicio de ensamblaje: Comment, Designator, Footprint, MPN, Fabricante, Cara)
    s2 = io.StringIO()
    w2 = csv.writer(s2, lineterminator="\n")
    w2.writerow(["Comment", "Designator", "Footprint", "Manufacturer Part Number", "Manufacturer", "Quantity", "Side"])
    for f in filas_pcb(por_lado=True):
        w2.writerow([f["modelo"], f["referencias"].replace(" ", ","), f["footprint"].split(":")[1], f["numero_parte"],
                     f["fabricante"], f["cantidad"], "Bottom" if f["lado"] == "inferior" else "Top"])
    # masa de la PCBA (componentes), con su centro
    m = x = y = z = 0.0
    for p in D.PARTES:
        if not p.en_bom:
            continue
        fila = next(f for f in pcb if f["numero_parte"] == p.mpn)
        mu = float(fila["masa_unitaria_g"])
        zc = 0.8 if p.lado == "F" else -0.7
        m += mu; x += mu * p.x; y += mu * p.y; z += mu * (zc + (1.6 if p.lado == "F" else 0.0))
    masa = dict(masa_g=round(m, 2), x=round(x / m, 2), y=round(y / m, 2), z=round(z / m, 2),
                origen="[E] suma de masas unitarias de la BOM (componentes); z relativo a la cara inferior de la PCB")
    return s1.getvalue(), s2.getvalue(), masa


def main():
    bom, ens, masa = generar()
    destinos = [(os.path.join(RAIZ, "docs", "BOM_FINAL.csv"), bom),
                (os.path.join(RAIZ, "hardware", "electronics", "fabricacion", "bom_ensamblaje.csv"), ens),
                (os.path.join(RAIZ, "hardware", "electronics", "verificacion", "masa_componentes.json"),
                 json.dumps(masa, indent=1, ensure_ascii=False) + "\n")]
    if "--verificar" in sys.argv:
        mal = [d for d, t in destinos if not os.path.exists(d) or open(d, encoding="utf-8").read() != t]
        print("BOM sincronizada con el diseño" if not mal else f"BOM NO sincronizada: {mal}")
        return 1 if mal else 0
    for d, t in destinos:
        os.makedirs(os.path.dirname(d), exist_ok=True)
        open(d, "w", encoding="utf-8").write(t)
        print("escrito", os.path.relpath(d, RAIZ))
    print(f"masa de componentes de la PCBA: {masa['masa_g']} g")
    return 0


if __name__ == "__main__":
    sys.exit(main())
