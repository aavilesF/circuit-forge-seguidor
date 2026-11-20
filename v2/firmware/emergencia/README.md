# Firmware del prototipo de EMERGENCIA (vigente)

**Estado:** compilado y probado en PC el 19 nov 2026. **Todavía no se ha cargado en el robot real**: falta la prueba física (sección 7).
**Hardware:** ESP32 DevKit de 30 pines, DRV8833, 2 motores N20 de 6 V y 8 TCRT5000 con el CD74HC4067.
**Fuente de verdad del hardware:** [`GUIA-FIRMWARE.md`](../../electronica/prototipo-emergencia/GUIA-FIRMWARE.md) y `robot_emergencia_unificado.kicad_sch`. Si algo de aquí contradice al esquema, manda el esquema.

## 1. De dónde sale (EM-07)
Se **adaptó** el firmware histórico `firmware/robot-casero/` en lugar de escribir uno nuevo. Esa lógica ya tenía pruebas en PC: posición de la línea, PID con anti-windup, filtro de sensores, límites del motor, máquina de estados y ajustes con CRC. El histórico **no se modificó** y sigue siendo HISTÓRICO.

| Tema | Histórico (`firmware/robot-casero`) | Este firmware |
|---|---|---|
| Sensores | 8 directos al ESP32 por defecto, o 12 por mux | **8 por el CD74HC4067**, canales C0–C7 |
| START | GPIO18 | **GPIO4** |
| Zumbador | GPIO4, melodías y tonos | **Eliminado** (D-V2-05). Los avisos usan el LED del DevKit (GPIO2) y la consola |
| nFAULT | GPIO15, ajuste `usar_nfault`, error 2 | **Eliminado** (P13: no está conectado) |
| Ventilador | No existía | No existe (EM-01). GPIO15 y GPIO17 quedan libres |
| Batería | Le sumaba 0.35 V por la caída del diodo D1 | **Medida directa**: el divisor 100k/33k va a `VBAT_SW` sin diodo |
| Voltaje del puente | Opción de alimentar VM directo de la batería | **Siempre 6.0 V** (MP1584 U2) |
| Paso de sensores | 9.525 mm (QTR-8A) | **12.7 mm** (barra recta de placa perforada) |
| Paradas | START o línea perdida | Además: **cualquier tecla por USB** y **ciclo de control atrasado** (error 2) |
| Memoria | Espacio `casero` | Espacio `emergencia` con otra firma: no carga datos viejos |

## 2. Archivos
| Archivo | Qué es |
|---|---|
| `emergencia/emergencia.ino` | Programa principal: ciclo de control a 400 Hz, consola USB, memoria |
| `emergencia/config.h` | **Pines y opciones de hardware** (lo único que se toca al armar) |
| `emergencia/hw.*` | Capa del ESP32: mux, ADC, PWM (LEDC, núcleos 2.x y 3.x), botones, LED |
| `emergencia/utiles.h` | Bits del mux, orden físico, voltaje de batería y antirrebote (C++ puro, probado) |
| `emergencia/posicion.*`, `pid.*`, `control.*`, `filtro.*`, `motor.*` | Lógica copiada del histórico **sin cambios** |
| `emergencia/estados.*`, `indicadores.*`, `ajustes.*`, `parametros.h` | Lógica del histórico **adaptada** (ver tabla de la sección 1) |
| `pruebas/test_emergencia.cpp` | 849 comprobaciones en PC, incluida una simulación en lazo cerrado |
| `pruebas/verificar_pines.py` | Compara `config.h` con el esquema (símbolo del ESP32 + netlist esperado) |
| `pruebas/ejecutar.sh` / `ejecutar.ps1` | Ejecutan las pruebas y la verificación de pines |
| `platformio.ini` | Compilación con PlatformIO: núcleo 3.x (`esp32dev`) y 2.0.17 (`esp32dev_nucleo2`) |

## 3. Cargar el programa

### Arduino IDE (2.x)
1. Instalen el soporte del ESP32: *Herramientas → Placa → Gestor de placas*, busquen **esp32 de Espressif Systems** e instalen. Sirven la versión 3.x y la 2.0.x.
2. Abran `v2/firmware/emergencia/emergencia/emergencia.ino`. Las demás pestañas (`config.h`, `hw.cpp`, …) se abren solas: tienen que quedarse en la misma carpeta.
3. *Herramientas → Placa → esp32 →* **ESP32 Dev Module**. Dejen los valores por defecto: Upload Speed 921600, Flash 4 MB y Partition Scheme "Default 4MB with spiffs".
4. Elijan el puerto COM del DevKit y suban el programa. Si se queda en `Connecting....`, mantengan oprimido el botón **BOOT** del DevKit hasta que empiece a escribir.
5. Abran el *Monitor Serie* a **115200** baudios con fin de línea **"Nueva línea"** y escriban `ayuda`.

No hacen falta bibliotecas externas. `Preferences` viene con el núcleo del ESP32.

### PlatformIO
```
cd v2/firmware/emergencia
pio run                      # compila (núcleo 3.x)
pio run -t upload            # compila y carga
pio device monitor           # consola a 115200
pio run -e esp32dev_nucleo2  # opcional: compila con el núcleo 2.0.17
```

### Pruebas en la PC (sin robot)
```
cd v2/firmware/emergencia/pruebas
./ejecutar.sh          # Linux, macOS o Git Bash
.\ejecutar.ps1         # PowerShell; requiere g++ (MinGW/WinLibs) y Python en el PATH
```

## 4. Uso en la competencia
1. Enciendan con el KCD1. El LED del DevKit parpadea lento: estado ESPERA.
2. **CAL**: pasen la barra 2 o 3 veces sobre la línea; el LED parpadea rápido. La calibración termina sola 1 s después de que los 8 sensores vieron blanco y negro (LED fijo 0.6 s). También termina con CAL o START, o a los 15 s como máximo. Si faltó contraste, el LED da 3 destellos rápidos y se conserva la calibración anterior.
3. Pongan el robot en la línea. En estado LISTO el LED queda fijo.
4. **START** arranca.
5. El robot se detiene con **START**, con **cualquier tecla** por el cable USB o solo, si pierde la línea más de ~1.5 s.

La calibración queda guardada. Si no hay tiempo, START en ESPERA usa la anterior.

| LED | Significado |
|---|---|
| Parpadeo lento (1 Hz) | ESPERA |
| Rápido (5 Hz); 10 Hz en los últimos 3 s | Calibrando |
| Fijo | LISTO (o la calibración salió bien) |
| Encendido / apagado en marcha | Ve / no ve la línea |
| Muy rápido (8 Hz) | Buscando la línea |
| 4 Hz | PARADA |
| 1 destello + pausa | ERROR 1: batería crítica |
| 2 destellos + pausa | ERROR 2: el ciclo de control se atrasó |
| 2 apagones cortos cada 3 s (en ESPERA o LISTO) | Batería baja |

## 5. Seguridad incluida
- **Arranque seguro:** lo primero que hace `setup()` es poner nSLEEP (GPIO16) en 0 y las 4 entradas del DRV8833 en 0. El puente solo despierta en LISTO, SIGUIENDO, RECUPERACIÓN y durante el frenado de PARADA.
- **El robot no se mueve sin START**, y START se rechaza sin calibración, sin batería (solo USB), con batería crítica o con un diagnóstico activo (`emis`/`mux`).
- **Paradas:** START, cualquier byte por USB, línea perdida → PARADA: frena 0.3 s y después suelta los motores y duerme el puente. Batería crítica sostenida 0.5 s, o un ciclo de control de más de 25 ms en marcha → ERROR: motores sueltos y puente dormido.
- **Límites de PWM** (`motor.h`): tope de ciclo `pwm_max` = 0.90 y `v_motor_max / 6 V`; rampa `rampa` = 6/s (0 → 100 % en ~170 ms); corriente estimada ≤ 1.2 A por motor y ≤ 2.0 A en total. PWM a 20 kHz y 10 bits, en decaimiento lento.
- **Antirrebote:** 25 ms de lectura estable (`ANTIRREBOTE_MS`); una pulsación da un solo evento.
- **Prueba de motores** (`m`): máximo 3 s y se corta con cualquier tecla.

## 6. Consola USB (115200, fin de línea "Nueva línea")
Mientras el robot corre, la consola no responde: cualquier tecla lo **detiene**.

| Comando | Qué hace |
|---|---|
| `ayuda` | Lista de comandos |
| `ver` / `pines` | Versión del firmware / mapa de pines compilado |
| `estado` | Estado, error, calibración y batería |
| `get` / `set <clave> <valor>` / `save` / `load` / `defecto` | Ver, cambiar (con rango), guardar, recargar o volver a los valores de fábrica |
| `sens` | Oscuridad 0–1 de cada sensor, de izquierda a derecha, y la posición de la línea (mm; + = derecha) |
| `crudo` | Lecturas del ADC con los LED IR encendidos y apagados |
| `cal` | Mínimo, máximo y contraste de cada sensor en la calibración guardada |
| `canal <0-15>` | Lee un canal del mux 16 veces con LED encendidos y apagados |
| `mux <0-15>` / `mux off` | Deja el mux fijo en un canal para medir `SIG` con el multímetro (bloquea START) |
| `emis 1` / `emis 0` | Deja los LED IR encendidos para medirlos o verlos con la cámara del celular (bloquea START) |
| `botones` | Lectura directa de START y CAL |
| `bat` | Voltaje de la batería, mV en el pin y umbrales |
| `perf` | Tiempo de lectura de sensores y ciclo máximo |
| `m <izq> <der> [ms]` | Prueba de motores, −1..1, **con las ruedas en el aire**. Pasa por el tope, la rampa y el límite de corriente |
| `stop` | Suelta los motores y duerme el puente |
| `tel 1` / `tel 0` | Telemetría en marcha a 100 Hz: `pos_mm,visible,ciclo_izq,ciclo_der,vbat` |

Parámetros principales (todos con `get`; los rangos están en `ajustes.cpp`): `kp` 0.010, `kd` 0.0004, `ki` 0, `vbase` 0.35, `pwm_max` 0.90, `rampa` 6, `i_max` 1.2 A, `i_total` 2.0 A, `inv_izq` 0, `inv_der` 1, `bat_baja` 6.8 V, `bat_critica` 6.4 V, `alfa` 0.6, `t_emisor_us` 150.

## 7. Qué se verificó y qué falta

### Verificado (19 nov 2026, en PC, sin robot)
| Prueba | Resultado |
|---|---|
| `pruebas/ejecutar.sh` (g++ 16.2, `-Wall -Wextra -Werror`) | 849/849 comprobaciones: filtro, tabla del DRV8833, límites del motor, estados, paradas por USB y por ciclo atrasado, LED, ajustes y CRC, mapa de pines, bits del mux, orden físico, batería y antirrebote |
| Simulación en lazo cerrado (8 sensores a 12.7 mm, motores a 6 V, ruido y picos) | Sin perder la línea. Desvío máximo de la barra: 5.1 / 5.5 / 6.0 mm en curvas de 600 / 300 / 200 mm a ~0.47 m/s |
| `pruebas/verificar_pines.py` | Las 14 señales de `config.h` coinciden con el esquema unificado. GPIO2 (LED) está libre y SEN1..SEN8 van en C0..C7 |
| Compilación para **ESP32 Dev Module** | Ver la tabla de abajo |

| Entorno | Núcleo | Resultado |
|---|---|---|
| PlatformIO `esp32dev` (espressif32 8.0.0) | arduino-esp32 3.3.12 | **Compila** desde cero, 0 advertencias con `-Wall -Wextra`. Flash 313 339 B (23.9 %), RAM 23 904 B (7.3 %) |
| PlatformIO `esp32dev_nucleo2` (espressif32 6.9.0) | arduino-esp32 2.0.17 | **Compila**, 0 advertencias en el código del robot. Flash 314 301 B (24.0 %), RAM 23 320 B (7.1 %) |

No se compiló con Arduino IDE en sí. Usa el mismo núcleo y la misma placa (`esp32dev` = ESP32 Dev Module), así que debería dar el mismo resultado, pero la primera carga lo confirmará.

### Falta probar con el robot [P]
Hagan las pruebas en orden, siguiendo la sección 9 de la GUIA:
1. Continuidad de cada pin contra el esquema, con la placa **sin batería**.
2. Con solo USB: `ver`, `pines`, `botones` (oprimir START y CAL) y `bat` (debe decir "solo USB").
3. Emisores: `emis 1` y ver los LED IR con la cámara del celular; `emis 0`.
4. Mux: `mux 0` … `mux 7` midiendo `SIG` con el multímetro sobre blanco y negro; `mux off`. Después, `canal 0` … `canal 7`.
5. **Orden de los sensores:** `sens` con la línea bajo el lado **derecho** del robot debe dar `pos` > 0. Si da negativo, pongan `SENSORES_INVERTIDOS 1` en `config.h` y vuelvan a cargar.
6. Con batería y **las ruedas en el aire**: `m 0.3 0` debe mover la rueda **izquierda hacia adelante** y `m 0 0.3` la **derecha hacia adelante**. Si alguna gira al revés: `set inv_izq 1` o `set inv_der 0` y `save`.
7. `bat` con la batería cargada: comparar con el multímetro. El divisor y el ADC pueden diferir ±0.1–0.2 V.
8. `perf`: la lectura de sensores debería tardar menos de 1.5 ms y el ciclo, menos de 2.5 ms.
9. Calibrar y correr primero con `vbase` 0.25. Subir `vbase` y afinar `kp`/`kd` en la pista con `tel 1`.

Datos que siguen sin medirse: distancia de la barra al eje (`DIST_SENSOR_EJE_MM`, EM-06), paso real de los sensores, sentido de los motores, corriente de bloqueo del N20 (`m_R`), umbrales de batería (definirlos con Alan) y las ganancias en la pista.
