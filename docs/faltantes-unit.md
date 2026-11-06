# Faltantes para pedir en UNIT (5 nov 2026)

Rama `engineering/robot-casero` (actualizado 6 nov 2026). Tienda: <https://uelectronics.com/> (pedido por unidad).
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
| 1 | Motorreductor GA12-N20 6 V **1000 RPM**, sin encoder (aún no se compran, P10) | 2 | <https://uelectronics.com/producto/ga12-n20-motorreductor-dc-3v-6v-12v-diferentes-rpm/> | 178 (V) | **Alto**: define la tracción |
| 2 | Asegurador (soporte) para motor N20 (el blanco de la foto) | 2 | Buscar "soporte motorreductor N20" en UNIT | ~30 (E) | Medio: sin él hay que usar cinchos |
| 3 | Multiplexor analógico **74HC4067**, módulo | 1 | <https://uelectronics.com/producto/74hc4067-multiplexor-analogico-digital-16-canales/> | 25 (V) | Medio |
| 4 | Conector JST-RC 2 pines (par) | 1 | Buscar "JST RC 2 pines" | 8 (V) | Bajo, depende de la LiPo |
| 5 | Ventilador 4010 (40 × 40 × 10 mm) **12 V** | 1 | <https://uelectronics.com/producto/ventilador-4010-12v-24v-dc-40x40x10mm/> | ~50 (E) | Medio |
| 6 | MOSFET IRLZ44N (TO-220) | 1 | Buscar "IRLZ44N" | ~20 (E) | Bajo |
| 7 | Fusible reseteable (PTC) radial 1.5 A | 1 | Buscar "fusible reseteable 1.5A" | ~15 (E) | Bajo |
| 8 | Resistencias 1/4 W: 14 × 330 Ω, 16 × 10 kΩ, 2 × 100 Ω, 1 × 100 kΩ, 1 × 33 kΩ | 34 pzas | Por valor | ~30 (E) | Bajo |
| 9 | Tira de pines macho y hembra de 15 (cable de la placa de sensores) | 1 + 1 | Buscar "header 1x40" | ~20 (E) | Bajo |
| | **Subtotal UNIT (filas 1 a 9)** | | | **≈ 376** | |

Ya **no** se compran: ESP32 (tienen uno de 30 pines, D03), llantas (D09), DRV8833 y MP1584 (ticket). La **rueda loca** sale de la lista si
se aprueba el patín (O02); si no, agregar 16 MXN.

## 1b. Lo que NO se encontró (o no conviene) en UNIT, con alternativa

| Componente | Por qué no en UNIT | Alternativa | MXN est. |
|---|---|---|---|
| LiPo 2S 450–500 mAh con balanceo | Solo vi un paquete 18650 2S de 2200 mAh: muy pesado | Tienda de radiocontrol en León o Mercado Libre (envío de LiPo puede tardar) | ~350 (E) |
| TCRT5000 suelto (14) | La página de UNIT parece ser el módulo con placa, que no cabe en el arco | Valtierra / tiendas locales; última opción: desoldar el sensor de 14 módulos | ~115 (E) |
| Brocas 1.0 y 1.3 mm | Ferretería | Ferretería o tienda de electrónica | ~30 (E) |
| Tornillo M3 de cabeza redonda de **nailon** (patín) | Ferretería | Tornillo M3 metálico con cabeza redonda pulida | ~10 (E) |
| Separadores M3 de 2 mm y 4 mm, tornillos M2 para aseguradores | Ferretería | Tuercas M3 como separador | ~40 (E) |
| Cable plano de 15 hilos (o cable UTP) | — | Cable plano de disco duro viejo / 2 cables UTP | ~20 (E) |

## 3. Total contra presupuesto (1,500–1,800 MXN con la LiPo)

| Concepto | MXN |
|---|---|
| Ya gastado (ticket Valtierra) | 510 |
| UNIT (filas 1 a 9) | ≈ 376 |
| Fuera de UNIT (LiPo, TCRT5000, brocas, tornillería, cable) | ≈ 565 |
| Cartulina y cinta de vinil (pista de prueba) | ~100 |
| **Total estimado, sin envío ni chasis** | **≈ 1,551** |
| Margen contra 1,800 | ≈ 249 |

**Sí cabe.** **Fecha límite de pedido:** no la dieron ([FECHA LÍMITE] vacío). Recomiendo pedir a UNIT **a más tardar el 7 de noviembre**
(el tiempo de entrega de UNIT no está verificado: revisarlo en el carrito).

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
