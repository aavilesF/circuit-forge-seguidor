# Paquete de fabricación — PCB-chasis del Speed Follower

Generado por `hardware/electronics/generar_fabricacion.sh` con KiCad 9.0.8 (`kicad-cli`). El script **solo escribe este
paquete si el ERC, el DRC con paridad esquemático-PCB y la comprobación de conectividad pasan sin errores**
(ver `informes/RESUMEN.md`). No editar estos archivos a mano: se regeneran desde `hardware/electronics/generador/`.

## Especificación para el fabricante

| Parámetro | Valor |
|---|---|
| Capas | 4: F.Cu (señales), In1.Cu (plano GND), In2.Cu (plano +3V3), B.Cu (señales + relleno GND) |
| Material y espesor | FR-4 TG155 (o TG150 o superior), 1.6 mm terminado |
| Cobre | 1 oz exteriores, 0.5 oz interiores |
| Dimensiones | 130 × 92 mm, contorno fresado con arco frontal R116 y agujero de Ø 6.4 mm para la bola |
| Pista / separación mínimas | 0.20 / 0.15 mm |
| Vía mínima | 0.55 mm de diámetro, taladro 0.25 mm (vías propias); **taladro de 0.20 mm** en las 12 vías térmicas de la huella oficial del DRV8833 (U3) |
| Acabado | ENIG (pads de paso 0.5 mm del STM32 y almohadilla térmica del DRV8833) |
| Máscara / serigrafía | Máscara **negra** (menos reflejo junto a los sensores de la cara inferior); serigrafía blanca en ambas caras |
| Vías | Sin tapar (no se pidió *tenting*); la serigrafía no pasa sobre vías |
| Componentes | **Ambas caras**: inferior = 16 sensores QRE1113GR, 32 resistencias de los sensores, C20-C23, R4 y C3 |

## Archivos

| Archivo | Contenido |
|---|---|
| `speed_follower_gerbers.zip` | Todo `gerber/` en un zip para subir al fabricante |
| `gerber/*.gbr` | Gerber X2: F/In1/In2/B Cu, máscaras, pasta, serigrafía, Edge.Cuts; `speed_follower-job.gbrjob` |
| `gerber/*-PTH.drl`, `*-NPTH.drl` | Taladros Excellon (mm), metalizados y no metalizados por separado; mapas en PDF y reporte `speed_follower-taladros.rpt` |
| `contorno_pcb.dxf` | Contorno (Edge.Cuts) en mm |
| `bom_ensamblaje.csv` | BOM de ensamblaje agrupada por valor, huella y cara (referencias, fabricante, número de parte) |
| `posiciones_superior.csv`, `posiciones_inferior.csv` | Pick and place (mm, grados) por cara |
| `speed_follower.ipc` | Netlist IPC-D-356 para la prueba eléctrica de la placa desnuda |
| `ensamblaje_superior.pdf`, `ensamblaje_inferior.pdf` | Planos de ensamblaje (capa Fab con referencias y contornos de pads; la inferior en espejo) |
| `esquematico.pdf` | Esquemático completo (5 hojas) |
| `pcb_capas.pdf` | Las 4 capas de cobre y las serigrafías, una por página |
| `speed_follower_pcba.step` | PCBA en 3D: placa, pads y componentes (modelos oficiales de KiCad 9; XT30 y PTC aproximados, ver `informes/modelos3d.md`) |
| `bom_compra.csv` | Copia de `docs/BOM_FINAL.csv` (lista de compra completa del robot) |
| `informes/` | `erc.rpt`, `drc.rpt`, `RESUMEN.md` (excepciones justificadas) y `modelos3d.md` |

**Origen de coordenadas** de taladros, gerbers y pick and place: el **centro del eje de las ruedas** (origen auxiliar de la
placa en (100, 100) mm de KiCad). Eje x hacia el frente del robot. Los servicios de ensamblaje suelen pedir revisar la
rotación de algunos encapsulados en su vista previa: verificar pin 1 del STM32 (U1), del DRV8833 (U3), del TPS563200 (U2)
y la orientación de los 16 QRE1113GR contra `ensamblaje_inferior.pdf` antes de aprobar.

## Piezas que se sueldan a mano (orificio pasante)

J1 (XT30UPB-M — **revisar el género contra la batería antes de soldar**), J4 (Harwin M50-3500742) y SW1 (OS102011MA1QN1,
el actuador sobresale 2 mm del borde derecho a propósito).

## Estado

Verificación CAD/EDA completa (`informes/RESUMEN.md`). **No hay placa fabricada ni probada**: las pruebas E1-E9 están en
`docs/MANUAL_ENSAMBLAJE.md`.
