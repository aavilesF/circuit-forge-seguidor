"""Cálculos analíticos de la fase de arquitectura (reproducibles). Uso: python3 fase1_calculos.py"""
import math
from modelo import MOTORES, G

D = 0.033; r = D / 2; MASA = 0.20; MU = 0.8; F_MOT = 0.7
VB = {"2S nominal": 7.4, "2S llena": 8.4, "2S crítica": 6.4}
print("=" * 100)
print("1) MOTORES con rueda de 33 mm y robot de 0.20 kg. Motores de 6 V limitados a 6 V promedio por PWM;")
print("   motores de 12 V directo a la 2S (siempre por debajo de su nominal). Bloqueo: dato de ficha escalado V/Vnom.")
a_grip = MU * G * F_MOT
print(f"   límite de tracción μ·g·f = {a_grip:.2f} m/s² (μ = {MU}, f = {F_MOT}: SUPUESTOS)")
print(f"   {'motor':32s} {'V aplicado':>10} {'v libre':>8} {'I bloqueo':>9} {'2×I (driver)':>12} {'a arranque':>10} {'τ mec':>6} {'freno a 1.2 m/s: corto / reversa'}")
for n, m in MOTORES.items():
    v = 6.0 if m.v_nom == 6 else 7.4
    vmax_ = 6.0 if m.v_nom == 6 else 8.4
    w0 = m.w0 * v / m.v_nom
    vlib = w0 * r
    i_s = m.i_s * vmax_ / m.v_nom
    ts = m.kt * (v / m.R - m.i0)
    a0 = min(2 * ts / r / MASA, 99)
    c = m.kt * m.ke / (m.R * r * r)                  # N/(m/s) por rueda
    tau = MASA / (2 * c)
    w12 = 1.2 / r
    f_corto = 2 * m.kt * (m.ke * w12 / m.R) / r      # freno corto: V = 0
    f_rev = 2 * m.kt * ((v + m.ke * w12) / m.R) / r  # contracorriente: V = −Vmax
    print(f"   {n:32s} {v:9.1f}V {vlib:7.2f} {i_s:8.2f}A {2 * i_s:11.2f}A {a0:9.1f} {tau:6.2f}s  {min(f_corto / MASA, a_grip):4.1f} / {min(f_rev / MASA, a_grip):4.1f} m/s²")
print("   (a arranque y freno se recortan al límite de tracción)")
print("=" * 100)
print("2) DRIVER: corriente continua requerida con 100 % de margen sobre el bloqueo")
print("   TB6612FNG: ≤ 1.0 A recomendado/canal; DRV8833 PWP/RTY: 1.5 A RMS, 2 A pico, OCP 2-3.3 A; DRV8833 PW: 0.5 A RMS")
print("=" * 100)
print("3) LATENCIA Y ANTICIPACIÓN DEL CUELLO")
for n in (8, 12, 16):
    for tc in (40e-6, 120e-6):
        t_lect = 2 * (n * tc + 100e-6)
        print(f"   {n:2d} canales, {tc * 1e6:3.0f} µs/canal, con resta de ambiente: lectura {t_lect * 1000:4.2f} ms")
t_lat = 1.36e-3 + 1.36e-3 + 4e-3      # lectura + periodo + filtro derivativo
print(f"   presupuesto electrónico (12 canales, 40 µs): lectura 1.36 + periodo 1.36 + filtro D 4 ms = {t_lat * 1000:.1f} ms")
print(f"   {'L (mm)':>8} | " + " | ".join(f"t=L/v a {v} m/s" for v in (0.8, 1.2, 1.6, 2.0)))
for L in (0.08, 0.10, 0.12, 0.14, 0.16):
    print(f"   {L * 1000:8.0f} | " + " | ".join(f"{L / v * 1000:12.0f} ms" for v in (0.8, 1.2, 1.6, 2.0)))
print("   Frenado necesario antes de una curva de R 150 (v_curva = sqrt(a_lat·R), a_lat = 4):")
vc = math.sqrt(4 * 0.15)
for v in (1.0, 1.2, 1.4, 1.6, 2.0):
    for ab in (2.0, 4.0):
        d = max(0, (v * v - vc * vc) / (2 * ab))
        print(f"   v = {v:.1f} m/s -> v_curva {vc:.2f}; con freno de {ab:.0f} m/s² necesita {d * 1000:5.0f} mm + latencia {v * t_lat * 1000:4.0f} mm")
print("=" * 100)
print("4) BARRA: desplazamiento lateral de la línea en la barra al entrar a un arco, L²/(2R)")
for L in (0.10, 0.12, 0.14, 0.16):
    print(f"   L {L * 1000:3.0f} mm: R150 {L * L / 0.30 * 1000:5.1f} mm | R200 {L * L / 0.40 * 1000:5.1f} mm | R400 {L * L / 0.80 * 1000:5.1f} mm"
          f"  -> semibarra mínima (R150, + 12.5 de media línea + 10 margen) {L * L / 0.30 * 1000 + 22.5:5.1f} mm")
print("   Paso: para ver la línea de 25 mm con >= 2 sensores siempre, paso <= 12.5 mm; con >= 3, paso <= 8.3 mm")
print("=" * 100)
