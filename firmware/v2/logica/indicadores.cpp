#include "indicadores.h"

namespace v2 {

static bool parpadeo(uint32_t t, uint32_t periodo) { return (t % periodo) < periodo / 2; }

Indicadores indicar(Estado e, Error err, uint32_t te, uint32_t t, AvisoSucc s, Melodia m, uint32_t tm) {
  Indicadores r;
  switch (e) {
    case Estado::INICIO:
      r.amarillo = true;
      if (te < 80) r.tono_hz = 4000;                       // pitido corto en la resonancia del PKLCS1212E4001 (4.0 kHz)
      break;
    case Estado::ESPERA: r.amarillo = parpadeo(t, 1000); break;
    case Estado::CALIBRACION: r.amarillo = parpadeo(t, 200); break;
    case Estado::LISTO: r.verde = parpadeo(t, 1000); break;
    case Estado::ARRANQUE:
      r.verde = true;
      if (te < 60 || (te >= 120 && te < 180)) r.tono_hz = 4000;
      break;
    case Estado::SIGUIENDO: r.verde = true; break;
    case Estado::RECUPERACION:
      r.verde = parpadeo(t, 200); r.amarillo = !r.verde;
      if ((t % 150) < 40) r.tono_hz = 4000;
      break;
    case Estado::PARADA: r.verde = parpadeo(t, 250); break;
    case Estado::ERROR: {
      const uint32_t n = static_cast<uint32_t>(err);
      const uint32_t ciclo = 400 * n + 1200;                // N destellos de 200 ms + 1.2 s de pausa
      const uint32_t f = t % ciclo;
      r.rojo = f < 400 * n && (f % 400) < 200;
      if (te < 600) r.tono_hz = 2000;                       // tono grave al entrar (fuera de resonancia: más bajo)
      break;
    }
  }
  if (m != Melodia::NINGUNA && tm < 450) {                  // tres notas de 150 ms
    static const uint16_t sube[3] = {3000, 3500, 4000}, baja[3] = {4000, 3500, 3000};
    const uint16_t* notas = (m == Melodia::CAL_BIEN) ? sube : baja;
    const uint32_t k = tm / 150u;
    r.tono_hz = notas[k < 3u ? k : 2u];
  }
  r.succion = (s == AvisoSucc::OK) || (s == AvisoSucc::SIN_SUCCION && parpadeo(t, 300));
  return r;
}

}  // namespace v2
