# Verificación independiente de la Fase 1

Fecha: 1 nov 2026 · `python3 sim/verificacion_fase1.py` → `sim/resultados/fase2/V_verificacion_fase1.csv`.
Cada cálculo de la Fase 1 (`sim/fase1/calculos_fisicos.py`, configuración v1 congelada) se recalculó por un camino distinto: geometría numérica, la planta dinámica del simulador o una fórmula alternativa. Veredictos: **CORRECTO** · **DIFERENCIA** (explicada) · **ERROR DE FASE 1** (omisión del modelo) · **ACTUALIZADO** (cambió el diseño, no el cálculo) · **SUPUESTO REVISADO** · **LIMITACIÓN**.

| Tema | Comprobación | Fase 1 | Verificado | Veredicto | Nota |
|---|---|---|---|---|---|
| Motor | I sin carga reproducida a 12 V | 0.08 A | 0.08 A | CORRECTO | R, Ke y Kt reproducen exactamente los 4 datos del fabricante |
| Motor | Par de bloqueo a 12 V | 0.02452 N·m | 0.02452 N·m | CORRECTO | |
| Motor | Velocidad libre a 7.4 V (D 34 mm) | 2.171 m/s | 2.236 m/s (sin carga) / 2.19 m/s (planta dinámica) | CORRECTO | La diferencia es la rodadura y la caída de la batería |
| Motor | Dispersión de ±20 % de rpm | no considerada | 1.74-2.60 m/s | LIMITACIÓN | El simulador incluye ±5 % entre motores |
| Motor | Inercia de rotores y llantas | 0 | 41.6 g equivalentes (+34 % de inercia) | **ERROR DE FASE 1** | J_rotor no publicado: supuesto |
| Motor | 0 a 1 m/s en recta | 0.185 s | 0.195 s | DIFERENCIA | La inercia de los rotores frena; la transferencia de carga ayuda |
| Motor (Fase 3) | Par supuesto del GA12-N20 6 V (0.30 kg·cm con 0.67 A) | — | implica una eficiencia de reductora de **1.56** | **ERROR (supuesto imposible)** | Reemplazado por T = η·Ke·(I_bl − I0) con η = 0.79, deducida de la ficha Pololu |
| Cuello | Radio del eje en R150, L = 80 / 100 / 120 mm | 126.9 / 111.8 / 90.0 mm | 130.6 / 116.6 / 96.6 mm | CORRECTO / DIFERENCIA | La línea queda 2.4-3.7 mm fuera del centro (error de régimen), por eso el radio real es algo mayor |
| Captura | Desplazamiento de la línea en la barra en arco, L = 90 / 100 / 110 mm | 27.0 / 33.33 / 40.33 mm | igual (bisección numérica) | CORRECTO | La fórmula está bien; el **criterio** (peor caso sin reacción) resultó conservador: L = 110 mm captura en la simulación dinámica |
| Frenado | Desaceleración máxima por agarre | 5.18 m/s² | 4.56 m/s² | **ERROR DE FASE 1** | Al frenar, el peso pasa al apoyo, que no frena (transferencia de carga) |
| Frenado | Frenado con inverso desde la velocidad libre (planta) | 5.18 m/s² | 3.89 m/s² | CORRECTO | Con ruedas bloqueadas actúa el μ cinético (supuesto 0.8·μ) |
| Frenado | Aceleración máxima por agarre | 5.18 m/s² | 7.1 m/s² | **ERROR DE FASE 1** | Asimetría acelerar/frenar no modelada |
| Frenado | FEM máxima a la velocidad libre con 8.4 V | 6.94 V | ≤ 7.12 V | CORRECTO | No hay bombeo de voltaje al bus por FEM en 2S |
| Masa | Masa total | 154.9 g | 121.4 g | ACTUALIZADO | Rediseño de la v2 (chasis, MCU, apoyo) |
| Masa | f_motriz | 0.66 | 0.708 | ACTUALIZADO | Ahora se calcula del CG de los componentes |
| Masa | Fracción de la succión sobre las ruedas | 0.90 | 0.80 | SUPUESTO REVISADO | 0.90 exige el faldón a 7.5 mm del eje |
| Energía | Corriente media por vuelta | 0.9 A | 0.25 A | CORRECTO (conservador) | 0.34 mAh por vuelta |
| Agarre | La fuerza lateral la dan solo las ruedas | sí | sí | CORRECTO | Además, el CG adelantado exige diferencia de fuerza entre ruedas para girar |

## Errores del modelo que solo aparecieron con la simulación dinámica

1. **Autoridad de giro sin ciclo negativo:** a ~1.2 m/s el robot giraba gracias al deslizamiento; con más agarre perdía la curva R150. Se agregó el parámetro `piso` (simulador y firmware).
2. **Derrape explotado por el optimizador:** con μ estático al deslizar, el ajuste bloqueaba la rueda interior y derrapaba (deriva ≈ 40°). Se agregaron μ cinético y el criterio de derrape (`traccion.desliz_valido`).
3. **La cota cuasiestática de la Fase 1 (3.0-3.4 s) es ≈ 45 % más rápida que lo simulado** (5.8 s): el robot solo ve 11 cm adelante y no puede frenar a tiempo para la curva si va rápido en la recta.

**Conclusión:** la aritmética de la Fase 1 es correcta. Los errores están en lo que el modelo cuasiestático no podía representar: inercia, transferencia de carga, fricción cinética, autoridad de giro y anticipación limitada. Por eso la Fase 1 queda como **evidencia histórica**, y las predicciones vigentes son las del simulador dinámico.
