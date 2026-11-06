# Faltantes para pedir en UNIT (5 nov 2026)

Rama `engineering/robot-casero`. Tienda: <https://uelectronics.com/> (pedido por unidad).
**Solo aparece lo que todavía falta comprar.** Lo que ya se compró en Electrónica Valtierra (ticket 223209, 510 MXN) está en
`docs/faltantes_robot-casero.md`, sección 1.

**Cómo leer esta tabla**
- *V* = precio anotado por el equipo en UNIT el 31 oct 2026 (hoy no pude abrir las páginas de UNIT desde mi entorno).
- *E* = estimado mío, sin cotización: **confirmar en el carrito antes de pagar**.
- Los enlaces son la referencia que encontré por búsqueda; la existencia en almacén **no está verificada**.
- Riesgo de retraso: Alto = si falta o llega tarde, el robot no se puede armar.

## 1. Tabla para UNIT

| # | Componente | Cant. | Enlace o referencia en UNIT | MXN est. | Riesgo de retraso |
|---|---|---|---|---|---|
| 1 | Motorreductor GA12-N20 6 V **1000 RPM**, sin encoder (elegir la variante de RPM en la lista desplegable) | 2 | <https://uelectronics.com/producto/ga12-n20-motorreductor-dc-3v-6v-12v-diferentes-rpm/> | 178 (V) | **Alto**: define la tracción |
| 2 | ESP32 DevKit 38 pines (ESP-WROOM-32). Elegir la versión micro-USB o USB-C, la que se tenga cable | 1 | <https://uelectronics.com/producto/esp32-38-pines-esp-wroom-32/> (USB-C: `.../esp32-38-pines-esp-wroom-32-microusb-usb-c/`) | 131 (V) | Medio |
| 3 | Multiplexor analógico **74HC4067 16 canales, módulo "en barrita"** | 1 | <https://uelectronics.com/producto/74hc4067-multiplexor-analogico-digital-16-canales/> | 25 (V) | Medio |
| 4 | Llantas N20 34 × 7 mm, eje en D de 3 mm | 2 | Buscar "llantas N20" en UNIT (agotadas el 31 oct) | 22 (V) | **Alto**: sin existencia |
| 5 | Rueda loca (caster) mini para N20 | 1 | Buscar "rueda loca" en UNIT | 16 (V) | Medio |
| 6 | Conector JST-RC de 2 pines (par macho/hembra) | 1 | Buscar "JST RC 2 pines" | 8 (V) | Bajo, **depende del conector de la LiPo** |
| 7 | Ventilador de succión, **opción A** 4010 (40 × 40 × 10 mm) 12 V | 1 | <https://uelectronics.com/producto/ventilador-4010-12v-24v-dc-40x40x10mm/> | ~50 (E) | Medio |
| 8 | MOSFET IRLZ44N (nivel lógico, TO-220) | 1 | Buscar "IRLZ44N" | ~20 (E) | Bajo |
| 9 | Fusible reseteable (PTC) radial, 1.5 A de mantenimiento, ≥ 16 V | 1 | Buscar "fusible reseteable 1.5A" | ~15 (E) | Bajo |
| 10 | Resistencias 1/4 W 5 %: 14 × 330 Ω, 16 × 10 kΩ, 2 × 100 Ω, 1 × 100 kΩ, 1 × 33 kΩ (incluye repuestos) | 34 pzas | Buscar por valor; en UNIT se piden por pieza | ~30 (E) | Bajo |
| 11 | Sensor infrarrojo **TCRT5000 suelto** (orificio pasante), 12 + 2 repuestos | 14 | La página de UNIT parece ser el *módulo con placa* (3.2 × 1.4 cm), **no sirve** para la curva: <https://uelectronics.com/producto/sensor-seguidor-de-linea-tcrt5000-optico-infrarrojo/> | ~115 (E) | **Alto**: probablemente solo en tienda local |
| | **Subtotal UNIT (filas 1 a 10)** | | | **≈ 495** | |

## 2. Lo que NO se consigue en UNIT (comprar en León o papelería)

| Componente | MXN est. | Dónde |
|---|---|---|
| LiPo 2S (7.4 V) 450–500 mAh, ≥ 20C, con conector de balanceo | ~350 (E) | Tienda de radiocontrol/hobby. En UNIT solo vi un paquete 2S de 18650 de 2200 mAh: **demasiado pesado** (<https://uelectronics.com/producto/bateria-18650-de-7-4v-2s1p-2200mah-2s2p-4400mah/>) |
| TCRT5000 sueltos (fila 11) | ~115 (E) | Valtierra u otra tienda local |
| Cable UTP o 24–26 AWG | ~20 (E) | Redes o computación |
| Tornillos M2/M3, tuercas, separadores, cinchos | ~60 (E) | Ferretería |
| Cartulina blanca mate | ~40 (E) | Papelería |
| Cinta de vinil negra 2.5 cm | ~60 (E) | Papelería o ferretería |

## 3. Total contra presupuesto (1,500–1,800 MXN con la LiPo)

| Concepto | MXN |
|---|---|
| Ya gastado (ticket Valtierra) | 510 |
| UNIT (filas 1 a 10) | ≈ 495 |
| TCRT5000 sueltos | ~115 |
| LiPo 2S | ~350 |
| Cable, tornillos, cartulina, cinta | ~180 |
| **Total estimado, sin envío ni chasis** | **≈ 1,650** |
| Margen contra 1,800 | ≈ 150 |

**Sí cabe**, pero el margen ~150 MXN tiene que cubrir el envío de UNIT y el chasis (acrílico o MDF en taller, o PLA). Si el taller cobra mucho,
la opción barata es imprimir en 3D. El cargador B3 (227 MXN) **no** está incluido: pedir prestado uno de balanceo.

## 4. Ventiladores recomendados (elegir uno)

Los tres usan corriente continua y se manejan con el MOSFET IRLZ44N desde la LiPo (7.4–8.4 V). Un ventilador de 12 V alimentado con ~8 V gira más lento
(aprox. 60–70 % de su velocidad), así que **mueve menos aire de lo que dice la etiqueta**: es normal. Todas las cifras de consumo son **típicas de este tipo de
ventilador, sin confirmar en la página de UNIT** (por eso están como pendiente en `pendientes-por-confirmar.md`).

| Opción | Tipo y tamaño | Voltaje | Consumo típico a 12 V (por confirmar) | Comentario |
|---|---|---|---|---|
| A. [4010](https://uelectronics.com/producto/ventilador-4010-12v-24v-dc-40x40x10mm/) | Axial 40 × 40 × 10 mm | 12 V (hay de 24 V: **elegir 12 V**) | ~0.1–0.2 A | Más compacto y liviano (~10–15 g). Caben dos. **Recomendada para empezar** |
| B. [5015 turbina](https://uelectronics.com/producto/ventiladores-de-refrigeracion-5015-12v-24v-dc-impresoras-3d/) | Centrífugo (turbina) 50 × 50 × 15 mm | 12 V | ~0.1–0.2 A | Genera más presión de aire: mejor para succionar bajo una falda. Un poco más alto |
| C. [6015 turbina](https://uelectronics.com/producto/ventiladores-6015-5v-12v-24v-dc/) | Centrífugo 60 × 60 × 15 mm | 12 V (hay de 5 V y 24 V) | ~0.15–0.3 A | La más fuerte; ocupa más placa y pesa más. Solo si sobra peso (límite 500 g) |

**Cuidados:** (1) un ventilador de 12 V puede no arrancar con ciclo de trabajo (PWM) bajo; úsenlo casi al 100 % o encendido/apagado. (2) El ventilador solo se
enciende **después** de la señal del árbitro. (3) Pesar el ventilador: cualquier pieza de más de 10 g que se caiga es falta. (4) Pidan por escrito a la
organización el permiso de usar ventilador (el repo indica que está permitido, pero hay que tenerlo por escrito para la homologación).
