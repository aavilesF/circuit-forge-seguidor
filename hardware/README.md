# Hardware — Speed Follower (configuración definitiva)

| Carpeta | Contenido | Detalle |
|---|---|---|
| [`electronics/`](electronics/README.md) | Proyecto KiCad 9 (esquemático jerárquico y PCB-chasis de 4 capas ruteada), generadores, verificaciones ERC/DRC/paridad, paquete de fabricación y vistas 2D/3D de la PCBA | [`electronics/README.md`](electronics/README.md), [`electronics/fabricacion/LEEME.md`](electronics/fabricacion/LEEME.md) |
| [`mechanical/`](mechanical/README.md) | CAD del robot completo (CadQuery): piezas impresas en STEP/STL, planos, ensamble STEP, vistas, verificación de interferencias, caja, altura, masa y CG | [`mechanical/README.md`](mechanical/README.md), [`mechanical/VERIFICACION_MECANICA.md`](mechanical/VERIFICACION_MECANICA.md) |
| `geometria.py` | Geometría única del robot (contorno de la PCB, arco y posición de los sensores, soportes, rueda loca, alturas) calculada desde `config/robot_maestro.yaml`; la usan la PCB, el CAD y las verificaciones | — |

Arquitectura y justificación: [`docs/ARQUITECTURA.md`](../docs/ARQUITECTURA.md). Lista de compra: [`docs/BOM_FINAL.csv`](../docs/BOM_FINAL.csv).
Montaje, pruebas de aceptación y calibración: [`docs/MANUAL_ENSAMBLAJE.md`](../docs/MANUAL_ENSAMBLAJE.md).

Todo lo que contiene esta carpeta está verificado en **EDA y CAD**; no hay placa ni robot fabricados.
