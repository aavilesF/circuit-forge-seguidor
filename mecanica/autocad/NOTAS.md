# Placa plana en "T" del robot casero (AutoCAD)

Archivos (milímetros, DXF R2010):
- `placa_acrilico.dxf`, `placa_mdf.dxf`, `placa_pla.dxf`: placa 2D para cortar (láser) o imprimir; `placa_*.png` vista previa.
- `robot_3d.dxf`: **modelo 3D del robot armado** (mallas MESH, una capa por pieza). En AutoCAD: abrir, `VISTA` → Isométrica SO y
  estilo visual "Realista" o "Sombreado". `robot_3d.png`: vistas del mismo modelo.
- Generadores: `generar_dxf.py` (2D), `generar_3d.py` (3D), `verificar_dxf.py`; parámetros en `parametros.yaml`.

## Diseño (basado en las fotos de seguidores profesionales que mandó Alan)
- **Base** trasera (105 × 98 mm) con muescas para las ruedas: motores N20 abajo con cinchos, LiPo a lo ancho y ventilador 4010 encima de la
  placa, y la **PCB principal** encima de todo sobre 3 separadores de 18 mm (pasa por encima de las ruedas).
- **Espina** central angosta (30 mm) con la rueda loca abajo.
- **Travesaño** delantero (42 × 96 mm) que sostiene por debajo la **placa de sensores** con 4 separadores de 7 mm: los sensores quedan a
  ~4 mm del piso (antes quedaban a 35 mm, eso ya se corrigió).
- Robot completo: **197 × 96 mm** (límite del reglamento 200 × 100). Placa sola: acrílico 3 mm ≈ 42 g, MDF ≈ 27 g, PLA ≈ 44 g.

## Verificado
Auditoría ezdxf sin errores, mm, capas, polilíneas cerradas, robot completo dentro de 200 × 100, agujeros a ≥ 2× espesor del borde y
≥ 2 mm entre sí y de las ranuras, piezas del mismo nivel sin encimarse. El 3D se abrió con ezdxf (37 mallas, 0 errores de auditoría).
**No verificado:** abrir en AutoCAD; medidas reales con vernier (ver `docs/pendientes-por-confirmar.md`). **No cortar todavía.**

## DWG
ezdxf no escribe DWG: abrir el DXF en AutoCAD y "Guardar como" DWG.
