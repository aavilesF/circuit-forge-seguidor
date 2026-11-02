# Cálculos eléctricos de la PCB-chasis (generado por hardware/electronics/herramientas/calculos_electricos.py)

Origen de los datos: [F] hoja de datos o ficha verificada, [S] supuesto conservador, [C] calculado. Pistas exteriores de 1 oz (35 µm). Corrientes admisibles según IPC-2221 con 10 °C de elevación.

## 1. Corrientes y anchos de pista (rutas reales de la PCB)

| Red | I máx [C] | Ancho mínimo usado | I admisible (IPC-2221, 10 °C) | Largo total | Largo bajo I máx | R de pista | Caída | Nota |
|---|---|---|---|---|---|---|---|---|
| VBAT_IN | 1.15 A | 0.80 mm | 2.03 A | 2.1 mm | 0.0 mm | 1.3 mΩ | 1.5 mV | 2 motores en bloqueo + lógica |
| VBAT_F | 1.15 A | 0.80 mm | 2.03 A | 6.3 mm | 0.0 mm | 3.9 mΩ | 4.4 mV |  |
| VBAT_SRC | 1.15 A | 0.80 mm | 2.03 A | 10.9 mm | 0.0 mm | 6.7 mΩ | 7.7 mV |  |
| VBAT_SW | 1.15 A | 0.30 mm | 1.00 A | 55.4 mm | 1.3 mm | 36.8 mΩ | 42.4 mV |  |
| MOT_L_1 | 0.53 A | 0.40 mm | 1.23 A | 11.6 mm | 0.0 mm | 14.2 mΩ | 7.5 mV | bloqueo a 8.4 V |
| MOT_L_2 | 0.53 A | 0.30 mm | 1.00 A | 12.1 mm | 0.0 mm | 19.9 mΩ | 10.4 mV |  |
| MOT_R_1 | 0.53 A | 0.40 mm | 1.23 A | 6.5 mm | 0.0 mm | 8.0 mΩ | 4.2 mV |  |
| MOT_R_2 | 0.53 A | 0.40 mm | 1.23 A | 10.3 mm | 0.0 mm | 12.6 mΩ | 6.6 mV |  |
| BUCK_SW | 1.17 A | 0.50 mm | 1.45 A | 6.1 mm | 0.0 mm | 6.0 mΩ | 7.0 mV | carga pico + mitad del rizo del inductor |
| EMIT_K | 0.45 A | 0.40 mm | 1.23 A | 102.3 mm | 0.0 mm | 125.7 mΩ | 56.3 mV | 16 emisores a 28 mA (peor caso) |

"Largo bajo I máx" suma los tramos cuya corriente admisible (IPC-2221, 10 °C) es menor que el peor caso de la red. En VBAT_SW es la entrada al pin 12 (VM) del DRV8833: 1.35 mm de pista de 0.30 mm entre la vía y el pin (el propio pad del encapsulado mide 0.45 mm), encerrada entre las ramas del bus PWM. Solo se acerca al límite con **los dos motores bloqueados a la vez con la batería llena** (1.05 A); el firmware corta a los 0.3 s de bloqueo y el pico simulado en carrera es 0.48 A por motor. Una pista de 0.30 mm admite 1.0 A con 10 °C y ≈ 1.3 A con 20 °C de elevación (misma fórmula): aceptado.

Los demás tramos delgados de las redes de potencia son entradas a pads pequeños (0402/0603) que solo llevan corriente de señal (divisor, habilitación, desacoplo); el tronco que lleva la corriente del motor es de 0.8 mm (VBAT) y 0.5 mm (motores). GND y +3V3 van por planos internos completos (In1.Cu y In2.Cu) más relleno de GND en ambas caras.

## 2. Ruta de potencia y caídas

- Corriente de bloqueo por motor a 8.4 V: 8.4 V / 16.0 Ω = **0.525 A** [C, R = 12 V / 0.75 A, ficha Pololu]
- Peor caso de la entrada (2 motores en bloqueo + lógica): 1.15 A
- Caída batería → VM: PTC (0.12 Ω [S]) + 2 MOSFET (0.1 Ω c/u [S]) + pistas (49 mΩ [C]) = **0.42 V** a 1.15 A (el simulador ya usa R_interna = 0.2 Ω para todo el lazo)
- Disipación en cada MOSFET: 132 mW (SOT-23) — sin disipador
- Fusible PTC 1812L150/12DR: corriente de mantenimiento 1.5 A [F] > 1.15 A de peor caso; dispara ante corto
- DRV8833PWPR: 1.5 A RMS por canal [F] contra 0.53 A de bloqueo; disipación en bloqueo de ambos motores 198 mW con HS+LS = 0.36 Ω [F]; la almohadilla térmica va a GND con vías térmicas (huella oficial)
- Protección contra inversión: Q1 bloquea con su diodo interno; |VGS| = 7.6 V con la batería llena (R1 100 k / R2 10 k) < 12 V máx. [F]. El interruptor SW1 solo conmuta la compuerta (≈ 80 µA) y es de 100 mA / 12 V [F]
- TVS SMAJ9.0A: VRWM 9.0 V [F] > 8.4 V; recorta picos inductivos y de conexión. **No conectar baterías 3S** (12.6 V): el TVS conduciría y el PTC dispararía; el DRV8833 admite 11.8 V máx. [F]

## 3. Regulador de 3.3 V (TPS563200)

- VOUT = 0.765 V · (1 + 33.2 k / 10 k) = **3.305 V** [F, VFB y tabla de la hoja de datos]
- Carga pico: emisores 448 mA + MCU 30 mA + encoders 10 mA + resistencias de los sensores 5.3 mA + LED = **496 mA**; promedio con emisores pulsados ≈ 141 mA. Capacidad: 3 A [F]
- Rizo de corriente del inductor (2.2 µH, 650 kHz, 8.4 V): 1.40 A pico a pico; pico del inductor 1.20 A, muy por debajo de la corriente nominal del 74438357022 (7 A Idc según RS; 5.2 A en la ficha de DigiKey) [F]
- Entrada 2 × 10 µF + 100 nF, salida 2 × 22 µF (dentro del rango 20-68 µF de la tabla [F]), arranque 100 nF [F]

## 4. Sensores QRE1113GR y emisores

- Corriente de cada LED: (3.3 − VF) / 75 Ω = 22.7-28.0 mA (VF 1.2-1.6 V [F]); máximo continuo 50 mA [F]
- Disipación en la resistencia de 75 Ω (0603, 100 mW): 59 mW con el emisor encendido continuo (peor caso)
- Q3 AO3400A conmuta 0.45 A (5.7 A [F])
- Fototransistor con 10 kΩ a 3.3 V: con IC(ON) = 0.1-0.9 mA [F, a 1 mm sobre espejo] la salida satura sobre blanco; a 3.05 mm sobre fórmica la señal real es una medición pendiente (M8)

## 5. Tiempos del ADC (ADC1 y ADC2 en paralelo, reloj HCLK/4 = 42.5 MHz)

- Conversión: (47.5 + 12.5) ciclos = 1.41 µs; 9 conversiones en serie por ADC = 12.7 µs por barrido
- Lectura con resta de luz ambiente: 2 barridos + 200 µs de establecimiento = **225 µs** (el simulador usa 478 µs: conservador)
- Muestreo con fuente de 10 kΩ: τ ≈ 110 ns; 47.5 ciclos = 1.12 µs = 10 τ → error < 1 LSB

## 6. Batería, encoders y USART

- Divisor 100 k / 33 k: 8.4 V → 2.084 V en el ADC (< 3.3 V); corriente 63 µA
- Encoders: 119.5 cuentas por vuelta de rueda (12 CPR [F] × 9.96); a v_max = 0.8165 m/s, 0.97 cuentas por ms (por eso la curvatura del control usa el modelo del motor y los encoders se usan para la detección de rueda trabada y la telemetría; el modo seguro C3e los usa con filtro)
- USART1: BRR = 170 MHz / 115200 = 1476 → error 0.021 %

## 7. Funciones alternas del MCU (verificadas con STM32_open_pin_data de ST y con el símbolo oficial de KiCad)

| Pin | Función | AF |
|---|---|---|
| PA10 | PWM_BIN2 (TIM1_CH3) | 6 |
| PA11 | PWM_BIN1 (TIM1_CH4) | 11 |
| PA12 | LED_ERR (GPIO_OUT) | — |
| PA13 | SWDIO (SYS_JTMS-SWDIO) | 0 |
| PA14 | SWCLK (SYS_JTCK-SWCLK) | 0 |
| PA15 | ENC_L_A (TIM2_CH1) | 1 |
| PA8 | PWM_AIN1 (TIM1_CH1) | 6 |
| PA9 | PWM_AIN2 (TIM1_CH2) | 6 |
| PB10 | DRV_SLEEP (GPIO_OUT) | — |
| PB13 | LED_OK (GPIO_OUT) | — |
| PB3 | ENC_L_B (TIM2_CH2) | 1 |
| PB4 | ENC_R_A (TIM3_CH1) | 2 |
| PB5 | ENC_R_B (TIM3_CH2) | 2 |
| PB6 | UART_TX (USART1_TX) | 7 |
| PB7 | UART_RX (USART1_RX) | 7 |
| PB8 | BOOT0 (BOOT0) | — |
| PB9 | EMIT_G (GPIO_OUT) | — |
| PC13 | BTN_START (GPIO_IN) | — |
| PC14 | BTN_CAL (GPIO_IN) | — |
| PC15 | DRV_FAULT (GPIO_IN) | — |
| PG10 | NRST (NRST) | — |

| Pin | Señal | ADC | Canal |
|---|---|---|---|
| PB14 | S1 | ADC1 | IN5 |
| PB12 | S2 | ADC1 | IN11 |
| PB11 | S3 | ADC2 | IN14 |
| PB2 | S4 | ADC2 | IN12 |
| PB1 | S5 | ADC1 | IN12 |
| PB0 | S6 | ADC1 | IN15 |
| PA7 | S7 | ADC2 | IN4 |
| PA6 | S8 | ADC2 | IN3 |
| PA5 | S9 | ADC2 | IN13 |
| PA4 | S10 | ADC2 | IN17 |
| PA3 | S11 | ADC1 | IN4 |
| PA2 | S12 | ADC1 | IN3 |
| PA1 | S13 | ADC1 | IN2 |
| PA0 | S14 | ADC2 | IN1 |
| PF1 | S15 | ADC2 | IN10 |
| PF0 | S16 | ADC1 | IN10 |
| PB15 | VBAT_MED | ADC2 | IN15 |
