# circuit-forge-seguidor

Robot seguidor de línea para **Robolympics RMX2026** (Tecnológico de Monterrey, Campus León).
Equipo **Circuit Forge**: diseño, firmware, pruebas y registro de resultados.

## Objetivo

Construir un robot autónomo, ligero y estable que recorra el circuito en el menor tiempo posible sin salirse de la línea. Prioridad del equipo: ganar; mínimo aceptable, completar la pista sin salirse. Se busca un buen equilibrio entre precisión de los sensores y velocidad.

## Competencia

| Dato | Valor |
|---|---|
| Evento | Robolympics RMX2026, categoría Seguidores de línea |
| Fecha | Sábado 21 de noviembre de 2026, 8:00 a 16:00 h |
| Sede | Tec de Monterrey, Campus León |
| Registro | Hasta el 17 de noviembre de 2026, 6:00 pm (confirmación por correo el 18 de noviembre) |
| Donación | Alimentos por $300 MXN por robot, se entregan el 21 de noviembre al registrarse |
| Reglamento | Ver [docs/requisitos.md](docs/requisitos.md) |

Las reglas pueden modificarse a más tardar el 18 de noviembre y se comunican por correo a los equipos registrados.

## Equipo

| Integrante | Rol |
|---|---|
| Alejandro Avilés Flores | Por definir |
| Alan Uzuel Vargas Zavala | Por definir |
| Daniel Navarro Robledo | Por definir |

## Estado actual (31 oct 2026, rama `engineering/final-prototype`)

**Preparación: parcial.** Hay base de ingeniería lista para armar, pero faltan dos decisiones del equipo y la primera compilación real. Detalle en [docs/INFORME_FINAL.md](docs/INFORME_FINAL.md).

- Microcontrolador: **ESP32** (decidido, D3).
- Pendiente de decisión: **alimentación de motores** (checkpoint C2, recomendado: directo de batería con compensación) y **sensor** (recomendado: QTR-8A de UNIT, $61, disponible).
- Firmware: 93 pruebas de lógica, sanitizers y cppcheck sin errores `[Probado en software]`. Código del ESP32 **solo verificado de sintaxis contra un stub**: `[PENDIENTE: compilar con el core real]` (INSTALLATION_GUIDE §6).
- Simulador: 9 escenarios (curvas R 150, U, S, huecos, empujones, fin de línea) × 5 controladores; se eligió PD con freno por error.
- Compras: 8 precios verificados en UNIT Electronics; batería, llantas, apoyo y consumibles **pendientes de cotización** ([docs/BOM_FINAL.csv](docs/BOM_FINAL.csv)).
- Hardware: nada comprado ni medido. Pista de práctica por construir.

## Contenido

| Archivo | Para qué sirve |
|---|---|
| [docs/INFORME_FINAL.md](docs/INFORME_FINAL.md) | **Empieza aquí**: estado, pendientes y siguientes pasos |
| [docs/AUDITORIA.md](docs/AUDITORIA.md) | Hallazgos del repositorio con severidad y evidencia |
| [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md) | Decisiones por bloque con fichas técnicas |
| [docs/C2_ALIMENTACION.md](docs/C2_ALIMENTACION.md) | Análisis del checkpoint C2 (alimentación de motores) para decidir |
| [docs/BOM_FINAL.csv](docs/BOM_FINAL.csv) | Lista de compra (abre en Excel/Sheets) |
| [docs/INSTALLATION_GUIDE.md](docs/INSTALLATION_GUIDE.md) | Qué instalar en la laptop y cómo compilar |
| [docs/PROTOCOLO_PRUEBAS.md](docs/PROTOCOLO_PRUEBAS.md) | Armado, calibración y pruebas físicas con criterios de aprobado |
| [docs/simulacion.md](docs/simulacion.md) | Matemáticas, resultados y límites del simulador |
| [docs/electronica.md](docs/electronica.md) · [docs/mecanica.md](docs/mecanica.md) | Reglas eléctricas, pines, geometría, peso |
| [docs/requisitos.md](docs/requisitos.md) | Reglamento y convocatoria |
| [docs/decisiones.md](docs/decisiones.md) | Registro de decisiones del equipo |
| [docs/presupuesto.md](docs/presupuesto.md) · [docs/plan.md](docs/plan.md) · [docs/armado.md](docs/armado.md) | Históricos (reemplazados por BOM_FINAL, INFORME_FINAL y PROTOCOLO_PRUEBAS) |
| [docs/contexto-ia.md](docs/contexto-ia.md) | Contexto para que cualquier IA o persona parta de lo mismo |
| `docs/diagramas/` | Bloques, cableado, vistas a escala, gráficas de simulación |
| `firmware/seguidor/` | Firmware (Arduino IDE o PlatformIO). `pines.h` es la única fuente de los pines |
| `pruebas/` | `ejecutar.sh`, `regresion.sh`, `verificar_sintaxis_esp32.sh` |
| `sim/` | Simulador en lazo cerrado con el mismo código de control |
| `herramientas/generar_diagramas.py` | Regenera diagramas, tabla de pines y gráficas |
| [modificaciones/](modificaciones/README.md) | Propuestas y registros de pruebas del equipo |

### Comandos rápidos

```bash
pruebas/regresion.sh                   # todo: pruebas, sanitizers, cppcheck, sintaxis, escenarios
sim/ejecutar.sh modo=comparar vbase=0.6 # escenarios × controladores (CSV)
python3 herramientas/generar_diagramas.py
```

## Forma de trabajo

- Cambios pequeños con commits descriptivos.
- Los cambios propuestos por los integrantes van en `modificaciones/` (ver su README), no directamente en `README.md` ni en `docs/`.
- Toda decisión de hardware o de interfaces se anota en `docs/decisiones.md`.
- Nada se da por terminado sin evidencia (foto, medición o registro de prueba).
