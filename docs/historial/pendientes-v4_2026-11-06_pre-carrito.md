# Pendientes por confirmar (robot casero) — versión 4

Rama `engineering/robot-casero`. Actualizado: 6 nov 2026.
**Regla:** ningún ID se borra. Si se resolvió, cambia su estado y se anota la decisión; si quedó obsoleto, se marca **obsoleto** con el motivo.
Versiones anteriores: `docs/historial/`. Medidas completas: `especificaciones-componentes.md`. Decisiones: `decisiones-robot-casero.md`.

**Estados:** `pendiente` · `escalímetro` (medido con regla/escalímetro, falta vernier) · `pregunta` (necesito respuesta de Alan) ·
`resuelto` · `obsoleto`. **Quién:** Alan salvo que se diga otra cosa.

## 0. General
| ID | Tema | Valor / situación | Fuente | Cómo confirmarlo | Estado | Quién |
|---|---|---|---|---|---|---|
| V01 | Confirmar medidas con vernier | Todas las "escalímetro" (M01, M02, M08, M09, M12, M16, M23, M24, M26, M27) | Escalímetro | Repetir con vernier; avisar si cambian más de 0.5 mm | pendiente | Alan |

## 1. Medidas de piezas (M)
| ID | Tema | Valor / situación | Fuente | Cómo confirmarlo | Estado | Quién |
|---|---|---|---|---|---|---|
| M01 | ESP32: tamaño de placa | **30 pines**, 5.1 × 2.8 cm (5.4 con USB-C) → 51 × 28 mm. (Antes se suponía uno de 38 pines de 54.4 × 27.9) | Alan | Vernier | escalímetro | Alan |
| M02 | ESP32: distancia entre filas | 2.55 cm → huella a 25.4 mm (estándar) | Alan | Vernier | escalímetro | Alan |
| M03 | ESP32: orden de pines | Leído de la serigrafía (ver especificaciones). Queda la duda del primer pin derecho: ver P07 | Foto de Alan | — | resuelto (salvo P07) | — |
| M04 | ESP32: pines por lado | 15 por lado, paso 2.54 mm | Foto | — | resuelto | — |
| M05 | Motor N20: largo y eje | 34 mm total, eje ∅3 × 10 mm, 10 g | mikroelectron | Alan medirá sus motores con regla (P10) | pendiente | Alan |
| M06 | N20: ancho × alto del cuerpo | 12 × 10 mm | típico, SIN FUENTE | Regla | pendiente | Alan |
| M07 | N20: agujeros del frente | Ya no se usan: el motor se sujeta con **asegurador** (M31) | — | — | obsoleto (6 nov) | — |
| M08 | Rueda (rin + llanta) | Llanta ∅2.8 × 2.15 cm, rin ∅2.1 × 2.2 cm → ∅28 × 21.5 mm. (Antes se pensaba comprar llantas de 34 × 7 mm) | Alan | Vernier; confirmar interpretación (P09) | escalímetro | Alan |
| M09 | DRV8833 (módulo): tamaño | **1.8 × 1.55 cm → 18 × 15.5 mm** (6 nov, regla). Cuadra con 6 pines a 2.54 mm. Sustituye la medida de 1.3 × 1.1 cm | Alan | Vernier; distancia entre filas de pines | escalímetro | Alan |
| M10 | DRV8833: orden de pines | IN4, IN3, GND, VCC, IN2, IN1 · EEP, OUT1…OUT4, ULT | Foto | — | resuelto | — |
| M11 | DRV8833: voltaje y corriente | VM 2.7–10.8 V, 1.5 A RMS por puente | [Datasheet TI](https://www.ti.com/lit/ds/symlink/drv8833.pdf) | — | resuelto | — |
| M12 | MP1584: tamaño | 2.2 × 1.65 × 0.4 cm → 22 × 16.5 × 4 mm. **Es el módulo MP1584** (reductor de voltaje) | Alan | Vernier | escalímetro | Alan |
| M13 | MP1584: terminales | OUT−/OUT+ a la izquierda, IN−/IN+ a la derecha | Foto | — | resuelto | — |
| M14 | LiPo 2S: medidas y peso | 61 × 16 × 15 mm, ~30 g | contexto del equipo | Al comprarla | pendiente | Alan |
| M15 | LiPo: conectores | JST-RC 2 pines + balanceo JST-XH 3 pines | típico | Al comprarla | pendiente | Alan |
| M16 | Módulo 74HC4067: tamaño | 18 × 41 mm | Alan | Vernier | escalímetro | Alan |
| M17 | 74HC4067: orden de pines | VCC, GND, S0–S3, SIG, EN en una fila; C0–C15 en otra | SIN FUENTE | Foto de la serigrafía | pendiente | Alan |
| M18 | TCRT5000: cuerpo | 10.2 × 5.8 × 7 mm | Vishay | — | resuelto | — |
| M19 | TCRT5000: patas | 4 en línea a 2.54 mm | SIN FUENTE (el datasheet lo da solo en dibujo) | Al comprarlos | pendiente | Alan |
| M20 | TCRT5000: orden A, K, C, E | A, K = LED; C, E = fototransistor | datasheet | Al comprarlos | pendiente | Alan |
| M21 | Ventilador: tamaño y consumo | 4010, 12 V, ~0.1–0.2 A | típico | Etiqueta + multímetro | pendiente | Alan |
| M22 | Ventilador: peso | ~10–15 g | típico | Báscula | pendiente | Alan |
| M23 | Capacitores | Electrolítico ∅8 mm, 3 mm entre patas (huella 3.5); cerámico 7 mm entre patas | Alan | Vernier | escalímetro | Alan |
| M24 | Diodo 1N5822: patas | 3.5 cm entre patas (pedido de Alan). En la PCB nueva se usó 15.24 mm para que quepa (ver `opciones-diseno.md`, O05) | Alan | Decidir | pregunta | Alan |
| M25 | 2N2222 "H331": orden de patas | E-B-C o C-B-E según fabricante. **Alan pidió dejarlo pendiente (6 nov)** | datasheets onsemi | Prueba con multímetro (P05) | pendiente | Alan |
| M26 | Pulsadores | Mediano 12 × 12 mm, pequeño 6 × 6 mm, 5 mm entre patas | Alan | Vernier | escalímetro | Alan |
| M27 | Interruptor de balancín KCD1 | 20 × 16 × 7 mm de cuerpo, 25 mm con patas; va cableado, no en la PCB | Alan | Confirmar que es el KCD1 rojo | escalímetro | Alan |
| M28 | Fusible reseteable: paso | 5 mm | SIN FUENTE | Al comprarlo | pendiente | Alan |
| M29 | Paso entre sensores de la "barra" | **Obsoleto:** no hay barra comercial. Se reemplazó por la decisión D05 (12 sensores a 7.5 mm en arco) | — | — | obsoleto (5 nov) | — |
| M30 | Rueda loca mini | En el diseño nuevo (opción A) **se elimina** y se usa 1 patín (tornillo de nailon) al centro de la placa de sensores (O02). Si se aprueba, pasa a obsoleto | — | Decidir | pregunta | Alan |
| M31 | Asegurador (soporte) del motor N20 | Pieza de plástico blanca con oreja para tornillo (foto 6 nov). Medidas **SIN FUENTE**: abrazadera de ~14 × 12 mm, oreja con agujero de ~2 mm | Foto de Alan | Medir con regla: largo, ancho, alto y distancia del agujero al eje | pendiente | Alan |

## 2. Preguntas y ambigüedades (P)
| ID | Tema | Lo que creo | Fuente | Cómo confirmarlo | Estado | Quién |
|---|---|---|---|---|---|---|
| P01 | Tamaño del DRV8833 no cuadraba | Resuelto con la nueva medida de 18 × 15.5 mm (M09) | Alan, 6 nov | — | resuelto | — |
| P02 | ¿La pieza de 2.2 × 1.65 × 0.4 cm (M12) es el MP1584? | Sí | Foto | Confirmar | pregunta | Alan |
| P03 | ¿El módulo con OUT−/OUT+ e IN−/IN+ (M13) es el MP1584? | Sí | Foto | Confirmar | pregunta | Alan |
| P04 | ¿La pieza de 3.5 cm entre patas (M24) es el diodo 1N5822? | Sí | Contexto | Confirmar | pregunta | Alan |
| P05 | Orden de patas del 2N2222 (M25) | Multímetro en modo diodo: la pata que da ~0.6 V hacia las otras dos (punta roja en ella) es la base | datasheets | Prueba | pendiente | Alan |
| P06 | ¿La pieza de 2 × 2.5 × 0.7 cm (M27) es el interruptor rojo KCD1? | Sí | Fotos | Confirmar | pregunta | Alan |
| P07 | ESP32: el primer pin de arriba a la derecha, ¿VIN o VN? | La serigrafía dice "VN" según Alan, pero en el diagrama de pines que mandó (mismo modelo, USB abajo) **VIN está en la esquina junto al USB** y VN (GPIO39) está en el otro extremo, junto a VP y EN. Con el USB arriba eso es el pin de arriba a la derecha → **VIN**. El esquema ya usa VIN y **no se cambia** hasta confirmar | Foto + diagrama de pines | Conectar el ESP32 por USB y medir con multímetro entre ese pin y GND: si marca ~4.7–5 V, es VIN | pendiente | Alan |
| P08 | DRV8833: puente J1 "sleep–en" | Es un puente de soldadura de 2 pastillas que une nSLEEP con VCC (el módulo quedaría siempre encendido). Viene **sin soldar** (foto 6 nov): así queda bien, el ESP32 controla nSLEEP por el pin EEP (GPIO16). **No soldarlo** | Foto + datasheet (nSLEEP tiene pulldown interno de 500 kΩ) | — | resuelto | — |
| P09 | Interpretación de la rueda (M08) | Llanta ∅28 × 21.5 mm sobre rin ∅21 × 22 con prisionero; agujero del rin de 3 mm | Fotos | Confirmar el agujero de 3 mm | pregunta | Alan |
| P10 | Motores N20 | No se han comprado; Alan tiene unos y los medirá con regla (M05, M06) | Alan, 6 nov | Medidas | pendiente | Alan |
| P11 | Electrolítico: 3 mm vs 3.5 mm entre patas (M23) | Huella de 3.5 mm; las patas se doblan | KiCad | Vernier | escalímetro | Alan |
| P12 | ¿Qué opción de diseño se elige? | Recomiendo la **opción A** de `opciones-diseno.md` (una sola placa de acrílico, todo abajo) | Este análisis | Alan elige | pregunta | Alan |

## 3. Chasis (C)
| ID | Tema | Valor / situación | Fuente | Cómo confirmarlo | Estado | Quién |
|---|---|---|---|---|---|---|
| C01 | Espesor del acrílico | 3 mm | estándar común | Preguntar al taller | pendiente | Equipo |
| C02 | Material | Acrílico, MDF o PLA (DXF de los tres) | — | Cotizar | pendiente | Equipo |
| C03 | Tamaño máximo | 200 × 100 mm de planta y 500 g, **robot completo** (reglamento). Antes se llamaba "caja"; ese nombre quedó **obsoleto** porque se confundía con el chasis | Reglamento | Medir el robot armado | resuelto | — |
| C04 | Peso del chasis | Placa sola: ver `mecanica/autocad/RESUMEN.md` | cálculo | Báscula | pendiente | Equipo |
| C05 | Holgura de corte | Láser −0.2 mm; PLA +0.3 mm en agujeros | valores de arranque | Pieza de prueba | pendiente | Equipo |
| C06 | Permiso para usar ventilador | **Confirmado** con expertos y participantes anteriores (Alan, 5 nov). Ver D08 | Alan | — | resuelto | — |
| C07 | Falda del ventilador y altura de los sensores | Sensores a **2.5–3 mm** del piso (ver `opciones-diseno.md`); la falda nunca debe tocar la pista | datasheet Vishay | Probar en pista | pendiente | Equipo |
| C08 | Posible cambio del reglamento el 18 nov | No hay que decidir nada: releer las reglas el 18 o 19 nov y avisar si cambió algo | Proyecto "Seguidor Línea V2" | Releer | pendiente | Equipo |
| C09 | Separadores y tornillería | Opción A: separadores M3 de 4 mm bajo las PCB, tornillos M2 para los aseguradores | Diseño | Comprar | pendiente | Alan |

## 4. Eléctrico (E)
| ID | Tema | Valor | Fuente | Cómo confirmarlo | Estado | Quién |
|---|---|---|---|---|---|---|
| E01 | MP1584 #1 | 5.0 V antes de conectar | Diseño | Multímetro | pendiente | Alan |
| E02 | MP1584 #2 | 6.0 V antes de conectar motores | Diseño | Multímetro | pendiente | Alan |
| E03 | Diodos 1N5822 | directa ~0.15–0.30 V, inversa OL | guía abajo | Multímetro | pendiente | Alan |
| E04 | ERC oficial de KiCad | El propio da 0 errores; el oficial no se pudo correr aquí | NOTAS | Abrir en KiCad 10 → Inspeccionar → ERC | pendiente | Alan |
| E05 | Divisor de batería | 8.4 V → 2.08 V | cálculo | LiPo cargada | pendiente | Alan |
| E06 | Corriente total | < 1.5 A | estimación | Multímetro en serie | pendiente | Alan |
| E07 | Corto antes de la LiPo | +VBAT–GND abierto | buena práctica | Multímetro | pendiente | Alan |
| E09 | Ruteo de las PCB de la opción A | Incompleto: principal 16 redes sin unir, sensores 5. Las PCB tienen errores de DRC | Enrutador propio | Terminar a mano en KiCad 10 o reacomodar piezas (siguiente sesión) | pendiente | Claude / Alan |
| E08 | Brocas | 1.0 mm (headers, TO-220) y 1.3 mm (1N5822); la de 0.8 solo para resistencias | diámetro de patas | Comprar | pendiente | Alan |

## 5. Riesgos (R)
| ID | Riesgo | Situación | Qué hacer | Estado |
|---|---|---|---|---|
| R01 | Ventilador tapado por la PCB | En la opción A el ventilador va sobre un hueco de la placa y de la PCB, con la salida libre | Probar la succión con báscula | pendiente |
| R02 | Puentes de alambre en la PCB casera | Cobre solo por abajo: cada cruce de pistas es un alambre soldado por arriba (pistas rojas en `vista_*.png`). Idea de Alan de dos placas fenólicas: evaluada en `opciones-diseno.md` (O04), **sin decidir** | Contar los puentes; elegir entre O04, doble cara o puentes | pendiente |
| R03 | Sensores en arco | Funcionan de 0.2 a 15 mm, mejor a 2.5 mm | Ajustar con arandelas | pendiente |
| R04 | El límite de 200 × 100 incluye ruedas y sensores | El diseño (opción A) mide 196 × 98 mm con todo | Medir armado | pendiente |

## 6. Cómo medir los diodos 1N5822 (E03)
1. Multímetro en **modo diodo** (▶|). 2. Directa: roja al lado sin franja, negra a la franja → ~0.15–0.30 V.
3. Inversa: al revés → **OL**. 4. ~0.55 V o más = no es Schottky; 0.00 en ambos sentidos = en corto.
Anotar: `Diodo 1: directa ___ V, inversa ___ · Diodo 2: directa ___ V, inversa ___ · letras del cuerpo ___`
