// Mapa de pines del ESP32 DevKit (38 pines) para el ROBOT CASERO. Es la ÚNICA fuente de verdad de los pines:
// el esquemático de electronica/kicad/principal/ se genera leyendo este archivo (herramientas/generar_principal.py).
//
// Reglas aplicadas (ver docs de la skill proyectos-electronicos-kicad):
//  - No se usan GPIO 6 a 11 (memoria flash) ni GPIO 1 y 3 (USB/serie).
//  - GPIO 34 a 39 son SOLO ENTRADA: aquí solo se usan como entradas analógicas (ADC1).
//  - GPIO 0, 2, 12, 15 y 5 son pines de arranque: no se usan para señales externas. El LED de la placa (GPIO 2) se usa sin conexión externa.
//  - Todo el análogo usa ADC1 (GPIO 32 a 39), porque el ADC2 no es fiable si el WiFi está activo y aquí el radio va apagado por reglamento.
//
// VERIFICAR con la placa real: el orden de pines de cada fabricante de DevKit cambia (ver electronica/kicad/NOTAS.md).
#pragma once

// ---- Barra de sensores (12 x TCRT5000 + multiplexor 74HC4067) ---------------
constexpr int PIN_MUX_S0   = 25;
constexpr int PIN_MUX_S1   = 26;
constexpr int PIN_MUX_S2   = 27;
constexpr int PIN_MUX_S3   = 33;
constexpr int PIN_MUX_SIG  = 34;   // ADC1_CH6, solo entrada. El multiplexor trabaja a 3.3 V.
constexpr int PIN_EMISORES = 13;   // enciende los LED infrarrojos (transistor 2N2222 en la barra)

// ---- Driver DRV8833 (2 pines de control por motor, PWM por LEDC) -------------
constexpr int PIN_AIN1 = 19;       // motor IZQUIERDO
constexpr int PIN_AIN2 = 21;
constexpr int PIN_BIN1 = 22;       // motor DERECHO
constexpr int PIN_BIN2 = 23;
constexpr int PIN_SLEEP = 16;      // nSLEEP del DRV8833 (con pulldown de 10 k: el driver arranca dormido)

// ---- Ventilador ---------------------------------------------------------------
constexpr int PIN_VENTILADOR = 17; // PWM hacia la compuerta del MOSFET IRLZ44N

// ---- Interfaz ------------------------------------------------------------------
constexpr int PIN_START = 4;       // a GND, pull-up interno
constexpr int PIN_CAL   = 14;      // a GND, pull-up interno
constexpr int PIN_BATERIA = 36;    // ADC1_CH0, divisor 100 k / 33 k (a 8.4 V da 2.08 V)
// RESET: botón entre EN y GND (sin GPIO). LED de estado: el de la placa (GPIO 2), sin componente externo.

constexpr float DIVISOR_BAT = (100.0f + 33.0f) / 33.0f;
