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

**Nota sobre "caja":** el reglamento limita el robot completo a **200 × 100 mm** de planta (largo × ancho). En los dibujos ese límite aparece
como un rectángulo gris llamado "límite de tamaño del reglamento". No es una caja física ni el chasis.

**Archivos fuera del alcance:** `docs/plan.md`, `docs/electronica.md`, `docs/armado.md`, `firmware/` y `simulacion/` son del robot avanzado
anterior (rama original). No se actualizan aquí; el firmware del robot casero queda pendiente de adaptar a estos pines y al DRV8833.
