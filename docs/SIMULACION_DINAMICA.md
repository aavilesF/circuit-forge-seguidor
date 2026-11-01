# Simulación dinámica — Fase 2

Fecha: 1 nov 2026 · Rama `engineering/speed-follower`.
Etiquetas: **[Simulado]** sale del simulador dinámico · **[Calculado]** · **[Supuesto]** · **[Pendiente de medición]**. Nada de esto se ha probado en hardware.

## 1. Qué modela

| Bloque | Modelo | Archivo |
|---|---|---|
| Cuerpo | Rígido plano (x, y, guiñada) con el CG en (x_cg, h_cg), calculado de los componentes del YAML; inercia de guiñada de masas puntuales + placa | `sim/nucleo.py`, `sim/config.py` |
| Llantas | Fricción de Coulomb regularizada: F = −μ·N·s/√(\|s\|² + ε²), con s la velocidad de deslizamiento del punto de contacto (longitudinal y lateral). La fuerza de cada llanta nunca supera μ·N, de modo que el **círculo de fricción** sale del modelo, no se impone aparte | `nucleo.simular` |
| Apoyo | Bola: solo resistencia a la rodadura, sin fuerza lateral ni de frenado | `nucleo.simular` |
| Cargas normales | Estática + transferencia longitudinal (m·a_x·h/b) y lateral (m·a_y·h/W). Si una carga se vuelve negativa, la corrida se marca como **vuelco** | `nucleo.simular` |
| Ruedas | J·dω/dt = T_motor − F_x·r, con J = J_rotor·G² + J_llanta (la inercia del rotor reflejada, que la Fase 1 omitía) | `nucleo.simular` |
| Motor | DC lineal con los datos del fabricante (R, Ke, Kt, I₀), PWM con decaimiento lento (V = d·V_bus), corriente pico y conteo de disparos de la protección (OCP ≥ 2 A) | `nucleo.simular` |
| Batería | V_bus = V_oc − R_int·I_bus, con I_bus = Σ d·I_motor + I_lógica (+ ventilador). Integra mAh y energía | `nucleo.simular` |
| Sensores | Posición real de cada sensor (barra recta o en arco), distancia a la línea, mancha óptica de 3 mm, ruido gaussiano, huecos de 5 mm, umbral y estimación **idénticos al firmware** (`estimar_coord`) | `nucleo.simular` |
| Tiempo real | Periodo de control = max(1 ms, tiempo de lectura + cálculo); la salida se aplica tras la lectura (latencia). Tiempo de lectura = 2·(n·t_canal + t_emisor) + t_cálculo (resta de luz ambiente) | `config.construir` |
| Control | C1: PD directo sobre el ciclo · C2: firmware vigente (perfil por curvatura 2e/L², feed-forward del motor, persecución pura, PD, sin inversión) · C3m: C2 + curvatura estimada con el modelo del motor a partir de la última salida · C3g: C2 + curvatura de un giroscopio (ruido y sesgo) | `nucleo.paso_sf` |
| Línea perdida | Igual al firmware: se conserva el último error y a los 0.3 s se detiene (C07) | `nucleo.simular` |
| Fallas | Barra fuera de la línea > 0.1 s fuera de un hueco, o eje a más de 12 cm de la línea → **pierde la línea**; retroceso > 5 cm → **sentido contrario**; detenido o > 15 s → **detenido/tiempo**; carga normal negativa → **vuelco** | `nucleo.simular` |
| Vuelta | Desde parado, con la barra sobre la línea de salida, hasta que la parte trasera cruza la meta (reglamento C04-C05) | `nucleo.simular` |

**Dispersión de cada corrida (Monte Carlo, `simulador.perturbacion_aleatoria`):** μ ±10 %; batería entre 7.6 y 8.3 V; constante de cada motor ±5 % (izquierdo y derecho por separado); colocación ±3 mm y ±2°; error de medición de batería ±2 %; ruido de sensores en cada lectura.

**Integración:** Euler semiimplícito con paso ≤ 100 µs, elegido según la rigidez de la fricción (`simulador.paso_integracion`). Una vuelta tarda 20-60 ms de cómputo.

## 2. Pruebas del simulador (ejecutadas)

`python3 sim/pruebas/test_fisica.py` compara la planta contra soluciones analíticas:

| Prueba | Simulado | Referencia | Error |
|---|---|---|---|
| Velocidad final en recta, ciclo 1.0 (12 V 10:1) | 3.3664 m/s | 3.3674 m/s (equilibrio motor-rodadura-batería) | 0.03 % |
| Velocidad final en recta, ciclo 0.5 | 1.2990 m/s | 1.2996 m/s | 0.05 % |
| Aceleración máxima desde parado | 6.85 m/s² | ≤ 7.10 m/s² (agarre con transferencia hacia las ruedas) | cumple |
| ω_z = (v_R − v_L)/W en círculo | 1.625 rad/s | 1.569 rad/s | 3.6 % (deslizamiento regularizado, ε = 0.02 m/s) |
| Radio del eje = v/ω | 508.6 mm | 508.8 mm | 0.03 % |
| \|a\| del CG en giro forzado (percentil 99) | 6.02 m/s² | ≤ 8.00 m/s² (μ·g + rodadura) | cumple |
| Frenado con inverso | 4.73 m/s² | ≤ 4.74 m/s² (agarre con transferencia hacia el apoyo) | cumple |
| Energía de la batería ≥ energía cinética | 5.47 J | ≥ 0.74 J | cumple |

`python3 sim/pruebas/test_control.py`: el C2 del simulador reproduce los vectores dorados del firmware con una diferencia máxima de **5.7 × 10⁻⁸**. `pruebas/sf/ejecutar.sh`: el C++ del firmware reproduce al simulador en C2, C3m y C3g (≤ 5.6 × 10⁻⁵, diferencia entre float y double) y en `estimar_coord` (6.9 × 10⁻⁹ m).

**Efecto que la Fase 1 no capturaba:** con el CG delante del eje y un apoyo que no da fuerza lateral, girar exige una diferencia de fuerza longitudinal entre ruedas. Con ciclos fijos de 0.30/0.45, el robot describe un círculo de 509 mm, no los 107 mm que darían las velocidades libres de cada motor: la rueda interior va arrastrada 259 mm/s por encima de su velocidad libre. El control en lazo cerrado lo compensa, pero la respuesta de guiñada es más lenta que la cinemática.

## 3. Limitaciones

1. Motor lineal con datos de bloqueo extrapolados por el fabricante; sin inductancia (τ ≈ 60 µs), temperatura ni holgura de la reductora. J_rotor es un supuesto (Pololu no lo publica).
2. Fricción de Coulomb regularizada con μ único (sin diferencia estático/dinámico ni rigidez lateral real de la llanta). **μ es el supuesto dominante** y debe medirse (M1).
3. Sensores: la mancha óptica, el ruido y el tiempo por canal son supuestos o mediciones de terceros. Las lecturas de un ciclo se toman en el mismo instante; en el MCU real cada canal se lee en un momento distinto.
4. Pistas sintéticas; superficie plana y uniforme; sin uniones entre placas ni polvo.
5. Sin rizado de PWM, sin flexión del chasis, sin golpes del rival (final).
6. Los criterios de falla son una interpretación del reglamento: el referee decide qué es "perder la pista".
