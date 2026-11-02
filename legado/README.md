# Legado — diseños históricos (NO vigentes)

Nada de esta carpeta describe el robot que se va a construir. Se conserva como historia de diseño y como evidencia de decisiones pasadas. La arquitectura vigente está en [`docs/ARQUITECTURA.md`](../docs/ARQUITECTURA.md), y sus parámetros, en [`config/robot_maestro.yaml`](../config/robot_maestro.yaml).

| Carpeta | Qué era | Por qué quedó histórico |
|---|---|---|
| `robot_basico/` | Primer robot: carrito con módulos (ESP32, TB6612, GA12-N20, barra de 8 o 24 sensores, L = 100 mm, control PD), su simulador en C++, sus pruebas y documentos (plan, presupuesto, compras, auditoría, guía de instalación) | Descartado el 1 nov 2026 por el pivote a Speed Follower |
| `speed_follower_v1/` | Primera versión del Speed Follower: simulador Python cinemático-cuasiestático, chasis Plan B (L = 130 mm, llanta 34 × 7, apoyo 3Pi), BOM con precios de tiendas, arquitectura y entregable 2 | Reemplazada por el simulador dinámico de la Fase 2 (`sim/`). El cuello de 130 mm no captura la curva R150 y el apoyo 3Pi es pieza de un robot comercial (prohibido, matriz R04). Su controlador C2 sigue vivo en `firmware/logica/` |
| `firmware_esp32_fase3/` | Firmware de la Fase 3 (ESP32 + TB6612 + clon QTR-8A, módulos cableados) y su stub de Arduino para revisar la sintaxis | Reemplazado en la fase final por la PCB-chasis con STM32G431 y su firmware real (`firmware/`) |
| `fase3_modulos/` | Herramientas del diseño de módulos de la Fase 3: verificación eléctrica por CSV (`verificar_electrica.py`, `conexiones.csv`), disposición en planta (`disposicion.py`), suma de presupuesto (`presupuesto.py`) | Sustituidas por el esquemático y la PCB de KiCad 9 (ERC/DRC), el CAD de `hardware/mechanical/cad/` y la BOM final; el presupuesto dejó de ser restricción |

**Advertencias:**
- Los scripts de estas carpetas pueden tener rutas rotas, porque se movieron sin adaptarlos. Para ejecutar algo, hay que consultar el commit anterior a la reorganización (`0143148`).
- `speed_follower_v1/sim/control.py` es la **referencia Python histórica** con la que se generan los vectores dorados del control C2 (`pruebas/sf/generar_dorados.py`). No se debe modificar.
- Los precios, tiendas y existencias de los documentos de compra eran válidos solo en su fecha de consulta.
