# Robot casero (ESP32, PCB casera, soldadura a mano)

Rama `engineering/robot-casero`. Versión del robot pensada para construirse con lo que el equipo tiene a su alcance:
PCB casera, soldadura a mano (orificio pasante), ESP32, motorreductores N20 sin encoder, puente H, ventilador y LiPo.
Presupuesto objetivo: 1,500–1,800 MXN incluyendo la batería.

La versión avanzada (STM32, encoders, SMD, sensores de presión) vive en la rama `engineering/final-robot-v2` y **no**
es la que se va a construir.

## Contenido

| Archivo | Para qué sirve |
|---|---|
| [materiales/CHECKLIST.md](materiales/CHECKLIST.md) | Lista de compra con casillas: qué está comprado y qué falta |
| [materiales/BOM.csv](materiales/BOM.csv) | Mismos materiales en tabla (cantidad, especificación, estado, precio) |

## Decisiones tomadas

- Microcontrolador: ESP32 DevKit de 30 pines (ya lo tienen). WiFi y Bluetooth **no se inicializan** (el reglamento prohíbe comunicación inalámbrica).
- Motores: GA12-N20 6 V 1000 RPM sin encoder, con llanta de 34 × 7 mm.
- Driver: módulo DRV8833. Alimentación directa de la LiPo 2S con el PWM limitado a ~6 V efectivos.
- Sensores: 12 × TCRT5000 (orificio pasante) en PCB propia, paso de 7.5 mm (~88 mm de ancho), multiplexor 74HC4067 en la misma placa de sensores (arco de 110 mm de radio).
- Resta de luz ambiente: los emisores se encienden y apagan con un 2N2222 y se resta la lectura.
- Ventilador: DC con escobillas, mando con MOSFET de nivel lógico (IRLZ44N) y diodo Schottky. Se deja para el final; el robot debe funcionar sin él.
- Calibración: manual (el reglamento prohíbe que el robot se mueva antes de la señal del referee).

## Pendientes

1. Confirmar con la organización (camilo.duque@tec.mx) si el chasis impreso en un servicio de la universidad cuenta como construido por el equipo.
2. Conseguir llantas N20 de 34 × 7 mm (agotadas en UNIT al 31 de octubre).
3. Diseñar el ventilador (rotor y faldón que nunca toque la pista) y elegir su motor.
4. Releer el reglamento el 18 de noviembre.


> Estado vigente: `docs/decisiones-robot-casero.md`, `docs/especificaciones-componentes.md`, `docs/pendientes-por-confirmar.md` y `docs/faltantes-unit.md`.
