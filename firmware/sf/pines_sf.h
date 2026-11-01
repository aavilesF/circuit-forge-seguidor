// Configuración de hardware del Speed Follower. Única fuente de pines y de selección de piezas.
// Pines del prototipo ESP32. Todo lo marcado VERIFICAR depende de la pieza real.
#pragma once
#include "sf_logica.h"

// ---- Robot y parámetros: vienen de config_maestra.h (generada de config/robot_maestro.yaml) ----------
// No escribir aquí números de motor, geometría o control: se editan en el YAML y se regenera la cabecera.
#include "config_maestra.h"

#define DRIVER_DRV8833 1
#define DRIVER_TB6612  2
#define DRIVER DRIVER_DRV8833      // VERIFICAR: módulo DRV8833 en encapsulado PWP (1.5 A RMS); el PW (0.5 A RMS) no sirve

inline sf::Robot robot_configurado() {
  sf::Robot r;
  r.motor = sf::Motor{cfg::MOTOR_V_NOM, cfg::MOTOR_RPM, cfg::MOTOR_PAR_BLOQUEO, cfg::MOTOR_I_BLOQUEO, cfg::MOTOR_I_VACIO};
  r.v_max_motor = cfg::MOTOR_LIMITE_V;
  r.diam = cfg::D_LLANTA;
  r.W = cfg::W_VIA;
  r.masa = cfg::MASA;
  r.L = cfg::L_CUELLO;
  r.n_sens = cfg::N_SENSORES;
  r.paso = 0.0f;                     // no se usa: la estimación usa cfg::SENSOR_Y (estimar_coord)
  return r;
}

inline sf::ParamSF parametros_maestros() {
  sf::ParamSF p;
  p.v_max = cfg::V_MAX; p.a_lat = cfg::A_LAT; p.a_lon = cfg::A_LON; p.k_pp = cfg::K_PP;
  p.kp = cfg::KP; p.kd = cfg::KD; p.tau_d = cfg::TAU_D; p.tau_k = cfg::TAU_K;
  p.t_perdida = cfg::T_PERDIDA; p.fuente_k = cfg::FUENTE_CURVATURA; p.piso = cfg::PISO;
  return p;
}

// ---- Sensores: un CD74HC4067 (16 canales)
// Canal i del mux = sensor i de cfg::SENSOR_Y (0 = extremo DERECHO visto desde atrás).
// VERIFICAR con 'sens' moviendo una línea de izquierda a derecha: e debe BAJAR (e > 0 = línea a la derecha).
constexpr int NUM_SENSORES = cfg::N_SENSORES;
static_assert(NUM_SENSORES <= 16, "un solo multiplexor de 16 canales");
constexpr int PIN_MUX_S0 = 25, PIN_MUX_S1 = 26, PIN_MUX_S2 = 27, PIN_MUX_S3 = 33;
constexpr int PIN_MUX_SIG = 34;          // ADC1
constexpr int PIN_EMISORES = 13;         // compuerta del MOSFET de emisores (VERIFICAR polaridad)
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
