# Pendientes por confirmar (robot casero)

Rama `engineering/robot-casero`. Actualizado: 5 nov 2026.
Las medidas ya tomadas están en `especificaciones-componentes.md`; aquí solo queda **lo que falta confirmar o decidir**.
Las decisiones ya tomadas están en `decisiones-robot-casero.md` (no se repiten aquí).

**Estados:** `pendiente` · `escalímetro` (medido, falta vernier) · `pregunta` (necesito respuesta de Alan) · `resuelto`.
**Quién:** Alan salvo que se diga otra cosa.

## 0. General

| ID | Tema | Valor propuesto | Fuente | Cómo confirmarlo | Estado | Quién |
|---|---|---|---|---|---|---|
| V01 | **Confirmar medidas con vernier** | Todas las de estado "escalímetro" en `especificaciones-componentes.md` (M01, M02, M08, M09, M12, M16, M23, M24, M26, M27) | Escalímetro (5 nov) | Repetir con vernier; si cambian más de 0.5 mm, avisar para regenerar huellas y DXF | pendiente | Alan |

## 1. Preguntas de identificación y ambigüedades

| ID | Tema | Lo que creo | Fuente | Cómo confirmarlo | Estado | Quién |
|---|---|---|---|---|---|---|
| P01 | M09: ¿el módulo de 1.3 × 1.1 cm es el DRV8833? | Sí: M09 era "tamaño del DRV8833". **Pero no cuadra**: 6 pines a 2.54 mm ocupan 12.7 mm de centro a centro, así que la placa debe medir al menos ~15 mm. En la foto se ve de ~15 × 18 mm | Foto + paso estándar | Medir de nuevo largo, ancho y **distancia entre las dos filas de pines** | pregunta | Alan |
| P02 | M12: ¿qué es la pieza de 2.2 × 1.65 × 0.4 cm? | El **MP1584** (reductor de voltaje). Coincide con su ficha (22 × 17 × 4) | Foto + sigmanortec | Confirmar que es la placa verde "MP1584" | pregunta | Alan |
| P03 | M13: ¿qué módulo tiene OUT−/OUT+ e IN−/IN+? | También el **MP1584**: entra la batería (IN) y sale el voltaje ajustado (OUT) | Foto | Confirmar | pregunta | Alan |
| P04 | M24: ¿qué pieza tiene 3.5 cm entre patas? | El **diodo 1N5822** (D1 y D2), patas dobladas a 3.5 cm | Foto / contexto | Confirmar | pregunta | Alan |
| P05 | M25: orden de patas del 2N2222 "H331" | PN2222A = E-B-C; P2N2222A = C-B-E (al revés). No se sabe cuál es | Datasheets onsemi | Multímetro en modo diodo: la pata que marca ~0.6 V hacia las otras dos (punta roja) es la **base**; la que da un poco menos es el colector | pendiente | Alan |
| P06 | M27: ¿qué es la pieza de 2 × 2.5 × 0.7 cm? | El **interruptor de balancín KCD1** (rojo, 6 A). Se conecta con 2 cables, no se suelda a la PCB | Fotos | Confirmar | pregunta | Alan |
| P07 | ESP32: el primer pin de la derecha, ¿VIN o VN? | **VIN** (entrada de 5 V, arriba junto al USB). "VN" es otro pin (GPIO39) que está abajo, junto a VP | Foto: arriba dice "VIN", abajo "VN" | Leer de nuevo la serigrafía con lupa | pregunta | Alan |
| P08 | DRV8833: "EEP" y "ULT" | EEP = **nSLEEP** (la letra "SL" quedó cortada) y ULT = **nFAULT** ("FA" cortado). El módulo además tiene un puente "J1 sleep–en" | Foto del reverso + datasheet TI | Dejar **J1 abierto** (sin soldar) para que el ESP32 controle SLEEP con GPIO16. Confirmar si viene soldado | pregunta | Alan |
| P09 | M08: interpretación de la rueda | Llanta de goma ∅28 mm y 21.5 mm de ancho sobre un rin de aluminio de ∅21 × 22 mm con tornillo prisionero que se aprieta sobre el eje del motor | Fotos | Confirmar que el agujero del rin es de 3 mm (eje del N20) | pregunta | Alan |
| P10 | ¿Ya tienen los motores N20? | En la lista de faltantes siguen como "por comprar" | Mensaje de Alan | Confirmar | pregunta | Alan |
| P11 | M23: electrolítico 3 mm entre patas | El estándar para ∅8 mm es 3.5 mm; la huella usa 3.5 mm (las patas se doblan un poco) | KiCad / fabricante | Vernier | escalímetro | Alan |

## 2. Medidas que faltan (piezas que aún no se miden o no se compran)

| ID | Tema | Valor propuesto | Fuente | Cómo confirmarlo | Estado | Quién |
|---|---|---|---|---|---|---|
| M05–M07 | Motor N20: cuerpo y agujeros | 24 + 10 mm, 12 × 10 mm, M1.6 a 9 mm | mikroelectron / típico | Escalímetro al tenerlos | pendiente | Alan |
| M14–M15 | LiPo 2S: medidas, peso y conectores | 61 × 16 × 15 mm, ~30 g, JST-RC | contexto del equipo | Al comprarla | pendiente | Alan |
| M16–M17 | Módulo 74HC4067: tamaño y orden de pines | 18 × 41 mm | Alan | Foto de la serigrafía + vernier | pendiente | Alan |
| M19–M20 | TCRT5000: patas y orden | 4 en línea a 2.54 mm | sin fuente | Al comprarlos | pendiente | Alan |
| M21–M22 | Ventilador: tamaño, consumo y peso | 4010, 12 V, ~0.15 A, ~12 g | típico | Etiqueta + multímetro + báscula | pendiente | Alan |
| M28 | Fusible reseteable: paso de patas | 5 mm | sin fuente | Al comprarlo | pendiente | Alan |
| M30 | Rueda loca: tornillos y altura | 2 × M2 a 12 mm; debe medir ~19.5 mm hasta el piso | sin fuente | Al comprarla | pendiente | Alan |

## 3. Chasis

| ID | Tema | Valor propuesto | Fuente | Cómo confirmarlo | Estado | Quién |
|---|---|---|---|---|---|---|
| C01 | Espesor del acrílico | 3 mm | Estándar más común | Preguntar al taller | pendiente | Equipo |
| C02 | Material | Acrílico, MDF o PLA (hay DXF de los tres) | — | Cotizar | pendiente | Equipo |
| C03 | Tamaño máximo del robot | 200 × 100 mm y 500 g (límite del reglamento, robot completo con ruedas). El diseño mide 197 × 96 mm | Reglamento | Medir el robot armado | resuelto (diseño) | Equipo |
| C05 | Holgura de corte | Láser −0.2 mm; PLA +0.3 mm en los agujeros | Valores de arranque | Pieza de prueba | pendiente | Equipo |
| C07 | Altura de los sensores al piso | 4 mm (separadores de 7 mm bajo el travesaño) | Diseño | Probar en pista: 2–8 mm | pendiente | Equipo |
| C08 | Reglamento: posible cambio el 18 nov | Ver nota abajo | Proyecto "Seguidor Línea V2" | Releer el reglamento el 18 o 19 nov | pendiente | Equipo |
| C09 | Separadores | M3: 3 de 18 mm (PCB principal) y 4 de 7 mm (placa de sensores) | Diseño | Comprar | pendiente | Alan |

**Qué es C08:** el documento de reglas dice que los organizadores pueden publicar cambios al reglamento el **18 de noviembre**.
No hay que decidir nada ahora: solo **revisar las reglas ese día** por si cambian tamaño, peso o algo del ventilador, y avisarme si algo cambió.

## 4. Eléctrico y pruebas

| ID | Tema | Valor propuesto | Fuente | Cómo confirmarlo | Estado | Quién |
|---|---|---|---|---|---|---|
| E01 | MP1584 #1 | 5.0 V antes de conectar | Diseño | Multímetro | pendiente | Alan |
| E02 | MP1584 #2 | 6.0 V antes de conectar motores | Diseño | Multímetro | pendiente | Alan |
| E03 | Diodos 1N5822 | Directa ~0.15–0.30 V, inversa OL | Guía abajo | Multímetro modo diodo | pendiente | Alan |
| E04 | ERC oficial de KiCad | El propio da 0 errores; el oficial no se pudo correr | `electronica/kicad/NOTAS.md` | Abrir en KiCad → Inspeccionar → ERC | pendiente | Alan |
| E05 | Divisor de batería | 8.4 V → 2.08 V | Cálculo | LiPo cargada | pendiente | Alan |
| E06 | Corriente total | < 1.5 A (fusible) | Estimación | Multímetro en serie | pendiente | Alan |
| E07 | Corto antes de la LiPo | +VBAT–GND abierto | Buena práctica | Multímetro | pendiente | Alan |
| E08 | Brocas para la PCB | 0.8 mm no basta: pines de header y TO-220 necesitan **1.0 mm** y el 1N5822 **1.3 mm** | Diámetro de las patas | Comprar brocas 1.0 y 1.3 mm (ver faltantes) | pendiente | Alan |

## 5. Riesgos de diseño

| ID | Riesgo | Explicación | Qué hacer |
|---|---|---|---|
| R01 | El ventilador queda debajo de la PCB principal | La PCB está a 8 mm sobre el ventilador: el aire sale de lado, no libre hacia arriba | Probar la succión con báscula; si no basta, mover el ventilador al frente de la PCB |
| R02 | Puentes de alambre en la PCB | Ver explicación abajo | Contarlos al armar; si son muchos, pulir la colocación |
| R03 | Sensores en arco | Funcionan mejor entre 2 y 8 mm del piso | Probar en pista y ajustar con arandelas |

**Qué es R02 (puentes de alambre):** la placa casera tiene cobre **solo por abajo**. Cuando dos pistas necesitan cruzarse, una de ellas no
puede pasar por el cobre: el diseño la dibuja en la capa de arriba (color **rojo** en `vista_*.png`), y eso significa que **ahí va un cable
soldado por encima de la placa** (un "puente"). El programa de diseño (KiCad) lo acepta sin error, pero en la vida real cada puente es un
alambre que hay que cortar, pelar y soldar en dos agujeros. En el diseño actual hay del orden de 20 a 30 puentes por placa, de ~2 cm cada uno.
Funciona, pero es trabajo y un lugar más donde equivocarse. Si se quiere menos, hay que reacomodar piezas a mano en KiCad.

## 6. Cómo medir los diodos 1N5822 (E03)

1. Multímetro en **modo diodo** (símbolo ▶|).
2. **Directa:** punta roja al lado **sin** franja, negra al lado **con** franja. Debe marcar ~0.15–0.30 V.
3. **Inversa:** al revés. Debe marcar **OL** (abierto).
4. Si marca ~0.55 V o más en directa, no es Schottky: avísame. Si marca 0.00 en ambos sentidos, está en corto.

Anotar: `Diodo 1: directa ___ V, inversa ___ · Diodo 2: directa ___ V, inversa ___ · letras del cuerpo ___`
