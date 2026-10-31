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

## Estado actual

- Repositorio creado y reglamento analizado (ver `docs/requisitos.md`).
- Microcontrolador: **ESP32** (decidido, D3). El resto de la arquitectura sigue como propuesta sin aprobar (`docs/plan.md`).
- Componentes: **sin comprar** (compra prevista la semana del 2 de noviembre). El sensor (QTR-8A o curvo de 24) sigue sin decidir.
- Firmware: **lógica probada en computadora** (60 pruebas) y **simulador** de la pista. Capa de hardware del ESP32 escrita pero **solo verificada de sintaxis**: no se ha compilado con el SDK real ni probado en la placa.
- Diagramas y guía de armado listos; las medidas de las piezas son nominales hasta tenerlas en la mano.
- Pista de práctica: **por construir**.

## Contenido

| Archivo | Para qué sirve |
|---|---|
| [docs/requisitos.md](docs/requisitos.md) | Restricciones del reglamento y de la convocatoria |
| [docs/presupuesto.md](docs/presupuesto.md) | Lista de compra y presupuesto |
| [docs/decisiones.md](docs/decisiones.md) | Registro de decisiones del equipo |
| [docs/plan.md](docs/plan.md) | Plan de 4 semanas y arquitectura propuesta (aún sin aprobar) |
| [docs/contexto-ia.md](docs/contexto-ia.md) | Resumen del proyecto y prompt de arranque para que cualquier IA o persona parta del mismo contexto |
| [modificaciones/](modificaciones/README.md) | Propuestas de cambio de cada integrante, sin tocar los documentos originales |

| [docs/simulacion.md](docs/simulacion.md) | Modelo virtual, matemáticas explicadas, resultados y límites del simulador |
| [docs/electronica.md](docs/electronica.md) | Reglas eléctricas, pines (`docs/diagramas/pines.md`), batería y sensores |
| [docs/mecanica.md](docs/mecanica.md) | Geometría, velocidades, distribución de peso |
| [docs/armado.md](docs/armado.md) | Guía de armado y pruebas por etapas, con criterios de aprobado |
| `docs/diagramas/` | Diagrama de bloques, cableado, vistas superiores a escala y gráficas de simulación |
| `firmware/seguidor/` | Firmware (ESP32, Arduino IDE o PlatformIO): `pines.h` es la única fuente de los pines |
| `pruebas/` | `ejecutar.sh` (lógica, g++) y `verificar_sintaxis_esp32.sh` (hardware contra un stub) |
| `simulacion/` | Simulador en lazo cerrado que usa el mismo código de control; resultados en `resultados/` |
| `herramientas/generar_diagramas.py` | Regenera diagramas, tabla de pines y gráficas |

### Comandos rápidos

```bash
pruebas/ejecutar.sh                    # pruebas de la lógica
simulacion/ejecutar.sh                 # simulación con los parámetros por defecto
pruebas/verificar_sintaxis_esp32.sh    # sintaxis del código de hardware (no es compilación real)
python3 herramientas/generar_diagramas.py
```

## Forma de trabajo

- Cambios pequeños con commits descriptivos.
- Los cambios propuestos por los integrantes van en `modificaciones/` (ver su README), no directamente en `README.md` ni en `docs/`.
- Toda decisión de hardware o de interfaces se anota en `docs/decisiones.md`.
- Nada se da por terminado sin evidencia (foto, medición o registro de prueba).
