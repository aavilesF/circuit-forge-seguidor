# Checkpoint C2 — Alimentación de los motores (versión 2)

Fecha: 31 oct 2026 · Estado: **ABIERTO, pendiente de aprobación de Alejandro.**
Este documento no cambia firmware, hardware ni BOM. `MOTOR_DESDE_BATERIA` sigue en `false`.
Cálculos reproducibles: `python3 herramientas/c2_calculos.py --sim`.

**Cambios respecto a la versión 1:**
- Se separan las corrientes recomendadas, los máximos absolutos y los picos del TB6612FNG.
- La disipación se calcula con la resistencia térmica de la ficha.
- El "tope de ciclo en hardware" se reetiqueta como **protección dependiente del software**.
- La afirmación de que "la batería absorbe el frenado" se corrige por un análisis de caminos de corriente; **la regeneración no está demostrada**.
- P1 se reescribe con fuente limitada en corriente; P3 se amplía.
- Se analiza qué conserva y qué no la compensación `6/Vbat`.

Etiquetas: **[Doc]** ficha o página oficial · **[Cálc]** cálculo teórico · **[Sup]** supuesto · **[MEDIR]** medición pendiente.

## 1. TB6612FNG: qué garantiza la ficha (Toshiba, Ta = 25 °C) [Doc]

| Categoría | Parámetro | Valor | Condición |
|---|---|---|---|
| **Operación recomendada** | IOUT por canal | **≤ 1.0 A** | VM ≥ 5 V (≤ 0.4 A si 4.5 ≤ VM < 5 V) |
| | VM | 4.5-13.5 V (la tabla de pines dice 2.5-13.5 V; se usa el rango más estricto) | |
| | VCC | 2.7-5.5 V | |
| | PWM | ≤ 100 kHz | |
| **Máximos absolutos** (no son operación) | IOUT | 1.2 A | límite de daño; **no** es corriente continua garantizada |
| | VM / salidas | 15 V | |
| | VCC / entradas | 6 V / −0.2 a 6 V | |
| | Temperatura de operación | −20 a 85 °C | |
| **Picos** (máximos absolutos) | IOUT pico | 2 A | pulsos de 20 ms, ciclo de trabajo ≤ 20 % |
| | IOUT pico | 3.2 A | **un solo** pulso de 10 ms |
| **Disipación** Pd | Solo el IC (SSOP24) | 0.78 W | θj-a = 160 °C/W |
| | Montado en PCB 50 × 50 × 1.6 mm, Cu ≥ 40 % | 0.89 W | |
| | Montado en PCB 76.2 × 114.3 × 1.6 mm, Cu ≥ 30 % | 1.36 W | |
| **Caída del puente** | Vsat (alto + bajo) | 0.5 V típ., 0.7 V máx. a 1 A; 0.15 V típ., 0.21 V máx. a 0.3 A | VM = VCC = 5 V |
| **Protecciones** | Apagado térmico | 175 °C típ., histéresis 20 °C | "no protegen al IC en todas las circunstancias" |
| | Bajo voltaje | ~1.9 V / ~2.2 V | |
| | **Limitación de corriente** | **no tiene** | |

**Nuestro módulo:** "Doble Puente H TB6612FNG" de UNIT. Su PCB es mucho menor que 50 × 50 mm y su cobre no está documentado, así que se usa el caso conservador **"solo IC", 0.78 W, θj-a 160 °C/W** [Sup]. La temperatura real es [MEDIR] (P6).

## 2. Motor GA12-N20 6 V 1000 RPM (UNIT) [Doc / Cálc / MEDIR]

- **Documentado [Doc]:** 6 V, 1000 RPM ±10 %, sin carga ≤ 0.2 A, par ≥ 0.15 kg·cm. **No hay corriente de bloqueo, corriente nominal, resistencia ni inductancia.**
- **Otras fichas GA12-N20** (variantes de 100-450 RPM, sin fabricante) dicen 0.67 A de bloqueo. **No se usan como dato:** otra relación de engranes y quizá otro devanado.
- **Teoría [Cálc]:** con el eje detenido no hay fuerza contraelectromotriz, así que I_bloqueo = V / R_devanado. La corriente de bloqueo es lineal con el voltaje y se puede **calcular midiendo R con el óhmetro**, sin bloquear el motor (P1-a).
- **Escenarios para los cálculos [Sup]:** Is6 (bloqueo a 6 V) = 0.67 A, 1.00 A o 1.60 A (este último, clase Pololu HP 6 V, otro motor).

### Pulsos de hasta 8.4 V (opción B)
- El voltaje **instantáneo** durante cada pulso es Vbat − I·Ron: de 8.25 V (batería llena) a 5.85 V (corte) [Cálc].
- Con el motor bloqueado, la corriente **al final de un pulso largo** tendería a 8.4 / R = **1.4 × Is6**. Que lo alcance depende de L/R frente al periodo de 50 µs:
  - si L/R ≫ 50 µs, la inductancia filtra y la corriente queda cerca del promedio, D·Vbat / R = Is6 con compensación;
  - si L/R ≪ 50 µs, la corriente sigue a los pulsos y su pico se acerca a 1.4 × Is6.
- **L no está documentada → [MEDIR]** (P4). Con L = 0.1 mH y R ≈ 6 Ω, L/R ≈ 17 µs (no filtra); con 1 mH, ≈ 170 µs (filtra) [Cálc].

## 3. Caminos de corriente del TB6612 y frenado [Doc + Cálc]

Tabla de modos (ficha; la extracción del PDF estaba desordenada y se reconstruyó; **verificar contra el PDF original**):

| IN1 | IN2 | PWM | STBY | OUT1/OUT2 | Modo |
|---|---|---|---|---|---|
| H | L | H | H | H / L | Giro CW |
| L | H | H | H | L / H | Giro CCW |
| H | L | L | H | L / L | **Freno corto** |
| L | H | L | H | L / L | **Freno corto** |
| H | H | x | H | L / L | Freno corto |
| L | L | H | H | alta impedancia | Paro (stop) |
| x | x | x | L | alta impedancia | Standby |

Nuestro firmware (`hardware.cpp`) fija IN1/IN2 según el sentido y aplica el PWM al pin PWM, así que **cada periodo alterna "giro" y "freno corto"** (decaimiento lento). Caminos de corriente:

| Fase | Camino | ¿Va energía hacia VM? |
|---|---|---|
| PWM alto, corriente positiva (motor consume) | VM → transistor alto → motor → transistor bajo → GND | No: sale de VM |
| PWM bajo (freno corto) | La corriente circula por **los dos transistores bajos** y el motor | **No**: VM queda desconectado; la energía se disipa en el devanado y en Ron |
| Tiempo muerto (t2, t4; todos apagados) | Por los diodos del puente (VF ≈ 1 V a 1 A) | Solo si en ese instante la corriente es negativa; dura muy poco |
| PWM alto con D·VM < E (se pide menos velocidad de la que lleva) | La corriente promedio (D·VM − E)/R es **negativa**: en la fase de giro entra a VM por el transistor alto | **Sí, en teoría.** Es el único camino regenerativo con nuestro esquema |
| Paro (IN1 = IN2 = L) o standby | Alta impedancia: la corriente del inductor decae por los diodos hacia VM. Luego el motor queda suelto (E ≈ 6 V < VM + 2 VF, no conduce) | Breve; la ficha advierte "corriente de regreso a la fuente por la fuerza contraelectromotriz" |
| Sentido invertido a −0.3 (freno del firmware) | El voltaje aplicado se suma a E (frenado por contracorriente) | **No**: consume energía de VM y la disipa en el devanado |

**Corrección a la versión 1:** decir que "en B la energía de frenado vuelve a la batería" **no estaba demostrado**.
- Con decaimiento lento, la mayor parte del frenado (freno corto y contracorriente) **se disipa en el motor**.
- Solo hay regeneración hacia VM cuando el firmware baja el ciclo por debajo de E/VM sin invertir el sentido. Ocurre, por ejemplo, al frenar antes de una curva con `freno_error`.
- Orden de magnitud [Cálc]: E = 5.4 V, el comando baja a D·VM = 3 V y R = 6 Ω dan I ≈ −0.4 A y ≈ 1.2 W hacia VM mientras dura la desaceleración (decenas de ms).
- **En B** esa corriente llegaría a la batería, que puede recibirla (además, el ESP32 consume del mismo bus).
- **En A3** el convertidor tiene salida "anti-reflujo" (UNIT): no puede devolverla, y si el otro motor no la consume carga el capacitor de VM. Con 1.2 W en 470 µF a 6 V, el voltaje subiría a ≈ 426 V/s, unos 4.3 V en 10 ms [Cálc], sin contar las pérdidas.
- **Ni la existencia ni la magnitud están medidas → [MEDIR] P8.**

## 4. Corrientes en arranque, aceleración e inversión [Cálc con Is6 supuesto]

| Is6 | R | Arranque desde parado: A y B compensado (promedio) | B **sin** compensación, 8.4 V | Inversión a −0.3 desde ~95 % de velocidad |
|---|---|---|---|---|
| 0.67 A | 8.96 Ω | 0.67 A | 0.94 A | 0.65 A |
| 1.00 A | 6.00 Ω | 1.00 A | 1.40 A | 1.06 A |
| 1.60 A | 3.75 Ω | 1.60 A | 2.24 A | 1.81 A |

- El arranque desde parado **es** un bloqueo momentáneo: la corriente empieza en Is6 y baja conforme el motor toma velocidad. La constante mecánica es [MEDIR]; típicamente decenas de ms en motores N20 [Sup].
- Frente a la ficha: hasta 1.0 A está en la zona recomendada. De 1.0 a 2 A solo es aceptable en pulsos de ≤ 20 ms con ciclo ≤ 20 % (máximo absoluto). Una curva cerrada con corrección sostenida **no** es un pulso.
- El firmware **no** limita hoy la rapidez de cambio del comando (rampa). Con Is6 > 1.0 A eso sería necesario en **A y en B por igual**.

## 5. Disipación y temperatura del driver [Cálc]

P = I² × Ron por canal, dos canales; Ron 0.5 Ω típ. (0.7 Ω máx., +40 %); Tj = 25 °C + P × 160 °C/W.

| Caso | P (típ.) | Tj estimada | Comentario |
|---|---|---|---|
| Crucero, 0.3 A c/u | 0.09 W | ≈ 39 °C | holgado |
| Aceleración sostenida, 0.6 A c/u | 0.36 W | ≈ 83 °C | aceptable |
| 1.0 A c/u (máximo recomendado) | 1.00 W | ≈ 185 °C | **llega al apagado térmico**: la recomendación de 1.0 A supone mejor disipación que la de un módulo pequeño |
| Ambos bloqueados, Is6 = 0.67 A | 0.45 W | ≈ 97 °C | soportable poco tiempo |
| Ambos bloqueados, Is6 = 1.00 A | 1.00 W | ≈ 185 °C | apagado térmico |

El rizado de PWM aumenta el valor eficaz (y la disipación) sin cambiar el promedio. Es mayor en B a igual voltaje promedio, porque Δi ∝ Vprom·(1 − D) (§7) [Cálc].

## 6. Qué es el "límite de ciclo de trabajo" y qué protege

| Protección | Tipo | Qué limita | ¿Independiente del software? |
|---|---|---|---|
| `compensar_bateria()` en `control.cpp` | Software | Voltaje promedio ≤ 6 V | **No** |
| Tope de ciclo `6/Vbat` en `hw::motores()` (propuesto, **no implementado**) | Software, en otra capa | Mismo límite: segunda barrera si falla la primera | **No**: el mismo firmware. Protege contra errores en el control, no contra un ESP32 colgado o mal programado |
| Suponer 8.4 V si la lectura de batería es inválida (propuesto) | Software | Evita el 100 % si falla el ADC | **No** |
| STBY en bajo al reiniciar | Hardware del TB6612 + pin del ESP32 | Motores sueltos mientras el ESP32 arranca. La ficha muestra resistencias internas de 200 kΩ en las entradas; su sentido es [MEDIR] P3 | Parcial |
| Fusible reseteable | Hardware | Corriente sostenida (cortos, bloqueo largo); no protege contra 8.4 V promedio en un motor girando | **Sí** |
| Apagado térmico del TB6612 | Hardware | Temperatura del driver | **Sí**, pero no protege al motor |
| Regulador de 6 V (A2 o A3) | Hardware | Voltaje del motor ≤ 6 V aunque el firmware falle | **Sí: solo existe en A** |

**Consecuencia:** en B, el límite de 6 V promedio **depende del software**. Un error de firmware o un ADC mal leído puede aplicar 8.4 V promedio: 140 % de velocidad, 1.4 veces la corriente y 1.96 veces la disipación. **A3 es la única opción con un límite de voltaje independiente.**

## 7. ¿La compensación 6/Vbat conserva el comportamiento del motor? [Cálc]

Modelo promedio en conducción continua (con freno corto, la corriente puede invertirse, así que conduce de forma continua):

`V_motor = D·(Vocv − I_total·R_pack) − I·Ron`

Ron aparece en ambas fases: alto + bajo en giro y bajo + bajo en freno corto. Que sean iguales es [Sup]: la ficha solo da "alto + bajo".

| Efecto | A (regulado 6 V) | B compensado (D = cmd·6 / V_medida) | ¿Igual? |
|---|---|---|---|
| Voltaje promedio en estado estable | cmd·6 − I·Ron | cmd·6·(V_carga / V_medida) − I·Ron | **Sí**, si V_medida = V_carga (el divisor mide la batería con carga) |
| Pérdida del puente (−I·Ron) | Igual | Igual | Sí |
| Caída de la batería con carga | La absorbe el regulador | La compensa el filtro con τ ≈ 0.2 s; en escalones de 1-2 A queda un déficit de 0.04-0.28 V (0.6-4.7 %) durante ~0.2 s, según R_pack de 0.05-0.20 Ω [Sup] | Casi; difiere en transitorios |
| Error de medición del ADC o del divisor | No aplica | Error de velocidad igual al error de medición (±1 % tras calibrar con multímetro; exactitud del ADC [MEDIR]) | Casi |
| Par promedio (∝ corriente promedio) | Igual a igual voltaje promedio | Igual | Sí |
| RPM = (Vprom − I·R_total) / Ke | Igual | Igual | Sí |
| Rizado de corriente, Δi ≈ Vprom·(1 − D)/(L·f) a 20 kHz | Menor (D mayor) | Mayor: con L = 0.3 mH y 6 V promedio, 0.29 A p-p con 8.4 V contra 0 en A al 100 % | **No**: más calor en motor y driver; no cambia el par promedio |
| Pico de corriente con L/R pequeña | ≤ 6/R | ≤ 8.4/R | **No** |
| Saturación | Ciclo 100 % = 6 V | El ciclo llega al 100 % si V_carga ≤ 6 V | Igual mientras V_carga > 6 V |
| Frecuencia PWM | — | 20 kHz: el TB6612 admite 100 kHz. Subirla reduce el rizado pero aumenta las pérdidas de conmutación (no documentadas) | Ajustable; [MEDIR] |

**Conclusión:** en promedio, con el motor girando, B compensado ≈ A (par, RPM y respuesta del PD iguales; ver §8). Difiere en el rizado y los picos de corriente, en los transitorios de caída de la batería y en que **depende del software**. La magnitud del rizado depende de L, que no se conoce.

## 8. Efecto en el control PD [Sim; modelo sin derrape ni rizado]

| Caso (vbase 0.6, Kp 0.04, Kd 0.002) | vmax | Pista de 4.4 m | Error medio / máx. | a_lat máx. |
|---|---|---|---|---|
| A, o B compensado (6 V) | 1400 mm/s [Sup] | 5.18 s | 1.57 / 4.2 mm | 0.61 g |
| B sin compensación, 8.4 V | 1960 | 4.22 s | 2.68 / 7.4 mm | 1.10 g (> 0.9 g supuesto de agarre) |
| B sin compensación, 6.4 V | 1493 | 4.92 s | 1.67 / 4.2 mm | 0.69 g |

Sin compensación, el tiempo de vuelta cambia 17 % entre batería llena y baja, y con batería llena el robot derraparía. **B solo es viable con compensación.**

## 9. Datos confirmados, cálculos, supuestos y mediciones pendientes

| Dato | Tipo | Valor o estado |
|---|---|---|
| TB6612: 1.0 A recomendado, 1.2 A absoluto, 2 A/20 ms/≤ 20 %, 3.2 A/10 ms, Pd 0.78-1.36 W, θj-a 160 °C/W, Vsat 0.5-0.7 V a 1 A, sin limitación de corriente | **Ficha** | Toshiba TB6612FNG |
| TB6612: PWM bajo = freno corto; IN1 = IN2 = L = alta impedancia | **Ficha** (tabla reconstruida) | Verificar contra el PDF original |
| GA12-N20 6 V 1000 RPM: ≤ 0.2 A sin carga, ±10 % RPM, ≥ 0.15 kg·cm | **Ficha del vendedor** | UNIT |
| LiPo: 4.2 V máx., 3.7 V nominal, 3.0 V corte por celda | **Ficha** (celda de referencia, no la batería real) | GRP704230 |
| ESP32-WROOM-32: 30-50 mA a 240 MHz sin radio; fuente ≥ 500 mA | **Ficha** | Espressif |
| MP1584: VIN > VOUT + 3 V a baja carga; bootstrap si VOUT/VIN > 65 % | **Ficha** | MPS r1.1 |
| AR4790: 5.5-30 V, 3 A, anti-reflujo, 41.7 g, 66 × 48 mm, $144 | **Página del vendedor** | UNIT |
| I_bloqueo = V/R; corrientes de §4; disipación de §5; rizado de §7; regeneración ≈ 1.2 W | **Cálculo** | `c2_calculos.py` |
| Is6 = 0.67 / 1.0 / 1.6 A; L = 0.1-1 mH; R_pack = 0.05-0.20 Ω; Ron bajo = alto; módulo ≈ "solo IC"; vmax 1400 mm/s; μ = 0.9 | **Supuestos** | Sustituir por las mediciones |
| R del devanado e Is6 reales (P1), corriente y RPM sin carga (P2), comportamiento de la lógica (P3), L y rizado (P4), caída de la batería (P5), temperaturas (P6), compensación (P7), voltaje de VM al frenar (P8) | **Mediciones pendientes** | Protocolo §10 |

## 10. Pruebas físicas

**P1 — Corriente de bloqueo (sin LiPo, sin TB6612)**
- *Equipo:* fuente de laboratorio con límite de corriente (CV/CC; la del laboratorio de la universidad), multímetro en escala de resistencia y en escala de 10 A con fusible (o el amperímetro de la fuente), pinzas o la rueda para sujetar el eje, cronómetro.
- *P1-a, sin estrés:* medir la resistencia del devanado en 6 posiciones del rotor, girando la salida un poco entre lecturas. Restar la resistencia de las puntas (puntas en corto). Is6 estimada = 6 V / R_mín.
- *P1-b, confirmación a voltaje reducido:* fuente a **3.0 V**, límite de corriente **1.5 A**, motor solo con cables ≥ 24 AWG.
  - Medir la corriente sin carga.
  - Sujetar la salida **≤ 2 s**, leer la corriente al segundo y soltar. **Esperar ≥ 30 s** entre pulsos. Máximo 3 pulsos por motor, en distintas posiciones del rotor.
  - Is6 = I(3 V) × 2 (lineal con el eje detenido).
- *P1-c, opcional:* un solo pulso a 6.0 V con límite de 2.0 A, ≤ 1 s, **solo** si P1-a y P1-b dan Is6 ≤ 1.5 A.
- *Interrumpir de inmediato si:* la fuente entra en limitación de corriente (el voltaje cae), hay olor, humo o ruido de engranes, la corriente sube mientras se sostiene, o la carcasa supera ~50 °C al tacto.
- *Prohibido:* usar la LiPo, el TB6612 o un regulador sin límite; sostener más de 2 s.
- *Criterio:* Is6 ≤ 1.0 A, apto en A y B. De 1.0 a 1.2 A: rampa y tope de comando obligatorios. > 1.2 A: no usar con el TB6612 sin limitar corriente.

**P2 — Sin carga:** 6.0 V con fuente, corriente ≤ 0.2 A; RPM 900-1100 (video o marca en la rueda).

**P3 — Lógica de 5 V y reinicios** (MP1584 real, ajustado a 5.0 V en vacío antes de conectar)
- *Equipo:* fuente variable o batería parcialmente descargada, multímetro con función MIN/MAX y, si es posible, osciloscopio (laboratorio).
- *Pasos:*
  1. ESP32 + sensor conectados con entrada de 8.4, 7.4 y 6.8 V: medir 5 V y 3V3.
  2. Con 6.8 V: 20 ciclos de `m 1 1` (arranque simultáneo), 20 de `m -0.3 -0.3` tras `m 1 1` (inversión) y 20 de `m 1 1` → `m 0.2 0.2` (desaceleración). En B, motores conectados a la misma batería; en A3, al convertidor.
  3. Monitor serie abierto: cualquier texto de arranque nuevo (`rst:` del ROM, o el aviso de brownout del core de Arduino) **es un reinicio**.
  4. Medir la temperatura del MP1584 tras 5 min.
  5. Verificar que STBY queda en bajo y los motores no se mueven durante el arranque del ESP32 (encender 10 veces con los motores conectados).
- *Criterio:* 5 V mínimo ≥ 4.75 V; 3V3 mínimo ≥ 3.0 V; **0 reinicios en 60 ciclos**; ningún movimiento al encender; MP1584 < 60 °C.
- **Por qué importa más en B:** los picos de los motores hunden directamente la batería que alimenta al MP1584.

**P4 — Inductancia y rizado:** medir L con un medidor LCR (laboratorio). Si no hay: corriente promedio con ciclo de 71 % a 8.4 V contra 100 % a 6 V (debe diferir ≤ 10 %); osciloscopio en una resistencia de 0.1 Ω en serie si está disponible.

**P5 — Caída de la batería:** `bat` en reposo y con los dos motores al máximo (ruedas en el aire); R_pack = ΔV / ΔI. Criterio: caída ≤ 0.3 V.

**P6 — Temperaturas:** 5 min de marcha continua; driver, motores y regulador < 60 °C.

**P7 — Compensación (solo B):** RPM con la batería a 8.4 V y a 7.0 V con el mismo comando; diferencia ≤ 5 %.

**P8 — Voltaje de VM al frenar (A3 y B):** osciloscopio en VM durante `m 1 1` → `m 0.2 0.2` y durante el paro; registrar el máximo. Criterio: ≤ 10 V (margen hasta los 13.5 V recomendados). En A3, si sube, agregar capacitor o carga de descarga.

## 11. Comparación final

| Criterio | A1 MP1584 6 V | A2 D24V22F6 | A3 buck-boost AR4790 | B directo + compensación |
|---|---|---|---|---|
| Dentro de su ficha | **No** | Sí hasta 6.4-6.9 V de batería | Sí | Sí |
| Límite de 6 V independiente del software | Sí, pero fuera de especificación | Sí | **Sí** | **No** (depende del software) |
| Velocidad durante la descarga | Incierta | Cae al final | Constante | Constante, si el software funciona |
| Rizado y picos de corriente | Menores | Menores | Menores | Mayores (según L) |
| Energía regenerativa (si existe) | Atrapada en la línea de motores | Atrapada | **Atrapada** (salida anti-reflujo) | Puede ir a la batería |
| Efecto de los motores en la lógica | Aislado por el regulador | Aislado | Aislado | **Directo**: P3 es crítica |
| Masa / espacio | ~2 g / pequeño | 2.3 g / 18 × 18 mm | **41.7 g / 66 × 48 mm** | 0 |
| Costo de potencia para motores | $19 | Pendiente (sin proveedor en México) | **$144** (+$125 sobre A1) | **$0** (−$19) |

## 12. Recomendación (C2 sigue pendiente de tu aprobación)

**Recomendación: B, condicionada a P1 y P3; A3 como alternativa.**
- B iguala a A en promedio (par, RPM, respuesta del PD), mantiene la velocidad durante la descarga, no agrega 42 g ni ocupa 16 % de la huella, y ahorra $19.
- Su debilidad real, que la versión 1 no dejaba clara: **el límite de 6 V depende del software** y los picos de corriente dependen de una inductancia desconocida.
- Si prefieres un límite independiente del firmware, o si P1 da Is6 > 1.0 A o P3 muestra reinicios, la opción correcta es **A3** (+$125, +42 g).
- **A1 no se recomienda** (fuera de su ficha) y **A2** deja de regular al final de la descarga.

Esto se puede decidir **después** de P1 y P3. Las piezas para B ya están en la BOM; A3 solo agrega un módulo de UNIT ($144, 155 en existencia).

**Decisión que te toca aprobar (cuando quieras, no ahora):**
1. B, A3 o esperar a P1/P3.
2. Si eliges B: autorizar los cambios de firmware listados (bandera, segunda barrera de software en `hw::motores()`, 8.4 V por defecto si la lectura falla, rampa de comando con pruebas), sabiendo que son protecciones **dependientes del software**.
3. Sub-decisión C2.2: conservar el MP1584 de 5 V si pasa P3, o cambiarlo por un regulador de entrada baja.

## 13. Fuentes
- Toshiba TB6612FNG, ficha técnica: https://tams-www.informatik.uni-hamburg.de/lehre/2019ss/vorlesung/es/doc/tb6612fng.pdf · https://faculty-web.msoe.edu/johnsontimoj/Common/FILES/TB6612FNG.pdf
- UNIT GA12-N20: https://uelectronics.com/producto/ga12-n20-motorreductor-dc-3v-6v-12v/ · UNIT AR4790: https://uelectronics.com/producto/convertidor-boost-buck-5-5-30v-a-0-5-30v-4a-35w/
- Ficha GA12-N20 (100-450 RPM): https://alhammadi-ye.com/public/uploads/all/NJuJywfAyWrHfIhxznQWZXDWtMauaFENb17d1Df5.pdf
- Pololu micro motores 6 V: https://www.pololu.com/product/3067 · D24V22F6: https://pololu.com/product/2859/specs · S18V20F6: https://www.pololu.com/product/2575/specs
- MPS MP1584: https://www.monolithicpower.com/pub/media/document/MP1584_r1.1.pdf
- Espressif ESP-WROOM-32: https://universal-solder.ca/downloads/esp-wroom-32_datasheet_en.pdf
- Celda LiPo de referencia: https://e2e.ti.com/cfs-file/__key/communityserver-discussions-components-files/196/GRP704230_2D00_3.7V_2D00_835mAh-cell-spec.pdf
