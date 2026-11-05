# V2 · Fase 3, entrega 1 — Esquemáticos, barra de sensores lista para fabricar y CAD mecánico

Fecha: 5 nov 2026 · Rama `engineering/final-robot-v2` · **Para revisión.**

Tipos de dato: **[V]** verificado documentalmente · **[C]** calculado (script del repositorio) · **[E]** estimado ·
**[S]** supuesto de diseño · **[P]** pendiente de medición física. Nada se ha fabricado, armado ni medido.

## 1. Qué contiene esta entrega

| Pieza | Estado | Archivos |
|---|---|---|
| **Barra de sensores** (PCB separable) | **Lista para pedir**: esquemático, PCB enrutada, ERC 0, DRC 0 errores (2 avisos), paridad esquemático-PCB, conectividad 41 redes / 183 pads | `hardware/v2/electronica/kicad/barra_sensores/`, paquete en `hardware/v2/electronica/fabricacion/barra_sensores/` |
| **PCB principal** (módulo WeAct en zócalos) | **Esquemático** completo, ERC 0, conectividad 64 redes / 293 conexiones. La PCB (colocación final, ruteo, Gerbers, pick and place) es la entrega 2 | `hardware/v2/electronica/kicad/principal/`, `fabricacion/principal_esquematico.pdf`, `fabricacion/principal/BOM.csv` |
| **CAD mecánico** | Chasis con cámara de 70 × 70 mm, alojamiento del ventilador del usuario, cachucha, soportes de motor, bahía del ESC, portabaterías, rueda loca, postes de la PCB. **Sin interferencias** (sólidos y mallas reales del ventilador). Masa y CG calculados | `hardware/v2/mecanica/` (STEP, STL, planos, vistas) |

Regenerar: `hardware/v2/electronica/generar.sh barra`, `hardware/v2/electronica/generar.sh principal`,
`python3 hardware/v2/mecanica/cad/generar_cad_v2.py`. Parámetros: `config/v2/robot_v2.yaml`.

## 2. Decisiones de arquitectura (para el calendario de 16 días)

1. **Chasis impreso, no PCB-chasis.** V1 usaba la PCB como chasis; en V2 la estructura es una pieza impresa que el equipo
   puede imprimir localmente en un día. Así el robot no depende de que llegue una PCB grande, y el mismo chasis acepta el
   plan B armado a mano si la PCB principal se retrasa (mismos agujeros y posiciones).
2. **Dos PCB pequeñas de 2 capas**: la barra de sensores (para pedir ya) y la principal (≈ 48.5 × 70 mm) con el módulo
   **WeAct STM32G474CEU6 Core Board** en zócalos, como pediste.
3. **Multiplexores en la barra**: con el módulo de 48 pines no alcanzan los pines para 16 entradas analógicas directas. Dos
   74HC4051 llevan las 16 señales al MCU por 2 hilos analógicos + 3 de selección; el cable a la barra queda en **8 hilos**
   (JST SH, cambio en segundos). Lectura: 2 ADC en paralelo × 8 canales; el tiempo lo fija la respuesta del fototransistor,
   no el multiplexor [E].
4. **Ventilador del usuario sin modificar**: base, pilares, soporte y rotor se atornillan al chasis tal como están. El
   motor 1104 (~9000 KV, supuesto por ti) va colgado bajo el soporte con el rotor en su campana y el ojo hacia la base
   (así encaja la geometría: 1.2 mm entre el rotor y la base) [C con las mallas].
5. **ESC comercial** (opción B): bahía en el chasis detrás de los motores, señal por cabecera de servo y potencia por pads.

## 3. Cambios respecto a la Fase 2 (y por qué)

| Fase 2 | Fase 3 | Motivo |
|---|---|---|
| STM32G474MET6 soldado (LQFP80) | Módulo **WeAct STM32G474CEU6 Core Board** en zócalos | Tu instrucción (plan B). Mismo silicio G474: 170 MHz, 128 KB RAM, 512 KB flash [V] |
| USB-C GCT USB4105-GF-A + USBLC6-2SC6 | **USB-C del módulo** | El módulo ya lo trae; queda en el borde trasero. DFU confirmado en AN2606 (G47x: USB DFU por PA11/PA12 con HSI48 + CRS, sin pull-up externo) [V] |
| ICM-42688-P | **ST ISM330DHCXTR** (LGA-14 2.5 × 3 × 0.86 mm, ±125-4000 dps, ±2-16 g, I2C/SPI, activo) [V] | Era la alternativa de la misma clase. Tiene símbolo y huella oficiales de KiCad; del ICM-42688-P no pude verificar el orden de pines con una fuente confiable y no quise dibujar una huella supuesta |
| 2 × BMP390 | **2 × ST LPS22DFTR** (260-1260 hPa, ±0.2 hPa absoluto, ruido 0.34 Pa, 200 Hz, I2C) [V] | Mismo motivo: huella oficial verificable (ST HLGA-10 2 × 2 mm). Igual de útil para la diferencia cámara-ambiente |
| Zumbador magnético CUI CMT-8540S | **Piezo Murata PKLCS1212E4001-R1** (excitación externa, 4 kHz) [V] | No pude confirmar qué pads del magnético son los terminales. El piezo tiene 2 pads (sin polaridad) y huella oficial; se excita de 0 a VBAT (≈ 8 V) para que suene más que a 3.3 V |
| MOSFET de protección "≥ 10 A, por elegir" | **Diodes DMP3013SFV-7** × 2 (−30 V, −12 A, 9.5 mΩ, VGS ±25 V) [V] | Cumple el requisito de la Fase 2 |
| Fusible "≈ 10 A, por elegir" | **Littelfuse 0297010.WXNV** (MINI 297, 10 A 32 V, rápido) [V] | Cumple el requisito; soldado directo |
| — | **onsemi MBR0540T1G** entre VBAT y el reductor | Con el USB conectado y la batería apagada, el 3.3 V del módulo no alimenta al ESC ni a los puentes H a través del reductor |
| 4 LED de estado | 3 LED (verde, amarillo, rojo) + el LED azul del módulo (PC6) para SUCCIÓN | Pines del módulo |

## 4. Barra de sensores (lista para pedir)

- 16 × onsemi QRE1113GR en la **cara inferior**, arco de **R 125 mm** con paso de 5.5 mm (±18.9°, |y| ≤ 40.5 mm); con
  la barra de 1.6 mm bajo la placa del chasis, **la cara de los sensores queda a 2.05 mm del piso** (V1: 3.05 mm) [C].
- Todo lo demás en la **cara superior** (2 × Nexperia 74HC4051PW,118 [V], 16 × 75 Ω, 16 × 10 kΩ, AO3400A, conector JST SH
  BM08B-SRSS-TB): la cara inferior queda libre para la cachucha.
- Placa: 2 capas, 1.6 mm, sector anular R 100-130 mm recortado a 90 mm de ancho; planos de GND en ambas caras.
- Conector J1 (8 vías, mismo orden que J2 de la PCB principal, cable 1:1): 1 +3V3 · 2 EMIT · 3 S0 · 4 S1 · 5 S2 · 6 SENS_A ·
  7 SENS_B · 8 GND.
- Canales (para el firmware): S1-S8 → SENS_A canales 0-7; S9-S16 → SENS_B canales 7-0 (S1 es el sensor más a la izquierda).

**Pedido (JLCPCB u otro):** `barra_sensores_gerbers.zip` (cobre, máscara, serigrafía, pasta, contorno y taladros PTH/NPTH
separados). Parámetros: 2 capas, FR-4, 1.6 mm, cobre 1 oz, pista y separación mínimas 0.15 mm, vía 0.6/0.3 mm.
- **Ensamblado por el fabricante**: `BOM.csv` y `CPL_JLCPCB.csv` (57 posiciones, superior e inferior). Hay que asignar los
  códigos del catálogo del fabricante a cada número de parte (no los busqué, por tu instrucción de no buscar tiendas) y
  **revisar las rotaciones en su vista previa**: las del CPL son las de KiCad. Ensamble en las dos caras.
- **A mano**: 57 piezas; los 16 sensores en la cara inferior (4 pads cada uno, pin 1 marcado).

Verificación: ERC 0; DRC 0 errores, 0 pads sin conectar, 2 avisos de tramo colgante de Freerouting (no afectan la
conexión); paridad esquemático-PCB sin diferencias.

## 5. PCB principal: esquemático

Bloques: XT30 → fusible 10 A → 2 × DMP3013SFV espalda con espalda (inversión de polaridad + encendido por el interruptor
deslizante, como V1) → TVS SMAJ9.0A y 2 × 22 µF → reductor TPS563200 a 3.3 V (circuito de V1) → módulo, sensores y lógica.
Puentes H: 2 × TI DRV8874PWPR en modo PH/EN (PMODE a GND), VCP 100 nF a VM, CPH-CPL 22 nF, IPROPI con 1.5 kΩ:
**ITRIP = VREF / (R_IPROPI × A_IPROPI)**; en la Fase 3.5 se bajó de 2.4 A a **1.056 V / (1.5 kΩ × 450 µA/A) ≈ 1.56 A por
motor** [C] tras la revisión térmica (`FASE35_CORRECCIONES.md` §3).

**Asignación de pines del módulo** (cada pin con el periférico que necesita según los datos de pines de ST [V]):

| Función | Pin | Periférico | Función | Pin | Periférico |
|---|---|---|---|---|---|
| SENS_A (mux 1) | PA0 | ADC1_IN1 | EN izquierdo (PWM) | PA10 | TIM1_CH3 |
| SENS_B (mux 2) | PA1 | ADC2_IN2 | EN derecho (PWM) | PA9 | TIM1_CH2 |
| Batería | PA2 | ADC1_IN3 | PH izquierdo / derecho | PC10 / PB5 | GPIO |
| IPROPI izquierdo | PA3 | ADC1_IN4 | nSLEEP / nFAULT (comunes) | PB4 / PB12 | GPIO |
| IPROPI derecho | PB2 | ADC2_IN12 | Encoder izquierdo A/B | PB6 / PB7 | TIM4 CH1/CH2 |
| EMIT, S0, S1, S2 | PA4, PB13, PB14, PB15 | GPIO | Encoder derecho A/B | PA15 / PB3 | TIM2 CH1/CH2 |
| I2C SCL / SDA (IMU + 2 barómetros) | PA8 / PC11 | I2C3 | ESC (PWM, Oneshot o DShot bidireccional) | PB9 | TIM17_CH1 |
| START / CAL | PC4 / PA5 | GPIO (antirrebote RC) | Zumbador | PB8 | TIM16_CH1 |
| LED verde / amarillo / rojo | PB0 / PB1 / PB10 | GPIO | RESET | NRST | botón externo |

Notas: PB11 (/CS de la flash QSPI del módulo) queda sin conectar, así la flash está deseleccionada y PB0, PB1 y PB10
sirven para los LED. PB8 es BOOT0 al reset: la compuerta del zumbador tiene 100 kΩ a GND y no cambia el arranque. En modo
cargador, PA9/PA10 son el USART1 del cargador (AN2606): los puentes H quedan dormidos porque nSLEEP tiene 100 kΩ a GND.
Libres: PA6, PA7, PC13 (botón del módulo), PC6 (LED azul del módulo). El módulo toma 3.3 V de esta placa por sus pines
3V3; su VCC queda libre.

Pendiente para la entrega 2: colocación final, ruteo (Freerouting, mismo flujo que la barra), DRC, Gerbers y pick and
place. Las posiciones del esquemático actual son la colocación inicial que usó el CAD.

## 6. CAD mecánico

| Pieza impresa | Función | Masa (PLA sólido, cota superior) |
|---|---|---|
| `chasis` | Placa de 2 mm (techo de la cámara), cunas de motor, alojamiento del ventilador (bolsillo para el realce de la base, entrada Ø20, 4 agujeros Ø1.8), chimenea al sensor de presión, bahía del ESC, portabaterías con ranuras para correa, rueda loca, postes de la PCB, ventana sobre la barra | 31.0 g [C] |
| `faldon_camara` | Cámara de 70 × 70 mm interior, pared de 1.2 mm. **Corregido en la Fase 3.5**: borde inclinado (3.86 mm atrás, 1.90 mm adelante) para quedar a ≥ 0.5 mm de la pista con las llantas comprimidas; tornillos desde arriba (ver `FASE35_CORRECCIONES.md`) | 2.0 g [C] |
| `tapa_motor_izq/der` | Abrazaderas de los motores; su cara superior apoya la PCB principal | 2 × 2.0 g [C] |
| `cachucha_sensores` | Escudo de luz bajo la barra: ventana alrededor de los 16 sensores y paredes hasta **1.0 mm** del piso | 2.2 g [C] |
| `tapa_rueda_loca` | Cierra el alojamiento de la bola de 1/4 in | 0.1 g [C] |

**Verificación** (`hardware/v2/mecanica/verificacion_mecanica.json`):
- **Sin interferencias** entre ninguna pieza del ensamble, y entre las **mallas reales de tu ventilador** (base, 4 pilares,
  soporte, rotor) y el chasis, las abrazaderas, los motores, la batería, el ESC y la PCB [C].
- Medidas totales **173.6 × 92.0 × 38.9 mm**: cabe en la caja de 192 × 92 mm (R01 con 4 mm de holgura por lado) [C].
- Holguras: rotor-base 1.2 mm; entrada Ø20 a la pared de la cámara 1.5 mm; pared de la cámara a la llanta 2.8 mm;
  encoder a la PCB 1.5 mm; pilares del ventilador a las abrazaderas 4.6 mm [C].
- (Antes de la Fase 3.5) lo más bajo sin contacto con la pista: faldón a 0.5 mm, cachucha a 1.0 mm, cara de los sensores a 2.05 mm, rueda loca a
  1.0 mm (solo la bola toca) [C]. **Todas con la succión apagada**: la compresión de las llantas con la succión puesta baja
  estas cifras y hay que medirla [P].
- **Masa total 156 g** (con las piezas impresas sólidas en PLA; con relleno parcial pesa menos) [C/E]; CG en
  x = 24.0 mm, z = 15.2 mm. El apoyo delantero no se levanta hasta 15.5 m/s² de aceleración sin contar la succión
  (los motores dan ≤ 10.5 m/s² a la salida de curva) [C]. Con 156 g el requisito de succión de la Fase 1 baja a ≈ 2.4 N [C].
- Centro de la cámara a 4 mm delante del eje: ≈ 96 % de la succión carga las ruedas motrices [C].

**Tornillería y extras** (para el kit de pits): ventilador a chasis 4 × M1.6 × 10 desde abajo a los pilares (los 2 traseros
quedan dentro de la cámara: la cabeza sella); faldón 4 × M2 × 8 con tuerca; abrazaderas 8 × autorroscante ST2.2 × 16
(agujeros ciegos: la cámara queda sellada); PCB principal 4 × ST2.2 × 6; barra + cachucha 3 × M2 × 8 con tuerca; bola de
acero de 1/4 in; correa de velcro de 8 mm para la batería (C09) y cinta Dual Lock para batería y ESC; empaque de 1 mm
(Ø8/Ø4) entre la chimenea y la PCB.

Impresión sugerida: PLA o PETG, capa de 0.2 mm, 4 perímetros, relleno ≥ 40 %; el chasis boca abajo (cara de la cámara
sobre la cama) para que el techo de la cámara salga sellado.

## 7. Supuestos que debes revisar

| Dato | Valor usado | Dónde cambiarlo |
|---|---|---|
| ESC | envolvente 14 × 26 × 6 mm | `config/v2/robot_v2.yaml` → `esc` |
| Motor del ventilador | 1104, Ø14.3 mm, colgado bajo el soporte | `generar_cad_v2.py` (`ventilador_aprox`) |
| Encoder del #5183 con conector lateral | envolvente 15 × 7.6 × 13 mm (Pololu no publica la medida) | `generar_cad_v2.py` (`motor`) |
| Radio del arco de sensores | 125 mm (rango 110-140 de la Fase 1) | `robot_v2.yaml` → `robot.L_sensores` |
| Material de las piezas | PLA/PETG impreso localmente | — |

Riesgos: la salida radial del ventilador está parcialmente tapada hacia adelante (batería a 6.5 mm del rotor) y hacia atrás
(abrazaderas); los lados quedan libres. En el régimen de la Fase 1 (casi en presión de cierre, poco caudal) eso afecta poco,
pero conviene confirmarlo en la prueba de báscula [E].

## 8. Fuentes nuevas de esta entrega

- WeAct STM32G474 Core Board (esquemático, contorno, modelo 3D, AN2606): <https://github.com/WeActStudio/WeActStudio.STM32G474CoreBoard>
- Pines del STM32G474CEU6: <https://github.com/STMicroelectronics/STM32_open_pin_data> (`STM32G474C(B-C-E)Ux.xml`)
- DRV8874 (pines, A_IPROPI 450 µA/A, condiciones de operación): <https://ti.com/document-viewer/DRV8874/datasheet/pin-configuration-and-functions-x119>
- Encoder Pololu (orden de pines 1 GND, 2 B, 3 A, 4 VCC, 5 M2, 6 M1; 12 CPR en el eje del motor): <https://www.pololu.com/product-info-merged/4760>
- ISM330DHCX: <https://st.com/en/mems-and-sensors/ism330dhcx.html> · LPS22DF: <https://st.com/en/mems-and-sensors/lps22df.html>
- 74HC4051PW,118: <https://www.nexperia.com/pip/74HC4051PW> · DMP3013SFV: <https://www.diodes.com/part/view/DMP3013SFV>
- 0297010.WXNV: <https://octopart.com/part/littelfuse/0297010.WXNV> · PKLCS1212E4001-R1: <https://octopart.com/part/murata/PKLCS1212E4001-R1>
