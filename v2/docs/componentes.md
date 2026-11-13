# Componentes (V2)
Compras: ticket Valtierra 5 nov y pedido UNIT 7 nov (ver `robot-casero/materiales/BOM.csv`, histórico).

## A. Montados en PCB principal
| Ref | Pieza | Usadas / compradas |
|---|---|---|
| A1 | ESP32 DevKit 30p USB-C | 1 / 1 |
| U1, U2 | Módulo MP1584 (5.0 V y 6.0 V) | 2 / 2 (sin repuesto) |
| U3 | Módulo DRV8833 | 1 / 2 |
| D1, D2 | 1N5822 (rueda libre ventilador; aislamiento USB) | 2 / 3 (Alan; el BOM viejo dice 2 → conciliar) |
| Q1 | IRLZ44N | 1 / 3 |
| C1, C2 | 470 µF 16 V | 2 / 2 |
| C3, C4, C5 | 100 nF cerámico | 3 (+1 en sensores) / 5 |
| R1, R2, R4, R5 | 100 k, 33 k, 100 Ω, 10 k | por comprar |
| F1 | PTC reseteable 1.5 A ≥ 16 V | por comprar |
| SW2, SW3, SW4 | Pulsadores START / CAL / RESET | 3 / 3 |
| J1–J6 | Headers para cables (5 × 1x2, 1 × 1x9) | tira macho y hembra 2.54 mm (Alan, 12 nov) |

## B. Montados en PCB de sensores
| Ref | Pieza | Usadas / compradas |
|---|---|---|
| OP1–OP12 | TCRT5000 | 12 / 14 |
| U1 | Módulo CD74HC4067 | 1 / 2 |
| Q1 | 2N2222 (H331, E-B-C) | 1 / 6 |
| R1–R12 | 220 Ω | por comprar |
| R13–R24, R26 | 10 kΩ | por comprar |
| R25 | 470 Ω | por comprar |
| C1 | 100 nF | ver arriba |
| J1 | Header 1x8 | ver P-V2-07 |

**Resistencias a comprar (total):** 12 × 220 Ω, 14 × 10 kΩ, 1 × 470 Ω, 1 × 100 Ω, 1 × 100 kΩ, 1 × 33 kΩ (+ repuestos a criterio).
Se quitaron del listado viejo: 2 × 1 kΩ sobrantes→ ahora 1, 1 × 100 Ω sobrante, R3 de nSLEEP.

## C. Eléctricos externos (en el esquema, sin huella; llegan por cable)
BT1 LiPo 2S → J1 · SW1 KCD1 → J2 · M1/M2 motores N20 → J3/J4 · M3 ventilador 4010 → J5 · cable de 8 hilos J6 ↔ J1 sensores.

## D. Mecánicos
Base (acrílico ≤ 3 mm), 2 llantas con rin, 1 rueda loca (+1 repuesto), 2 soportes N20 con tornillos M2, kit separadores M3 UNIT, tornillos M3.

## E. Insumos y herramientas
Placa fenólica 20 × 20 (D-V2-03), cloruro férrico, brocas 0.8 (tengo) y 1.0/1.3/3.2 mm (por comprar), estaño, pasta, termofit,
cable 18 AWG, cable 22–26 AWG, alambre para vías, papel de transferencia, cartulina y vinil para pista.
**Por comprar:** LiPo 2S 450–500 mAh, PTC, resistencias, brocas, cable fino, cartulina, vinil.
