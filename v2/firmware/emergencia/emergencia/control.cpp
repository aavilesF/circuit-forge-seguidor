// Lógica V1 (firmware/seguidor, rama main) probada en PC. Cambios: los valores de param_por_defecto() (solo se usan
// hasta que el firmware aplica `Ajustes`) y el turbo de recta (v2.1, ver control.h). Con v_recta ≤ vbase la salida es
// la misma que la V1.
#include "control.h"
#include <math.h>

ParamControl param_por_defecto() {
  ParamControl p;
  p.kp = 0.010f;
  p.ki = 0.0f;
  p.kd = 0.0004f;
  p.vbase = 0.30f;
  p.freno_error = 0.30f;
  p.error_ref_mm = 30.0f;
  p.vmin_rel = 0.50f;
  p.u_max = 0.60f;
  p.rueda_min = -0.30f;
  p.tau_d_s = 0.010f;
  p.t_retencion_s = 0.060f;
  p.t_busqueda_s = 1.500f;
  p.u_busqueda = 0.35f;
  p.vbusqueda_rel = 0.40f;
  return p;
}

ControladorLinea::ControladorLinea(const ParamControl& p) : p_(p) { fijar(p); }

void ControladorLinea::fijar(const ParamControl& p) {
  p_ = p;
  pid_.fijar(p_.kp, p_.ki, p_.kd);
  pid_.limites(-p_.u_max, p_.u_max);
  pid_.filtro_derivada(p_.tau_d_s);
}

void ControladorLinea::reiniciar() {
  pid_.reiniciar();
  t_sin_linea_ = 0.0f;
  ultimo_error_ = 0.0f;
  ultima_u_ = 0.0f;
  ultimo_signo_ = 1.0f;
  cancelar_turbo();
  de_t_ = e_t_ = 0.0f;
  ini_t_ = false;
}

SalidaControl ControladorLinea::actualizar(const posicion::Estimacion& est, float dt_s, bool turbo_permitido) {
  SalidaControl s{};
  float u;
  float v_rel = 1.0f;

  if (est.linea_visible) {
    t_sin_linea_ = 0.0f;
    ultimo_error_ = est.pos_mm;
    if (fabsf(est.pos_mm) > 1.0f) ultimo_signo_ = est.pos_mm > 0.0f ? 1.0f : -1.0f;
    u = pid_.calcular(est.pos_mm, dt_s);
    ultima_u_ = u;
  } else {
    t_sin_linea_ += dt_s;
    if (t_sin_linea_ <= p_.t_retencion_s) {
      // Hueco de la línea (hasta 5 mm en la pista): se sigue con la última orden.
      u = ultima_u_;
    } else if (t_sin_linea_ <= p_.t_retencion_s + p_.t_busqueda_s) {
      // Línea perdida: se gira hacia el último lado en que se vio.
      s.buscando = true;
      u = ultimo_signo_ * p_.u_busqueda;
      v_rel = p_.vbusqueda_rel;
      pid_.reiniciar();
    } else {
      s.linea_perdida = true;
      s.buscando = true;
      s.error_mm = ultimo_error_;
      s.izq = 0.0f;
      s.der = 0.0f;
      return s;
    }
  }

  s.error_mm = est.linea_visible ? est.pos_mm : ultimo_error_;
  s.u = u;

  // Turbo de recta. Para entrar exige t_confirmar_s seguidos de recta limpia; las condiciones duras lo cancelan en el
  // acto y el error o su crecimiento, tras recta_n_out ciclos seguidos (histéresis: entrar es más estricto que salir).
  if (est.linea_visible) {           // derivada propia del turbo, en mm/s
    if (ini_t_ && dt_s > 0.0f) {
      const float a = dt_s / (p_.recta_tau_de_s + dt_s);
      de_t_ += a * ((est.pos_mm - e_t_) / dt_s - de_t_);
    } else {
      ini_t_ = true;
      de_t_ = 0.0f;
    }
    e_t_ = est.pos_mm;
  } else {
    ini_t_ = false;
    de_t_ = 0.0f;
  }
  const float de = de_t_;
  const bool se_aleja = est.pos_mm * de > 0.0f && fabsf(est.pos_mm) > p_.recta_e_in;
  const bool fuera = fabsf(est.pos_mm) > p_.recta_e_out || (fabsf(de) > p_.recta_de_out && se_aleja);
  n_fuera_ = (est.linea_visible && fuera) ? n_fuera_ + 1 : 0;
  const bool cancelar = !turbo_permitido || !est.linea_visible || s.buscando || !(p_.v_recta > p_.vbase) ||
                        est.confianza < p_.recta_conf_out || n_fuera_ >= p_.recta_n_out;
  if (cancelar) {
    cancelar_turbo();
  } else {
    if (!recta_) {
      const bool entra = fabsf(est.pos_mm) < p_.recta_e_in && fabsf(de) < p_.recta_de_in &&
                         est.confianza >= p_.recta_conf_in;
      t_ok_ = entra ? t_ok_ + dt_s : 0.0f;
      if (t_ok_ >= p_.t_confirmar_s) recta_ = true;
    }
    if (recta_) {
      g_ += (p_.t_acel_s > 1e-3f) ? dt_s / p_.t_acel_s : 1.0f;
      if (g_ > 1.0f) g_ = 1.0f;
    }
  }
  const float vbase_ef = p_.vbase + g_ * (p_.v_recta - p_.vbase);
  s.turbo = g_;

  // Frenado proporcional al error: en curva cerrada se reduce la velocidad base.
  if (!s.buscando) {
    float frac = fabsf(s.error_mm) / p_.error_ref_mm;
    if (frac > 1.0f) frac = 1.0f;
    v_rel = 1.0f - p_.freno_error * frac;
    if (v_rel < p_.vmin_rel) v_rel = p_.vmin_rel;
  }
  const float v = (s.buscando ? p_.vbase : vbase_ef) * v_rel;   // en búsqueda nunca hay turbo (g = 0)
  s.v = v;

  float izq = v + u;
  float der = v - u;

  // Saturación que conserva la diferencia entre ruedas (la diferencia es la que gira el robot).
  const float alto = fmaxf(izq, der);
  if (alto > 1.0f) {
    const float exceso = alto - 1.0f;
    izq -= exceso;
    der -= exceso;
  }
  const float bajo = fminf(izq, der);
  if (bajo < p_.rueda_min) {
    const float falta = p_.rueda_min - bajo;
    izq += falta;
    der += falta;
  }
  if (izq > 1.0f) izq = 1.0f;
  if (der > 1.0f) der = 1.0f;
  if (izq < p_.rueda_min) izq = p_.rueda_min;
  if (der < p_.rueda_min) der = p_.rueda_min;

  s.izq = izq;
  s.der = der;
  return s;
}
