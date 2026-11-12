#include "indicadores.h"

namespace casero {

static bool parpadeo(uint32_t t, uint32_t periodo) { return (t % periodo) < periodo / 2; }

static const uint16_t AGUDO = 3000, MEDIO = 2000, GRAVE = 800;

Indicacion indicar(const Contexto& c) {
  Indicacion r;
  const uint32_t te = c.t_estado_ms, t = c.t_ms;
  switch (c.estado) {
    case Estado::INICIO:
      r.led = true;
      if (te < 100) r.tono_hz = AGUDO;
      break;
    case Estado::ESPERA:
      r.led = parpadeo(t, 1000);
      break;
    case Estado::CALIBRACION: {
      r.led = parpadeo(t, 200);
      const uint32_t s = te % 1000;
      const bool ultimos = te + 3000 >= c.cal_max_ms;
      if (s < 30 || (ultimos && s >= 150 && s < 180)) r.tono_hz = MEDIO;
      break;
    }
    case Estado::LISTO:
      r.led = true;
      if (te < 60 || (te >= 120 && te < 180)) r.tono_hz = AGUDO;
      break;
    case Estado::SIGUIENDO:
      r.led = c.linea_visible;
      break;
    case Estado::RECUPERACION:
      r.led = parpadeo(t, 120);
      if ((te % 150) < 40) r.tono_hz = AGUDO;
      break;
    case Estado::PARADA:
      r.led = parpadeo(t, 250);
      if (te < 400) r.tono_hz = MEDIO;
      break;
    case Estado::ERROR: {
      const uint32_t n = static_cast<uint32_t>(c.error);
      const uint32_t ciclo = 400 * n + 1200;
      const uint32_t f = t % ciclo;
      r.led = n > 0 && f < 400 * n && (f % 400) < 200;
      if (te < 600) r.tono_hz = GRAVE;
      break;
    }
  }
  // avisos que se superponen
  if (c.fin_cal != FinCal::NINGUNO && c.t_desde_fin_cal < 450) {
    static const uint16_t sube[3] = {2000, 2500, 3000}, baja[3] = {3000, 2000, 800};
    const uint16_t* notas = (c.fin_cal == FinCal::BIEN) ? sube : baja;
    const uint32_t k = c.t_desde_fin_cal / 150u;
    r.tono_hz = notas[k < 3u ? k : 2u];
  } else if (c.rechazo && c.t_desde_rechazo < 400) {
    if (c.t_desde_rechazo < 120 || (c.t_desde_rechazo >= 220 && c.t_desde_rechazo < 340)) r.tono_hz = GRAVE;
  } else if (c.bat_baja && (c.estado == Estado::ESPERA || c.estado == Estado::LISTO)) {
    const uint32_t f = t % 5000;
    if (f < 450 && (f % 150) < 70) r.tono_hz = GRAVE;
  }
  return r;
}

}  // namespace casero
