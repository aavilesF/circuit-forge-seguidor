> **HISTÓRICO (rama anterior `engineering/robot-casero`). No es información vigente de V2.** Inventario, decisiones y pendientes vigentes: `v2/inventario.csv`, `v2/docs/decisiones.md`, `docs/pendientes-por-confirmar.md`. Estado de cada documento: `v2/docs/ESTADO-DOCUMENTOS.md`.

> **HISTÓRICO (11 nov 2026).** Este archivo describe el *plan B*: una sola placa fenólica de una cara, con 8 sensores directos y zumbador.
> Quedó sustituido por las decisiones **D18** (PCB de doble cara), **D19** (sin zumbador) y **D20** (placa de sensores con multiplexor).
> Las PCB vigentes están en `electronica/kicad/` (principal y sensores); la fabricación, en `electronica/kicad/FABRICACION_CASERA.md`.
> Ojo: el firmware (`firmware/robot-casero/`) todavía usa los pines de este archivo hasta que se resuelva **P18**.

# Robot casero · Plan B (prototipo oficial para la competencia)

Decisión del equipo (6 nov 2026): por presupuesto, logística y tiempo (15 días), el robot que compite es el casero. V1 (`main`) y V2 (`engineering/final-robot-v2`) quedan como referencia.

**Material:** solo piezas que ya están en la mesa.

- ESP32 DevKit de 30 pines y módulo DRV8833.
- 2 × MP1584, 1N5822 y 2N2222.
- Botones y el interruptor SW-104S.
- Placa fenólica FEN20X20, cloruro férrico y broca de 0.8 mm.

No hay PCB fabricada ni piezas impresas.

| Entregable | Archivo |
|---|---|
| A. Diagrama de conexiones (y por qué de cada pieza) | [`CONEXIONES.md`](CONEXIONES.md) · [`diagrama_conexiones.pdf`](diagrama_conexiones.pdf) |
| B. Layout de la placa fenólica | [`LAYOUT_PLACA.md`](LAYOUT_PLACA.md) · **[`placa/PLANTILLA_PLACA_1a1.pdf`](placa/PLANTILLA_PLACA_1a1.pdf)** |
| C. Firmware V3 | [`firmware/robot-casero/`](../../firmware/robot-casero/README.md) |
| D. Manual de ensamblaje y pruebas por etapa | [`MANUAL_ENSAMBLAJE.md`](MANUAL_ENSAMBLAJE.md) |
| Generadores (se ejecutan con `python3`) | [`herramientas/placa_principal.py`](herramientas/placa_principal.py) (layout + comprobación) · [`herramientas/diagrama_conexiones.py`](herramientas/diagrama_conexiones.py) |

## Preguntas abiertas (cambian el diseño o el firmware)

1. **Sensores físicos:** QTR-8A, TCRT5000 sueltos (¿cuántos?) o 74HC4067. El firmware sirve para los tres (`config.h`); la barra casera solo hace falta con TCRT5000. **Resuelta el 7 nov (D16):** 12 TCRT5000 sueltos con 74HC4067; falta decidir si van en placa aparte (P15).
2. **FEN20X20:** ¿cobre liso o perforada? El layout sirve para las dos (rejilla de 2.54 mm). **Resuelta el 7 nov (D15):** cobre liso, plancha y taladrado después.
3. **LiPo 2S:** ¿ya la tienen? ¿Qué conector? ¿Y el **fusible**? (fusible: ver P16)
4. **N20:** voltaje y RPM de la etiqueta. Los valores del modelo se ajustan con `set m_R …`.
5. **Resistencias que tienen:** hacen falta 2 × 1 kΩ, 100 kΩ, 33 kΩ, y con TCRT5000 además 8 × 330 Ω y 8 × 10 kΩ.
6. **Zumbador:** ¿activo o pasivo? ¿Hay LED suelto? (ver P14)
7. **MSW-39, MSW-67 y SW-104S:** no aparecen en ningún catálogo consultable. Se supone que son el botón 6×6, el botón 12×12 y el balancín KCD1.

## Diferencias con lo que había en la rama

| Antes (Alan) | Ahora | Motivo |
|---|---|---|
| START en GPIO4 | START en GPIO18; zumbador en GPIO4 | Placa de una cara sin puentes de alambre |
| Pull-down de 10 kΩ en nSLEEP | Sin él | El DRV8833 trae 500 kΩ internos [V TI] |
| D1 en la PCB | D1 en el cable de la batería | Patas de 1.3 mm y broca de 0.8 mm |
| nFAULT sin usar | GPIO15 a través de JP1 (abierto hasta medir) | Detectar fallas del puente sin arriesgar el pin |
| 12 TCRT5000 en arco + 74HC4067 (D05) | 8 directos por defecto; los 12 con mux siguen soportados | Menos piezas y sin multiplexor que comprar. **7 nov: Alan confirmó los 12 con mux (D16); este cambio queda sin efecto y falta actualizar el layout y `config.h` (P15)** |
| Botón RESET en la placa | Botón EN del DevKit | Menos huecos y pistas |
