# Guía de firmware — Prototipo de EMERGENCIA (placa perforada)

**Para:** Alejandro y cualquier integrante del equipo. **Estado:** documento de trabajo, 19 nov 2026.
**Esquema de referencia:** `robot_emergencia_unificado.kicad_sch` (principal + 8 sensores en una sola hoja A2).

> **Permisos:** Alan autorizó el 19 nov que **cualquier integrante del equipo con acceso al repositorio** modifique cualquier archivo, incluido el firmware (EM-05 queda autorizado). Siguen vigentes las reglas de seguridad: trabajar en la rama `seguidor-caseroV2`, no tocar `main`, sin merges ni force push. **EM-07 resuelto:** el firmware vigente está en `v2/firmware/emergencia/` (adaptado del histórico, sección 6).

---

## 1. Qué cambió frente al diseño V2 aprobado

| Tema | Diseño V2 (PCB) | Emergencia (este esquema) |
|---|---|---|
| Sensores | 12 TCRT5000 | **8 TCRT5000**, canales C0–C7 del mux (decisión D-V2-41) |
| Ventilador | GPIO17 (`FAN_PWM`) controla el MOSFET | **Sin ventilador** (propuesta EM-01, pendiente de OK). GPIO17 queda libre |
| Botón RESET | SW4 a EN | **Sin botón**; se usa el botón EN del DevKit |
| Fusible y conector de batería | PTC F1 y JST-RC | **Ninguno** (D-V2-45): batería → KCD1 → MP1584, cables soldados directo |
| Pines GPIO del ESP32 | — | Los mismos del diseño V2 aprobado para START, CAL, EMIT_EN, SIG, S0–S3, motores y batería |

**Qué significa para el código:** solo cambian la cantidad de sensores (12 → 8) y, si se confirma EM-01, la línea del ventilador. El resto de los GPIO se mantiene.

---

## 2. Asignación de pines del ESP32 (DevKit 30 pines)

Nombres GPIO leídos del símbolo del ESP32 en el propio esquema.

| Señal | GPIO | Pin del DevKit | Dirección | Función |
|---|---|---|---|---|
| `SIG` | **34** | 4 (VDET_1, ADC1_CH6) | entrada analógica | Lectura del sensor elegido por el mux |
| `S0` | **25** | 8 | salida | Bit 0 de selección del mux |
| `S1` | **26** | 9 | salida | Bit 1 de selección del mux |
| `S2` | **27** | 10 | salida | Bit 2 de selección del mux |
| `S3` | **33** | 7 | salida | Bit 3 de selección del mux |
| `EMIT_EN` | **13** | 13 | salida | Enciende los LED IR de los sensores (alto = encendidos) |
| `START` | **4** | 20 | entrada, pull-up interno | Botón START a GND |
| `CAL` | **14** | 11 | entrada, pull-up interno | Botón CAL a GND |
| `VBAT_SENSE` | **36** | 2 (VP, solo entrada) | entrada analógica | Divisor de batería 100 kΩ / 33 kΩ (8.4 V → 2.08 V) |
| `DRV_SLEEP` | **16** | 21 | salida | Habilita el DRV8833 (nSLEEP: alto = activo) |
| `AIN1` | **19** | 25 | salida PWM | Motor izquierdo, IN1 |
| `AIN2` | **21** | 26 | salida PWM | Motor izquierdo, IN2 |
| `BIN1` | **22** | 29 | salida PWM | Motor derecho, IN3 |
| `BIN2` | **23** | 30 | salida PWM | Motor derecho, IN4 |
| `FAN` | 17 | 22 | — | **Libre** en emergencia (sin ventilador) |

Alimentación del DevKit: pin 15 (5V) y pin 16 (3V3), GND en el pin 14 y 17.

---

## 3. Sensores: 8 TCRT5000 con el multiplexor CD74HC4067

> **Montaje vigente: 6 sensores (equipo, 21 nov 2026).** El firmware usa SEN1–SEN6 en C0–C5; C6–C15 no se leen. SEN7/SEN8 (C6/C7) siguen dibujados en el esquema y en esta guía, pero no se montan: actualizar el esquema es el pendiente EM-09. El mux y sus pines no cambian.


### Conexiones
- Cada sensor `SEN n` entra al canal **C(n−1)** del mux. Es decir: SEN1 → C0, …, SEN8 → C7. C8–C15 no se usan.
- El mux recibe `S0–S3` del ESP32 y devuelve la lectura por `SIG` (GPIO34).
- `EN` del mux va a GND: el mux siempre está habilitado.
- Los LED de los sensores van a **+5 V** (regulador U1), **no** a 3.3 V. Su cátodo común pasa por el 2N2222 (Q1), que controla `EMIT_EN`.

### Cómo elegir un sensor
Para leer el sensor `n` (0 a 7), escribe el número en binario en los pines de selección:

| Sensor | S3 (GPIO33) | S2 (GPIO27) | S1 (GPIO26) | S0 (GPIO25) |
|---|---|---|---|---|
| SEN1 (C0) | 0 | 0 | 0 | 0 |
| SEN2 (C1) | 0 | 0 | 0 | 1 |
| SEN3 (C2) | 0 | 0 | 1 | 0 |
| SEN4 (C3) | 0 | 0 | 1 | 1 |
| SEN5 (C4) | 0 | 1 | 0 | 0 |
| SEN6 (C5) | 0 | 1 | 0 | 1 |
| SEN7 (C6) | 0 | 1 | 1 | 0 |
| SEN8 (C7) | 0 | 1 | 1 | 1 |

S3 es el bit más significativo y S0 el menos significativo (es el orden estándar del CD74HC4067).

### Secuencia de lectura sugerida
1. Apagar LED: `EMIT_EN = 0`. Leer los 8 sensores con LED apagados (para restar la luz del ambiente).
2. Encender LED: `EMIT_EN = 1`. Esperar un tiempo corto para que el fototransistor se estabilice.
3. Para cada sensor: poner S0–S3, esperar un instante corto a que el mux conmute, y leer `SIG` con el ADC.
4. Apagar LED al terminar, si no se usan.

El firmware vigente (`v2/firmware/emergencia/`, `hw.cpp`) hace esta secuencia con sobremuestreo y un tiempo de encendido del emisor ajustable (`t_emisor_us`).

### Orden físico
En el esquema, SEN1 está a la izquierda y SEN8 a la derecha. **Confirmar con Alan** si ese orden coincide con la izquierda y la derecha reales del robot, porque depende de cómo se mire la barra. En el firmware vigente se corrige sin recompilar con `set inv_sens 1` y `save` (`v2/firmware/emergencia/README.md`, sección 5); equivocarse en la fila de sensores hace que el robot gire al revés.

---

## 4. Motores y driver (DRV8833)
- Motor izquierdo: `AIN1` (GPIO19), `AIN2` (GPIO21).
- Motor derecho: `BIN1` (GPIO22), `BIN2` (GPIO23).
- `DRV_SLEEP` (GPIO16) debe quedar en **0** al arrancar y pasar a **1** solo cuando el firmware esté listo.
- `ULT` (nFAULT) no está conectado (pendiente P13 del diseño V2). No dependas de él para detectar fallas.
- Ambos motores van a 6.0 V (regulador U2), no a la batería directa.

---

## 5. Botones, batería y LED
- **START** (GPIO4) y **CAL** (GPIO14): botones a GND, se leen con pull-up interno.
- **Batería** (GPIO36): el voltaje real es `lectura × (100 + 33) / 33`. Con 8.4 V en la LiPo, el pin lee 2.08 V.
- **LED del DevKit:** no hay zumbador ni LED extra en el diseño V2 (D-V2-05). No reutilices GPIO4 para nada más: es el botón START.

---

## 6. Base de código (EM-07)

No hay zumbador en este robot (D-V2-05): ni en el diseño V2 ni en el de emergencia. GPIO4 es el botón START.

El repositorio tiene `firmware/robot-casero/`, marcado como **HISTÓRICO** (`v2/docs/ESTADO-DOCUMENTOS.md`). Su `config.h` difiere del esquema unificado en:

| Señal | Esquema unificado | `firmware/robot-casero/config.h` | Qué hacer al adaptarlo |
|---|---|---|---|
| START | GPIO4 | GPIO18 | Cambiar a GPIO4 |
| Zumbador (`PIN_ZUMBADOR` GPIO4, `CANAL_ZUMB`) | no existe | GPIO4 | **Quitarlo** (también su código en indicadores/motor si lo usan) |
| `NUM_SENSORES` (modo mux) | 8 (montaje vigente: **6**, C0–C5) | 12 | El firmware vigente usa 6 (canales C0–C5) |
| Motores AIN/BIN, `PIN_NSLEEP` | 19, 21, 22, 23, 16 | 19, 21, 22, 23, 16 | Coinciden |
| Mux S0–S3, SIG, emisores, CAL, batería | 25, 26, 27, 33, 34, 13, 14, 36 | igual | Coinciden |

**Base elegida (19 nov, EM-07): adaptar.** El firmware vigente es `v2/firmware/emergencia/` (`emergencia/emergencia.ino`). Aplica esta tabla y además quita nFAULT (no está conectado, P13) y la suma de la caída de D1 al medir la batería (en emergencia el divisor va directo a `VBAT_SW`). `firmware/robot-casero/` sigue sin cambios y es HISTÓRICO. La tabla de la sección 2 manda sobre cualquier `config.h`; `v2/firmware/emergencia/pruebas/verificar_pines.py` comprueba que coincidan con el esquema.

---

## 7. Qué debe hacer el código (resumen)
1. Inicializar los pines de la sección 2 con las direcciones indicadas.
2. Dejar `DRV_SLEEP = 0` y los motores parados mientras arranca.
3. Leer los 8 sensores por el mux, con restar luz ambiente.
4. Controlar los motores con AIN/BIN (PWM) según la lectura.
5. Leer START y CAL con antirrebote.
6. Leer la batería y advertir si baja de un umbral (el umbral se define con Alan).
7. Quitar cualquier código de ventilador si se confirma EM-01.

---

## 8. Qué NO hacer
- No cambiar pines ni conexiones del esquema desde el código. Si un pin no sirve, se reporta con un ID en pendientes.
- No subir cambios a `main` ni hacer merge. El trabajo va a la rama `seguidor-caseroV2`.
- No dar por verificado el código solo porque compila. Falta probarlo con el robot.
- No usar el firmware histórico de `firmware/robot-casero/` sin adaptar los pines (sección 6): quitar el zumbador y poner START en GPIO4.

---

## 9. Pruebas antes de conectar motores
1. Con la placa **sin batería**, comprobar continuidad de cada pin de la sección 2 contra el esquema.
2. Con 5 V de USB (sin motores), probar START, CAL, EMIT_EN y la lectura de un sensor con el multímetro.
3. Probar la selección del mux: cada `S0–S3` combinado debe cambiar el canal (con el multímetro en `SIG` o con el ADC).
4. Solo después: motores a 6 V, con el robot levantado de las ruedas.

---

## Referencias
- Esquema: `robot_emergencia_unificado.kicad_sch` (y `.pdf`).
- Conexiones del diseño V2 aprobado: `v2/docs/conexiones.md`.
- Decisiones: `v2/docs/decisiones.md` (D-V2-05, D-V2-40 a D-V2-43).
- Pendientes: `docs/pendientes-por-confirmar.md`, sección E (EM-01 a EM-08).
- Firmware vigente: `v2/firmware/emergencia/` (README con carga, consola y prueba física).
- Compras y componentes: `README.md` de esta carpeta.
