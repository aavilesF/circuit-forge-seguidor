# Estado del proyecto — Speed Follower

Actualizado: 1 nov 2026 · Rama `engineering/speed-follower` · Competencia: 21 nov 2026.

## Fases

| Fase | Entregables | Estado |
|---|---|---|
| 1. Reglamento y cálculos físicos | `docs/REGLAMENTO_MATRIZ.md`, `docs/CALCULOS_FISICOS.md`, `config/robot_maestro.yaml`, `sim/fase1/` | **Hecho** (cálculo; sin mediciones) |
| 2. Simulador con control y escenarios | `sim/` con CSV de tiempo, velocidades, % de vueltas completadas, causas de falla y sensibilidad | Pendiente |
| 3. Selección de MCU, driver, motor y BOM | `docs/BOM_FINAL.csv` (reemplaza la del robot básico) | Pendiente: depende de la succión (consulta a organizadores + medición M3) |
| 4. Firmware | `firmware/` modular + `.ino`, compilado con el toolchain real | Pendiente. Sin compilación real hasta ahora (auditoría H07) |
| 5. Electrónica | `hardware/electronics/` KiCad con ERC/DRC, Gerbers y 3D | Pendiente |
| 6. Mecánica | `hardware/mechanical/` STL/STEP y planos | Pendiente |
| 7. Auditoría de robustez | `docs/AUDITORIA_ROBUSTEZ.md` | Pendiente |

## Decisiones vigentes después de la Fase 1

| Decisión | Valor | Base | Estado |
|---|---|---|---|
| Cuello | L = 100 mm | CALCULOS §5: límite de captura de la barra en arco en R150 | Propuesta (se confirma con el simulador de la Fase 2) |
| Barra | En arco, radio 100 mm, cuerda 92 mm, 13-16 sensores | CALCULOS §5 | Propuesta |
| Periodo de control | ≤ 1 ms | CALCULOS §9 | Requisito |
| Batería | LiPo 2S; 3S prohibida con DRV8833 | CALCULOS §8 | Vigente |
| Apoyo delantero | Rueda loca genérica o patín propio, **no** el apoyo 3Pi | REGLAMENTO R04 | Vigente |
| Reparto de peso | Batería sobre el eje; objetivo f_motriz ≥ 0.75 | CALCULOS §6 | Requisito |
| Succión | Prevista en el chasis; se adopta solo con permiso escrito de los organizadores y succión medida > 22 gf | CALCULOS §6; REGLAMENTO pregunta 1 | Abierta |
| Motor | 12 V 15:1 sin succión; reevaluar (6 V 15:1 con límite de corriente) si hay succión | CALCULOS §6-7 | Abierta |

## Qué se conserva y qué queda obsoleto

| Elemento | Situación |
|---|---|
| `firmware/seguidor/`, `sim/simular.cpp`, `sim/ejecutar.sh`, `sim/resultados/` (raíz), `pruebas/` (raíz), `herramientas/`, `docs/ARQUITECTURA.md`, `docs/BOM_FINAL.csv`, `docs/PLAN_PRIMERA_COMPRA.md`, `docs/C2_ALIMENTACION.md`, `docs/INFORME_FINAL.md`, `docs/armado.md`, `docs/mecanica.md`, `docs/electronica.md`, `docs/presupuesto.md` | **Obsoleto**: robot básico descartado. Se moverá a `legado/` al reestructurar la Fase 2 |
| `docs/requisitos.md` | Sustituido por `docs/REGLAMENTO_MATRIZ.md` |
| `speed-follower/sim/` (modelo y control C2) | Útil: base del simulador de la Fase 2. Debe leer `config/robot_maestro.yaml` y corregir los hallazgos H04, H09, H11 y H12 de la auditoría |
| `speed-follower/firmware/sf/` (control C2 en C++ verificado contra Python) | Útil: base del firmware de la Fase 4 |
| `speed-follower/cad/generar_chasis.py` | Útil como generador, pero la geometría queda obsoleta (L = 130 mm, apoyo 3Pi, cuna que choca: H02) |
| `docs/speed-follower/ARQUITECTURA_SF.md`, `ENTREGABLE_2.md`, `BOM_SF.csv` | Historia de diseño. Las cifras de velocidad y el cuello de 130 mm quedan reemplazados por CALCULOS_FISICOS |

## Pendientes urgentes (fuera del repositorio)

1. **Registro:** la convocatoria fija el **2 nov** en un punto y el 17 nov en otro. Confirmar la inscripción ya.
2. Enviar las 5 preguntas de REGLAMENTO_MATRIZ §5 a camilo.duque@tec.mx.
3. Mediciones M1-M6 (CALCULOS §13) en cuanto haya llanta y un trozo de fórmica.

## Evidencia reproducible

| Comando | Resultado | Fecha |
|---|---|---|
| `python3 sim/fase1/calculos_fisicos.py` | 11 CSV (C0-C10) y 5 PNG (F0-F4) en `sim/resultados/fase1/`; 4/4 pistas cumplen el reglamento | 1 nov 2026 |

Versiones: Python 3.13.17, numpy 2.5.3, pandas 3.0.5, PyYAML 6.0.3, matplotlib 3.11.2.
