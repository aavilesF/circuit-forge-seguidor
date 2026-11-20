// Robot de emergencia · funciones puras pequeñas que usa la capa de hardware (C++ puro, se prueban en la PC).
#pragma once
#include <stdint.h>

namespace util {

// ---- CD74HC4067: bits S0..S3 para el canal c (0..15). S0 = bit 0 (LSB), S3 = bit 3 (MSB) [V GUIA, sección 3].
struct BitsMux { uint8_t s0, s1, s2, s3; };
inline BitsMux bits_mux(int c) {
  const unsigned u = static_cast<unsigned>(c) & 0x0Fu;
  return BitsMux{static_cast<uint8_t>(u & 1u), static_cast<uint8_t>((u >> 1) & 1u), static_cast<uint8_t>((u >> 2) & 1u),
                 static_cast<uint8_t>((u >> 3) & 1u)};
}

// ---- Orden físico: índice lógico i (0 = extremo IZQUIERDO del robot) → canal del mux.
// SEN(n) está en el canal C(n−1). Con invertidos = false, SEN1 (C0) es el de la izquierda.
inline int canal_de_sensor(int i, int n, bool invertidos) { return invertidos ? (n - 1 - i) : i; }

// ---- Batería: mV medidos en el pin → V de la batería (divisor directo a VBAT_SW, sin diodo)
inline float volts_bateria(float mv_pin, float divisor) { return mv_pin * 0.001f * divisor; }

// ---- Botón con antirrebote: pulso() devuelve true UNA vez cuando el botón queda oprimido de forma estable.
// lectura: true = oprimido. Un rebote más corto que ms_estable no cambia el estado.
struct Boton {
  bool estable = false, crudo = false;
  uint32_t t_cambio = 0;
  uint32_t ms_estable = 25;
  bool pulso(bool lectura, uint32_t t) {
    if (lectura != crudo) { crudo = lectura; t_cambio = t; }
    if (crudo != estable && t - t_cambio >= ms_estable) { estable = crudo; return estable; }
    return false;
  }
};

}  // namespace util
