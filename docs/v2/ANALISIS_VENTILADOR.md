# V2 · Fase 1 — Análisis del ventilador y su montaje (modelos 3D entregados)

Archivos (exportados de Autodesk Fusion, en mm): `hardware/v2/referencia_succion/VentiladorATS1.obj`, `BaseATS1.obj`,
`PilarATS1.obj`, `BracketATS1.obj`. Medidas obtenidas cortando las mallas (trimesh 4.x/5.2, script en la sección 4).
Tipo de todas las medidas de esta página: **medido en el modelo 3D entregado** (no en la pieza física).

## 1. Qué es cada pieza

| Pieza | Geometría medida | Interpretación |
|---|---|---|
| **Ventilador** (`VentiladorATS1`) | Rueda centrífuga **cerrada**: disco trasero Ø34 × 1 mm; **12 álabes rectos radiales** de 1.0 mm de espesor, de r = 10 a r = 17 mm y 6 mm de alto; tapa anular de 1 mm con **ojo de entrada Ø20 mm**. Altura total 8 mm. Volumen 1 987 mm³. En el disco: 5 agujeros Ø2.2 (uno central y 4 sobre un círculo de Ø5 mm) | Rotor tipo "rueda de paletas" (álabes radiales): da presión estable con poco caudal, lo que conviene para succión con faldón. **El material del modelo dice "acero satinado"**: probablemente es la apariencia por defecto de Fusion; hay que confirmarlo (con acero pesaría ≈ 15.6 g; impreso en PA12, ≈ 2 g) |
| **Base** (`BaseATS1`) | Placa 38 × 38 × 1.9 mm con un realce inferior de 31.8 × 31.8 × 0.85 mm. Agujero central **cónico de Ø24.4 (cara inferior) a Ø18.6 mm** (garganta). 4 agujeros Ø1.8 en (±15, ±15) mm | Entrada de aire con boquilla, desde el piso hacia el ojo del rotor. El área que "ve" depresión si la base va pegada al piso es solo su cara inferior (≈ 10 cm²) |
| **Pilar** (`PilarATS1`, se usan 4) | 5.5 × 4.8 × 22 mm, agujero pasante Ø1.4 | Separadores de 22 mm entre base y soporte (Ø1.4 = rosca para tornillo autorroscante pequeño, a confirmar) |
| **Soporte** (`BracketATS1`) | Placa 35.8 × 35.8 × 2 mm. Agujero central Ø5 (Ø9.6 en la cara superior); 4 agujeros Ø2.2 sobre un círculo de Ø9 mm, avellanados a Ø3.3 arriba; 4 agujeros Ø1.8 en las esquinas | Montaje de un motor pequeño (4 tornillos sobre Ø9 mm) con el rotor colgando hacia la base. **El motor no viene en los archivos** |

Conjunto: base (abajo) → 4 pilares de 22 mm → soporte (arriba, con el motor) → rotor entre ambos con el ojo hacia la base.
El aire entra por la base, el rotor lo expulsa radialmente por los costados abiertos entre los pilares. Altura del conjunto
≈ 26.5 mm sin contar lo que sobresalga del motor.

## 2. Lo que sí se puede calcular con la geometría (estimaciones de orden de magnitud)

Presión de cierre ideal de un rotor de álabes radiales: ΔP₀ ≈ ½·ρ·ω²·(r₂² − r₁²), con r₁ = 10 mm y r₂ = 17 mm. El caudal libre
se estima como Q₀ ≈ φ·π·D₂·b₂·u₂, con φ = 0.10-0.25 **supuesto**. Densidad del aire en León (1 815 m, atmósfera estándar):
**1.025 kg/m³**, 15 % menos que a nivel del mar: el ventilador da 15 % menos presión allá que en una ficha medida a nivel del mar.

| RPM | u₂ (m/s) | ΔP₀ ideal en León (Pa) | ΔP₀ con 60-90 % de rendimiento de presión (Pa) | Q₀ (L/s, φ 0.10-0.25) |
|---|---|---|---|---|
| 15 000 | 26.7 | 239 | 143-215 | 1.7-4.3 |
| 20 000 | 35.6 | 425 | 255-383 | 2.3-5.7 |
| 25 000 | 44.5 | 664 | 398-598 | 2.9-7.1 |
| 30 000 | 53.4 | 956 | 574-861 | 3.4-8.6 |
| 40 000 | 71.2 | 1 700 | 1 020-1 530 | 4.6-11.4 |

**Estas cifras no sustituyen la curva del fabricante**: dependen de RPM bajo carga que no conozco y de un rendimiento
supuesto. Sirven para saber qué orden de RPM haría falta: la Fase 1 pide ≈ 800-1 200 Pa de presión de cierre en León
(ver `FASE1_FISICA.md` §6), es decir, **≈ 30 000-40 000 RPM con este rotor**.

## 3. Conclusiones sobre la integración (condicionadas a la curva real)

1. **El rotor puede servir; la base entregada, tal como está, no.** Con la base como única cámara (≈ 10 cm²), la fuerza
   queda en ≈ 0.4-1.3 N aun con ranuras pequeñas (T6, escenario C0), y la meta pide ≈ 3-5 N (T3b). La modificación que
   justifica el cálculo es **una cámara con faldón de ≥ 50 × 50 mm** (idealmente ≈ 70 × 70 mm) alimentada por el mismo
   rotor, no rediseñar los álabes. Se confirma o se descarta cuando llegue la curva presión-caudal.
2. **La ranura del faldón manda**: con el escenario intermedio, pasar de 0.5 a 1.0 mm quita ≈ 46 % de la fuerza (T6).
3. **El centro de la cámara debe quedar cerca del eje de las ruedas motrices**: con el centro a 30 mm del eje, solo el 70 %
   de la succión carga las ruedas que frenan y doblan; a 60 mm, el 40 % (T3b).
4. **Reacción y giroscopio**: el par de arranque del motor del ventilador hace girar al robot sobre su eje vertical; el
   firmware debe arrancar el ventilador antes de soltar los motores. El efecto giroscópico es nulo en guiñada (ejes paralelos).

## 4. Datos que necesito del ventilador (pedido)

| Dato | Para qué |
|---|---|
| Fabricante y **número de parte** del motor del ventilador (y del controlador, si es sin escobillas) | Selección eléctrica, conector, protocolo de mando (PWM, DShot u otro), telemetría |
| **Curva presión-caudal** (ΔP contra Q) a una tensión y RPM dadas, con la densidad de la medición | Punto de funcionamiento real con la cámara y la ranura |
| RPM sin carga y con el rotor puesto a 7.4 V y 8.4 V (o KV) | Escalar la curva con la tensión de la batería |
| Corriente y potencia a esas RPM; corriente de arranque | Puente o controlador, caída de la batería, energía |
| Masa del motor, del rotor y del montaje | Masa total y CG |
| Material real del rotor | Masa e inercia (tiempo de caída de la presión cuando falla) |
| ¿Salida de tacómetro o telemetría de RPM? | Supervisión del ventilador en el firmware |
| ¿Se midió la fuerza de succión con este conjunto? ¿Con qué cámara y ranura? | Validar el modelo de inmediato |

**Si no hay ficha**, el dato más útil se puede medir en una tarde sin instrumentos especiales: el conjunto sobre una
cámara de prueba de 70 × 70 mm con un faldón rígido, apoyado con calzas de 0.3, 0.5, 1.0 y 2.0 mm sobre una placa de
fórmica que descansa en una báscula de 0.1 g; la lectura de la báscula al encender el ventilador es directamente la fuerza de
succión, a 7.4 V y a 8.4 V, junto con la corriente de la fuente. Eso da F(ranura, V) e I(V) sin conocer la curva.

Script del análisis de las mallas: `sim/v2/analisis_obj.py` (regenera las medidas de esta página).
