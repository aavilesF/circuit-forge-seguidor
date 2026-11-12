// V2 · LED y zumbador por estado (FASE2_COMPONENTES §7). Función pura del estado y del tiempo: se prueba en la PC.
//
//   INICIO        amarillo fijo, pitido corto            LISTO          verde parpadeo lento
//   ESPERA        amarillo parpadeo lento                ARRANQUE       verde fijo, pitido doble
//   CALIBRACION   amarillo parpadeo rápido; al terminar tono ascendente (bien) o descendente (no alcanzó el contraste)
//   SIGUIENDO     verde fijo, silencio                   RECUPERACION   verde y amarillo alternando, pitidos rápidos
//   PARADA        verde parpadeo rápido                  ERROR          rojo: N parpadeos (código) y pausa; tono grave
//   SUCCIÓN (LED azul del módulo): fijo = ΔP en su ventana; parpadeo = modo sin succión; apagado = ventilador apagado
#pragma once
#include <stdint.h>

#include "estados_v2.h"

namespace v2 {

struct Indicadores {
  bool verde = false, amarillo = false, rojo = false, succion = false;
  uint16_t tono_hz = 0;          // 0 = silencio
};

enum class AvisoSucc : uint8_t { APAGADO, OK, SIN_SUCCION };
enum class Melodia : uint8_t { NINGUNA, CAL_BIEN, CAL_MAL };

// t_estado_ms: tiempo desde que se entró al estado; t_ms: reloj; melodia: se toca al salir de CALIBRACION
// (t_melodia_ms = tiempo desde que empezó).
Indicadores indicar(Estado e, Error err, uint32_t t_estado_ms, uint32_t t_ms, AvisoSucc s,
                    Melodia m = Melodia::NINGUNA, uint32_t t_melodia_ms = 0);

}  // namespace v2
