// Robot casero · máquina de estados (C++ puro, se prueba en la PC). Toma la idea de V2 (estados_v2) simplificada
// a lo que hay en la mesa: sin encoders, sin succión, sin mapa.
//
//   INICIO ──0.8 s──► ESPERA ──CAL──► CALIBRACION ──(bien)──► LISTO ──START──► SIGUIENDO ◄──línea──► RECUPERACION
//                        ▲   └START (con calibración guardada)──┘  ▲                │  START / línea perdida │
//                        │                     (mal)               │                ▼                        ▼
//                        └──────────────── ERROR ◄── batería/driver └──START─── PARADA ◄────────────────────┘
//
// CALIBRACION (reglamento: 15 s para calibrar Y colocar): se pasa el robot a mano sobre la línea. Termina con CAL o
// START, sola 1 s después de que TODOS los sensores vieron blanco y negro, o a los 15 s como máximo.
// El robot no se mueve solo antes de START.
#pragma once
#include <stdint.h>

namespace casero {

enum class Estado : uint8_t { INICIO, ESPERA, CALIBRACION, LISTO, SIGUIENDO, RECUPERACION, PARADA, ERROR };
enum class Error : uint8_t { NINGUNO = 0, BATERIA = 1, DRIVER = 2 };   // código = número de destellos
enum class FinCal : uint8_t { NINGUNO, BIEN, MAL };

const char* nombre(Estado e);

struct Entradas {
  bool start = false, cal = false;        // pulsación (flanco ya sin rebote)
  bool cal_lista = false;                 // la calibración en curso ya tiene contraste en todos los sensores
  bool cal_valida = false;                // hay calibración utilizable (nueva o guardada en memoria)
  bool linea_visible = false;
  bool buscando = false;                  // del ControladorLinea: sin línea más allá de la retención
  bool linea_perdida = false;             // del ControladorLinea: se acabó la búsqueda
  bool hay_bateria = true;                // false = solo USB (VBAT < 3 V): no se arranca
  bool bat_critica = false;               // ya filtrada en el tiempo
  bool falla_driver = false;              // nFAULT bajo sostenido (solo si JP1 está cerrado)
};

struct Tiempos {
  uint32_t inicio_ms = 800;
  uint32_t cal_max_ms = 15000;            // reglamento
  uint32_t cal_extra_ms = 1000;           // tras ver contraste en todos, sigue muestreando 1 s más
  uint32_t freno_ms = 300;                // en PARADA frena y luego suelta y duerme el puente
};

class Maquina {
 public:
  void reiniciar(uint32_t t_ms);
  Estado paso(const Entradas& in, uint32_t t_ms);
  void fijar_tiempos(const Tiempos& t) { tp_ = t; }

  Estado estado() const { return e_; }
  Error error() const { return err_; }
  uint32_t desde(uint32_t t_ms) const { return t_ms - t_entrada_; }   // ms en el estado actual
  bool entro() const { return entro_; }                                 // primer paso del estado actual
  bool motores() const { return e_ == Estado::SIGUIENDO || e_ == Estado::RECUPERACION; }
  bool frenando(uint32_t t_ms) const { return e_ == Estado::PARADA && desde(t_ms) < tp_.freno_ms; }
  bool despierto(uint32_t t_ms) const;  // nSLEEP en alto
  FinCal fin_cal() const { return fin_cal_; }
  uint32_t t_fin_cal() const { return t_fin_cal_; }
  bool rechazo() const { return rechazo_; }   // START sin calibración / sin batería: pitido de "no"
  uint32_t t_rechazo() const { return t_rechazo_; }

 private:
  void ir(Estado e, uint32_t t);
  Tiempos tp_;
  Estado e_ = Estado::INICIO;
  Error err_ = Error::NINGUNO;
  uint32_t t_entrada_ = 0, t_lista_ = 0, t_fin_cal_ = 0, t_rechazo_ = 0;
  bool lista_ = false, entro_ = true, rechazo_ = false;
  FinCal fin_cal_ = FinCal::NINGUNO;
};

}  // namespace casero
