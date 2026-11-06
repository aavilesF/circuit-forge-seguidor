# Pendientes por confirmar (robot casero)

Rama `engineering/robot-casero`. **Aquí vive todo lo que el diseño supone pero todavía no está medido ni verificado.**
No tenemos vernier: Alan mide con regla (precisión ~0.5–1 mm) y compara con el valor propuesto.

**Regla de decisión:** diferencia ≤ 1 mm con la regla → se da por buena (estado *aceptada*). Más de 1 mm, o si la pieza es de ajuste justo (agujeros, ranuras,
distancia entre filas de pines) → anotar la medida de la regla y conseguir un vernier (o una escuadra con escala fina) para repetirla.

**Estados:** `pendiente` · `medida con regla` · `aceptada` · `con vernier` · `descartada`.
**Quién mide:** Alan salvo que se indique otra persona (columna "Quién").
Los valores marcados **SIN FUENTE** son marcadores de posición míos para poder dibujar; **no deben usarse para cortar ni fabricar**.

## 1. Medidas de módulos y piezas

| ID | Tema | Valor propuesto | Fuente | Cómo confirmarlo | Estado | Quién |
|---|---|---|---|---|---|---|
| M01 | ESP32 DevKit 38 pines: largo × ancho de la placa | 54.4 × 27.9 mm | Reportado para el DevKitC V4 (Espressif, [guía](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html), hay PDF/DXF de dimensiones ahí); **el clon que vende UNIT puede variar** | Regla: largo y ancho con la placa recostada | pendiente | Alan |
| M02 | ESP32: distancia entre las dos filas de pines (centro a centro) | 25.4 mm (1 pulgada) | **SIN FUENTE verificada** (valor habitual de 38 pines; algunos clones usan 22.9 mm) | Regla: medir de pin a pin enfrentados. **Es la medida que más importa para el PCB** | pendiente | Alan |
| M03 | ESP32: orden de pines | 19 pines por lado, orden Espressif (3V3, EN, VP, VN, 34, 35, 32, 33, 25, 26, 27, 14, 12, GND, 13, D2, D3, CMD, 5V // GND, 23, 22, TX, RX, 21, GND, 19, 18, 5, 17, 16, 4, 0, 2, 15, D1, D0, CLK) | Espressif DevKitC V4 | Leer la serigrafía de la placa y comparar con el esquema (foto de ambos lados) | pendiente | Alan |
| M04 | ESP32: cantidad de pines por lado y paso | 19 × 2,54 mm | Espressif | Contar pines | pendiente | Alan |
| M05 | Motor GA12-N20 6 V 1000 RPM: largo del cuerpo y del eje | 34 mm total (incluye eje ∅3 × 10 mm); peso 10 g; 0.07 A nominal, 1 A en atasco | [mikroelectron.com](https://mikroelectron.com), página del GA12-N20 | Regla | pendiente | Alan |
| M06 | N20: ancho × alto del cuerpo | 12 × 10 mm | **SIN FUENTE verificada** (medida habitual del N20) | Regla | pendiente | Alan |
| M07 | N20: posición de los 2 agujeros M1.6 del frente | separación 9 mm, a ~3 mm del frente | **SIN FUENTE** | Regla; se usa para ver si se sujeta con abrazadera o tornillos | pendiente | Alan |
| M08 | Rueda 34 × 7 mm, eje en D de 3 mm | ∅34 × 7 mm | Contexto del equipo (compra no concretada) | Regla al llegar | pendiente | Alan |
| M09 | Driver DRV8833 (módulo): largo × ancho | 21 × 18 mm | **SIN FUENTE** (los módulos genéricos varían mucho) | Regla | pendiente | Alan |
| M10 | DRV8833: orden de pines | VM, GND, AIN1, AIN2, BIN1, BIN2, SLEEP, FAULT (un lado) y AOUT1, AOUT2, BOUT1, BOUT2 (otro) | **SIN FUENTE verificada**: ya compramos 2; el orden cambia entre módulos (el de Pololu es distinto) | Fotografiar el módulo comprado y leer la serigrafía | pendiente | Alan |
| M11 | DRV8833: voltaje de motor y corriente | 2.7–10.8 V; 1.5 A continuo por puente | [Components101](https://components101.com/ics/drv8833-motor-driver-ic) (el chip, no el módulo) | Datasheet del módulo comprado | pendiente | Alan |
| M12 | MP1584 (módulo): largo × ancho × alto | 22 × 17 × 4 mm | [sigmanortec](https://sigmanortec.ro) | Regla | pendiente | Alan |
| M13 | MP1584: posición de IN+/IN− y OUT+/OUT− | IN a un extremo, OUT al otro | **SIN FUENTE** (cada módulo tiene sus pads) | Foto del módulo; marcar cuál pad es cuál | pendiente | Alan |
| M14 | LiPo 2S 450–500 mAh: largo × ancho × alto y peso | 55 × 18 × 14 mm, ~30 g | **SIN FUENTE** (valor típico de esa capacidad) | Medir cuando se compre; es la pieza que más decide la distribución de peso | pendiente | Alan |
| M15 | LiPo: tipo de conector de potencia y de balanceo | JST-RC 2 pines + JST-XH 3 pines | **SIN FUENTE** | Mirar la batería antes de comprar el conector (ver faltantes) | pendiente | Alan |
| M16 | Multiplexor 74HC4067 (módulo en barrita): tamaño | 18 × 41 mm | Mensaje de Alan al ver la pieza; sin datasheet | Regla | pendiente | Alan |
| M17 | 74HC4067: orden y posición de los pines | VCC, GND, SIG, EN, S0–S3 en un extremo; C0–C15 en los lados (8 por lado) | **SIN FUENTE**; cada vendedor lo hace distinto | Foto de la serigrafía | pendiente | Alan |
| M18 | TCRT5000 suelto: cuerpo | 10.2 × 5.8 × 7 mm | Vishay (datasheet) | Regla | pendiente | Alan |
| M19 | TCRT5000: separación de patas (paso) y entre filas | 2.54 mm y 4.5 mm | **SIN FUENTE** (no pude leerla en el datasheet) | Regla en el sensor comprado | pendiente | Alan |
| M20 | TCRT5000: orden de pines (A, K, C, E) | A=ánodo, K=cátodo (LED); C=colector, E=emisor (fototransistor) | Convención del datasheet; el orden en el cuerpo se confirma | Mirar el lado con la muesca/chaflán | pendiente | Alan |
| M21 | Ventilador elegido: tamaño, voltaje y consumo reales | Ver `faltantes-unit.md` (4010: 40 × 40 × 10 mm, 12 V, ~0.1–0.2 A) | **SIN FUENTE** de consumo (páginas de UNIT no legibles desde mi entorno) | Etiqueta del ventilador + multímetro en serie a 8 V | pendiente | Alan |
| M22 | Ventilador: peso | ~10–15 g | **SIN FUENTE** | Báscula | pendiente | Alan |
| M23 | Cerámicos 100 nF, electrolíticos 470 µF: diámetro y paso de patas | 100 nF: 5 mm; 470 µF: ∅8 mm, paso 3.5 mm | **SIN FUENTE** (valores habituales) | Regla en las piezas del ticket | pendiente | Alan |
| M24 | Diodo 1N5822: distancia entre patas | 15.24 mm (huella DO-201AD horizontal) | KiCad (`D_DO-201AD_P15.24mm_Horizontal`) | Regla; si se dobla distinto, ajustar | pendiente | Alan |
| M25 | Transistor 2N2222: orientación de patas | Si es PN2222A plástico: E-B-C; si es metálico, no | Hoja de datos del fabricante; **varía** | Ver letras de la caja y probar con multímetro (modo diodo) antes de soldar | pendiente | Alan |
| M26 | Pulsadores (3 comprados): tamaño y paso de patas | 6 × 6 mm, 4 patas | Ticket | Regla | pendiente | Alan |
| M27 | Interruptor balancín: agujero de montaje y tamaño | ~19 × 13 mm | **SIN FUENTE** | Regla | pendiente | Alan |
| M28 | Fusible reseteable radial: paso de patas | 5.0 mm | **SIN FUENTE** | Regla | pendiente | Alan |
| M29 | Sensor de la barra: paso entre sensores | 7.5 mm (12 sensores = ~88 mm de ancho) | Cálculo del diseño (mismos 12 × 7.5 mm) | Decidir después de ver la pieza | pendiente | Equipo |

## 2. Chasis y reglamento

| ID | Tema | Valor propuesto | Fuente | Cómo confirmarlo | Estado | Quién |
|---|---|---|---|---|---|---|
| C01 | Espesor del acrílico | **3 mm** (espesores comunes: 2, 3, 5 mm) | Propuesta mía; 3 mm es el estándar más frecuente | Preguntar al taller qué tienen y su precio | pendiente | Equipo |
| C02 | Material del chasis | Acrílico, MDF o PLA. DXF de los tres | Decisión del equipo | Cotizar taller; probar impresión 3D | pendiente | Equipo |
| C03 | Dimensiones máximas del chasis | Caja de **200 × 100 mm** (largo × ancho) y 500 g totales; margen de diseño: placa ≤ 190 × 95 mm | Reglamento (proyecto "Seguidor Línea V2") | Releer reglas el 18 nov (pueden cambiar) | aceptada | Equipo |
| C04 | Peso del chasis | Acrílico 3 mm ≈ 50–70 g según el área; MDF 3 mm ≈ 45 g; PLA según relleno | Cálculo área × espesor × densidad (acrílico 1.18 g/cm³; PLA 1.24 g/cm³) | Pesar la pieza | pendiente | Equipo |
| C05 | Holgura de agujeros y ranuras | Láser: +0.2 mm, ranura = espesor medido +0.1; FDM: +0.3 mm | Skill `mecanica-dxf-autocad` (valores de arranque) | Cortar una pieza de prueba | pendiente | Equipo |
| C06 | Permiso por escrito para usar ventilador | Permitido según el repositorio | `docs/requisitos.md` | Correo a los organizadores | pendiente | Equipo |
| C07 | Altura mínima de la falda sobre la pista | 0 mm de contacto (nunca debe tocar) | Diseño | Probar con la pista real | pendiente | Equipo |
| C08 | Fecha de congelamiento del reglamento | 18 nov | Proyecto "Seguidor Línea V2" | Revisar al día siguiente | pendiente | Equipo |

## 3. Eléctrico y pruebas

| ID | Tema | Valor propuesto | Fuente | Cómo confirmarlo | Estado | Quién |
|---|---|---|---|---|---|---|
| E01 | MP1584 #1 salida | **5.0 V** antes de conectar nada | Diseño | Multímetro y tornillo del módulo | pendiente | Alan |
| E02 | MP1584 #2 salida | **6.0 V** antes de conectar motores | Diseño | Multímetro | pendiente | Alan |
| E03 | Diodo 1N5822 (D1 y D2): ¿buena caída directa y bloqueo inverso? | Ver sección 4 | Datasheet y guía abajo | Multímetro en modo diodo | pendiente | Alan |
| E04 | ERC oficial de KiCad | Los verificadores propios dan 0 errores. **El ERC oficial no se pudo correr** (KiCad 7 sin comando) | `electronica/kicad/NOTAS.md` | Abrir el proyecto en KiCad 8/9 → Inspeccionar → Verificar reglas eléctricas | pendiente | Alan |
| E05 | Divisor de batería 100 k / 33 k | 8.4 V → 2.08 V (ADC) | Cálculo | Medir con LiPo cargada | pendiente | Alan |
| E06 | Corriente de ventilador y fusible 1.5 A | ≤ 0.3 A del ventilador + motores < 1.5 A | Estimación | Multímetro en serie | pendiente | Alan |
| E07 | Revisar corto antes de conectar la LiPo | Continuidad entre +VBAT y GND debe ser abierta | Buena práctica | Multímetro | pendiente | Alan |

## 4. Cómo medir el diodo (1N5822)

**¿Qué diodo es?** El del ticket: **1N5822**, diodo *Schottky* (tipo con caída de voltaje baja y muy rápido) de 3 A y 40 V. Se compraron 2.
- **D1**: diodo de rueda libre del ventilador (protege al MOSFET de los picos al apagar el motor). Cátodo hacia +VBAT, ánodo hacia el drenador del MOSFET.
- **D2**: protección entre la salida de 5 V del MP1584 y el pin 5V del ESP32 (impide que la USB y la batería se peleen). Ánodo hacia el MP1584, cátodo hacia el ESP32.

**Material:** multímetro con símbolo de diodo (▶|). Diodo sin soldar.

**Paso a paso**
1. Gira el selector a **modo diodo**. Si no existe, no mides bien: avisa y ajustamos la prueba.
2. **Directa:** punta roja en el lado sin franja (**ánodo**), punta negra en el lado con franja (**cátodo**). Anota el número en pantalla.
3. **Inversa:** invierte las puntas (roja en la franja). Debe mostrar **OL** o "1" (abierto).
4. Repite con el otro diodo y anota.

**Valores esperados (orientativos, varían con el multímetro)**

| Tipo | Directa (modo diodo) | Inversa |
|---|---|---|
| Schottky (1N5822) | ~0.15–0.30 V (en un multímetro de corriente baja suele leerse menos de 0.35 V) | OL |
| Silicio normal (1N4007) | ~0.5–0.7 V | OL |
| Roto en corto | ~0.00 V en ambos sentidos | 0.00 V |
| Roto abierto | OL en ambos sentidos | OL |

Si lee ~0.55 V o más en directa, **no es Schottky** (lo cambiaron por uno de silicio): avísame, porque D2 bajaría más voltaje del que cabe en el ESP32.

**Cómo anotarlo** (copia y pega en este archivo, tabla E03):

`Diodo 1: directa = ___ V; inversa = ___ ; marca/letras en el cuerpo = ___ ; multímetro = ___`
`Diodo 2: directa = ___ V; inversa = ___ ; marca/letras en el cuerpo = ___`

Con una foto del cuerpo del diodo basta también. **Pregunta:** ¿el diodo del ticket dice "1N5822" en el cuerpo o solo el mostrador lo escribió? Si dice otra cosa, avísame.
