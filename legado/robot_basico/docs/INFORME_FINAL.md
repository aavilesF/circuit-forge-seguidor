# Informe final — Nivel A (MVP competitivo)

Fecha: 31 oct 2026 · Rama: `engineering/final-prototype` · Competencia: 21 nov 2026 (21 días).
Etiquetas: `[Implementado]` `[Compilado]` `[Probado en software]` `[Verificado documentalmente]` `[Validado físicamente]` `[PENDIENTE: razón]`.

## A. Estado inicial del repositorio
- Solo existía `main` (`a12b865`). Ningún integrante había subido trabajo. Casi todo lo existente lo escribió esta IA en sesiones previas (ver aviso en `AUDITORIA.md`).
- Firmware con lógica pura probada (60 pruebas) y simulador, pero **nunca compilado para ESP32**, con la máquina de estados sin pruebas y varios defectos (rebote de START, batería en el lazo, divisor fuera del rango del ADC).
- Arquitectura y presupuesto propuestos, sin precios verificados ni fichas técnicas citadas. Nada comprado ni medido.

## B. Cambios realizados

| Archivo | Cambio | Estado |
|---|---|---|
| `firmware/seguidor/estados.h/.cpp` | **Nuevo**: máquina de estados (8 estados), antirrebote, monitor de batería | `[Probado en software]` |
| `firmware/seguidor/seguidor.ino` | Reescrito como orquestador; NVS con versión; `diag`; telemetría diezmada; compensación de batería opcional | `[Implementado]` sintaxis OK contra stub |
| `firmware/seguidor/pines.h` | Divisor 100k/33k; tiempos de mux 15 µs; polaridad de emisores; opción C2 | `[Implementado]` |
| `firmware/seguidor/control.*` | `compensar_bateria`; búsqueda 1.5 → 0.25 s | `[Probado en software]` |
| `firmware/seguidor/posicion.*` | `lecturas_imposibles` | `[Probado en software]` |
| `firmware/seguidor/hardware.*` | Constantes de tiempo, polaridad de emisores, lectura cruda | `[Implementado]` sintaxis OK |
| `pruebas/test_logica.cpp` | 60 → 93 pruebas | `[Probado en software]` |
| `pruebas/regresion.sh` | **Nuevo**: pruebas + ASan/UBSan + cppcheck + sintaxis + escenarios | `[Probado en software]` |
| `pruebas/verificar_sintaxis_esp32.sh`, `stub_arduino/` | Cubre todo el firmware con `-Werror` | `[Implementado]` |
| `simulacion/` → `sim/` | Renombrado (git mv); escenarios y comparación de controladores | `[Probado en software]` |
| `herramientas/generar_diagramas.py` | Ruta `sim/` | `[Implementado]` |
| `docs/AUDITORIA.md`, `ARQUITECTURA.md`, `INSTALLATION_GUIDE.md`, `BOM_FINAL.csv`, `PROTOCOLO_PRUEBAS.md`, `INFORME_FINAL.md` | **Nuevos** | `[Implementado]` |
| `docs/armado.md` | Reemplazado por un índice hacia PROTOCOLO_PRUEBAS (contenido anterior en git) | `[Implementado]` |
| `docs/electronica.md`, `mecanica.md`, `simulacion.md`, `decisiones.md`, `presupuesto.md`, `plan.md`, `contexto-ia.md`, `README.md` | Actualizados (divisor, altura de sensor, escenarios, C2, rutas) | `[Implementado]` |

Eliminados: ninguno.

## C. Arquitectura
Detalle y fichas en `ARQUITECTURA.md`.

| Bloque | Decisión | Estado | Fuente técnica |
|---|---|---|---|
| MCU | ESP32-WROOM-32 DevKit 38 pines | **Aprobada** (D3) | Espressif ESP-IDF ADC |
| Sensores | QTR-8A clon de UNIT (8 canales) vía CD74HC4067 | **Recomendada**, decisión del equipo pendiente | página UNIT; TI CD74HC4067; Pololu QTR guía 0J12 (original) |
| Driver | TB6612FNG | Recomendada | Toshiba TB6612FNG |
| Motores | GA12-N20 6 V 1000 RPM (medir bloqueo); Pololu 30:1 HP como mejora | Recomendada | página UNIT; Pololu #1093 |
| Batería | LiPo 2S 300-500 mAh | Recomendada | — |
| Alimentación | Motores directo de batería + compensación; 1 MP1584 a 5 V para lógica | **Checkpoint C2 abierto** | MPS MP1584 r1.1; Toshiba |
| Control | PD + freno por error, retención en huecos, búsqueda 0.25 s | `[Probado en software]` | `sim/resultados/comparar_*.csv` |

## D. Rendimiento esperado

**Cálculos** (supuestos en `ARQUITECTURA.md` §3.4): velocidad libre 1.73 m/s (33 mm, 1000 RPM); límite en curva R 150 mm ≈ 1.15 m/s con μ = 0.9; aceleración limitada por agarre ≈ 5.3 m/s²; frenado de 1.15 m/s en ≈ 0.22 s / 12 cm; autonomía ≈ 20-30 min con 450 mAh.

**Simulaciones** (`sim/`, modelo ideal: sin derrape, sin caída de batería, vmax supuesto 1.4 m/s):

| Situación (PD, QTR-8A) | vbase 0.4 | vbase 0.6 |
|---|---|---|
| Pista de prueba de 4.4 m | 7.5 s, error medio 1.1 mm | 5.2 s, 1.6 mm |
| Curva 90° / U / S de R 150 mm (error máx.) | — | 3.7 / 4.3 / 3.4 mm |
| Huecos de 5 mm | — | 0 pérdidas |
| Fin de línea | — | se detiene en 0.32 s |
| Retardo de lectura 12 ms / 24 ms | — | error medio 6.8 / 18.4 mm (dominante) |

**Mediciones físicas:** ninguna todavía.

## E. Estado de validación

| Qué | Estado |
|---|---|
| Lógica (posición, PID, control, estados) | 93 pruebas, 0 fallos; ASan/UBSan sin errores; cppcheck sin advertencias — `[Probado en software]` (g++ 13.3, Ubuntu 24.04) |
| Escenarios del simulador | 18/18 cumplen criterios (`pruebas/regresion.sh`) — `[Probado en software]` |
| Firmware completo vs. stub de Arduino (2 perfiles × API PWM 2.x/3.x) | OK con `-Werror` — **no es compilación real** |
| Compilación con core arduino-esp32 | `[PENDIENTE: la red del entorno bloqueó la descarga de la toolchain; la hace el equipo]` |
| Hardware | `[PENDIENTE: no hay piezas]` |

## F. Software por instalar
Ver `INSTALLATION_GUIDE.md`. Mínimo para competir: Git, Arduino IDE 2.x, core "esp32 by Espressif Systems" 3.x, driver USB (CP210x o CH340/CH9102 según la placa). Para desarrollo: Python ≥ 3.10 + numpy/matplotlib, g++ (en Windows por WSL). Nivel B: KiCad 8/9 y un CAD.

## G. Componentes por comprar
`BOM_FINAL.csv` (29 renglones).
- **Presupuesto verificado** (precios consultados en uelectronics.com el 31 oct 2026, sin envío):
  - Solo imprescindibles (ESP32, sensor, mux, driver, 2 motores, 2 soportes, cargador, regulador): **$693 a $732 MXN**.
  - Con repuestos recomendados (ESP32, sensor, mux, driver, 2 motores, regulador): **$1,149 a $1,227 MXN**.
  - El rango viene de las variantes del ESP32 ($131-156) y del motor ($83-90).
- **Pendientes de cotización (15 partidas):** batería 2S (+ repuesto), ruedas, ball caster, fusible, interruptor, botones, potenciómetro, resistencias, capacitores, conectores, perfboard, cable, material de chasis, pista de práctica. UNIT no vende baterías LiPo 2S.
- El presupuesto anterior ($4,002.79) **no era verificado** y no se puede comparar renglón por renglón.
- Además: donación de $300 MXN en alimentos el día del evento.

## H. Pendientes

| # | PENDIENTE | Bloquea | Alternativa sin bloqueo | Cómo se resuelve |
|---|---|---|---|---|
| 1 | Compilar con el core real (H01) | Subir firmware | Todo lo demás | Alejandro/Alan: INSTALLATION_GUIDE §6; reportar errores en `modificaciones/` |
| 2 | **Checkpoint C2** (alimentación) | Cableado de motores; 1 o 2 reguladores | Firmware soporta ambas | Equipo: aprobar B o mantener A; anotar en `decisiones.md` |
| 3 | Sensor definitivo (P10) | Compra; `pines.h` | Firmware parametrizado | Equipo decide; al recibir: paso, polaridad, LEDON (protocolo F1/F5) |
| 4 | Corriente de bloqueo y RPM reales del motor | Límite de `u_max`; `vmax` del simulador | Usar valores nominales | Protocolo F4 |
| 5 | Tiempo de lectura real (`diag`) | Periodo de control | 2 ms nominal | Protocolo F5 paso 7 |
| 6 | 15 precios | Presupuesto total | Comprar lo verificado | Cotizar en tiendas físicas de León/Irapuato o en línea; registrar enlace y fecha |
| 7 | Agarre (μ) de las llantas | Velocidad máxima en curvas | Suponer 0.9 | Medir: inclinar una tabla con el robot hasta que resbale, μ = tan(ángulo) |
| 8 | Masa real | Homologación | Estimación < 300 g | Báscula (protocolo F1/F12) |
| 9 | Altura del apoyo vs. altura del sensor | Calidad de lectura | — | Elegir caster/patín según el sensor comprado |
| 10 | Roles (P4) y aportación por persona (P5) | Organización | — | Equipo |
| 11 | P8/P9 (chasis y confirmación con la organización) | — | — | Alejandro indicó el 31 oct que el tema "ya quedó"; falta anotar el resultado en `decisiones.md` |
| 12 | Interpretación de "U" en el reglamento (H22) | Nada (se probó el caso más exigente) | — | Opcional |

## I. Repositorio
- Rama: `engineering/final-prototype` (publicada en GitHub). `main` no se modificó.
- Commits: ver `git log --oneline main..engineering/final-prototype` (lista en el mensaje de entrega).
- Sin squash, sin reescritura, sin ramas borradas. Archivo renombrado: `simulacion/` → `sim/`.

## J. Preparación para construcción: **Preparado parcialmente**
Justificación: hay arquitectura, firmware probado en software, simulador, BOM con precios verificados de las piezas principales, guía de instalación y protocolo con criterios.
No es "preparado para ensamblaje" porque faltan la compilación real (H01), la decisión C2, la decisión de sensor y 15 cotizaciones.
Se vuelve **"preparado para ensamblaje"** en cuanto se cierren los pendientes 1-3 y se cotice la batería; eso puede ocurrir esta semana.

**Calendario sugerido hasta el 21 nov:**

| Fechas | Meta | Prueba de terminado |
|---|---|---|
| 1-3 nov | Instalar software, compilar, decidir C2 y sensor, comprar | Compila; pedido hecho |
| 4-8 nov | Recepción, alimentación, motores, sensores (F1-F5) | Registros F1-F5 aprobados |
| 9-14 nov | Chasis, calibración, primera marcha, ajuste (F6-F8) | 5 vueltas sin salirse |
| 15-17 nov | Casos límite, autonomía, temperatura, homologación (F9-F12); inscripción antes del 17 nov 18:00 | Registros F9-F12 |
| 18 nov | Releer el reglamento (último día de cambios); congelar firmware | Commit etiquetado |
| 19-20 nov | Solo ajustes de parámetros; cargar baterías | — |

**Post-competencia (nivel B, requiere aprobación):** PCB en KiCad (requisitos en ARQUITECTURA §6), chasis CAD, encoders y control de velocidad en lazo cerrado, lectura del ADC por DMA, ESP32-S3 sin multiplexor.
