// Robot de emergencia · LED azul integrado del DevKit (GPIO2) según el estado. Función pura del estado y el tiempo.
// No hay zumbador (D-V2-05): todos los avisos son con el LED (y por la consola USB).
//
//   INICIO        fijo                                      LISTO         fijo; esperando t_arranque: 12 Hz
//   ESPERA        parpadeo lento (1 Hz)                     SIGUIENDO     encendido = ve la línea
//   CALIBRACION   rápido (5 Hz); en los últimos 3 s, 10 Hz  RECUPERACION  muy rápido (8 Hz)
//   PARADA        4 Hz                                      ERROR         N destellos + pausa (1 = batería, 2 = ciclo)
//   fin de calibración: BIEN = 0.6 s fijo · MAL = 3 destellos rápidos (repetir)
//   rechazo (START sin calibración o sin batería): 2 destellos rápidos
//   batería baja (en ESPERA/LISTO): el LED se apaga 2 veces seguidas cada 3 s
#pragma once
#include <stdint.h>

#include "estados.h"

namespace robot {

struct Indicacion {
  bool led = false;
};

struct Contexto {
  Estado estado;
  Error error;
  uint32_t t_estado_ms;      // tiempo en el estado
  uint32_t t_ms;             // reloj
  bool linea_visible;
  FinCal fin_cal;            // resultado de la última calibración
  uint32_t t_desde_fin_cal;  // ms desde que terminó
  bool rechazo;
  uint32_t t_desde_rechazo;
  bool bat_baja;
  bool armando;              // LISTO con START oprimido, esperando t_arranque
  uint32_t cal_max_ms;
};

Indicacion indicar(const Contexto& c);

}  // namespace robot
