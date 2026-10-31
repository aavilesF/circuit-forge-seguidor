# Plan de primera compra

Fecha: 31 oct 2026 · Rama `engineering/final-prototype`.
**Nada se ha comprado.** Este plan no aprueba C2 (sigue abierto), no cambia firmware ni `MOTOR_DESDE_BATERIA`, y no elimina componentes de la arquitectura.

Etiquetas: **[Verificado]** precio y existencia leídos en la página del vendedor el 31 oct 2026 (pueden cambiar) · **[Estimado]** cálculo o rango · **[Pendiente]** sin cotizar o sin dato.
Proveedor principal: UNIT Electronics (uelectronics.com), consultado con el navegador; los enlaces son las páginas de producto.

## 1. Auditoría de los documentos

| # | Documento | Hallazgo | Acción |
|---|---|---|---|
| D1 | `BOM_FINAL.csv` | TB6612: "VM 2.5-13.5 V, 1.2 A prom./3.2 A pico". La ficha de Toshiba recomienda **≤ 1.0 A** y VM 4.5-13.5 V; 1.2 A es máximo absoluto; los picos tienen condiciones | **Corregido en la BOM** (error documental confirmado) |
| D2 | `ARQUITECTURA.md` §3.3, §3.4 (línea "dentro del 1.2 A") y §6 ("2 × 1.2 A continuos") | Mismo error que D1 | **No editado** (fuera del alcance pedido). Corregir cuando se autorice |
| D3 | `PROTOCOLO_PRUEBAS.md` F4.1 | Pide bloquear el motor a 6 V "desde el regulador o una fuente" con criterio "≤ 1.2 A (promedio del TB6612)". Contradice el P1 seguro de `C2_ALIMENTACION.md` §10 (fuente con límite, 3 V, sin LiPo) | **No editado**. Usar el P1 de C2 (§7 de este plan). Corregir F4.1 cuando se autorice |
| D4 | `BOM_FINAL.csv` | Precios en rango (ESP32 $131-156, motor $83-90). Ya se conoce el precio exacto: ESP32 MicroUSB **$131** (SKU AR1191, chip USB CP2102); GA12-N20 **6 V 1000 RPM $89** | No es un error; el precio exacto se usa en este plan |
| D5 | `BOM_FINAL.csv` | Pide resistencias de 1 %; UNIT solo tiene THT de carbón al 5 % en estos valores (1 % solo en SMD) | Se acepta 5 % porque el protocolo F3 calibra `DIVISOR_BAT` con multímetro |
| D6 | `BOM_FINAL.csv` | "Rueda Ø 30-34 mm": la llanta de 34 × 7 mm de UNIT está **sin existencias** | Ver §3 (decisión de llanta) |
| D7 | Página de UNIT del TB6612 | Dice "Tensión input (IN1, IN2, STBY, PWM): 4.5 to 6 V". Toshiba: entradas −0.2 a 6 V con VCC 2.7-5.5 V (lógica a 3.3 V válida) | Prevalece la ficha del fabricante; se prueba en la recepción (§6, R5) |
| D8 | `INFORME_FINAL.md` §G | Totales calculados con rangos y sin batería | Este plan los sustituye para la compra |
| D9 | `C2_ALIMENTACION.md` | Coherente con la ficha. Su P1 y P3 piden instrumentos de laboratorio (§7) | Sin cambio |

## 2. Qué es imprescindible para el primer prototipo

**Primer prototipo funcional** = robot que siga una línea con cualquiera de las dos arquitecturas de C2. Todo lo que es **común a A3 y a B** se puede comprar ya. Lo que solo sirve a una de las dos, o depende de P1/P3, espera.

| Grupo | Componentes | ¿Comprar ya? |
|---|---|---|
| Control y sensado | ESP32, sensor, multiplexor | Sí (el sensor sigue siendo decisión P10 del equipo; ver §8) |
| Potencia común | TB6612, MP1584 para 5 V, batería 2S, cargador, fusible, interruptor, conector, capacitores, divisor | Sí |
| Movimiento | 2 motores, 2 soportes, 2 llantas, 1 apoyo | Sí, con la decisión de llanta (§3) |
| Montaje | Perfboard, headers, cable de señal | Sí |
| Solo para A3 | Convertidor buck-boost AR4790 | **Esperar** a C2 |
| Depende de P1 | Motores de repuesto, valor final del fusible, motor alternativo | **Esperar** a P1 |
| Depende de P3 | Regulador alternativo de 5 V (C2.2) | **Esperar** a P3 |

## 3. Compatibilidad entre piezas

| Unión | Dato A | Dato B | Resultado |
|---|---|---|---|
| ESP32 ↔ sensor | ESP32 lógica 3.3 V, ADC con rango sugerido 150-2450 mV a 11 dB (Espressif) | Clon: VCC 3-5 V, salidas analógicas D1-D8, pin **IR** (activación de infrarrojos), pad "3.3V" visible en la foto (UNIT, pinout) | Compatible a 3.3 V. Polaridad de salida y de IR, y paso entre sensores: [Pendiente, medir] |
| Sensor ↔ multiplexor | 8 salidas | 74HC4067: 2-6 V, 16 canales | Compatible (un solo mux) |
| ESP32 ↔ TB6612 | Salidas 3.3 V | Toshiba: VCC 2.7-5.5 V; VCC a 3.3 V | Compatible por ficha (D7) |
| TB6612 ↔ batería 2S (B) | VM 6.0-8.4 V | VM recomendado 4.5-13.5 V | Compatible |
| TB6612 ↔ motor | ≤ 1.0 A recomendado | Bloqueo del GA12-N20 6 V 1000 RPM: **no publicado** | [Pendiente P1] |
| Motor ↔ llanta | Eje D de 3 mm | Llanta 34 × 7: eje D 3 mm (agotada); llanta 43 × 19: eje D 3 mm (138 en existencia) | Compatibles en eje |
| Llanta ↔ velocidad | 1000 RPM | 34 mm → 1.78 m/s; 43 mm → **2.25 m/s** sin carga [Estimado: π·D·RPM/60] | La de 43 mm sube la velocidad 26 % y el par necesario; hay que cambiar `DIAMETRO_RUEDA_MM` y volver a simular |
| Llanta ↔ huella | Ancho máximo 100 mm | 43 × 19 mm: con centros a ±37.5 mm el borde exterior queda en ±47 mm → 94 mm [Estimado] | Cabe, justo |
| Llanta ↔ apoyo | Eje a 17 mm (34 mm) o 21.5 mm (43 mm) del piso | Apoyo "Mini rueda universal 3Pi N20": 22 × 16 × 15 mm | Con 43 mm de llanta hace falta un separador de ~6 mm para nivelar [Estimado]; medir al recibir |
| Batería ↔ conector | Turnigy 500 mAh 2S: descarga **JST-RC**, balanceo JST-XH (tiendadeelectronica.mx) | UNIT: par JST-RC $8 / XT30 $15 | Comprar **JST-RC** para no soldar en la batería |
| Batería ↔ cargador | Balanceo JST-XH 2S | Cargador B3 2S/3S, 1.6 A | Compatible |
| Batería ↔ consumo | 500 mAh, 20C o 35C (la página dice ambos) → ≥ 10 A | Pico estimado < 4 A | Compatible |
| Interruptor ↔ corriente | Línea de motores (B): hasta ~2-3 A en picos [Estimado] | Deslizable SPDT: **0.5 A** (no sirve); KCD1-110: 6 A/250 V **AC** (no tiene valor en DC publicado) | KCD1-110 [DC pendiente; razonable a 8.4 V, verificar caída en R3] |
| Cable ↔ corriente | Línea de batería/VM | Cable 22 AWG de UNIT: "corriente máxima 1 A" | **No** para la línea de potencia. Cable de silicón 18-20 AWG [Pendiente]; los cables de la batería sirven hasta el fusible |
| Fusible ↔ batería | 8.4 V | MINISMDC150F/16-2: 16 V, sostiene 1.5 A, dispara 2.8 A, ≤ 500 ms; SMD 1812 | Compatible en voltaje; el valor de corriente se revisa tras P1. **No** usar los modelos de 6 V |
| Capacitor ↔ VM | 8.4 V (B); en A3 la línea puede subir al frenar | 470 µF 25 V THT | Compatible con margen |
| ESP32 ↔ huella | 55 × 28 × 6 mm, 11 g (UNIT) | Vista superior a escala (55 × 28) | Coincide con lo supuesto |
| ESP32 ↔ alimentación | La página de UNIT no menciona el pin VIN | Diseño: MP1584 a 5 V → VIN | [Pendiente: confirmar VIN/5V en el pinout de la placa recibida] |

## 4. Primera compra (verificar existencias el día del pago)

### 4.1 UNIT Electronics — imprescindible y común a A3/B

| Componente | Modelo exacto | Cant. | Precio unit. | Subtotal | Existencia | Enlace | Alternativa |
|---|---|---:|---:|---:|---|---|---|
| Microcontrolador | ESP32 38 pines ESP-WROOM-32 **MicroUSB** (AR1191, CP2102) | 1 | $131 | $131 | 3085 | [link](https://uelectronics.com/producto/esp32-38-pines-esp-wroom-32-microusb-usb-c/) | Variante USB-C (AR5464) $156, 4 piezas |
| Sensor (si el equipo confirma P10) | QTR-8A Módulo de Seguimiento 8 Canales (AR3482, TCRT5000) | 1 | $61 | $61 | 842 | [link](https://uelectronics.com/producto/qtr-8a-modulo-de-seguimiento-8-canales/) | Pololu QTR-8A original [Pendiente] |
| Multiplexor | 74HC4067 16 canales (AR1722) | 1 | $25 | $25 | 20 | [link](https://uelectronics.com/producto/74hc4067-multiplexor-analogico-digital-16-canales/) | — |
| Driver | Doble Puente H TB6612FNG | 1 | $54 | $54 | 856 | [link](https://uelectronics.com/producto/doble-puente-h-tb6612fng/) | — |
| Motores | GA12-N20 **6 V 1000 RPM** | 2 | $89 | $178 | 224 | [link](https://uelectronics.com/producto/ga12-n20-motorreductor-dc-3v-6v-12v/) | Pololu 30:1 HP 6 V [Pendiente] |
| Soportes | Soporte para motorreductor N20 N30 | 2 | $5 | $10 | [Pendiente] | (página del motor) | Soporte fabricado |
| Llantas | Llanta de goma N20 **43 × 19 mm** (34 × 7 agotada) | 2 | $15 | $30 | 138 | [link](https://uelectronics.com/producto/llanta-de-goma-para-motorreductor-n20-de-43x19mm/) | 34 × 7 mm $11 si vuelve a haber existencia |
| Apoyo | Mini rueda universal 3Pi N20 (bola de acero, 22 × 16 × 15 mm, 10 g) | 1 | $16 | $16 | 76 | [link](https://uelectronics.com/producto/mini-rueda-universal-3pi-n20/) | W420 $17 (20 mm de alto, 17.8 g) |
| Regulador 5 V | MP1584EN Step Down 3 A (AR0087) | 1 | $19 | $19 | 3158 | [link](https://uelectronics.com/producto/mp1584en-modulo-step-down-3a-dc-dc/) | Pololu D24V10F5 [Pendiente] |
| Fusible | MINISMDC150F/16-2 reseteable 16 V, 1.5/2.8 A, 1812 | 2 | $16 | $32 | 42 | [link](https://uelectronics.com/producto/fusible-reseteable-16v-2-8a-smd-1812-minismdc150f-16-2/) | NSMD150-13.2V (1206) $7 |
| Interruptor | KCD1-110 basculante | 1 | $9 | $9 | [Pendiente] | [link](https://uelectronics.com/producto/kcd1-110-interruptor-basculante/) | Desconectar el JST-RC |
| Conector batería | Par de cables hembra/macho JST RC | 1 | $8 | $8 | [Pendiente] | [link](https://uelectronics.com/producto/par-de-cables-hembra-macho-conector-jst-rc/) | XT30 $15 (re-soldar la batería: no recomendado) |
| Capacitor VM | Electrolítico 470 µF 25 V THT | 2 | $7 | $14 | [Pendiente] | [link](https://uelectronics.com/producto/capacitores-electroliticos-25v-10uf-a-10000uf/) | 470 µF 16 V $2 |
| Capacitor | Cerámico 100 nF 50 V THT | 6 | $1 | $6 | 13 625 | [link](https://uelectronics.com/producto/capacitor-ceramico-100nf-0-1uf-104/) | — |
| Divisor | Resistencias de carbón 1/4 W 5 %: 100 kΩ y 33 kΩ | 2 + 2 | $0.10-0.50 | ≤ $2 | [Pendiente] | [link](https://uelectronics.com/producto/resistencia-de-1-ohm-1m-ohms-1-4w/) | — |
| Placa | Perfboard una cara 5 × 10 cm | 2 | $13 | $26 | [Pendiente] | [link](https://uelectronics.com/producto/placa-perforada-pcb-una-cara/) | 7 × 9 $16 |
| Headers | Tira header hembra 2.54 mm | 2 | $2-5 | ≤ $10 | [Pendiente] | [link](https://uelectronics.com/producto/tira-header-hembra-2-54mm-diferentes-pines/) | — |
| Cable de señal | Cable 22 AWG 1 m (rojo y negro) | 2 | $5 | $10 | Verde agotado | [link](https://uelectronics.com/producto/cable-electrico-calibre-22-awg-1-metro-diferentes-colores/) | — |
| **Subtotal UNIT imprescindible** | | | | **$633-641** (rango por resistencias y headers) | | | |

### 4.2 Otros proveedores — imprescindible
| Componente | Modelo | Cant. | Precio | Proveedor | Estado |
|---|---|---:|---:|---|---|
| Batería | Turnigy LiPo 500 mAh 7.4 V 2S (JST-RC + JST-XH, 55 × 30 × 14 mm, 36 g; la página dice 35C en el título y 20C en la ficha) | 1 | $538 IVA incl. | [Tienda de Electrónica MX (Puebla)](https://tiendadeelectronica.mx/tienda/bateria-lipo-500mah-7-4v-turnigy-2s-35c/) | [Verificado] "hay existencias"; envío [Pendiente] |
| Cargador (solo si el equipo no tiene) | Cargador Balanceador B3 2S/3S 20 W (AR1760) | 1 | $227 | [UNIT](https://uelectronics.com/producto/cargador-balanceador-b3-lipo-2s-3s-20w/) | [Verificado] 14 piezas |
| Cable de potencia | Silicón 18-20 AWG, rojo y negro | 1 m c/u | [Pendiente] | Tienda de aeromodelismo | [Pendiente] |
| Botones | Pulsador táctil 6 × 6 mm THT | 4 | [Pendiente] | Tienda local (UNIT solo vende kit de 200 por $73) | [Pendiente] |
| Material del chasis | Acrílico o MDF de 3 mm, tornillería M2/M3 | — | [Pendiente] | Local | Esperar a tener piezas para diseñar |
| Pista de práctica | Superficie blanca mate + vinil negro de 2.5 cm | — | [Pendiente] | Local | — |

### 4.3 Repuestos baratos recomendados en la misma orden (UNIT)
| Componente | Cant. | Subtotal | Motivo |
|---|---:|---:|---|
| TB6612FNG | 1 | $54 | Se daña con un corto o un bloqueo |
| 74HC4067 | 1 | $25 | Solo hay 20 en existencia |
| MP1584EN | 1 | $19 | Ajuste de voltaje con potenciómetro: fácil de dañar el ESP32 si se mueve |
| **Subtotal repuestos** | | **$98** | |

## 5. Lo que **no** se compra todavía

| Componente | Precio | Espera a | Razón |
|---|---:|---|---|
| Convertidor buck-boost AR4790 | $144 [Verificado, 155 piezas] | C2 | Solo sirve si se elige A3 |
| 2 motores de repuesto | $178 | P1 | Si el bloqueo pasa de 1.2 A, serían 4 motores inservibles |
| Motor alternativo (Pololu HP o MP) | [Pendiente] | P1 | Solo si P1 falla |
| Regulador 5 V alternativo (D24V10F5) | [Pendiente; sin proveedor en México encontrado] | P3 | Solo si el MP1584 falla P3 (C2.2) |
| ESP32 y sensor de repuesto | $131 + $61 | Primera semana de pruebas | Más caros; se compran si algo se daña o tras validar el modelo |
| Segunda batería | $538 + envío | P5 y F10 | Primero confirmar que la primera sirve y cuánto dura |
| Llanta 34 × 7 | $11 | Reabastecimiento | Si regresa, preferible a 43 × 19 (geometría ya simulada) |

## 6. Recepción e inspección (antes de conectar nada al resto)

Orden: inspección visual → medición en vacío → prueba aislada → integración. Registrar cada resultado en `modificaciones/` con fecha.

| # | Pieza | Al recibir | Prueba aislada antes de integrar | Criterio |
|---|---|---|---|---|
| R1 | ESP32 | Etiqueta ESP-WROOM-32 (no WROVER); 38 pines; chip CP2102; ubicar pin VIN/5V | Solo USB: subir el firmware (INSTALLATION_GUIDE §6-8) | Compila, sube y muestra el mensaje de inicio |
| R2 | Batería | Voltaje por celda en el balanceo; inspección de hinchazón; pesar | Cargar con B3 en superficie no inflamable, sin dejarla sola | 3.7-4.2 V/celda; diferencia < 0.05 V; sin deformación |
| R3 | Interruptor, fusible, conector | Continuidad en ON, aislamiento en OFF; polaridad del JST-RC | Batería → conector → fusible → interruptor sin carga | 0 Ω en ON, abierto en OFF; voltaje de salida = batería |
| R4 | MP1584 | — | Desde fuente o batería, **sin carga**, ajustar a 5.00 V antes de conectar el ESP32; marcar el potenciómetro con pintura | 4.95-5.05 V en vacío |
| R5 | TB6612 | Serigrafía de pines (VM, VCC, STBY, AIN/BIN, PWMA/B) | VCC 3.3 V desde el ESP32, VM sin motores; poner STBY en alto y medir las salidas con multímetro | Salidas conmutan; nada se calienta |
| R6 | Sensor | Medir el paso centro a centro con vernier; anotar el pin IR y el pad "3.3V" | A 3.3 V: con multímetro, salida sobre papel blanco y sobre cinta negra; IR a GND y a 3.3 V | Diferencia clara entre blanco y negro; anotar polaridad de salida y de IR |
| R7 | 74HC4067 | Pines S0-S3, SIG, EN | A 3.3 V, EN a GND: resistencia entre SIG y cada canal seleccionado | Conmuta |
| R8 | Motores | Misma variante en las dos etiquetas | **P1-a** (resistencia del devanado) antes de cualquier otra cosa; luego P1-b y P2 en el laboratorio | Ver §7 |
| R9 | Llantas y apoyo | Diámetro y ancho con vernier; altura del apoyo | Montaje en seco sobre una tabla: altura del sensor al piso | La que pida el sensor (clon: 8-12 mm según el vendedor) |
| R10 | Capacitores, resistencias | Polaridad y voltaje del electrolítico; valor de las resistencias con multímetro | — | 100 kΩ y 33 kΩ ±5 %; anotar el valor real para `DIVISOR_BAT` |

## 7. Instrumentos (no son componentes del robot)

| Instrumento | Uso | Dónde conseguirlo | Para qué prueba |
|---|---|---|---|
| Multímetro con escala de 10 A con fusible | Voltajes, continuidad, resistencias, corriente | **Propio recomendado** (uso diario). UNIT: MUL-281 $346 o RM102 $452 [Verificado]; confirmar que traiga 10 A | R1-R10, P1-a, P2, P5 |
| Fuente de laboratorio con límite de corriente (CV/CC) | P1-b/P1-c, P3 a voltaje controlado | **Laboratorio de la universidad** [Pendiente confirmar] | P1, P3 |
| Osciloscopio | Caídas rápidas de 5 V/3.3 V, voltaje de VM al frenar, rizado | Laboratorio [Pendiente confirmar] | P3 (recomendado), P4, P8 |
| Medidor LCR | Inductancia del motor | Laboratorio [Pendiente confirmar] | P4 |
| Cautín con control de temperatura, malla, flux | Soldar el fusible SMD 1812 y headers | Propio o laboratorio | Armado |
| Báscula de 0.1-1 g | Masa (máx. 500 g) | Propia o laboratorio [Pendiente] | F1, F12 |
| Vernier | Paso del sensor, llantas, alturas | Propio o laboratorio [Pendiente] | R6, R9 |
| Bolsa o caja para LiPo | Carga segura | Tienda de aeromodelismo [Pendiente; UNIT no la tiene] | R2 |
| Termómetro IR (opcional) | Temperaturas de P6 | Laboratorio | P6 |

**¿Se pueden ejecutar P1 y P3 con esto?**
- **P1-a** (resistencia del devanado): sí, con el multímetro propio.
- **P1-b/P1-c** (bloqueo a 3 V con límite de 1.5 A): solo con la **fuente del laboratorio**. Sin ella no se hace; no hay sustituto seguro con la LiPo.
- **P3**:
  - El criterio principal (0 reinicios en 60 ciclos, leído en el monitor serie) **sí** se puede hacer con el multímetro y la batería parcialmente descargada (entrada de ~6.8 V).
  - El voltaje mínimo de 5 V y 3.3 V en transitorios cortos **requiere osciloscopio**: la función MIN/MAX de un multímetro no capta caídas de microsegundos.
  - Sin osciloscopio, P3 queda "aprobado por reinicios, sin medir transitorios".

## 8. Presupuestos (MXN, sin envío)

| Concepto | Imprescindible | Opcional / después |
|---|---:|---:|
| UNIT, imprescindible (§4.1) | $633-641 | |
| Batería Turnigy 500 mAh 2S | $538 | |
| Cargador B3 | $227 si no tienen | |
| Repuestos baratos (§4.3) | | $98 (recomendado en la misma orden) |
| Potenciómetro trimpot 10 kΩ (perilla de velocidad) | | $7 |
| **Primera compra** | **$1,171-1,179** (sin cargador) · **$1,398-1,406** (con cargador) | **+$105** |
| Pendientes de cotizar en la primera compra | cable de silicón, botones, bolsa LiPo, material de chasis, pista, envíos | — |
| Esperar (§5): motores de repuesto $178, ESP32 $131, sensor $61, 2ª batería $538 | | $908 |
| Solo si se elige A3 | | $144 |
| **Compra completa (máximo, con A3 y todos los repuestos)** | | **$2,555-2,563** con cargador, + pendientes |
| Instrumentos propios (multímetro) | | $346-452 |

El rango sale de las resistencias y headers con precio por rango. No incluye la donación de $300 del evento.

## 9. Riesgos de comprar antes de resolver C2

| Riesgo | Efecto | Mitigación |
|---|---|---|
| Se elige A3 después | +$144, +42 g, 66 × 48 mm ocupados | Todo lo de §4 sirve igual en A3; **no fabricar el chasis definitivo** hasta decidir C2 |
| P1 da bloqueo > 1.2 A | Los 2 motores ($178) no sirven con el TB6612 | No comprar repuestos todavía; P1-a se hace el día que lleguen |
| Fusible mal dimensionado | Disparos falsos o protección tardía | Es barato ($16); se cambia tras P1 |
| Llanta de 43 mm en lugar de 34 mm | +26 % de velocidad, otra altura, simulación desactualizada | Actualizar `DIAMETRO_RUEDA_MM` y volver a simular (cuando se autorice); o esperar la de 34 mm |
| Cable de 22 AWG (1 A según el vendedor) en la línea de potencia | Calentamiento, caída de voltaje | Cable de silicón 18-20 AWG para batería → fusible → interruptor → VM |
| Interruptor sin valor en DC | Contacto que se degrada | Medir su caída en R3; alternativa: desconectar con el JST-RC |
| Sensor clon sin ficha completa | Paso y polaridad distintos a lo supuesto | Es barato; el firmware está parametrizado; R6 lo mide |
| Página del TB6612 contradice a Toshiba (D7) | Confusión al cablear | Seguir la ficha de Toshiba; R5 verifica con 3.3 V |
| Existencias que cambian (multiplexor: 20; ESP32 USB-C: 4) | Pedido incompleto | Revisar el carrito antes de pagar |
| Envío de la batería desde Puebla y de UNIT | Retraso con 21 días a la competencia | Preguntar tiempos antes de pagar; considerar recoger en tienda si existe |

## 10. Recomendación

**Comprar primero** (una orden en UNIT + la batería):
1. UNIT §4.1 completo ($633-641) + repuestos §4.3 ($98) ≈ **$731-739**, con llantas de 43 × 19 mm **solo** si no hay otra fuente de 32-34 mm.
2. Batería Turnigy 500 mAh 2S ($538 + envío).
3. Cargador B3 ($227) solo si el equipo no tiene uno balanceador.
4. Multímetro propio si nadie del equipo tiene.

**No comprar todavía:** AR4790 (A3), motores de repuesto, regulador alternativo, segunda batería, ESP32 y sensor de repuesto.

**Verificar antes de pagar:**
1. **P10:** que el equipo confirme el sensor (clon de UNIT, $61). Es la última decisión que bloquea la compra.
2. Existencias en el carrito: multiplexor, soportes, JST-RC, interruptor, capacitores, resistencias.
3. La llanta: decidir 43 × 19 mm o buscar 32-34 mm en otra tienda.
4. Tasa C real y tiempo de envío de la batería (la página dice 35C y 20C).
5. Costo y tiempo de envío de UNIT a León, o si se puede recoger.
6. Con el laboratorio: disponibilidad de **fuente con límite de corriente** (P1) y **osciloscopio** (P3/P8) en la semana del 4 al 8 de noviembre.
7. Que nadie del equipo tenga ya cargador, multímetro o cautín (evita gastos duplicados).

C2 sigue **pendiente de tu aprobación**; nada de esta compra lo decide.
