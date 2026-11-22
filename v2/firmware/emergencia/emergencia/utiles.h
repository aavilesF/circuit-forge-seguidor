// Robot de emergencia · funciones puras pequeñas que usan la capa de hardware y el programa principal
// (C++ puro, se prueban en la PC).
#pragma once
#include <stdint.h>
#include <stdlib.h>

#include "posicion.h"

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

// ---- Máscara de sensores en uso (bit i = sensor lógico i, 0 = izquierda). Sirve para ignorar un TCRT5000 dañado.
inline bool activo(uint32_t mascara, int i) { return i >= 0 && i < 32 && ((mascara >> i) & 1u) != 0u; }
inline int contar_activos(uint32_t mascara, int n) {
  int k = 0;
  for (int i = 0; i < n; ++i) k += activo(mascara, i) ? 1 : 0;
  return k;
}
inline int primer_activo(uint32_t mascara, int n) {
  for (int i = 0; i < n; ++i) if (activo(mascara, i)) return i;
  return -1;
}
inline int ultimo_activo(uint32_t mascara, int n) {
  for (int i = n - 1; i >= 0; --i) if (activo(mascara, i)) return i;
  return -1;
}

// La calibración sirve si TODOS los sensores activos vieron blanco y negro (contraste ≥ rango_minimo).
inline bool cal_lista(const posicion::Calibracion& c, float rango_minimo, uint32_t mascara) {
  int vistos = 0;
  for (int i = 0; i < c.n; ++i) {
    if (!activo(mascara, i)) continue;
    if (c.maximo[i] - c.minimo[i] < rango_minimo) return false;
    ++vistos;
  }
  return vistos >= 2;   // con menos de 2 sensores no hay posición útil
}

inline bool contraste_ok(const posicion::Calibracion& c, int i, float rango_minimo) {
  return i >= 0 && i < c.n && c.maximo[i] - c.minimo[i] >= rango_minimo;
}

// Pone en 0 (blanco) la oscuridad de los sensores fuera de la máscara.
inline void enmascarar(float* osc, int n, uint32_t mascara) {
  for (int i = 0; i < n; ++i) if (!activo(mascara, i)) osc[i] = 0.0f;
}

// Cuántos sensores activos están "oscuros" (≥ umbral). Si todos lo están no hay piso: robot levantado
// (el TCRT5000 sin reflejo lee igual que la línea negra) o una marca ancha.
inline int contar_oscuros(const float* osc, int n, float umbral, uint32_t mascara) {
  int k = 0;
  for (int i = 0; i < n; ++i) if (activo(mascara, i) && osc[i] >= umbral) ++k;
  return k;
}

// ---- Batería: mV medidos en el pin → V de la batería (divisor directo a VBAT_SW, sin diodo)
inline float volts_bateria(float mv_pin, float divisor) { return mv_pin * 0.001f * divisor; }

// Voltaje que llega al DRV8833: el MP1584 U2 entrega vm_fijo mientras la batería alcance (caída propia del regulador).
inline float v_puente(bool hay_bateria, float vbat, float vm_fijo, float caida_reg) {
  if (!hay_bateria) return 0.0f;
  const float v = vbat - caida_reg;
  return v < vm_fijo ? (v > 0.0f ? v : 0.0f) : vm_fijo;
}

// ---- Lectura estricta de números de la consola: falso si el texto no es un número completo (evita que
// `set kp x` deje kp = 0, como hacía atof).
inline bool leer_float(const char* s, float* v) {
  if (!s || !*s) return false;
  char* fin = nullptr;
  const float x = strtof(s, &fin);
  if (fin == s || *fin != '\0') return false;
  if (!(x == x)) return false;   // NaN
  *v = x;
  return true;
}
inline bool leer_int(const char* s, int min, int max, int* v) {
  float x;
  if (!leer_float(s, &x)) return false;
  const int k = static_cast<int>(x);
  if (static_cast<float>(k) != x || k < min || k > max) return false;
  *v = k;
  return true;
}

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
