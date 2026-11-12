# Validación final — cierre de ingeniería

Fecha: 2 nov 2026. Cada validación indica **de qué tipo es**. Ninguna es una prueba física: no hay placa fabricada ni robot
armado. Las pruebas físicas de aceptación (E1-E9) y las mediciones (M1-M8) están definidas en `MANUAL_ENSAMBLAJE.md`.

| Tipo | Significa |
|---|---|
| **Prueba de software** | Código ejecutado y comparado con una referencia (analítica, Python o vectores dorados) |
| **Simulación** | Simulador dinámico de `sim/` (modelo; depende de los datos [S] del YAML) |
| **EDA** | Verificación de KiCad 9 (reglas eléctricas y de diseño de la PCB, paridad con el esquemático) |
| **CAD** | Geometría y masas del modelo CadQuery |
| **Compilación** | El firmware compila y enlaza para el STM32G431 con el toolchain real |
| **Física** | Medido en el robot real — **ninguna todavía** |

## 1. Resumen

| # | Verificación | Tipo | Resultado | Evidencia |
|---|---|---|---|---|
| 1 | Encabezados del firmware = YAML + diseño eléctrico | Prueba de software | Sincronizados | `pruebas/registro_ejecutar_todo.txt` §1 |
| 2 | Física del simulador contra soluciones analíticas | Prueba de software | 4 comparaciones dentro de tolerancia (≤ 3.0 %) + cotas de agarre, frenado y energía | §2 del registro |
| 3 | Control del simulador = control del firmware | Prueba de software | C2: 5.7 × 10⁻⁸; lógica C++ (ASan/UBSan) = Python: 1.9 × 10⁻⁵ en 12 000 pasos; C2/C3m/C3g/C3e: ≤ 4.3 × 10⁻⁶; estimación de la línea: 7.3 × 10⁻⁹ m en 500 casos | §3-4 del registro |
| 4 | Compilación real del firmware | Compilación | arm-none-eabi-gcc 13.2.1, `-Wall -Wextra -Werror`: sin avisos; 16.2 KB de flash (12.6 %), 4.7 KB de RAM; rutinas de interrupción enlazadas a la tabla de vectores | `firmware/stm32/registro_compilacion.txt` |
| 5 | Control final en 200 salidas | Simulación | 5.81 s, 100 % (IC 95 % 98.1-100) | `sim/resultados/final/F_validacion_robustez.csv` |
| 6 | Robustez (17 escenarios + modo seguro + tolerancia de CG) | Simulación | 100 % salvo CG ≥ 7 mm adelante (§3) | `F_…csv`, `G_modo_seguro.csv` |
| 7 | ERC del esquemático | EDA | 0 errores; 2 avisos justificados (AISEN/BISEN a GND) | `hardware/electronics/verificacion/erc.rpt`, `RESUMEN.md` |
| 8 | DRC de la PCB con todas las reglas | EDA | **0 violaciones, 0 elementos sin conectar** | `verificacion/drc.rpt` |
| 9 | Paridad esquemático-PCB | EDA | **0 diferencias** | `verificacion/drc.rpt` |
| 10 | Conectividad diseño = esquemático = PCB | EDA + prueba de software | 78 redes, 346 conexiones idénticas; 365 pads de la PCB con la red correcta | `verificar_conectividad.py --pcb` |
| 11 | Huellas | EDA | 131 huellas, todas de las bibliotecas oficiales de KiCad 9 | `verificacion/modelos3d.md` |
| 12 | Modelos 3D | EDA | 109 componentes con modelo; 107 oficiales, 2 aproximados marcados (XT30, PTC 1812); 0 modelos faltantes en la exportación | `verificacion/modelos3d.md` |
| 13 | STEP de la PCBA = PCB | EDA + prueba de software | 109 componentes del STEP con posición (± 0.01 mm), cara y giro (± 0.1°) iguales a su huella | `verificar_modelos3d.py` |
| 14 | Interferencias mecánicas | CAD | 35 pares (piezas, PCBA real de KiCad y tornillería): 0 interferencias | `hardware/mechanical/VERIFICACION_MECANICA.md` |
| 15 | Caja del reglamento y altura | CAD | 132.0 × 92.0 mm (≤ 192 × 92 de diseño, 200 × 100 del reglamento); punto más bajo de la PCBA a 2.96 mm del piso | ídem |
| 16 | Masa y CG del CAD = simulador | CAD | 112.9 g frente a 113.0 g (−0.1 %); x_CG 20.1 mm frente a 20.1 mm | ídem |
| 17 | Accesibilidad | CAD | START, CAL, RESET, STDC14, XT30, ON/OFF y LEDs fuera de la batería y de los soportes | ídem |
| 18 | BOM = diseño | Prueba de software | Referencias, cantidades y números de parte iguales al diseño | `herramientas/generar_bom.py --verificar` |
| 19 | Cálculos eléctricos | Cálculo | Pistas, caídas, regulador, sensores, ADC y UART dentro de límites (§4) | `docs/CALCULOS_ELECTRICOS.md` |
| 20 | Funcionamiento del hardware real | **Física** | **No realizada**: no hay placa | `MANUAL_ENSAMBLAJE.md` E1-E9 |

Todo lo anterior se repite con `pruebas/ejecutar_todo.sh` (los pasos de EDA y CAD verifican los resultados guardados; se
regeneran con `hardware/electronics/generar_fabricacion.sh` y `hardware/mechanical/cad/generar_cad.py`).

## 2. Comparación firmware ↔ simulador

El control del firmware (`firmware/logica/`) es C++ puro y se compila dos veces: para la PC (pruebas con ASan/UBSan) y para
el STM32 (el mismo código fuente). En la PC se compara paso a paso con el simulador en Python usando vectores dorados
generados por el propio simulador: las diferencias (≤ 4.3 × 10⁻⁶) son de redondeo de `float` frente a `double`. Lo que esa
prueba **no** cubre: la capa de hardware (`firmware/stm32/src/hw.cpp`: reloj, ADC, PWM, encoders, USART, flash), que solo
se puede validar en la placa (pruebas E5-E8).

## 3. Simulación del control final

| Escenario | Competencia C3m (0.8165 m/s) | Modo seguro C3e (0.6327 m/s) |
|---|---|---|
| Nominal (200 salidas) | **100 %, 5.81 s** | **100 %, 7.16 s** |
| μ 0.60 | 100 %, 5.85 s | 100 %, 7.23 s |
| Masa + 10 g | 100 %, 5.86 s | 100 %, 7.19 s |
| CG 5 mm adelante | 100 %, 5.87 s | 100 %, 7.13 s |
| CG 7 mm adelante | 98.3 %, 5.92 s | — |
| CG 10 mm adelante | 80.0 %, 6.13 s | 60.0 %, 7.69 s |

Los demás escenarios (ruido × 3, sensores más altos, fototransistor lento, encoder desconectado, batería baja, latencia,
motores desparejos, bloqueo ± 20 %) dan 100 % (ver `AUDITORIA_ROBUSTEZ.md`). **Criterio de aceptación físico derivado:**
x_CG ≤ 25 mm (manual §7.5).

## 4. Cálculos eléctricos (resumen de `CALCULOS_ELECTRICOS.md`)

- Bloqueo por motor a 8.4 V: 0.525 A; peor caso de la entrada (2 bloqueos + lógica): 1.15 A < 1.5 A del PTC; DRV8833:
  1.5 A RMS por canal.
- Pistas de potencia de 0.8 mm (batería) y 0.5 mm (motores); única entrada estrecha: 1.35 mm de 0.30 mm al pin VM del
  DRV8833 (1.0 A admisibles con 10 °C de elevación, 1.3 A con 20 °C), aceptada y documentada.
- Caída batería → VM: 0.42 V a 1.15 A. Regulador: 3.305 V, 0.50 A de pico frente a 3 A.
- LED de los sensores: 22.7-28.0 mA (máx. 50 mA). Lectura de los 16 sensores con resta de luz ambiente: 225 µs.

## 5. Lo que falta validar (físico)

| Qué | Cómo | Dónde |
|---|---|---|
| Placa sin cortos, regulador, protección contra inversión | E1-E4 | Manual §3 |
| Programación, consola, tensión de batería | E5 | Manual §4 |
| Señal, ruido y resta de luz ambiente de los sensores (M8) | E6 | Manual §5 |
| Sentido de giro, encoders, velocidad libre y bloqueo (M7) | E7 | Manual §8 |
| Masa y reparto (M2, M5): x_CG ≤ 25 mm | Básculas | Manual §7.5 |
| Calibración y vueltas en pista, modo seguro y competencia | E8-E9 | Manual §9 |
