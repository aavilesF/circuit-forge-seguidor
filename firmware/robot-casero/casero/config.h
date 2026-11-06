// Robot casero (Plan B) · configuración de hardware. Lo único que se cambia al armar es este archivo.
// Pines = placa principal en placa fenólica (docs/robot-casero/CONEXIONES.md, herramientas/placa_principal.py).
// Marcas: [V] verificado en ficha/serigrafía · [C] calculado · [E] estimado · [P] pendiente de medir en el robot.
#pragma once

// ============================================================ sensores
// 1 = 8 salidas analógicas directas al ESP32 (QTR-8A o 8 TCRT5000 sueltos con su pull-up de 10 kΩ).
// 0 = 12 TCRT5000 con el módulo 74HC4067 (decisión D05 de Alan; mismos pines del conector J6).
#define SENSORES_DIRECTOS 1

#if SENSORES_DIRECTOS
#define NUM_SENSORES 8
// J6: A1 (sensor de la IZQUIERDA del robot) … A8 (derecha). GPIO25-27 son ADC2: funcionan porque el radio
// nunca se enciende (prohibido por reglamento). GPIO34/35/39 solo son entradas.
static const int PINES_SENSORES[NUM_SENSORES] = {27, 26, 25, 33, 32, 35, 34, 39};
#else
#define NUM_SENSORES 12
#define PIN_MUX_S0 25   // J6.A3
#define PIN_MUX_S1 26   // J6.A2
#define PIN_MUX_S2 27   // J6.A1
#define PIN_MUX_S3 33   // J6.A4
#define PIN_MUX_SIG 34  // J6.A7 (ADC1_CH6)
#endif

// QTR-8A [V Pololu 0J12]: más reflejo = menos voltaje. TCRT5000 con pull-up de 10 kΩ al colector: igual.
#define LUZ_BAJA_VOLTAJE 1
#define RESTA_AMBIENTE 1          // lee con emisores encendidos y apagados y resta (luz del lugar)

// Geometría de la barra (marco del robot: x a la derecha, y hacia adelante desde el eje de ruedas)
#define BARRA_EN_ARCO 0
#define PASO_SENSORES_MM 9.525f   // QTR-8A [V Pololu]; barra casera de TCRT5000: 10.16 (4 agujeros) [P]
#define RADIO_ARCO_MM 110.0f      // solo si BARRA_EN_ARCO (D05)
#define DIST_SENSOR_EJE_MM 100.0f // [P] medir en el chasis armado

// ============================================================ DRV8833 (módulo) [V TI SLVSAR1]
#define PIN_AIN1 19   // IN1 → OUT1/OUT2 = motor IZQUIERDO (J4)
#define PIN_AIN2 21   // IN2
#define PIN_BIN1 22   // IN3 → OUT3/OUT4 = motor DERECHO (J3)
#define PIN_BIN2 23   // IN4
#define PIN_NSLEEP 16 // EEP: alto = puente activo. Pull-down interno de 500 kΩ [V]
#define PIN_NFAULT 15 // ULT: drenador abierto, bajo = falla [V]. Llega solo si se cerró JP1 (ver manual)
#define PWM_FREC_HZ 20000   // inaudible; el DRV8833 acepta PWM hasta 250 kHz [V]
#define PWM_BITS 10

// ============================================================ interfaz
#define PIN_START 18      // botón a GND (pull-up interno)
#define PIN_CAL 14        // botón a GND (pull-up interno)
#define PIN_LED 2         // LED azul del DevKit
#define PIN_ZUMBADOR 4    // base de Q2 (2N2222) por 1 kΩ
#define PIN_EMISORES 13   // base de Q1 por 1 kΩ (TCRT5000) o LEDON de la QTR-8A: alto = LED IR encendidos
#define PIN_BATERIA 36    // VP: divisor 100 kΩ / 33 kΩ
#define DIVISOR_BATERIA ((100.0f + 33.0f) / 33.0f)   // [C] 8.4 V → 2.08 V en el pin

// ============================================================ canales LEDC (arduino-esp32 2.x)
#define CANAL_AIN1 0
#define CANAL_AIN2 1
#define CANAL_BIN1 2
#define CANAL_BIN2 3
#define CANAL_ZUMB 4      // otro temporizador (canales 4-5 usan el timer 2)
