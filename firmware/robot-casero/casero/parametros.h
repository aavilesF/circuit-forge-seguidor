// Robot casero · constantes que comparten la lógica, las pruebas en PC y el firmware (sin Arduino).
// Mismos nombres que firmware/seguidor/parametros.h (V1) para usar posicion/pid/control sin cambios.
#pragma once

namespace par {

constexpr int   MAX_SENSORES       = 16;      // 8 directos o hasta 16 con el 74HC4067
constexpr float LARGO_MAX_MM       = 200.0f;  // reglamento
constexpr float ANCHO_MAX_MM       = 100.0f;
constexpr float ANCHO_LINEA_MM     = 25.0f;
constexpr float HUECO_MAX_MM       = 5.0f;

constexpr unsigned long PERIODO_CONTROL_US = 2500;  // 400 Hz: deja tiempo al ADC2 del ESP32 (más lento que el ADC1)

constexpr int   ADC_MAX            = 4095;    // 12 bits
constexpr float UMBRAL_RUIDO       = 0.10f;   // oscuridad menor a esto se ignora (V1)
constexpr float CONFIANZA_MIN      = 0.30f;   // suma mínima de oscuridad para "ver" la línea (V1)
constexpr float RANGO_CAL_MIN      = 150.0f;  // cuentas: contraste mínimo blanco-negro por sensor (V1)

}  // namespace par
