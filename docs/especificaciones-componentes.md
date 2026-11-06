# Especificaciones de componentes (robot casero)

Rama `engineering/robot-casero`. Actualizado: 6 nov 2026. Ningún ID se borra: los obsoletos se marcan como tales.
Medidas de Alan con **escalímetro** (precisión ~0.5 mm): se guardan en cm tal como las dio y se convierten a mm (cm × 10).
**Todas quedan "por confirmar con vernier"** (ver `pendientes-por-confirmar.md`, V01). Cuando una medida no coincide con una hoja de
datos o con lo esperado, se anota la diferencia, no se cambia en silencio.

Estados: **confirmado (datasheet)** = validado con hoja de datos oficial · **escalímetro** = medido por Alan, por confirmar con vernier ·
**nominal** = de internet o típico · **pendiente** = sin dato.

| ID | Componente | Medida tal como la dio Alan | En mm (diseño) | Fuente | Estado |
|---|---|---|---|---|---|
| M01 | ESP32 DevKit **30 pines** (clon, USB-C, chip ESP-WROOM-32) | Placa 5.1 × 2.8 cm; con el USB-C 5.4 cm (sobresale 0.3 cm) | 51 × 28 mm; 54 mm con USB-C | Alan, fotos de la placa | escalímetro |
| M02 | ESP32: distancia entre filas de pines (centro a centro) | 2.55 cm | **25.4 mm** en la huella (1 pulgada, estándar de los DevKit de 30 pines). La diferencia de 0.1 mm está dentro del error del escalímetro | Alan + estándar de 2.54 mm | escalímetro |
| M03 | ESP32: orden de pines (USB-C arriba) | Izq.: 3V3, GND, D15, D2, D4, D16, D17, D5, D18, D19, D21, RX0, TX0, D22, D23. Der.: VIN, GND, D13, D12, D14, D27, D26, D25, D33, D32, D35, D34, VN, VP, EN | Pines 1–15 a la izquierda (arriba → abajo); 30 (VIN) a 16 (EN) a la derecha | Serigrafía (foto) | confirmado con la foto |
| M04 | ESP32: pines por lado | 15 por lado | 15 × 2.54 mm = 35.56 mm de fila | Alan + M03 | confirmado con la foto |
| M05 | Motorreductor GA12-N20 6 V 1000 RPM | — | 34 mm total (eje ∅3 × 10 mm), 10 g, 0.07 A nominal, 1 A atasco | mikroelectron.com | nominal |
| M06 | N20: ancho × alto del cuerpo | — | 12 × 10 mm | valor típico | pendiente |
| M07 | N20: agujeros de montaje del frente | — | 2 × M1.6 a 9 mm | sin fuente | pendiente |
| M08 | Rueda: rin de aluminio + llanta de goma (Alan ya las tiene) | Rin ∅2.1 cm, 2.2 cm de alto; llanta ∅2.8 cm, 2.15 cm de alto (ancho) | Llanta ∅28 × 21.5 mm; rin ∅21 × 22 mm; tornillo prisionero lateral | Alan + fotos | escalímetro |
| M09 | Tamaño del módulo DRV8833 | 1.8 × 1.55 cm (6 nov, regla). La medida de 1.3 × 1.1 cm del 5 nov queda sustituida | 18 × 15.5 mm; 2 filas de 6 pines a 2.54 mm, filas a ~15.24 mm | Alan; cuadra con la foto | regla (por confirmar con vernier) |
| M10 | Módulo DRV8833: pines | Izq.: IN4, IN3, GND, VCC, IN2, IN1. Der.: EEP, OUT1, OUT2, OUT3, OUT4, ULT | EEP = nSLEEP, ULT = nFAULT (letras cortadas de "SLEEP" y "FAULT"), VCC = VM | Serigrafía (fotos) + datasheet TI | confirmado (foto + datasheet) |
| M11 | Chip DRV8833 (marca "DRV8833 82K CV25") | — | VM 2.7–10.8 V; **1.5 A RMS / 2 A pico por puente**; entradas lógicas hasta 5.75 V; nSLEEP alto = encendido (pulldown interno de 500 kΩ); nFAULT de drenador abierto, bajo = falla | [Datasheet TI DRV8833](https://www.ti.com/lit/ds/symlink/drv8833.pdf) (encapsulado PWP, el que dice "DRV8833") | **confirmado (datasheet)** |
| M12 | Módulo **MP1584** (reductor de voltaje, "buck") | 2.2 × 1.65 × 0.4 cm | 22 × 16.5 × 4 mm | Alan; coincide con sigmanortec (22 × 17 × 4) | escalímetro |
| M13 | MP1584: terminales | Izq.: OUT−, OUT+. Der.: IN−, IN+ | Huella: OUT a la izquierda, IN a la derecha; cada terminal tiene 2 agujeros | Serigrafía (foto) | confirmado con la foto |
| M14 | LiPo 2S 450–500 mAh | — | 61 × 16 × 15 mm, ~30 g (Tattu 450) | contexto del equipo | nominal (sin comprar) |
| M15 | Conectores de la LiPo | — | JST-RC 2 pines + JST-XH 3 pines | típico | pendiente |
| M16 | Módulo 74HC4067 (multiplexor, 16 canales) | — | 18 × 41 mm | Alan (mensaje anterior) | escalímetro (pendiente de vernier) |
| M17 | 74HC4067: orden de pines | — | VCC, GND, S0–S3, SIG, EN en una fila; C0–C15 en otra | sin fuente | pendiente |
| M18 | TCRT5000 suelto: cuerpo | — | 10.2 × 5.8 × 7 mm | Vishay | **confirmado (datasheet)** |
| M19 | TCRT5000: patas | — | 4 patas en línea a 2.54 mm | sin fuente | pendiente |
| M20 | TCRT5000: orden A, K, C, E | — | A, K (LED); C, E (fototransistor) | datasheet; orden físico por ver | pendiente |
| M21 | Ventilador (sin comprar) | — | 4010: 40 × 40 × 10 mm, 12 V, ~0.1–0.2 A | típico | pendiente |
| M22 | Peso del ventilador | — | ~10–15 g | típico | pendiente |
| M23 | Capacitores | Electrolítico: ∅0.8 cm, 0.3 cm entre patas. Cerámico: 0.7 cm entre patas | Electrolítico ∅8 mm, huella de 3.5 mm (estándar; Alan midió 3.0). Cerámico: huella de 7.5 mm | Alan | escalímetro |
| M24 | Diodo **1N5822** (Schottky, D1 y D2) | 3.5 cm entre patas (para no forzar las patas al doblarlas) | En la PCB de la opción A se usó la huella estándar de **15.24 mm** (taladro 1.6 mm) para que quepa; existen también las de 20.32 y 35.56 mm (O05, por decidir) | Alan + DO-201AD | pregunta (M24) |
| M25 | Transistor 2N2222 de plástico (TO-92), marca "H331" | — | Huella TO-92 de paso ancho (2.54 mm). Orden supuesto E-B-C (PN2222A); **el P2N2222A es C-B-E** | datasheets onsemi PN2222A / P2N2222A | pendiente (probar, P05) |
| M26 | Pulsadores | Mediano 1.2 × 1.2 cm, 0.5 cm entre patas. Pequeño 0.6 × 0.6 cm, 0.5 cm entre patas | Mediano: huella SW_PUSH-12mm (START). Pequeños: SW_PUSH_6mm (CAL, RESET) | Alan + fotos | escalímetro |
| M27 | **Interruptor de balancín KCD1** (6 A 250 V), 2 terminales de pala | 2 cm de ancho, 2.5 cm de largo con patas, 1.6 cm de cuerpo, 0.7 cm de alto | 20 × 16 × 7 mm de cuerpo; se cablea con 2 hilos al conector SW1 (no va soldado a la PCB) | Alan + fotos | escalímetro |
| M28 | Fusible reseteable radial | — | paso de 5 mm | sin fuente | pendiente |
| M29 | Paso entre sensores de la "barra" | — | **Obsoleto**: no hay barra comercial; ver D05 (12 sensores a 7.5 mm) | — | obsoleto |
| M30 | Rueda loca mini (sin comprar) | — | En la opción A se sustituye por un patín (O02); si se aprueba queda obsoleta | sin fuente | pregunta |
| M31 | Asegurador de motor N20 (foto 6 nov) | — | Supuesto: 14 × 16 mm, base de 1.5 mm, 2 agujeros de 2.2 mm a 22 mm | SIN FUENTE | pendiente |

**Decisión de diseño (no es medida):** los 12 sensores van a **7.5 mm** uno de otro en un arco de 110 mm de radio (ver D05 en
`decisiones-robot-casero.md`). El antiguo M29 ("paso de la barra") quedó **obsoleto**, no borrado (ver tabla).
