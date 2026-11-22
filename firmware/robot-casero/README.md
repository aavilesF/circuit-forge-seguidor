# Robot casero · C. Firmware V3 (ESP32 + DRV8833)

Firmware del prototipo oficial (Plan B). Usa lo mejor de V1 y V2, adaptado a las piezas reales: ESP32 DevKit de 30 pines, módulo DRV8833, N20 sin encoder, 8 sensores analógicos (QTR-8A o TCRT5000), 2 × MP1584.

| Parte | Origen | Archivo |
|---|---|---|
| Calibración por sensor y posición de la línea (promedio ponderado) | V1, sin cambios | `casero/posicion.*` |
| PID con anti-windup y derivada filtrada; seguimiento con retención en huecos y búsqueda | V1, sin cambios | `casero/pid.*`, `casero/control.*` |
| Máquina de estados INICIO → ESPERA → CALIBRACIÓN (≤ 15 s) → LISTO → SIGUIENDO ⇄ RECUPERACIÓN → PARADA / ERROR | V2, simplificada | `casero/estados.*` |
| LED y zumbador por estado (melodía al calibrar, código de error en destellos) | V2 | `casero/indicadores.*` |
| Límite de corriente con modelo del motor (`limitar_ciclo` de V2) y **velocidad estimada** (no hay encoders), tope de PWM, rampa | V2 + nuevo | `casero/motor.*` |
| Parámetros por consola guardados con CRC32 | V2 | `casero/ajustes.*` |
| Filtro de sensores: mediana de 3 + pasa-bajas, sobremuestreo y resta de luz ambiente | Nuevo (ruido de la placa fenólica) | `casero/filtro.*`, `casero/hw_casero.cpp` |
| DRV8833 en decaimiento lento (IN1 = 1, IN2 = PWM) [V TI, tabla 2] | Nuevo | `casero/motor.cpp`, `casero/hw_casero.cpp` |
| Pines y opciones de hardware | Nuevo | `casero/config.h` |

## Cargar el programa

**Arduino IDE:**

1. Abran `firmware/robot-casero/casero/casero.ino`.
2. Elijan la placa **"ESP32 Dev Module"**. Sirve el núcleo esp32 2.0.x o 3.x.
3. Suban el programa.

**PlatformIO:** `cd firmware/robot-casero && pio run -t upload && pio device monitor`.

Compilado aquí con arduino-esp32 **2.0.17** para ESP32 Dev Module: 303 KB (23 %), sin advertencias, en las dos variantes de sensores. El ESP32 real no se ha probado [P].

**Antes de compilar, revisen `config.h`:**

| Opción | Valor | Cuándo |
|---|---|---|
| `SENSORES_DIRECTOS` | 1 | 8 sensores en J6 (QTR-8A o TCRT5000 sueltos) |
| `SENSORES_DIRECTOS` | 0 | 12 TCRT5000 con el 74HC4067 (D05) |
| `PASO_SENSORES_MM` | 9.525 | QTR-8A |
| `PASO_SENSORES_MM` | 10.16 | Barra casera con sensores cada 4 agujeros |
| `DIST_SENSOR_EJE_MM` | medir [P] | Distancia de la barra al eje de las ruedas en el chasis armado |

## Uso en la competencia

1. Encender con el SW-104S. Se oye un pitido y el LED parpadea (ESPERA).
2. **CAL**: pasen la barra 2–3 veces sobre la línea. Termina sola 1 s después de que todos los sensores vieron blanco y negro (3 notas que suben), o con CAL/START, o a los 15 s como máximo. Si faltó contraste, suenan 3 notas que bajan y se conserva la calibración anterior.
3. Pongan el robot en la línea. El estado es LISTO: LED fijo.
4. **START** arranca.
5. **START** otra vez lo detiene. También se detiene solo si pierde la línea más de ~1.5 s.

La calibración queda guardada: si no hay tiempo, START en ESPERA usa la anterior.

## Consola USB (115200 baudios)

Solo responde cuando el robot no está corriendo.

| Comando | Qué hace |
|---|---|
| `ayuda` | Lista de comandos |
| `estado` | Estado, error, calibración y batería |
| `get` | Todos los parámetros |
| `set <clave> <valor>` | Cambia un parámetro (con rango). **Falta `save` para que se quede** |
| `save` / `load` / `defecto` | Guardar, recargar o volver a los valores de fábrica |
| `sens` | Oscuridad 0–1 de cada sensor y posición de la línea (mm, + = derecha) |
| `crudo` | Lecturas del ADC con LED IR encendidos y apagados |
| `bat` | Voltaje de la batería (divisor + caída de D1) |
| `perf` | Tiempo de lectura de sensores y del ciclo; nivel de nFAULT |
| `m <izq> <der> [ms]` | Prueba de motores, −1..1, **con las ruedas en el aire**. Pasa por el tope, la rampa y el límite de corriente |
| `tel 1` | Telemetría en marcha a 100 Hz: `pos_mm,visible,ciclo_izq,ciclo_der,vbat` |

## Parámetros principales

Todos se ven con `get`. Rangos en `casero/ajustes.cpp`.

| Clave | Por defecto | Qué es | Marca |
|---|---|---|---|
| `kp`, `kd`, `ki` | 0.010, 0.0004, 0 | PID sobre el error en mm. Los de V1 (0.04 y 0.002) oscilan con este motor en la simulación | [S] |
| `vbase` | 0.35 | Velocidad base (fracción del máximo permitido) ≈ 0.45 m/s | [S] |
| `pwm_max` | 0.90 | Tope de ciclo del DRV8833 | — |
| `v_motor_max` | 6.0 V | Si VM sale directo de la LiPo (`vm_bateria 1`), el tope baja a 6/VBAT ≈ 0.71 | [C] |
| `i_max`, `i_total` | 1.2 A, 2.0 A | Límite por motor (DRV8833: 1.5 A RMS [V]) y de los dos juntos (MP1584 #2) | [E] |
| `rampa` | 6 /s | Cambio máximo del ciclo: 0 → 100 % en ~170 ms | — |
| `m_R`, `m_ke`, `m_tau` | 6 Ω, 0.0533, 0.08 s | Modelo del N20 de 6 V y 1000 rpm. **Midan** la corriente de bloqueo: R = 6 V / I | [E] |
| `inv_izq`, `inv_der` | 0, 1 | Sentido de cada motor (manual, etapa 7) | [P] |
| `alfa`, `sobremuestreo` | 0.6, 1 | Filtro de sensores | — |
| `bat_baja`, `bat_critica`, `caida_d1` | 6.8 V, 6.4 V, 0.35 V | Batería 2S | [E] |
| `usar_nfault` | 0 | 1 solo con JP1 cerrado (manual, etapa 7) | — |
| `zumb_activo` | 1 | 0 si el zumbador es pasivo (necesita tono) | [P] |

## Pruebas en la PC

```
cd firmware/robot-casero/pruebas && ./ejecutar.sh      # 802 comprobaciones
```

Cubren:

- filtro (picos, escalones);
- tabla del DRV8833;
- límites del motor (rampa, tope, corriente en reversa y en arranque, suma);
- todos los cambios de estado, incluidos los 15 s de calibración;
- indicadores;
- ajustes y CRC;
- **simulación en lazo cerrado** de toda la cadena (sensores con ruido y picos → filtro → posición → PID → DRV8833 → motor con constante de tiempo distinta a la del modelo → cinemática).

En la simulación, la barra se desvía como máximo **1.5 / 3.5 / 7.2 mm** en curvas de 600 / 300 / 200 mm a ~0.5 m/s, con VM de 6 V y de 8.4 V [S].

Con `-DBARRIDO` se compila el barrido de ganancias con el que se eligieron kp y kd.

## Pendiente de medir en el robot [P]

- Sentido de los motores.
- Corriente de bloqueo del N20.
- Tiempo real de lectura de 8 canales con ADC2 (`perf`).
- Distancia barra–eje.
- Tipo de zumbador.
- Caída real de D1.
- Ganancias en la pista.
