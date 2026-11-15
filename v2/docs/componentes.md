# Componentes (V2) — GENERADO desde `v2/inventario.csv`

No editar a mano: se cambia `v2/inventario.csv` y se corre `python3 v2/herramientas/generar_componentes.py`.
Compras: ticket Electrónica Valtierra 5 nov y pedido UNIT 7 nov (detalle de precios en el BOM histórico `robot-casero/materiales/BOM.csv`).
**Repuesto = comprada − usada.** *Usada* se verifica contra los esquemáticos con `v2/herramientas/validar_repo.py`.

| Pieza | Comprada | Usada | Repuesto | Estado | Nota |
|---|---|---|---|---|---|
| ESP32 DevKit 30p USB-C | 1 | 1 | 0 | recibida y confirmada | Sobre tira hembra |
| Módulo MP1584 (5.0 V y 6.0 V) | 2 | 2 | 0 | recibida y confirmada | Sin repuesto. Ajustar a 5.0 y 6.0 V (E01/E02) |
| Módulo DRV8833 | 2 | 1 | 1 | recibida y confirmada | 1 de repuesto |
| Diodo 1N5822 (D1 rueda libre ventilador; D2 aislamiento USB) | 2 | 2 | 0 | recepción sin confirmar | CONFLICTO: la migración del 12 nov anotó 3. Ver P-V2-39 |
| MOSFET IRLZ44N (TO-220) | 3 | 1 | 2 | recepción sin confirmar | 2 de repuesto |
| Transistor 2N2222 (TO-92; marcado H331; E-B-C) | 6 | 1 | 5 | recibida y confirmada | 5 de repuesto |
| Capacitor electrolítico 470 µF 16 V | 2 | 2 | 0 | recepción sin confirmar | Sin repuesto |
| Capacitor cerámico 100 nF | 5 | 4 | 1 | recepción sin confirmar | 3 en principal + 1 en sensores; 1 de repuesto |
| Pulsador 4 patas (SW2 12 mm; SW3 y SW4 6 mm) | 3 | 3 | 0 | recepción sin confirmar | Sin repuesto |
| Sensor TCRT5000 (individual) | 14 | 12 | 2 | recibida y confirmada | 2 de repuesto |
| Módulo multiplexor CD74HC4067 | 2 | 1 | 1 | recibida y confirmada | 1 de repuesto |
| Resistencia 220 Ω 1/4 W | 0 | 12 | — | por comprar | Sensores R1-R12 |
| Resistencia 10 kΩ 1/4 W | 0 | 14 | — | por comprar | Sensores R13-R24 y R26 + principal R5 |
| Resistencia 470 Ω 1/4 W | 0 | 1 | — | por comprar | Sensores R25 |
| Resistencia 100 Ω 1/4 W | 0 | 1 | — | por comprar | Principal R4 |
| Resistencia 100 kΩ 1/4 W | 0 | 1 | — | por comprar | Principal R1 |
| Resistencia 33 kΩ 1/4 W | 0 | 1 | — | por comprar | Principal R2 |
| PTC reseteable Bel Fuse 0ZRE0150FF1A (F1) | 0 | 1 | — | por comprar | Ver P-V2-44 |
| Header macho 1x2 (J1-J5) y 1x9 (J6 y sensores J1): 28 pines | ? | 28 | ? | recepción sin confirmar | Ver P-V2-41 |
| Tira hembra para ESP32/MP1584/DRV8833/mux | 80 | 74 | 6 | recepción sin confirmar | Ver P-V2-41 |
| Conector JST-RC (pares macho/hembra) | 2 | 1 | 1 | recepción sin confirmar | Conector de batería; 1 par de repuesto |
| Motorreductor GA12-N20 6 V 1000 RPM | 2 | 2 | 0 | recibida y confirmada | Eje 2.3 mm medido (D-V2-11) |
| Ventilador 4010 12 V | 1 | 1 | 0 | recibida y confirmada | Pesado 15 g el 13 nov |
| Mini rueda universal 3Pi N20 (rueda loca) | 2 | 1 | 1 | recepción sin confirmar | 1 de repuesto (D-V2-10) |
| Soporte motorreductor N20 con tornillos M2 | 2 | 2 | 0 | recepción sin confirmar |  |
| Kit separadores de latón M3 (120 piezas) | 1 | 1 | 0 | recibida y confirmada | Pesados 13 nov |
| Interruptor de balancín (BOM: SW-104S; diseño: KCD1 rojo) | 1 | 1 | 0 | recepción sin confirmar | Ver P-V2-42 |
| LiPo 2S 7.4 V 450-500 mAh | 0 | 1 | — | por comprar | M14 |
| Cable 18 AWG (potencia) | ? | ? | ? | recepción sin confirmar | Ver P-V2-43 |

## Externos y mecánicos sin fila en el inventario
Base de acrílico (≤ 3 mm), 2 llantas con rin (ya disponibles, M08), placa fenólica 20 × 20 cm doble cara (comprada), cloruro férrico, broca 0.8 mm, estaño, pasta, termofit (comprados).
**Por comprar:** LiPo 2S, PTC, resistencias (30 en total: 12 × 220 Ω, 14 × 10 kΩ, 1 × 470 Ω, 1 × 100 Ω, 1 × 100 kΩ, 1 × 33 kΩ), brocas 1.0 / 1.3 / 3.2 mm, cable fino, alambre para vías, cartulina, vinil.

## Pesos medidos (Alan, báscula)
| Pieza | Peso | Fuente |
|---|---|---|
| Ventilador 4010 | 15 g | 13 nov (ficha: 16 g) |
| Separadores M3 macho/hembra 6 y 10 mm | ≈ 1 g c/u | 13 nov |
