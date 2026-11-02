// Constantes de hardware que NO son parámetros de diseño (no están en config/robot_maestro.yaml).
// Motor, geometría, sensores y control vienen de config_maestra.h (generada del YAML).
#pragma once

namespace par {
constexpr int   MAX_SENSORES  = 32;      // tamaño de los arreglos de lectura
constexpr int   ADC_MAX       = 4095;    // ADC de 12 bits
constexpr float RANGO_CAL_MIN = 150.0f;  // diferencia mínima (cuentas ADC) blanco-negro para aceptar la calibración
}  // namespace par
