#include "estados.h"

namespace casero {

const char* nombre(Estado e) {
  switch (e) {
    case Estado::INICIO: return "INICIO";
    case Estado::ESPERA: return "ESPERA";
    case Estado::CALIBRACION: return "CALIBRACION";
    case Estado::LISTO: return "LISTO";
    case Estado::SIGUIENDO: return "SIGUIENDO";
    case Estado::RECUPERACION: return "RECUPERACION";
    case Estado::PARADA: return "PARADA";
    case Estado::ERROR: return "ERROR";
  }
  return "?";
}

void Maquina::reiniciar(uint32_t t) {
  e_ = Estado::INICIO;
  err_ = Error::NINGUNO;
  t_entrada_ = t;
  entro_ = true;
  lista_ = false;
  rechazo_ = false;
  fin_cal_ = FinCal::NINGUNO;
}

void Maquina::ir(Estado e, uint32_t t) {
  e_ = e;
  t_entrada_ = t;
  entro_ = true;
  if (e == Estado::CALIBRACION) {
    lista_ = false;
    fin_cal_ = FinCal::NINGUNO;
  }
}

bool Maquina::despierto(uint32_t t) const {
  switch (e_) {
    case Estado::LISTO:
    case Estado::SIGUIENDO:
    case Estado::RECUPERACION: return true;
    case Estado::PARADA: return frenando(t);
    default: return false;
  }
}

Estado Maquina::paso(const Entradas& in, uint32_t t) {
  const Estado antes = e_;
  const uint32_t en_estado = desde(t);

  // fallas que detienen los motores en cualquier estado de marcha
  if (motores()) {
    if (in.falla_ciclo) { err_ = Error::CICLO; ir(Estado::ERROR, t); }
    else if (in.bat_critica) { err_ = Error::BATERIA; ir(Estado::ERROR, t); }
  }

  if (e_ == antes) {
    switch (e_) {
      case Estado::INICIO:
        if (en_estado >= tp_.inicio_ms) ir(Estado::ESPERA, t);
        break;

      case Estado::ESPERA:
        if (in.cal) ir(Estado::CALIBRACION, t);
        else if (in.start) {
          if (in.cal_valida) ir(Estado::LISTO, t);
          else { rechazo_ = true; t_rechazo_ = t; }
        }
        break;

      case Estado::CALIBRACION: {
        bool fin = in.cal || in.start;
        if (in.cal_lista) {
          if (!lista_) { lista_ = true; t_lista_ = t; }
          if (t - t_lista_ >= tp_.cal_extra_ms) fin = true;
        } else {
          lista_ = false;
        }
        if (en_estado >= tp_.cal_max_ms) fin = true;
        if (fin) {
          fin_cal_ = in.cal_lista ? FinCal::BIEN : FinCal::MAL;
          t_fin_cal_ = t;
          ir(in.cal_lista ? Estado::LISTO : Estado::ESPERA, t);
        }
        break;
      }

      case Estado::LISTO:
        if (in.cal) ir(Estado::CALIBRACION, t);
        else if (in.start) {
          if (!in.hay_bateria || in.bat_critica) { rechazo_ = true; t_rechazo_ = t; }
          else ir(Estado::SIGUIENDO, t);
        }
        break;

      case Estado::SIGUIENDO:
        if (in.start || in.parar || in.linea_perdida) ir(Estado::PARADA, t);
        else if (in.buscando) ir(Estado::RECUPERACION, t);
        break;

      case Estado::RECUPERACION:
        if (in.start || in.parar || in.linea_perdida) ir(Estado::PARADA, t);
        else if (in.linea_visible && !in.buscando) ir(Estado::SIGUIENDO, t);
        break;

      case Estado::PARADA:
        if (in.cal) ir(Estado::CALIBRACION, t);
        else if (in.start) ir(Estado::LISTO, t);
        break;

      case Estado::ERROR:
        if (in.start || in.cal) { err_ = Error::NINGUNO; ir(Estado::ESPERA, t); }
        break;
    }
  }
  entro_ = (e_ != antes);
  if (rechazo_ && t - t_rechazo_ > 1000) rechazo_ = false;
  return e_;
}

}  // namespace casero
