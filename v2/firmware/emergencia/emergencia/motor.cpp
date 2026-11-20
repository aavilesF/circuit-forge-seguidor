#include "motor.h"

#include <math.h>

namespace motor {

static inline float lim(float x, float a, float b) { return x < a ? a : (x > b ? b : x); }

Modelo Modelo::desde_ficha(float v_nom, float rpm0, float i_bloqueo, float i_vacio, float tau_s) {
  Modelo m;
  m.R = v_nom / i_bloqueo;
  const float w0 = rpm0 * 6.2831853f / 60.0f;
  m.ke = (v_nom - i_vacio * m.R) / w0;
  m.tau = tau_s;
  return m;
}

Puente drv8833(float d, Decaimiento k) {
  d = lim(d, -1.0f, 1.0f);
  if (k == Decaimiento::LENTO) {
    if (d >= 0.0f) return {1.0f, 1.0f - d};   // (1,0) maneja · (1,1) frena
    return {1.0f + d, 1.0f};                  // (0,1) maneja en reversa · (1,1) frena
  }
  if (d >= 0.0f) return {d, 0.0f};            // (1,0) maneja · (0,0) libre
  return {0.0f, -d};
}

float Accionamiento::tope(float v) const {
  float t = l_.pwm_max;
  if (v > 0.5f) t = fminf(t, l_.v_motor_max / v);
  return lim(t, 0.0f, 1.0f);
}

void Accionamiento::actualizar(float cmd_izq, float cmd_der, float v, float dt) {
  if (!(dt > 0.0f)) return;
  const float cmd[2] = {lim(cmd_izq, -1.0f, 1.0f), lim(cmd_der, -1.0f, 1.0f)};
  if (v < 1.0f) {                       // sin voltaje en el puente (solo USB): todo a cero
    reiniciar();
    return;
  }
  const float tp = tope(v);
  float d[2];
  for (int k = 0; k < 2; ++k) {
    float x = cmd[k] * tp;                                    // 1. tope
    // 2. rampa: frenar = moverse hacia el lado contrario del ciclo actual (bajar |d| o invertir)
    const bool frenando = (x - d_[k]) * d_[k] < 0.0f;
    const float paso = (frenando ? l_.rampa_freno : l_.rampa) * dt;
    x = lim(x, d_[k] - paso, d_[k] + paso);
    const float e = m_.ke * w_[k];                            // 3. corriente por motor
    x = lim(x, (e - l_.i_max * m_.R) / v, (e + l_.i_max * m_.R) / v);
    d[k] = lim(x, -tp, tp);
  }
  // 4. corriente total: si la suma estimada pasa del límite, se escalan las dos corrientes por igual
  float i0 = m_.corriente(d[0], v, w_[0]), i1 = m_.corriente(d[1], v, w_[1]);
  const float suma = fabsf(i0) + fabsf(i1);
  if (suma > l_.i_total && suma > 1e-6f) {
    const float s = l_.i_total / suma;
    i0 *= s;
    i1 *= s;
    d[0] = lim((i0 * m_.R + m_.ke * w_[0]) / v, -tp, tp);
    d[1] = lim((i1 * m_.R + m_.ke * w_[1]) / v, -tp, tp);
  }
  for (int k = 0; k < 2; ++k) {
    d_[k] = d[k];
    i_[k] = m_.corriente(d[k], v, w_[k]);
    const float w_obj = d[k] * v / m_.ke;                     // velocidad sin carga para ese ciclo
    const float a = dt / (m_.tau + dt);
    w_[k] += a * (w_obj - w_[k]);
  }
}

}  // namespace motor
