# Opciones de diseño del robot (6 nov 2026)

Alan revisó en AutoCAD el diseño en "T" (placa de sensores colgada debajo de un travesaño) y no le gustó: quiere un robot **más unido**,
todo en **una sola base de acrílico**, sin segundos pisos, lo más **compacto** posible y con las ruedas más adelante.
Este documento compara las opciones y explica la que quedó dibujada. **La elección final es de Alan (P12).**

## 1. ¿A qué altura deben ir los sensores?

| Dato | Valor | Fuente |
|---|---|---|
| Distancia de mejor respuesta del TCRT5000 | **2.5 mm** ("peak operating distance") | Hoja de datos Vishay TCRT5000 ([copia en EPFL](https://www.epfl.ch/campus/associations/robopoly/wp-content/uploads/2018/09/TCRT5000.pdf)) |
| Rango útil (corriente > 20 % del máximo) | 0.2 a 15 mm | misma hoja de datos |

**Decisión propuesta:** cara del sensor a **2.5–3 mm** de la pista. Más cerca de 1 mm roza la pista en las uniones; más lejos de ~6 mm el
contraste blanco/negro baja mucho y la luz ambiente pesa más. Por eso la placa de sensores queda casi pegada al acrílico y la altura fina se
ajusta con arandelas (0.5–1 mm). Queda como C07 por confirmar en la pista real.

## 2. Problema de la rueda loca
Con los sensores a 2.5 mm del piso, la placa de acrílico tiene que ir **muy baja** (su cara inferior a ~4.5 mm del piso). Una rueda loca
mini mide más que eso y levantaría el frente. Opciones:

| Opción | Ventajas | Desventajas |
|---|---|---|
| O01. Rueda loca mini (la de UNIT) | Rueda de verdad, poca fricción | Levanta el frente (los sensores se alejan); ocupa espacio; hay que cortar una ventana |
| **O02. Patín: tornillo M3 de cabeza redonda de nailon** bajo el centro de la placa de sensores | Casi no ocupa espacio, cuesta ~5 MXN, la altura se ajusta con tuercas; mantiene los sensores a altura fija | Roza la pista (poca fricción si la cabeza es lisa y redonda); se gasta y se cambia |
| O03. Bolita de acero en cuna impresa en 3D | Fricción muy baja | Otra pieza que imprimir y medir |

**Propuesta: O02** (un solo patín al centro + las dos ruedas = 3 puntos de apoyo, como muchos seguidores profesionales). La rueda loca (M30)
quedaría obsoleta si Alan lo aprueba.

> Nota de nombres: en la tabla de pendientes "O03" también se usa para la separación de patas del diodo (sección 5 de este documento).
> Para no confundir, la del diodo es **O05**.

## 3. Forma del robot: una sola base

| | **Opción A (recomendada): todo sobre una placa baja** | Opción B: subir la LiPo y bajar la PCB principal | Diseño anterior en T (5 nov) |
|---|---|---|---|
| Placas de acrílico | 1 | 1 | 1, con la placa de sensores colgada debajo |
| Placa de sensores | Encima de la misma placa; los sensores bajan por **12 ventanas** en el acrílico | igual que A | colgada debajo con separadores |
| PCB principal | Sobre la placa con separadores de 4 mm | Sobre la placa | En segundo piso (18 mm) |
| LiPo | Pegada encima del ESP32 (cinta doble cara o cincho) | En un soporte encima de la PCB | Entre la placa y la PCB |
| Ventilador | Sobre un hueco de 34 mm que atraviesa PCB y placa, salida libre | igual | Tapado por la PCB |
| Altura total | ~45 mm (hasta la LiPo) | ~50 mm | ~55 mm |
| Centro de gravedad | **Muy bajo** | Algo más alto | Alto |
| Riesgo | La LiPo arriba del ESP32 calienta poco (no hay radio encendido) pero hay que fijarla bien (pieza > 10 g que se cae = falta) | Más piezas | Sensores lejos del piso |

**Por qué no "sin nada encima" al 100 %:** los motores N20 miden 10 mm de alto y su eje queda a 14 mm (radio de la llanta). La PCB no puede
pasar por encima de los motores sin ser un segundo piso, y los motores ocupan casi todo el ancho entre las ruedas. Por eso el robot se ordena
en **tres franjas** a lo largo: sensores al frente, motores al centro y PCB principal atrás. Esto también obliga a que sean **dos PCB**
(una delante y otra detrás de los motores), unidas por un cable de 15 hilos, pero **las dos sobre la misma base**.

## 4. Tamaño final y por qué
- Ancho: **98 mm**. Lo fija el arco de 12 sensores a 7.5 mm (88 mm) más el borde de la placa, y las ruedas (cara exterior a 48 mm del centro).
- Largo: **196 mm** = placa de sensores 50 mm + franja de motores 44 mm + PCB principal 102 mm.
  La PCB principal es la que manda: mide 90 × 106 mm porque la PCB casera usa pistas de 0.8 mm, módulos grandes (ESP32, 2 MP1584, DRV8833,
  multiplexor) y el hueco del ventilador. **No se usó el espacio por gusto:** para acortar más habría que pasar a PCB de doble cara o
  cambiar el ventilador de lugar (ver sección 6).
- Ruedas: el eje quedó **a 50 mm del frente de la placa de sensores** y a ~86 mm de los sensores del centro: las ruedas ya no están atrás,
  están al centro del robot, justo detrás de los sensores (lo que pidió Alan).

## 5. Diodo 1N5822: separación de patas (O05)
Alan pidió 3.5 cm entre patas para no forzarlas (M24). En la PCB nueva se usó la huella estándar de **15.24 mm** (deja ~3 mm de pata recta
a cada lado del cuerpo, que es lo normal) para que quepa todo. Si prefieren más, la de 20.32 mm ya existe en la biblioteca del proyecto.
**Pendiente de Alan (M24).**

## 6. Idea de Alan para R02: dos placas fenólicas "palmadas" (O04) — opción, no decisión

**La idea:** grabar dos placas de una cara: una con pistas abajo y otra con pistas arriba; pegarlas espalda con espalda (o con una capa
aislante en medio) y soldar componentes por arriba y por abajo.

| | O04. Dos placas fenólicas pegadas | Doble cara casera (una placa de doble cobre) | Una cara + puentes de alambre (descartada el 11 nov: se eligió doble cara, D18) |
|---|---|---|---|
| Cruces de pistas | Sí, por la otra placa | Sí, por la otra cara | Con alambres |
| Unir las dos caras | Hay que pasar **cada** pata y cada vía por las dos placas y soldar en ambas; las placas deben coincidir al décimo de mm | Alinear dos fotolitos en la misma placa y hacer vías con alambre | No hace falta |
| Soldar la cara de arriba | Difícil: el cuerpo de la pieza tapa la soldadura | Difícil por la misma razón | Fácil |
| Grosor y peso | ~3.2 mm, el doble de peso | 1.6 mm | 1.6 mm |
| Riesgo | Alto: desalineación, cortos entre caras si la capa aislante falla, soldaduras ocultas | Medio | Bajo, pero ~50 alambres |
| Material | Dos placas (ya tienen 1 de 20 × 20 cm) | Placa de doble cara (~60–90 MXN, no comprada) | Ya lo tienen |

**Evaluación:** la idea funciona en teoría (es lo que hace una PCB de dos capas), pero para soldadura manual es la opción **más difícil**:
cada pata tiene que soldarse en dos placas separadas y las soldaduras de arriba quedan tapadas. Si se quieren menos alambres, es mejor
una **placa de doble cara** y solo poner por arriba las pistas que crucen (como "puentes impresos"). Queda registrada como **O04, sin decidir**.

## 7. Referencias que mandó Alan
| Referencia | Para qué sirve aquí | Licencia | ¿Se copió código? |
|---|---|---|---|
| [sparkfun-kicad-libraries](https://github.com/sparkfun/sparkfun-kicad-libraries) | Símbolos y huellas de módulos | CC BY-SA 4.0 (según su repositorio; revisar antes de copiar) | No |
| [JLCPCB-Kicad-Library](https://github.com/CDFER/JLCPCB-Kicad-Library) | Piezas SMD de JLCPCB (no aplica a PCB casera) | revisar en el repositorio | No |
| [MarsRoverHardware](https://github.com/uwrobotics/MarsRoverHardware), [best practices](https://michael-vl.github.io/learning-wiki/kicad/best-practices/), [Embedded Encyclopedia](https://qtejada.github.io/Embedded-Encyclopedia/docs/PCB-Layout/Overview) | Buenas prácticas: separar potencia y señal, conectores al borde, desacoplo cerca del chip | contenido de lectura | No |
| [KiCadRoutingTools](https://github.com/drandyhaas/KiCadRoutingTools) | Enrutado automático; alternativa al enrutador propio | revisar | No |
| [ezdxf](https://github.com/mozman/ezdxf) | Biblioteca con la que se generan los DXF | MIT | Se usa como biblioteca (pip), no se copia |
| [realdwg-web](https://github.com/mlightcad/realdwg-web), [cad-data](https://github.com/mlightcad/cad-data) | Ver DWG/DXF en el navegador; archivos de ejemplo | revisar | No |

No se copió código ni huellas de ninguna de estas fuentes; las huellas del proyecto son propias.
