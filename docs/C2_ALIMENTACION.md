# Checkpoint C2 — Alimentación de los motores

Fecha: 31 oct 2026 · Estado: **ABIERTO, pendiente de aprobación de Alejandro**. Este documento no cambia firmware ni hardware:
`MOTOR_DESDE_BATERIA` sigue en `false`.
Cálculos reproducibles: `python3 herramientas/c2_calculos.py --sim`.

Etiquetas: **[Doc]** dato de ficha o página oficial · **[Cálc]** cálculo con supuestos explícitos · **[Sim]** simulador `sim/` · **[MEDIR]** medición física pendiente.

## 0. Resumen

| | Recomendación |
|---|---|
| Arquitectura | **B: motores directo de la batería 2S con PWM compensado**, condicionada a medir la corriente de bloqueo del motor antes de conectarlo |
| Por qué | Mismo voltaje promedio que A (6 V), velocidad constante durante la descarga, sin regulador fuera de especificación, la batería absorbe la energía de frenado, −1 pieza |
| Costo | −$19 frente a la arquitectura actual; −$144 frente a la única A regulada viable que se encontró |
| Lo que no resuelve ninguna opción | Si el motor bloqueado consume > 1.0 A, el TB6612 queda fuera de su recomendación **en A y en B por igual** |

## 1. Fuentes

| Componente | Documento | Datos usados |
|---|---|---|
| TB6612FNG (Toshiba) | Ficha técnica (copia MSOE) | VM abs. 15 V; recomendado 4.5-13.5 V; IOUT abs. **1.2 A**; recomendado **≤ 1.0 A** (VM ≥ 5 V); pico 2 A (20 ms, ciclo ≤ 20 %) y 3.2 A (10 ms, único); Pd 0.78 W solo IC / 0.89 W PCB 50×50 mm / 1.36 W PCB 76×114 mm; Vsat(alto+bajo) 0.5 V @ 1 A y 0.15 V @ 0.3 A; apagado térmico 175 °C; PWM ≤ 100 kHz **[Doc]** |
| GA12-N20 6 V 1000 RPM (UNIT Electronics, el que se va a comprar) | Página del producto (consulta 31 oct) | 6 V, 1000 RPM ±10 %, sin carga **≤ 0.2 A**, par ≥ 0.15 kg·cm. **No publica corriente de bloqueo ni corriente nominal** **[Doc]** |
| GA12-N20 de otros vendedores | Ficha sin fabricante (variantes 100, 200, 450 RPM) | Bloqueo 0.67 A, nominal 0.04 A. **No es nuestra variante: no se usa como dato**, solo como escenario |
| | Guía de Phipps Electronics (serie metálica) | Bloqueo 0.67 A pero junto a "15 RPM a 6 V": dato genérico, no aplica |
| Pololu 30:1 Micro Metal Gearmotor HP 6 V #1093 | pololu.com | 1000 RPM, 120 mA sin carga, **1.6 A bloqueo**. Motor distinto, misma forma N20: escenario de "motor fuerte" |
| LiPo (celda de referencia GRP704230) | Ficha del fabricante | 4.2 V máx., 3.7 V nominal, 3.0 V corte, ≤ 25 mΩ. **La batería real aún no se elige**: su resistencia interna es [MEDIR] |
| MP1584 (MPS r1.1) | Ficha | 4.5-28 V, 3 A; pide VIN > VOUT + 3 V a baja carga; diodo bootstrap si VOUT/VIN > 65 % |
| Pololu D24V22F6 (step-down 6 V) | pololu.com #2859 | Entrada mínima 6.4 V (carga baja) a 6.9 V (2.5 A); 2.2-2.5 A típ.; protección contra inversión |
| Pololu S18V20F6 (buck-boost 6 V) | pololu.com #2575 | Entrada 3-30 V; 2 A típ. "cuando la entrada es cercana a la salida"; 7.5 g; protección contra inversión |
| Convertidor Boost Buck 5.5-30 V 4 A (UNIT, SKU AR4790) | Página del producto | Entrada 5.5-30 V; 3 A (4 A con disipador); 88 %; 180 kHz; anti-reflujo en la salida; **66 × 48 × 21 mm, 41.7 g; $144** |

**Corriente de bloqueo del motor elegido: DESCONOCIDA.** Todo cálculo de corriente se hace para tres escenarios (Is6 = corriente de bloqueo a 6 V): 0.67 A, 1.00 A (hipotético) y 1.60 A. El valor real se mide en la prueba P1.

## 2. Voltaje de la batería 2S [Doc + Cálc]

| Estado | Por celda | Paquete | Con 2 A (2 × 25 mΩ) |
|---|---|---|---|
| Llena | 4.20 V | 8.4 V | 8.30 V |
| Nominal | 3.70 V | 7.4 V | 7.30 V |
| Umbral de arranque del firmware | 3.40 V | 6.8 V | 6.70 V |
| Crítica del firmware (paro) | 3.20 V | 6.4 V | 6.30 V |
| Corte de la celda (no bajar de aquí) | 3.00 V | 6.0 V | 5.90 V |

Los paquetes pequeños de aeromodelismo suelen tener más resistencia interna que esta celda de referencia: la caída real es [MEDIR] (P5).

## 3. Voltaje instantáneo en el motor [Cálc]

El TB6612 entrega pulsos (20 kHz en nuestro firmware): durante el pulso el motor ve el voltaje de VM menos la caída del driver.

| Arquitectura | Pulso con 0.3 A | Promedio máximo |
|---|---|---|
| A (regulador en regulación) | 6.0 − 0.15 = **5.85 V** | 6.0 V con ciclo 100 % |
| B, batería llena | 8.4 − 0.15 = **8.25 V** | 6.0 V con ciclo máx. 71.4 % (compensado) |
| B, nominal | 7.25 V | 6.0 V con ciclo máx. 81.1 % |
| B, crítica | 6.25 V | 6.0 V con ciclo máx. 93.8 % |
| B, corte de celda | 5.85 V | 6.0 V con ciclo 100 % |

El motor responde al **promedio** porque su constante eléctrica L/R filtra los pulsos. Que esto se cumpla a 20 kHz depende de su inductancia: **[MEDIR]** (P4, rizado de corriente).

## 4. Corrientes por canal [Cálc, escenarios de Is6]

Modelo: V = I·R + Ke·ω, con R = 6 V / Is6 y Ke tal que 6 V den 1000 RPM con 0.2 A.

| Is6 supuesto | R | Arranque desde parado, A (6 V) | Arranque B **sin** compensación (8.4 V) | De adelante a fondo a −0.3 (freno del firmware) |
|---|---|---|---|---|
| 0.67 A | 8.96 Ω | 0.67 A | 0.94 A | 0.65 A |
| 1.00 A | 6.00 Ω | 1.00 A | **1.40 A** | 1.06 A |
| 1.60 A | 3.75 Ω | **1.60 A** | **2.24 A** | **1.81 A** |

Límites del TB6612: 1.0 A recomendado, 1.2 A absoluto, 2 A en pulsos de 20 ms (ciclo ≤ 20 %), 3.2 A en un pulso de 10 ms.

- **Con compensación, el promedio de B es igual al de A** (mismo voltaje promedio). El pico instantáneo dentro de cada pulso puede llegar hasta Vbat/R: **1.4 veces el de A** si la inductancia no lo filtra [MEDIR].
- Arranques e inversiones duran decenas de ms (constante mecánica): caben en la tolerancia de pulsos de 2 A **solo si** no se repiten más del 20 % del tiempo. El firmware **no limita hoy la rapidez de cambio** del comando. Un limitador de rampa sirve a las dos arquitecturas y está en la lista de cambios a aprobar (§10).
- Si el motor real mide **Is6 > 1.0 A**, ninguna de las dos arquitecturas deja al driver dentro de su recomendación al arrancar. Habría que limitar el comando en firmware (rampa y tope) o cambiar de driver. **Es independiente de C2.**

## 5. Disipación del TB6612 [Cálc]

P = I² × 0.5 Ω por canal, con dos canales:

| Caso | Potencia | Pd disponible (0.78-1.36 W según PCB) |
|---|---|---|
| Crucero, 0.3 A c/u | 0.09 W | holgado |
| Aceleración, 0.6 A c/u | 0.36 W | holgado |
| 1.0 A c/u (recomendado máx.) | 1.00 W | **excede** 0.78 y 0.89 W; un módulo pequeño se parece más a "solo IC" |
| Ambos bloqueados, Is6 0.67 A | 0.45 W | dentro |
| Ambos bloqueados, Is6 1.00 A | 1.00 W | **excede** → apagado térmico a ~175 °C |
| Ambos bloqueados, Is6 1.60 A | 2.56 W | **muy por encima** |

Con compensación, A y B disipan casi lo mismo: igual corriente promedio, y en B el valor eficaz es algo mayor por el rizado [MEDIR]. **B sin compensación** con batería llena disipa hasta 1.4² ≈ **1.96 veces** más.

## 6. Comportamiento durante la descarga [Doc + Cálc]

| Variante | De 8.4 a 6.8 V | De 6.8 a 6.4 V | Velocidad con comando 1 |
|---|---|---|---|
| A1: MP1584 a 6 V | Fuera de especificación en todo el rango (§1) | Igual | Incierta |
| A2: step-down D24V22F6 | 6 V regulados | Sale de regulación (entrada mínima 6.4-6.9 V): sigue a la batería | 100 % y luego cae |
| A3: buck-boost (UNIT AR4790 o Pololu S18V20F6) | 6 V | 6 V | 100 % |
| B sin compensación | Promedio = Vbat | = Vbat | 140 % → 107 % (varía 24 %) |
| **B con compensación** | 6 V promedio | 6 V promedio | **100 %** hasta 6.0 V |

## 7. Compensación por medición de batería [Cálc]

`pwm = cmd × 6.0 / Vbat_filtrada` (ya escrita y probada en software, apagada): `compensar_bateria()` en `control.cpp`, con 4 pruebas.
- **Exactitud:** el error de velocidad es igual al error de medición. Fuentes de error: resistencias de 1 % (±1.3 % en la relación del divisor) y el ADC del ESP32 (exactitud con calibración de fábrica [MEDIR]). Se calibra `DIVISOR_BAT` contra el multímetro (protocolo F3) para dejarlo en ≈ ±1 %.
- **Retardo:** filtro con α = 0.1 cada 20 ms → τ ≈ 0.2 s. Corrige la descarga lenta y la caída sostenida; no corrige caídas de < 0.2 s. Con 25 mΩ por celda esas caídas son ≈ 0.1 V (1.3 %).
- **Falla de medición:** si la lectura es inválida, lo seguro es **suponer 8.4 V** (el ciclo más bajo). Hoy el firmware no lo hace explícitamente: está en la lista de cambios a aprobar.
- **Resolución:** PWM de 10 bits; con ciclo máximo del 71 % quedan ~730 pasos. Suficiente.

## 8. Efecto en par, velocidad y control PD [Doc + Sim]

- Par T = Kt·I: con el mismo voltaje promedio, A y B dan el mismo par y la misma velocidad. B **sin** compensación da hasta 40 % más de velocidad con batería llena, por encima del voltaje nominal del motor.
- Para el control, la "ganancia de la planta" es vmax (mm/s por unidad de comando). Si cambia con la batería, el mismo Kp y Kd se comportan distinto:

| Simulación (vbase 0.6, Kp 0.04, Kd 0.002) | vmax | Pista 4.4 m | Error medio / máx. | Curva 90° R150 / U, error máx. | a_lat máx. |
|---|---|---|---|---|---|
| A, o B compensado (6 V) | 1400 mm/s | 5.18 s | 1.57 / 4.2 mm | 3.7 / 4.3 mm | 0.61 g |
| B sin comp., 8.4 V | 1960 | 4.22 s | 2.68 / 7.4 mm | 5.4 / 7.3 mm | **1.10 g** |
| B sin comp., 7.4 V | 1727 | 4.41 s | 2.01 / 5.4 mm | 4.6 / 5.6 mm | 0.91 g |
| B sin comp., 6.4 V | 1493 | 4.92 s | 1.67 / 4.2 mm | 4.2 / 4.3 mm | 0.69 g |

Lectura: sin compensación, el tiempo de vuelta varía 17 % con la carga de la batería y, con batería llena, la aceleración lateral (1.10 g) supera el agarre supuesto (0.9 g). En la realidad eso sería un derrape, que el simulador no modela. **La compensación es obligatoria si se elige B.** Con ella, el PD que se ajuste hoy sirve igual el día de la competencia.

## 9. Riesgos de sobrevoltaje y sobrecorriente

| Riesgo | A (regulado) | B (directo + compensación) | Mitigación |
|---|---|---|---|
| Pulsos de 8.4 V en un motor de 6 V | No | Sí | Mismo promedio. UNIT vende la misma carcasa en versiones de 12 V (otro devanado), pero no hay voltaje máximo publicado para la de 6 V. Desgaste de escobillas y temperatura [MEDIR, P6] |
| Error de firmware con ciclo 100 % | 6 V (seguro) | **8.4 V promedio: 140 % de velocidad, 1.4× corriente, 1.96× calor** | Tope de ciclo en la capa de hardware además de la compensación; suponer 8.4 V si la lectura falla (cambios a aprobar) |
| Energía de frenado regresando a VM | El buck-boost tiene salida **anti-reflujo**: la energía no puede volver a la batería y sube el voltaje de la línea de motores | La absorbe la batería | Cota superior: 0.2 J (0.30 kg a 1.15 m/s) en 470 µF subirían la línea a 29.7 V. Es irreal, porque la mayor parte se disipa en el devanado y el freno corto, pero en A hace falta capacitor de 470-1000 µF y rampa de frenado. Tope del TB6612: 15 V |
| Corriente de bloqueo > 1.0 A | Mismo riesgo | Mismo riesgo promedio; pico hasta 1.4× | Medir (P1); rampa y tope de comando; fusible |
| Sobredescarga de la LiPo | El buck-boost sigue drenando bajo 6 V (no se apaga solo) | El firmware para a 6.4 V | Monitor de batería ya implementado |
| Corto en la línea de motores | El regulador limita | Solo el fusible limita (la LiPo entrega decenas de A) | **Fusible reseteable obligatorio** en B |
| Inversión de polaridad | Pololu y AR4790 protegen; el módulo MP1584 no | TB6612 sin protección | Conector con polaridad única |

## 10. Tabla comparativa

| Criterio | A1 MP1584 6 V | A2 D24V22F6 | A3 buck-boost AR4790 | **B directo + comp.** |
|---|---|---|---|---|
| Dentro de su ficha | **No** | Sí, hasta 6.4-6.9 V | Sí | Sí (VM ≤ 13.5 V) |
| Velocidad durante la descarga | Incierta | Cae al final | Constante | Constante (con compensación) |
| Pulso en el motor | 6 V | 6 V | 6 V | 8.4 → 6.0 V |
| Corriente disponible | 3 A (teórico) | 2.2-2.5 A | 3 A (4 A con disipador) | La que dé la batería (limita el fusible) |
| Energía de frenado | Sube la línea | Sube la línea | Sube la línea (anti-reflujo) | La absorbe la batería |
| Masa añadida | ~2 g [MEDIR] | 2.3 g | **41.7 g** | 0 g |
| Espacio | Pequeño | 18 × 18 mm | **66 × 48 mm** (≈ 16 % de la huella de 20 × 10 cm) | 0 |
| Costo | $19 (verificado) | Pendiente de cotización (sin proveedor en México encontrado) | **$144** (verificado) | $0 |
| Disponibilidad | UNIT | Desconocida | UNIT, 155 piezas | — |
| Depende del firmware | No | No | No | **Sí** (compensación y tope) |

## 11. Arquitectura recomendada: B

```
LiPo 2S ─ fusible reseteable ─ interruptor ─┬─ VM TB6612FNG (+470 µF, +100 nF) ─ 2 × GA12-N20 6 V 1000 RPM
                                            └─ MP1584 a 5 V ─ VIN ESP32          (sub-decisión C2.2, abajo)
ESP32 GPIO36 ← divisor 100k/33k ← batería (compensación cada 20 ms)
```

**Componentes necesarios para B:** fusible reseteable (valor tras medir P1; orientativo: mayor que 2 × la corriente de crucero y menor que la suma de los dos bloqueos), interruptor ≥ 2 A, conector con polaridad única, capacitor de 470 µF 16 V + 100 nF en VM, divisor 100 kΩ/33 kΩ al 1 %, un MP1584 (lógica). **Se elimina** el MP1584 de motores.

**Sub-decisión C2.2 (lógica a 5 V, independiente de A/B):** el MP1584 a 5 V tiene menos de los 3 V de margen que pide su ficha cuando la batería baja de 8 V. Opciones: dejarlo y medirlo (prueba P3: ≥ 4.75 V con 6.8 V de entrada), o regulador con entrada mínima baja (Pololu D24V10F5: 5.1-5.8 V; cotización pendiente).

## 12. Impacto en costo (precios de UNIT del 31 oct 2026, sin envío)

| Opción | Partes de potencia de motores | Diferencia vs. BOM actual (A1) |
|---|---|---|
| A1 (actual) | MP1584 $19 | $0 |
| A3 | Buck-boost AR4790 $144 en lugar del MP1584 | +$125 (bajo el umbral de $200 de C4) |
| **B** | Ninguna | **−$19** |

## 13. Pruebas físicas necesarias (antes de conectar los motores al driver)

| # | Prueba | Cómo | Criterio |
|---|---|---|---|
| P1 | **Corriente de bloqueo** de cada motor a 6.0 V | Fuente o regulador a 6 V, amperímetro en serie, frenar el eje ≤ 1 s | Anotar. ≤ 1.0 A: sin restricción adicional. 1.0-1.2 A: rampa y tope obligatorios. > 1.2 A: no usar con TB6612 sin limitar |
| P2 | Corriente sin carga y RPM reales | `m 1 1` con el motor libre; contar vueltas en video | ≤ 0.2 A; 900-1100 RPM |
| P3 | MP1584 de lógica con batería baja | Fuente a 6.8 V, ESP32 conectado | ≥ 4.75 V |
| P4 | Rizado de corriente con PWM a 20 kHz (solo B) | Amperímetro promedio y, si hay, osciloscopio en una resistencia de 0.1 Ω | Promedio a ciclo 71 % con 8.4 V ≈ promedio a 100 % con 6 V (±10 %) |
| P5 | Caída de la batería en carga | `bat` en reposo y con ambos motores a fondo (ruedas en el aire) | Caída ≤ 0.3 V |
| P6 | Temperatura del motor y del driver | 5 min de marcha continua (A3 o B) | < 60 °C, sin olor |
| P7 | Compensación (solo B) | Medir RPM con batería a 8.4 V y a 7.0 V, mismo comando | Diferencia ≤ 5 % |

## 14. Decisión que debes aprobar

> **Apruebo C2-B:** los motores se alimentan directo de la batería 2S a través del TB6612FNG, con PWM compensado por el voltaje medido, y se quita el regulador de 6 V.
> Condición: la prueba P1 se hace antes de conectar los motores. Si algún motor mide más de 1.2 A de bloqueo, se revisa la decisión.

Al aprobarla se harían exactamente estos cambios (ninguno hecho todavía):
1. `pines.h`: `MOTOR_DESDE_BATERIA = true`.
2. `hardware.cpp`: tope de ciclo `6.0 / Vbat` también en `hw::motores()` (segunda barrera).
3. `seguidor.ino`: si la lectura de batería no es válida, compensar con 8.4 V.
4. `control.*`: limitador de rampa del comando de rueda (sirve también en A), con pruebas.
5. BOM: quitar un MP1584 y precisar el fusible después de P1. Diagramas y `decisiones.md`.

Alternativas: **A3** (+$125, +42 g, 66 × 48 mm de espacio; no depende del firmware) o **dejar A1** (no recomendado: fuera de su ficha).
Además hay que elegir en **C2.2** entre conservar el MP1584 de 5 V (si pasa P3) o cambiarlo por un regulador de entrada baja.
