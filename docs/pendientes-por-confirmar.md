# Pendientes por confirmar (robot casero) — versión 7

Rama `engineering/robot-casero`. Actualizado: **11 nov 2026** con las medidas de vernier y las respuestas por ID de Alan.
Copia íntegra de la v6 (la última publicada): `docs/historial/pendientes-v6_2026-11-07_pre-compra-unit.md`.

**Cómo leer este archivo**
1. **Sección A — Activos:** lo único que falta. Cada fila dice qué falta, por qué importa y cómo se resuelve.
2. **Sección B — Resueltos y obsoletos:** ningún ID se borra. Aquí queda la respuesta de cada uno y dónde se aplicó.
3. **Sección C — Explicaciones detalladas** de los IDs que Alan pidió entender mejor (M19, M20, M21, M22, P13, C07, R01, R03).

IDs nuevos en esta versión: **M33, P19, C10, D18–D24**. Medidas completas: `especificaciones-componentes.md`.
Decisiones: `decisiones-robot-casero.md`. **Quién:** Alan, salvo que se diga otra cosa.

**¿Bloquea las PCB?** — **sí** = sin ese dato no se puede taladrar o planchar esa placa · **no** = la PCB puede avanzar.

---

## A. Pendientes activos

### Medidas y piezas (M)
| ID | Tema | Qué falta | ¿Bloquea las PCB? | Cómo resolverlo | Quién |
|---|---|---|---|---|---|
| M14 | LiPo 2S: medidas y peso | Elegir y comprar el pack (7.4 V, 450–500 mAh) | no | Al comprarla: medidas, peso y conector | Alan |
| M15 | LiPo: conectores | Que el conector de descarga de la LiPo coincida con el JST-RC comprado y que traiga balanceo JST-XH de 3 pines | no (J1 es un header de 2 pines con cable) | Comparar al comprar la LiPo | Alan |
| M16 | 74HC4067: medida con vernier | Por ahora se usan las de la ficha UNIT (40 × 20 mm), como pidió Alan | no | Medir con vernier cuando se pueda; si difiere más de 0.5 mm se corrige la huella | Alan |
| M17 | 74HC4067: orden y separación de sus pines | La huella supone: fila de control VCC, GND, S0, S1, S2, S3, SIG, EN y fila de canales C0–C15, a 15.24 mm. **Sin fuente** | **sí** (placa de sensores) | Foto de las dos caras del módulo, donde se lea la serigrafía de los pines, y distancia entre las dos filas | Alan |
| M19 | TCRT5000: posición de las patas | Ya se sabe que son 2 filas de 2. Faltan **2 medidas** (ver C.1) | **sí** (placa de sensores) | (a) distancia entre las 2 patas de una misma fila; (b) distancia entre las dos filas. Centro a centro, con vernier | Alan |
| M20 | TCRT5000: qué pata es cuál (A, K, C, E) | Saber cuál es el ánodo y cátodo del LED y el colector y emisor del sensor (ver C.2) | **sí** (si se invierte, el sensor no funciona) | Prueba de C.2 con multímetro, o foto de abajo del sensor | Alan |
| M21 | Ventilador 4010: consumo real con la LiPo | Es de 12 V; con 7.4–8.4 V gira más lento y puede no arrancar (ver C.3) | no | Conectarlo a la batería y medir la corriente | Alan |
| M22 | Ventilador: peso y sujeción | Ficha: 16 g. Más de 10 g que se caiga es falta (ver C.4) | no | Pesarlo (C04) y sujetarlo con sus 4 tornillos M3 | Alan |
| M28 | Fusible reseteable (PTC): elegir la pieza | Tipo decidido: **reseteable** (P16). Faltan los datos para comprarlo: corriente de mantenimiento (aprox. 2–3 A [E]), voltaje máximo ≥ 16 V, encapsulado radial y paso de patas | no (huella **provisional** F1 de 5.08 mm) | Buscar un PTC radial ≥ 16 V de 2–3 A; al comprarlo, medir el paso de patas y cambiar la huella | Alan / Claude |
| M33 | MP1584: posición de sus 4 agujeros (nuevo) | La huella supone 19.5 mm entre los agujeros IN y OUT y 13.5 mm entre + y −. Sin fuente | **sí** (placa principal) | Con vernier: distancia de IN+ a IN− y de IN+ a OUT+, centro a centro | Alan |

### Preguntas (P)
| ID | Tema | Qué falta | ¿Bloquea las PCB? | Cómo resolverlo | Quién |
|---|---|---|---|---|---|
| P13 | Señal de falla del DRV8833 (pin ULT) | Saber si se puede conectar al ESP32 sin dañarlo (ver C.5). Hoy la PCB **no** la conecta | no | Multímetro en resistencia entre ULT y VCC del DRV8833, sin alimentar | Alan |
| P18 | Mapa de pines del firmware | La PCB de KiCad manda (START = GPIO4, ventilador = GPIO17, 12 sensores con multiplexor, sin zumbador ni nFAULT). Falta pasar eso a `firmware/robot-casero/casero/config.h`, que hoy dice START = GPIO18, zumbador en GPIO4, nFAULT en GPIO15 y 8 sensores directos | no | Trabajo de Claude en la siguiente tanda (con pruebas del firmware) | Claude |
| P19 | Eje del motor contra agujero del rin (nuevo) | P09 dice agujero de **2.3 mm**; el BOM y la ficha de UNIT dicen motor con **eje en D de 3 mm**. Un eje de 3 mm no entra en 2.3 mm | no (es mecánico) | Medir el diámetro del eje de los motores cuando lleguen (o el de los motores de referencia) | Alan |

### Chasis (C)
| ID | Tema | Qué falta | ¿Bloquea las PCB? | Cómo resolverlo | Quién |
|---|---|---|---|---|---|
| C01 | Espesor del acrílico | Ideal: **3 mm máximo** (Alan) | no | Confirmar con el taller | Equipo |
| C02 | Material de la base | Acrílico, MDF o PLA | no | Decidir | Equipo |
| C04 | Peso total | Alan irá pesando las piezas; Claude las suma | no | Mandar pesos | Alan |
| C05 | Holgura de corte | Láser −0.2 mm; PLA +0.3 mm en agujeros | no | Pieza de prueba | Equipo |
| C07 | Falda del ventilador | Decidir si se usa (ver C.6) | no | Depende de R01 y de la prueba de succión | Equipo |
| C09 | Tornillos M2 y M3 | Dónde va cada uno (ver C.8) | no | — | — |
| C10 | Reacomodo mecánico por las PCB nuevas (nuevo) | La placa de sensores creció de 94 × 50 a **94 × 75 mm** porque ahora lleva el multiplexor (P15). Con el arreglo actual el robot pasaría de 200 mm de largo. También se corrigió en `generar_dxf.py` un desfase de 3.81 mm de las ventanas de los sensores. Falta regenerar los DXF | no para grabar; **sí** para fijar dónde van los agujeros de montaje | Elegir una opción de R01 y reacomodar en AutoCAD | Alan / Claude |

### Eléctrico (E)
| ID | Tema | Valor | ¿Bloquea las PCB? | Cómo resolverlo | Quién |
|---|---|---|---|---|---|
| E01 | MP1584 #1 (5 V) | Ajustar la salida a **5.0 V** antes de conectar nada | no | Alimentar IN+/IN− con 7–8.4 V sin nada en OUT; girar el tornillito hasta 5.00 V con el multímetro en OUT | Alan |
| E02 | MP1584 #2 (6 V motores) | Ajustar a **6.0 V** antes de conectar el DRV8833 | no | Igual que E01 | Alan |
| E03 | Diodos 1N5822 | Directa ~0.15–0.30 V, inversa OL | no | Sección D | Alan |
| E04 | ERC y DRC oficiales en KiCad 10 | **Hechos el 11 nov con KiCad 10.0.8 por el servidor MCP** (sin intervención de Alan): 0 errores de ERC y de DRC en las dos placas, 0 conexiones faltantes; solo avisos esperados. Informes en `electronica/kicad/<placa>/verificacion_kicad10/` | no | Se repiten cada vez que se regeneren las PCB (huellas confirmadas) | Claude (MCP) |
| E05 | Divisor de batería | 8.4 V → 2.08 V | no | Medir con la LiPo cargada | Alan |
| E06 | Corriente total | < 1.5 A estimado | no | Multímetro en serie | Alan |
| E07 | Corto antes de la LiPo | +VBAT–GND abierto | no | Multímetro | Alan |
| E08 | Brocas | 0.8 mm (resistencias, sensores, vías), 1.0 mm (headers, módulos, TO-220, PTC), 1.3 mm (1N5822), 3.2 mm (M3) | no | Comprar las que falten | Alan |
| E09 | Ruteo de las PCB de doble cara | **Las dos placas quedaron ruteadas al 100 %** (11 nov): sensores 0 conexiones faltantes, 37 vías; principal 0 faltantes, 29 vías (se reacomodó: ESP32 a la derecha, DRV8833 girado 180° de frente a él, J5 y botones junto a la columna de señales). DRC KiCad 7: 0 errores en ambas (solo avisos de serigrafía). Estado **C** (verificadas); pasan a **D** cuando se confirmen las huellas provisionales M17, M19, M20 y M33 y se regenere | ya no bloquea | Regenerar con `generar_pcb.py` tras cada medida nueva; archivos 1:1 en `electronica/kicad/<placa>/fabricacion/` | Claude |

### Riesgos (R)
| ID | Riesgo | Situación | Qué hacer | Quién |
|---|---|---|---|---|
| R01 | Posición del ventilador | Hoy va sobre un hueco de 34 mm de la PCB principal. Alan pide evaluar moverlo hacia adelante (ver C.7) | Alan elige una opción de C.7 | Alan |
| R03 | Altura de la rueda loca (15 mm) | **Sí hay problema**: la base queda a ~3.9 mm del piso y la rueda loca mide 15 mm (ver C.9) | Medir lo que pide C.9 y decidir cómo montarla | Alan |
| R04 | Verificación física de medidas y el límite de 200 × 100 mm | Alan medirá en físico; las medidas conocidas ya están en `mecanica/autocad/parametros.yaml` | Medir el robot armado | Alan |
| V01 | Medidas con vernier | Ya están todas, salvo el multiplexor (M16) | — | Alan |

---

## B. Resueltos y obsoletos (no se borran)
| ID | Tema | Resolución | Fecha | Dónde quedó |
|---|---|---|---|---|
| M01 | ESP32: tamaño | 51.9 × 28.7 mm; 54 mm con USB-C (vernier) | 11 nov | Huella `ESP32_DevKit_30`; especificaciones |
| M02 | ESP32: distancia entre filas | 25.5 mm (vernier) → huella a 25.4 mm (paso estándar) | 11 nov | Huella; especificaciones |
| M03 | ESP32: orden de pines | Serigrafía + pinout (P07) | 7 nov | Especificaciones |
| M04 | ESP32: pines por lado | 15 por lado a 2.54 mm | 6 nov | Huella |
| M05 | Motor N20: largo | Cuerpo 24.5 mm, eje 8.5 mm, total 33 mm. Referencia aceptada por Alan (P10) | 11 nov | `parametros.yaml`; especificaciones |
| M06 | Motor N20: ancho × alto | 12 × 10 mm (antes se había anotado 5 mm de ancho; manda la medida nueva) | 11 nov | `parametros.yaml`; especificaciones |
| M07 | N20: agujeros del frente | **Obsoleto**: se sujeta con el asegurador M31 | 6 nov | — |
| M08 | Rueda | Llanta ∅26.7 × 21.7 mm; rin ∅21 × 22.1 mm (vernier) | 11 nov | `parametros.yaml`; especificaciones |
| M09 | DRV8833: tamaño | 16 × 18.5 mm (dibujo UNIT) | 7 nov | Huella |
| M10 | DRV8833: orden de pines | IN4, IN3, GND, VCC, IN2, IN1 · EEP, OUT1…OUT4, ULT | 6 nov | Símbolo y huella |
| M11 | DRV8833: voltaje y corriente | VM 2.7–10.8 V, 1.5 A RMS por puente (datasheet TI) | 6 nov | Especificaciones |
| M12 | MP1584: tamaño | 22.4 × 16.8 mm (vernier). Agujeros: M33 | 11 nov | Huella |
| M13 | MP1584: terminales | OUT−/OUT+ y IN−/IN+ (confirmado en P03) | 11 nov | Huella |
| M18 | TCRT5000: cuerpo | 10.2 × 5.8 × 7 mm (datasheet) | 6 nov | Huella |
| M23 | Capacitores | Electrolítico ∅8 × 12.8 mm, 4.1 mm entre patas → huella de 3.8 mm; cerámico 5.5 mm → huella de 5.0 mm (paso estándar; las patas se acomodan) | 11 nov | Huellas en `generar_principal.py` y `generar_sensores.py` |
| M24 | 1N5822: separación de patas | **Decisión de Alan: ~20 mm** → huella de 20.32 mm, taladro 1.3 mm (D1 y D2) | 11 nov | D21; huella |
| M25 | 2N2222 H331: orden de patas | **E-B-C** viendo la cara plana. La huella TO-92_Inline_Wide coincide (pad 1 = E con la cara plana al frente) | 11 nov | Placa de sensores, Q1 |
| M26 | Pulsadores | 6 × 6 y 12 × 12 mm, 5 mm entre patas | 11 nov | Huellas SW_PUSH_6mm y SW_PUSH-12mm |
| M27 | Interruptor KCD1 rojo | 18.8 × 6.7 mm, 16.5 mm de alto (25 con terminales). **Cableado**, fijo en la estructura | 11 nov | SW1 = header de 2 pines; mecánica |
| M29 | Paso de la "barra" | **Obsoleto**: no hay barra (D05) | 5 nov | — |
| M30 | Rueda loca | **Mini rueda universal 3Pi N20** (UNIT): 22 × 16 × 15 mm, agujeros a 15 mm, 10 g. Medidas de la ficha como verdaderas | 11 nov | D23; `parametros.yaml`; ver R03 |
| M31 | Asegurador de motor N20 | **Solo mecánico** (no va en la PCB): espesor 1.5 mm, 19.5 mm entre agujeros | 11 nov | `parametros.yaml` |
| M32 | DRV8833: separación entre filas | **15.9 mm** (vernier) | 11 nov | Huella `Modulo_DRV8833` |
| P01 | Tamaño del DRV8833 | Resuelto con M09 | 6 nov | — |
| P02 | ¿La pieza de M12 es el MP1584? | Sí | 11 nov | M12 |
| P03 | ¿El módulo OUT−/OUT+ e IN−/IN+ es el MP1584? | Sí (Alan) | 11 nov | M13 |
| P04 | ¿La pieza de M24 es el 1N5822? | Sí; separación según M24 | 11 nov | M24 |
| P05 | Orden de patas del 2N2222 | Resuelto en M25 | 11 nov | M25 |
| P06 | ¿Es el interruptor KCD1? | Sí, rojo KCD1; solo enciende y apaga; va cableado y fijo | 11 nov | M27 |
| P07 | ESP32: ¿VIN o VN arriba a la derecha? | VIN | 7 nov | Huella |
| P08 | Puente J1 del DRV8833 | No soldarlo | 6 nov | D14 |
| P09 | Rin | Rin con prisionero; agujero de 2.3 mm (ver P19 por el eje de 3 mm) | 11 nov | M08 |
| P10 | Medidas de los motores | Usar M05/M06 como referencia para avanzar | 11 nov | `parametros.yaml` |
| P11 | Distancia entre patas de capacitores | Resuelto en M23 | 11 nov | M23 |
| P12 | Opción de diseño | **Opción A**: todo en una sola placa de acrílico, sin niveles | 11 nov | D22 |
| P14 | Zumbador | **Se quita** del diseño: es un buzzer y no se necesita. La PCB de KiCad no lo tiene; falta quitarlo del firmware (P18) | 11 nov | D19 |
| P15 | Sensores y multiplexor | Sensores + multiplexor + transistor de emisores en la **placa de sensores**; a la principal van 8 hilos | 11 nov | D20; esquemáticos |
| P16 | Fusible | Tipo: **reseteable**. La pieza exacta queda en M28 | 11 nov | D24; F1 provisional |
| P17 | ¿Qué son las "ruedas 3Pi"? | Ruedas locas (M30) | 11 nov | BOM |
| C03 | Tamaño máximo | 200 × 100 mm y 500 g (reglamento). No se busca usar el máximo: siempre ahorrar espacio y peso | 11 nov | Reglamento |
| C06 | Permiso para el ventilador | Confirmado (D08) | 5 nov | — |
| C08 | Cambio del reglamento | No cambiará (Alan) | 11 nov | — |
| R02 | Puentes de alambre | Se resuelve con **PCB de doble cara** (D18) | 11 nov | E09 |

---

## C. Explicaciones detalladas

### C.1 — M19: posición de las patas del TCRT5000
El TCRT5000 tiene 4 patas: dos del LED infrarrojo (fila 1) y dos del fototransistor (fila 2). Para dibujar los agujeros de
la PCB necesito saber **dónde cae cada pata**. La huella actual es provisional: 2.54 mm entre las patas de una fila y 5.08 mm
entre filas. Si eso no coincide con la pieza real, las patas no entran en los agujeros y la placa de sensores se tira.
**Qué medir, centro a centro y con vernier:** (a) entre las 2 patas de una misma fila; (b) entre una fila y la otra.
Truco: apoyar el sensor sobre una tira de cartón para que las patas lo perforen, y medir los agujeros.

### C.2 — M20: qué pata es cuál
- **A** (ánodo) y **K** (cátodo) son del LED infrarrojo; **C** (colector) y **E** (emisor) son del fototransistor.
- **Si se invierte A con K**, el LED no prende. **Si se invierte C con E**, el sensor no da lectura.
- **Prueba del LED:** con el multímetro en modo diodo, entre las dos patas del lado del LED (normalmente el de lente azulada o transparente), una dirección marca ~1.0–1.2 V y la otra OL. Donde marca, la punta roja está en **A** y la negra en **K**. Con la cámara del celular se ve el LED prender.
- **Prueba del fototransistor:** con las dos patas del otro lado en modo diodo, cubre el sensor y luego ilumínalo con el LED de otro TCRT5000 o con un control remoto. El valor cambia solo con la punta roja en **C** y la negra en **E**.
- **Alternativa:** manda una foto de la cara de abajo del sensor y lo reviso.

### C.3 — M21: consumo del ventilador
El 4010 que compraron es de **12 V**, y la batería da 7.4–8.4 V. Va a girar más lento que en la ficha y, con PWM bajo, puede
no arrancar. **No afecta a la PCB:** el MOSFET IRLZ44N y el diodo aguantan de sobra 100 mA. Sirve para saber si mueve aire
suficiente y desde qué PWM arranca, para el firmware. **Prueba:** rojo a + y negro a − de la batería, el multímetro en serie
en mA, y anotar la corriente y si arranca.

### C.4 — M22: peso y sujeción del ventilador
El reglamento sanciona que se caiga del robot una pieza de más de 10 g, y el ventilador pesa 16 g. Hay que pesarlo para la
suma total (C04) y sujetarlo con sus **4 tornillos M3** (agujeros de Ø3.2 en un cuadrado de 32 mm, ya están en la PCB). No
basta con cinta.

### C.5 — P13: señal de falla del DRV8833 (pin ULT)
- **Qué es:** el DRV8833 tiene un pin llamado **ULT** (nFAULT) que se pone en 0 V cuando el driver se calienta demasiado o un motor pide demasiada corriente. Si se conecta a una entrada del ESP32, el programa se entera de la falla y puede parar los motores o avisar.
- **El problema:** ese pin solo sabe "jalar a 0 V" (drenador abierto). Para leerlo hace falta una resistencia que lo suba a "1". El ESP32 tiene una interna de 3.3 V que sirve, pero no sabemos si el **módulo** trae otra resistencia hacia el voltaje de los motores (6 V); en la foto hay resistencias, sin esquema. Si la trae y se conecta ULT al ESP32, entrarían 6 V a un pin que aguanta 3.3 V y se puede dañar.
- **Situación hoy:** la PCB de KiCad **no conecta** ULT (queda libre). El robot funciona sin ella, porque el chip se protege solo y se apaga si se calienta.
- **Qué necesito:** con todo desconectado, el multímetro en resistencia entre **ULT** y **VCC** del módulo.
  - "OL" (sin resistencia): es seguro conectarlo y lo agrego a la PCB con un pin libre del ESP32.
  - Algunos kΩ: no se conecta (o se agrega un divisor).

### C.6 — C07: qué es la "falda"
La falda es una **tira delgada y flexible** (acetato, plástico de botella o hule espuma delgado) que se pega alrededor de la
parte de abajo del robot, o solo alrededor de la zona del ventilador, y baja hasta casi tocar el piso.

- **Función:** cerrar el espacio entre la base y el piso. Así, cuando el ventilador saca el aire de abajo hacia arriba, se forma un vacío pequeño que **empuja el robot contra la pista** y le da más agarre en curvas.
- **Sin falda**, el aire entra por los lados y la succión casi no se nota.
- **Dónde va:** debajo de la base de acrílico, rodeando el hueco del ventilador. No debe tocar la pista con fuerza, porque frena.
- **Cómo afecta a los sensores:** los sensores deben quedar **fuera** de la zona cerrada, o la falda no debe taparles la vista ni reflejar su luz.
- **Cómo afecta al ventilador:** sin falda, el ventilador casi no sirve para agarre.
- **Con un 4010 de 12 V a 7.4 V la succión será pequeña** (R01, M21). Por eso la falda queda pendiente hasta medir con báscula si vale la pena.

### C.7 — R01: dónde poner el ventilador
| Opción | Qué es | Ventajas | Desventajas |
|---|---|---|---|
| **A (actual)** | Ventilador sobre el hueco de 34 mm de la PCB principal | Sin cables extra; ya está ruteada | La PCB principal mide 90 × 106 mm por el hueco; con la placa de sensores nueva (75 mm) el robot pasa de 200 mm de largo |
| **B (recomendada)** | Sacar el ventilador de la PCB: va en su propio hueco de la base de acrílico, entre los motores y la placa de sensores; se conecta con 2 cables a J4 | La PCB principal se acorta unos 40 mm y deja lugar para la placa de sensores más grande. La succión queda más cerca del centro del robot | Hay que rediseñar la base en AutoCAD y regenerar la PCB principal sin el hueco. Menos espacio entre los motores |
| **C** | Quitar el ventilador | −16 g, −100 mA, menos piezas | Se pierde el posible agarre extra |

### C.8 — C09: dónde va cada tornillo
| Medida | Dónde | Qué sujeta |
|---|---|---|
| **M3** (kit de latón: separadores de 6–20 mm, tornillos y tuercas) | PCB principal (3 agujeros), placa de sensores (3 agujeros) y ventilador (4 agujeros a 32 mm) | Las dos PCB a la base de acrílico con separadores, y el ventilador |
| **M2** (vienen con el asegurador, 2 tornillos M2 × 7 mm + tuercas por asegurador) | Base de acrílico | Los aseguradores de los motores N20 (agujeros a 19.5 mm) |
| Por definir | Rueda loca 3Pi (agujeros a 15 mm) | Depende de R03; normalmente lleva tornillos M2 |

### C.9 — R03: altura de la rueda loca
- **Altura de la base:** la llanta mide ∅26.7 mm, así que el eje del motor queda a 13.35 mm del piso. El motor (10 mm de alto) va encima de la base sobre el asegurador (1.5 mm), así que la cara de arriba de la base queda a 13.35 − 5 − 1.5 ≈ **6.85 mm**. Con acrílico de 3 mm, **la cara de abajo de la base queda a ~3.9 mm del piso**.
- **El problema:** la rueda loca mide **15 mm** de alto. Atornillada debajo de la base, levantaría ese extremo del robot unos 11 mm. El robot quedaría inclinado y los sensores lejos del piso: el TCRT5000 lee mejor a ~2.5 mm y pierde contraste rápido al alejarse. **No funcionaría así.**
- **Solución 1 (recomendada):** hacer un hueco en la base y meter la rueda loca **desde arriba**, de modo que solo salga por abajo la parte de la esfera que hace falta (~3.9 mm).
- **Solución 2:** subir todo el robot (motores debajo de la base). Eso aleja los sensores del piso, y habría que bajarlos con separadores.
- **Qué necesito:** la distancia desde la cara donde se apoyan las orejas de los tornillos de la rueda loca hasta la parte de abajo de la esfera. Con eso dibujo el hueco.

---

## D. Cómo medir los diodos 1N5822 (E03)
1. Multímetro en **modo diodo** (▶|). 2. Directa: roja al lado sin franja, negra a la franja → ~0.15–0.30 V.
3. Inversa: al revés → **OL**. 4. ~0.55 V o más = no es Schottky; 0.00 en ambos sentidos = en corto.
Anotar: `Diodo 1: directa ___ V, inversa ___ · Diodo 2: directa ___ V, inversa ___ · letras del cuerpo ___`
