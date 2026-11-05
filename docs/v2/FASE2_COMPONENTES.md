# V2 · Fase 2 — Selección de componentes

Fecha: 4 nov 2026 · Rama `engineering/final-robot-v2` · **Aprobada** (actualizada en la Fase 3.5, 5 nov 2026: reglas
oficiales, motor del ventilador, límite de corriente y cambios de componentes de la Fase 3, ver §0).

Marcas de tipo que usa esta página: **[V]** verificado documentalmente (hoja de datos o página del fabricante, §11) ·
**[C]** calculado (`sim/v2/fase2_motores.py`, tablas T10-T11, o aritmética mostrada) · **[E]** estimado · **[S]** supuesto de
diseño · **[P]** pendiente de medición física. Ningún componente de esta página se ha comprado, armado ni medido.

## 0. Actualización de la Fase 3.5

- **Reglas oficiales** (FASE1_AUDITORIA §4): succión permitida; los 500 g se pesan con el robot **apagado** (la succión no
  cuenta); el faldón puede estar cerca de la pista si **nunca** la toca; mapas permitidos (la pista puede cambiar entre
  rondas); **comunicación inalámbrica prohibida** (R10).
- **Ventilador**: motor brushless **1104 ~9000 KV** con **ESC comercial de 20 A** (opción B de §2.2), indicación del
  usuario [S]. Hasta la prueba de báscula, los cálculos usan una presión de cierre **conservadora de 500 Pa** (fase35.py).
- **Límite de corriente de los puentes H**: ITRIP bajado de ≈ 2.4 A a **≈ 1.56 A** por motor (VREF 1.055 V) y límite de
  frenado de **1.5 A** en el firmware con estimador térmico; ver `FASE35_CORRECCIONES.md` §3. Los 2.35 A de frenado por
  inversión de §2.1 son lo que el motor PEDIRÍA a 2 m/s; la adherencia solo aprovecha ≤ 1.57 A aun con 3.1 N de succión.
- **Componentes cambiados en la Fase 3** (FASE3_ENTREGA1 §3): MCU en módulo WeAct STM32G474CEU6; IMU ISM330DHCX en lugar
  de ICM-42688-P; 2 × LPS22DF en lugar de 2 × BMP390; piezo Murata PKLCS1212E4001-R1 en lugar del zumbador magnético; USB-C
  del módulo.

## 1. Requisitos nuevos (respuestas oficiales) y qué cambian

| Fuente | Respuesta o requisito | Consecuencia en la selección |
|---|---|---|
| Organizadores 1 | Ventilador (succión) permitido | Se diseña con succión. Mando del ventilador, supervisión de presión y modo degradado "sin succión" |
| Organizadores 2 | Los 500 g se pesan con el robot **APAGADO** antes de la ronda | La succión no cuenta como peso: el "peso aparente" (518 g con 3.1 N y 200 g) deja de ser un riesgo. El tope de masa propio sigue en 200 g por física (T3b), no por reglamento |
| Organizadores 3 | Mapas permitidos sin radio, pero la pista puede cambiar entre rondas | El mapa se aprende **en cada ronda** (vuelta 1 reactiva y mapeando, vueltas 2-3 con el mapa y validación continua; si no coincide, vuelve a reactivo). Pide giroscopio, encoders con buena resolución y RAM |
| Organizadores 4 | Cámara de succión permitida si el faldón **nunca** toca la pista | Ranura de diseño 0.5 mm **con la succión encendida** (las llantas se comprimen con la carga extra) [P]; faldón rígido; el sensor de presión detecta una ranura abierta |
| R10 / organizadores | Comunicación inalámbrica prohibida | Sin radio en el robot; ajustes y registros por USB-C entre rondas |
| Profesor | Botón físico de arranque | START dedicado (R08), separado de CAL y RESET |
| Profesor | Calibración + colocación ≤ 15 s | Calibración **manual** por barrido (el reglamento C03 prohíbe que el robot se mueva solo antes de la señal), con confirmación por LED y sonido. Cero de presión e IMU en la misma ventana |
| Profesor | Sensores lo más bajo posible, con "cachucha" | Se conservan los QRE1113GR (cuerpo de 1.45 mm de alto [V]) y se montan más cerca del piso que en V1 (cara a 3.05 mm del piso en V1). La altura final y la cachucha se fijan en la Fase 3 |
| Profesor | Máquina de estados 100 % autónoma | Inicio, calibración, listo, siguiendo, recuperación, error (§7) |
| Profesor | LEDs y sonido por estado | 4 LED de estado + zumbador magnético de 100 dBA a 10 cm (a 5 V) [V] |
| Profesor | Reparación en 2 min | Motores con encoder integrado y conector; módulo del ventilador desmontable; barra de sensores separable (propuesta, §8) |
| Profesor | Ajustes en 20-30 min: reset y USB accesibles | USB-C en el borde (consola y parámetros sin abrir nada); RESET accesible |

**Sobre los 3.1 N**: es la fuerza **mínima calculada que hace falta** para que un robot reactivo de 200 g con μ 0.8 y la
succión sobre el eje llegue a 2.0 m/s (T3b) [C]. No es lo que el ventilador entrega: eso depende de la curva presión-caudal,
que no tengo, y de la ranura real. Tampoco está validado: μ es un supuesto [S] y nada se ha medido [P]. Con la masa que estima
esta fase (≈ 120-150 g, §6) el requisito baja a ≈ 2.3 N (T3b, 150 g) [C]. Se vuelve un dato seguro cuando la prueba de báscula de
`ANALISIS_VENTILADOR.md` §4 mida la fuerza con la cámara y la ranura reales.

## 2. Tabla de componentes

### 2.1 Núcleo (cálculo, sensores, tracción)

| Función | Selección (fabricante · número de parte) | Encapsulado | Especificaciones clave | Por qué | Alternativa |
|---|---|---|---|---|---|
| **Microcontrolador** | STMicroelectronics · **STM32G474MET6** | LQFP80, 12 × 12 mm, paso 0.5 mm [V] | Cortex-M4F 170 MHz; 512 KB flash con ECC en 2 bancos; 128 KB SRAM (96 + 32 CCM); **5 ADC de 12 bits a 4 Msps**; 7 comparadores; HRTIM 184 ps; USB 2.0 FS (PA11/PA12); 3 FDCAN; 1.71-3.6 V [V]. **66 I/O, 38 con entrada de ADC** (datos de pines de ST) [V] | Necesito 59 pines (§4): no caben en LQFP64 (52 I/O). Misma familia que V1: se reutiliza el firmware, la capa CMSIS y la cadena de compilación. 5 ADC leen los 16 sensores más corrientes y batería en menos tiempo que los 2 ADC de V1. 128 KB de RAM para el mapa de la vuelta | STM32G474RET6 (LQFP64, mismo silicio [V]) solo si se quitan 7 funciones; STM32G431RBT6 (LQFP64, 32 KB RAM [V]) no alcanza en pines ni en RAM |
| **Sensores de línea** ×16 | onsemi · **QRE1113GR** | SMD 4 pines (CASE 100CY), 3.2 × 2.6 × 1.45 mm [V] | LED IR 940 nm + fototransistor; I_F 50 mA máx. [V] | Los de V1, con hoja de datos y huella ya verificadas; el más bajo disponible del diseño V1. Resta de luz ambiente con emisores conmutados (R06) | Sin alternativa verificada en esta fase |
| Conmutador de emisores | Alpha & Omega · **AO3400A** | SOT-23 [V] | N 30 V 5.7 A [V]; 16 × ≈ 28 mA = 0.45 A [C] | Igual que V1 | — |
| **Motores** ×2 | Pololu · **#5183** "15:1 Micro Metal Gearmotor HPCB 6V with 12 CPR Encoder, Side Connector" | 10 × 12 × 32 mm + eje de 10 mm, 11 g [V] | Relación 15.25:1; a 6 V: 2100 rpm sin carga, 0.15 A sin carga, **0.25 kg·cm** y 1.5 A de bloqueo (extrapolados por Pololu), 1.3 W [V]. Encoder de cuadratura 12 CPR integrado [V]; si los 12 CPR son del eje del motor, como en los encoders magnéticos de Pololu (confirmar en la ficha), dan 183 cuentas por vuelta de rueda y 0.55 mm por cuenta con llanta de 32 mm [C] | Única opción del catálogo HPCB que cumple las dos condiciones de T10: llega a 2.0 m/s con margen (2.0 / 3.52 m/s = 57 % de la velocidad sin carga) y frena a 2.0 m/s más fuerte de lo que la adherencia permite (24.0 contra 15.8 m/s², 200 g) [C]. Se alimenta a 2S con el PWM limitado a **6 V efectivos** = tensión nominal: el par no cae cuando baja la batería | #5182 (mismo motor, conector atrás [V]); #5181 (10:1 6V, lateral [V]): frena 14.2 m/s² < 15.8, no cumple (T10) |
| **Puente H** ×2 (uno por motor) | Texas Instruments · **DRV8874** (pedido: DRV8874PWPR, nomenclatura TI PWP + R; confirmar en el anexo de empaque) | HTSSOP-16 PowerPAD (PWP), 5 × 6.4 mm [V] | 4.5-37 V; **6 A pico**; 200 mΩ (alto + bajo); modos PH/EN, PWM e independiente; **IPROPI** (espejo de corriente, sin resistencia de sensado); regulación de corriente por VREF sin el MCU; UVLO, OCP, TSD, nFAULT [V] | Al frenar por inversión a 2.0 m/s cada motor pide **2.35 A** [C]: el DRV8833 de V1 (1.5 A RMS por canal) no lo da. IPROPI da la corriente de cada motor al ADC: detección de bloqueo (C10, humo) y de patinaje | **DRV8876** (misma huella, 3.5 A pico, 700 mΩ [V]) como respaldo si falta el DRV8874 |
| **IMU** | TDK InvenSense · **ICM-42688-P** | LGA-14, 2.5 × 3 mm [V] | Giroscopio ±15.6 a ±2000 dps, ruido 2.8 mdps/√Hz; acelerómetro ±2 a ±16 g, 70 µg/√Hz; SPI 24 MHz, I2C 1 MHz, I3C; 1.71-3.6 V; 0.88 mA; FIFO 2 KB [V] | Rumbo para el mapa de la vuelta (curvatura = guiñada / distancia) y **detección de derrape** (guiñada del giroscopio contra la de los encoders): es la única forma de ver una pérdida de succión que la presión no explique (FASE1_FISICA §8, punto 5). Curva de R 150 mm a 1.1 m/s = 420 °/s [C]: rango ±1000 dps | ST **LSM6DSOXTR** (LGA-14 [V]; especificaciones por confirmar si se usa) |
| **Presión de la cámara** ×2 | Bosch Sensortec · **BMP390** | LGA-10 con tapa metálica, 2.0 × 2.0 × 0.75 mm [V] | 300-1250 hPa; precisión relativa ±0.03 hPa (= ±3 Pa); absoluta ±0.50 hPa; ruido 0.02 Pa RMS al menor ancho de banda; hasta 200 Hz; I2C y SPI; 1.65-3.6 V; deriva ±0.6 Pa/K [V] | Uno dentro de la cámara y otro afuera: ΔP = diferencia, con el cero hecho en la calibración (ventilador apagado) para quitar el error absoluto de ±50 Pa. Señal de 500-900 Pa contra ±3 Pa [C]. **Es lo único que ve el faldón gastado o un escalón de la pista** (T7: 54 % y 19 % de la succión) que RPM y corriente no ven. A 200 Hz hay 10 lecturas en τ = 50 ms, la caída más rápida de T7b [C]. Ruido a 200 Hz: se fija en la Fase 4 con la tabla de sobremuestreo | Sensor diferencial de ±1 kPa o más: no encontré uno verificado de tamaño similar |
| **Llantas** | Pololu · **#1087** (par 32 × 7 mm, silicón) | Ø32 × 7 mm, 6.24 g el par [V] | Eje en D de 3 mm (el de los motores #5183 [V]) | Las de V1; el diámetro de 32 mm es el de los cálculos T9/T10 | μ con succión y compresión de la llanta: [P] |

### 2.2 Ventilador (resuelto en la Fase 3: 1104 ~9000 KV + ESC de 20 A, opción B)

| Función | Selección | Estado |
|---|---|---|
| Rotor y montaje | Modelos entregados: rotor de 12 álabes radiales (r 10-17 mm) + base, 4 pilares y soporte | Se integran. Masa impresa en PA12: rotor 2.0 g, montaje 3.6 g [C con el volumen de las mallas y densidad 1.01 g/cm³ [S]] |
| **Motor del ventilador** | **Brushless 1104 ~9000 KV** (indicación del usuario, Fase 3) [S] | El soporte tiene 4 agujeros Ø2.2 sobre un círculo de Ø9 mm y paso central Ø5 [medido en el modelo]: es compatible con los motores sin escobillas clase 11xx de patrón de 9 mm y tornillos M2 [V: TuneRC 1104, Darwin 1104]. **Necesito modelo, KV y número de polos** |
| **Mando del ventilador** | **Opción A**: TI **MCT8316AV** (VQFN-40 RGF, 7 × 5 mm; I2C con EEPROM) [V] en la placa. **Opción B**: módulo ESC comercial con firmware AM32/BLHeli_S/Bluejay, mando DShot (telemetría de RPM bidireccional) o PWM | Decide la frecuencia eléctrica f_e = pares de polos × rpm / 60 (T11) [C]. El MCT8316A llega a **3 kHz** eléctricos [V]: con un motor 9N12P (6 pares, típico de 11xx [V: Darwin 1104]) eso es **30 000 rpm, justo el mínimo estimado** (30 000-40 000 rpm) **sin margen**; con 12N14P, 25 700 rpm: no alcanza. **Recomiendo B** si el motor es 11xx de 12 o 14 polos; A solo si f_e ≤ 2.5 kHz a las rpm de trabajo (margen de ≈ 17 % [S]). El MCF8316A (control FOC) queda descartado: 1.5 kHz |

La opción B usa un módulo de controlador, que el reglamento acepta como componente (R04: "módulos sueltos (sensor, driver, MCU)
son componentes" [V, `REGLAMENTO_MATRIZ.md`]). El modelo exacto del ESC se elige con el motor: 2S, corriente continua ≥ 2 × la del
motor a plena carga, DShot bidireccional deseable. Va con el motor como un solo módulo intercambiable (§8).

### 2.3 Interfaz con el operador y mantenimiento

| Función | Selección (fabricante · número de parte) | Encapsulado | Especificaciones clave | Por qué |
|---|---|---|---|---|
| **Botón START** (R08) | Omron · **B3FS-1000P** | SMD 6 × 6 × 3.1 mm [V] | 24 V DC, 50 mA [V] | El de V1, grande y con recorrido claro; START solo arranca, nunca calibra |
| Botón CAL | Omron · **B3FS-1000P** | igual | igual | Separado de START para no arrancar por error durante los 15 s |
| **Botón RESET** | Omron · **B3U-1000P** | SMD 3.0 × 2.5 × 1.6 mm [V] | 12 V DC, 50 mA [V] | El de V1; va al pin NRST, en un borde accesible (Fase 3) |
| **LED de estado** ×4 | Kingbright · **APT1608SGC** (verde ×2: ESTADO y SUCCIÓN), **APT1608YC** (amarillo), **APT1608EC** (rojo) | 0603 (1.6 × 0.8 mm) [V] | Verde y rojo de V1; amarillo de la misma serie [V] | Colores que funcionan con 3.3 V (se evitó el azul: su caída directa es cercana a 3.3 V) [E]. Significado en §7 |
| LED de alimentación | Kingbright · **APT1608SGC** | 0603 | — | Como V1: 3.3 V presente |
| **Zumbador** | CUI Devices (Same Sky) · **CMT-8540S-SMT-TR** | SMD 8.5 × 8.5 × 4.0 mm, 0.8 g [V] | Transductor magnético de **mando externo**; 5.0 V nominal, 1-6 V de operación; 150 mA a 5 V; bobina 13 Ω; 4 kHz; **100 dBA a 10 cm** a 5 V [V] | Mando externo = el MCU elige el tono (un tono por estado). Con 3.3 V suena ≈ 3.6 dB menos que a 5 V [E]; se enciende con un AO3400A y diodo de rueda libre (número de parte del diodo en la Fase 3) |
| **USB-C** | GCT · **USB4105-GF-A** | Receptáculo USB 2.0 tipo C de ángulo recto, SMD con postes de orificio pasante [V] | 16 contactos de señal [V]; CC con 2 × 5.1 kΩ a tierra (dispositivo) | Ajustes en los 20-30 min sin abrir nada: consola, parámetros, registros de la vuelta. Postes pasantes = resiste tirones del cable |
| Protección ESD del USB | STMicroelectronics · **USBLC6-2SC6** | SOT-23-6 [V] | 2 líneas, 3.5 pF máx., 5 V de trabajo [V] | Conector expuesto en el borde |
| Programación SWD | Harwin · **M50-3500742** + ST **STLINK-V3MINIE** | 2 × 7, paso 1.27 mm [V] | Como V1 | Programación garantizada aunque falle el USB. Cargador DFU por USB del G474: **por confirmar en AN2606** (no pude leer la sección del G47x) |
| Cristal HSE 8 MHz | número de parte en la Fase 3 | — | PF0/PF1 [V] | Exactitud del reloj del USB y del cargador DFU sin depender del oscilador interno |

### 2.4 Energía

| Función | Selección | Estado |
|---|---|---|
| Batería | Tattu · TA-75C-450-2S1P-L-XT30 (LiPo 2S 450 mAh 75C) [V] | Se conserva. 75C × 0.45 Ah = 33.8 A nominales del vendedor contra ≈ 8 A pico estimados (§5) |
| Conector de batería | Amass · XT30UPB-M [V] | Se conserva (15 A) |
| Reductor 3.3 V | TI · TPS563200DDCR (3 A, 4.5-17 V) [V] | Se conserva: ≈ 0.75 A pico en 3.3 V (§5) [E] |
| Interruptor de encendido | C&K · OS102011MA1QN1 [V] | Se conserva (solo conmuta la compuerta) |
| TVS de la alimentación | Littelfuse · SMAJ9.0A [V] | Se conserva |
| MOSFET P de protección y encendido | **Reemplazar** los AO3401A de V1 (−4 A [V]) | Requisito: ≥ 10 A continuos, R_DS(on) ≤ 20 mΩ, encapsulado DFN 3 × 3 o similar. Número de parte en la Fase 3 |
| Fusible | **Reemplazar** el PTC de 1.5 A de V1 [V] | Requisito: ≈ 10 A, que no actúe con el pico de frenado (≈ 8 A) y sí con un corto. Número de parte en la Fase 3 |
| USB como alimentación de la lógica | Diodo-OR a la entrada del reductor (no a los motores) | Permite ajustar parámetros con la batería quitada; motores y ventilador quedan sin energía (Fase 3) |

## 3. Por qué esta selección es mejor que V1

1. **Tracción** [C, T10, 200 g]. Con el motor de V1 a 2S (0.105 kg·cm), el robot acelera 4.4 m/s² al salir de una curva a
   1.1 m/s y frena 10.1 m/s² desde 2.0 m/s. Con los #5183 a 6 V efectivos: **10.5 m/s² y 24.0 m/s²**. Con la succión, la llanta
   ya puede frenar 15.8 m/s²: con V1 el motor sería el límite y la succión se desperdiciaría; con V2 el límite vuelve a ser la
   llanta, que es lo que el firmware sabe controlar. La velocidad sin carga es la misma (3.5 m/s): no se pierde velocidad punta.
2. **Tensión constante en los motores**. El tope de 6 V efectivos se mantiene hasta 6.4 V de batería bajo carga [S]: el
   comportamiento del robot no cambia entre la primera y la tercera vuelta (V1 dependía de la carga de la batería).
3. **Puente H con margen y medición**. 6 A pico contra 2.35 A pedidos [C], frente a 2 A del DRV8833. IPROPI por motor da
   detección de bloqueo (C10) y limita la corriente por hardware aunque el firmware falle.
4. **Supervisión real de la succión**. V1 no tenía succión. V2 no confía en ella a ciegas: presión de la cámara (BMP390 ×2),
   derrape (IMU contra encoders) y estado del ventilador (RPM o telemetría). Cubre los 7 fallos de T7, incluidos los dos que
   RPM y corriente no ven (faldón gastado, escalón de la pista).
5. **Mapa en cada ronda**. El IMU y los encoders de 183 cuentas por vuelta de rueda permiten mapear la vuelta 1 y usarla en
   las vueltas 2-3; la RAM del G474 (128 KB contra 32 KB) guarda el mapa y el registro.
6. **Más pines y ADC**. 59 funciones caben en 66 I/O con 7 libres; V1 ya estaba casi lleno con 48 pines (FASE1_AUDITORIA §3).
7. **Operación en competencia**. START, CAL y RESET separados; 4 LED y zumbador para cada estado (V1: 2 LED, sin sonido); USB-C
   en el borde para ajustar sin herramienta especial; motores con encoder integrado y conector (V1 tenía encoders en kit aparte).
8. **Masa**. ≈ 120-150 g estimados [E] contra el tope de 200 g: cada 50 g menos baja ≈ 0.8 N el requisito de succión (T3b).

## 4. Presupuesto de pines del STM32G474MET6 [C]

| Función | Pines | Función | Pines |
|---|---|---|---|
| 16 sensores de línea (ADC) | 16 | IMU (SPI + INT1) | 5 |
| Batería (ADC) | 1 | I2C (2 × BMP390) | 2 |
| IPROPI × 2 (ADC) | 2 | Compuerta de emisores | 1 |
| Corriente del ventilador (ADC, reserva) | 1 | START y CAL | 2 |
| DRV8874: EN y PH × 2 | 4 | LED de estado | 4 |
| DRV8874: nSLEEP común, nFAULT × 2 | 3 | Zumbador (temporizador) | 1 |
| Encoders A/B × 2 (temporizadores) | 4 | USB D−/D+ (PA11/PA12) | 2 |
| Ventilador: mando, RPM o telemetría, falla | 3 | SWD (SWDIO, SWCLK, SWO) | 3 |
| USART a la consola del STLINK | 2 | HSE (PF0/PF1) y BOOT0 (PB8) | 3 |
| **Total** | **59 de 66** (20 analógicos de 38 posibles) | LQFP64 | 52: no cabe |

La asignación concreta de pines (ADC, temporizadores, DMA) se hace en la Fase 3.

## 5. Corrientes pico de la batería [E salvo indicación]

| Carga | Pico | Origen |
|---|---|---|
| Motores, frenado por inversión a 2.0 m/s | 2 × 2.35 A | [C] T10; la regulación del DRV8874 lo limita |
| Ventilador | 0.7-2.7 A | Barrido de la Fase 1 (5-20 W a 7.4 V); el real depende del motor que falta |
| Lógica (3.3 V: emisores 0.45 A, zumbador ≤ 0.25 A, MCU, IMU, LED) | ≈ 0.4 A en la batería | ≈ 0.75 A en 3.3 V a través del reductor |
| **Total** | **≈ 6-8 A** | Dimensiona MOSFET, fusible, pistas y conector |

## 6. Presupuesto de masa (tope de diseño 200 g)

| Elemento | Masa | Tipo |
|---|---|---|
| 2 motores #5183 | 22.0 g | [V] |
| Llantas #1087 | 6.2 g | [V] |
| Batería Tattu 450 mAh 2S | 28.4 g (la tabla del vendedor dice 37 g ±20) | [V] del vendedor; [P] |
| Rotor (PA12) + montaje entregado | 2.0 + 3.6 g | [C] (con rotor de acero serían 15.6 g) |
| Motor del ventilador clase 11xx | 5-6 g | [E] (Darwin 1104 5.9 g, TuneRC 1104 5.1 g [V]) |
| ESC (opción B) | 2-4 g | [E] |
| Cámara y faldón | 8-12 g | [E] |
| PCB-chasis | 25-35 g | [E] (V1: 35.1 g con 130 × 92 mm) |
| Componentes electrónicos y conectores | 6-8 g | [E] |
| Cachucha de sensores, apoyo delantero | 4-6 g | [E] |
| Tornillos, cables, sujeción | 6-8 g | [E] |
| **Total** | **≈ 120-150 g** | [E] |

## 7. Indicaciones de la máquina de estados

| Estado | LED | Sonido | Qué hace |
|---|---|---|---|
| INICIO | amarillo fijo | pitido corto | Autoprueba: batería, IMU, presión (lectura de los dos sensores), encoders, driver (nFAULT). Si algo falla, pasa a ERROR |
| CALIBRACIÓN (CAL) | amarillo parpadeo rápido | tono ascendente si sale bien; descendente si el contraste no alcanza | Barrido **manual** sobre la línea (C03: el robot no se mueve solo), cero de presión con el ventilador apagado, sesgo del giroscopio. Meta ≤ 10 s [S], dentro de los 15 s |
| LISTO | verde parpadeo lento | — | Espera START (R08) |
| SIGUIENDO | verde fijo; SUCCIÓN verde fijo si ΔP está en su ventana | silencio | Arranca el ventilador con las ruedas frenadas, confirma la presión y suelta los motores. Vuelta 1 mapeando, 2-3 con mapa. Si la succión falla: perfil sin succión y LED SUCCIÓN parpadeando |
| RECUPERACIÓN | verde y amarillo alternando | pitidos rápidos | Línea perdida o derrape: frena dentro del círculo de fricción y busca la línea (≤ 0.3 s, C07) |
| ERROR | rojo, número de parpadeos = código | tono grave | Motores y ventilador apagados. Batería baja, motor bloqueado, sensor de presión o IMU sin respuesta |

## 8. Reparación en 2 minutos y ajustes entre rondas

| Pieza que más se daña | Cómo se cambia | Estado |
|---|---|---|
| Motor y encoder | #5183 con conector lateral: cable JST SH de 6 pines (como V1, Pololu #4765 [V]) y 2 tornillos del soporte | Seleccionado |
| Llanta | A presión en el eje en D | Seleccionado |
| Batería | XT30 + sujeción positiva (C09: piezas de más de 10 g no pueden caerse) | Seleccionado |
| Ventilador | Módulo (base, pilares, soporte, motor y ESC): 4 tornillos y 2 conectores (potencia y señal) | Conectores en la Fase 3 |
| Barra de sensores | **Propuesta**: barra en una PCB aparte, unida al cuello con 2 tornillos y un conector; se cambia completa y además permite fijar su altura independiente del chasis | **Necesita tu aprobación** (agrega un conector de ≈ 20 vías) |
| Faldón | Pieza impresa atornillada; repuesto en el kit de pits | Fase 3 |

Ajustes entre rondas (20-30 min): por USB-C, sin abrir el robot: velocidades, crédito de succión, ganancias y registro de
la ronda anterior (presión, RPM, derrapes).

## 9. Comparación V1 contra V2

| Aspecto | V1 (`engineering/speed-follower`) | V2 (esta propuesta) |
|---|---|---|
| Concepto | Sin succión | Succión con cámara y faldón sin contacto, centrada en el eje motriz |
| Velocidad de diseño | 0.8165 m/s máx. (5.81 s simulados por vuelta) | Meta 2.0 m/s con ≥ 3.1 N (200 g) o ≈ 2.3 N (150 g) de succión [C]; sin succión ≈ 1.2 m/s |
| Microcontrolador | STM32G431CBT6, LQFP48, 32 KB RAM, 2 ADC | **STM32G474MET6**, LQFP80, 128 KB RAM, 5 ADC, 66 I/O |
| Motores | Pololu #3048, 10:1 HPCB 12V a 2S: 0.105 kg·cm | **Pololu #5183**, 15.25:1 HPCB 6V a 6 V efectivos: 0.25 kg·cm |
| Aceleración al salir de una curva (1.1 m/s, 200 g) | 4.4 m/s² [C] | **10.5 m/s²** [C] |
| Frenado por inversión a 2.0 m/s (200 g) | 10.1 m/s² [C] | **24.0 m/s²** (la llanta limita a 15.8 con succión) [C] |
| Encoders | Kit aparte #4760, 12 CPR | Integrados en el motor, 12 CPR, 183 cuentas por vuelta de rueda |
| Puente H | 1 × DRV8833 (1.5 A RMS por canal) | **2 × DRV8874** (6 A pico, IPROPI, regulación de corriente) |
| Sensores de línea | 16 × QRE1113GR, cara a 3.05 mm del piso | 16 × QRE1113GR más bajos, con cachucha |
| IMU | No | **ICM-42688-P** |
| Presión de la cámara | No | **2 × BMP390** |
| Ventilador | No | Rotor y montaje entregados + motor pendiente + mando A (MCT8316AV) o B (ESC) |
| Botones | START, CAL, RESET | Igual |
| Indicación | 2 LED verdes + 1 rojo, sin sonido | 4 LED de estado + LED de 3.3 V + **zumbador de 100 dBA** |
| Programación y ajustes | Solo SWD + puerto serie del STLINK | **USB-C** en el borde + SWD |
| Protección de la alimentación | MOSFET de 4 A, PTC de 1.5 A | ≥ 10 A (Fase 3) |
| Reparación | Motores con cable; batería con XT30 | + motores con encoder integrado, módulo de ventilador, barra separable (propuesta) |
| Masa | 112.9 g (CAD) | ≈ 120-150 g [E] |
| Mapa | No | Por ronda, con validación continua |

## 10. Cierre de la Fase 2 (resuelto)

1. **Motor del ventilador**: 1104 ~9000 KV con ESC comercial de 20 A (opción B). Resuelto por el usuario.
2. **Barra de sensores separable**: aprobada.
3. **Calendario**: la competencia es el 21 de noviembre. Fabricar y enviar la PCB, armar y hacer las pruebas físicas
   en ese plazo es el riesgo principal del proyecto. Todo lo elegido es de catálogo; el ESC en módulo evita diseñar un controlador.

Reproducir T10 y T11: `python3 sim/v2/fase2_motores.py` (datos en `config/v2/parametros_fase2.yaml`).

## 11. Fuentes

- Pololu, tabla de motorreductores micro metal: <https://www.pololu.com/category/60/micro-metal-gearmotors>; #5183:
  <https://www.pololu.com/product/5183/specs>
- STMicroelectronics: <https://st.com/en/microcontrollers-microprocessors/stm32g474re.html>,
  <https://st.com/en/microcontrollers-microprocessors/stm32g474me.html>; pines por encapsulado (ST open pin data):
  <https://github.com/STMicroelectronics/STM32_open_pin_data> (`STM32G474M(B-C-E)Tx.xml`, `STM32G474R(B-C-E)Tx.xml`,
  `STM32G431R(6-8-B)Tx.xml`)
- Texas Instruments: <https://www.ti.com/product/DRV8874>, <https://www.ti.com/product/MCT8316A>
- TDK ICM-42688-P (hoja de datos): <https://en.sekorm.com/doc/3922353.html>; encapsulado: <https://www.lcsc.com/product-detail/C1850418.html>
- Bosch BMP390: <https://bosch-sensortec.com/products/environmental-sensors/pressure-sensors/bmp390>
- CUI Devices CMT-8540S-SMT (hoja de datos): <https://cdn.eicom.ru/media/PDF/3650547.pdf>
- GCT USB4105-GF-A: <https://www.digikey.com/en/products/detail/gct/USB4105-GF-A/11198441>
- ST USBLC6-2SC6 (hoja de datos): <https://elcodis.com/parts/140811/USBLC6-2SC6_p2.html>
- Kingbright APT1608YC: <https://datasheets.globalspec.com/ds/kingbright/apt1608yc/f40b7d73-ea4b-4b75-9d19-02b2785d6ad2>
- Motores 1104 de referencia para el patrón de montaje: <https://darwinfpv.com/products/darwin-1104-4300kv-brushless-motor>,
  <https://pyrodrone.com/products/tunerc-1104-3600kv-brushless-motor>
- Componentes que se conservan de V1: fuentes en `docs/BOM_FINAL.csv`
