# Conexiones de los esquemáticos V2 (12 nov 2026)
Archivos: `v2/electronica/principal/principal.kicad_sch` y `v2/electronica/sensores/sensores.kicad_sch`
(copias de `SDL V2 General/KiCAD/Esquemas V2/`). Todas las conexiones son **cables reales** de KiCad; GND y +3V3 se dibujan
con su símbolo de alimentación (igual que en un esquema clásico). Las 6 señales del cable entre placas llevan además su etiqueta.
Comprobación: conectividad recalculada desde el archivo contra la lista esperada (0 cortos, 0 redes partidas) y ERC oficial de
KiCad 10.0.8 por el MCP (principal: 0 errores, 0 avisos; sensores: 0 errores, 4 avisos sin efecto eléctrico).

## A. PCB principal
| Origen | Destino | Red | ¿Por qué? |
|---|---|---|---|
| BT1 + (LiPo, externa) | J1.1 → F1.1 | VBAT_RAW | La batería entra a la placa por J1 y pasa primero por el fusible |
| F1.2 | J2.1 → KCD1 (externo) | VBAT_F | El PTC corta la corriente si hay un corto; después va al interruptor de encendido |
| KCD1 → J2.2 | C1+, U1 IN+, U2 IN+, R1, D1 K, J5.1 | VBAT_SW | Batería ya encendida: alimenta los dos reguladores, el ventilador y la medición de batería. C1 (470 µF) amortigua los picos de los motores |
| BT1 −, J1.2 y todos los GND | Símbolo GND | GND | Retorno común: todas las piezas comparten la misma tierra |
| U1 OUT+ (5.0 V) | D2 ánodo | +5V | El primer MP1584 baja la batería a 5 V para el ESP32 |
| D2 cátodo | A1 pin 15 (5V/VIN) | ESP_5V | El diodo deja pasar 5 V al ESP32 pero impide que el USB de la PC empuje corriente al regulador |
| A1 pin 16 (3V3) | Símbolo +3V3 → J6.1 | +3V3 | El regulador del DevKit da 3.3 V; de ahí se alimenta la lógica de la placa de sensores |
| U2 OUT+ (6.0 V) | C2+, U3 VCC | +6V_MOT | El segundo MP1584 da 6 V fijos al DRV8833, que alimenta a los motores; C2 filtra |
| R1 100 k / R2 33 k + C3 | A1 pin 2 (GPIO36) | VBAT_SENSE | Divisor: 8.4 V → 2.08 V, dentro del rango del ADC; C3 quita ruido |
| A1 25/26 (GPIO19/21) | U3 IN1/IN2 | AIN1, AIN2 | El ESP32 manda velocidad (PWM) y sentido del motor izquierdo |
| A1 29/30 (GPIO22/23) | U3 IN3/IN4 | BIN1, BIN2 | Igual para el motor derecho |
| A1 21 (GPIO16) | U3 EEP (nSLEEP) | DRV_SLEEP | El ESP32 enciende el driver solo cuando está listo (el chip trae pull-down interno) |
| U3 OUT1/OUT2 | C4, J3 → M1 | MOTL_A/B | El driver entrega la corriente al motor izquierdo e invierte la polaridad para cambiar el sentido; C4 reduce el ruido de escobillas |
| U3 OUT3/OUT4 | C5, J4 → M2 | MOTR_A/B | Igual para el motor derecho |
| U3 ULT | sin conectar (X) | — | Pendiente P13 |
| A1 22 (GPIO17) → R4 100 Ω | Q1 compuerta (G) | FAN_PWM / FAN_G | El ESP32 prende el ventilador con el MOSFET; R4 limita el pico de corriente al cargar la compuerta |
| R5 10 k | G a GND | FAN_G | Mantiene el MOSFET apagado mientras el ESP32 arranca |
| Q1 drenador (D) | J5.2, D1 ánodo, M3 − | FAN_SW | El MOSFET conecta el negativo del ventilador a tierra (interruptor de lado bajo) |
| Q1 fuente (S) | GND | GND | Camino de retorno |
| D1 | en paralelo con el ventilador | VBAT_SW/FAN_SW | Absorbe el pico de voltaje del motor del ventilador al apagarlo y protege a Q1 |
| A1 20 (GPIO4) | SW2 START → GND | START | Al presionar, el pin baja a 0 (pull-up interno del ESP32) |
| A1 11 (GPIO14) | SW3 CAL → GND | CAL | Igual para calibrar |
| A1 1 (EN) | SW4 RESET → GND | EN | Bajar EN reinicia el ESP32 |
| A1 8, 9, 10, 7 (GPIO25, 26, 27, 33) | J6.3–6 | S0–S3 | Eligen cuál de los 16 canales del multiplexor se lee |
| A1 4 (GPIO34) | J6.7 | SIG | Regresa la lectura analógica del sensor elegido (ADC1) |
| A1 13 (GPIO13) | J6.8 | EMIT_EN | Orden de prender/apagar los LED de los sensores |
| PWR_FLAG | VBAT_SW, +5V, +6V_MOT, ESP_5V, GND, +3V3 | — | Solo avisan al ERC que esas redes tienen fuente; no son piezas |

## B. PCB de sensores
| Origen | Destino | Red | ¿Por qué? |
|---|---|---|---|
| J1.1 (+3V3) | R1–R12 (330 Ω), R13–R24 (10 k), U1 VCC, C1 | +3V3 | Alimenta LED, resistencias de pull-up y el multiplexor |
| J1.2 | Todos los GND | GND | Tierra común con la placa principal |
| R_n (330 Ω) | OP_n ánodo (A) | LEDA_n | La resistencia limita la corriente del LED infrarrojo |
| OP1–OP12 cátodo (CATH) | Q1 colector | EMIT_K | Los 12 LED regresan juntos por el transistor: si Q1 está apagado, ningún LED prende |
| OP_n colector (COLL) | R(12+n) 10 k a +3V3 y U1 C(n−1) | SEN_n | El fototransistor baja el voltaje cuando ve luz reflejada (blanco); el pull-up lo sube en negro. Cada sensor entra a un canal del mux |
| OP_n emisor (E) | GND | GND | Retorno del fototransistor |
| U1 C12–C15 | sin conectar (X) | — | Solo se usan 12 canales |
| U1 EN | GND | GND | El mux siempre habilitado (EN es activo en bajo) |
| U1 S0–S3 | J1.3–6 | S0–S3 | Vienen del ESP32 |
| U1 SIG | J1.7 | SIG | Salida común: el canal elegido llega aquí y viaja al ESP32 |
| C1 100 nF | +3V3 a GND junto a U1 | — | Desacople del multiplexor |
| J1.8 → R25 1 k | Q1 base | EMIT_EN / BASE_Q1 | El GPIO solo da ~2.6 mA a la base; el transistor maneja la corriente de los LED |
| R26 10 k | base a GND | BASE_Q1 | LED apagados si el cable se desconecta o el ESP32 está arrancando |
| Q1 emisor | GND | GND | Retorno |

## C. Alimentación de los LED: 3.3 V (actual) contra 5 V (propuesta, sin aplicar)
- **Hoy:** cada LED toma corriente de **+3V3** (el regulador de 3.3 V del DevKit) por su 330 Ω: (3.3 − 1.2 − 0.1)/330 ≈ 6 mA × 12 ≈ **72 mA**. El GPIO13 **no** da esa corriente: solo manda ~2.6 mA a la base del 2N2222, que es el que conduce los 72 mA.
- **Riesgo real:** no es el GPIO sino el pequeño regulador de 3.3 V del DevKit, que también alimenta al ESP32 (≈ 80–250 mA con picos). Aguanta, pero se calienta más y la luz de los LED es débil.
- **Propuesta (recomendada):** alimentar los ánodos desde **+5V** (salida del MP1584 #1, que da hasta ~3 A) con un **9.º hilo** en el cable, y cambiar R1–R12 a **220 Ω**: (5 − 1.2 − 0.1)/220 ≈ 17 mA × 12 ≈ **200 mA** (TCRT5000: máx. 60 mA por LED, Vishay). El 2N2222 aguanta 600 mA; para saturarlo con 200 mA conviene bajar R25 a **470 Ω** (~5.5 mA de base, β forzada ≈ 36).
- **¿Llega 5 V al ESP32?** No: los pull-up de 10 k y el multiplexor siguen en **+3V3**, así que SIG y los canales nunca pasan de 3.3 V. El 5 V solo toca los LED y el colector de Q1.
- Con esto el ESP32 y su regulador quedan libres de los 12 LED y los sensores ven más luz. **Requiere tu aprobación** (cambia la arquitectura: +1 hilo, 12 resistencias de 220 Ω y R25 de 470 Ω).

## D. IRLZ44N (RDS(on))
RDS(on) es la resistencia del MOSFET encendido. IR la garantiza con 4–5 V de compuerta; a 3.3 V enciende (umbral máx. 2 V)
pero con algo más de resistencia. Con un ventilador de ~100 mA la pérdida es de milivatios: **sirve, no se cambia**.
