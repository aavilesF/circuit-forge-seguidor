# Diagnóstico mecánico del robot casero (Fase 1 y 2) — 6 nov 2026

Rama `engineering/robot-casero`. Este documento **no cambia el diseño**: audita lo que hay (YAML, scripts, DXF, notas y decisiones)
y propone dos alternativas. **Nada se rediseña hasta que Alan elija (P12).**

Ejes: origen en el centro del eje de las ruedas, X al frente, Y a la izquierda, Z arriba (piso = 0).
Todas las masas son **estimaciones** (no pesadas); lo marcado "sin fuente" no debe usarse para cortar.

## 1. Lo que dicen realmente los archivos (geometría vigente)

Los scripts y `parametros.yaml` describen la **opción A** (placa única). Corrida de `generar_dxf.py` + `verificar_dxf.py`: los 3 DXF pasan
(196 × 98 mm, acrílico ≈ 55 g, MDF ≈ 35 g, PLA ≈ 58 g).

| Conjunto | Posición en X | Altura (Z) |
|---|---|---|
| Placa de acrílico 3 mm | −126 a +70 mm | cara inferior 4.5 mm, superior 7.5 mm |
| Placa de sensores (PCB 94 × 50) | +20 a +70 | sobre separadores de 2 mm (PCB a 9.5 mm) |
| 12 TCRT5000 | arco R 110 mm, centro ≈ +55 a +65 | cara a 2.5 mm del piso (atraviesan ventanas de 11 × 7 mm) |
| Ruedas ∅28 × 21.5 | eje en 0 | eje a 14 mm |
| Motores N20 (medidas pendientes) | en 0, a lo largo de Y, de y = ±2 a ±26 | sobre aseguradores |
| PCB principal 90 × 106 | −20 a −126 | separadores de 4 mm (PCB a 11.5 mm) |
| ESP32 + LiPo encima | ≈ −58 | LiPo arriba de todo (~45 mm) |
| Ventilador 4010 | ≈ −102 | encima de la PCB, separadores de 8 mm |
| Patín (tornillo de nailon) | ≈ +48 | **en el modelo 3D no toca el piso** (empieza en z = 0.3) |

## 2. Hallazgo principal: el robot no se apoya donde el diseño supone

Un robot de dos ruedas + un patín tiene **tres puntos de apoyo**. Para que se quede así, el **centro de gravedad** (CG, *center of gravity*)
tiene que caer **dentro del triángulo** que forman: entre el eje de las ruedas (x = 0) y el patín (x ≈ +48).

Estimación de masas (g): placa 55, PCB principal ≈ 28, placa de sensores ≈ 14, sensores y resistencias ≈ 8, multiplexor 8, ESP32 ≈ 10,
LiPo ≈ 30 (modelo no elegido), ventilador 16, tornillería ≈ 15, MP1584 + DRV8833 + varios ≈ 15, motores ≈ 20 (sin confirmar),
ruedas ≈ 14 (sin pesar), soportes 3, cables y soldadura ≈ 15. **Total ≈ 250 g** (lejos del límite de 500 g).

**CG estimado: x ≈ −33 mm, es decir 33 mm DETRÁS del eje.** Casi toda la masa (PCB principal, ESP32, LiPo, ventilador) está detrás de las ruedas
y no hay nada que la sostenga atrás. Consecuencias:

1. El robot **se va de espaldas** hasta que el borde trasero del acrílico (x = −126, a 4.5 mm del piso) toca la pista: inclinación ≈ 2°.
2. El frente sube ≈ 2 mm: los sensores pasan de 2.5 a **~4.5 mm** del piso y el patín queda en el aire.
3. El borde trasero **arrastra** sobre la fórmica con ≈ 25 % del peso: frena, raya la pista (el reglamento prohíbe dañarla) y quita carga a las ruedas.
4. Lo que da agarre a las ruedas es su carga normal; con el CG detrás del eje, una parte del peso se va al borde que arrastra.

Esto no se ve en el DXF 2D ni en el verificador actual, porque **ninguno revisa la estabilidad**.

## 3. Otros hallazgos

### 3.1 Contradicciones entre archivos
| # | Dónde | Contradicción |
|---|---|---|
| X1 | `mecanica/autocad/NOTAS.md` | Describe el diseño **en T** (base 106 × 98, espina de 30 mm, travesaño, PCB a 18 mm, rueda loca, 198 × 96, pesos 42/27/44 g). Los scripts generan la **opción A** (196 × 98, separadores de 4 mm, patín, 55/35/58 g). NOTAS está desactualizado |
| X2 | `decisiones-robot-casero.md` | **D06** (forma en T) sigue vigente y choca con **D12** (una sola base). D06 debería marcarse como sustituida por D12 |
| X3 | `parametros.yaml` → `asegurador` | Usa 14 × 16 mm, base 1.5, agujeros a 22 mm (**SIN FUENTE**). La ficha de UNIT (M31) dice 25 mm de ancho × 11 mm de alto. Los DXF tienen **taladros dibujados con datos inventados** |
| X4 | YAML `separadores_mm` 4 (PCB) y 2 (sensores), ventilador 8 | El kit del carrito (C09) solo trae 6/10/15/20 mm. Ninguna altura del diseño existe en el kit |
| X5 | YAML `lipo_2s` 61 × 16 × 15 | M14 dice explícitamente que no se fije medida de batería; el 3D la usa como si fuera real |
| X6 | YAML `motor_ancho/alto` 12 × 10 | M06 pendiente. Las muescas de las ruedas y la holgura entre los dos motores (4 mm en el centro) dependen de una medida que no existe |
| X7 | `generar_dxf.py` (comentario de capas) | Dice que en `PIEZAS_FANTASMA_ABAJO` van "rueda loca, placa de sensores"; en la opción A no hay rueda loca y la placa de sensores va arriba |
| X8 | `faltantes-unit.md` | Hay 2 ruedas libres en el carrito y M30 sigue en "pregunta" |
| X9 | Modelo 3D | El patín empieza en z = 0.3 mm: el robot del modelo no se apoya en ningún punto delantero |

### 3.2 Geometría y fabricación
- **Contorno con dos aristas de longitud cero** en (−24, ±49): `trasera` y `centro` tienen el mismo medio ancho. Por eso sale la advertencia
  `invalid value encountered in scalar divide` en `verificar_dxf.py`. No rompe el corte, pero es un vértice duplicado que conviene quitar.
- **Esquinas interiores vivas** en las muescas de las ruedas: en acrílico son el punto donde nace una grieta con un golpe. Conviene un radio
  de ~1.5–2 mm (*fillet*, redondeo de esquina interior).
- Margen al reglamento: 2 mm por lado en ancho y 2 mm por extremo en largo. Aceptable, pero la llanta de goma se deforma y el rin (22 mm)
  es más ancho que la llanta (21.5 mm): medir el conjunto con vernier antes de cortar.
- Verificador: comprueba planta y agujeros, pero **no** comprueba alturas, apoyo en el piso ni CG.

### 3.3 Distancia sensores–eje (*lookahead*)
Los sensores quedan a ~55–65 mm del eje. En seguidores de competición suele usarse bastante más (los sensores más adelante "ven" la curva
antes y el control es más estable a alta velocidad). Alan pidió ruedas más adelante; eso acorta esta distancia. Es un **compromiso** real,
no un error, pero hoy juega en contra en dos cosas a la vez: menos anticipación y CG detrás del eje.

### 3.4 Electrónica y mantenimiento
- La LiPo encima del ESP32 tapa el ESP32 y su USB; para reprogramar hay que despegarla. Una pieza de más de 10 g que se cae es falta.
- El ventilador encima de la PCB tapa parte de ella; para cambiar algo debajo hay que quitarlo.
- El multiplexor está en la PCB principal: los 12 cables de señal analógica de los sensores viajan por el cable de 15 hilos. Si el multiplexor
  fuera en la placa de sensores, el cable bajaría a ~8 hilos (SIG, S0–S3, EN, VCC, GND) y tendría menos ruido. **Afecta la electrónica; es
  solo una sugerencia.**
- El ruteo de las PCB no está terminado (E09). Eso hace que **ahora** sea el momento más barato para reacomodar la planta.

## 4. Succión: qué se puede esperar del 4010 (Fase 4, adelanto)

Hoy no hay cámara de succión: el ventilador jala aire por un hueco de 34 mm, pero debajo de la placa hay una rendija de 4.5 mm abierta por
todos lados. El aire entra por el borde sin crear presión: **la fuerza hacia el piso sería prácticamente cero**.

La fuerza que da la succión es: **F = ΔP × A** (diferencia de presión × área de la cámara). Cuenta de orden de magnitud, con supuestos:
- Ventilador axial 4010: su presión estática máxima suele ser de pocas decenas de pascales a 12 V; a 7.4–8.4 V la presión baja
  aproximadamente con el cuadrado de la velocidad (≈ 40–50 %). **Dato no verificado: medirlo.**
- Cámara de 60 × 80 mm (0.0048 m²) con falda bien hecha y 20–30 Pa → 0.1–0.15 N ≈ **10–15 g de fuerza extra**.
- Con una rendija de 1 mm alrededor, la fuga se come casi todo: ≈ 5 g.

Comparado con un robot de ~250 g, eso es un **2–6 %** más de carga en el mejor caso, a cambio de 16 g y ~0.1 A. La turbina centrífuga 5015
(*blower*) da bastante más presión estática con el mismo tamaño de boca, por lo que se acerca más a lo útil, pero pesa y consume algo más.
**No se compra nada todavía:** primero la prueba de la Fase 4 (báscula + plano inclinado) decide si la succión vale la pena. El diseño debe
funcionar **sin** ventilador y dejar el montaje preparado.

## 5. Dos alternativas (Fase 2)

### Alternativa A — Optimizar la placa única actual
Mismo orden: sensores al frente, motores en medio, PCB principal atrás.
- Añadir un **segundo patín trasero** (x ≈ −115) para que el borde no arrastre. Quedan 4 apoyos: 2 ruedas + 2 patines; el delantero fija la
  altura de los sensores y el trasero sostiene ≈ 25 % del peso.
- Pasar la LiPo a la franja de las ruedas si cabe (detrás de los motores), para acercar el CG al eje.
- Quitar el vértice duplicado, redondear esquinas de las muescas, aligerar la zona trasera con huecos (*pockets*).
- Rehacer `NOTAS.md`, marcar D06 sustituida, separar aseguradores "SIN FUENTE" en una capa que diga NO CORTAR.
- Succión: cámara pequeña bajo la PCB principal, lejos del eje (poco útil para las ruedas).

### Alternativa B — Rediseño compacto tipo competición (propio, no copiado)
Orden invertido: **sensores al frente → placa de sensores → PCB principal compacta → motores atrás**, todo sobre una sola placa.
- Eje de las ruedas a ~20 mm del extremo trasero. Toda la electrónica queda **delante** del eje: CG entre ruedas y patín, apoyo de 3 puntos
  real, sin patín trasero y con ≈ 70–80 % del peso sobre las ruedas (agarre).
- Sensores a ~120–140 mm del eje (más anticipación).
- LiPo baja, sobre la placa, delante del eje; ESP32 accesible (USB hacia un costado).
- Cámara de succión centrada entre el eje y el CG, con falda de lámina delgada (poliéster o cinta Kapton, *Kapton tape*) a 0.5–1 mm del
  piso; el ventilador se atornilla a la placa sobre la cámara, no encima de la PCB.
- Exige reacomodar la PCB principal a ~90 × 75–80 mm (hoy 90 × 106). Como el ruteo está incompleto (E09), el costo es razonable, pero es el
  mayor riesgo: hay que comprobar que todo cabe en una cara.

### Comparación
| Criterio | A. Optimizar | B. Compacto (motores atrás) |
|---|---|---|
| Dimensiones | 196 × 98 mm | ≈ 185–195 × 98 mm |
| Peso estimado | ≈ 250 g | ≈ 235–245 g (PCB y placa más chicas) |
| Facilidad de fabricación | Alta (casi igual que hoy) | Alta en el chasis; media en la PCB (re-acomodo) |
| Rigidez | Placa larga con muescas al centro: zona débil | Muescas al extremo trasero: menos flexión |
| Accesibilidad | LiPo/ventilador tapan electrónica | ESP32 y LiPo accesibles |
| Distribución de masa | CG cerca o detrás del eje; necesita patín trasero | CG delante del eje: 3 apoyos, buen agarre |
| Succión | Lejos del eje, poco efecto en las ruedas | Cámara donde sí carga las ruedas |
| Riesgo | Bajo en fabricación; alto en comportamiento (arrastre, agarre) | Medio: que la PCB no quepa |
| Costo extra | ~5–10 MXN (2º tornillo de nailon) | ~30–60 MXN (lámina para falda, tornillería); sin piezas nuevas de UNIT |

**Recomendación: B.** A corrige el síntoma (un segundo patín) pero deja la masa detrás de las ruedas, que es justo donde no ayuda al agarre.
B es la arquitectura que usan los seguidores rápidos por una razón física (peso sobre las ruedas, sensores lejos del eje), cabe en el
reglamento con margen y llega en el momento en que reacomodar la PCB todavía es barato. Nota: B pone las ruedas **atrás**, lo contrario de
lo que pidió Alan en D12; por eso la decisión es suya.

## 6. Medidas que bloquean cualquier diseño definitivo
| ID | Qué falta | Bloquea |
|---|---|---|
| M05, M06, P10 | Largo, ancho, alto del GA12-N20 de 1000 RPM recibido; largo y ∅ del eje | Posición de motores, muescas, ancho total |
| M31 | Asegurador: base, agujeros y su distancia | Taladros de los motores |
| M14 | LiPo elegida (medidas y peso) | Posición y CG |
| M08, P09 | Rueda con vernier (∅, ancho del conjunto rin + llanta) | Ancho total y holgura al reglamento |
| C01, C05 | Espesor real y kerf | Compensación del corte |
| C07 | Altura óptima medida sobre vinil real | Altura de sensores y patín |
| C09 | Qué separadores se usan de verdad | Todas las alturas Z |
| M21, M22 | Corriente y peso real del ventilador a 7.4–8.4 V | Succión |
