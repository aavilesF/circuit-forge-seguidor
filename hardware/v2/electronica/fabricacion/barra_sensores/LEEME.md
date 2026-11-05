# Barra de sensores V2 — paquete de fabricación

| Archivo | Uso |
|---|---|
| `barra_sensores_gerbers.zip` | Lo que se sube al fabricante (cobre, máscara, serigrafía, pasta, contorno, taladros PTH y NPTH) |
| `BOM.csv` | Lista de partes con fabricante y número de parte |
| `CPL_JLCPCB.csv` | Posiciones para ensamble (cara superior e inferior). Revisar rotaciones en la vista previa del fabricante |
| `posiciones_superior.csv`, `posiciones_inferior.csv` | Posiciones tal como las exporta KiCad |
| `barra_sensores_esquematico.pdf`, `barra_sensores_superior.pdf`, `barra_sensores_inferior.pdf` | Revisión y armado a mano |
| `barra_sensores_pcba.step`, `barra_sensores_3d_*.png` | Modelo 3D y vistas |

Placa: 2 capas, FR-4, 1.6 mm, cobre 1 oz, pista/separación mínima 0.15 mm, vía 0.6/0.3 mm, sector R 100-130 mm (90 mm de
ancho). Sensores en la cara **inferior**; el resto en la superior. Regenerar: `hardware/v2/electronica/generar.sh barra`.
