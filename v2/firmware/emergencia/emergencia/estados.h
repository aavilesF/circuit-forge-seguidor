// Robot de emergencia · máquina de estados (C++ puro, se prueba en la PC). Adaptada de firmware/robot-casero
// (HISTÓRICO): sin nFAULT (no está conectado, P13), con arranque diferido y con todas las paradas seguras.
//
//   INICIO ──0.8 s──► ESPERA ──CAL──► CALIBRACION ──(bien)──► LISTO ──START (+t_arranque)──► SIGUIENDO ◄──► RECUPERACION
//                        ▲   └START (con calibración guardada)──┘  ▲                         │                      │
//                        │                     (mal)               │                         ▼                      ▼
//                        └──────────────── ERROR ◄── batería/ciclo  └─────────START──── PARADA ◄────────────────────┘
//
// CALIBRACION (reglamento: 15 s para calibrar Y colocar): se pasa el robot a mano sobre la línea. Termina con CAL o
// START, sola 1 s después de que TODOS los sensores vieron blanco y negro, o a los 15 s como máximo. La consola
// (`autocal`) también puede calibrar girando el robot y avisa con calibracion_externa().
// LISTO + START: espera t_arranque (LED muy rápido) y arranca; START o CAL durante la espera la cancelan.
// El robot no se mueve solo antes de START.
//
// Parada segura en marcha (SIGUIENDO / RECUPERACION):
//   → PARADA (frena 0.3 s, después suelta y duerme el puente): START, CAL, `parar` (cualquier byte por USB),
//     línea perdida (fin de la búsqueda) o `levantado` (todos los sensores negros: no hay piso).
//   → ERROR (frena 0.3 s, después suelta y duerme el puente): batería crítica o sin batería (ERROR 1) y ciclo de
//     control atrasado (ERROR 2). Si loop() se cuelga del todo, el watchdog de hardware reinicia el ESP32.
#pragma once
#include <stdint.h>

namespace robot {

enum class Estado : uint8_t { INICIO, ESPERA, CALIBRACION, LISTO, SIGUIENDO, RECUPERACION, PARADA, ERROR };
enum class Error : uint8_t { NINGUNO = 0, BATERIA = 1, CICLO = 2 };   // código = número de destellos
enum class FinCal : uint8_t { NINGUNO, BIEN, MAL };
enum class Motivo : uint8_t { NINGUNO, START, CAL, USB, LINEA_PERDIDA, LEVANTADO, BATERIA, SIN_BATERIA, CICLO };

const char* nombre(Estado e);
const char* nombre(Motivo m);

struct Entradas {
  bool start = false, cal = false;        // pulsación (flanco ya sin rebote)
  bool cal_lista = false;                 // la calibración en curso ya tiene contraste en todos los sensores
  bool cal_valida = false;                // hay calibración utilizable (nueva o guardada en memoria)
  bool linea_visible = false;
  bool buscando = false;                  // del ControladorLinea: sin línea más allá de la retención
  bool linea_perdida = false;             // del ControladorLinea: se acabó la búsqueda
  bool levantado = false;                 // todos los sensores negros más de t_negro (ya filtrado en el tiempo)
  bool hay_bateria = true;                // false = solo USB (VBAT < 3 V): no se arranca; en marcha → ERROR 1
  bool bat_critica = false;               // ya filtrada en el tiempo
  bool parar = false;                     // parada pedida por la consola USB (cualquier byte en marcha)
  bool falla_ciclo = false;               // el ciclo de control se atrasó (lecturas viejas): se para por seguridad
};

struct Tiempos {
  uint32_t inicio_ms = 800;
  uint32_t cal_max_ms = 15000;            // reglamento
  uint32_t cal_extra_ms = 1000;           // tras ver contraste en todos, sigue muestreando 1 s más
  uint32_t freno_ms = 300;                // en PARADA y ERROR frena y luego suelta y duerme el puente
  uint32_t arranque_ms = 0;               // espera entre START y SIGUIENDO (ajuste t_arranque)
};

class Maquina {
 public:
  void reiniciar(uint32_t t_ms);
  Estado paso(const Entradas& in, uint32_t t_ms);
  void fijar_tiempos(const Tiempos& t) { tp_ = t; }
  // Resultado de una calibración hecha fuera de la máquina (autocal por consola). Solo desde ESPERA, LISTO o
  // PARADA: bien → LISTO, mal → ESPERA. Devuelve false si el estado actual no lo permite.
  bool calibracion_externa(bool bien, uint32_t t_ms);

  Estado estado() const { return e_; }
  Error error() const { return err_; }
  Motivo motivo() const { return motivo_; }   // por qué se paró la última vez
  uint32_t desde(uint32_t t_ms) const { return t_ms - t_entrada_; }   // ms en el estado actual
  bool entro() const { return entro_; }                                 // primer paso del estado actual
  bool motores() const { return e_ == Estado::SIGUIENDO || e_ == Estado::RECUPERACION; }
  bool armando() const { return e_ == Estado::LISTO && armado_; }     // START oprimido, esperando t_arranque
  bool frenando(uint32_t t_ms) const {
    return (e_ == Estado::PARADA || (e_ == Estado::ERROR && freno_error_)) && desde(t_ms) < tp_.freno_ms;
  }
  bool despierto(uint32_t t_ms) const;  // nSLEEP en alto
  FinCal fin_cal() const { return fin_cal_; }
  uint32_t t_fin_cal() const { return t_fin_cal_; }
  bool rechazo() const { return rechazo_; }   // START sin calibración / sin batería: destellos de "no"
  uint32_t t_rechazo() const { return t_rechazo_; }

 private:
  void ir(Estado e, uint32_t t);
  void parar(Estado e, Motivo m, uint32_t t);
  Tiempos tp_;
  Estado e_ = Estado::INICIO;
  Error err_ = Error::NINGUNO;
  Motivo motivo_ = Motivo::NINGUNO;
  uint32_t t_entrada_ = 0, t_lista_ = 0, t_fin_cal_ = 0, t_rechazo_ = 0, t_armado_ = 0;
  bool lista_ = false, entro_ = true, rechazo_ = false, armado_ = false, freno_error_ = false;
  FinCal fin_cal_ = FinCal::NINGUNO;
};

}  // namespace robot
