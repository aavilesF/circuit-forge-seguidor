#include "sf_logica.h"
#include <math.h>

namespace sf {

static inline float clampf(float x, float a, float b) { return x < a ? a : (x > b ? b : x); }

Lectura estimar(const float* lect, int n, float paso, float umbral) {
  float s = 0, m = 0, w0 = 0, wn = 0;
  for (int i = 0; i < n; ++i) {
    float w = clampf((lect[i] - umbral) / (1.0f - umbral), 0.0f, 1.0f);
    const float x = (i - (n - 1) * 0.5f) * paso;
    s += w; m += w * x;
    if (i == 0) w0 = w;
    if (i == n - 1) wn = w;
  }
  if (s < 0.5f) return Lectura{0.0f, false, false};
  return Lectura{m / s, true, (w0 > 0.3f) || (wn > 0.3f)};
}

Lectura estimar_coord(const float* lect, const float* y, int n, float umbral) {
  float s = 0, m = 0, w0 = 0, wn = 0;
  for (int i = 0; i < n; ++i) {
    const float w = clampf((lect[i] - umbral) / (1.0f - umbral), 0.0f, 1.0f);
    s += w; m += w * (-y[i]);
    if (i == 0) w0 = w;
    if (i == n - 1) wn = w;
  }
  if (s < 0.5f) return Lectura{0.0f, false, false};
  return Lectura{m / s, true, (w0 > 0.3f) || (wn > 0.3f)};
}

float ControlSF::ff(float v, float a, float v_bat) const {
  const Motor& m = r_.motor;
  const float w_r = v / r_.r();
  const float i_a = p_.ff_acel ? r_.masa * a * r_.r() / (2.0f * m.kt()) : 0.0f;
  const float i0 = (fabsf(w_r) > 1e-3f) ? copysignf(m.i0, w_r) : 0.0f;
  return (m.ke() * w_r + m.R() * (i0 + i_a)) / v_bat;
}

Salida ControlSF::paso(float e, bool borde, float dt, float v_bat, float gz) {
  const float L = r_.L, W = r_.W;
  if (inicial_) { e_f_ = e; inicial_ = false; }
  const float de = (e - e_f_) / dt;
  e_f_ = e;
  de_f_ += dt / (p_.tau_d + dt) * (de - de_f_);
  const float k_inst = 2.0f * e / (L * L);
  k_f_ += dt / (p_.tau_k + dt) * (k_inst - k_f_);
  float kmag = fabsf(k_f_);
  const float vref = fmaxf(v_cmd_, 0.1f);
  if (p_.fuente_k == 1) {          // C3m: curvatura que pide la última salida, con el modelo del motor
    const Motor& m = r_.motor;
    const float wl = (dl_ant_ * v_bat - m.R() * m.i0) / m.ke();
    const float wr = (dr_ant_ * v_bat - m.R() * m.i0) / m.ke();
    const float km = (wr - wl) * r_.r() / (W * vref);
    km_f_ += dt / (p_.tau_k + dt) * (km - km_f_);
    kmag = fmaxf(kmag, fabsf(km_f_));
  } else if (p_.fuente_k == 2) {   // C3g: curvatura = guiñada medida / velocidad
    km_f_ += dt / (p_.tau_k + dt) * (gz / vref - km_f_);
    kmag = fmaxf(kmag, fabsf(km_f_));
  }
  const float v_obj = fminf(p_.v_max, sqrtf(p_.a_lat / fmaxf(kmag, 1e-6f)));
  const float paso = clampf(v_obj - v_cmd_, -p_.a_lon * dt, p_.a_lon * dt);
  v_cmd_ += paso;
  const float a_cmd = paso / dt;
  const float v = fmaxf(v_cmd_, 0.05f);
  const float lim = fminf(v_bat, r_.v_max_motor) / v_bat;

  const float base = ff(v, a_cmd, v_bat);
  const float dv_pp = p_.k_pp * 2.0f * v * e * W / (L * L);
  const float delta = (ff(v + dv_pp * 0.5f, 0.0f, v_bat) - ff(v - dv_pp * 0.5f, 0.0f, v_bat)) + p_.kp * e + p_.kd * de_f_;
  float dl = base + delta * 0.5f, dr = base - delta * 0.5f;
  const float hi = fmaxf(dl, dr);
  if (hi > lim) { dl -= hi - lim; dr -= hi - lim; }
  const bool emergencia = p_.permitir_inversion && borde && fabsf(e) > p_.e_critico * r_.semibarra();
  float piso = emergencia ? -p_.d_inv : 0.0f;
  if (p_.freno_activo && base < 0.0f) piso = fminf(piso, fmaxf(base, -lim));
  const float bajo = fminf(dl, dr);
  if (bajo < piso) { dl -= bajo - piso; dr -= bajo - piso; }
  dl = clampf(dl, -lim, lim);
  dr = clampf(dr, -lim, lim);
  dl_ant_ = dl; dr_ant_ = dr;
  return Salida{dl, dr, v_cmd_, (dl < 0.0f) != (dr < 0.0f), false};
}

Salida ControlSF::actualizar(const Lectura& l, float dt, float v_bat, float gz) {
  if (l.visible) { e_ult_ = l.e; t_sin_ = 0.0f; }
  else t_sin_ += dt;
  if (!l.visible && t_sin_ > p_.t_perdida) { dl_ant_ = dr_ant_ = 0.0f; return Salida{0.0f, 0.0f, 0.0f, false, true}; }
  return paso(l.visible ? l.e : e_ult_, l.visible ? l.borde : true, dt, v_bat, gz);
}

}  // namespace sf
