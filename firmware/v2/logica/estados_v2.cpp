#include "estados_v2.h"

namespace v2 {

const char* nombre(Estado e) {
  switch (e) {
    case Estado::INICIO: return "INICIO";
    case Estado::ESPERA: return "ESPERA";
    case Estado::CALIBRACION: return "CALIBRACION";
    case Estado::LISTO: return "LISTO";
    case Estado::ARRANQUE: return "ARRANQUE";
    case Estado::SIGUIENDO: return "SIGUIENDO";
    case Estado::RECUPERACION: return "RECUPERACION";
    case Estado::PARADA: return "PARADA";
    case Estado::ERROR: return "ERROR";
  }
  return "?";
}

void MaquinaV2::ir(Estado e, uint32_t t, Motivo m, Error er) {
  if (e == Estado::SIGUIENDO && e_ == Estado::ARRANQUE) arranque_ = true;
  if (e == Estado::ARRANQUE) t_carrera_ = t;
  e_ = e;
  t_ = t;
  motivo_ = m;
  err_ = er;
}

bool MaquinaV2::actualizar(const Eventos& ev, uint32_t t) {
  const Estado antes = e_;
  arranque_ = false;
  // START durante la carrera detiene, salvo en los primeros bloqueo_ms_ (rebote o dedo aún sobre el botón)
  const bool start_parar = ev.start && (uint32_t)(t - t_carrera_) >= bloqueo_ms_;

  switch (e_) {
    case Estado::INICIO:
      if (!ev.autoprueba_hecha) break;
      if (ev.autoprueba != Error::NINGUNO) ir(Estado::ERROR, t, Motivo::NINGUNO, ev.autoprueba);
      else if (!ev.bateria_permite) ir(Estado::ERROR, t, Motivo::BATERIA_ARRANQUE, Error::BATERIA);
      else ir(ev.cal_guardada_ok ? Estado::LISTO : Estado::ESPERA, t);
      break;

    case Estado::ESPERA:
      if (ev.cal) ir(Estado::CALIBRACION, t);
      break;

    case Estado::CALIBRACION:
      if (ev.cal || ev.cal_tiempo_agotado) {
        if (ev.cal_suficiente) ir(Estado::LISTO, t);
        else ir(Estado::ESPERA, t, Motivo::CAL_INSUFICIENTE);
      }
      break;

    case Estado::LISTO:
      if (ev.cal) ir(Estado::CALIBRACION, t);
      else if (ev.start) {
        if (ev.bateria_permite) ir(Estado::ARRANQUE, t);
        else motivo_ = Motivo::BATERIA_ARRANQUE;          // se queda en LISTO y avisa
      }
      break;

    case Estado::ARRANQUE:
      if (ev.falla_motor) ir(Estado::ERROR, t, Motivo::NINGUNO, Error::MOTOR);
      else if (ev.bateria_critica) ir(Estado::PARADA, t, Motivo::BATERIA_CRITICA);
      else if (start_parar) ir(Estado::PARADA, t, Motivo::BOTON);
      else if (ev.succion_lista) ir(Estado::SIGUIENDO, t);
      break;

    case Estado::SIGUIENDO:
    case Estado::RECUPERACION:
      if (ev.falla_motor) ir(Estado::ERROR, t, Motivo::NINGUNO, Error::MOTOR);
      else if (ev.sobrecalentado) ir(Estado::ERROR, t, Motivo::NINGUNO, Error::TEMPERATURA);
      else if (ev.falla_sensores) ir(Estado::ERROR, t, Motivo::NINGUNO, Error::SENSORES);
      else if (ev.linea_perdida) ir(Estado::PARADA, t, Motivo::LINEA_PERDIDA);
      else if (ev.bateria_critica) ir(Estado::PARADA, t, Motivo::BATERIA_CRITICA);
      else if (start_parar) ir(Estado::PARADA, t, Motivo::BOTON);
      else if (e_ == Estado::SIGUIENDO && ev.buscando) { e_ = Estado::RECUPERACION; t_ = t; }
      else if (e_ == Estado::RECUPERACION && !ev.buscando) { e_ = Estado::SIGUIENDO; t_ = t; }
      break;

    case Estado::PARADA:
      if (ev.cal) ir(Estado::CALIBRACION, t);
      else if (ev.start) ir(Estado::LISTO, t);
      break;

    case Estado::ERROR:
      if (ev.cal) ir(Estado::INICIO, t);                 // vuelve a hacer la autoprueba
      break;
  }
  return e_ != antes;
}

}  // namespace v2
