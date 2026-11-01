# Estado del proyecto — Speed Follower

Actualizado: 1 nov 2026 · Rama `engineering/speed-follower` (PR #1, sin fusionar) · Competencia: 21 nov 2026.
**Nada está comprado, construido ni medido.** Todos los resultados de rendimiento son simulados.

## Fases

| Fase | Entregables | Estado |
|---|---|---|
| 1. Reglamento y cálculos | `REGLAMENTO_MATRIZ.md`, `CALCULOS_FISICOS.md` | Hecha. Verificada en `VERIFICACION_FASE1.md` (4 omisiones del modelo cuasiestático) |
| 2. Simulación dinámica | `sim/` + `SIMULACION_DINAMICA.md` §1-4 | Hecha. Arquitectura de referencia: Pololu + barra en arco, 5.76 s |
| **3. Presupuesto de $2,000** | `ARQUITECTURA.md`, `BOM_FINAL.csv`, `AUDITORIA_ROBUSTEZ.md`, `SIMULACION_DINAMICA.md` §5, `CALCULOS_FISICOS.md` §14, `hardware/` | **Hecha en simulación y documentación** |
| 4. Firmware en el MCU | Compilar con el toolchain real del ESP32 | **Pendiente** (bloqueado en el entorno de trabajo) |
| 5. Construcción y medición | Mediciones M1-M8, CAD definitivo, armado, pista de práctica | Pendiente |

## Arquitectura vigente (detalle en `ARQUITECTURA.md`)

Chihai N20 12 V 2200 rpm i10 (×2) · barra clon QTR-8A (8 TCRT5000) · ESP32 DevKit 38 pines · TB6612FNG · LiPo 2S 300-450 mAh · MP1584 · control C3m (v_max 0.66 m/s) · cuello de 110 mm · 132 g [E] · sin IMU, sin succión, sin PCB propia.

| Resultado | Valor | Tipo |
|---|---|---|
| Costo | $1,361 en componentes + $150 de reserva = **$1,511 de $2,000** (máximo permitido $1,846) | Estimado con precios observados el 31 oct; **no son cotizaciones** |
| Vuelta media en 4 pistas sintéticas | **6.35 s, 100 % de éxito (200 salidas, IC 98.1-100 %)** | Simulado |
| Frente a la Fase 2 (mismo procedimiento robusto) | 2-10 % más lenta; la Fase 2 no es presupuestable | Simulado |
| Corriente pico por motor | 0.34 A (driver: 1.0 A) | Simulado / [C] |
| Robustez | 100 % ante batería baja, +2 ms de latencia y errores de montaje de barra, llantas y vía; **falla** con motor más fuerte de lo supuesto, CG adelantado, μ 0.6 o ruido ×3 | Simulado (`AUDITORIA_ROBUSTEZ.md`) |

## Pruebas ejecutadas (`pruebas/ejecutar_todo.sh`: TODO OK)

| # | Prueba | Resultado |
|---|---|---|
| 1 | `config_maestra.h` sincronizada con el YAML | OK |
| 2 | Física del simulador contra soluciones analíticas (8 casos + regresión de latencia) | OK |
| 3 | C2 del simulador = vectores dorados del firmware | 5.7 × 10⁻⁸ |
| 4 | C++ del firmware (ASan/UBSan) = Python histórico (11 pruebas) y = simulador en C2/C3m/C3g/estimar_coord | ≤ 8 × 10⁻⁶ |
| 5 | Sintaxis del firmware contra un stub de Arduino (2 drivers × 2 API de PWM) | OK. **No es compilar para el ESP32** |
| 6 | Pistas sintéticas dentro del reglamento | 4/4 |
| 7 | Verificación eléctrica (pines, ADC1, flash, arranque, VM, bloqueo, frenado, fusible) | 0 fallas, 1 aviso (barra a 5 V → mux a 3.3 V) |
| 8 | Disposición mecánica (caja 192 × 92 mm, choques, CG, masa) | 0 fallas |
| 9 | Presupuesto contra el límite del YAML | OK |

## Pendientes, en orden

| # | Pendiente | Quién | Bloquea |
|---|---|---|---|
| 1 | Confirmar la inscripción (la convocatoria fija el 2 y el 17 nov) y enviar las preguntas de `REGLAMENTO_MATRIZ.md` §5 | Equipo | Participar |
| 2 | Comprar según `BOM_FINAL.csv`, verificando primero las partidas marcadas `verificar = sí` (motores, envío, batería, consumibles) | Equipo | Todo |
| 3 | Decidir motor por calendario: Chihai (19-28 nov mostrado) o respaldo local GA12-N20 6 V | Equipo | Chasis y ajuste |
| 4 | **Compilar** `firmware/sf` con arduino-esp32 3.x en una laptop y guardar la salida | Equipo | Subir el firmware |
| 5 | Mediciones: M1 μ estático y cinético; M2 reparto de peso; M5 masas; **M7 velocidad libre y bloqueo de los motores**; **M8 paso, altura, ruido y pin de emisores de la barra**; M4 R interna | Al recibir piezas | Ajuste final |
| 6 | Con las mediciones: actualizar el YAML → `generar_config_firmware.py` → `python3 sim/fase3.py G` → barrido de v_max → validación de 200 salidas | Simulación | Velocidad de competencia |
| 7 | CAD definitivo con piezas medidas (base: `legado/speed_follower_v1/cad/generar_chasis.py`, con L 110 mm y sin apoyo 3Pi) | Equipo | Imprimir |
| 8 | Esquemático en KiCad de la placa perforada (opcional en esta arquitectura) | — | — |
| 9 | Pista de práctica (fórmica + vinil 2.5 cm) y pruebas físicas | Equipo | Validación real |

## Limitaciones vigentes

- Motores sin ficha técnica: el modelo usa un bloqueo supuesto de 0.5 A y η = 0.79.
- Barra clon sin datos de paso, ruido ni pin de emisores; sin resta de luz ambiente.
- μ y μ cinético supuestos (0.8 y 0.64). El umbral de derrape (0.4 m/s) es una decisión de diseño.
- Pistas sintéticas; el circuito real se conoce el día del evento.
- La búsqueda de parámetros tiene varianza de ≈ ±5 %.

## Evidencia reproducible

| Comando | Salida |
|---|---|
| `pruebas/ejecutar_todo.sh` | Todas las pruebas (≈ 1 min) |
| `python3 sim/experimentos.py A B C D F` | Fase 2 (`sim/resultados/fase2/`; rondas 1 y 2 archivadas como evidencia de los errores corregidos) |
| `python3 sim/fase3.py T G S M P` | Fase 3 (`sim/resultados/fase3/`) |
| `python3 sim/graficas_fase3.py` | Gráficas F1-F4 de la Fase 3 |
| `python3 sim/verificacion_fase1.py` | `fase2/V_verificacion_fase1.csv` |
| `python3 herramientas/presupuesto.py` | Totales de la BOM |
| `python3 hardware/electronics/verificar_electrica.py` · `python3 hardware/mechanical/disposicion.py` | Verificaciones eléctrica y mecánica |

Versiones: Python 3.13.17, numpy 2.5.3, numba 0.68.1, PyYAML 6.0.3, matplotlib 3.11.2, g++ (C++17).
