# Robot final V2 (alta velocidad y succión) — en desarrollo

Rama `engineering/final-robot-v2`, creada desde `0714c7c` (punta de `engineering/speed-follower`). Las ramas `main`,
`engineering/speed-follower` y `engineering/final-prototype` no se modifican.

| Fase | Contenido | Estado |
|---|---|---|
| **1. Auditoría y física** | [`FASE1_AUDITORIA.md`](FASE1_AUDITORIA.md), [`FASE1_FISICA.md`](FASE1_FISICA.md), [`ANALISIS_VENTILADOR.md`](ANALISIS_VENTILADOR.md); `sim/v2/`, `config/v2/`, `sim/resultados/v2_fase1/` | Aprobada (el reglamento quedó resuelto por los organizadores) |
| **2. Selección de componentes** | [`FASE2_COMPONENTES.md`](FASE2_COMPONENTES.md); `sim/v2/fase2_motores.py`, `config/v2/parametros_fase2.yaml`, `sim/resultados/v2_fase2/` | Entregada; **espera el motor del ventilador y la aprobación** |
| 3. CAD y electrónica (KiCad) | — | No iniciada |
| 4. Firmware, simulación y entregables | — | No iniciada |

Reproducir la Fase 1:

```bash
python3 sim/v2/analisis_obj.py    # medidas de los modelos 3D del ventilador y su montaje
python3 sim/v2/fase1_v2.py        # tablas T1-T9 y gráficas F1-F2 (≈ 10 s)
python3 sim/v2/fase2_motores.py   # Fase 2: motores candidatos (T10) y frecuencia del mando del ventilador (T11)
```

La configuración de V1 (`config/robot_maestro.yaml`, `hardware/`, `firmware/`) sigue intacta en esta rama como referencia;
V2 usará sus propios archivos.
