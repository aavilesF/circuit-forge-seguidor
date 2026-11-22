# Optimización de las PCB V2 — 14 nov 2026

Aprobada por Alan el 14 nov. Estado anterior: commit `3842103` de la rama (la etiqueta git no se pudo subir: el servidor solo acepta la rama).
Comparar con `git diff 3842103 -- v2/electronica` o abrir los archivos de ese commit.

| | Principal antes | Principal ahora | Sensores antes | Sensores ahora (A) | Sensores alternativa (B) |
|---|---|---|---|---|---|
| Tamaño | 96 × 84 mm | **96 × 74 mm** | 96 × 88 mm | **96 × 68 mm**, frente curvo | 96 × 59 mm, frente curvo |
| Vías | 23 | **22** | 16 | 18 | 24 |
| Tramos de pista | 631 | 559 | 645 | 608 | 710 |
| Pista arriba / abajo | 273 / 1179 mm | 297 / 1176 mm | 647 / 987 mm | 656 / 735 mm | — |
| Conexiones pendientes (DRC) | 0 | 0 | 0 | 0 | 0 |
| Errores DRC (KiCad 10.0.8) | 0 | 0 | 0 | 0 | 0 |

ERC (KiCad 10.0.8): principal 0 errores y 0 avisos; sensores 0 errores, 4 avisos (3 `pin_to_pin` y 1 `lib_symbol_mismatch`, los mismos de antes).
Avisos DRC: solo serigrafía, un tramo colgante en sensores y diferencias de campos de texto (`footprint_symbol_field_mismatch`); `net_conflict` = pines marcados sin conexión.

**Redes:** se compararon pad por pad contra las PCB anteriores (que ya coincidían con los esquemas): 102 pads en la principal y 138 en sensores, **0 diferencias** (`herramientas/padnets.py`).

## Cambios
- Principal: ESP32 bajado con el USB-C al borde; SW2 a la derecha del USB, SW3/SW4 arriba del ESP32; F1, J1, J2 en la columna izquierda bajo los reguladores; R1, R2, C3 arriba. Ningún componente nuevo ni quitado.
- Sensores: 12 TCRT5000 en el mismo arco (R = 90 mm, 7.7 mm entre sensores, simétrico, 2 al centro); 10 kΩ detrás; multiplexor 15.5 mm más adelante; contorno delantero en arco (R = 103 mm, concéntrico con los sensores).
- Las 220 Ω siguen delante: ver P-V2-35.
- Bibliotecas ESP32 y HC4067: dibujos de Edge.Cuts pasados a Dwgs.User (P-V2-28).

## Cálculos revisados
- **Emisores TCRT5000:** +5 V del MP1584 U1 → J6 pin 9 → +5 V de sensores → 220 Ω → ánodo. Con VF 1.25 V típ. (Vishay TCRT5000, IF = 20 mA) y 0.2–0.3 V en el 2N2222: I ≈ (5 − 1.25 − 0.25)/220 ≈ **16 mA por LED** (estimado), ~15 mA con VF máx. 1.5 V. Total de 12 LED ≈ **190 mA**.
- **2N2222:** base por R25 = 470 Ω desde 3.3 V → Ib ≈ (3.3 − 0.8)/470 ≈ 5.3 mA (R26 10 kΩ resta 0.08 mA). β forzada ≈ 190/5.2 ≈ 36. El P2N2222A (onsemi) garantiza hFE ≥ 100 a 150 mA y Ic máx. 600 mA, así que satura (VCE(sat) ≤ 0.3 V garantizado a 150 mA / 15 mA de base; a β 36 se estima 0.2–0.4 V). Disipación ≈ 0.19 A × 0.3 V ≈ 60 mW (límite 625 mW). **Suficiente.** Si se quiere saturación más profunda, R25 = 330 Ω (requiere aprobación).
- **Cable de 9 hilos:** 1 +3V3, 2 GND, 3 S0, 4 S1, 5 S2, 6 S3, 7 SIG, 8 EMIT_EN, 9 +5V, igual en las dos placas. Pin 9 y pin 2 llevan ~0.2 A: suficiente para cable de 26–28 AWG.
- Alimentación, motores y ventilador: U1→+5V→D2→VIN del ESP32; U2→+6V_MOT→DRV8833 VCC; J3/J4 a OUT1–4; J5 entre VBAT_SW y el drenador de Q1 (IRLZ44N, G-D-S = 1-2-3) con D1 en antiparalelo. Sin cambios.

## Tamaño del robot completo (estimado, falta mecánica)
- **Ancho:** las ruedas fijan el ancho, no las PCB. 2 × 24.5 mm (N20) + 2 × (≈1 + 22.1 mm de rin) ≈ 95 mm, más las terminales traseras de los motores → **~99–101 mm frente a 100 mm del reglamento**. Es el punto crítico (P-V2-34).
- **Largo:** sensores 68 + separación ~5 + principal 74 ≈ **150 mm** si van en línea; la rueda (∅26.7) no sobresale si el eje está a ≥ 14 mm del borde trasero. Cumple los 200 mm con margen.
- El USB-C necesita ~30 mm libres fuera del borde para el enchufe (~12 × 7 × 20 mm) y la curva del cable.
- Ventilador: ver P-V2-36.

## Limitaciones
ERC y DRC no comprueban la geometría física real (alturas, cables, chasis), el orden de patas del 2N2222 del lote, ni la huella final de F1 (provisional, P-V2-31). Q1 IRLZ44N usa la huella oficial `TO-220-3_Vertical` (pines a 2.54 mm, G-D-S como el datasheet de Infineon).
