#include "mapa.h"

#include <math.h>
#include <stdlib.h>

namespace v2 {

static constexpr float DOS_PI = 6.2831853f;

float tope_curvatura(float kappa, float a_lat, float v_max) {
  const float k = fabsf(kappa);
  if (k < 1e-6f) return v_max;
  const float v = sqrtf(a_lat / k);
  return v < v_max ? v : v_max;
}

float perfil_factible(const float* cap, int n, float a_acc, float a_fr, float ds, float v_ini, float* vel) {
  // vel[i + 1] guarda primero el tope con la pasada hacia atrás (vb[i]); la pasada hacia adelante lo reemplaza.
  for (int i = 0; i < n; ++i) vel[i + 1] = cap[i];
  for (int i = n - 2; i >= 0; --i) {
    const float lim = sqrtf(vel[i + 2] * vel[i + 2] + 2.0f * a_fr * ds);
    if (lim < vel[i + 1]) vel[i + 1] = lim;
  }
  vel[0] = v_ini;
  float a_req = 0.0f;
  for (int i = 0; i < n; ++i) {
    float v_sig = sqrtf(vel[i] * vel[i] + 2.0f * a_acc * ds);
    if (vel[i + 1] < v_sig) v_sig = vel[i + 1];
    const float a = (vel[i] * vel[i] - v_sig * v_sig) / (2.0f * ds);
    if (a > a_req) a_req = a;
    vel[i + 1] = v_sig;
  }
  return a_req;
}

void perfil_ciclico(const float* cap, int n, float a_acc, float a_fr, float ds, float* vel) {
  if (n <= 0) return;
  for (int i = 0; i < n; ++i) vel[i] = cap[i];
  for (int r = 0; r < 2; ++r)            // dos vueltas hacia atrás: el frenado cruza el final de la vuelta
    for (int i = n - 1; i >= 0; --i) {
      const float sig = vel[(i + 1) % n];
      const float lim = sqrtf(sig * sig + 2.0f * a_fr * ds);
      if (lim < vel[i]) vel[i] = lim;
    }
  float v = vel[0];
  for (int r = 0; r < 2; ++r)            // dos vueltas hacia adelante: la segunda ya parte del valor exacto
    for (int i = 0; i < n; ++i) {
      v = sqrtf(v * v + 2.0f * a_acc * ds);
      if (vel[i] < v) v = vel[i];
      vel[i] = v;
    }
}

void Mapa::reiniciar(const ParamMapa& p) {
  p_ = p;
  modo_ = Modo::APRENDIENDO;
  i_ = n_ = pos_ = w_firma_ = mejor_n_ = desde_ = fallos_ = vueltas_ = im_ = nm_ = 0;
  mejor_err_ = 1e9f;
  acum_ds_ = acum_dpsi_ = psi_tot_ = frac_ = err_ult_ = giro_ = 0.0f;
  marca_ = -1;
  cierre_nuevo_ = perfil_ok_ = false;
}

void Mapa::avanzar(float ds, float dpsi) {
  if (modo_ == Modo::INVALIDO) return;
  if (ds < 0.0f) ds = 0.0f;              // marcha atrás (búsqueda de línea): no avanza en el mapa
  acum_ds_ += ds;
  acum_dpsi_ += dpsi;
  while (acum_ds_ >= p_.ds) {
    const float f = p_.ds / acum_ds_;     // reparte el giro en proporción si en un ciclo se avanzó más de una muestra
    const float dp = acum_dpsi_ * f;
    muestra(dp / p_.ds, dp);
    acum_ds_ -= p_.ds;
    acum_dpsi_ -= dp;
    if (modo_ == Modo::INVALIDO) return;
  }
  frac_ = acum_ds_;
}

void Mapa::muestra(float kappa, float dpsi) {
  psi_tot_ += dpsi;
  if (modo_ == Modo::APRENDIENDO) {
    if (i_ >= MAX) { modo_ = Modo::INVALIDO; return; }       // vuelta de más de 30 m: no cabe
    k_[i_] = kappa;
    psi_[i_] = psi_tot_;
    ++i_;
    if (w_firma_ == 0) {                  // firma de inicio: hasta incluir giro_firma de curva, más 20 cm
      giro_ += fabsf(kappa) * p_.ds;
      if (marca_ < 0 && giro_ >= p_.giro_firma) marca_ = i_ + 20;
      if ((marca_ >= 0 && i_ >= marca_) || i_ * p_.ds >= p_.firma_max) w_firma_ = i_;
    } else {
      buscar_cierre();
    }
    return;
  }
  // CERRADO: avanza en el mapa y se compara con la curvatura medida
  med_[im_] = kappa;
  im_ = (im_ + 1) & 127;
  if (nm_ < 128) ++nm_;
  if (++pos_ >= n_) { pos_ -= n_; ++vueltas_; }
  if (++desde_ >= static_cast<int>(p_.cada / p_.ds + 0.5f)) { desde_ = 0; localizar(); }
}

float Mapa::err_rms(const float* a, int ia, const float* b, int ib, int n, int mod_b) const {
  float s = 0.0f;
  for (int j = 0; j < n; ++j) {
    int kb = ib + j;
    if (mod_b > 0) { kb %= mod_b; if (kb < 0) kb += mod_b; }
    const float d = a[ia + j] - b[kb];
    s += d * d;
  }
  return sqrtf(s / static_cast<float>(n));
}

void Mapa::buscar_cierre() {
  const int w = w_firma_;
  const int N = i_ - w;                   // largo de vuelta candidato: la muestra N coincide con la 0
  if (N * p_.ds < p_.largo_min) return;
  const float tot = psi_[N - 1];          // giro de una vuelta completa
  const float k = floorf(tot / DOS_PI + 0.5f);
  const bool rumbo = fabsf(tot - k * DOS_PI) < p_.tol_rumbo;
  if (rumbo) {
    const float e = err_rms(k_, N, k_, 0, w, 0);
    if (e < mejor_err_) { mejor_err_ = e; mejor_n_ = N; }
  }
  const int pasado = static_cast<int>(p_.busqueda / p_.ds + 0.5f);
  if (mejor_err_ < p_.err_cierre && (N - mejor_n_ > pasado || !rumbo)) {
    // cierre: el mapa son las muestras [0, mejor_n_); la muestra en curso es la (i_ − mejor_n_) del mapa
    n_ = mejor_n_;
    pos_ = (i_ - n_) % n_;
    modo_ = Modo::CERRADO;
    vueltas_ = 1;
    err_ult_ = mejor_err_;
    const int c = i_ < 128 ? i_ : 128;    // curvatura reciente para la localización
    nm_ = im_ = 0;
    for (int j = i_ - c; j < i_; ++j) { med_[im_] = k_[j]; im_ = (im_ + 1) & 127; ++nm_; }
    cierre_nuevo_ = true;
    perfil_ok_ = false;
    fallos_ = desde_ = 0;
  } else if (!rumbo && mejor_err_ >= p_.err_cierre) {
    mejor_err_ = 1e9f;                    // candidato descartado: se busca el siguiente
  }
}

void Mapa::localizar() {
  const int W = static_cast<int>(p_.ventana_loc / p_.ds + 0.5f);
  if (nm_ < W || W > 128) return;
  float m[128];
  float energia = 0.0f;
  for (int j = 0; j < W; ++j) {
    m[j] = med_[(im_ - W + j + 256) & 127];
    energia += m[j] * m[j];
  }
  energia = sqrtf(energia / W);
  const int S = static_cast<int>(p_.busqueda / p_.ds + 0.5f);
  float mejor = 1e9f, mejor_mapa_e = 0.0f;
  int s_mejor = 0;
  for (int s = -S; s <= S; ++s) {
    const float e = err_rms(m, 0, k_, pos_ - W + s, W, n_);
    if (e < mejor - 1e-6f || (fabsf(e - mejor) <= 1e-6f && abs(s) < abs(s_mejor))) { mejor = e; s_mejor = s; }
  }
  // Solo se corrige si el mejor corrimiento es claramente mejor que no corregir: en un arco de radio constante o en
  // una recta la firma es igual en cualquier corrimiento y el ruido elegiría uno al azar (la posición derivaría).
  const float e0 = err_rms(m, 0, k_, pos_ - W, W, n_);
  if (e0 - mejor < 0.15f * e0 + 0.1f) s_mejor = 0;
  for (int j = 0; j < W; ++j) {
    const float v = k_[((pos_ - W + j) % n_ + n_) % n_];
    mejor_mapa_e += v * v;
  }
  mejor_mapa_e = sqrtf(mejor_mapa_e / W);
  err_ult_ = mejor;
  if (energia < 0.5f && mejor_mapa_e < 0.5f) return;      // recta en las dos: no hay con qué corregir
  if (mejor < p_.err_loc) {
    pos_ = ((pos_ + s_mejor) % n_ + n_) % n_;    // (s_mejor = 0 si la firma no distingue)
    fallos_ = 0;
  } else if (++fallos_ >= p_.fallos_max) {
    modo_ = Modo::INVALIDO;               // la pista ya no coincide: el robot vuelve a reactivo
    perfil_ok_ = false;
  }
}

void Mapa::calcular_perfil(float a_lat, float a_acc, float a_fr, float v_max) {
  if (modo_ != Modo::CERRADO) return;
  // tope por curvatura con el máximo de |κ| en ±3 cm (la curvatura medida tiene ruido y el robot entra antes a la curva)
  float* cap = psi_;                      // el rumbo ya no se usa después del cierre
  for (int i = 0; i < n_; ++i) {
    float km = 0.0f;
    for (int d = -3; d <= 3; ++d) {
      const float k = fabsf(k_[((i + d) % n_ + n_) % n_]);
      if (k > km) km = k;
    }
    cap[i] = tope_curvatura(km, a_lat, v_max);
  }
  perfil_ciclico(cap, n_, a_acc, a_fr, p_.ds, v_);
  perfil_ok_ = true;
}

float Mapa::v_perfil(float adelanto_m) const {
  if (!perfil_listo()) return 0.0f;
  int i = pos_ + static_cast<int>(adelanto_m / p_.ds + 0.5f);
  i %= n_;
  if (i < 0) i += n_;
  return v_[i];
}

}  // namespace v2
