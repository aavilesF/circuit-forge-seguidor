// Copiado sin cambios de firmware/seguidor/pid.cpp (rama main, lógica V1 probada en PC).
#include "pid.h"
#include <math.h>

void PID::reiniciar() {
  integ_ = 0.0f;
  e_prev_ = 0.0f;
  d_filt_ = 0.0f;
  ultima_ = 0.0f;
  inicializado_ = false;
}

float PID::calcular(float error, float dt_s) {
  if (!(dt_s > 0.0f)) return ultima_;  // dt inválido: no se toca el estado

  // Derivada del error con filtro de primer orden.
  if (inicializado_) {
    const float d_cruda = (error - e_prev_) / dt_s;
    const float alfa = dt_s / (tau_ + dt_s);
    d_filt_ += alfa * (d_cruda - d_filt_);
  } else {
    inicializado_ = true;
    d_filt_ = 0.0f;
  }
  e_prev_ = error;

  const float p = kp_ * error;
  const float d = kd_ * d_filt_;

  // Anti-windup: no se acumula la integral si la salida ya está saturada
  // y el error empuja más hacia el mismo lado.
  const float integ_cand = integ_ + error * dt_s;
  const float u_cand = p + d + ki_ * integ_cand;
  const bool sat_alta = (u_cand > max_) && (error > 0.0f);
  const bool sat_baja = (u_cand < min_) && (error < 0.0f);
  if (!(sat_alta || sat_baja)) integ_ = integ_cand;

  // Además la integral solo puede aportar, como máximo, la salida completa.
  if (ki_ > 0.0f) {
    const float lim = fmaxf(fabsf(max_), fabsf(min_)) / ki_;
    if (integ_ > lim) integ_ = lim;
    if (integ_ < -lim) integ_ = -lim;
  }

  float u = p + d + ki_ * integ_;
  if (u > max_) u = max_;
  if (u < min_) u = min_;
  ultima_ = u;
  return u;
}
