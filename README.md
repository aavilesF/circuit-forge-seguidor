# circuit-forge-seguidor

Speed Follower (seguidor de línea de velocidad) del equipo **Circuit Forge** para **Robolympics RMX2026**, categoría Seguidores de línea: sábado 21 de noviembre de 2026, Tec de Monterrey campus León.

> **Una sola arquitectura vigente:** la de [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md), con todos sus parámetros en [`config/robot_maestro.yaml`](config/robot_maestro.yaml). Todo lo que está en [`legado/`](legado/README.md) es **histórico** (el robot básico descartado y la primera versión del Speed Follower) y no se debe usar para construir.

## Estado

Ver [`docs/ESTADO_PROYECTO.md`](docs/ESTADO_PROYECTO.md). Resumen: arquitectura elegida con **simulación dinámica** (Fase 2); nada se ha construido ni medido; la PCB y el CAD definitivo **no** se han empezado; el firmware **no** se ha compilado con el toolchain real del microcontrolador.

## Estructura

| Ruta | Contenido |
|---|---|
| `config/robot_maestro.yaml` | **Única fuente de parámetros** (reglamento, componentes con posición y masa, motores, barra, MCU, control). Cada valor indica su origen |
| `docs/REGLAMENTO_MATRIZ.md` | Reglas oficiales → requisitos de diseño → verificación; preguntas a los organizadores |
| `docs/ARQUITECTURA.md` | Arquitectura vigente y su justificación con resultados de simulación |
| `docs/SIMULACION_DINAMICA.md` | Modelo, pruebas, resultados, límites del simulador |
| `docs/VERIFICACION_FASE1.md` | Verificación independiente de los cálculos de la Fase 1 |
| `docs/CALCULOS_FISICOS.md` | Fase 1 (cálculos cuasiestáticos; evidencia histórica, ver su nota de estado) |
| `docs/BOM_FINAL.csv` | Lista de materiales técnica: especificaciones, sin precios, tiendas ni enlaces |
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
python3 sim/experimentos.py A B C D F          # optimización completa (≈ 1 h en 2 núcleos)
python3 sim/validacion_final.py                # validación de la arquitectura vigente
python3 sim/verificacion_fase1.py              # verificación de la Fase 1
python3 herramientas/generar_config_firmware.py  # tras editar el YAML
```

## Equipo

Alejandro Avilés Flores · Alan Uzuel Vargas Zavala · Daniel Navarro Robledo. Contacto de la organización: camilo.duque@tec.mx.
