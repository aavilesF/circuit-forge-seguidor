#include "control.h"
#include <math.h>

ParamControl param_por_defecto() {
  ParamControl p;
  // Punto de partida obtenido en simulación (ver docs/simulacion.md): kp=0.04 y kd=0.002
  // dieron el menor error en el barrido. El modelo es ideal; con el robot real hay que
  // volver a ajustarlos. vbase=0.40 es una primera vuelta prudente, no la velocidad final.
  p.kp = 0.04f;
  p.ki = 0.0f;
  p.kd = 0.002f;
  p.vbase = 0.40f;
  p.freno_error = 0.30f;
  p.error_ref_mm = 30.0f;
  p.vmin_rel = 0.50f;
  p.u_max = 0.60f;
  p.rueda_min = -0.30f;
  p.tau_d_s = 0.010f;
  p.t_retencion_s = 0.060f;
  p.t_busqueda_s = 0.250f;   // sim/: con 0.4 s o más el robot reencuentra la línea al revés (escenario fin_de_linea)
  p.u_busqueda = 0.35f;
  p.vbusqueda_rel = 0.40f;
  return p;
}

float compensar_bateria(float cmd, float v_bateria, float v_motor_nominal) {
  if (!(v_bateria > v_motor_nominal) || v_motor_nominal <= 0.0f) return cmd;
  return cmd * (v_motor_nominal / v_bateria);
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
}

SalidaControl ControladorLinea::actualizar(const posicion::Estimacion& est, float dt_s) {
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

  // Frenado proporcional al error: en curva cerrada se reduce la velocidad base.
  if (!s.buscando) {
    float frac = fabsf(s.error_mm) / p_.error_ref_mm;
    if (frac > 1.0f) frac = 1.0f;
    v_rel = 1.0f - p_.freno_error * frac;
    if (v_rel < p_.vmin_rel) v_rel = p_.vmin_rel;
  }
  const float v = p_.vbase * v_rel;

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
