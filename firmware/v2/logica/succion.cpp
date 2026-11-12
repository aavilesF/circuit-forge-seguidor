#include "succion.h"

namespace v2 {

void SupervisorSuccion::encender(uint32_t ahora_ms) {
  if (e_ != Estado::APAGADO) return;
  e_ = Estado::ARRANQUE;
  t_inicio_ = ahora_ms;
  bajo_ = alto_ = false;
}

void SupervisorSuccion::apagar() {
  e_ = Estado::APAGADO;
  mando_ = 0.0f;
}

void SupervisorSuccion::muestra(float p_ambiente, float p_camara, bool validas, uint32_t ahora_ms) {
  valida_ = validas;
  t_ult_ = ahora_ms;
  if (!validas) return;
  const float dp = (p_ambiente - p_camara) - cero_;
  if (!hay_muestra_) { dp_f_ = dp; hay_muestra_ = true; }
  else dp_f_ += p_.alfa * (dp - dp_f_);
}

float SupervisorSuccion::fuerza() const {
  if (e_ != Estado::OK || dp_f_ <= 0.0f) return 0.0f;
  return dp_f_ * p_.area * p_.fraccion_ruedas;
}

void SupervisorSuccion::actualizar(uint32_t ahora_ms) {
  if (e_ == Estado::APAGADO) { mando_ = 0.0f; return; }
  // rampa del acelerador (evita el pico de corriente del ESC y deja que la cámara se vacíe)
  const float t = (ahora_ms - t_inicio_) * 1e-3f;
  mando_ = t >= p_.rampa_s ? p_.mando_crucero : p_.mando_crucero * t / p_.rampa_s;
  const bool sensor_ok = valida_ && (ahora_ms - t_ult_) < 100u;   // lecturas a 200 Hz: 100 ms sin datos = falla
  if (!sensor_ok) {
    // sin barómetros no se puede confirmar la succión: el robot corre con el perfil sin succión (no se detiene)
    if (e_ == Estado::ARRANQUE && t < p_.t_arranque_max) return;
    e_ = Estado::SIN_SENSOR;
    return;
  }
  const bool arriba = dp_f_ >= p_.dp_min;
  switch (e_) {
    case Estado::ARRANQUE:
      if (arriba && t >= p_.rampa_s) e_ = Estado::OK;
      else if (t >= p_.t_arranque_max) e_ = Estado::DEGRADADO;
      break;
    case Estado::OK:
      if (!arriba) {
        if (!bajo_) { bajo_ = true; t_bajo_ = ahora_ms; }
        if ((ahora_ms - t_bajo_) * 1e-3f >= p_.t_perdida) { e_ = Estado::DEGRADADO; alto_ = false; }
      } else {
        bajo_ = false;
      }
      break;
    case Estado::DEGRADADO:
    case Estado::SIN_SENSOR:
      if (arriba) {
        if (!alto_) { alto_ = true; t_alto_ = ahora_ms; }
        if ((ahora_ms - t_alto_) * 1e-3f >= p_.t_recupera) { e_ = Estado::OK; bajo_ = false; }
      } else {
        alto_ = false;
      }
      break;
    default:
      break;
  }
}

}  // namespace v2
