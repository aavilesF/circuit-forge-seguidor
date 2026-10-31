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
constexpr int PIN_EMISORES = 13;   // compuerta del MOSFET que enciende los LED IR

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
constexpr int PIN_BATERIA = 36; // divisor de la batería: 100 kΩ (arriba) / 47 kΩ (abajo), ADC1_CH0
constexpr float DIVISOR_BAT = (100.0f + 47.0f) / 47.0f;
constexpr float BATERIA_MIN_V = 6.6f;  // 2S: 3.3 V por celda; abajo de esto no se arranca

// ---- Motores PWM ------------------------------------------------------------
constexpr int PWM_FREC_HZ = 20000;  // fuera del rango audible
constexpr int PWM_BITS    = 10;     // 0..1023
