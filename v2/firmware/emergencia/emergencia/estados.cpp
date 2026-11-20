#include "estados.h"

namespace robot {

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

const char* nombre(Motivo m) {
  switch (m) {
    case Motivo::NINGUNO: return "-";
    case Motivo::START: return "boton START";
    case Motivo::CAL: return "boton CAL";
    case Motivo::USB: return "tecla por USB";
    case Motivo::LINEA_PERDIDA: return "linea perdida (fin de la busqueda)";
    case Motivo::LEVANTADO: return "todos los sensores negros (robot levantado?)";
    case Motivo::BATERIA: return "bateria critica";
    case Motivo::SIN_BATERIA: return "sin bateria (KCD1 apagado o cable suelto)";
    case Motivo::CICLO: return "ciclo de control atrasado";
  }
  return "?";
}

void Maquina::reiniciar(uint32_t t) {
  e_ = Estado::INICIO;
  err_ = Error::NINGUNO;
  motivo_ = Motivo::NINGUNO;
  t_entrada_ = t;
  entro_ = true;
  lista_ = false;
  rechazo_ = false;
  armado_ = false;
  freno_error_ = false;
  fin_cal_ = FinCal::NINGUNO;
}

void Maquina::ir(Estado e, uint32_t t) {
  e_ = e;
  t_entrada_ = t;
  entro_ = true;
  armado_ = false;
  if (e == Estado::CALIBRACION) {
    lista_ = false;
    fin_cal_ = FinCal::NINGUNO;
  }
}

void Maquina::parar(Estado e, Motivo m, uint32_t t) {
  freno_error_ = motores();   // en ERROR solo se frena si venía en marcha
  motivo_ = m;
  if (e == Estado::ERROR) err_ = (m == Motivo::CICLO) ? Error::CICLO : Error::BATERIA;
  ir(e, t);
}

bool Maquina::despierto(uint32_t t) const {
  switch (e_) {
    case Estado::LISTO:
    case Estado::SIGUIENDO:
    case Estado::RECUPERACION: return true;
    case Estado::PARADA:
    case Estado::ERROR: return frenando(t);
    default: return false;
  }
}

bool Maquina::calibracion_externa(bool bien, uint32_t t) {
  if (e_ != Estado::ESPERA && e_ != Estado::LISTO && e_ != Estado::PARADA) return false;
  fin_cal_ = bien ? FinCal::BIEN : FinCal::MAL;
  t_fin_cal_ = t;
  ir(bien ? Estado::LISTO : Estado::ESPERA, t);
  return true;
}

Estado Maquina::paso(const Entradas& in, uint32_t t) {
  const Estado antes = e_;
  const uint32_t en_estado = desde(t);

  // fallas que detienen los motores en cualquier estado de marcha (prioridad sobre todo lo demás)
  if (motores()) {
    if (in.falla_ciclo) parar(Estado::ERROR, Motivo::CICLO, t);
    else if (!in.hay_bateria) parar(Estado::ERROR, Motivo::SIN_BATERIA, t);
    else if (in.bat_critica) parar(Estado::ERROR, Motivo::BATERIA, t);
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

      case Estado::LISTO: {
        const bool no_puede = !in.hay_bateria || in.bat_critica || !in.cal_valida;
        if (in.cal) ir(Estado::CALIBRACION, t);                  // también cancela un arranque pendiente
        else if (armado_) {
          if (in.start) armado_ = false;                         // segundo START: cancela
          else if (no_puede) { armado_ = false; rechazo_ = true; t_rechazo_ = t; }
          else if (t - t_armado_ >= tp_.arranque_ms) { motivo_ = Motivo::NINGUNO; ir(Estado::SIGUIENDO, t); }
        } else if (in.start) {
          if (no_puede) { rechazo_ = true; t_rechazo_ = t; }
          else if (tp_.arranque_ms == 0) { motivo_ = Motivo::NINGUNO; ir(Estado::SIGUIENDO, t); }
          else { armado_ = true; t_armado_ = t; }
        }
        break;
      }

      case Estado::SIGUIENDO:
      case Estado::RECUPERACION:
        if (in.start) parar(Estado::PARADA, Motivo::START, t);
        else if (in.cal) parar(Estado::PARADA, Motivo::CAL, t);
        else if (in.parar) parar(Estado::PARADA, Motivo::USB, t);
        else if (in.levantado) parar(Estado::PARADA, Motivo::LEVANTADO, t);
        else if (in.linea_perdida) parar(Estado::PARADA, Motivo::LINEA_PERDIDA, t);
        else if (e_ == Estado::SIGUIENDO && in.buscando) ir(Estado::RECUPERACION, t);
        else if (e_ == Estado::RECUPERACION && in.linea_visible && !in.buscando) ir(Estado::SIGUIENDO, t);
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

}  // namespace robot
