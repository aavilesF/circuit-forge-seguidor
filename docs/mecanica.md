> **HISTÓRICO (rama anterior `engineering/robot-casero`). No es información vigente de V2.** Inventario, decisiones y pendientes vigentes: `v2/inventario.csv`, `v2/docs/decisiones.md`, `docs/pendientes-por-confirmar.md`. Estado de cada documento: `v2/docs/ESTADO-DOCUMENTOS.md`.

# Mecánica

Vista a escala: `docs/diagramas/03_vista_superior_8.png` y `03_vista_superior_24.png`. Las medidas de las piezas son **nominales**
(`herramientas/generar_diagramas.py`): al comprar, medir con vernier y actualizar; el script calcula si el conjunto cabe.

## Reglas que mandan (reglamento)
- Huella máxima 20 × 10 cm y **máximo 500 g en todo momento**. Medido en el diseño nominal: 85 × 192 mm (QTR-8A) y 100 × 192 mm (curvo 24, justo en el límite de ancho).
- El chasis lo construye el equipo (sin kits ni piezas comerciales de robot). Sigue pendiente confirmar por correo si imprimir en un servicio de la universidad cuenta como "construido por el equipo".

## Geometría nominal
| Dato | Valor | Nota |
|---|---|---|
| Rueda | Ø 33 mm, 10 mm de ancho | medir la real |
| Separación entre ruedas | 75 mm (centro a centro) | cinemática y ancho total |
| Eje de ruedas a sensores | 100 mm | el profesor recomienda 80-120 mm |
| Altura de sensores al piso | 8-10 mm | ajustar con el sensor real |
| Apoyo trasero | ball caster o patín de teflón | evita arrastre |

Efecto de la distancia sensores-eje (simulación, vbase 0.6): 80 mm → 1.4 mm de error; 100 mm → 1.6 mm; 120 mm → 1.8 mm. Más cerca sigue mejor, más lejos anticipa más; 100 mm es un punto de partida razonable.

## Velocidad esperada de las ruedas (v = π·D·RPM/60, D = 33 mm)
| RPM | m/s sin carga |
|---|---|
| 300 | 0.52 |
| 600 | 1.04 |
| 1000 | 1.73 |
| 2000 | 3.46 |

Con carga se pierde ~20 %. A 1000 RPM el límite lo pone el agarre en curvas de 15 cm (~1.15 m/s), no el motor.

## Distribución de masa
Batería lo más cerca del eje y adelante de él (carga las ruedas motrices); ESP32 y driver atrás; sensores adelante, lo más ligeros posible. Apuntar a ~60 % del peso sobre las ruedas motrices.
Presupuesto de peso orientativo (verificar con báscula): motores+ruedas ~40 g, batería 2S pequeña ~35-50 g, ESP32 ~10 g, driver+reguladores ~15 g, sensores+mux ~20 g, chasis ~40-80 g, cables/tornillos ~20 g → bien por debajo de 500 g.

## Diseño del chasis
Pendiente hasta tener las piezas en la mano: se diseña (CAD paramétrico) con las medidas reales. Hasta entonces se puede armar un prototipo de prueba con cartón pluma o acrílico para validar fit y centro de gravedad.
