# Electrónica — PCB-chasis (KiCad 9)

La placa es el chasis del robot: 4 capas, 130 × 92 mm, con los 16 sensores en la cara inferior. Todo el diseño eléctrico
se **genera** desde una sola fuente (`generador/diseno.py`), así que el esquemático, la PCB, la BOM y los pines del
firmware no pueden divergir.

```
generador/diseno.py ──► esquematico.py ──► kicad/*.kicad_sch ──► netlist (kicad-cli)
        │                                                              │
        ├──► pcb_plan.py ──► plan_pcb.json ◄─────── nombres de red ────┘
        │         │
        │         ├──► pcb_kicad.py construir ──► colocar.py (legaliza cortijos) ──► enrutar.py ──► rutas.json
        │         └──► pcb_kicad.py final + rellenar_zonas.py ──► kicad/speed_follower.kicad_pcb
        ├──► herramientas/generar_bom.py ──► docs/BOM_FINAL.csv, fabricacion/bom_ensamblaje.csv
        └──► herramientas/generar_config_firmware.py ──► firmware/stm32/src/pines_generados.h
```

## Contenido

| Ruta | Qué es |
|---|---|
| `kicad/` | **Proyecto KiCad 9 editable**: `speed_follower.kicad_pro`, esquemático jerárquico (raíz + 5 hojas: alimentación, MCU, motores, sensores, mecánica), `speed_follower.kicad_pcb` ruteada con planos, biblioteca propia `circuitforge.kicad_sym` (QRE1113GR), `sym-lib-table`, `fp-lib-table`, `3d/` (2 modelos aproximados) |
| `generador/` | Scripts que generan todo lo anterior (`diseno.py` partes y redes, `esquematico.py`, `pcb_plan.py`, `pcb_kicad.py`, `colocar.py`, `enrutar.py`, `rellenar_zonas.py`, `modelos3d.py`) y sus datos intermedios |
| `herramientas/` | `kicad.sh` (kicad-cli), `verificar_conectividad.py` (diseño = esquemático = PCB), `resumen_verificacion.py` (filtro de ERC/DRC), `verificar_modelos3d.py`, `calculos_electricos.py`, `ver_colocacion.py` |
| `verificacion/` | Reportes de ERC y DRC (`.rpt` y `.json`), `RESUMEN.md`, `modelos3d.md`, netlist del esquemático, pads de la PCB |
| `fabricacion/` | Paquete para el fabricante: Gerbers, taladros, contorno DXF, pick and place, BOM de ensamblaje, planos de ensamblaje, PDF, STEP. Ver [`fabricacion/LEEME.md`](fabricacion/LEEME.md) |
| `pcba/` | Vistas de la PCBA: 2D superior e inferior (SVG con referencias y cotas) y 3D superior, inferior e isométrica (PNG de 3200 × 2400) |

## Reglas de diseño

Separación 0.15 mm; pistas 0.2 mm (señal), 0.4 mm (+3V3 y lógica del puente H), 0.5 mm (motores), 0.8 mm (batería);
vías 0.55/0.25 mm; cobre al borde 0.3 mm. In1.Cu = GND y In2.Cu = +3V3 completos; rellenos de GND en ambas caras.
El bus PWM del MCU al DRV8833 se traza a mano (4 pistas paralelas, `enrutar.py`, `BUS_PWM`); el resto lo rutea
`enrutar.py` (A* en rejilla de 0.05 mm con separación exacta, árbol de expansión mínima y reparación por arranque).
Corrientes, caídas, disipación y tiempos: [`docs/CALCULOS_ELECTRICOS.md`](../../docs/CALCULOS_ELECTRICOS.md).

## Regenerar y verificar

```bash
hardware/electronics/generar_fabricacion.sh            # esquemático -> PCB -> ERC/DRC/paridad -> conectividad -> paquete
hardware/electronics/generar_fabricacion.sh --enrutar  # además vuelve a colocar y rutear (≈ 10-20 min)
```

El script se detiene **antes** de escribir Gerbers si el ERC o el DRC tienen errores, o avisos que no estén en la lista de
excepciones justificadas de `herramientas/resumen_verificacion.py` (hoy: 2 avisos del ERC por AISEN/BISEN del DRV8833 a
GND, que la hoja de datos indica cuando no se usa la regulación de corriente).

Requisitos: KiCad 9 (`kicad-cli` y el módulo `pcbnew` de su Python) y Python 3 con numpy, numba, scipy, shapely y
matplotlib. En Windows, abrir `kicad/speed_follower.kicad_pro` con KiCad 9 basta para revisar o editar; para regenerar,
usar el "KiCad 9.0 Command Prompt" con `PY_KICAD=python` y Git Bash para el script.

## Estado

ERC, DRC con paridad, conectividad y modelos 3D verificados (`verificacion/RESUMEN.md`, `verificacion/modelos3d.md`).
**Validación EDA, no física**: la placa no se ha fabricado.
