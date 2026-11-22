#include "indicadores.h"

namespace robot {

static bool parpadeo(uint32_t t, uint32_t periodo) { return (t % periodo) < periodo / 2; }

Indicacion indicar(const Contexto& c) {
  Indicacion r;
  const uint32_t te = c.t_estado_ms, t = c.t_ms;
  switch (c.estado) {
    case Estado::INICIO: r.led = true; break;
    case Estado::ESPERA: r.led = parpadeo(t, 1000); break;
    case Estado::CALIBRACION: r.led = parpadeo(t, te + 3000 >= c.cal_max_ms ? 100 : 200); break;
    case Estado::LISTO: r.led = c.armando ? parpadeo(t, 80) : true; break;
    case Estado::SIGUIENDO: r.led = c.linea_visible; break;
    case Estado::RECUPERACION: r.led = parpadeo(t, 120); break;
    case Estado::PARADA: r.led = parpadeo(t, 250); break;
    case Estado::ERROR: {
      const uint32_t n = static_cast<uint32_t>(c.error);
      const uint32_t f = t % (400 * n + 1200);
      r.led = n > 0 && f < 400 * n && (f % 400) < 200;
      break;
    }
  }
  // avisos que se superponen (tienen prioridad sobre el patrón del estado)
  if (c.fin_cal != FinCal::NINGUNO && c.t_desde_fin_cal < 600) {
    r.led = c.fin_cal == FinCal::BIEN ? true : (c.t_desde_fin_cal % 200) < 100;
  } else if (c.rechazo && c.t_desde_rechazo < 400) {
    r.led = (c.t_desde_rechazo % 200) < 100;
  } else if (c.bat_baja && (c.estado == Estado::ESPERA || c.estado == Estado::LISTO)) {
    const uint32_t f = t % 3000;
    if (f < 400) r.led = (f % 200) >= 100;   // dos apagones cortos
  }
  return r;
}

}  // namespace robot
