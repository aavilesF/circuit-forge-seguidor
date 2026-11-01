// Configuración de hardware del Speed Follower. Única fuente de pines y de selección de piezas.
// Todo lo marcado VERIFICAR depende de la pieza real (ver docs/speed-follower/ENTREGABLE_2.md).
#pragma once
#include "sf_logica.h"

// ---- Selección de piezas (decisiones SF-2 y SF-3, pendientes de aprobación) ----------
#define DRIVER_DRV8833 1
#define DRIVER_TB6612  2
#define DRIVER DRIVER_DRV8833      // VERIFICAR: módulo DRV8833 en encapsulado PWP (1.5 A RMS); si es PW (0.5 A RMS), usar TB6612

#define MOTOR_POLOLU_12V_15 1
#define MOTOR_GA12_6V       2
#define MOTOR MOTOR_POLOLU_12V_15

inline sf::Robot robot_configurado() {
  sf::Robot r;
#if MOTOR == MOTOR_POLOLU_12V_15
  r.motor = sf::motor_pololu_12v_15();
  r.v_max_motor = 99.0f;             // 12 V nominal: en 2S siempre por debajo
#else
  r.motor = sf::motor_ga12_n20_6v_supuesto();
  r.v_max_motor = 6.0f;              // motor de 6 V en 2S: PWM limitado a 6 V promedio
#endif
  r.diam = 0.033f;                   // VERIFICAR con la llanta comprada
  r.W = 0.085f;                      // VERIFICAR (centro a centro de llantas en el chasis impreso)
  r.masa = 0.20f;                    // VERIFICAR con báscula
  r.L = 0.130f;                      // cuello (SF-4)
  r.n_sens = 8;
  r.paso = 0.0095f;                  // VERIFICAR: paso real del sensor (clon UNIT no lo publica)
  return r;
}

// ---- Sensores: un CD74HC4067, 8 canales
// Canal 0 del mux = sensor del extremo IZQUIERDO visto desde atrás (sf::estimar: e > 0 = línea a la derecha).
// VERIFICAR con 'sens' moviendo una línea de izquierda a derecha: e debe crecer. ------------------------------------------------
constexpr int NUM_SENSORES = 8;
constexpr int PIN_MUX_S0 = 25, PIN_MUX_S1 = 26, PIN_MUX_S2 = 27, PIN_MUX_S3 = 33;
constexpr int PIN_MUX_SIG = 34;          // ADC1
constexpr int PIN_EMISORES = 13;         // pin "IR" del sensor (VERIFICAR polaridad)
constexpr bool EMISOR_ACTIVO_ALTO = true;
constexpr bool ALTO_ES_NEGRO = true;     // VERIFICAR con 'crudo'
constexpr bool RESTA_AMBIENTE = true;
constexpr unsigned MUX_ESTABLECIMIENTO_US = 15;
constexpr unsigned EMISOR_ESTABLECIMIENTO_US = 100;   // 5 × 20 µs (subida típica de fototransistores)

// ---- Driver ----------------------------------------------------------------------------
#if DRIVER == DRIVER_DRV8833
constexpr int PIN_AIN1 = 19, PIN_AIN2 = 21;   // motor izquierdo
constexpr int PIN_BIN1 = 22, PIN_BIN2 = 23;   // motor derecho
constexpr int PIN_SLEEP = 16;                 // nSLEEP (alto = activo)
#else
constexpr int PIN_PWMA = 18, PIN_AIN1 = 19, PIN_AIN2 = 21;
constexpr int PIN_PWMB = 17, PIN_BIN1 = 22, PIN_BIN2 = 23;
constexpr int PIN_STBY = 16;
#endif
constexpr bool INVERTIR_IZQ = false, INVERTIR_DER = false;
constexpr int PWM_FREC_HZ = 20000, PWM_BITS = 10;

// ---- Interfaz y batería -----------------------------------------------------------------
constexpr int PIN_START = 4, PIN_CAL = 14, PIN_LED = 2;
constexpr int PIN_BATERIA = 36;
constexpr float DIVISOR_BAT = (100.0f + 33.0f) / 33.0f;   // 100k / 33k (8.4 V -> 2.08 V)
constexpr float BATERIA_MIN_V = 6.8f, BATERIA_CRITICA_V = 6.4f;
