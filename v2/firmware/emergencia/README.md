# Firmware del prototipo de EMERGENCIA — versión 2.2 (vigente)

**Estado (20 nov 2026):** completo, compilado sin advertencias propias para **ESP32 Dev Module** con arduino-esp32 **3.3.12** y **2.0.17**, y con **1773/1773** comprobaciones en PC (última ejecución exitosa; la repetición posterior quedó bloqueada por Windows, sección 9). La versión 2.2 trabaja con **6 sensores** (SEN1–SEN6 en C0–C5; sección 9). La versión 2.1 agregó un **turbo de recta** opcional, apagado de fábrica (sección 6.1): sus pruebas en C++ solo compilaron y lo valida un modelo en Python. **Todavía no se ha cargado en el robot.** Todo lo que depende del montaje real se ajusta por consola, sin recompilar (sección 4).

**Hardware (no cambia):** ESP32 DevKit de 30 pines, DRV8833, 2 motores N20 de 6 V sin encoder, **6 TCRT5000** con CD74HC4067 (SEN1–SEN6 en C0–C5; C6–C15 sin usar), MP1584 a 5 V (lógica y sensores) y MP1584 a 6 V (motores), botones START y CAL, y medición de batería. **No hay** zumbador, ventilador ni `nFAULT`.

**Fuente de verdad:** [`GUIA-FIRMWARE.md`](../../electronica/prototipo-emergencia/GUIA-FIRMWARE.md) y `robot_emergencia_unificado.kicad_sch`. `pruebas/verificar_pines.py` comprueba que `config.h` coincide con el esquema.

---

## 1. Archivos del firmware final

Todo está en `v2/firmware/emergencia/emergencia/`. Arduino IDE necesita que los archivos estén en la misma carpeta que el `.ino`.

| Archivo | Qué hace | Origen |
|---|---|---|
| `emergencia.ino` | Programa principal: ciclo de control a 400 Hz, paradas, consola USB, memoria, prueba de motores y `autocal` | Nuevo |
| `config.h` | **Pines** (iguales al esquema) y valores **iniciales** de lo que depende del montaje | Nuevo |
| `hw.h`, `hw.cpp` | Capa del ESP32: mux optimizado, ADC, PWM (LEDC 2.x y 3.x), botones, LED, watchdog | Nuevo |
| `utiles.h` | Bits del mux, orden físico, máscara de sensores, batería, lectura estricta de números y antirrebote | Nuevo |
| `autocal.h`, `autocal.cpp` | Autocalibración girando sobre la línea, guiada por los sensores | Nuevo |
| `ajustes.h`, `ajustes.cpp` | 48 parámetros + 5 del turbo, con rango y ayuda, coherencia, perfiles y guardado con CRC32 (el turbo en su propia clave de memoria) | Adaptado |
| `estados.h`, `estados.cpp` | Máquina de estados: arranque diferido y todas las paradas con su motivo | Adaptado |
| `indicadores.h`, `indicadores.cpp` | Patrones del LED integrado (GPIO2) | Adaptado |
| `motor.h`, `motor.cpp` | Tope de PWM, rampas de aceleración y frenado, y límite de corriente estimada | Adaptado |
| `control.h`, `control.cpp` | Control de línea: PID, freno en curva, retención en huecos, búsqueda y turbo de recta (2.1) | Lógica V1 probada + turbo |
| `pid.h`, `pid.cpp` | PID con anti-windup y derivada filtrada | Lógica V1, sin cambios |
| `posicion.h`, `posicion.cpp` | Calibración por sensor y posición de la línea (promedio ponderado) | Lógica V1, sin cambios |
| `filtro.h`, `filtro.cpp` | Mediana de 3 + pasa-bajas por sensor | Sin cambios de lógica |
| `parametros.h` | Constantes fijas: período, watchdog y límites de tiempo | Adaptado |

Fuera del sketch:

| Archivo | Qué es |
|---|---|
| `platformio.ini` | Entornos `esp32dev` (núcleo 3.3.12) y `esp32dev_nucleo2` (2.0.17) |
| `pruebas/test_emergencia.cpp` | Pruebas en PC, con simulación en lazo cerrado y de la autocalibración |
| `pruebas/verificar_pines.py` | Compara `config.h` con el esquema. Prohíbe WiFi/Bluetooth y los restos del firmware histórico |
| `pruebas/modelo_pista.py` | Modelo en Python del control (puerto 1:1) en la pista recta → R150 → recta → R200, sin y con turbo. Falla si sus constantes difieren del firmware |
| `pruebas/ejecutar.sh` / `ejecutar.ps1` | Corren todo lo anterior |

El firmware histórico `firmware/robot-casero/` no se usa ni se modificó.

---

## 2. Compilar y cargar

### Arduino IDE 2.x
1. *Herramientas → Placa → Gestor de placas* → **esp32** de Espressif Systems. Sirven la 3.x y la 2.0.17.
2. *Archivo → Abrir* → `v2/firmware/emergencia/emergencia/emergencia.ino`.
3. *Herramientas → Placa → esp32 →* **ESP32 Dev Module**. Dejen los valores por defecto: CPU 240 MHz, Flash 4 MB, Partition "Default 4MB with spiffs" y Upload Speed 921600.
4. *Herramientas → Puerto*: el COM del DevKit.
5. **Subir** (→). Si se queda en `Connecting....`, mantengan oprimido **BOOT** hasta que empiece a escribir.
6. *Herramientas → Monitor Serie*: **115200** baudios, cualquier fin de línea. Escriban `ver`.

No hacen falta bibliotecas externas.

### PlatformIO (PowerShell, desde la raíz del repositorio)
```powershell
cd v2\firmware\emergencia
```
```powershell
pio run -e esp32dev -t upload
```
```powershell
pio device monitor
```
- Solo compilar: `pio run -e esp32dev`. Con el núcleo 2.0.17: `pio run -e esp32dev_nucleo2 -t upload`.
- Si hay varios puertos: `pio run -e esp32dev -t upload --upload-port COM5` (cambien el número).
- Cierren el monitor serie antes de cargar: si está abierto, el puerto está ocupado.

### Pruebas en la PC (sin robot)
```powershell
cd v2\firmware\emergencia\pruebas
```
```powershell
.\ejecutar.ps1
```
Necesita g++ (MinGW/WinLibs) y Python en el PATH. En Git Bash o Linux: `./ejecutar.sh`. Barrido de ganancias: compilar `test_emergencia.cpp` con `-DBARRIDO`.
Si Windows responde "Una directiva de Control de aplicaciones bloqueó este archivo" (Smart App Control), el `.exe` de las pruebas no se puede ejecutar en esa PC. Córranlas en otra máquina o en Linux. No hace falta para cargar el robot: PlatformIO y Arduino IDE no se ven afectados.

---

## 3. Comandos USB (115200 baudios)

**En marcha la consola no responde: cualquier tecla PARA el robot.** También cancela la espera de arranque.

| Grupo | Comando | Qué hace |
|---|---|---|
| Información | `ayuda` | Lista de comandos |
| | `ver` | Versión, núcleo, MHz de la CPU y si el watchdog quedó activo |
| | `pines` | Pines compilados, inversiones y máscara |
| | `estado` | Estado, motivo de la última parada, calibración y batería |
| | `perf` | µs de lectura de sensores y ciclo máximo (luego lo reinicia) |
| Ajustes | `rangos` | Todos los parámetros con valor, rango y explicación |
| | `get` / `get <clave>` | Ver todos o uno |
| | `set <clave> <valor>` | Cambiar (rechaza texto, fuera de rango o incoherente). **No se guarda hasta `save`** |
| | `perfil seguro` / `normal` / `rapido` | Velocidad, PWM, rampas, kp, kd, freno en curva y turbo (`v_recta`) de una vez |
| | `save` / `load` / `defecto` | Guardar ajustes y calibración / recargar / volver a fábrica |
| Sensores | `sens` | Oscuridad 0–1 de izquierda a derecha, posición (mm, + = derecha) y cuántos están negros |
| | `crudo` | ADC con LED encendidos y apagados, y la diferencia (grande = blanco) |
| | `sensor <1-6>` | Prueba un TCRT5000 (SENn = canal Cn−1, de C0 a C5) con LED encendido y apagado, con diagnóstico |
| | `canal <0-15>` | Lo mismo por canal del mux |
| | `mux <0-15>` / `mux off` | Deja el mux fijo para medir SIG (GPIO34) con multímetro |
| | `emis 1` / `emis 0` | LED IR encendidos fijos (se ven con la cámara del celular) |
| | `mon sens` · `mon crudo` · `mon pos` · `mon bat` · `mon bot` | Muestra en vivo a 10 Hz; cualquier tecla lo detiene |
| Calibración | `calibrar` | Igual que el botón CAL (barrido a mano) |
| | `autocal` | Calibra **girando solo** sobre la línea (requiere las inversiones ya verificadas) |
| | `cal` | Negro, blanco y contraste de cada sensor, y cuál falta |
| Motores | `m <izq> <der> [ms]` | Prueba con **ruedas en el aire**: −1..1, 50–3000 ms (1000 por defecto); cualquier tecla corta |
| | `stop` | Suelta los motores y duerme el DRV8833 |
| Otros | `botones` | Lectura directa de START y CAL |
| | `bat` | ADC crudo de GPIO36, voltaje en VP, factor aplicado (medido) y nominal, batería ahora y filtrada, umbrales y voltaje estimado en el puente |
| | `tel 1` / `tel 0` | Telemetría en marcha a 100 Hz: `t_ms,estado,pos_mm,visible,u,ciclo_izq,ciclo_der,vbat,turbo,v` (turbo 0..1 y velocidad base efectiva) |
| | `reiniciar` | Reinicia el ESP32 |

---

## 4. Parámetros ajustables sin recompilar

Se cambian con `set <clave> <valor>`, se ven con `rangos` y quedan guardados con `save`, junto con la calibración (memoria interna con CRC32). Los valores de fábrica son el **perfil seguro**. Los marcados [P] dependen del montaje real.

| Clave | Fábrica | Rango | Qué es |
|---|---|---|---|
| **Control** | | | |
| `kp` | 0.010 | 0 – 1 | PID proporcional (por mm de error) |
| `ki` | 0 | 0 – 5 | PID integral (dejar en 0 salvo deriva constante) |
| `kd` | 0.0004 | 0 – 0.1 | PID derivativo |
| `vbase` | 0.25 | 0 – 1 | Velocidad base (fracción del máximo) |
| `freno` | 0.30 | 0 – 1 | Fracción de `vbase` que se quita en curva |
| `error_ref` | 30 | 1 – 100 | mm de error con freno de curva completo |
| `vmin_rel` | 0.50 | 0 – 1 | Piso de velocidad en curva |
| `u_max` | 0.60 | 0.05 – 2 | Saturación de la corrección del PID |
| `rueda_min` | −0.30 | −1 – 0.5 | Mínimo por rueda (negativo = puede ir en reversa en curva cerrada) |
| `tau_d` | 0.010 | 0 – 0.2 | s, filtro de la derivada |
| `t_ret` | 0.060 | 0 – 0.5 | s, retención en huecos de la línea |
| `t_busq` | 1.5 | 0 – 5 | s de búsqueda antes de parar por línea perdida |
| `u_busq` / `v_busq` | 0.35 / 0.40 | 0 – 1 | Giro y velocidad relativa durante la búsqueda |
| **Motores** | | | |
| `pwm_max` | 0.80 | 0.1 – 1 | Tope de ciclo PWM |
| `rampa` / `rampa_freno` | 4 / 8 | 0.5 – 100 | 1/s al acelerar / al frenar o invertir |
| `i_max` / `i_total` | 1.2 / 2.0 | 0.1 – 1.5 / 0.2 – 3 | A estimados por motor / entre los dos |
| `inv_izq` / `inv_der` [P] | 0 / 1 | 0 – 1 | Invierte el sentido de la rueda izquierda / derecha |
| `cruzar` [P] | 0 | 0 – 1 | Intercambia los lados (si M1 quedó a la derecha) |
| `vm_fijo` [P] | 6.0 | 2.7 – 10.8 | V reales del MP1584 de motores (medir con el multímetro) |
| `caida_reg` | 0.6 | 0 – 2 | V que pierde ese MP1584 con la batería baja |
| `m_R` / `m_ke` / `m_tau` [P] | 6 / 0.0533 / 0.08 | — | Modelo del N20 para el límite de corriente (`m_R` = 6 V / corriente de bloqueo) |
| `v_motor_max` | 6.0 | 1 – 9 | V máximos sobre el motor |
| `lento` | 1 | 0 – 1 | 1 = decaimiento lento (más lineal), 0 = rápido |
| **Sensores** | | | |
| `inv_sens` [P] | 0 | 0 – 1 | 1 = SEN1 está a la derecha. Al cambiarlo, la calibración se espeja sola |
| `mascara` [P] | 63 | 1 – 63 | Sensores en uso: bit 1 = el de la izquierda … bit 32 = el de la derecha (47 ignora el 5.º) |
| `paso_mm` [P] | 12.7 | 5 – 30 | mm entre sensores |
| `alfa` | 0.6 | 0.05 – 1 | Pasa-bajas (1 = sin filtro) |
| `sobremuestreo` / `descartes` | 2 / 1 | 1 – 4 / 0 – 3 | Lecturas ADC promediadas / descartadas al cambiar de canal |
| `t_emisor_us` / `t_mux_us` | 150 / 5 | µs | Esperas de los LED IR y del mux |
| `umbral` / `confianza` | 0.10 / 0.30 | — | Oscuridad ignorada / suma mínima para "ver" la línea |
| `contraste` | 150 | 20 – 3000 | Cuentas mínimas blanco–negro por sensor para aceptar la calibración |
| `t_negro` | 0.50 | 0 – 3 | s con todos los sensores negros (robot levantado) antes de parar; 0 = desactivado. Solo seguridad, no es meta |
| **Batería y arranque** | | | |
| `bat_baja` / `bat_critica` | 6.8 / 6.4 | 5 – 9 | V de aviso / de parada (se exige `bat_critica` < `bat_baja`) |
| `t_cal_max` / `t_cal_extra` | 15 / 1 | s | Calibración: máximo / extra tras ver contraste |
| `ac_u` / `ac_t` | 0.20 / 1.0 | — | Giro y s máximos por fase de `autocal` |
| `t_arranque` | 0.5 | 0 – 5 | s entre START y arrancar (para retirar la mano); 0 = inmediato |
| **Turbo de recta** (clave de memoria aparte) | | | |
| `v_recta` | 0 (apagado) | 0 – 1 | Velocidad en recta confiable. Si es ≤ `vbase`, el turbo está **apagado** |
| `recta_e_in` / `recta_e_out` | 3 / 6 | mm | Error para entrar a modo recta / error que lo cancela (2 ciclos seguidos). Debe cumplirse in < out |
| `recta_t_conf` | 0.15 | 0 – 2 | s seguidos de recta limpia antes de acelerar |
| `recta_t_acel` | 0.5 | 0.05 – 5 | s para subir de `vbase` a `v_recta` (la bajada es inmediata) |

Lo que **sí** requiere recompilar está en `config.h`: los pines (no se tocan; mandan el esquema), la frecuencia y resolución del PWM, el antirrebote (25 ms) y los valores de fábrica de los [P]. En `parametros.h` están el período de control (2.5 ms), el límite de ciclo (25 ms) y el watchdog (1 s).

---

## 5. Primera conexión: secuencia exacta

Cada paso dice qué debe salir. Si algo no coincide, paren y revisen el cableado contra el esquema antes de seguir.

**A. Sin batería, solo USB** (KCD1 apagado; los motores no tienen voltaje, así que no se pueden mover)
1. Carguen el firmware (sección 2) y abran el monitor serie. Al reiniciar debe salir `Robot de emergencia · emergencia 2.0 … watchdog ok`. El LED parpadea lento (ESPERA).
2. `ver` → `arduino-esp32 3.x` o `2.0.17`, `CPU 240 MHz`, `watchdog activo`.
3. `estado` → `bateria=0.00 V (solo USB)`, `cal=NO`.
4. `botones`, oprimiendo y soltando cada botón → `START=OPRIMIDO` / `CAL=OPRIMIDO`. También pueden usar `mon bot` y probar en vivo.
5. `emis 1` → con la cámara del celular se ven los 6 LED IR encendidos. `emis 0` para terminar.
6. Pongan la barra sobre **blanco**: `sensor 1` … `sensor 6`, uno por uno. Cada uno debe dar `dif` de varios cientos o más. Sobre **negro**, `dif` debe ser pequeña. Si dice "SIG casi en 0", revisen el pull-up de 10 kΩ. Si dice "casi sin reflejo" sobre blanco, revisen el LED, su 220 Ω o la altura de la barra.
7. `crudo` sobre blanco: los 6 valores de `dif` deben ser parecidos. Uno muy distinto indica un sensor mal soldado o torcido. Si uno está dañado, se puede ignorar con la máscara: `set mascara 47` ignora el 5.º.
8. **Orden de los sensores:** `mon pos` y muevan una tira negra de **izquierda a derecha** bajo la barra (mirando el robot desde atrás). `pos` debe ir de **negativo a positivo**. Si va al revés: `set inv_sens 1`. Antes de calibrar `pos` puede no aparecer; si no aparece, usen `crudo` y vean qué columna cambia: la 1.ª columna debe ser la de la izquierda.

**B. Con batería (KCD1 encendido) y RUEDAS EN EL AIRE**
9. `bat` → muestra el ADC crudo, el voltaje en VP, el factor aplicado (4.7619, medido), la batería y los umbrales. Compárenlo con el multímetro en la batería 2S definitiva (8.4 V cargada; ±0.2 V es normal). Si pasa de 8.6 V, avisa: revisen la batería o la calibración. Vean "Batería y su medición" en la sección 9.
10. `m 0.3 0` → solo la rueda **izquierda** gira, **hacia adelante**.
    - Si gira la derecha en lugar de la izquierda: `set cruzar 1` y repitan.
    - Si gira la correcta pero hacia atrás: `set inv_izq 1` (o 0 si ya estaba en 1).
11. `m 0 0.3` → solo la rueda **derecha**, **hacia adelante**. Si va hacia atrás, cambien `inv_der` (de 1 a 0, o al revés).
12. `m 0.3 0.3` → las dos hacia adelante. `m 0.3 -0.3` → el robot giraría a la **derecha** (izquierda adelante, derecha atrás).
13. `save` (guarda las inversiones).

**C. Calibración y primera vuelta**
14. Pongan el robot **centrado sobre la línea**, en el piso.
15. Calibren con **CAL** (o `calibrar`) y pasen el robot a mano de lado a lado 2–3 veces sobre la línea. El LED da 0.6 s fijo si salió bien. Con `cal`, todos los sensores deben decir `ok`. Si alguno dice `<- FALTA`, repitan con barridos más amplios.
    - Alternativa: `autocal` (el robot gira solo). Si dice "giro al revés", vuelvan a los pasos 8 y 10–12.
16. `sens` sobre la línea centrada → `pos` cerca de 0 y `visible=1`. Moviendo el robot a mano, `pos` debe seguir a la línea con el signo correcto.
17. `perf` → la lectura de sensores debe tardar < 1500 µs y el ciclo máximo < 2500 µs. Si no, bajen `sobremuestreo` a 1.
18. Primera vuelta con el **perfil seguro** (ya está de fábrica): START, retiren la mano (arranca a los 0.5 s) y estén listos para oprimir START o cualquier tecla. Si oscila (zigzag), bajen `kp` o suban `kd` (sección 6). Si se sale en curva, suban `freno` o bajen `vbase`.
19. `save`.

---

## 6. Valores iniciales y cómo ir más rápido

Los valores salen de la simulación [S]: curvas de 200 a 600 mm con la barra de 8 sensores (C++, columna de la tabla), y la pista recta → R150 → R200 con **6 sensores** (modelo Python, sección 6.1); paso 12.7 mm y un N20 **supuesto** de 1000 rpm con ruedas de 28 mm. Con otro N20 las velocidades en m/s cambian, pero el orden de los pasos es el mismo.

| Perfil | `vbase` | `v_recta` (turbo) | `pwm_max` | `rampa` / `rampa_freno` | `kp` | `kd` | `freno` | Círculos con 8 sensores, versión anterior (desvío / velocidad) |
|---|---|---|---|---|---|---|---|---|
| **seguro** (fábrica) | 0.25 | apagado | 0.80 | 4 / 8 | 0.010 | 0.0004 | 0.30 | 5.1 mm / ~0.30 m/s |
| **normal** | 0.35 | 0.42 | 0.90 | 6 / 12 | 0.010 | 0.0004 | 0.30 | 6.0 mm / ~0.46 m/s |
| **rapido** | 0.50 | 0.55 | 1.00 | 8 / 16 | 0.012 | 0.0006 | 0.40 | 6.5 mm / ~0.70 m/s |

**Primera prueba segura:** perfil `seguro`, más `t_arranque 0.5`, `t_negro 0.5` y `t_busq 1.5` (todos de fábrica).

**Para buscar más velocidad** (un cambio a la vez, probando cada uno en la pista con `tel 1`):
1. `perfil normal`, una vuelta. Luego `perfil rapido`.
2. Subir `vbase` de 0.05 en 0.05. En la simulación, `vbase 0.60` con `kp 0.012–0.014` y `kd 0.0004` todavía sigue bien (≤ 7.3 mm de desvío).
3. **Zigzag en recta:** bajar `kp` 0.002, o subir `kd` 0.0002. En la simulación, `kd` ≥ 0.0008 con `kp` 0.014 ya empieza a oscilar.
4. **Se sale en curvas cerradas:** subir `freno` (0.4–0.5), bajar `error_ref` (20–25 mm) o subir `kp`.
5. **Pierde la línea en curvas muy cerradas:** bajar `rueda_min` (−0.5) para que la rueda interior frene más.
6. **Tarda en acelerar:** subir `rampa` (8–12). Mantener `rampa_freno` ≥ `rampa`.
7. Si el robot se apaga o se reinicia al acelerar (caída de batería o del regulador), bajar `rampa`, `i_max` o `i_total`.

### 6.1 Turbo de recta (versión 2.1)
Sin encoders: decide solo con los sensores (error, confianza y derivada del error), el estado, la batería y el tiempo del ciclo (`control.cpp`, `ControladorLinea::actualizar`).

- **Entra** cuando durante `recta_t_conf` (0.15 s) seguidos se cumple todo esto:
  - línea visible con confianza ≥ 1.2;
  - |error| < `recta_e_in` (3 mm);
  - |derivada del error| < 40 mm/s, con una derivada propia filtrada a 40 ms, distinta de la del PID;
  - el programa lo permite: estado **SIGUIENDO** (no RECUPERACIÓN), batería sin aviso de baja ni crítica, ciclo de control ≤ 5 ms, sin "todo negro", sin tecla USB pendiente y sin diagnóstico.
- **Acelera despacio:** la velocidad base sube de `vbase` a `v_recta` en `recta_t_acel` (0.5 s).
- **Se cancela al instante** (vuelve a `vbase` en el mismo ciclo; la caída física la dan `rampa_freno` y el freno en curva):
  - no ve la línea (también en un hueco);
  - confianza < 0.8;
  - búsqueda;
  - permiso retirado: batería, ciclo, START, CAL o tecla USB.
- **Se cancela tras 5 ms** (2 ciclos seguidos, para ignorar picos de ruido) si |error| > `recta_e_out` (6 mm), o si el error ya pasó 3 mm y se aleja del centro a > 150 mm/s.
- **Histéresis:** entrar es más estricto que seguir; con 3–6 mm de error no entra, pero si ya estaba en recta, sigue.
- **No toca** el PID, el PWM máximo, las rampas, el límite de corriente, el watchdog, las paradas, la búsqueda, las inversiones ni la calibración.

**Modelo de pista con 6 sensores** (`pruebas/modelo_pista.py`: recta 1 m → R150 → recta 0.6 m → R200 → recta 0.6 m, ruido de sensores y picos; N20 de 1000 rpm supuesto):

| Perfil | Vuelta sin / con turbo | Desvío máx. sin / con | Velocidad al entrar a R150 | El turbo se cancela, dentro de la curva | Pérdidas de línea |
|---|---|---|---|---|---|
| seguro | 9.55 s / (apagado) | 6.2 mm | 0.32 m/s | — | 0 |
| normal (`v_recta` 0.42) | 6.16 s / **5.72 s (−7 %)** | 8.1 / 8.1 mm | 0.50 → 0.60 m/s | 50 mm (R150), 67 mm (R200) | 0 |
| rápido (`v_recta` 0.55) | 4.00 s / **3.88 s (−3 %)** | 8.8 / 9.4 mm | 0.79 → 0.87 m/s | 54 mm, 70 mm | 0 |

- **Por qué la cancelación dentro de la curva es aceptable:** la barra va 100 mm por delante del eje, así que cancelar a < 100 mm de la entrada frena antes de que el eje llegue a la curva.
- **Cómo se eligieron los valores** (barrido con 5 semillas de ruido): en normal, más de 0.45 empieza a subir el desvío; en rápido, 0.60 sube 1.3 mm y 0.65 satura las ruedas.
- **Ruido triple** (3 % de picos) en una recta de 4 m: el turbo no parpadea (1 y 3 cambios).
- **Línea borrada 120 ms:** busca, la reencuentra y termina.

**Cómo usarlo:**
- `perfil normal` o `perfil rapido` lo activan; `perfil seguro` o `set v_recta 0` lo apagan.
- `save` lo guarda en su propia clave de memoria; las inversiones y la calibración no cambian de formato.
- Con `get` o `estado` se ve si está activo; con `tel 1`, las columnas `turbo` y `v`.

**Primera prueba física con turbo:** solo después de que el robot complete vueltas estables con el mismo perfil **sin** turbo (`set v_recta 0`). Luego actívenlo y con `tel 1` comprueben:
- que `turbo` suba de 0 a 1 solo en rectas largas;
- que vuelva a 0 **antes** de que el eje llegue a cada curva;
- que en curvas cerradas no aparezca RECUPERACIÓN.

Si se sale o aparece RECUPERACIÓN, bajen `v_recta` 0.03 o suban `recta_t_conf`.

---

## 7. Cómo funciona

**Ciclo de control (400 Hz):**
1. **Lectura:** LED IR apagados → los 6 canales C0–C5 (luz ambiente); LED encendidos → los mismos 6 canales. En cada canal: espera del mux, `descartes` lecturas tiradas y `sobremuestreo` lecturas promediadas. Solo se escriben los bits S0–S2 que cambian; S3 queda fijo en 0.
2. **Tratamiento:** reflectancia = apagados − encendidos (sin luz ambiente), luego mediana de 3 + pasa-bajas por sensor, normalización con la calibración (0 = blanco, 1 = negro) y la máscara.
3. **Posición:** promedio ponderado (mm, + = derecha).
4. **Control:** PID con anti-windup y derivada filtrada, freno proporcional al error en curva, retención en huecos (`t_ret`), búsqueda girando hacia el último lado visto (`t_busq`) y, si está activo, turbo de recta (sección 6.1).
5. **Motores:** tope (`pwm_max`), rampas, límite de corriente estimada por motor y total → DRV8833 en decaimiento lento a 20 kHz.

**Paradas** (todas imprimen su motivo; `estado` lo repite):

| Causa | Resultado |
|---|---|
| START, CAL o cualquier tecla por USB en marcha | PARADA: frena 0.3 s, luego suelta los motores y duerme el DRV8833 |
| Línea perdida (fin de `t_busq`) | PARADA |
| Todos los sensores negros más de `t_negro` (robot levantado) | PARADA. Es solo de seguridad, **no** es detección de meta (ver 7.1) |
| Batería < `bat_critica` sostenida 0.5 s, o sin batería en marcha | ERROR 1: frena y duerme el puente |
| Un ciclo de control de más de 25 ms en marcha | ERROR 2: frena y duerme el puente |
| `loop()` colgado más de 1 s | El **watchdog** reinicia el ESP32. Los GPIO quedan en alta impedancia y el LEDC se detiene; los pull-down internos del DRV8833 (nSLEEP e IN1–IN4) lo dejan dormido; `setup()` pone primero nSLEEP = 0 y los 4 PWM en 0 |

**Arranque:** `setup()` deja nSLEEP en 0 y las 4 entradas del puente en 0 antes de cualquier otra cosa. El puente solo despierta en LISTO, en marcha y durante el frenado. START se rechaza sin calibración, sin batería, con batería crítica o con un diagnóstico activo.

| LED (GPIO2) | Significado |
|---|---|
| Parpadeo lento (1 Hz) | ESPERA |
| 5 Hz; 10 Hz en los últimos 3 s | Calibrando |
| Fijo | LISTO (o calibración buena) |
| 12 Hz | START oprimido, esperando `t_arranque` |
| Encendido / apagado en marcha | Ve / no ve la línea |
| 8 Hz | Buscando la línea |
| 4 Hz | PARADA |
| 1 o 2 destellos + pausa | ERROR 1 (batería) o ERROR 2 (ciclo) |
| 2 apagones cada 3 s (en ESPERA o LISTO) | Batería baja |

### 7.1 Fin de la vuelta: parada manual con START
Confirmado por el equipo (20 nov 2026): la pista **no requiere detección automática de meta**, y el firmware no la tiene ni se le agregará. El equipo detiene el robot a mano después de completar la vuelta.

**Procedimiento normal al terminar:**
1. Cuando el robot completa la vuelta, el operador oprime **START** una vez.
2. El robot pasa a PARADA con el motivo "boton START": frena 0.3 s, luego suelta los motores y duerme el DRV8833.
3. Confirmen que se detuvo:
   - las ruedas están quietas;
   - el LED parpadea a 4 Hz (PARADA);
   - si hay consola, `estado` dice `ultima parada: boton START`.
4. Con los motores detenidos, ya pueden retirar el robot de la pista. Para guardarlo, apaguen el KCD1.

**Cuidados:**
- **No vuelvan a oprimir START para "asegurarse".** Desde PARADA, un segundo START pasa a LISTO, y un tercero lo arranca a los `t_arranque` (0.5 s). Si se oprimió de más: con START o cualquier tecla por USB durante la espera se cancela; si no, apaguen el KCD1.
- **`t_negro` no es detección de meta.** Es solo una parada de seguridad para cuando el robot queda levantado en marcha: los sensores sin piso leen "negro" y, tras 0.5 s, pasa a PARADA con el motivo "todos los sensores negros (robot levantado?)". No lo usen para terminar la vuelta: durante esos 0.5 s las ruedas siguen girando en la mano. El método normal es START.
- Las demás paradas (línea perdida, batería, ciclo, watchdog, sección 7) son de seguridad y tampoco son una meta.

---

## 8. Revisión del commit `de1290f` (firmware 1.0) y correcciones

| # | Problema encontrado | Riesgo | Corrección en 2.0 |
|---|---|---|---|
| 1 | Sin watchdog: si `loop()` se cuelga, el PWM por hardware sigue moviendo los motores (el chequeo de ciclo solo corre si `loop()` corre) | Robot sin control | Watchdog de 1 s en la tarea de `loop()` (IDF 4.4 e IDF 5) |
| 2 | Robot levantado: sin piso, los TCRT5000 leen "negro" en todos, la línea parece centrada y sigue a toda velocidad | Ruedas a tope en la mano | `t_negro`: todos negros más de 0.5 s → PARADA |
| 3 | ERROR (batería o ciclo) soltaba los motores a toda velocidad, sin frenar | Sigue rodando | ERROR frena 0.3 s y luego duerme el puente |
| 4 | Si la batería se desconecta en marcha, el estado seguía en SIGUIENDO | Estado imposible | → ERROR 1 "sin batería" |
| 5 | `set kp x` dejaba kp = 0 (`atof`). Lo mismo con `canal x` (canal 0) | Robot sin control tras un error de tecleo | Lectura estricta: rechaza texto, NaN, fuera de rango e incoherencias (`bat_critica` ≥ `bat_baja`, inversiones que no sean 0/1…) |
| 6 | START arrancaba en el acto, con la mano encima | Golpe o arranque torcido | `t_arranque` (0.5 s); START o cualquier tecla lo cancela |
| 7 | Inversión de sensores, paso, umbrales y contraste solo cambiaban recompilando | Mañana habría que recompilar | Todo por consola. Al cambiar `inv_sens` la calibración se espeja sola |
| 8 | Sin forma de ignorar un sensor dañado | Un TCRT5000 malo invalidaba la calibración | `mascara` |
| 9 | Mux: escribía los 4 bits en cada canal y no descartaba la primera lectura (el ADC conserva carga del canal anterior; fuente de 10 kΩ) | Lecturas cruzadas entre sensores | Solo cambian los bits necesarios; `descartes` y `t_mux_us` |
| 10 | La rampa limitaba igual al frenar que al acelerar | Frenado lento antes de curvas | `rampa_freno` separada |
| 11 | El puente se suponía siempre a 6 V aunque la batería ya no alcanzara al regulador | Límite de corriente mal estimado | `v_puente = min(vm_fijo, vbat − caida_reg)` |
| 12 | `m` permitido con batería crítica; `canal` movía el mux fijado con `mux` | Pruebas engañosas | Bloqueado / se restaura el canal |
| 13 | CAL en marcha no hacía nada | Un botón menos para parar | CAL también para |
| 14 | Con fin de línea "CR" en el Monitor Serie no se ejecutaba ningún comando | Consola "muerta" | Acepta LF, CR y CRLF |
| 15 | Telemetría a 100 Hz podía bloquear esperando al UART | Falso ERROR 2 | Búfer de envío de 2 KB |
| 16 | Restos del histórico: namespace `casero`, comentarios "MP1584 #2", "DRV8874", "placa fenólica", valores por defecto de otro robot en `control.cpp` | Confusión | Limpiado; `verificar_pines.py` falla si vuelven a aparecer |

Revisado sin problemas: pinout (14 señales = esquema), selección del mux (S0 = LSB), signos (error > 0 = línea a la derecha → rueda izquierda más rápida), saturación diferencial de ruedas, anti-windup del PID, resta de luz ambiente con fototransistor con pull-up, PWM 100 % real en los dos núcleos y ausencia de condiciones de carrera (todo corre en la tarea de `loop()`, sin interrupciones propias).

---

## 9. Qué se verificó y qué falta

### Verificado por compilación (20 nov 2026, desde cero, PlatformIO)
| Entorno | Resultado |
|---|---|
| `esp32dev`: arduino-esp32 3.3.12 (IDF 5) | 11 fuentes, **0 advertencias propias** con `-Wall -Wextra`; flash 324 943 B (24.8 %), RAM 24 072 B (7.3 %) |
| `esp32dev_nucleo2`: arduino-esp32 2.0.17 (IDF 4.4) | 11 fuentes, **0 advertencias propias**; flash 326 085 B (24.9 %), RAM 23 472 B (7.2 %) |

La compilación confirma que el watchdog usa la API correcta en cada núcleo: `esp_task_wdt_reconfigure`/`init(&cfg)` en IDF 5 y `esp_task_wdt_init(segundos, panic)` en IDF 4.4. También confirma que los dos tienen `CONFIG_ESP_SYSTEM_PANIC_PRINT_REBOOT` (reinicio inmediato al vencer). No se compiló dentro de Arduino IDE en sí: usa los mismos núcleos y la misma placa, pero la primera carga lo confirmará.

### Verificado por pruebas en PC
| Prueba | Resultado |
|---|---|
| `pruebas/ejecutar.sh` (g++ 16.2, `-Wall -Wextra -Werror`), **última ejecución exitosa: 20 nov 2026, 07:14** | **1773/1773** comprobaciones |
| … dentro de eso: simulación en lazo cerrado, 3 perfiles × 3 curvas | Nunca pierde la línea; desvío máx. 5.1 / 6.0 / 6.5 mm |
| … dentro de eso: simulación de `autocal` | Lista en 0.6 s y centrada (+2°). Falla correctamente sin línea (1 s) y con los motores al revés (aborta enseguida, sin calibración falsa) |
| `verificar_pines.py` (Python) | 14 señales = esquema; LED en pata libre; 24 archivos sin WiFi/Bluetooth ni restos del histórico |
| `v2/herramientas/validar_repo.py` (clon LF) | 0 errores, 2 avisos de inventario que ya existían |

**La repetición posterior NO se cuenta como aprobada:** Windows (Smart App Control) bloqueó el `.exe` recién compilado ("Una directiva de Control de aplicaciones bloqueó este archivo"). Las pruebas sí volvieron a **compilar** sin advertencias con `-Werror`, pero no se pudieron **ejecutar**. La evidencia válida es la ejecución de las 07:14. Hasta el commit `b4eb31f` no cambió ningún archivo que esas pruebas compilan; solo cambiaron `hw.cpp` (capa del ESP32, que no entra en las pruebas de PC), Python y documentación.

**Cambio de batería (después de `b4eb31f`): solo compilado, NO ejecutado.** Se agregaron a `test_emergencia.cpp` cuatro comprobaciones:
- 2100 mV × 4.7619 ≈ 10.0 V;
- umbrales ordenados para 2S Li-ion;
- `bat_critica` ≥ 3.0 V/celda;
- 8.6 V dentro del rango del ADC.

Compilan con `-Werror`, pero Windows volvió a bloquear el `.exe` (código 126). La 1773/1773 no las incluye. Los cálculos de la tabla de batería se hicieron a mano con los mismos valores.

### Cambio a 6 sensores (versión 2.2, 21 nov 2026)
**Montaje asumido por el equipo:**
- SEN1 → C0 … SEN6 → C5, con SEN1 a la izquierda y SEN6 a la derecha.
- C6–C15 no se usan.
- No cambian el mux ni sus pines (S0 = 25, S1 = 26, S2 = 27, S3 = 33, SIG = 34, EMIT_EN = 13), ni los motores, la batería, el PID, el turbo, el watchdog, las paradas o la consola.

| Qué | Detalle |
|---|---|
| Firmware | `NUM_SENSORES = 6` y `MASCARA_TODOS = 63` (`config.h`). El barrido, los filtros, la calibración, la máscara, la geometría (x = ±6.35, ±19.05, ±31.75 mm con paso 12.7) y "todo negro" usan `NUM_SENSORES` |
| Memoria | El bloque guardado no cambia de formato. Si lo guardado trae una calibración de otra cantidad de sensores (la versión de 8), al arrancar avisa `AVISO: calibracion guardada de 8 sensores descartada (ahora 6): RECALIBRAR`. **Se conservan** inversiones, PID, batería y demás ajustes, y la máscara vuelve a 63 (`adaptar_a_sensores`). El turbo no se toca |
| Pendiente de medir [P] | `paso_mm` (12.7 supuesto, igual que la barra de 8) y el orden físico (`inv_sens`). Ambos se ajustan por consola |
| Esquema | Todavía dibuja SEN7/SEN8 en C6/C7 (D-V2-41). `verificar_pines.py` lo reporta como aviso: el firmware no los lee. Actualizarlo es el pendiente EM-09 |

**Evidencia:**

| Prueba | Resultado |
|---|---|
| `verificar_pines.py` | Exactamente 6 sensores, SEN1..SEN6 en C0..C5 según el esquema; el barrido no lee C6..C15; pines y mux iguales |
| Modelo Python con 6 sensores (lee `NUM_SENSORES` de `config.h`) | **Ejecutado, todo OK**: los 3 perfiles, con y sin turbo, completan la pista sin perder la línea (también la R150); desvío máx. 6.2 / 8.1 / 9.4 mm, prácticamente igual que con 8. Tras borrar la línea 120 ms, el perfil normal buscó 2 veces y terminó |
| Pruebas C++ (`prueba_seis_sensores` y las demás, con `N = NUM_SENSORES`) | **Solo compiladas** con `-Werror` (Windows bloquea el `.exe`; sin WSL). **No cuentan como aprobadas** |
| `pio run -e esp32dev` y `-e esp32dev_nucleo2` | Compilan sin advertencias propias |

### Turbo de recta (versión 2.1): qué se ejecutó y qué no
| Evidencia | Estado |
|---|---|
| Pruebas C++ anteriores (`test_emergencia.cpp`, 20 nov 07:14) | **1773/1773 ejecutadas**, sin el turbo y con 8 sensores |
| Pruebas C++ nuevas del turbo (`prueba_turbo_control`, `prueba_turbo_ajustes`, `prueba_pista`) | **Solo compiladas** con `-Werror`. Windows bloquea el `.exe` y WSL no está instalado. **No cuentan como aprobadas** |
| Modelo Python (`pruebas/modelo_pista.py`) | **Ejecutado, todas sus comprobaciones OK**. Es un puerto 1:1 de la lógica; antes de simular comprueba que 10 constantes del turbo, 31 ajustes y los 3 perfiles coinciden con `control.h`, `ajustes.h` y `ajustes.cpp` |
| Compilación `esp32dev` y `esp32dev_nucleo2` | Sin advertencias propias |
| Robot físico | **Pendiente**: ver "Primera prueba física con turbo", sección 6.1 |

### Batería y su medición (20 nov 2026)
**Batería definitiva:** pack 2S de 18650 Li-ion, 7.4 V nominal, ~2500 mAh. Cargada: 8.4 V (4.2 V por celda).

| Dato | Valor | Origen |
|---|---|---|
| Divisor del esquema | R1 = 100 kΩ (VBAT_SW → VBAT_SENSE), R2 = 33 kΩ (→ GND), C3 = 100 nF; mide después del KCD1, sin diodo | Esquema unificado (**nominal**) |
| Factor nominal | 133 / 33 = **4.030** (`DIVISOR_BATERIA`, solo referencia) | Calculado del esquema |
| Voltaje medido en la fuente de calibración | **10.0 V** | Multímetro (equipo) |
| Voltaje medido en VP / GPIO36 | **2.1 V** | Multímetro (equipo); misma medición, mismo GND, KCD1 encendido (**confirmado**) |
| Factor empírico | 10.0 / 2.1 = **4.7619**, offset 0 V | Calculado de las dos medidas |
| Lo que usa el firmware | `FACTOR_BATERIA = 4.7619` en `config.h` | Código. Con 2.1 V en GPIO36, `bat` reporta ≈ 10.0 V (comprobado en PC) |
| Lectura esperada con la batería definitiva | 8.4 V → 1.76 V en VP; 6.4 V → 1.34 V | Calculado con el factor medido; dentro del rango del ADC |

**Los 10.0 V son solo el punto de calibración**, no el voltaje normal de la batería definitiva, que nunca pasa de 8.4 V. El factor medido no coincide con el nominal (con 4.030, 2.1 V serían 8.46 V): el divisor soldado no es exactamente 100k/33k. El factor está en una constante de `config.h`, no en la memoria del ESP32, así que **no invalida** las inversiones ni la calibración ya guardadas. Para volver al nominal se cambia `FACTOR_BATERIA` por `DIVISOR_BATERIA` y se recompila.

**Umbrales (no cambiaron, son adecuados para 2S Li-ion):**

| Umbral | Valor | Por celda | Por qué |
|---|---|---|---|
| `bat_baja` | 6.8 V | 3.4 V | Aviso cuando queda poca carga. Queda muy por encima del corte de una 18650 (2.5–3.0 V/celda) |
| `bat_critica` | 6.4 V sostenidos 0.5 s | 3.2 V | Para el robot en marcha (ERROR 1). Deja margen sobre el corte de la celda y para la caída bajo carga; con más carga, el regulador de 5 V del ESP32 sigue regulando |
| Aviso de sobrevoltaje | > 8.6 V (`BAT_MAX_2S`) | 4.3 V | 8.4 V cargada + ~0.2 V de tolerancia (ADC ±1–2 % y calibración de un solo punto). **Solo avisa** por consola (al cruzar el valor y en `bat` / `estado`); no bloquea nada |

**Todavía NO está calibrada definitivamente:** falta comparar `bat` con el multímetro **usando la batería final 2S de 7.4 V**, a dos cargas distintas (por ejemplo, llena ≈ 8.4 V y a media carga ≈ 7.4 V). Si difieren más de ±0.2 V, se ajusta `FACTOR_BATERIA` con un nuevo punto medido y se recompila.

### Pendiente de verificar en el robot físico (EM-08)
- **Watchdog:** `ver` debe decir `watchdog activo`. Que el reinicio por cuelgue deje el DRV8833 dormido sale de la ficha y del código; no se ha visto en el robot:
  - en el reinicio el ESP32 deja los GPIO en alta impedancia y el LEDC se detiene;
  - el DRV8833 tiene pull-down interno en nSLEEP y en IN1–IN4;
  - `setup()` llama primero a `hw::iniciar()`, que pone nSLEEP = 0 y los 4 PWM en 0.

  Hasta que vence (1 s) el PWM sigue como estaba. Comprobación sugerida: multímetro en nSLEEP (GPIO16) al oprimir EN, debe dar ~0 V.

Además, la secuencia de la sección 5. En especial:
- el orden de los sensores (`inv_sens`);
- las inversiones de motores (`inv_izq`, `inv_der`, `cruzar`);
- los tiempos reales (`perf`);
- `vm_fijo` medido;
- la corriente de bloqueo del N20 (`m_R`);
- la distancia de la barra al eje y el paso real;
- `bat` contra el multímetro con la batería 2S Li-ion definitiva (calibración definitiva) y los umbrales con Alan;
- las ganancias en la pista.
