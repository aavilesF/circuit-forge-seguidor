# KiCad – robot casero

| Carpeta | Qué es | Estado |
|---|---|---|
| `principal/` | ESP32 DevKit **30 pines**, DRV8833, 2 × MP1584, ventilador, botones, medición de batería. PCB 90 × 92 mm | Esquemático y PCB (medidas de escalímetro) |
| `sensores/` | **Placa de sensores en curva**: 12 × TCRT5000 + módulo 74HC4067 + interruptor de emisores (2N2222) | Esquemático y PCB |
| `robot_casero.pretty/` | Huellas propias (ESP32 30p, DRV8833, MP1584, diodo de 35.56 mm, TCRT5000, módulo mux, PTC, agujero M3) | Medidas en `docs/especificaciones-componentes.md` |
| `herramientas/` | Generadores (`generar_principal.py`, `generar_sensores.py`, `huellas_propias.py`, `generar_pcb.py`, `ruteador.py`) y `verificar_esquematico.py` | — |
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

## Reglas de PCB casera
Pistas 0.8 mm, separación 0.5 mm, pastillas de 1.8 mm. Pistas ROJAS (capa superior) = **puentes de alambre** (R02).
Brocas: 0.8 mm para resistencias, **1.0 mm** para headers y TO-220, **1.3 mm** para el 1N5822 (E08).

## Estado de la PCB (6 nov, opción A) — RUTEO INCOMPLETO
- Colocación nueva de las dos PCB sin piezas encimadas (DRC de colocación limpio antes de rutear).
- **El enrutador automático no pudo unir todas las redes:** principal 15 redes distintas sin conectar (44 pastillas, según `principal_drc.rpt`; antes se decía 16) más 1 error de separación, sensores 5 (de 27).
  Las PCB de este commit tienen **errores de DRC `unconnected_items`**: no fabricarlas así.
- Siguiente paso: terminar el ruteo a mano en KiCad 10 (las pistas que faltan se ven como líneas de "ratsnest") o reacomodar piezas.

## Verificado / no verificado
- Esquemáticos: netlist de KiCad 7.0.11 + ERC propio, 0 errores. **ERC oficial no corrido** (E04).
- PCB: DRC oficial de pcbnew (`*_drc.rpt`). Ver resultado en el commit; avisos de serigrafía no son errores.
- Ruteo con enrutador propio (Freerouting bloqueado en el entorno). La placa de sensores conserva el ruteo anterior (no cambió el circuito).
- Ninguna prueba eléctrica real.
