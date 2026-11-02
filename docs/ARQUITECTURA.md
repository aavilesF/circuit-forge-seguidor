# Arquitectura definitiva — Speed Follower Circuit Forge (fase final)

Fecha: 2 nov 2026 · Parámetros: [`config/robot_maestro.yaml`](../config/robot_maestro.yaml) (v3) · Compras: [`BOM_FINAL.csv`](BOM_FINAL.csv) ·
Evidencia de simulación: `sim/resultados/final/` · Electrónica: `hardware/electronics/` · Mecánica: `hardware/mechanical/`.

Etiquetas: **[F]** dato del fabricante · **[C]** calculado · **[Sim]** simulado · **[CAD]** medido en el modelo CAD ·
**[E]** estimado · **[S]** supuesto que debe medirse. **Nada está fabricado, armado ni medido**: toda validación de este
documento es de simulación o de CAD.

La arquitectura queda **cerrada**: una sola configuración, sin alternativas paralelas. El presupuesto dejó de ser
restricción en esta fase; se eligió lo que mejor cumple con datos publicados y verificables.

## 1. Configuración definitiva

| Bloque | Selección (número de parte) | Por qué |
|---|---|---|
| Motores | **Pololu #3048** — 10:1 Micro Metal Gearmotor **HPCB 12 V** con eje extendido (×2) | Datos de ficha completos (3400 rpm, 0.75 A de bloqueo, 0.17 kg·cm a 12 V [F]). En la etapa Z fue el más rápido de los motores con datos publicados (5.39 s, 100 %) y en la R el más robusto (§2) |
| Encoders | **Pololu #4760** (par, 12 CPR, conector superior JST SH) | Detección de rueda trabada, telemetría y el modo seguro C3e. Se conectan con 2 cables Pololu #4765 |
| Llantas | **Pololu #1087** 32 × 7 mm (par) | Diámetro del modelo (D = 32 mm); se ajusta a presión en el eje D de 3 mm |
| Sensores | **16 × onsemi QRE1113GR** en la cara inferior de la PCB, arco de radio 110 mm, paso 5.9 mm | Arco concéntrico al eje: cada sensor mide el error a la misma distancia L. Cara del sensor a 3.05 mm del piso [CAD] |
| Emisores | AO3400A (Q3) conmuta los 16 LED (75 Ω c/u) | Permite **restar la luz ambiente** en cada ciclo (lectura apagada y encendida) |
| MCU | **STMicroelectronics STM32G431CBT6** (LQFP-48), 170 MHz con HSI16 + PLL | 2 ADC en paralelo: 16 sensores + batería en ≈ 225 µs por ciclo; TIM1 para el PWM, TIM2/TIM3 en modo encoder, USART1 a la consola. Sin cristal: el HSI16 (±1 % [F]) basta para 115200 baud |
| Puente H | **TI DRV8833PWPR** (HTSSOP-16 PowerPAD) | 1.5 A RMS por canal [F] contra 0.53 A de bloqueo a 8.4 V [C]; 10.8 V máx. con batería 2S |
| Alimentación | XT30UPB-M → PTC 1812L150/12DR → 2 × AO3401A espalda con espalda → TVS SMAJ9.0A → VBAT_SW | Inversión de polaridad, encendido por la compuerta (SW1 OS102011MA1QN1, solo 80 µA) y recorte de picos |
| Regulación | **TI TPS563200DDCR** a 3.30 V (33.2 k / 10 k), inductor Würth 74438357022; ferrita BLM18PG221SN1D a VDDA | 3 A [F] contra ≈ 0.6 A de pico [C] (`CALCULOS_ELECTRICOS.md`) |
| Batería | **Tattu TA-75C-450-2S1P-L-XT30** (2S, 450 mAh, 75C) | 7.4 V nominales: los motores de 12 V nunca rebasan su tensión; el DRV8833 admite 8.4 V con margen |
| Interfaz | START y CAL (Omron B3FS-1000P), RESET (B3U-1000P), LEDs 3V3/OK (APT1608SGC) y ERR (APT1608EC) | START obligatorio para arrancar (R08); calibración a mano (C03) |
| Programación | Harwin **M50-3500742** (STDC14, 2 × 7, 1.27 mm) + **STLINK-V3MINIE** | SWD y puerto serie virtual por el mismo cable |
| Chasis | **La PCB es el chasis**: 4 capas, FR-4 1.6 mm, 130 × 92 mm | Sin placa adicional ni cableado de módulos; In1 = GND, In2 = +3V3 |
| Mecánica | Soportes de motor (base + tapa) y rueda loca (carcasa + tapa) en **PA12 por MJF**; bola de acero de 1/4 in; batería sobre los motores con Dual Lock SJ3550 | Los soportes elevan la PCB a 4.5 mm del piso; la bola va a 92 mm del eje |
| Control | **C3m** (perfil de velocidad por curvatura desde el modelo del motor, persecución pura y PD), v_max **0.8165 m/s**. **Modo seguro C3e** (curvatura de los encoders), v_max 0.6327 m/s | Elegidos por el tiempo esperado medio sobre 6 plantas de incertidumbre del motor (§3) |
| IMU | **No** | El control con giroscopio (C3g) no superó a C3m en la Fase 2 |
| Succión | **No** | Sin autorización de los organizadores (`REGLAMENTO_MATRIZ.md`) |

Masa: **112.9 g** [CAD] (límite de diseño 450 g; reglamento 500 g). CG a **20.1 mm** delante del eje, 15.4 mm sobre el piso [CAD]; el YAML del simulador usa estas masas y posiciones.
Huella: **132.0 × 92.0 mm**, alto 39.2 mm [CAD] (caja del reglamento 200 × 100 mm).

![Robot completo](../hardware/mechanical/render/robot_isometrica.png)

## 2. Decisión de motor (Pololu 10:1 frente a Pololu 15:1 y Chihai N20)

Ajuste del control por motor (etapa Z, 200 salidas en 4 pistas sintéticas) y sensibilidad a los datos que no publica el
fabricante (etapa R, 120 salidas por caso). Archivos: `sim/resultados/final/Z_motores.csv`, `R_sensibilidad_motores.csv`.

| Motor | Datos | Mejor ajuste (Z) | J_rotor × 0.5 | μ 0.70 | I de bloqueo alto |
|---|---|---|---|---|---|
| **Pololu #3048 HPCB 12 V 10:1** | Ficha completa [F]; J_rotor [S] | **5.39 s, 100 %** | 90.0 % | 97.5 % | 100 % (0.90 A) |
| Pololu #4789 HPCB 12 V 15:1 | Ficha completa [F]; J_rotor [S] | 5.56 s, 100 % | 70.8 % | 99.2 % | 100 % (0.90 A) |
| Chihai N20 12 V 2200 rpm i10 | Solo anuncio del vendedor; par, bloqueo y relación [S] | 5.03 s, 100 % | 100 % | 95.0 % | **75.0 %** (0.80 A) |

El Chihai solo es más rápido con datos supuestos y falla si su bloqueo real es alto; el 15:1 es más lento y más sensible a
la inercia del rotor. **Se elige el Pololu 10:1.** Con él, el control final se volvió a ajustar con robustez (§3), lo que
baja la velocidad de 0.892 a 0.8165 m/s a cambio de no depender del valor exacto de J_rotor ni del bloqueo.

## 3. Control elegido

Etapa E (`E_fuente_curvatura.csv`, `E_eleccion.json`): cada candidato se evaluó en la planta nominal y en 5 plantas extremas
(J_rotor × 0.5 y × 2, bloqueo × 0.8 y × 1.2, μ 0.70). Criterio: **tiempo esperado E** (tiempo medio + castigo por salidas
fallidas), promediado sobre las 6 plantas, porque no se sabe cuál es la real hasta medir el motor.

| Control | v_max | E medio | Peor E | Peor éxito | Nominal |
|---|---|---|---|---|---|
| **C3m (competencia)** | 0.8165 m/s | **6.64 s** | 10.69 s | 98.3 % | **5.81 s, 100 %** |
| C3m | 0.8875 m/s | 6.72 s | 12.83 s | 97.5 % | 5.48 s |
| C3m | 0.9407 m/s | 11.87 s | 34.83 s | 90.0 % | 5.30 s |
| **C3e (modo seguro)** | 0.6327 m/s | 7.17 s | 7.21 s | **100 %** | 7.16 s, 100 % |
| C3e | 0.6877 m/s | 7.41 s | 11.53 s | 98.3 % | 6.57 s |

## 4. Validación de robustez del control final con las masas del CAD (etapas F y G)

| Caso | Éxito | Tiempo medio |
|---|---|---|
| Nominal (200 salidas) | 100 % (IC 95 % 98.1-100) | 5.81 s |
| μ 0.70 / 0.60 | 100 % / 100 % | 5.83 / 5.85 s |
| CG 3 / 5 mm más adelante | 100 % / 100 % | 5.85 / 5.87 s |
| CG 7 mm más adelante | 98.3 % | 5.92 s |
| **CG 10 mm más adelante** | **80 %** (24 derrapes) | 6.13 s |
| CG 10 mm más atrás | 100 % | 5.74 s |
| Masa +10 g / +40 g | 100 % / 100 % | 5.86 / 5.98 s |
| Sensores más altos (mancha × 1.6), ruido × 2 y × 3, fototransistor lento (400 µs) | 100 % | 5.55-5.82 s |
| Encoder desconectado, batería a 6.9 V, latencia +1 ms, motores desparejos ± 10 % | 100 % | 5.82-5.92 s |
| Corriente de bloqueo × 0.8 / × 1.2 | 100 % / 100 % | 5.83 / 5.80 s |
| Modo seguro C3e: nominal (200) / CG 5 mm adelante / μ 0.60 | 100 % / 100 % / 100 % | 7.16 / 7.13 / 7.23 s |

El único caso sensible es el **CG adelantado**: hasta 5 mm por delante del CAD (x_CG ≤ 25 mm) el éxito es 100 %; a 10 mm
baja a 80 % (y el modo seguro a 60 %, así que no lo compensa). El reparto de peso real se mide al armar con ese criterio
(manual §7.5, mediciones M2 y M5).

## 5. Diagrama de bloques

```
 Batería 2S ─ XT30 J1 ─ PTC F1 ─ Q1/Q2 (AO3401A, SW1 en la compuerta) ─ TVS D1 ─ VBAT_SW ──┬─ DRV8833 U3 ─ J2/J3 ─ motores + encoders
                                                                                         ├─ TPS563200 U2 ─ +3V3 ─┬─ STM32G431 U1 (+3V3A por FB1)
                                                                                         │                       ├─ 16 × QRE1113GR (fototransistores, 10 k)
                                                                                         │                       ├─ emisores (75 Ω) ─ Q3 AO3400A ← EMIT_G
                                                                                         │                       └─ encoders (VCC 3.3 V)
                                                                                         └─ divisor 100 k / 33 k (R3/R4, C3) ─ VBAT_MED → ADC
 U1: ADC1/ADC2 ← S1-S16, VBAT_MED · TIM1 CH1-CH4 → AIN1, AIN2, BIN2, BIN1 · TIM2/TIM3 ← encoders · USART1 ↔ J4 (STDC14) · SWD ↔ J4
     PC13 START · PC14 CAL · PC15 nFAULT · PB10 nSLEEP · PB9 EMIT_G · PB13 LED OK · PA12 LED ERR · PB8 BOOT0 (10 k a GND)
```

Pines, funciones alternas y canales del ADC: `docs/CALCULOS_ELECTRICOS.md` §7 y `firmware/stm32/src/pines_generados.h`
(generado del mismo diseño que el esquemático y la PCB).

## 6. Qué cambió respecto a la Fase 3

| Bloque | Fase 3 ($2,000) | Final | Motivo |
|---|---|---|---|
| Motores | Chihai N20 12 V i10 | Pololu #3048 HPCB 12 V 10:1 | Datos publicados; el Chihai falla con bloqueo alto |
| Barra | Clon QTR-8A (8 TCRT5000) sin resta de luz ambiente | 16 × QRE1113GR en arco, con resta de luz ambiente | Sin depender de un módulo sin ficha |
| MCU | ESP32 DevKit | STM32G431CBT6 en la PCB | ADC doble y temporizadores de encoder; firmware sin Arduino |
| Driver | TB6612FNG (módulo) | DRV8833PWPR en la PCB | |
| Construcción | Módulos cableados sobre placa perforada | PCB-chasis de 4 capas | Menos masa y sin conectores entre módulos |
| Control | C3m, v_max 0.66 m/s | C3m 0.8165 m/s + modo seguro C3e | |

## 7. Supuestos que quedan por medir

| Dato | Valor usado | Medición | Si sale distinto |
|---|---|---|---|
| Inercia del rotor J_rotor | 2.4 × 10⁻⁸ kg·m² [S] | Indirecta: respuesta al escalón con los encoders | Con × 0.5 el éxito simulado baja a 98.3 %: usar el modo seguro o bajar v_max |
| Corriente de bloqueo y velocidad libre | 0.75 A, 3400 rpm a 12 V [F] | M7 (manual, paso 8) | Actualizar el YAML y correr `python3 sim/fase_final.py F` |
| μ llanta-pista | 0.80 [S] | M1 | Tabla de v_max por μ (`SIMULACION_DINAMICA.md`) |
| Señal y ruido de los sensores a 3.05 mm | mancha 3 mm, ruido 0.03 [S] | M8 | Probado hasta ruido × 3 sin pérdida (§4) |
| Reparto de peso | CG 20.1 mm [CAD] | M2, M5 | Si x_CG > 25 mm, mover la batería hacia atrás |
