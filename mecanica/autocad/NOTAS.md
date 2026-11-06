# Placa plana del robot casero (DXF para AutoCAD)

Archivos: `placa_acrilico.dxf`, `placa_mdf.dxf`, `placa_pla.dxf` (milímetros, DXF R2010), `placa_acrilico.png` (vista previa).
Se **generan** con `python3 generar_dxf.py` desde `parametros.yaml`; se comprueban con `python3 verificar_dxf.py`.
Los agujeros de las PCB salen de `electronica/kicad/*/*_mecanica.json` (los escribe `generar_pcb.py`).

## Qué contiene
- Placa de 192 × 95 mm (la caja del reglamento es 200 × 100), esquinas con chaflán de 4 mm, **muescas** para las ruedas.
- Agujeros M3 (3.2 mm) para las dos PCB sobre separadores de 15 mm.
- Hueco de 34 mm y 4 agujeros para el ventilador 4010. El ventilador queda **entre la placa y las PCB** (riesgo R01).
- Ranuras para cinchos: 2 por motor y 2 para la LiPo. Dos agujeros para la rueda loca.
- Capas: CORTE, TALADROS, GRABADO, REFERENCIA (caja del reglamento), COTAS y tres de piezas fantasma
  (arriba = PCB, abajo = motores/batería/rueda loca, entre = ventilador).

## Peso estimado de la placa sola (sin piezas)
Acrílico 3 mm ≈ 58 g · MDF 3 mm ≈ 37 g · PLA macizo 3 mm ≈ 61 g (el relleno de la impresión lo baja). Ver `RESUMEN.md`.

## Qué se verificó
Auditoría de ezdxf sin errores, unidades en mm, todas las capas, polilíneas cerradas, la placa y todo el conjunto dentro de 200 × 100 mm,
agujeros a ≥ 2× el espesor del borde y ≥ 2 mm entre sí, y que las piezas fantasma del mismo nivel no se encimen.
**No se verificó:** ninguna medida real (todas son `nominal`/`pendiente`: ver `docs/pendientes-por-confirmar.md`), ni se abrió en AutoCAD
(se comprobó con ezdxf y vista previa). **No cortar hasta confirmar** C01, C05, M05–M07, M14, M21 y las PCB.

## DWG
`ezdxf` no escribe DWG. En AutoCAD: abrir el DXF y Guardar como DWG.
