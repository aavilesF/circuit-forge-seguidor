# circuit-forge-seguidor

Speed Follower (seguidor de línea de velocidad) del equipo **Circuit Forge** para **Robolympics RMX2026**, categoría Seguidores de línea: sábado 21 de noviembre de 2026, Tec de Monterrey campus León.

> **Una sola arquitectura vigente:** la de [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md), con todos sus parámetros en [`config/robot_maestro.yaml`](config/robot_maestro.yaml). Todo lo que está en [`legado/`](legado/README.md) es **histórico** (el robot básico descartado y la primera versión del Speed Follower) y no se debe usar para construir.

## Estado

Ver [`docs/ESTADO_PROYECTO.md`](docs/ESTADO_PROYECTO.md). Resumen: arquitectura de **$2,000 MXN** (Fase 3: Chihai N20 12 V + clon QTR-8A + ESP32 + TB6612), con un costo estimado de $1,511 con reserva. Simulada: 6.35 s por vuelta y 100 % de éxito en 200 salidas. Nada se ha comprado, construido ni medido; el firmware **no** se ha compilado con el toolchain real del ESP32; el CAD definitivo espera las piezas medidas.

## Estructura

| Ruta | Contenido |
|---|---|
| `config/robot_maestro.yaml` | **Única fuente de parámetros** (reglamento, componentes con posición y masa, motores, barra, MCU, control). Cada valor indica su origen |
| `docs/REGLAMENTO_MATRIZ.md` | Reglas oficiales → requisitos de diseño → verificación; preguntas a los organizadores |
| `docs/ARQUITECTURA.md` | Arquitectura vigente y su justificación con resultados de simulación |
| `docs/SIMULACION_DINAMICA.md` | Modelo, pruebas, resultados (Fase 2 y Fase 3) y límites del simulador |
| `docs/AUDITORIA_ROBUSTEZ.md` | Escenarios desfavorables de la arquitectura vigente |
| `docs/VERIFICACION_FASE1.md` | Verificación independiente de los cálculos de la Fase 1 |
| `docs/CALCULOS_FISICOS.md` | Fase 1 (cálculos cuasiestáticos; evidencia histórica, ver su nota de estado) |
| `docs/BOM_FINAL.csv` | Lista de materiales con especificaciones y presupuesto (objetivo, estimado y máximo permitido; no son cotizaciones) |
| `hardware/` | Conexiones y verificación eléctrica; disposición mecánica (no es CAD definitivo) |
| `docs/ESTADO_PROYECTO.md` | Fases, decisiones, limitaciones, pendientes y evidencia reproducible |
| `sim/` | Simulador dinámico (`nucleo.py`, `simulador.py`, `config.py`, `pistas.py`), experimentos, validación y pruebas; `sim/fase1/` cálculos de la Fase 1; `sim/resultados/` CSV y gráficas |
| `firmware/sf/` | Firmware (lógica C++ pura + capa de hardware ESP32 + `sf.ino`). `config_maestra.h` se **genera** del YAML |
| `herramientas/generar_config_firmware.py` | Genera `config_maestra.h`; `--verificar` falla si no está sincronizada |
| `pruebas/` | `ejecutar_todo.sh` corre todas las pruebas; `pruebas/sf/` pruebas del firmware |
| `legado/` | Diseños históricos (no vigentes) |
| `modificaciones/` | Plantilla para registrar cambios hechos en el robot físico |

## Reproducir

```bash
pip install numpy numba pyyaml matplotlib      # Python ≥ 3.10; g++ con C++17
pruebas/ejecutar_todo.sh                       # todas las pruebas (≈ 1 min)
python3 sim/fase3.py T G S M P                 # Fase 3: candidatos, ajuste final, sensibilidad, escenarios
python3 sim/graficas_fase3.py                  # gráficas de la Fase 3
python3 herramientas/presupuesto.py            # costo de la BOM contra $2,000
python3 sim/verificacion_fase1.py              # verificación de la Fase 1
python3 herramientas/generar_config_firmware.py  # tras editar el YAML
```

## Equipo

Alejandro Avilés Flores · Alan Uzuel Vargas Zavala · Daniel Navarro Robledo. Contacto de la organización: camilo.duque@tec.mx.
