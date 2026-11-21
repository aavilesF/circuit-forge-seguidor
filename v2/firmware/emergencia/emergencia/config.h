// Robot de EMERGENCIA (placa perforada) · configuración de hardware.
// Fuente de verdad: v2/electronica/prototipo-emergencia/GUIA-FIRMWARE.md (sección 2) y el esquema unificado
// robot_emergencia_unificado.kicad_sch. NO cambiar un pin aquí sin cambiar antes el esquema (GUIA, sección 8).
// La prueba pruebas/verificar_pines.py compara este archivo con el netlist esperado del esquema.
// Marcas: [V] verificado en ficha/esquema · [C] calculado · [E] estimado · [P] pendiente de medir en el robot.
#pragma once

// ============================================================ sensores: 6 TCRT5000 por el CD74HC4067
// Montaje vigente (equipo, 21 nov 2026): SEN1..SEN6 en C0..C5; C6..C15 NO se usan. El esquema unificado todavía dibuja
// SEN7/SEN8 en C6/C7 (D-V2-41, 8 sensores): pendiente de actualizar el esquema (EM-09). Mux y pines no cambian.
#define NUM_SENSORES 6          // SEN1..SEN6 en los canales C0..C5 del mux
#define MASCARA_TODOS ((1u << NUM_SENSORES) - 1u)   // 0b111111 = 63: los 6 sensores en uso
#define PIN_MUX_S0 25           // DevKit pin 8  [V esquema]
#define PIN_MUX_S1 26           // DevKit pin 9  [V esquema]
#define PIN_MUX_S2 27           // DevKit pin 10 [V esquema]
#define PIN_MUX_S3 33           // DevKit pin 7  [V esquema]
#define PIN_MUX_SIG 34          // DevKit pin 4, ADC1_CH6, solo entrada [V esquema]
#define PIN_EMISORES 13         // EMIT_EN, DevKit pin 13: alto = LED IR encendidos (2N2222 Q1) [V esquema]
// TCRT5000 con pull-up de 10 kΩ a 3V3 y emisor a GND: más reflejo = menos voltaje [V esquema].
#define LUZ_BAJA_VOLTAJE 1
#define RESTA_AMBIENTE 1        // lee con emisores encendidos y apagados y resta (luz del lugar)

// ---- Valores INICIALES de lo que depende del montaje real. Todos se cambian sin recompilar con
// `set <clave> <valor>` + `save` (la clave va entre corchetes). Cambiarlos aquí solo cambia los de fábrica.
// Orden físico [inv_sens]: SEN1 a la izquierda y SEN6 a la derecha (equipo); FALTA confirmarlo con la barra montada
// [P]. Con la línea bajo el lado DERECHO, `sens` debe dar pos > 0; si no, `set inv_sens 1`.
#define SENSORES_INVERTIDOS 0
#define PASO_SENSORES_MM 12.7f    // [paso_mm] 5 agujeros de placa perforada, como la barra de 8 [P: medir la barra de 6]
#define DIST_SENSOR_EJE_MM 100.0f // solo informativo (la posición usa x); medir en el chasis armado (EM-06) [P]
#define MUX_ASENTAMIENTO_US 5     // [t_mux_us] espera tras cambiar S0..S3 [E: el CD74HC4067 conmuta en < 1 µs]
#define MOTOR_IZQ_INVERTIDO 0     // [inv_izq] [P] verificar con `m 0.3 0` (ruedas en el aire)
#define MOTOR_DER_INVERTIDO 1     // [inv_der] [P] los N20 van espejados; verificar con `m 0 0.3`
#define MOTORES_CRUZADOS 0        // [cruzar] 1 si el motor de AIN (M1) quedó montado del lado DERECHO

// ============================================================ DRV8833 (módulo) [V TI SLVSAR1, V esquema]
#define PIN_AIN1 19   // DevKit pin 25 · IN1 → OUT1/OUT2 = motor IZQUIERDO (M1)
#define PIN_AIN2 21   // DevKit pin 26 · IN2
#define PIN_BIN1 22   // DevKit pin 29 · IN3 → OUT3/OUT4 = motor DERECHO (M2)
#define PIN_BIN2 23   // DevKit pin 30 · IN4
#define PIN_NSLEEP 16 // DevKit pin 21 · DRV_SLEEP: alto = puente activo. Pull-down interno de 500 kΩ [V]
// nFAULT (ULT) NO está conectado (P13, D-V2-05): el firmware no lo lee.
#define PWM_FREC_HZ 20000   // inaudible; el DRV8833 acepta PWM hasta 250 kHz [V]
#define PWM_BITS 10

// ============================================================ interfaz
#define PIN_START 4       // DevKit pin 20 · botón a GND, pull-up interno [V esquema]
#define PIN_CAL 14        // DevKit pin 11 · botón a GND, pull-up interno [V esquema]
#define ANTIRREBOTE_MS 25 // lectura estable este tiempo antes de aceptar el cambio
#define PIN_LED 2         // LED azul integrado del DevKit (GPIO2 no está conectado en el esquema) [V esquema]
// Sin zumbador (D-V2-05) y sin ventilador (EM-01): no hay pines para ellos. GPIO15 y GPIO17 quedan libres.

// ============================================================ batería 2S
// Batería definitiva: pack 2S de 18650 Li-ion, 7.4 V nominal, ~2500 mAh. 8.4 V cargada (4.2 V/celda).
#define PIN_BATERIA 36    // VP, DevKit pin 2 · VBAT_SENSE [V esquema]
// Divisor NOMINAL del esquema: R1 = 100 kΩ (VBAT_SW → VBAT_SENSE) / R2 = 33 kΩ (→ GND), conectado DIRECTO a VBAT_SW
// (después del KCD1, sin diodo): no se suma caída. Factor nominal 133/33 = 4.030 (8.4 V → 2.08 V en el pin).
#define DIVISOR_BATERIA ((100.0f + 33.0f) / 33.0f)   // [C] solo referencia
// Factor EMPÍRICO que usa el firmware: punto de calibración físico del 20 nov 2026, medido al mismo tiempo, con el
// mismo GND y con el KCD1 encendido: fuente de 10.0 V → 2.1 V en VP/GPIO36 → 10.0 / 2.1 = 4.7619, offset 0 V.
// Esos 10.0 V son SOLO el punto de calibración (no el voltaje de la batería definitiva). No coincide con el nominal
// (con 4.030, 2.1 V serían 8.46 V): el divisor soldado no es exactamente 100k/33k. Pendiente: comparar `bat` con el
// multímetro usando la batería definitiva. Para volver al nominal: usar DIVISOR_BATERIA aquí.
#define FACTOR_BATERIA 4.7619f                        // [M] medido, punto único
// Máximo razonable de una 2S Li-ion: 8.4 V cargada + ~0.2 V de tolerancia (ADC calibrado de fábrica ±1–2 % y
// calibración de un solo punto). Por encima, la consola avisa (otra batería, cargador mal o lectura mal calibrada).
// Solo es aviso: no bloquea ni cambia ninguna protección.
#define BAT_MAX_2S 8.6f

// ============================================================ canales LEDC (solo arduino-esp32 2.x)
#define CANAL_AIN1 0
#define CANAL_AIN2 1
#define CANAL_BIN1 2
#define CANAL_BIN2 3
