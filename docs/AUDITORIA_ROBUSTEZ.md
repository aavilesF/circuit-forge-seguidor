# Auditoría de robustez — arquitectura de $2,000 MXN (Fase 3)

Fecha: 1 nov 2026. **Todo es simulado** (`python3 sim/fase3.py S M P`, resultados en `sim/resultados/fase3/`). Nada se ha medido en hardware.
Configuración: Chihai N20 12 V i10 + barra clon QTR-8A (8 sensores) + ESP32 + TB6612FNG, cuello de 110 mm, control C3m (`config/robot_maestro.yaml`, v_max 0.66 m/s).
En cada escenario, el firmware conserva los parámetros y el modelo nominales; lo que cambia es el robot real (la planta). Son 30 salidas por pista (120 por escenario) con la dispersión normal (μ ±10 %, batería 7.6-8.3 V, motores ±5 %, colocación ±3 mm y ±2°). IC = intervalo de Wilson al 95 %.

**Criterio de aceptación:** ≥ 99 % de vueltas completas, porque un intento perdido vale 5 minutos.

## 1. Referencia

| Escenario | Éxito | t medio | Nota |
|---|---|---|---|
| Nominal (200 salidas, `G_barrido_vmax_robusto.csv`) | **100 %** (IC 98.1-100 %) | **6.35 s** | v_max 0.66 m/s, elegida por tiempo esperado |

## 2. Datos no publicados del motor (`S_sensibilidad_motor.csv`)

| Motor real distinto del supuesto | Éxito | t medio | Lectura |
|---|---|---|---|
| I de bloqueo 0.35 A (más débil) | 99.2 % | 7.02 s | Más lento, todavía estable |
| I de bloqueo 0.45 A | 100 % | 6.49 s | |
| **I de bloqueo 0.80 A (más fuerte)** | **57.5 %** | 6.30 s | **Derrapes**: el feed-forward manda más par del previsto |
| **I de bloqueo 1.0 A** | **5 %** | 6.66 s | No sirve sin reajustar |
| Eficiencia de reductora 0.6 | 79 % | 6.76 s | Pierde la línea: le falta par para girar |
| Eficiencia 0.7 / 0.85 | 100 % / 100 % | 6.39 / 6.32 s | |
| rpm −10 % / +10 % | 100 % / 98.3 % | 6.49 / 6.23 s | |

**Hallazgo crítico:** el resultado depende de que el modelo del motor en el YAML coincida con el motor real. **Antes de cualquier prueba en pista hay que medir la velocidad libre y la corriente de bloqueo (M7), actualizar `motores.chihai_n20_12v_2200_i10`, regenerar `config_maestra.h` y volver a correr el ajuste final** (`python3 sim/fase3.py G` y luego validar).

## 3. Fabricación y montaje (`M_fabricacion.csv`)

| Error | Éxito | t medio |
|---|---|---|
| Barra 3 mm más adelante / más atrás | 100 % / 100 % | 6.34 / 6.36 s |
| Barra desplazada 2 mm de lado | 100 % | 6.34 s |
| Barra girada 3° | 100 % | 6.40 s |
| Paso de sensores +5 % | 100 % | 6.32 s |
| Sensor más alto (mancha ×1.6) | 100 % | 6.23 s |
| Vía +3 mm | 100 % | 6.35 s |
| Llanta 1 mm menor | 100 % | 6.39 s |
| Motores desparejos ±10 % | 100 % | 6.42 s |
| **CG 10 mm más adelante** | **62.5 %** | 6.88 s |
| CG 10 mm más atrás | 100 % | 6.32 s |
| **Masa +40 g** | **84 %** | 6.66 s |

**Hallazgos:** la geometría de la barra tolera los errores de montaje típicos. Lo crítico es el **reparto de masa**: el CG debe quedar en x ≤ 22 mm (batería sobre o detrás del eje) y la masa en ≈ 132 g. Hay que pesar el robot y medir el reparto con dos básculas (M2, M5) antes de ajustar.

## 4. Batería, fricción, latencia, ruido y pérdida de línea (`P_escenarios.csv`)

| Escenario | Éxito | t medio | Fallas |
|---|---|---|---|
| Batería llena (8.4 V) | 99.2 % | 6.18 s | 1 derrape |
| Batería 7.4 V | 100 % | 6.57 s | — |
| Batería baja (6.9 V) | 100 % | 6.79 s | — |
| μ 0.90 | 100 % | 6.30 s | — |
| μ 0.70 | 97.5 % | 6.45 s | 3 derrapes |
| **μ 0.60** | **88 %** | 6.64 s | 14 derrapes |
| Latencia +2 ms | 100 % | 6.46 s | — |
| **Ruido de sensores ×3** | **50 %** | 6.32 s | pierde la línea |
| Huecos de 5 mm (reglamento) | 98.3 % | 6.33 s | 1 derrape |
| Huecos de 10 mm | 96.7 % | 6.35 s | — |
| Huecos de 20 / 40 mm | 75 % / 75 % | 6.67 s | Fuera de reglamento: margen de recuperación |

Corriente máxima por motor: 0.35 A (TB6612: 1.0 A continuos). Batería mínima: 6.8 V con 6.9 V en vacío. Consumo: 0.44-0.46 mAh por vuelta.

**Frenado en recta** (`P_frenado.csv`) desde 2.17 m/s: 4.0 m/s² con el piso del control, 3.9 m/s² con freno corto y 4.0 m/s² con inverso total. Llega al 20 % de la velocidad en 0.57 m. El frenado lo limita el agarre: el inverso total no gana nada y duplica la corriente (0.56 A).

## 5. Riesgos y mitigaciones

| # | Riesgo | Severidad | Mitigación |
|---|---|---|---|
| R1 | Motor real distinto del supuesto (bloqueo, eficiencia) | **Crítica** | Medir (M7) → YAML → reajuste → validar 200 salidas |
| R2 | μ y μ cinético reales menores | Alta | Medir (M1); usar la tabla v_max por μ (`SIMULACION_DINAMICA.md` §5); bajar v_max por consola |
| R3 | Ruido real de la barra clon mayor al supuesto (sin resta de luz ambiente) | Alta | Medir el ruido con `crudo` y `sens` (M8); si el ruido es más de 2× el supuesto, filtrar en firmware o cambiar a una barra con pin de emisores |
| R4 | CG adelantado o masa extra | Alta | Batería detrás del eje; pesar el robot (M2, M5) |
| R5 | Luz ambiente fuerte (la barra clon no resta luz ambiente) | Media | Probar bajo lámpara y luz de ventana (R06); pantalla negra alrededor de la barra |
| R6 | Batería llena: algo más de velocidad y 1 derrape en 120 | Baja | Validar con batería llena antes de cada intento |
| R7 | Salida de la barra a 5 V hacia el mux de 3.3 V | Media | 10 kΩ en serie por canal (BOM R1) |
| R8 | Entrega de los motores Chihai (19-28 nov) | Calendario | Respaldo local GA12-N20 6 V (5.64 s simulados en la etapa T); parámetros `control.C3m_ga12` |
