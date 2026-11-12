#include "estados.h"

// ---------------------------------------------------------------- Boton
bool Boton::actualizar(bool crudo, uint32_t ahora) {
  if (crudo != crudo_prev_) {        // la entrada cambió: reinicia la ventana de espera
    crudo_prev_ = crudo;
    t_cambio_ = ahora;
    return false;
  }
  if (crudo != estable_ && (uint32_t)(ahora - t_cambio_) >= t_ms_) {
    estable_ = crudo;
    return estable_;                 // pulso solo en la transición a "presionado"
  }
  return false;
}

// ---------------------------------------------------------------- MonitorBateria
void MonitorBateria::muestra(float v, uint32_t ahora) {
  if (!iniciado_) { v_filt_ = v; iniciado_ = true; }
  else v_filt_ += alfa_ * (v - v_filt_);

  if (v_filt_ < v_crit_) {
    if (!bajo_) { bajo_ = true; t_bajo_ = ahora; }
    if ((uint32_t)(ahora - t_bajo_) >= pers_ms_) critico_ = true;
  } else {
    bajo_ = false;
    critico_ = false;
  }
}

// ---------------------------------------------------------------- MaquinaEstados
const char* nombre_estado(Estado e) {
  switch (e) {
    case Estado::INICIO: return "INICIO";
    case Estado::ESPERA: return "ESPERA";
    case Estado::CALIBRANDO: return "CALIBRANDO";
    case Estado::LISTO: return "LISTO";
    case Estado::SIGUIENDO: return "SIGUIENDO";
    case Estado::RECUPERANDO: return "RECUPERANDO";
    case Estado::PARADA: return "PARADA";
    case Estado::ERROR: return "ERROR";
  }
  return "?";
}

void MaquinaEstados::ir(Estado e, uint32_t t, Motivo m) {
  e_ = e;
  t_entrada_ = t;
  motivo_ = m;
  arranque_ = (e == Estado::SIGUIENDO);
}

bool MaquinaEstados::actualizar(const Eventos& ev, uint32_t t) {
  const Estado antes = e_;
  arranque_ = false;

  switch (e_) {
    case Estado::INICIO:
      if (!ev.bateria_permite) ir(Estado::ERROR, t, Motivo::BATERIA_ARRANQUE);
      else ir(Estado::ESPERA, t);
      break;

    case Estado::ESPERA:
      if (ev.cal) ir(Estado::CALIBRANDO, t);
      else if (ev.start && ev.cal_guardada_ok) ir(Estado::LISTO, t);
      break;

    case Estado::CALIBRANDO:
      if (ev.cal || ev.cal_tiempo_agotado) {
        if (ev.cal_suficiente) ir(Estado::LISTO, t);
        else ir(Estado::ESPERA, t, Motivo::CAL_INSUFICIENTE);
      }
      break;

    case Estado::LISTO:
      if (ev.cal) ir(Estado::ESPERA, t);
      else if (ev.start) {
        if (ev.bateria_permite) ir(Estado::SIGUIENDO, t);
        else motivo_ = Motivo::BATERIA_ARRANQUE;   // se queda en LISTO y avisa
      }
      break;

    case Estado::SIGUIENDO:
    case Estado::RECUPERANDO: {
      // Durante bloqueo_ms_ tras arrancar se ignora START: evita que el rebote o el dedo
      // todavía sobre el botón detengan el robot en la salida.
      const bool start_valido = ev.start && (uint32_t)(t - t_entrada_) >= bloqueo_ms_;
      if (ev.linea_perdida) ir(Estado::PARADA, t, Motivo::LINEA_PERDIDA);
      else if (ev.bateria_critica) ir(Estado::PARADA, t, Motivo::BATERIA);
      else if (ev.falla_sensores) ir(Estado::ERROR, t, Motivo::SENSORES);
      else if (ev.falla_motor) ir(Estado::ERROR, t, Motivo::MOTOR);
      else if (start_valido) ir(Estado::PARADA, t, Motivo::BOTON);
      else if (e_ == Estado::SIGUIENDO && ev.buscando) { e_ = Estado::RECUPERANDO; }
      else if (e_ == Estado::RECUPERANDO && !ev.buscando) { e_ = Estado::SIGUIENDO; }
      break;
    }

    case Estado::PARADA:
      if (ev.start || ev.cal) ir(Estado::LISTO, t);
      break;

    case Estado::ERROR:
      if (ev.cal) ir(Estado::ESPERA, t);
      break;
  }
  return e_ != antes;
}
