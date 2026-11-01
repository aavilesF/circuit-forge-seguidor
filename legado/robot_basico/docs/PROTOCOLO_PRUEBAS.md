# Protocolo de construcción, calibración y pruebas físicas

Nada de esto se ha ejecutado todavía: **no hay mediciones**. Cada etapa tiene criterio de aprobado; no pasar a la siguiente si falla.
Registrar cada resultado en `modificaciones/AAAA-MM-DD-pruebas.md` (fecha, quién, valor medido, foto si aplica). Solo entonces una afirmación pasa a `[Validado físicamente]`.

**Instrumentos:** multímetro (V, A en escala de 10 A, continuidad), báscula de 0.1-1 g, vernier, cronómetro (celular), cinta métrica, termómetro infrarrojo o el dedo con cuidado (opcional), cable USB de datos, laptop con el software de `INSTALLATION_GUIDE.md`.

**Riesgos generales:** LiPo (incendio si se perfora, se carga sin balanceador o se descarga bajo 3.0 V/celda): cargar sobre superficie no inflamable y sin dejarla sola. Cortos al soldar con la batería conectada: **conectar la batería solo cuando la etapa lo pida**.

## F0. Antes de que lleguen las piezas
| Paso | Criterio de aprobado |
|---|---|
| Instalar software y compilar `seguidor.ino` (INSTALLATION_GUIDE §6) | Compila. Registrar versión del core |
| `pruebas/regresion.sh` | "REGRESIÓN COMPLETA: OK" |
| Decidir checkpoint C2 y sensor (ARQUITECTURA §3.2, §3.6) | Anotado en `decisiones.md` |

## F1. Recepción e inspección
| Pieza | Qué medir / revisar | Aceptación | Por qué |
|---|---|---|---|
| Todas | Pesar y anotar | Suma estimada + 60 g de chasis/cables ≤ 450 g | Margen de 50 g bajo el límite de 500 g |
| ESP32 | Etiqueta del módulo y número de pines | ESP-WROOM-32, 38 pines; serigrafía coincide con `pines.h` | GPIO16/17 se usan; en WROVER están ocupados |
| Sensor | Ancho, paso entre sensores (vernier, centro a centro), pines, si tiene LEDON/puente 3.3 V | Anotar; actualizar `PASO_MM` en `pines.h` | El clon de UNIT no publica paso (H05) |
| Motores | Que los dos sean de la misma variante (6 V 1000 RPM) | Etiqueta/lote iguales | RPM distintas tuercen la trayectoria |
| Batería | Voltaje por celda en el conector de balanceo | 3.7-4.2 V por celda y diferencia < 0.05 V | Celda dañada = no usar |
| Reguladores | Ajustar el MP1584 **antes** de conectarlo a nada | 5.00 ± 0.10 V en vacío | El potenciómetro viene en cualquier posición |

## F2. Polaridad y conexiones (sin batería)
1. Revisar con continuidad: no hay corto entre + batería y GND, ni entre 3V3 y GND, ni entre 5 V y GND. **Aceptación:** sin continuidad (más de 1 kΩ).
2. Revisar que el conector de batería solo entre en un sentido y que el rojo vaya al fusible.
3. Revisar cada señal de `docs/diagramas/pines.md` con continuidad del pin del ESP32 al destino.

## F3. Alimentación
| Paso | Medición | Aceptación |
|---|---|---|
| Batería → fusible → interruptor → regulador 5 V (nada más conectado) | Salida del regulador | 4.9-5.1 V |
| Misma prueba con fuente o batería a ~6.8 V (batería casi descargada) y carga de ~200 mA (el ESP32) | Salida | **≥ 4.75 V** (si no, el MP1584 no sirve con batería baja: usar D24V10F5; ver ARQUITECTURA §3.6) |
| Conectar ESP32 por VIN | Pin 3V3 | 3.2-3.4 V |
| Corriente de reposo (amperímetro en serie con la batería) | — | Anotar (esperado < 150 mA sin sensores) |
| Comando `bat` | Comparar con multímetro en la batería | Diferencia ≤ 0.15 V; si no, ajustar `DIVISOR_BAT` |
| Opción A de C2 solamente: regulador de motores | Salida en vacío y con un motor girando | 6.0 ± 0.3 V |

## F4. Motores (ruedas en el aire)
1. **Corriente de bloqueo, antes de conectar al driver** (el genérico no la publica): motor a 6 V desde el regulador o una fuente, amperímetro en serie, detener el eje con los dedos **≤ 1 segundo**. Anotar. **Aceptación:** ≤ 1.2 A (promedio del TB6612). Si da más, mantener `u_max` y aceleraciones bajas y nunca dejar el robot trabado con motores encendidos.
2. Conectar TB6612 (VM según C2, VCC a 3.3 V, STBY a GPIO16).
3. `m 0.3 0.3`: ambas ruedas hacia adelante 1 s. Si una gira al revés: `INVERTIR_IZQ/DER` en `pines.h`.
4. `m 0.3 0.1`: la izquierda más rápida. Si es la derecha, intercambiar canales A y B.
5. `m 0.6 0.6` durante 1 s, cinco veces: el driver no debe quemar al tacto (< ~60 °C) y el fusible no debe dispararse.
6. Velocidad libre: marca en la rueda, contar vueltas en 10 s con `m 1 1` repetido (o video en cámara lenta). **Anotar RPM reales**: con ellas se calcula `vmax` del simulador.

## F5. Sensores (robot en la mano, sobre la pista o una hoja blanca con cinta negra de 2.5 cm)
1. Altura: Pololu QTR-8A 3 mm (máx. 6 mm); clon UNIT 8-12 mm según el vendedor. Ajustar con el apoyo.
2. Pololu a 3.3 V: soldar/puentear "3.3V BYPASS" (guía Pololu).
3. `crudo` sobre blanco y sobre negro, sensor por sensor. **Aceptación:** diferencia ≥ 500 cuentas en cada canal. Si es menor, revisar altura, alimentación, emisores.
4. Polaridad: si el valor **sube** en negro, `ALTO_ES_NEGRO = true`; si baja, `false`.
5. Emisores: con `crudo`, desconectar/forzar LEDON a GND: los valores deben cambiar. Si no cambian, el clon no tiene control de emisores → `RESTA_AMBIENTE = false`.
6. Orden de canales: tapar uno por uno de izquierda a derecha; deben cambiar en orden 0→7. Si no, corregir el cableado del multiplexor.
7. `diag`: anota el tiempo de lectura. **Aceptación:** ≤ 1500 µs (deja margen en el ciclo de 2000 µs). Si es mayor: subir `PERIODO_CONTROL_US` en `parametros.h` y volver a correr el simulador con el retardo real (`retardo=` ciclos).
8. Cruce entre canales: línea bajo un solo sensor; los vecinos deben leer como blanco. Si "arrastran", subir `MUX_ESTABLECIMIENTO_US`.

## F6. Calibración (procedimiento de competencia, ≤ 15 s)
1. Encender, LED parpadea lento (ESPERA). Colocar el robot sobre la línea.
2. Botón CAL → LED rápido. Deslizar el robot a mano de lado a lado 2-3 veces de modo que **cada** sensor pase por blanco y negro (≈ 5 s).
3. CAL otra vez → LED fijo (LISTO). Si vuelve a ESPERA y la consola dice "calibracion insuficiente", repetir.
4. `sens` con el robot centrado: `pos` entre −3 y +3 mm. Línea a la derecha del robot: `pos` positivo.
**Aceptación:** tres calibraciones seguidas en ≤ 10 s cada una.

## F7. Primera marcha (pista simple: recta + curva amplia)
1. Perilla al mínimo (25 % de vbase). `tel 1`. START.
2. Duración del ciclo: la primera columna de la telemetría es la duración máxima del cálculo de control en µs. **Aceptación:** < 1800 µs (cabe en el periodo de 2000 µs). Si no, subir `PERIODO_CONTROL_US`; el simulador muestra que cada ms extra de retardo aumenta el error.
3. Comprobar que el robot **no** se detiene al soltar START (antirrebote) y que se detiene al presionarlo después de 0.5 s.

## F8. Ajuste del controlador (orden)
1. `set vbase 0.25`, `set kd 0`, `set kp 0.02`. Subir Kp hasta que siga la curva sin salirse; si zigzaguea en recta, bajarlo.
2. Subir Kd (0.0005 → 0.002) hasta que el zigzag desaparezca.
3. Subir vbase de 0.05 en 0.05; parar cuando se salga en la curva de radio 15 cm y regresar un paso.
4. `save`. Anotar los valores en `modificaciones/`.
**Aceptación:** 5 vueltas seguidas sin salirse en la pista de práctica (con U y curvas de R = 15 cm).

## F9. Recuperación y casos límite
| Prueba | Aceptación |
|---|---|
| Huecos de 5 mm (cortar el vinil) a vbase final | Pasa sin cambio de rumbo visible, 10/10 |
| Empujón lateral de ~3 cm con el dedo en recta | Vuelve a la línea sin perderla |
| Fin de línea (vinil que termina) | Se detiene en < 0.5 s y < 25 cm (simulación: 0.32 s, 12-21 cm) y **no** regresa al revés |
| Levantar el robot en marcha | Se detiene (PARADA o ERROR) |
| Luz: lámpara directa, sombra, luz de celular | Mismo comportamiento (resta de ambiente) |
| Arranque detrás de la línea de salida | No se mueve antes de START |

## F10. Autonomía
Batería llena (8.4 V): correr vueltas continuas hasta que `bat` marque 7.2 V. Anotar tiempo y número de vueltas.
**Aceptación:** ≥ 15 min (3 intentos de 5 min máximo cada uno).

## F11. Temperatura
Tras 5 min de marcha continua: tocar/medir driver, motores, regulador. **Aceptación:** < 60 °C (se pueden tocar sin quemarse). El reglamento sanciona humo.

## F12. Homologación (simulacro)
| Prueba | Aceptación |
|---|---|
| Peso completo con batería | ≤ 480 g (margen de 20 g) |
| Caja de 20 × 10 cm | Entra sin forzar, incluidos cables |
| Piezas sueltas | Nada > 10 g puede caerse: batería sujeta con cincho/velcro |
| Sin cable USB, WiFi/BT sin inicializar | Verificado por código (`seguidor.ino` no incluye WiFi/BT) |
| Calibración + colocación | ≤ 15 s, cronometrado 3 veces |

## Registro (copiar por cada sesión)
```
Fecha / integrantes:
Versión de firmware (commit):        Core ESP32:
Etapa:            Medición:            Valor:            ¿Aprobado?:
Parámetros (kp, kd, vbase, freno):
Observaciones / fotos:
```
