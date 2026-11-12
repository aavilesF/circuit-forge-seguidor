# KiCad – robot casero

| Carpeta | Qué es | Estado |
|---|---|---|
| `principal/` | ESP32 DevKit **30 pines**, DRV8833, 2 × MP1584, ventilador, botones, medición de batería. PCB 90 × 106 mm, **doble cara**, con hueco para el ventilador 4010 | Ruteada y verificada (estado C); huellas de módulos por confirmar |
| `sensores/` | **Placa de sensores en curva**: 12 × TCRT5000 (montados abajo) + módulo 74HC4067 + interruptor de emisores (2N2222). PCB 94 × 75 mm, **doble cara** | Ruteada y verificada (estado C); huellas TCRT5000/mux por confirmar (M17, M19, M20) |
| `robot_casero.pretty/` | Huellas propias (ESP32 30p, DRV8833, MP1584, diodo de 35.56 mm, TCRT5000, módulo mux, PTC, agujero M3) | Medidas en `docs/especificaciones-componentes.md` |
| `herramientas/` | Generadores (`generar_principal.py`, `generar_sensores.py`, `huellas_propias.py`, `generar_pcb.py`, `ruteador.py`, `exportar_fabricacion.py`) y `verificar_esquematico.py` | — |
| `pines_robot_casero.h` | Única fuente de verdad de los pines del ESP32 | — |

## Regenerar
```bash
python3 herramientas/generar_principal.py && python3 herramientas/generar_sensores.py
python3 herramientas/verificar_esquematico.py principal && python3 herramientas/verificar_esquematico.py sensores
export KICAD7_FOOTPRINT_DIR=/usr/share/kicad/footprints
python3.12 herramientas/huellas_propias.py
python3.12 herramientas/generar_pcb.py principal      # placa + ruteo + DRC (tarda varios minutos)
python3.12 herramientas/generar_pcb.py sensores
python3.12 herramientas/exportar_fabricacion.py principal sensores   # patrón 1:1, perforaciones y puentes
```
Fabricación casera (planchado), reglas y cómo correr ERC/DRC en KiCad 10: ver `FABRICACION_CASERA.md`.

## Pines del ESP32 de 30 pines (todos existen en esa placa)
Mux S0=GPIO25, S1=26, S2=27, S3=33, SIG=34 (ADC1); emisores=13; motores AIN1=19, AIN2=21, BIN1=22, BIN2=23, SLEEP=16;
ventilador=17; START=4, CAL=14; batería=36 (VP, divisor 100k/33k). El 5 V del MP1584 entra por **VIN** a través de D2.

## Módulo DRV8833 comprado
Pines (M10): IN4, IN3, GND, VCC, IN2, IN1 | EEP (=nSLEEP), OUT1, OUT2, OUT3, OUT4, ULT (=nFAULT). VCC = VM (6 V del MP1584 #2).
IN1/IN2 → motor izquierdo (OUT1/OUT2); IN3/IN4 → motor derecho (OUT3/OUT4). **Dejar abierto el puente J1 "sleep–en"** del módulo para que
el ESP32 controle nSLEEP (P08). Datasheet TI: VM 2.7–10.8 V, 1.5 A RMS por puente.

## Reglas de PCB casera (doble cara, D18)
Pistas 0.8 mm, separación 0.5 mm, pastillas de 1.8 mm, vías de 1.8 mm con agujero de 0.8 mm (se rellenan con alambre soldado por
las dos caras: no hay metalizado). Brocas: 0.8 mm (resistencias, sensores, vías), **1.0 mm** (headers, módulos, TO-220, PTC),
**1.3 mm** (1N5822), 3.2 mm (M3) (E08). Las patas que deben soldarse por ARRIBA se listan en `<placa>/fabricacion/<placa>_soldar_arriba.csv`.

## Estado de las PCB (11 nov, V7) — RUTEO COMPLETO
| Placa | Tamaño | Conexiones faltantes | Vías | DRC KiCad 7 | DRC/ERC KiCad 10 (MCP) | Estado |
|---|---|---|---|---|---|---|
| sensores | 94 × 75 mm | 0 | 37 | 0 errores (avisos de serigrafía) | DRC 0 errores; ERC 0 errores (avisos `endpoint_off_grid`) | **C** verificada |
| principal | 90 × 106 mm | 0 | 29 | 0 errores (avisos de serigrafía) | DRC 0 errores; ERC 0 errores (avisos `endpoint_off_grid`, `pin_to_pin`) | **C** verificada |

Estados: A = diseño, B = ruteada, C = verificada (ERC/DRC limpios), D = lista para fabricar. Pasan a **D** cuando se confirmen las huellas
provisionales (M17 pines del mux, M19/M20 TCRT5000, M33 agujeros del MP1584) y se regenere todo con los comandos de arriba.
Colocación de la principal: ESP32 a la derecha con AIN/BIN/START/FAN_PWM/DRV_SLEEP de frente al DRV8833 (girado 180°) y
S0–S3/SIG/EMIT_EN/CAL/EN en la columna que da a J5 y a los botones; así el ruteo cerró sin redes faltantes.

## Verificado / no verificado
- Esquemáticos: netlist de KiCad 7.0.11 + ERC propio, 0 errores. ERC y DRC oficiales de KiCad 10.0.8 corridos por el MCP: 0 errores en ambas placas (JSON en `<placa>/verificacion_kicad10/`).
- PCB: DRC oficial de pcbnew (`*_drc.rpt`). Ver resultado en el commit; avisos de serigrafía no son errores.
- Ruteo con el enrutador propio `ruteador.py` (A* en rejilla de 0.25 mm, dos capas, rip-up and reroute). Freerouting no se pudo ejecutar en el entorno; Alan puede usarlo desde KiCad 10 si quiere mejorar el ruteo.
- Ninguna prueba eléctrica real.
