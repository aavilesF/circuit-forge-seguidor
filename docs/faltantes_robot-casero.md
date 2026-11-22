# Faltantes para el robot casero (5 nov 2026) — HISTÓRICO

> **Desactualizado.** La lista vigente es `docs/faltantes-unit.md` y las decisiones están en `docs/decisiones-robot-casero.md`.
> Se conserva solo como registro del ticket de compra (sección 1).

Rama `engineering/robot-casero`. Compara tres fuentes: la lista que acordó el equipo, el ticket de Electrónica Valtierra
(223209, 5 nov 2026, 510 MXN) y lo que ya había en el repositorio (`docs/presupuesto.md`, `docs/decisiones.md`, `firmware/seguidor/pines.h`).

**Cómo leer los precios.** *V* = verificado en UNIT el 31 oct 2026 (según el archivo de contexto del equipo; no se pudo volver a abrir
la página de UNIT hoy). *T* = precio real del ticket de Valtierra. *E* = estimado, sin cotización: confirmar antes de pagar.
La tienda física cuesta más que UNIT (en el ticket, MP1584 a 30 contra 19 y DRV8833 a 33 contra 24).

## 1. Ya lo tenemos (ticket Valtierra, total 510 MXN)

| Componente | Cant. | MXN (T) |
|---|---|---|
| Broca 0.8 mm | 1 | 15 |
| Cloruro férrico | 1 | 32 |
| Termofit 1/8" | 1 | 11 |
| Conector hembra de headers (CON-HH40) | 2 | 28 |
| Conector "5030552" (tipo por confirmar) | 2 | 12 |
| Pulsadores de 4 patas (2 pequeños, 1 ancho) | 3 | 16 |
| Diodo Schottky 1N5822 | 2 | 20 |
| Transistor 2N2222 | 6 | 36 |
| Capacitor cerámico 100 nF | 5 | 15 |
| Capacitor electrolítico 470 µF 16 V | 2 | 7 |
| Interruptor balancín | 1 | 13 |
| Cable 18 AWG | 3 | 33 |
| Tubo de soldadura (estaño) | 1 | 40 |
| Pasta para soldar | 1 | 32 |
| Placa fenólica 20 × 20 cm | 1 | 74 |
| Módulo MP1584 | 2 | 60 |
| Módulo DRV8833 | 2 | 66 |
| **Subtotal ya gastado** | | **510** |

## 2. Faltantes

| Componente | Cant. | Precio est. (MXN) | Tienda sugerida | ¿Ya lo tenemos? | Riesgo de llegar tarde |
|---|---|---|---|---|---|
| Motorreductor GA12-N20 6 V 1000 RPM, sin encoder | 2 | 178 (V) | UNIT en línea; preguntar antes a Valtierra | No | **Alto**: es la pieza que define la tracción; no hay sustituto rápido |
| LiPo 2S 450–500 mAh, ≥ 20C, con balanceo | 1 | ~350 (E) | Tienda de radiocontrol local (León) | No | **Alto**: sin cotizar; las baterías LiPo suelen tener restricciones de envío por paquetería (por confirmar) |
| Llantas N20 34 × 7 mm, eje en D de 3 mm | 2 | 22 (V) | Otra tienda (agotadas en UNIT el 31 oct) | No | **Alto**: sin existencia |
| Sensores TCRT5000 individuales, orificio pasante | 14 (12 + 2 de repuesto) | ~115 (E) | Valtierra o tienda local | No | **Alto**: la página de UNIT que apareció en la búsqueda parece ser el *módulo* con placa, no la pieza suelta (no se pudo abrir para confirmar). Se necesita la pieza suelta |
| ESP32 DevKit 38 pines (ESP32-WROOM-32) | 1 | 131 (V) | UNIT; preguntar antes a Valtierra | No | Medio |
| Multiplexor 74HC4067, DIP-24 o módulo | 1 | 25 (V) | UNIT | No | Medio: verificar que no sea la versión SMD sola |
| Rueda loca mini N20 | 1 | 16 (V) | UNIT | No | Medio |
| Resistencias 1/4 W 5 %: 14 × 330 Ω, 16 × 10 kΩ, 2 × 100 Ω, 1 × 100 kΩ, 1 × 33 kΩ (ya incluyen repuestos; las de 1 kΩ ya no se usan) | surtido | ~15 (E) | Valtierra | No | Bajo |
| Fusible reseteable radial, 1.5 A de mantenimiento, ≥ 16 V (orificio pasante) | 1 | ~15 (E) | Valtierra o UNIT | No | Bajo |
| Conector JST-RC (par, 2 pines) que coincida con la LiPo | 1 | 8 (V) | UNIT | No | Bajo, pero **depende de qué conector traiga la batería** |
| Cable UTP o 24–26 AWG para la barra de sensores y motores | ~1 m | ~20 (E) | Tienda de redes o computación | No | Bajo |
| Tornillos M2/M3, tuercas, separadores M3 de 10–15 mm, cinchos 100 mm | surtido | ~60 (E) | Ferretería | No | Bajo |
| Cartulina blanca mate (≥ 1.2 m) | 1 | ~40 (E) | Papelería | No | Bajo |
| Cinta de vinil negra de 2.5 cm | 1 | ~60 (E) | Papelería o ferretería | No | Bajo |
| MOSFET IRLZ44N (nivel lógico) | 1 | ~20 (E) | Valtierra | No | Bajo |
| Motor DC con escobillas para el ventilador (clase 720 u 8520) | 1 | ~100 (E) | Por definir con el diseño del rotor | No | Medio: falta el diseño |
| **Subtotal faltantes (sin envío, chasis ni cargador)** | | **~1,175** | | | |

## 3. Opcionales y por confirmar

| Componente | Precio | Nota |
|---|---|---|
| Cargador balanceador B3 2S | 227 (V) | Solo si la escuela no presta uno. **Con él el total se pasa del presupuesto** |
| Cautín 30–40 W, malla desoldadora | por confirmar | No sabemos si el equipo ya los tiene |
| Multímetro | ~150 (cifra del repo, sin verificar) | Indispensable para ajustar el MP1584 a 5.0 V. ¿Lo tienen? |
| Báscula de 1 g | ~124 (cifra del repo, sin verificar) | Para el control de peso y medir la succión del ventilador |
| Material del chasis (acrílico o PLA) | sin cotizar | Falta decidir material y servicio |
| Envío en línea | sin verificar | Se ve en el carrito de UNIT al pagar |

## 4. Total contra presupuesto (1,500–1,800 MXN, incluida la LiPo)

| Concepto | MXN |
|---|---|
| Ya gastado (ticket) | 510 |
| Faltantes (sin envío, chasis ni cargador) | ~1,175 |
| **Total estimado** | **~1,685** |
| Margen contra el tope de 1,800 | ~115 |

- **Cabe**, pero con poco margen: ~115 MXN deben cubrir el envío, el material del chasis y cualquier diferencia de precio en tienda.
- **Con el cargador B3 ($227) el total sería ~1,912 y se pasa.** Pidan prestado el de la escuela.
- Si hace falta recortar: el motor del ventilador (~100) puede esperar a que el robot siga la línea sin él, y la cartulina y la cinta se pueden resolver con material que ya tengan.

## 5. Fecha límite para pedir

- Competencia: sábado **21 de noviembre**. Registro hasta el 17 de noviembre, 6:00 pm (`README.md`). Congelamiento del diseño propuesto en el repo: 15 de noviembre.
- **No pude verificar el tiempo de entrega de UNIT** (la página de envíos no abrió). Revisen la fecha estimada que muestra el carrito antes de pagar.
- **Recomendación (criterio mío, no dato verificado):** que las piezas críticas estén en la mano a más tardar el **11 de noviembre**, para tener unos 10 días de armado y afinación. Con eso, el pedido en línea debería hacerse **hoy o mañana (6 de noviembre)**.
- Primero pregunten a Valtierra por WhatsApp (477 397 6529, viene en el ticket) por motores, ESP32, TCRT5000 sueltos y resistencias: si los tienen, se compran hoy mismo en León. Lo que no tengan se pide a UNIT de inmediato.

## 6. Diferencias con lo que ya estaba en el repo

| Tema | En el repo (`presupuesto.md`, `pines.h`) | Robot casero |
|---|---|---|
| Sensor | QTR-8A (8 canales) o curvo de 24 | 12 × TCRT5000 en PCB propia |
| Driver | TB6612FNG | DRV8833 (2 pines de control por motor, sin pin STBY) |
| Alimentación de motores | Buck de 6 V (propuesta P7) | Directo de la LiPo con el PWM limitado a ~6 V efectivos (P7 sin decidir) |
| Divisor de batería | 100 kΩ / 47 kΩ | 100 kΩ / 33 kΩ (resultado 2.08 V a 8.4 V) |
| Multiplexores | 1 o 2 × CD74HC4067 | 1 × 74HC4067 |
| Chasis | por confirmar | por confirmar; sigue pendiente el correo a la organización |

**Impacto en firmware:** `firmware/seguidor/pines.h` y `hardware.cpp` están escritos para TB6612 y 8 o 24 sensores. Habrá que
adaptarlos al DRV8833 y a 12 sensores. No se modificaron en esta rama.


## Actualización 15 nov 2026 (respuestas de Alan)
Fuente vigente de cantidades: **`v2/inventario.csv`** (este archivo solo conserva la lista original de la rama anterior).
- **Recibido en UNIT (7 nov):** todo el pedido, confirmado por Alan (D-V2-36). Incluye IRLZ44N, ruedas locas 3Pi, soportes N20, JST-RC, motores, ventilador, separadores y mux.
- **Diodos 1N5822:** se compraron 3; 2 en uso y 1 de recambio (D-V2-34, P-V2-39).
- **Interruptor:** el SW-104S comprado es el KCD1 del diseño (D-V2-35, P-V2-42).
- **Cable 18 AWG:** 3 m en total, 1.5 m rojo y 1.5 m negro, de reserva (D-V2-35, P-V2-43).
- **Por comprar:** LiPo 2S (M14), PTC Bel Fuse 0ZRE0150FF1A (D-V2-24, P-V2-44), resistencias (ver `componentes.md`), brocas 1.0 / 1.3 / 3.2 mm, cable 22–26 AWG, alambre para vías, cartulina y vinil.
- **Por aclarar:** conectores "5030552" (P-V2-41) y una pieza que la tienda no anotó (P-V2-45).

---
