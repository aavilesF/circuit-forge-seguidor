# Notas de la electrónica del robot casero (KiCad)

Rama `engineering/robot-casero`. Dos proyectos independientes:

| Carpeta | Contenido | Estado |
|---|---|---|
| `principal/` | ESP32 + DRV8833 + reguladores + ventilador + botones + medición de batería | Esquemático y PCB listos (medidas provisionales) |
| `barra_sensores/` | 12 × TCRT5000 + multiplexor 74HC4067 + interruptor de emisores | Esquemático y PCB listos (medidas provisionales) |

Los `.kicad_sch` se **generan** con `herramientas/generar_principal.py` y `herramientas/generar_barra.py`
(los pines del ESP32 se leen de `pines_robot_casero.h`). No se editan a mano: se cambia el script y se regenera.

## Cómo verificar (después de cualquier cambio)

```bash
python3 herramientas/generar_principal.py && python3 herramientas/generar_barra.py
python3 herramientas/verificar_esquematico.py principal
python3 herramientas/verificar_esquematico.py barra_sensores
```

## Qué se verificó y qué NO

- **Hecho:** KiCad 7.0.11 abre y exporta la netlist de ambos esquemáticos; las redes coinciden pin por pin con lo que declara el generador; un ERC propio no encuentra pines sueltos, redes de un solo pin, salidas en conflicto ni referencias repetidas. Se comprobó que ese ERC propio sí detecta una etiqueta borrada y una errata.
- **NO hecho:** el **ERC oficial de KiCad**. El `kicad-cli` de KiCad 7 no lo incluye y no se pudo instalar KiCad 8 (descarga bloqueada). Antes de fabricar, abrir cada proyecto en KiCad y correr Inspeccionar > Comprobador de reglas eléctricas (ERC).
- **NO hecho:** ninguna prueba eléctrica real. Un esquemático sin errores no garantiza que funcione.

## Decisiones de diseño

- Barra separada de la placa principal, unida por 8 hilos: +3V3, GND, S0, S1, S2, S3, SIG, EMIT_EN.
- La barra trabaja a **3.3 V** (multiplexor, emisores y resistencias de carga) para que la señal nunca supere el límite del ADC del ESP32.
- Emisores de los 12 sensores: 330 Ω a 3.3 V ≈ 5.6 mA cada uno (≈ 67 mA en total), con un 2N2222 que los apaga y enciende para restar la luz ambiente.
- Motores: segundo MP1584 como reductor fijo de **6 V** (decisión del equipo). Ventilador directo de la batería (VBAT_SW) con MOSFET IRLZ44N y diodo 1N5822.
- D2 (1N5822) entre el MP1584 de 5 V y el pin 5V del ESP32 evita que el USB devuelva corriente al regulador. Cuesta unos 0.3 V: medir el voltaje real en el pin 5V del ESP32 (debe quedar ≥ 4.5 V).
- El driver arranca dormido (nSLEEP con pulldown de 10 kΩ) para que los motores no giren mientras el ESP32 arranca.

## Por verificar con la pieza real (la huella o el símbolo es provisional)

| Pieza | Qué falta |
|---|---|
| ESP32 DevKit 38 pines | Orden de pines de **esa** placa y separación entre las dos filas de pines (mm) |
| Módulo DRV8833 (ya comprado) | Orden y nombres de los pines, largo × ancho y posición de los pines |
| Módulos MP1584 (ya comprados) | Posición de los 4 pads, largo × ancho, altura |
| TCRT5000 (sin comprar) | Posición física de las 4 patas (ánodo, cátodo, colector, emisor) y su separación |
| 74HC4067 (módulo en barrita) | Orden de pines y tamaño (el esquemático usa un símbolo funcional del **módulo**, no el DIP-24) |
| Pulsadores de 4 patas (comprados) | Tamaño y separación de patas |
| Capacitor 470 µF 16 V (comprado) | Diámetro y separación de patas |
| Fusible reseteable | Separación de patas |
| Diodo 1N5822 (comprado) | Separación de patas |
| Transistor PN2222 (comprado) | Orden de pines (E-B-C es el habitual del PN2222A; confirmar en el empaque) |
| Ventilador | Voltaje y corriente. El MOSFET y el fusible de 1.5 A dependen de esto |

## PCB (casera, una cara)

```bash
export KICAD7_FOOTPRINT_DIR=/usr/share/kicad/footprints      # solo para correr en este entorno
python3.12 herramientas/huellas_propias.py                    # crea robot_casero.pretty (medidas provisionales)
python3.12 herramientas/generar_pcb.py barra_sensores         # placa + ruteo + informe DRC
python3.12 herramientas/generar_pcb.py principal
```

- Reglas: pistas 0.8 mm, separación 0.5 mm, pastillas redondas de 1.8 mm, taladro 0.8 mm (la broca del ticket), vía 1.6/0.8 mm.
- **Las pistas de la capa superior (F.Cu) NO se graban: son puentes de alambre** soldados por las pastillas/vías. Se cuentan en `docs/pendientes-por-confirmar.md` (R02).
- El ruteo lo hace un enrutador propio (`ruteador.py`, A* en rejilla de 0.25 mm). No se usó Freerouting: el JAR se descargó pero el entorno bloqueó ejecutarlo.
- El DRC es el **oficial de pcbnew** (`WriteDRCReport`), KiCad 7.0.11. Quedan avisos de serigrafía (texto encima de cobre); no son errores.
- `*_mecanica.json` guarda el contorno y los agujeros M3 de cada PCB: de ahí los toma `mecanica/autocad/generar_dxf.py`.
- Todas las huellas de módulos son provisionales (ver IDs M01 a M20 en `docs/pendientes-por-confirmar.md`).

## Cambios a la lista de compra que salen de este diseño

- Resistencias de 330 Ω: **13** (12 de los LED y 1 de la base del 2N2222), más repuestos.
- Resistencias de 10 kΩ: **14** (12 de carga y 2 en la placa principal), más repuestos.
- Resistencias de 100 Ω: 1. De 100 kΩ: 1. De 33 kΩ: 1. **Ya no se usan** las de 1 kΩ.
- Cerámicos de 100 nF: se usan los 5 comprados (2 en los motores, 1 en la medición de batería, 2 en la barra).
