// Robot casero · LED azul del DevKit (GPIO2) y zumbador (Q2) según el estado. Función pura del estado y el tiempo
// (idea de V2, indicadores.cpp, con un solo LED). Con zumbador ACTIVO la frecuencia se ignora: solo suena/calla.
//
//   INICIO        LED fijo, pitido corto                    LISTO         LED fijo, doble pitido al entrar
//   ESPERA        LED parpadeo lento (1 Hz)                 SIGUIENDO     LED = ve la línea, silencio
//   CALIBRACION   LED rápido (5 Hz), "tic" cada segundo;    RECUPERACION  LED rápido, pitidos cortos seguidos
//                 tic doble en los últimos 3 s              PARADA        LED 4 Hz, pitido largo al entrar
//   fin de calibración: 3 notas que suben (bien) o bajan (faltó contraste: repetir)
//   ERROR         N destellos + pausa (1 = batería, 2 = driver), tono grave al entrar
//   rechazo       (START sin calibración o sin batería): dos pitidos graves
//   batería baja  (en ESPERA/LISTO): 3 pitidos cada 5 s
#pragma once
#include <stdint.h>

#include "estados.h"

namespace casero {

struct Indicacion {
  bool led = false;
  uint16_t tono_hz = 0;   // 0 = silencio
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
  uint32_t cal_max_ms;
};

Indicacion indicar(const Contexto& c);

}  // namespace casero
