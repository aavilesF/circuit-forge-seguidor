#include "motor_v2.h"

#include <math.h>

namespace v2 {

static inline float limitar(float x, float a, float b) { return x < a ? a : (x > b ? b : x); }

ModeloMotor ModeloMotor::desde_ficha(float v_nom, float rpm0, float par_bloqueo, float i_bloqueo, float i_vacio) {
  ModeloMotor m;
  m.R = v_nom / i_bloqueo;
  const float w0 = rpm0 * 6.2831853f / 60.0f;
  m.ke = (v_nom - i_vacio * m.R) / w0;
  m.kt = par_bloqueo / (i_bloqueo - i_vacio);
  m.i0 = i_vacio;
  return m;
}

float limitar_ciclo(const ModeloMotor& m, float ciclo, float w, float v_bat, float i_max, float v_lim) {
  if (v_bat < 1.0f) return 0.0f;
  const float e = m.ke * w;                       // fuerza contraelectromotriz
  const float d_min = (e - i_max * m.R) / v_bat;  // corriente = −i_max (frenado)
  const float d_max = (e + i_max * m.R) / v_bat;  // corriente = +i_max (tracción)
  const float tope = limitar(v_lim / v_bat, 0.0f, 1.0f);
  return limitar(limitar(ciclo, d_min, d_max), -tope, tope);
}

float LazoCorriente::actualizar(float i_medida, float i_lim, float dt) {
  if (i_lim <= 0.0f) return 0.0f;
  const float exceso = i_medida - 1.05f * i_lim;  // 5 % de tolerancia: error de IPROPI ±6-7.5 % [V SLVSF66A]
  if (exceso > 0.0f) k_ -= 2.0f * exceso / i_lim * dt * 50.0f;   // baja en ≈ 10-20 ms ante un exceso sostenido
  else k_ += 0.5f * dt;                                         // se recupera en ≈ 2 s
  k_ = limitar(k_, 0.4f, 1.0f);
  return k_ * i_lim;
}

void EstimadorTermico::paso(float i, float dt) {
  const float P = i * i * R_;
  T_ += (P - T_ / Rth_) / Cth_ * dt;
  if (T_ < 0.0f) T_ = 0.0f;
}

float EstimadorTermico::limite(float i_nom, float i_min, float t_reduce, float t_max) const {
  if (T_ <= t_reduce) return i_nom;
  if (T_ >= t_max) return 0.0f;
  return i_nom + (i_min - i_nom) * (T_ - t_reduce) / (t_max - t_reduce);
}

}  // namespace v2
