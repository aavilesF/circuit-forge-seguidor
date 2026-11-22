> **HISTÓRICO (rama anterior `engineering/robot-casero`). No es información vigente de V2.** Inventario, decisiones y pendientes vigentes: `v2/inventario.csv`, `v2/docs/decisiones.md`, `docs/pendientes-por-confirmar.md`. Estado de cada documento: `v2/docs/ESTADO-DOCUMENTOS.md`.

# Decisiones tomadas (robot casero)

Registro de lo que **ya se decidió**. Si algo de aquí aparece en otro archivo como "pendiente", ese archivo está desactualizado.
Rama `engineering/robot-casero`.

| ID | Fecha | Decisión | Quién | Dónde se refleja |
|---|---|---|---|---|
| D01 | 31 oct 2026 | Robot casero dentro de 1,500–1,800 MXN con la LiPo; PCB hecha a mano y soldadura de orificio pasante | Alan | `faltantes-unit.md` |
| D02 | 31 oct 2026 | ESP32, motorreductores N20 sin encoder, driver DRV8833, ventilador, LiPo 2S | Alan | Esquemático principal |
| D03 | 5 nov 2026 | ESP32 DevKit de **30 pines** (clon USB-C que ya tienen), no el de 38 | Alan | Símbolo y huella `ESP32_DevKit_30` |
| D04 | 5 nov 2026 | Segundo MP1584 como reductor de 6 V para los motores | Alan | Esquemático principal |
| D05 | 5 nov 2026 | **No se usa barra comercial (QTR-8).** 12 sensores TCRT5000 sueltos en arco (radio 110 mm, 7.5 mm entre sensores) en una **placa de sensores** propia, leídos con un multiplexor 74HC4067 en módulo | Alan | `electronica/kicad/sensores/` |
| D06 | 5 nov 2026 | Chasis = **placa plana**, no una caja. Forma de "T" como los seguidores profesionales: motores atrás, espina al centro, travesaño al frente que sostiene la placa de sensores muy cerca del piso | Alan (fotos de referencia) | `mecanica/autocad/` |
| D07 | 5 nov 2026 | Material del chasis: acrílico, MDF o impresión 3D (se elige después); hay DXF de los tres | Alan | `mecanica/autocad/placa_*.dxf` |
| D08 | 5 nov 2026 | **Ventilador permitido** (confirmado con expertos y participantes de competencias anteriores). Ya no está pendiente | Alan | este archivo |
| D09 | 5 nov 2026 | Ruedas: las que Alan ya tiene (rin de aluminio + llanta de goma ∅28 mm). Ya no se compran llantas | Alan | `faltantes-unit.md` |
| D10 | 5 nov 2026 | Medidas con escalímetro como valores de trabajo; se confirmarán con vernier | Alan | `especificaciones-componentes.md` |
| D11 | 6 nov 2026 | **Nunca se borran IDs** de pendientes; se guardan versiones anteriores en `docs/historial/` | Alan | skill `mantenimiento-repositorio` |
| D12 | 6 nov 2026 | El chasis debe ser una sola base de acrílico, compacta, sin segundo piso; ruedas más adelante (la opción concreta se elige en P12) | Alan | `opciones-diseno.md` |
| D13 | 6 nov 2026 | Motores sujetos con aseguradores de plástico (M31) | Alan | DXF |
| D14 | 6 nov 2026 | El puente J1 del DRV8833 se deja sin soldar (P08) | Alan (foto) + datasheet | NOTAS de KiCad |
| D15 | 7 nov 2026 | Placa fenólica FEN20X20 de **cobre liso** (sin perforar). El diseño se transfiere con **plancha** (tóner) y los agujeros se taladran después del ataque | Alan | `docs/robot-casero/LAYOUT_PLACA.md` (el orden de taladrado y plancha del manual ya lo cubre; pregunta abierta 2 del README resuelta) |
| D16 | 7 nov 2026 | Sensores: **12 TCRT5000 sueltos** en arco, soldados a la placa, con multiplexor 74HC4067 para ahorrar pines. Confirma D05 y sustituye el "8 directos por defecto" del plan B | Alan | Reflejado en D20 (11 nov): placa de sensores con multiplexor. Falta `config.h` (P18) |
| D17 | 7 nov 2026 | Medidas: si una pieza trae dibujo o datasheet con sus dimensiones, esa medida vale y no se mide con vernier (V01, M09) | Alan | `pendientes-por-confirmar.md` |
| D18 | 11 nov 2026 | Las PCB (principal y sensores) son de **doble cara**: una sola placa fenólica con cobre arriba y abajo, grabadas por planchado. Vías = agujero con alambre soldado en las dos caras (sin metalizado) | Alan | `electronica/kicad/` (ruteador, exportador, `FABRICACION_CASERA.md`); E09; R02 resuelto |
| D19 | 11 nov 2026 | **Sin zumbador** (buzzer): no se necesita y ocupa espacio | Alan | P14; la PCB no lo tiene; falta el firmware (P18) |
| D20 | 11 nov 2026 | Multiplexor 74HC4067, 12 TCRT5000 e interruptor de emisores (Q1) en la **placa de sensores**; a la principal van 8 hilos (+3V3, GND, S0–S3, SIG, EMIT_EN) | Alan | P15; `generar_sensores.py`, `generar_principal.py` |
| D21 | 11 nov 2026 | Diodos 1N5822 con **~20 mm** entre patas (huella de 20.32 mm) | Alan | M24; huella `D_DO-201AD_P20.32mm_Taladro1.3` |
| D22 | 11 nov 2026 | Diseño mecánico: **opción A**, todo en una sola placa de acrílico sin niveles (ahorrar espacio y peso) | Alan | P12; `mecanica/autocad/` |
| D23 | 11 nov 2026 | Rueda loca: **Mini rueda universal 3Pi N20** de UNIT (ya comprada); medidas de la ficha como verdaderas. El patín de nailon (O02) queda descartado | Alan | M30, P17; `parametros.yaml`; R03 |
| D24 | 11 nov 2026 | Protección de la batería con **fusible reseteable** (PTC); la pieza exacta queda en M28 con huella provisional | Alan | P16, M28; F1 |

**Nota sobre "caja":** el reglamento limita el robot completo a **200 × 100 mm** de planta (largo × ancho). En los dibujos ese límite aparece
como un rectángulo gris llamado "límite de tamaño del reglamento". No es una caja física ni el chasis.

**Archivos fuera del alcance:** `docs/plan.md`, `docs/electronica.md`, `docs/armado.md`, `firmware/` y `simulacion/` son del robot avanzado
anterior (rama original). No se actualizan aquí; el firmware del robot casero queda pendiente de adaptar a estos pines y al DRV8833.
