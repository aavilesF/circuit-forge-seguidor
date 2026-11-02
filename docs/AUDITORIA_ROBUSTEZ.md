# Auditoría de robustez — configuración definitiva

Fecha: 2 nov 2026. **Todo es simulado** (`python3 sim/fase_final.py Z R E S F G`, resultados en `sim/resultados/final/`).
Nada se ha medido en hardware. La versión de la Fase 3 (Chihai + barra clon + ESP32) está en el historial de git
(commit `033b641`).

Configuración: Pololu #3048 HPCB 12 V 10:1 + 16 × QRE1113GR en arco (resta de luz ambiente) + STM32G431 + DRV8833,
cuello de 110 mm, masas y CG del CAD (113.0 g, x_CG 20.1 mm), control **C3m v_max 0.8165 m/s** (competencia) y **C3e
v_max 0.6327 m/s** (modo seguro). En cada escenario el firmware conserva sus parámetros nominales; lo que cambia es el
robot real (la planta). Cada salida tiene la dispersión normal (μ ± 10 %, batería 7.6-8.3 V, motores ± 5 %, colocación
± 3 mm y ± 2°). IC = intervalo de Wilson al 95 %.

**Criterio de aceptación:** ≥ 99 % de vueltas completas, porque un intento perdido vale 5 minutos.

## 1. Datos del motor que el fabricante no publica (etapas R y E)

Pololu publica velocidad libre, corriente de bloqueo, par y relación; **no publica la inercia del rotor** (J_rotor, [S]).
Para el motor elegido (`R_sensibilidad_motores.csv`, con el ajuste de la etapa Z):

| Caso | Éxito | t medio |
|---|---|---|
| Nominal | 100 % | 5.39 s |
| J_rotor × 0.5 | 90.0 % | 5.44 s |
| J_rotor × 2 | 100 % | 5.45 s |
| μ 0.70 | 97.5 % | 5.43 s |
| I de bloqueo 0.60 A / 0.90 A | 100 % / 100 % | 5.42 / 5.37 s |

Ese ajuste (v_max 0.892) no cumple el criterio con J_rotor × 0.5, por eso el control final se eligió por el tiempo esperado
**medio** sobre 6 plantas (`E_eleccion.json`): C3m con v_max 0.8165 m/s queda en 98.3 % en el peor caso (J_rotor × 0.5) y
100 % en las otras 5; el modo seguro C3e queda en 100 % en las 6.

## 2. Validación del control de competencia con las masas del CAD (etapa F, `F_validacion_robustez.csv`)

| Escenario | Salidas | Éxito (IC 95 %) | t medio | I máx por motor |
|---|---|---|---|---|
| Nominal | 200 | **100 %** (98.1-100) | **5.81 s** | 0.48 A |
| μ 0.70 / 0.60 | 120 / 120 | 100 % / 100 % | 5.83 / 5.85 s | 0.47 A |
| **CG 10 mm más adelante** | 120 | **80.0 %** (72.0-86.2), 24 derrapes | 6.13 s | 0.48 A |
| CG 10 mm más atrás | 120 | 100 % | 5.74 s | 0.47 A |
| Masa + 10 g (batería de 37 g) / + 40 g | 120 / 120 | 100 % / 100 % | 5.86 / 5.98 s | 0.47 A |
| Sensores más altos (mancha × 1.6) | 120 | 100 % | 5.80 s | 0.48 A |
| Ruido de sensores × 2 / × 3 | 120 / 120 | 100 % / 100 % | 5.73 / 5.55 s | 0.51 A |
| Fototransistor lento (t_emisor 400 µs) | 120 | 100 % | 5.82 s | 0.48 A |
| Encoder desconectado | 120 | 100 % | 5.82 s | 0.47 A |
| Batería baja (6.9 V) | 120 | 100 % | 5.83 s | 0.39 A |
| Latencia + 1 ms | 120 | 100 % | 5.82 s | 0.48 A |
| Motores desparejos ± 10 % | 120 | 100 % | 5.92 s | 0.48 A |
| I de bloqueo × 0.8 / × 1.2 | 120 / 120 | 100 % / 100 % | 5.83 / 5.80 s | 0.38 / 0.56 A |

Corriente máxima por motor 0.56 A (DRV8833: 1.5 A RMS por canal). Que el ruido × 3 dé un tiempo menor no se toma como
una mejora: sale del modelo de ruido supuesto ([S]) y se revisa con la medición M8.

## 3. Modo seguro y tolerancia del CG (etapa G, `G_modo_seguro.csv`)

| Escenario | Salidas | Éxito (IC 95 %) | t medio |
|---|---|---|---|
| C3e (modo seguro) nominal | 200 | 100 % (98.1-100) | 7.16 s |
| C3e μ 0.60 / masa + 10 g | 120 / 120 | 100 % / 100 % | 7.23 / 7.19 s |
| C3e CG 5 mm más adelante | 120 | 100 % | 7.13 s |
| C3e CG 10 mm más adelante | 120 | **60.0 %** (51.1-68.3), 48 derrapes | 7.69 s |
| C3m CG 3 mm más adelante | 120 | 100 % | 5.85 s |
| C3m CG 5 mm más adelante | 120 | 100 % | 5.87 s |
| C3m CG 7 mm más adelante | 120 | 98.3 % (94.1-99.5) | 5.92 s |
| C3m CG 10 mm más adelante (etapa F) | 120 | 80.0 % | 6.13 s |

**Tolerancia del CG:** hasta 5 mm por delante del CAD (x_CG ≤ 25 mm) ambos controles dan 100 %; desde 7 mm el de
competencia baja del criterio. Con el CG adelantado **el modo seguro no ayuda** (60 % a 10 mm): lo que se reduce al
adelantar el CG es la carga sobre las ruedas motrices, y eso afecta a los dos controles. La medición M2/M5 del manual tiene
por eso un criterio de aceptación explícito.

## 4. Riesgos y mitigaciones

| # | Riesgo | Severidad | Mitigación |
|---|---|---|---|
| R1 | **CG real adelantado** (por ejemplo, cables o batería más adelante de lo modelado) | **Alta** | El CAD da 20.1 mm; medir el reparto con dos básculas (manual §7.5, M2/M5). Criterio: x_CG ≤ 25 mm. Si no se cumple, mover la batería hacia atrás sobre los soportes (el modo seguro **no** compensa este caso) |
| R2 | Inercia del rotor menor a la supuesta | Media | Control elegido para 98.3 % en ese caso; el modo seguro da 100 %. Medición indirecta con los encoders |
| R3 | Motor real distinto de la ficha (velocidad libre, bloqueo) | Media | M7 (manual §8) → YAML → `python3 sim/fase_final.py F` antes de competir |
| R4 | μ real menor | Baja | 100 % hasta μ 0.60 simulado; M1 confirma |
| R5 | Señal de los QRE1113GR a 3.05 mm menor a la supuesta | Media | M8 (manual §5); la calibración exige 150 cuentas de rango por sensor |
| R6 | Batería con otro conector o género del XT30 | Baja | Revisar antes de soldar J1 (manual §2.4) |
| R7 | Defecto de ensamble de la PCB (puentes en el LQFP de 0.5 mm, almohadilla del DRV8833 sin soldar) | Media | Pruebas E1-E4 sin batería y con fuente limitada antes de conectar motores |
