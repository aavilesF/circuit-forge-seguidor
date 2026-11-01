// Parámetros compartidos por el firmware, las pruebas y el simulador.
// Sin dependencias de Arduino: se compila igual con g++ en la computadora.
//
// Los valores marcados "NOMINAL" son supuestos de diseño, no medidas.
// Hay que confirmarlos con las piezas reales (ficha técnica o vernier)
// y anotar el cambio en docs/decisiones.md.
#pragma once

namespace par {

// ---- Sensores ---------------------------------------------------------
constexpr int   MAX_SENSORES      = 32;      // 2 multiplexores de 16 canales

// ---- Geometría del robot (marco: x a la derecha, y hacia adelante) -----
// Reglamento: caber en 20 x 10 cm.
constexpr float LARGO_MAX_MM            = 200.0f;
constexpr float ANCHO_MAX_MM            = 100.0f;
constexpr float DIST_SENSOR_EJE_MM      = 100.0f; // NOMINAL: 8 a 12 cm delante del eje
constexpr float SEPARACION_RUEDAS_MM    = 75.0f;  // NOMINAL: entre centros de ruedas
constexpr float DIAMETRO_RUEDA_MM       = 33.0f;  // NOMINAL

// ---- Pista (reglamento) -----------------------------------------------
constexpr float ANCHO_LINEA_MM          = 25.0f;
constexpr float RADIO_MIN_CURVA_MM      = 150.0f;
constexpr float HUECO_MAX_MM            = 5.0f;

// ---- Tiempos -----------------------------------------------------------
constexpr unsigned long PERIODO_CONTROL_US = 2000;  // 500 Hz

// ---- Lectura de sensores ----------------------------------------------
constexpr int   ADC_MAX           = 4095;   // ESP32, 12 bits
constexpr float UMBRAL_RUIDO      = 0.10f;  // oscuridad menor a esto se ignora
constexpr float CONFIANZA_MIN     = 0.30f;  // suma mínima de oscuridad para ver la línea
constexpr float RANGO_CAL_MIN     = 150.0f; // diferencia mínima (cuentas ADC) para dar por buena la calibración

}  // namespace par
