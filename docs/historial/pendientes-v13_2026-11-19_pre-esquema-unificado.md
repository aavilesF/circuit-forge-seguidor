# Pendientes por confirmar (robot casero) — versión 13 (rama seguidor-caseroV2)

Rama `engineering/robot-casero`. Actualizado: **12 nov 2026** con las respuestas de Alan, fichas oficiales de UNIT y datasheets (TCRT5000 Vishay, 74HC4067 Philips).
Copia íntegra de la v7: `docs/historial/pendientes-v7_2026-11-11_pre-V2.md`. Los IDs P-V2-xx vienen de `v2/docs/`.

**Cómo leer este archivo**
1. **Sección A — Activos:** lo único que falta. Cada fila dice qué falta, por qué importa y cómo se resuelve.
2. **Sección B — Resueltos y obsoletos:** ningún ID se borra. Aquí queda la respuesta de cada uno y dónde se aplicó.
3. **Sección C — Explicaciones detalladas** de los IDs que Alan pidió entender mejor (M19, M20, M21, M22, P13, C07, R01, R03).

v13 (15 nov, tarde): P-V2-27 resuelto; PCB aprobadas por Alan; patrones de planchado generados (D-V2-39). Copia de la v12: `docs/historial/pendientes-v12_2026-11-15_pre-planchado.md`.

v12 (15 nov): P-V2-37, P-V2-41 y P-V2-44 pasan a resueltos/aparcados; P-V2-27 queda a la espera del OK final. Copia de la v11: `docs/historial/pendientes-v11_2026-11-15_pre-diodos-20mm.md`.

v11 (15 nov, tarde): respuestas de Alan: P-V2-39, 40, 42, 43 resueltos; P-V2-37 autorizado (D-V2-33, falta ejecutar); nuevo P-V2-45.

v10 (15 nov): sincronización total con el inventario (`v2/inventario.csv`) y las decisiones D-V2-24 a D-V2-32. Resueltos: P-V2-31, 32, 35, 36, 38. IDs nuevos: **P-V2-39 a P-V2-44**. Copia de la v9: `docs/historial/pendientes-v9_2026-11-15_pre-mantenimiento.md`. Fila duplicada de M18 unificada.

v9 (14 nov): optimización de las dos PCB aprobada por Alan. Copia de la v8: `docs/historial/pendientes-v8_2026-11-14_pre-optimizacion.md`. IDs nuevos: **P-V2-34 a P-V2-38**.
IDs nuevos en la v8: **M33, P19, C10, D18–D24**. Medidas completas: `especificaciones-componentes.md`.
Decisiones: `decisiones-robot-casero.md`. **Quién:** Alan, salvo que se diga otra cosa.

**¿Bloquea las PCB?** — **sí** = sin ese dato no se puede taladrar o planchar esa placa · **no** = la PCB puede avanzar.

---

## A. Pendientes activos

Estados de medida: **vernier** (Alan) · **UNIT** (ficha oficial del vendedor, válida por decisión de Alan) · **datasheet** · **estimado**.

| ID | Tema | Qué falta | ¿Bloquea? | Cómo resolverlo | Quién |
|---|---|---|---|---|---|
| P-V2-29 | Posición del ventilador / chasis | El ventilador se queda y se atornilla al acrílico (D-V2-26). Orden propuesto por Alan: ruedas atrás, PCB principal, ventilador, sensores al final; batería junto o sobre los motores (D-V2-27). Falta validarlo con medidas en AutoCAD; si los motores no dejan espacio, se quita | no | Etapa 3 (mecánica) | Equipo |
| P-V2-33 | Capucha para sensores | Alan acepta la capucha, que puede ser algo plana, y mi ayuda (D-V2-30). Falta el diseño: pieza negra mate a 1–2 mm del piso y compensación de luz ambiente por firmware | no | Etapa 3 | Equipo |
| P-V2-34 | **Ancho total del robot (ruedas)** | Con 2 N20 espalda con espalda ≈ 95 mm sin terminales; con terminales y cable soldado **~99–101 mm** (límite 100 mm). Alan decidió recortar el acrílico hacia dentro en la zona de los motores y dejarlos lo más juntos posible (D-V2-28). Falta medir | **sí, para la mecánica** | Medir con vernier un motor con terminales y cable soldado, y la posición del rin en el eje | Alan |
| P-V2-16 | Cable entre placas: 9 hilos | Hace falta cable de 9 hilos y una tira de 1×9 por placa. **Cómo pedirlo en la tienda:** "cable plano de 10 conductores (se separa 1) o cable multiconductor 9 hilos, calibre 24–28 AWG, ~30 cm" y "tira de pines macho 2.54 mm, 1 fila, se corta a 9". Alternativa: cable UTP (8) + 1 hilo suelto | no | Compra | Alan |
| P-V2-07 | Headers | Alan usará **tira hembra** en la PCB para ESP32, MP1584, DRV8833 y mux (módulos con pines macho). No se dibujan en el esquema | no (PCB) | Considerar alturas y pasos en la etapa 2 | Claude |
| P-V2-20 | EN ESTUDIO: encoders y aprendizaje de pista | Ver `v2/docs/evaluaciones.md`. Recomendación: no cambiar hardware; opcional reservar 4 GPIO en un header | no | Alan decide | Alan |
| P-V2-21 | EN ESTUDIO: ¿vale la pena el ventilador? | Ver `v2/docs/evaluaciones.md`. No se quita; probar con báscula | no | Pruebas físicas | Alan |
| M14 | LiPo 2S | Comprar (7.4 V, 450–500 mAh) | no | Al comprarla: medidas, peso, conector | Alan |
| M15 | Conector de la LiPo | Que coincida con el JST-RC comprado | no | Al comprar | Alan |
| M21 | Ventilador: corriente real a 7.4–8.4 V | Medir | no | Multímetro en serie | Alan |
| M28 | PTC | **Elegido (D-V2-24): Bel Fuse 0ZRE0150FF1A**, 1.5 A mantenimiento. No comprado; ver P-V2-44 | no | Comprar; medir paso de patas (10.2 mm esperado) | Alan |
| M33 | MP1584: posición de agujeros | Ahora la da la huella de Alan (19.5–20.5 mm entre lados, 2.54 mm entre agujero cuadrado y redondo); verificar al montar | no | Plantilla 1:1 | Alan |
| P13 | ULT (nFAULT) del DRV8833 | Sigue sin conectar | no | Medir ULT–VCC sin alimentar | Alan |
| P18 | Firmware | Pasar el mapa de pines V2 a `config.h` (no autorizado aún) | no | Etapa futura | Claude |
| C01, C02, C04, C05, C07, C09, C10 | Chasis | Igual que v7 (sección C) | no | Etapa 3 | Equipo |
| R01, R03, R04 | Ventilador, altura de rueda loca, verificación física | Igual que v7 | no | Etapa 3 | Alan |
| E01 | MP1584 #1 (5 V) | Ajustar a 5.0 V antes de conectar nada | no | Sección C del historial v7; multímetro en OUT | Alan |
| E02 | MP1584 #2 (6 V motores) | Ajustar a 6.0 V antes de conectar el DRV8833 | no | Igual que E01 | Alan |
| E03 | Diodos 1N5822 | Directa ~0.15–0.30 V, inversa OL (sección D). Cuenta física: P-V2-39 | no | Sección D | Alan |
| E05 | Divisor de batería | 8.4 V → 2.08 V | no | Medir con la LiPo cargada | Alan |
| E06 | Corriente total | < 1.5 A estimado (relevante para el PTC de 1.5 A, D-V2-24) | no | Multímetro en serie | Alan |
| E07 | Corto antes de la LiPo | +VBAT–GND abierto | no | Multímetro | Alan |
| E08 | Brocas | 0.8 mm (resistencias, sensores, vías), 1.0 mm (headers, módulos, TO-220, PTC), 1.3 mm (1N5822), 3.2 mm (M3) | no | Comprar las que falten | Alan |
| P-V2-45 | Pieza no anotada por la electrónica | Alan dice que la tienda le vendió una pieza que se olvidó anotar y que, si no es necesaria, no hay problema; si al armar hace falta, avisa. **Falta saber cuál es.** | no | Alan dice qué pieza fue | Alan |

## B. Resueltos y obsoletos (no se borran)
| ID | Tema | Resolución | Fecha | Dónde quedó |
|---|---|---|---|---|
| P-V2-28 | Dibujos en Edge.Cuts de las huellas ESP32 y HC4067 | **Resuelto 14 nov (Alan aprueba):** eran 4 círculos de los agujeros del DevKit y el contorno de 40 × 20 mm del módulo; pasados a Dwgs.User en las PCB y en las bibliotecas de origen (copia `.antes_edgecuts_2026-11-14.bak`). Pads sin cambios (comprobado) | 14 nov | `Librerias/Footprints`, `v2/electronica/bibliotecas` |
| P-V2-30 | USB-C bloqueado por SW2 | **Resuelto 14 nov:** el ESP32 se bajó hasta que su USB-C queda en el borde inferior de la PCB principal (en el dibujo); SW2 pasó a la derecha del USB y SW3/SW4 arriba del ESP32. Ningún componente queda en el camino del enchufe (pasillo libre de x 44 a 53 mm hacia fuera de la placa). Falta que la mecánica deje libres ~30 mm detrás del borde para el enchufe y la curva del cable | 14 nov | `v2/electronica/principal` |
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
| M23 | Capacitores | Electrolítico ∅8 × 12.8 mm, 4.1 mm entre patas → huella de 3.8 mm; cerámico 5.5 mm → huella de 5.0 mm (paso estándar; las patas se acomodan) | 11 nov | Huellas en `generar_principal.py` y `generar_sensores.py` |
| M24 | 1N5822: separación de patas | **Decisión de Alan: ~20 mm** → huella de 20.32 mm, taladro 1.3 mm (D1 y D2) | 11 nov | D21; huella |
| M25 | 2N2222 H331: orden de patas | **E-B-C** viendo la cara plana. La huella TO-92_Inline_Wide coincide (pad 1 = E con la cara plana al frente) | 11 nov | Placa de sensores, Q1 |
| M26 | Pulsadores | 6 × 6 y 12 × 12 mm, 5 mm entre patas | 11 nov | Huellas SW_PUSH_6mm y SW_PUSH-12mm |
| M27 | Interruptor KCD1 rojo | 18.8 × 6.7 mm, 16.5 mm de alto (25 con terminales). **Cableado**, fijo en la estructura | 11 nov | SW1 = header de 2 pines; mecánica |
| M29 | Paso de la "barra" | **Obsoleto**: no hay barra (D05) | 5 nov | — |
| M30 | Rueda loca | **Mini rueda universal 3Pi N20** (UNIT): 22 × 16 × 15 mm, agujeros a 15 mm, 10 g. Medidas de la ficha como verdaderas | 11 nov | D23; `parametros.yaml`; ver R03 |
| M31 | Asegurador de motor N20 | **Solo mecánico** (no va en la PCB): espesor 1.5 mm, 19.5 mm entre agujeros | 11 nov | `parametros.yaml` |
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
| M16 | 74HC4067: medida | **40 × 20 mm, ficha UNIT** (vale como oficial, D17 y 12 nov) | 12 nov | Imagen "Dimensiones 74HC4067" UNIT |
| M17 | 74HC4067: orden de pines | **Resuelto**: lado izquierdo C15…C0 (arriba→abajo); lado derecho SIG, S3, S2, S1, S0, EN, VCC, GND (arriba→abajo). EN activo en bajo con pull-down de 10 k en el módulo (esquemático UNIT); se ata a GND. El símbolo de Alan usa esos mismos nombres | 12 nov | Pinout y esquemático UNIT + datasheet 74HC4067 |
| M18 | TCRT5000: cuerpo | 10 × 5 mm (UNIT); 10.2 × 5.8 × 7 mm (Vishay) | 12 nov | UNIT + Vishay |
| M19 | TCRT5000: posición de patas | **Resuelto**: 2 × 2, se usará la **huella oficial de KiCad**, que corresponde al sensor comprado (Alan) | 12 nov | Alan + KiCad oficial (P-V2-13) |
| M20 | TCRT5000: A, K, C, E | **Resuelto**: con las patas hacia el observador y los ópticos al frente: arriba-izq. **ÁNODO**, arriba-der. **COLECTOR**, abajo-izq. **CÁTODO**, abajo-der. **EMISOR**. LED (A–K) y fototransistor (C–E) quedan en lados opuestos, como en el datasheet y la foto de UNIT (lente azul = LED) | 12 nov | Alan + pinout UNIT + Vishay |
| M28 | PTC (selección) | Referencia de compra elegida: 1.5 A, ≥ 16 V (sigue en A hasta comprarlo) | 12 nov | Alan |
| P19 | Eje del motor vs rin | **Resuelto**: el eje mide **≈ 2.3 mm de diámetro**; los "3 mm" eran una longitud. Entra en el rin de 2.3 mm. El eje sobresale 8.5 mm (M05) | 12 nov | Alan |
| E09 | Ruteo de las PCB anteriores | **Obsoleto**: las PCB de `electronica/kicad/` son históricas; la V2 se diseña desde cero | 12 nov | `v2/README.md` |
| E04 | ERC/DRC de la versión anterior | **Obsoleto** (diseño anterior). ERC V2: ver `v2/docs/conexiones.md` | 12 nov | — |
| V01 | Medidas con vernier | Las fichas UNIT valen como oficiales mientras tanto | 12 nov | Alan |
| P-V2-01 | MP1584: pin IN+ sin número | **Resuelto**: el símbolo tenía IN+ con número vacío y la huella numeraba sus 8 agujeros solo 1 y 2 (habría unido IN+ con OUT+). Corregido: símbolo IN+ = 1; huella 1 IN+, 2 IN−, 3 OUT−, 4 OUT+ (cada borne tiene 2 agujeros con el mismo número). Copias de respaldo `.bak` en la biblioteca | 12 nov | Autorización de Alan |
| P-V2-02 | DRV8833: dibujo de pines | **Sin cambio**: no es error eléctrico. Los 12 pines tienen nombre y número correctos (1 EEP, 2–5 OUT1–4, 6 ULT, 7 IN1, 8 IN2, 9 GND, 10 VCC, 11 IN3, 12 IN4) y la huella usa los mismos números. Solo el extremo de conexión queda dentro del recuadro | 12 nov | Revisión |
| P-V2-03 | Valor del PTC | Ver M28 y D-V2-24 | 12 nov | Alan |
| P-V2-05 | IRLZ44N a 3.3 V | Apto para el ventilador de 100 mA; no se cambia | 12 nov | Datasheet IR: VGS(th) ≤ 2 V |
| P-V2-06 | Botón RESET | **Se queda** en la PCB (SW4 a EN) | 12 nov | Alan |
| P-V2-08 | Módulos soldados vs. removibles | Removibles con tira hembra (P-V2-07) | 12 nov | Alan |
| P-V2-09 | Símbolo TCRT5000 | KiCad 10 no tiene símbolo oficial (comprobado con el MCP); se usa el de Alan (pines A, CATH, COLL, E). La huella sí será la oficial | 12 nov | MCP + Alan |
| P-V2-10 | Medidas de la placa de sensores | Se definen en la etapa 2 dentro del reglamento | 12 nov | — |
| P-V2-04 | LED de sensores a 5 V | **Aprobado (13 nov) y aplicado**: ánodos a +5V (salida del MP1584 de 5 V) por un 9.º hilo; R1–R12 = 220 Ω (~17 mA c/u, ~200 mA total); R25 = 470 Ω. Pull-ups de 10 k y mux siguen en +3V3: SIG nunca pasa de 3.3 V | 13 nov | Alan |
| P-V2-23 | Huellas asignadas en los esquemáticos | **Hecho (13 nov)**: campo Footprint lleno con huellas oficiales o de Alan; una etiqueta de nombre por red para que la PCB reciba los mismos nombres | 13 nov | DRC paridad |
| P-V2-15 | ¿Esquemáticos terminados? | **Sí (13 nov)**: ERC KiCad 10 principal 0/0; sensores 0 errores, 4 avisos sin efecto. Vistas en `v2/electronica/vistas/` | 13 nov | ERC MCP |
| M22 | Ventilador: peso | **15 g medido** (Alan, báscula 13 nov); la ficha decía 16 g | 13 nov | Alan |
| M32 | DRV8833: medidas finales | Filas **15.7 mm** y paso **2.54 mm** (Alan 13 nov; sustituye 15.9 y 15.5) | 13 nov | Alan |
| P-V2-12 | MP1584: huella | **Resuelto (13 nov, aprobado por Alan)**: vista superior → par de arriba (redondos) IN− izq./OUT− der.; par de abajo (cuadrados) IN+ izq./OUT+ der. Pads: 1 IN+ abajo-izq., 2 IN− arriba-izq., 3 OUT− arriba-der., 4 OUT+ abajo-der. Símbolo sin cambio | 13 nov | Fotos de Alan |
| P-V2-13 | TCRT5000: símbolo vs huella oficial | **Resuelto**: símbolo renumerado COLL=1, E=2, A=3, CATH=4 (= Vishay y huella oficial). Conexiones sin cambio | 13 nov | Datasheet Vishay + Alan |
| P-V2-14 | Mux: distancia entre filas | **Resuelto**: huella HC4067 de Alan corregida a **15.7 mm** (antes 14.99). Orden de pads ya coincidía con el módulo | 13 nov | Alan, vernier |
| P-V2-17 | DRV8833: huella | **Resuelto**: paso 2.54, filas 15.7 mm, columna derecha renumerada (12 IN4, 11 IN3, 9 GND, 10 VCC, 8 IN2, 7 IN1 de arriba a abajo, vista superior). Símbolo sin cambio | 13 nov | Fotos + vernier Alan |
| P-V2-18 | Mux: huella | **Resuelto**: se usa `HC4067:ANALOG_MUX_BREAKOUT_HC4067` (Alan, carpeta Footprints) | 13 nov | Alan |
| P-V2-19 | Cara de los sensores | **Resuelto**: TCRT5000 en la cara inferior (B), mirando al piso; KiCad espeja la huella, cada pata en su pad; se sueldan por arriba. Pines confirmados = vista "patas hacia mí": A arriba-izq., C arriba-der., K abajo-izq., E abajo-der. | 13 nov | Alan |
| P-V2-22 | Colocación | **Resuelto**: sensores en curva (radio 90 mm, 7.7 mm entre sensores), placas centradas en la hoja. Principal 96 × 84 mm, sensores 96 × 88 mm | 13 nov | — |
| P-V2-24 | Interpretación de pines | **Aprobada por Alan (13 nov)** | 13 nov | Alan |
| P-V2-25 | Contradicción TCRT5000 | **Resuelta**: vale la descripción del 12 nov | 13 nov | Alan |
| P-V2-26 | Separadores M3 | **Pesados**: macho y hembra de 6 y 10 mm ≈ **1 g c/u** (Alan, báscula) | 13 nov | Alan |
| P-V2-11 | Pendientes mecánicos | Siguen en la tabla A (C, R, M14/M15) | 12 nov | — |
| P-V2-31 | F1 grande | **Resuelto 15 nov (Alan):** una huella grande es aceptable si es oficial; F1 usa la oficial Bel Fuse 0ZRE0150FF. Pieza a comprar: D-V2-24. Verificar existencia y plazo: P-V2-44 | 15 nov | `v2/docs/decisiones.md` |
| P-V2-32 | Optimizar tamaño de las PCB | **Resuelto 15 nov (Alan):** PCB optimizadas en tamaño: principal 96 × 74 mm, sensores 96 × 59 mm (opción B, D-V2-25). Estado previo: commit `3842103` | 15 nov | `v2/docs/decisiones.md` |
| P-V2-35 | Resistencias de 220 Ω delante de los sensores | **Resuelto 15 nov (Alan):** las resistencias de 220 Ω quedan delante de los sensores, sin cambiar el esquema (D-V2-29) | 15 nov | `v2/docs/decisiones.md` |
| P-V2-36 | Ventilador con una sola base | **Resuelto 15 nov (Alan):** el ventilador se queda, atornillado al acrílico (D-V2-26); posición en la secuencia de D-V2-27 | 15 nov | `v2/docs/decisiones.md` |
| P-V2-38 | Versión de la placa de sensores | **Resuelto 15 nov (Alan):** se elige la **opción B (96 × 59 mm, curva)** (D-V2-25). La A queda en `v2/electronica/sensores/alternativa_68mm_curva/` | 15 nov | `v2/docs/decisiones.md` |
| P-V2-39 | 1N5822: cantidad real | Respondido 15 nov: se compraron **3** (2 en uso + 1 de recambio). Inventario y decisión D-V2-34 | 15 nov | `v2/inventario.csv`, `v2/docs/decisiones.md` |
| P-V2-40 | Recepción del pedido UNIT | Respondido 15 nov: todo lo pedido a UNIT está recibido. Inventario actualizado (D-V2-36). Alan comenta que una pieza que le vendió la electrónica no se anotó (no dijo cuál); el ID P-V2-21 es el de la evaluación del ventilador, así que se pregunta aparte (ver P-V2-45) | 15 nov | `v2/inventario.csv`, `v2/docs/decisiones.md` |
| P-V2-42 | Interruptor: ¿SW-104S es el KCD1? | Respondido 15 nov: el SW-104S es el interruptor KCD1 (D-V2-35) | 15 nov | `v2/inventario.csv`, `v2/docs/decisiones.md` |
| P-V2-43 | Cable 18 AWG ×3 | Respondido 15 nov: 3 m en total, 1.5 m rojo y 1.5 m negro, de reserva (D-V2-35) | 15 nov | `v2/inventario.csv`, `v2/docs/decisiones.md` |
| P-V2-37 | Huella del 1N5822 (D1, D2) | **Resuelto 15 nov:** huella derivada de 20.32 mm aplicada a D1 y D2 (D-V2-33, D-V2-37). PCB principal rehecha: mismas conexiones, ERC 0, DRC 0 errores | 15 nov | `v2/docs/decisiones.md` |
| P-V2-41 | Conectores: ¿alcanzan? | **Aparcado por Alan (15 nov):** "olvídalo por el momento, no tiene peso en nuestros componentes". Sin acción. Si se vuelve a necesitar: tipo de las tiras "5030552" y pines (cuenta calculada: 74 hembra necesarias, 80 compradas) | 15 nov | `v2/docs/decisiones.md` |
| P-V2-44 | PTC: compra | **Resuelto 15 nov:** Alan se apega a conseguir ese fusible (Bel Fuse 0ZRE0150FF1A, D-V2-38). Riesgo conocido: plazo de entrega si no hay existencia | 15 nov | `v2/docs/decisiones.md` |
| P-V2-27 | Revisión final de las PCB / exportar para planchar | **Resuelto 15 nov:** Alan vio la principal y los sensores (opción B) y los aprobó; patrones de planchado generados (D-V2-39) | 15 nov | `v2/electronica/fabricacion/planchado/` |
---


## E. Prototipo de emergencia (placa perforada, 19 nov) — separado del diseño de PCB
| ID | Tema | Estado / qué falta | ¿Bloquea? | Cómo resolver | Quién |
|---|---|---|---|---|---|
| EM-01 | Quitar el ventilador | **Propuesta de Claude, sin decidir.** El esquema de emergencia se dibujó sin ventilador; si Alan lo quiere, se vuelve a poner el bloque del diseño anterior | no | Alan dice sí o no | Alan |
| EM-02 | Comprar placa perforada, LiPo 2S, resistencias y (si no tienen) cargador 2S | Lista en `v2/electronica/prototipo-emergencia/README.md` | **sí** | Comprar | Alan |
| EM-03 | Fusible en línea 3 A | Recomendado; si no hay, seguir las verificaciones de seguridad del README | no | Comprar portafusible | Alan |
| EM-04 | Ajustar MP1584 a 5.0 V y 6.0 V antes de soldar | Igual que E01/E02 | **sí** | Multímetro | Alan |
| EM-05 | Firmware para 8 sensores (canales 0–7 del mux) | No se tocó el firmware (sin autorización) | **sí, para que siga la línea** | Alan autoriza cambiar el firmware | Alan |
| EM-06 | Soporte de la barra recta de sensores (el brazo DXF es para la PCB curva) | No se inició la mecánica | sí, para montar | Después del circuito | Equipo |

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
