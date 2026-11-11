# Especificaciones de componentes (robot casero)

Rama `engineering/robot-casero`. Actualizado: **11 nov 2026** (medidas con **vernier** de Alan y respuestas por ID). Ningún ID se borra: los obsoletos se marcan como tales.
Cuando una medida nueva no coincide con la anterior o con una hoja de datos, se usa la de Alan más reciente y se anota la diferencia.
Regla de Alan (D17, 11 nov): las medidas de las fichas de UNIT valen como verdaderas; no se vuelven a pedir con vernier.

Estados: **vernier** = medido por Alan con vernier · **ficha** = dato del vendedor (UNIT) o datasheet · **referencia** = medido en
una pieza equivalente y aceptado por Alan para avanzar (verificar al recibir) · **provisional** = la huella existe pero falta el dato ·
**pendiente** = sin dato · **obsoleto**.

| ID | Componente | Medida tal como la dio Alan | En mm (diseño) | Fuente | Estado |
|---|---|---|---|---|---|
| M01 | ESP32 DevKit **30 pines** (clon, USB-C, ESP-WROOM-32) | 51.9 × 28.7 mm; 54 mm con el USB-C (antes, con regla: 5.1 × 2.8 cm) | 51.9 × 28.7 mm (contorno de la huella) | Alan, vernier 11 nov | vernier |
| M02 | ESP32: distancia entre filas de pines (centro a centro) | 25.5 mm | **25.4 mm** en la huella (paso estándar de 1 pulgada; la diferencia de 0.1 mm es tolerancia de medida) | Alan, vernier 11 nov | vernier |
| M03 | ESP32: orden de pines (USB-C arriba) | Izq.: 3V3, GND, D15, D2, D4, D16, D17, D5, D18, D19, D21, RX0, TX0, D22, D23. Der.: VIN, GND, D13, D12, D14, D27, D26, D25, D33, D32, D35, D34, VN, VP, EN | Pines 1–15 a la izquierda (arriba → abajo); 30 (VIN) a 16 (EN) a la derecha | Serigrafía (foto) | confirmado con la foto |
| M04 | ESP32: pines por lado | 15 por lado | 15 × 2.54 mm = 35.56 mm de fila | Alan + M03 | confirmado con la foto |
| M05 | Motorreductor N20 (medidas de referencia, P10) | Cuerpo 24.5 mm; eje que sobresale 8.5 mm (ahí entra el rin); total con eje 33 mm | Mismos valores. Alan: los GA12-N20 de UNIT tendrán casi seguro las mismas medidas; si al recibirlos difieren, se corrige | Alan, vernier 11 nov, sobre motores N20 que ya tenía | referencia |
| M06 | N20: ancho × alto del cuerpo | 12 × 10 mm | 12 × 10 mm. **Ojo:** el 6 nov se había anotado 5 mm de ancho en otros motores; se usa la medida nueva | Alan, vernier 11 nov | referencia |
| M07 | N20: agujeros de montaje del frente | — | **Obsoleto**: el motor se sujeta con el asegurador M31, no por el frente | — | obsoleto |
| M08 | Rueda: llanta de goma sobre rin con prisionero (ya las tienen) | Llanta ∅26.7 mm, 21.7 mm de ancho. Rin ∅21 mm, 22.1 mm de ancho. Agujero del rin 2.3 mm (P09) | Mismos valores (antes, con regla: llanta ∅28 × 21.5) | Alan, vernier 11 nov | vernier |
| M09 | Tamaño del módulo DRV8833 | Dibujo oficial de UNIT (7 nov): 16 × 18.5 mm, paso 2.54 mm. Sustituye 1.8 × 1.55 cm (regla, 6 nov) y 1.3 × 1.1 cm (5 nov) | **16 × 18.5 mm**; 2 filas de 6 pines a 2.54 mm. La separación entre filas **no está acotada**: ver M32 (el layout asume 15.24 mm) | Dibujo "Dimensiones DRV8833 Controlador Motor DC Dual" de UNIT, aportado por Alan | confirmado por dibujo del vendedor (tamaño); filas por confirmar (M32) |
| M10 | Módulo DRV8833: pines | Izq.: IN4, IN3, GND, VCC, IN2, IN1. Der.: EEP, OUT1, OUT2, OUT3, OUT4, ULT | EEP = nSLEEP, ULT = nFAULT (letras cortadas de "SLEEP" y "FAULT"), VCC = VM | Serigrafía (fotos) + datasheet TI | confirmado (foto + datasheet) |
| M11 | Chip DRV8833 (marca "DRV8833 82K CV25") | — | VM 2.7–10.8 V; **1.5 A RMS / 2 A pico por puente**; entradas lógicas hasta 5.75 V; nSLEEP alto = encendido (pulldown interno de 500 kΩ); nFAULT de drenador abierto, bajo = falla | [Datasheet TI DRV8833](https://www.ti.com/lit/ds/symlink/drv8833.pdf) (encapsulado PWP, el que dice "DRV8833") | **confirmado (datasheet)** |
| M12 | Módulo **MP1584** (reductor de voltaje) | 22.4 × 16.8 mm | 22.4 × 16.8 mm (contorno de la huella). Posición de los 4 agujeros: M33 | Alan, vernier 11 nov | vernier |
| M13 | MP1584: terminales | OUT− / OUT+ de un lado, IN− / IN+ del otro (confirmado por Alan, P03) | Huella: OUT a la izquierda, IN a la derecha | Alan | confirmado |
| M14 | LiPo 2S 450–500 mAh | — (por comprar fuera de UNIT) | Objetivo eléctrico: 2S, 7.4 V nominal / 8.4 V cargada, 450–500 mAh. Dimensiones y peso: **no fijar** hasta elegir modelo; 61 × 16 × 15 mm / ~30 g era solo referencia Tattu 450 | Requisito del proyecto; referencia Tattu 450 no seleccionada | pendiente |
| M15 | Conectores de la LiPo y cable JST-RC añadido al carrito | Alan informa 2 pares macho/hembra JST-RC; cable 22 AWG, 10 cm, pitch 2.5 mm | Descarga: JST-RC 2 pines; balanceo de batería 2S: JST-XH 3 pines. **Confirmar que el conector de descarga de la LiPo elegida coincide físicamente** | Ficha UNIT del par JST-RC + requisito 2S | pendiente de compatibilidad con batería |
| M16 | Módulo 74HC4067 (multiplexor, 16 canales) | Alan: aprox. 41 × 18 mm (regla). Ficha UNIT: 40 × 20 × 3 mm | **40 × 20 mm de la ficha UNIT** mientras Alan mide con vernier (pedido de Alan) | Ficha UNIT | ficha (vernier pendiente) |
| M17 | 74HC4067: orden de pines | — | VCC, GND, S0–S3, SIG, EN en una fila; C0–C15 en otra | sin fuente | pendiente |
| M18 | TCRT5000 suelto: cuerpo | Ficha UNIT: 10 × 5 × 7 mm, 0.3 g; Vishay: 10.2 × 5.8 × 7 mm | 10.2 × 5.8 × 7 mm según datasheet; 10 × 5 × 7 mm como redondeo de vendedor | UNIT (producto individual, no módulo) + datasheet Vishay | confirmado por datasheet; dimensiones del lote por verificar |
| M19 | TCRT5000: posición de las 4 patas | Alan (11 nov): **2 filas de 2 patas** (no 4 en línea) | Huella 2 × 2 **provisional**: 2.54 mm entre las patas de una fila y 5.08 mm entre filas. El dibujo de Vishay trae las cotas solo como imagen; faltan 2 medidas (ver pendientes) | Alan + datasheet Vishay | provisional |
| M20 | TCRT5000: orden A, K, C, E | — | A, K (LED); C, E (fototransistor) | datasheet; orden físico por ver | pendiente |
| M21 | Ventilador 4010 12 V añadido al carrito | Ficha UNIT: 40 × 40 × 10 mm; 12 V; 100 mA ±10 %; 1.2 W; 5000 RPM ±10 %; 5 CFM; cable 10 cm | 40 × 40 × 10 mm; 12 V; 90–110 mA nominal según tolerancia. Dibujo UNIT (7 nov): 4 agujeros Ø3.2 ±0.2 mm en cuadrado de 32 ±0.3 mm | Ficha y dibujo UNIT aportados por Alan | nominal de proveedor; verificar etiqueta y corriente real al recibirlo |
| M22 | Peso del ventilador 4010 | Ficha UNIT: 16 g | 16 g (dato del vendedor) | Ficha UNIT aportada por Alan | nominal de proveedor; verificar con báscula |
| M23 | Capacitores | Electrolítico ∅8 mm, 12.8 mm de alto, 4.1 mm entre patas. Cerámico: 5.5 mm entre patas | Electrolítico: huella CP_Radial_D8.0mm **P3.80 mm**. Cerámico: C_Disc **P5.00 mm**. Se usa el paso estándar más cercano; las patas son flexibles y la diferencia (0.3–0.5 mm) se absorbe al insertarlas | Alan, vernier 11 nov | vernier |
| M24 | Diodo **1N5822** (Schottky, D1 y D2) | Alan decide (11 nov) unos **20 mm** entre patas para no cortar ni doblar de más | Huella de **20.32 mm** (8 × 2.54), taladro 1.3 mm. Sustituye la de 15.24 mm | Decisión de Alan | decidido |
| M25 | Transistor 2N2222 TO-92, marca "H331" | **E – B – C** viendo la cara plana (Alan, 11 nov) | Huella TO-92_Inline_Wide: pad 1 = E, 2 = B, 3 = C, con la cara plana del dibujo hacia el frente: **coincide** | Alan + revisión de la huella | confirmado |
| M26 | Pulsadores | Pequeño 6 × 6 mm; mediano 12 × 12 mm; 5 mm entre patas en ambos | SW_PUSH_6mm (6.5 × 4.5 mm) y SW_PUSH-12mm (12.5 × 5.0 mm) de KiCad; el lado de 5 mm coincide | Alan, vernier 11 nov | vernier |
| M27 | **Interruptor de balancín KCD1 rojo** | 18.8 mm de largo × 6.7 mm de ancho; 16.5 mm de alto sin terminales, 25 mm con terminales (terminales de 8.5 mm) | **No va en la PCB**: se fija en la estructura (AutoCAD) y llega por 2 cables a SW1 (header de 2 pines). Solo enciende y apaga el robot | Alan, vernier 11 nov | vernier |
| M28 | Fusible reseteable (PTC) de la batería | Alan no lo encontró (11 nov); se quiere reseteable | Huella **provisional** radial de 5.08 mm (F1). Falta elegir la pieza real: ver pendientes | Decisión de Alan (P16) | provisional |
| M29 | Paso entre sensores de la "barra" | — | **Obsoleto**: no hay barra comercial; ver D05 (12 sensores a 7.5 mm) | — | obsoleto |
| M30 | **Rueda loca "Mini rueda universal 3Pi N20"** (comprada en UNIT) | Ficha UNIT: rueda libre, soporte de plástico, esfera de acero, 22 × 16 × 15 mm, 2 agujeros de fijación a ~15 mm, 10 g | Mismos valores (Alan: tomar la ficha como verdadera). Ver R03 por su altura de 15 mm | Ficha UNIT | ficha |
| M31 | Asegurador de plástico para motores N20 (**solo mecánico**, no va en la PCB) | Espesor 1.5 mm; 19.5 mm entre agujeros (Alan, 11 nov) | Se atornilla a la base de acrílico (AutoCAD). Sustituye el valor de 22 mm de `mecanica/autocad/parametros.yaml` | Alan | vernier |
| M32 | DRV8833: separación entre las dos filas de pines | **15.9 mm** | Huella con filas a 15.9 mm (antes 15.24 mm estimado de una imagen) | Alan, vernier 11 nov | vernier |
| M33 | MP1584: posición de los 4 agujeros (IN−, IN+, OUT−, OUT+) | — | Huella **provisional**: 19.5 mm entre los agujeros IN y OUT, 13.5 mm entre + y − | sin fuente | provisional |

**Decisión de diseño (no es medida):** los 12 sensores van a **7.5 mm** uno de otro en un arco de 110 mm de radio (ver D05 en
`decisiones-robot-casero.md`). El antiguo M29 ("paso de la barra") quedó **obsoleto**, no borrado (ver tabla).
