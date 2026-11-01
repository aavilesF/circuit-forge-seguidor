# Auditoría técnica del repositorio

Fecha: 31 oct 2026 · Rama: `engineering/final-prototype` (desde `main` @ `a12b865`) · Autor: Claude (IA), a petición de Alejandro.

> **Aviso de imparcialidad:** casi todo el código y la documentación auditados los escribió esta misma IA en sesiones anteriores.
> Esta auditoría es, en buena parte, una autoauditoría. Para compensarlo se usaron herramientas externas (sanitizers, cppcheck),
> fichas técnicas oficiales y el reglamento, y cada hallazgo indica su evidencia.

Etiquetas de evidencia: `[Implementado]` `[Compilado]` `[Probado en software]` `[Verificado documentalmente]` `[Validado físicamente]` `[PENDIENTE: razón]`.

## 1. Estado inicial (lo que había en `main` @ `a12b865`)

| Área | Encontrado | Evidencia |
|---|---|---|
| Ramas | Solo `main`. Ningún integrante había subido cambios ni propuestas en `modificaciones/` | `git ls-remote`, `git ls-files` |
| Firmware | Lógica pura (posicion, pid, control) + capa de hardware + `seguidor.ino` con la máquina de estados dentro | 57 archivos versionados |
| Pruebas | 60 pruebas unitarias con g++; verificación de sintaxis contra stub de Arduino | `pruebas/ejecutar.sh` → 60/0 |
| Simulador | `simulacion/simular.cpp` en lazo cerrado con el mismo código; barridos de velocidad y PID | ejecución real |
| Compilación ESP32 | **Nunca compilado con la toolchain real** | intentos de descarga bloqueados (ver §6) |
| Hardware | Nada comprado; ningún dato medido | `docs/decisiones.md` |
| Documentación | requisitos, plan, presupuesto, decisiones, contexto-ia, simulación, electrónica, mecánica, armado, diagramas | — |

## 2. Estructura del repositorio (después de esta rama)

```
README.md
docs/      AUDITORIA, ARQUITECTURA, INSTALLATION_GUIDE, BOM_FINAL.csv, PROTOCOLO_PRUEBAS, INFORME_FINAL,
           requisitos, decisiones, plan, presupuesto, simulacion, electronica, mecanica, armado, contexto-ia, diagramas/
firmware/  platformio.ini, seguidor/ (seguidor.ino, pines.h, parametros.h, posicion.*, pid.*, control.*, estados.*, hardware.*)
pruebas/   test_logica.cpp, ejecutar.sh, regresion.sh, verificar_sintaxis_esp32.sh, stub_arduino/
sim/       simular.cpp, ejecutar.sh, resultados/   (antes simulacion/; renombrado con git mv)
herramientas/generar_diagramas.py
modificaciones/
```

## 3. Hallazgos

Severidad: **C** crítico (puede impedir competir o dañar hardware), **I** importante (degrada rendimiento o confiabilidad), **M** mejora.

| ID | Sev. | Hallazgo | Evidencia | Impacto | Estado |
|---|---|---|---|---|---|
| H01 | C | El firmware del ESP32 nunca se ha compilado con la toolchain real; solo con un stub | intentos fallidos: `espressif.github.io`, `github.com/releases`, registro de PlatformIO → 403 del proxy | Errores de API del core solo aparecerán al compilar | `[PENDIENTE: el equipo compila en su laptop, INSTALLATION_GUIDE §4]` |
| H02 | C | Rebote del botón START: el primer flanco arrancaba el robot y un rebote milisegundos después lo detenía (START en marcha = parar) | Lectura del código anterior (`flanco_boton` sin tiempo) | Robot que "no arranca" en la salida | Corregido: `Boton` con antirrebote 30 ms + START ignorado 500 ms tras arrancar `[Probado en software]` |
| H03 | C | Divisor de batería 100k/47k: con 8.4 V daba 2.69 V, fuera del rango sugerido del ADC a 11 dB (150-2450 mV) | Espressif ESP-IDF v4.4.4, ADC, tabla de atenuación `[Verificado documentalmente]` | Lectura de batería errónea con batería llena | Corregido: 100k/33k → 2.08 V `[Implementado]` |
| H04 | C | MP1584 propuesto para dar 6 V a los motores desde 2S (6.6-8.4 V): la ficha pide VIN > VOUT + 3 V a baja carga y diodo bootstrap si VOUT/VIN > 65 % | MPS MP1584 r1.1 `[Verificado documentalmente]` | Regulación inestable, motores sin control de voltaje | **Checkpoint C2** (ARQUITECTURA §3.6). Firmware listo para la alternativa (`MOTOR_DESDE_BATERIA`) |
| H05 | C | El "QTR-8A" a la venta en UNIT Electronics es un clon con TCRT5000 (65.7 × 16 mm, detección 8-12 mm), no el Pololu (75 mm de ancho, 3 mm óptimo). Paso, polaridad y control de emisores no documentados | Página del producto, consulta 31 oct 2026 | Geometría y polaridad del firmware pueden no corresponder | `[PENDIENTE: medir al recibir]`. Firmware parametrizado (`pines.h`) y prueba de polaridad en el protocolo |
| H06 | I | La batería se leía con `analogReadMilliVolts` **en cada ciclo de control** y sin filtro: lento y con disparos falsos por picos de corriente | código anterior de `seguidor.ino` | Ciclo más largo y paradas falsas | Corregido: lectura cada 20 ms fuera del lazo + `MonitorBateria` (filtro + persistencia 300 ms) `[Probado en software]` |
| H07 | I | Telemetría: hasta ~25 caracteres por ciclo a 500 Hz ≈ 12 500 car/s, más que los ~11 500 car/s de 115 200 baud → `Serial.printf` bloquearía el lazo | cálculo: 115200/10 bits por carácter | Lazo de control lento solo con `tel 1` | Corregido: 1 de cada 20 ciclos `[Implementado]` |
| H08 | I | Máquina de estados dentro del `.ino`: no se podía probar; sin estados de ERROR ni RECUPERACIÓN | código anterior | Transiciones sin pruebas | Corregido: `estados.*` puro con 8 estados; 33 pruebas nuevas en total (estados, botón, batería, compensación, fallas) `[Probado en software]` |
| H09 | I | Búsqueda de línea de 1.5 s: en simulación el robot da la vuelta y reencuentra la línea **en sentido contrario** (reglamento: "sentido correcto") | escenario `fin_de_linea`: con 0.4-1.5 s nunca se detiene (40 s, 39-40 pérdidas) `[Probado en software]` | Robot circulando al revés | Corregido: 0.25 s → se detiene a 0.32 s y ~120-210 mm del final |
| H10 | I | Tiempo de establecimiento del multiplexor de 4 µs con salidas de 47 kΩ (QTR-8A) y ~50 pF del mux: τ ≈ 2.4 µs, 4 µs ≈ 1.7τ → cruce entre canales | guía Pololu QTR (47 kΩ) y TI CD74HC4067 (CCOM 50 pF) `[Verificado documentalmente]` | Posición sesgada | Corregido a 15 µs (~6τ), ajustable `[PENDIENTE: confirmar con 'diag']` |
| H11 | I | El tiempo real de lectura de 8/24 canales en el ESP32 es desconocido; la simulación muestra que el retardo es el factor dominante (12 ms → error 1.6 → 6.8 mm) | `sim/` (barrido de retardo) | Si el ciclo pasa de ~4 ms el seguimiento empeora mucho | `[PENDIENTE: medir con 'diag']`. Comando `diag` agregado |
| H12 | I | Altura de sensores documentada en 8-10 mm (dato del profesor para sensores sueltos); el QTR-8A Pololu rinde mejor a 3 mm (máx. 6 mm) y el clon dice 8-12 mm | Pololu QTR guide; UNIT | Lecturas débiles | Corregido en `mecanica.md` y protocolo: altura según el sensor comprado |
| H13 | I | Calibración/parámetros guardados en NVS sin versión: un firmware nuevo podía leer bytes con otro significado | código anterior | Parámetros corruptos tras actualizar | Corregido: clave `ver` (VERSION_NVS) `[Implementado]` |
| H14 | I | Sin detección de sensores desconectados/saturados | código anterior | Robot ciego que sigue avanzando | Corregido: `lecturas_imposibles` 300 ms → ERROR `[Probado en software]` |
| H15 | I | Pista de prueba original del simulador se cruzaba consigo misma (prohibido por reglamento) | gráfica revisada en sesión anterior | Resultados no representativos | Ya corregido en `a12b865` |
| H16 | I | Precios de `presupuesto.md` sin verificar | el propio documento lo dice | Presupuesto poco fiable | `BOM_FINAL.csv` con 8 precios consultados; el resto "Pendiente de cotización" |
| H17 | M | Parámetros del simulador duplicados respecto a `parametros.h` (L = 75 mm, dist_eje = 100 mm) | `sim/simular.cpp` `Config` | Riesgo de desalinear | Pendiente menor: documentado; ambos marcados NOMINAL |
| H18 | M | Avisos de cppcheck (variables sin inicializar en el simulador) | cppcheck 2.22 | Ninguno funcional | Corregido; `regresion.sh` falla si reaparecen |
| H19 | M | `docs/plan.md` tiene calendario de 4 semanas con fechas ya pasadas | lectura | Confusión | Se conserva como histórico; el plan vigente está en INFORME_FINAL §J |
| H20 | M | `docs/armado.md` y `PROTOCOLO_PRUEBAS.md` duplicarían contenido | — | Documentos contradictorios | `armado.md` queda como índice que apunta al protocolo (contenido anterior en el historial de git) |
| H21 | M | El robot calibra solo con barrido manual; el reglamento da 15 s para calibrar y colocar | reglamento | Calibración apresurada | Calibración con tope de 10 s; se conserva la última calibración en NVS |
| H22 | M | Interpretación de curvas: "ángulos menores a 90° medidos desde la parte frontal del robot hacia un lado ... Puede haber secciones en U" | reglamento §Especificaciones de la pista `[Verificado documentalmente]` | Ambigüedad (¿U = dos curvas < 90° seguidas?) | El simulador prueba curvas de 90° y U de 180° con R = 150 mm (caso más exigente) |

## 4. Riesgos principales (ordenados)

1. **No compilar a tiempo** (H01): primera compilación real debe hacerse el día en que se instale el software, antes de comprar.
2. **Alimentación** (H04): decisión C2 pendiente; afecta cableado y BOM.
3. **Sensor real distinto al modelado** (H05, H12): la geometría, polaridad y altura se confirman al recibirlo.
4. **Tiempo de lectura** (H11): puede obligar a menos canales o a quitar la lectura con emisores apagados.
5. **Motor genérico sin corriente de bloqueo documentada**: hay que medirla antes de conectar al TB6612 (1.2 A promedio, 3.2 A pico 10 ms).
6. **Agarre de las llantas** desconocido: limita la velocidad en curvas de 15 cm a ≈ √(μ·g·R).

## 5. Elementos que se conservan

- Separación lógica pura / hardware (permitió 93 pruebas sin ESP32).
- `pines.h` como única fuente de pines y generador de diagramas con validaciones.
- PID con anti-windup y derivada filtrada; estimación por promedio ponderado (suficiente para pista sin cruces).
- Flujo `modificaciones/` para el equipo; `decisiones.md` como registro.

## 6. Herramientas usadas en la auditoría

| Herramienta | Uso | Resultado |
|---|---|---|
| g++ 13.3 (Ubuntu 24.04) | pruebas y simulador | 93 pruebas, 0 fallos |
| g++ `-fsanitize=address,undefined` | errores de memoria/indefinidos | 0 errores |
| cppcheck 2.22 | análisis estático | 0 advertencias (tras corregir H18) |
| Stub de Arduino | sintaxis de todo el firmware, 2 perfiles × 2 APIs PWM, `-Werror` | OK (no es compilación real) |
| PlatformIO / arduino-cli | compilación real ESP32 | **No disponible**: descargas bloqueadas por la red del entorno |
| KiCad / CAD | — | No disponibles (tampoco requeridos en nivel A) |
| WebSearch/WebFetch y navegador | fichas técnicas y precios | Espressif, Pololu, TI, Toshiba, MPS, UNIT Electronics |

## 7. Decisiones pendientes (detalle en INFORME_FINAL §H)

C2 alimentación de motores · sensor definitivo (clon UNIT, Pololu original o curvo 24) · modelo de motor (genérico o Pololu) · llantas y apoyo · batería 2S (capacidad y proveedor).
