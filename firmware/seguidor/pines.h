// Configuración de hardware: perfil de sensor y mapa de pines del ESP32 DevKit (38 pines, "esp32dev").
// Es la ÚNICA fuente de verdad de los pines: docs/electronica.md y los diagramas se generan
// de esta tabla (herramientas/generar_diagramas.py la lee).
//
// Todo lo marcado VERIFICAR depende de la pieza real que se compre: se confirma al armar
// (docs/armado.md) y se anota en docs/decisiones.md.
#pragma once

// ---- Perfil de sensor (elegir UNO) ----------------------------------------
#define PERFIL_QTR8A    1   // barra recta de 8 sensores analógicos
#define PERFIL_CURVO24  2   // arreglo curvo de 24 canales (dos multiplexores de 16)
#define PERFIL_SENSOR   PERFIL_QTR8A

#if PERFIL_SENSOR == PERFIL_QTR8A
  constexpr int   NUM_SENSORES        = 8;
  constexpr bool  ARCO                = false;
  constexpr float PASO_MM             = 9.525f;  // VERIFICAR en la ficha / con vernier
  constexpr float RADIO_ARCO_MM       = 0.0f;
  constexpr bool  ALTO_ES_NEGRO       = true;    // VERIFICAR: en el QTR-xA el voltaje sube con menos reflectancia
#else
  constexpr int   NUM_SENSORES        = 24;
  constexpr bool  ARCO                = true;
  constexpr float PASO_MM             = 4.0f;    // VERIFICAR: paso a lo largo del arco
  constexpr float RADIO_ARCO_MM       = 80.0f;   // VERIFICAR: radio del arco
  constexpr bool  ALTO_ES_NEGRO       = true;    // VERIFICAR
#endif

constexpr bool RESTA_AMBIENTE = true;  // lee con emisores encendidos y apagados y resta

// ---- Multiplexores CD74HC4067 (16 canales cada uno) ------------------------
// Direcciones compartidas por los dos multiplexores. Se leen los dos a la vez.
constexpr int PIN_MUX_S0   = 25;
constexpr int PIN_MUX_S1   = 26;
constexpr int PIN_MUX_S2   = 27;
constexpr int PIN_MUX_S3   = 33;
constexpr int PIN_MUX_SIG1 = 34;   // canales 0..15   (ADC1_CH6, solo entrada)
constexpr int PIN_MUX_SIG2 = 35;   // canales 16..31  (ADC1_CH7, solo entrada; sin usar con 8 sensores)
constexpr int PIN_EMISORES = 13;   // QTR-8A Pololu: directo al pin LEDON (ya trae MOSFET). Sensores sueltos: compuerta de un MOSFET.
constexpr bool EMISOR_ACTIVO_ALTO = true;   // QTR-8A: LEDON alto (o al aire) = encendido. VERIFICAR en clones.
// Tiempos de lectura. La salida del QTR-8A tiene divisores de 47 kΩ (guía de Pololu), y el
// multiplexor agrega ~50 pF: τ ≈ 47 kΩ × 50 pF ≈ 2.4 µs. Se esperan ~6τ antes de leer.
constexpr unsigned MUX_ESTABLECIMIENTO_US = 15;  // VERIFICAR con el comando 'diag' (cruce entre canales)
constexpr unsigned EMISOR_ESTABLECIMIENTO_US = 30;

// ---- Driver de motores TB6612FNG (lógica a 3.3 V) --------------------------
// Canal A = rueda IZQUIERDA, canal B = rueda DERECHA (visto desde atrás, mirando al frente).
constexpr int PIN_PWMA = 18;
constexpr int PIN_AIN1 = 19;
constexpr int PIN_AIN2 = 21;
constexpr int PIN_PWMB = 17;
constexpr int PIN_BIN1 = 22;
constexpr int PIN_BIN2 = 23;
constexpr int PIN_STBY = 16;
constexpr bool INVERTIR_IZQ = false;  // cambiar a true si "adelante" gira al revés (prueba con ruedas en el aire)
constexpr bool INVERTIR_DER = false;

// ---- Interfaz ---------------------------------------------------------------
constexpr int PIN_START = 4;    // botón de arranque (a GND, pull-up interno)
constexpr int PIN_CAL   = 14;   // botón de calibración / selección (a GND, pull-up interno)
constexpr int PIN_LED   = 2;    // LED de estado (el azul de la tarjeta)
constexpr int PIN_PERFIL = 39;  // perilla (potenciómetro) de perfil de velocidad, ADC1_CH3
constexpr int PIN_BATERIA = 36; // divisor de la batería: 100 kΩ (arriba) / 33 kΩ (abajo), ADC1_CH0
// Con 11 dB el ESP32 mide bien de 150 a 2450 mV (Espressif). 8.4 V × 33/133 = 2.08 V: dentro del rango.
// (El divisor anterior, 100k/47k, daba 2.69 V con batería llena: fuera del rango recomendado.)
constexpr float DIVISOR_BAT = (100.0f + 33.0f) / 33.0f;
constexpr float BATERIA_MIN_V = 6.8f;      // 2S: no se arranca abajo de 3.4 V por celda
constexpr float BATERIA_CRITICA_V = 6.4f;  // 3.2 V por celda sostenido 300 ms en marcha: se detiene

// ---- Alimentación de los motores (checkpoint C2, ver docs/ARQUITECTURA.md) -----------
// false: motores desde un regulador de 6 V (arquitectura documentada hasta hoy).
// true:  motores directo de la batería 2S y el firmware limita el PWM a V_MOTOR_NOMINAL.
constexpr bool  MOTOR_DESDE_BATERIA = false;
constexpr float V_MOTOR_NOMINAL = 6.0f;

// ---- Motores PWM ------------------------------------------------------------
constexpr int PWM_FREC_HZ = 20000;  // fuera del rango audible
constexpr int PWM_BITS    = 10;     // 0..1023
