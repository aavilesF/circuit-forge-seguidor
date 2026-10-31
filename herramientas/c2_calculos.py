#!/usr/bin/env python3
"""Cálculos reproducibles del checkpoint C2 (alimentación de motores).

Uso:  python3 herramientas/c2_calculos.py            (solo cálculos)
      python3 herramientas/c2_calculos.py --sim      (además corre sim/ con vmax según el voltaje)

Modelo de motor DC con escobillas (estado estable):  V = I·R + Ke·ω   ;   T = Kt·I
Parámetros DOCUMENTADOS (fuente en docs/C2_ALIMENTACION.md):
  TB6612FNG (Toshiba): Vsat(U+L) 0.5 V típ./0.7 V máx. @ 1 A; 0.15 V típ./0.21 V máx. @ 0.3 A;
             RECOMENDADO IOUT ≤ 1.0 A (VM ≥ 5 V); MÁXIMO ABSOLUTO 1.2 A (no es operación garantizada);
             pico 2 A en pulsos de 20 ms con ciclo ≤ 20 %; 3.2 A en un solo pulso de 10 ms;
             Pd (Ta 25 °C) 0.78 W solo IC (θj-a 160 °C/W), 0.89 W PCB 50x50 Cu≥40 %, 1.36 W PCB 76x114 Cu≥30 %;
             apagado térmico 175 °C típ.; con PWM bajo el puente queda en FRENO CORTO (OUT1 = OUT2 = L)
  LiPo (celda de referencia GRP704230): 4.2 V máx., 3.7 V nominal, 3.0 V corte, ≤ 25 mΩ
  GA12-N20 6 V 1000 RPM (UNIT): sin carga ≤ 0.2 A, 1000 RPM ±10 %. CORRIENTE DE BLOQUEO NO PUBLICADA.
Por eso la corriente de bloqueo a 6 V (Is6) se trata como PARÁMETRO DESCONOCIDO y se barre:
  0.67 A (dato de otra ficha GA12-N20, variantes 100-450 RPM; NO es la nuestra)
  1.00 A (valor intermedio, hipotético)
  1.60 A (Pololu 30:1 HP 6 V, clase de motor N20 de alta potencia; NO es la nuestra)
"""
import math, subprocess, sys

V_NOM = 6.0
RON = 0.5                       # Ω, TB6612 alto+bajo típico (0.5 V @ 1 A); máx. 0.7 Ω
RON_MAX = 0.7
THETA_JA = 160.0                # °C/W, solo IC (ficha); el módulo real es PENDIENTE de medir
I_ABS, I_REC = 1.2, 1.0         # A por canal
PD = {"solo IC": 0.78, "PCB 50x50": 0.89, "PCB 76x114": 1.36}
R_CELDA = 0.025                 # Ω, celda de referencia (paquetes de hobby suelen ser mayores: PENDIENTE medir)
BAT = {"llena 4.20 V/celda": 8.4, "nominal 3.70": 7.4, "umbral de arranque fw 3.40": 6.8,
       "crítica fw 3.20": 6.4, "corte de celda 3.00": 6.0}
I0 = 0.2                        # A sin carga (máximo publicado por UNIT)
N0 = 1000.0                     # RPM sin carga a 6 V (nominal, ±10 %)
IS6 = {"0.67 A (otra variante)": 0.67, "1.00 A (hipotético)": 1.00, "1.60 A (clase Pololu HP)": 1.60}


def motor(is6):
    R = V_NOM / is6                                  # bloqueo: ω = 0 → I = V/R
    w0 = N0 * 2 * math.pi / 60
    ke = (V_NOM - I0 * R) / w0                       # V·s/rad
    return R, ke, w0


def linea(t="-"):
    print(t * 78)


def main():
    linea("=")
    print("1) VOLTAJE DE BATERÍA 2S Y CAÍDA POR RESISTENCIA INTERNA (2 celdas x 25 mΩ)")
    for k, v in BAT.items():
        print(f"   {k:30s} {v:4.1f} V | con 2 A: {v - 2 * 2 * R_CELDA:4.2f} V | con 3 A: {v - 3 * 2 * R_CELDA:4.2f} V")

    linea("=")
    print("2) VOLTAJE INSTANTÁNEO EN EL MOTOR (pulso PWM 'encendido', I = 0.3 A en crucero)")
    print("   A (regulador 6 V en regulación): 6.0 - 0.3*0.5 = %.2f V en cada pulso" % (6.0 - 0.3 * RON))
    for k, v in BAT.items():
        d = min(1.0, V_NOM / v)
        print(f"   B {k:30s} pulso = {v - 0.3 * RON:4.2f} V | ciclo máx. con compensación = {d * 100:5.1f} % | promedio máx. = {d * v:4.2f} V")

    linea("=")
    print("3-5) CORRIENTES POR CANAL (estado estable promedio; R = 6 V / Is6)")
    print(f"   {'Is6 supuesto':28s} {'R (Ω)':>6} {'arranque A':>11} {'arranque B sin comp.':>21} {'inversión a -0.3':>17}")
    for k, is6 in IS6.items():
        R, ke, w0 = motor(is6)
        ia = V_NOM / R                                # arranque desde parado con cmd 1 (6 V)
        ib = 8.4 / R                                  # B sin compensación con batería llena, cmd 1
        e = ke * w0 * 0.95                            # fuerza contraelectromotriz a ~95 % de velocidad
        irev = (0.3 * V_NOM + e) / R                  # de adelante a fondo a -0.3 (rueda_min del firmware)
        print(f"   {k:28s} {R:6.2f} {ia:10.2f}A {ib:20.2f}A {irev:16.2f}A")
    print("   Límites TB6612: recomendado 1.0 A | absoluto 1.2 A | 2 A en pulsos de 20 ms (≤20 % ciclo) | 3.2 A 10 ms único")
    print("   Con compensación, B tiene el MISMO promedio que A. Pico instantáneo de B ≤ Vbat/R (si la")
    print("   inductancia no filtra; L del motor PENDIENTE de medir): hasta 8.4/6 = 1.40 veces el de A.")

    linea("=")
    print("6) DISIPACIÓN EN EL TB6612 (P = I² · 0.5 Ω por canal, dos canales)")
    for etiqueta, i in (("crucero 0.3 A c/u", 0.3), ("aceleración 0.6 A c/u", 0.6), ("recomendado 1.0 A c/u", 1.0)):
        print(f"   {etiqueta:26s} P = {2 * i * i * RON:4.2f} W")
    for k, is6 in IS6.items():
        p = 2 * is6 ** 2 * RON
        print(f"   ambos bloqueados, Is6 {k:26s} P = {p:4.2f} W  vs Pd 0.78-1.36 W -> {'EXCEDE' if p > 0.89 else 'dentro'} (PCB 50x50)")

    print("   Elevación de temperatura de unión con θj-a = 160 °C/W (supuesto: módulo pequeño ≈ 'solo IC'):")
    for etiqueta, p in (("crucero 0.09 W", 0.09), ("aceleración 0.36 W", 0.36), ("1.0 A c/u, 1.0 W", 1.0)):
        print(f"      {etiqueta:22s} ΔT = {p * THETA_JA:5.0f} °C -> Tj ≈ {25 + p * THETA_JA:4.0f} °C a 25 °C ambiente (apagado a ~175 °C)")
    print("   Con Ron máximo (0.7 Ω) la disipación sube 40 %.")

    linea("=")
    print("6b) RIZADO DE CORRIENTE POR PWM (modo freno corto, conducción continua)")
    print("   Δi_pp ≈ Vbus·D·(1−D) / (L·f) = Vprom·(1−D)/(L·f);  f = 20 kHz.  L del motor: DESCONOCIDA (medir)")
    f = 20e3
    for vprom in (3.0, 6.0):
        for L_mH in (0.1, 0.3, 1.0):
            L = L_mH * 1e-3
            fila = []
            for etiqueta, vbus in (("A 6.0 V", 6.0), ("B 8.4 V", 8.4), ("B 7.4 V", 7.4)):
                d = vprom / vbus
                if d > 1: fila.append(f"{etiqueta}: n/a"); continue
                fila.append(f"{etiqueta}: {vbus * d * (1 - d) / (L * f):5.2f} A")
            print(f"   Vprom {vprom:.0f} V, L {L_mH:3.1f} mH | " + " | ".join(fila))
    print("   Válido si L/R ≫ 50 µs. Con L = 0.1 mH y R ≈ 6 Ω, L/R ≈ 17 µs: la corriente sigue a los pulsos")
    print("   (el promedio se conserva, pero el valor eficaz y el pico suben). El par promedio depende del")
    print("   promedio de la corriente; el calentamiento depende del valor eficaz.")

    linea("=")
    print("7) VELOCIDAD SIN CARGA RELATIVA vs. BATERÍA (cmd = 1)")
    print("   A con step-down (p.ej. D24V22F6, entrada mínima 6.4-6.9 V): 100 % hasta ~6.9 V, luego sigue a la batería")
    print("   A con buck-boost (S18V20F6, entrada 3-30 V): 100 % en todo el rango")
    for k, v in BAT.items():
        sin = v / V_NOM
        con = min(v, V_NOM) / V_NOM
        print(f"   B {k:30s} sin compensación {sin * 100:5.1f} % | con compensación {con * 100:5.1f} %")

    linea("=")
    print("8) ERROR DE LA COMPENSACIÓN (velocidad ∝ V_promedio ∝ Vbat_real / Vbat_medida)")
    for err in (0.01, 0.02, 0.05):
        print(f"   error de medición ±{err * 100:.0f} %  ->  error de velocidad ±{err * 100:.0f} %")
    tau = 0.020 / 0.1
    print(f"   filtro EMA alfa=0.1 cada 20 ms: constante de tiempo ≈ {tau:.2f} s (no sigue caídas rápidas de < 0.2 s)")

    linea("=")
    print("8b) ¿LA COMPENSACIÓN IGUALA A 'A'? Modelo promedio en conducción continua:")
    print("   V_motor = D·(Vocv − I_tot·R_pack) − I·Ron   (Ron en fase ON: alto+bajo; en freno corto: bajo+bajo, SUPUESTO igual)")
    print("   A:  V_motor = cmd·6 − I·Ron             B comp.: D = cmd·6/V_medida, V_medida = Vocv − I_tot·R_pack (filtrada)")
    print("   En estado estable B = A (mismo término −I·Ron). Diferencias:")
    for rpack in (0.05, 0.10, 0.20):
        for di in (1.0, 2.0):
            dv = di * rpack * 0.71
            print(f"   R_pack {rpack:.2f} Ω (SUPUESTO), escalón de {di:.0f} A: déficit transitorio ≈ {dv:4.2f} V ({dv / 6 * 100:4.1f} %) durante ~0.2 s")
    print("   Error del ADC/divisor ±ε → velocidad ±ε. Saturación: con cmd = 1 el ciclo llega a 100 % si V_medida ≤ 6 V.")

    linea("=")
    print("10) REGENERACIÓN HACIA VM (solo ocurre si D·VM < E en la fase ON; freno corto y contracorriente NO regeneran)")
    E, vcmd, R = 5.4, 3.0, 6.0
    i = (vcmd - E) / R
    p = vcmd * abs(i)
    print(f"   E = {E} V, D·VM = {vcmd} V, R = {R} Ω -> I = {i:.2f} A, potencia hacia VM ≈ {p:.1f} W")
    for c_uF in (470, 1000):
        dvdt = p / (c_uF * 1e-6 * 6.0)
        print(f"   A3 (salida anti-reflujo), {c_uF} µF a 6 V sin otra carga: dV/dt ≈ {dvdt:.0f} V/s -> {dvdt * 0.01:.1f} V en 10 ms")
    print("   Cota de energía total (irreal: supone que TODA la energía cinética vuelve a VM):")
    m, v = 0.30, 1.15
    e = 0.5 * m * v * v
    for c_uF in (100, 470, 1000):
        c = c_uF * 1e-6
        v2 = math.sqrt(V_NOM ** 2 + 2 * e / c)
        print(f"   E = {e:.3f} J; con {c_uF:4d} µF en VM y sin carga que la absorba: V sube hasta {v2:5.1f} V (cota irreal, ver doc)")

    if "--sim" in sys.argv:
        linea("=")
        print("9) EFECTO EN EL CONTROL PD (sim/, vbase 0.6, kp 0.04, kd 0.002; vmax = 1400 mm/s × Vprom/6)")
        casos = [("A o B con compensación (6 V)", 1400)] + [(f"B sin comp. {v} V", round(1400 * v / 6)) for v in (8.4, 7.4, 6.4)]
        for etiqueta, vmax in casos:
            out = subprocess.run(["sim/ejecutar.sh", "vbase=0.6", f"vmax={vmax}", "modo=escenarios"],
                                 capture_output=True, text=True, check=True).stdout
            filas = [l.split(",") for l in out.splitlines() if l and not l.startswith(("#", "escenario"))]
            d = {f[0]: f for f in filas}
            pc, cu, u = d["pista_completa"], d["curva_90_r150"], d["U_r150"]
            print(f"   {etiqueta:28s} vmax {vmax:4d} | pista {pc[5]:>5} s err_med {pc[6]:>4} err_max {pc[7]:>4} mm | "
                  f"curva err_max {cu[7]:>4} | U err_max {u[7]:>4} | a_lat máx {pc[14]} g")
    linea("=")


if __name__ == "__main__":
    main()
