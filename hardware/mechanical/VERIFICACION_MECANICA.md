# Verificación mecánica del CAD (generado por hardware/mechanical/verificar_mecanica.py)

Validación **CAD**: geometría, masas de ficha y volúmenes. No sustituye pesar y medir el robot armado (M2, M5).

## 1. Interferencias: 35 pares revisados, 0 con interferencia

| A | B | Volumen común (mm³) | OK |
|---|---|---|---|
| soporte_motor_base_izq | APROX_motor_pololu3048_encoder4760_izq | 0.0 | sí |
| soporte_motor_tapa_izq | APROX_motor_pololu3048_encoder4760_izq | 0.0 | sí |
| soporte_motor_base_der | APROX_motor_pololu3048_encoder4760_der | 0.0 | sí |
| soporte_motor_tapa_der | APROX_motor_pololu3048_encoder4760_der | 0.0 | sí |
| APROX_bateria_tattu450_2s | soporte_motor_tapa_izq | 0.0 | sí |
| APROX_bateria_tattu450_2s | soporte_motor_tapa_der | 0.0 | sí |
| APROX_bateria_tattu450_2s | APROX_motor_pololu3048_encoder4760_izq | 0.0 | sí |
| APROX_bateria_tattu450_2s | APROX_motor_pololu3048_encoder4760_der | 0.0 | sí |
| APROX_motor_pololu3048_encoder4760_izq | APROX_motor_pololu3048_encoder4760_der | 0.0 | sí |
| APROX_llanta_pololu1087_izq | soporte_motor_base_izq | 0.0 | sí |
| APROX_llanta_pololu1087_der | soporte_motor_base_der | 0.0 | sí |
| rueda_loca_carcasa | APROX_bola_6.35mm | 0.0 | sí |
| rueda_loca_tapa | APROX_bola_6.35mm | 0.0 | sí |
| PCBA | APROX_motor_pololu3048_encoder4760_izq | 0.0 | sí |
| PCBA | APROX_motor_pololu3048_encoder4760_der | 0.0 | sí |
| PCBA | APROX_llanta_pololu1087_izq | 0.0 | sí |
| PCBA | APROX_llanta_pololu1087_der | 0.0 | sí |
| PCBA | APROX_bateria_tattu450_2s | 0.0 | sí |
| PCBA | soporte_motor_base_izq | 0.0 | sí |
| PCBA | soporte_motor_base_der | 0.0 | sí |
| PCBA | soporte_motor_tapa_izq | 0.0 | sí |
| PCBA | soporte_motor_tapa_der | 0.0 | sí |
| PCBA | APROX_bola_6.35mm | 0.0 | sí |
| PCBA | rueda_loca_carcasa | 0.0 | sí |
| PCBA | rueda_loca_tapa | 0.0 | sí |
| PCBA | tornillo_M2x12_1 | 0.0 | sí |
| PCBA | tornillo_M2x12_2 | 0.0 | sí |
| PCBA | tornillo_M2x12_3 | 0.0 | sí |
| PCBA | tornillo_M2x12_4 | 0.0 | sí |
| PCBA | tornillo_M2x12_5 | 0.0 | sí |
| PCBA | tornillo_M2x12_6 | 0.0 | sí |
| PCBA | tornillo_M2x12_7 | 0.0 | sí |
| PCBA | tornillo_M2x12_8 | 0.0 | sí |
| PCBA | tornillo_M2x8_rl1 | 0.0 | sí |
| PCBA | tornillo_M2x8_rl2 | 0.0 | sí |

## 2. Huella: 132.00 × 92.00 mm, alto 39.20 mm (reglamento R01: 200 × 100 mm; límite de diseño 192 × 92 mm) → cumple

## 3. Altura sobre el piso (R11): punto más bajo de la PCBA 2.96 mm (caras de los sensores); piezas rígidas bajo 2 mm (sin contar llantas, bola y carcasa de la bola): 0
- Carcasa de la rueda loca: 1.60 mm sobre el piso, alrededor del punto de apoyo de la bola (≤ 8 mm del contacto)
- Cabezas de los tornillos de la rueda loca: 1.70 mm, dentro de la caja de la carcasa (no sobresalen del fondo)

## 4-5. Masa y centro de gravedad

| | CAD | Simulador (YAML) | Diferencia | Criterio |
|---|---|---|---|---|
| Masa | 112.9 g | 113.0 g | -0.1 % | ±3 %; ≤ 450 g |
| x del CG (adelante del eje) | 20.1 mm | 20.1 mm | -0.0 mm | ±2 mm |
| y del CG | -0.65 mm | 0 | | simétrico |
| z del CG | 15.4 mm | 15.4 mm | +0.0 mm | informativo |

Desglose del CAD:

| Pieza | Masa (g) | CG (mm) |
|---|---|---|
| soporte_motor_base_izq | 2.73 | [-0.0, 24.79, 8.47] |
| soporte_motor_base_der | 2.73 | [-0.0, -24.79, 8.47] |
| soporte_motor_tapa_izq | 1.57 | [0.0, 25.2, 17.02] |
| soporte_motor_tapa_der | 1.57 | [0.0, -25.2, 17.02] |
| rueda_loca_carcasa | 0.23 | [92.0, -0.0, 3.12] |
| rueda_loca_tapa | 0.13 | [92.0, -0.0, 6.71] |
| motor+encoder_izq | 10.2 | [-0.0, 23.7, 15.78] |
| llanta_izq | 3.12 | [-0.0, 42.5, 16.0] |
| motor+encoder_der | 10.2 | [-0.0, -23.7, 15.78] |
| llanta_der | 3.12 | [-0.0, -42.5, 16.0] |
| bateria | 28.4 | [0.0, -0.0, 31.7] |
| bola | 1.05 | [92.0, -0.0, 3.17] |
| tornillo_M2x12_1 | 0.51 | [10.0, 16.0, 8.58] |
| tornillo_M2x12_2 | 0.51 | [10.0, 34.0, 8.58] |
| tornillo_M2x12_3 | 0.51 | [-10.0, 16.0, 8.58] |
| tornillo_M2x12_4 | 0.51 | [-10.0, 34.0, 8.58] |
| tornillo_M2x12_5 | 0.51 | [10.0, -16.0, 8.58] |
| tornillo_M2x12_6 | 0.51 | [10.0, -34.0, 8.58] |
| tornillo_M2x12_7 | 0.51 | [-10.0, -16.0, 8.58] |
| tornillo_M2x12_8 | 0.51 | [-10.0, -34.0, 8.58] |
| tornillo_M2x8_rl1 | 0.39 | [92.0, 6.0, 5.45] |
| tornillo_M2x8_rl2 | 0.39 | [92.0, -6.0, 5.45] |
| cables_encoder (2 × #4765) | 2.0 | [10.0, 0.0, 12.0] |
| dual_lock (2 piezas) | 1.2 | [0.0, 0.0, 23.4] |
| PCB FR-4 4 capas 1.6 mm | 35.06 | [51.5, -0.0, 5.3] |
| componentes de la PCBA | 4.77 | [50.37, -15.27, 6.45] |

## 6. Accesibilidad: 10 elementos, 0 tapados

| Ref | Uso | Posición (x, y) mm | Cara | Libre |
|---|---|---|---|---|
| SW2 | botón START | (80.0, -22.0) | superior | sí |
| SW3 | botón CAL | (82.0, -5.5) | superior | sí |
| SW4 | botón RESET | (73.5, -6.0) | superior | sí |
| J4 | conector STDC14 (programación) | (66.4, -14.9) | superior | sí |
| J1 | XT30 de la batería | (19.5, -24.5) | superior | sí |
| SW1 | interruptor ON/OFF | (45.0, -25.8) | superior | sí |
| D3 | LED OK | (53.5, 8.0) | superior | sí |
| D4 | LED ERR | (53.0, -9.0) | superior | sí |
| D2 | LED 3V3 | (55.0, -18.0) | superior | sí |
| bola | cambio de la bola: 2 tuercas M2 sobre la tapa (cara superior) | (92.0, 0.0) | superior | sí |

RESULTADO: CUMPLE (validación CAD)
