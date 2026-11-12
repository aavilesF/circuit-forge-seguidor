// V2 · Máquina de estados del robot (FASE2_COMPONENTES §7). C++17 puro: se prueba en la PC.
//
//   INICIO ─(autoprueba ok, batería ok)─> LISTO (si hay calibración guardada) o ESPERA
//     │                                     │ CAL            │ START (R08: nada se mueve antes)
//     └─(falla)─> ERROR <───────────────────┼────────────────┼─────────── (falla durante la carrera)
//                  │ CAL                     v                v
//                  └──> INICIO        CALIBRACION      ARRANQUE (ventilador en rampa, ruedas frenadas)
//                                       │ CAL/tiempo     │ succión confirmada o modo sin succión
//                                       v                v
//                                     LISTO / ESPERA   SIGUIENDO <──> RECUPERACION (línea perdida o derrape, ≤ 0.3 s)
//                                                        │ línea perdida, batería crítica, START
//                                                        v
//                                                      PARADA ──(START o CAL)──> LISTO
#pragma once
#include <stdint.h>

namespace v2 {

enum class Estado : uint8_t { INICIO, ESPERA, CALIBRACION, LISTO, ARRANQUE, SIGUIENDO, RECUPERACION, PARADA, ERROR };
const char* nombre(Estado e);

// Código de error = número de parpadeos del LED rojo.
enum class Error : uint8_t { NINGUNO = 0, BATERIA = 1, MOTOR = 2, IMU = 3, BAROMETROS = 4, SENSORES = 5, TEMPERATURA = 6 };
enum class Motivo : uint8_t { NINGUNO, LINEA_PERDIDA, BOTON, BATERIA_CRITICA, CAL_INSUFICIENTE, BATERIA_ARRANQUE };

struct Eventos {
  bool start = false, cal = false;          // pulsos de los botones (ya sin rebote)
  bool autoprueba_hecha = false;            // INICIO terminó de revisar los periféricos
  Error autoprueba = Error::NINGUNO;        // resultado de la autoprueba
  bool cal_guardada_ok = false;
  bool cal_suficiente = false, cal_tiempo_agotado = false;
  bool bateria_permite = true, bateria_critica = false;
  bool succion_lista = false;               // el supervisor confirmó la succión o pasó al modo sin succión
  bool buscando = false;                    // línea no vista o derrape: el controlador está recuperando
  bool linea_perdida = false;               // se acabó el tiempo de búsqueda (C07)
  bool falla_sensores = false, falla_motor = false, sobrecalentado = false;
};

class MaquinaV2 {
 public:
  explicit MaquinaV2(uint32_t bloqueo_start_ms = 500) : bloqueo_ms_(bloqueo_start_ms) {}
  bool actualizar(const Eventos& ev, uint32_t ahora_ms);   // true si cambió de estado
  Estado estado() const { return e_; }
  Error error() const { return err_; }
  Motivo motivo() const { return motivo_; }
  uint32_t desde_ms() const { return t_; }
  bool motores_habilitados() const { return e_ == Estado::SIGUIENDO || e_ == Estado::RECUPERACION; }
  bool ventilador_encendido() const { return e_ == Estado::ARRANQUE || motores_habilitados(); }
  bool frenado_activo() const { return e_ == Estado::ARRANQUE; }   // puente H en freno mientras sube la presión
  bool recien_arrancado() const { return arranque_; }              // primer ciclo de SIGUIENDO

 private:
  void ir(Estado e, uint32_t t, Motivo m = Motivo::NINGUNO, Error er = Error::NINGUNO);
  Estado e_ = Estado::INICIO;
  Error err_ = Error::NINGUNO;
  Motivo motivo_ = Motivo::NINGUNO;
  uint32_t t_ = 0, t_carrera_ = 0, bloqueo_ms_;
  bool arranque_ = false;
};

}  // namespace v2
