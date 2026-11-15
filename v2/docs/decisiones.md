# Decisiones vigentes (V2)
| ID | Decisión | Origen |
|---|---|---|
| D-V2-01 | Reglamento: robot ≤ 200 × 100 mm, ≤ 500 g, sin telemetría inalámbrica; arranque con pulsador | Reglas del proyecto |
| D-V2-02 | ESP32 DevKit 30 pines USB-C, DRV8833 en módulo, 2 × MP1584 (5.0 V lógica, 6.0 V motores), N20 6 V sin encoder, LiPo 2S, ventilador 4010 12 V con IRLZ44N | D02–D04 anteriores, confirmado por Alan 12 nov |
| D-V2-03 | **PCB principal y de sensores de doble cara** (una placa fenólica con cobre en ambas caras). Definitivo; requisito de la etapa 2. Optimizar tamaño | Alan, 12 nov |
| D-V2-04 | 12 TCRT5000 sueltos + CD74HC4067 en la placa de sensores; cable de **9 hilos** a la principal (corregido 15 nov; antes decía 8, ver D-V2-19) | D05/D16/D20 anteriores |
| D-V2-05 | Sin zumbador, sin LED extra, sin pulldown externo en nSLEEP (el chip trae 500 kΩ), sin nFAULT conectado (P13) | D19 + Alan 12 nov |
| D-V2-06 | 3 pulsadores: START (12 × 12 mm), CAL y RESET (6 × 6 mm) | Alan, 12 nov |
| D-V2-07 | Interruptor KCD1 rojo en el chasis, cableado a la PCB (18.8 × 6.7 × 16.5 mm, 25 mm con terminales) | M27 anterior |
| D-V2-08 | Fusible PTC reseteable a la entrada de batería; valor: ver D-V2-13 y D-V2-24 (corregido 15 nov; P-V2-03 resuelto) | D24 + Alan 12 nov |
| D-V2-09 | Solo símbolos oficiales de KiCad o los de `SDL V2 General/KiCAD/Librerias` aprobados por Alan | Alan, 12 nov |
| D-V2-10 | Se usa 1 rueda loca 3Pi N20 (otra de repuesto) | Alan, 12 nov |
| D-V2-11 | Eje del N20: **diámetro ≈ 2.3 mm** (entra en el rin de 2.3 mm). El "3 mm" anterior era una longitud, no diámetro. Sobresale 8.5 mm (M05) | Alan, 12 nov (cierra P19) |
| D-V2-12 | Nunca se borran IDs; los de la rama anterior quedan en sus archivos históricos | D11 |
| D-V2-13 | PTC de referencia: radial reseteable **1.5 A de mantenimiento, ≥ 16 V** (no comprado) | Alan, 12 nov |
| D-V2-14 | Botón RESET (SW4 a EN) se queda en la PCB aunque el DevKit tenga el suyo | Alan, 12 nov |
| D-V2-15 | ESP32, MP1584, DRV8833 y mux irán sobre **tira hembra** en la PCB (los módulos usan sus pines macho) para poder cambiarlos. No se dibuja en el esquema | Alan, 12 nov |
| D-V2-16 | TCRT5000: símbolo de Alan + **huella oficial de KiCad**. Pines confirmados (M20) | Alan, 12 nov |
| D-V2-17 | Fichas de UNIT valen como medida oficial hasta medir con vernier | Alan, 12 nov |
| D-V2-18 | Esquemáticos con cables reales; etiquetas solo de complemento (cable entre placas) | Alan, 12 nov |
| D-V2-19 | LED de los TCRT5000 a **+5V** (9.º hilo, 220 Ω, R25 470 Ω); mux y pull-ups siguen en 3.3 V | Alan, 13 nov |
| D-V2-20 | Esquemáticos V2 terminados (13 nov) | Alan aprueba la presentación |
| D-V2-21 | Se conserva el ventilador 4010 en el diseño (eficacia aún no comprobada) | Alan, 13 nov |
| D-V2-22 | Correcciones de MP1584, DRV8833 (2.54 / 15.7 mm), mux (15.7 mm) y TCRT5000 aprobadas | Alan, 13 nov |
| D-V2-23 | Sensores en curva, en la cara inferior, mirando al piso | Alan, 13 nov |
| D-V2-24 | **PTC a comprar: Bel Fuse 0ZRE0150FF1A** (Digi-Key 5923-0ZRE0150FF1A-ND), la pieza que corresponde a la huella oficial `Fuse_BelFuse_0ZRE0150FF_L23.4mm_W5.3mm` de F1. Datos de Digi-Key (no se pudo leer la hoja de datos): 1.5 A mantenimiento, 3 A disparo, 240 V, ∅23.4 × 5.3 mm, patas a 10.2 mm. Existencia y plazo por verificar (P-V2-44) | Alan, 14 nov ("el que tú me diste y pusiste en la PCB") |
| D-V2-25 | **PCB de sensores: opción B, 96 × 59 mm** (corta, curva). La principal de 96 × 74 mm queda aprobada. La opción A (96 × 68 mm) queda como alternativa en `v2/electronica/sensores/alternativa_68mm_curva/` | Alan, 14 nov (P-V2-38, P-V2-32) |
| D-V2-26 | El ventilador se queda. Si los motores no dejan espacio, se quita. Va **atornillado al acrílico** (M3) | Alan, 14 nov (P-V2-29, P-V2-36) |
| D-V2-27 | Orden de atrás hacia adelante (idea de Alan, por validar en AutoCAD): ruedas lo más atrás posible, PCB principal, ventilador, sensores al final; batería junto o encima de los motores, quizá en una mini repisa con separadores | Alan, 14 nov (P-V2-29) |
| D-V2-28 | Corte del acrílico: recortar hacia dentro la zona de los motores y dejarlos **lo más juntos posible** (cable soldado), para ganar espacio | Alan, 14 nov (P-V2-34) |
| D-V2-29 | Las resistencias de 220 Ω de los LED quedan **delante** de los sensores (sin cambiar el esquema) | Alan, 14 nov (P-V2-35) |
| D-V2-30 | Se acepta explorar una capucha para los sensores, que puede ser algo plana; Claude ayuda con el diseño. El diseño sigue abierto | Alan, 14 nov (P-V2-33) |
| D-V2-31 | Un PTC grande es aceptable si su huella es oficial de KiCad | Alan, 14 nov (P-V2-31) |
| D-V2-32 | Un diodo 1N5822 por posición con la separación de patas que Alan dio (~20 mm). La huella oficial más cercana es de 15.24 mm; P-V2-37 autorizado el 15 nov (D-V2-33) | Alan, 14 nov |
| D-V2-33 | **Huella derivada de 20.32 mm para D1 y D2 (1N5822)**, taladro 1.3 mm, autorizada. Sustituye a la oficial de 15.24 mm en la PCB principal. Pendiente de ejecutar: rehacer D1/D2 en `principal.kicad_pcb` y repetir DRC (ver P-V2-37) | Alan, 15 nov (P-V2-37) |
| D-V2-34 | Diodos 1N5822: se compraron **3**; 2 se usan (D1, D2) y **1 queda de recambio** | Alan, 15 nov (P-V2-39) |
| D-V2-35 | Interruptor SW1: el **SW-104S** comprado es el interruptor KCD1 del diseño. Cable 18 AWG: **3 m** (1.5 m rojo + 1.5 m negro) de reserva para conexiones | Alan, 15 nov (P-V2-42, P-V2-43) |
| D-V2-36 | Todo lo pedido a UNIT el 7 nov está recibido | Alan, 15 nov (P-V2-40) |
