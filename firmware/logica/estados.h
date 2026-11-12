// Máquina de estados del robot, rebote de botones y monitor de batería.
// C++ puro: no depende del MCU; se prueba en la PC (pruebas/sf/test_sf.cpp).
//
// Estados y transiciones (ver docs/ARQUITECTURA.md, sección firmware):
//
//   INICIO ──(arranque ok)──> ESPERA ──(CAL)──> CALIBRANDO ──(ok)──> LISTO
//     │                         ↑  ↑               │ (insuficiente)     │ (START y batería ok)
//     └─(batería fuera)─> ERROR ─┘  └───────────────┘                    v
//                            ↑                                       SIGUIENDO <──> RECUPERANDO
//                            └─────(sensores sin señal)────────────────┘  │ (línea perdida, START,
//                                                                         v  batería crítica)
//                                                                      PARADA ──(START o CAL)──> LISTO
#pragma once
#include <stdint.h>

// ---------------------------------------------------------------- botón con antirrebote
// Entrega un pulso (true) una sola vez por cada pulsación estable.
class Boton {
 public:
  explicit Boton(uint32_t antirrebote_ms = 30) : t_ms_(antirrebote_ms) {}
  // presionado_crudo: lectura directa del pin (true = presionado). ahora_ms: reloj.
  bool actualizar(bool presionado_crudo, uint32_t ahora_ms);
  bool estable() const { return estable_; }

 private:
  uint32_t t_ms_;
  bool crudo_prev_ = false;
  bool estable_ = false;
  uint32_t t_cambio_ = 0;
};

// ---------------------------------------------------------------- monitor de batería
// Filtra el voltaje (los picos de corriente de los motores lo hunden por instantes) y
// solo declara "crítica" si se mantiene bajo el umbral un tiempo.
class MonitorBateria {
 public:
  MonitorBateria(float v_min_arranque, float v_critica, uint32_t persistencia_ms, float alfa = 0.1f)
      : v_min_(v_min_arranque), v_crit_(v_critica), pers_ms_(persistencia_ms), alfa_(alfa) {}
  void muestra(float v, uint32_t ahora_ms);
  float voltaje() const { return v_filt_; }
  bool valida() const { return iniciado_; }
  bool permite_arranque() const { return iniciado_ && v_filt_ >= v_min_; }
  bool critica() const { return critico_; }

 private:
  float v_min_, v_crit_;
  uint32_t pers_ms_;
  float alfa_;
  float v_filt_ = 0.0f;
  bool iniciado_ = false;
  bool bajo_ = false;
  bool critico_ = false;
  uint32_t t_bajo_ = 0;
};

// ---------------------------------------------------------------- máquina de estados
enum class Estado : uint8_t { INICIO, ESPERA, CALIBRANDO, LISTO, SIGUIENDO, RECUPERANDO, PARADA, ERROR };

const char* nombre_estado(Estado e);

// Lo que pasó en este ciclo. firmware/stm32/main.cpp lo llena; la máquina decide.
struct Eventos {
  bool start = false;              // pulso del botón START (ya sin rebote)
  bool cal = false;                // pulso del botón CAL
  bool cal_guardada_ok = false;    // hay una calibración válida en memoria
  bool cal_suficiente = false;     // al terminar de calibrar, todos los sensores vieron blanco y negro
  bool cal_tiempo_agotado = false; // se acabó el tiempo de calibración
  bool bateria_permite = true;     // voltaje suficiente para arrancar
  bool bateria_critica = false;    // voltaje críticamente bajo y sostenido
  bool buscando = false;           // el controlador no ve la línea y está buscando
  bool linea_perdida = false;      // el controlador se rindió
  bool falla_sensores = false;     // lecturas imposibles (todas iguales/saturadas) sostenidas
  bool falla_motor = false;        // nFAULT del puente H o rueda trabada (encoder sin giro con ciclo alto)
};

enum class Motivo : uint8_t { NINGUNO, LINEA_PERDIDA, BOTON, BATERIA, SENSORES, CAL_INSUFICIENTE, BATERIA_ARRANQUE, MOTOR };

class MaquinaEstados {
 public:
  explicit MaquinaEstados(uint32_t bloqueo_start_ms = 500) : bloqueo_ms_(bloqueo_start_ms) {}
  // Devuelve true si el estado cambió en esta llamada.
  bool actualizar(const Eventos& ev, uint32_t ahora_ms);
  Estado estado() const { return e_; }
  Motivo motivo() const { return motivo_; }      // por qué se llegó a PARADA o ERROR
  uint32_t desde_ms() const { return t_entrada_; }
  bool motores_habilitados() const { return e_ == Estado::SIGUIENDO || e_ == Estado::RECUPERANDO; }
  // true en el ciclo en que se debe arrancar (reiniciar controlador, fijar velocidad)
  bool recien_arrancado() const { return arranque_; }

 private:
  void ir(Estado e, uint32_t t, Motivo m = Motivo::NINGUNO);
  Estado e_ = Estado::INICIO;
  Motivo motivo_ = Motivo::NINGUNO;
  uint32_t t_entrada_ = 0;
  uint32_t bloqueo_ms_;
  bool arranque_ = false;
};
