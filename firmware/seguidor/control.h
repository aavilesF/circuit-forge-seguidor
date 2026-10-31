// Controlador de seguimiento de línea: convierte la posición estimada de la línea
// en órdenes de velocidad para las dos ruedas. C++ puro (lo usa también el simulador).
//
// Convención de signos (marco: x a la derecha):
//   error > 0  -> la línea está a la DERECHA del centro del robot
//   u > 0      -> el robot debe girar a la derecha: rueda izquierda más rápida
//   izq = v + u,  der = v - u
// Comprobar en el robot real con las ruedas en el aire antes de ponerlo en la pista.
#pragma once
#include "pid.h"
#include "posicion.h"

struct ParamControl {
  float kp, ki, kd;       // ganancias del PID (velocidad normalizada por mm de error)
  float vbase;            // velocidad base, 0 a 1 (fracción de la velocidad máxima)
  float freno_error;      // 0 a 1: cuánta velocidad base se pierde con error grande
  float error_ref_mm;     // error con el que se aplica el freno completo
  float vmin_rel;         // piso de la velocidad relativa al frenar (0 a 1)
  float u_max;            // límite de la corrección del PID
  float rueda_min;        // velocidad mínima de cada rueda (negativa permite girar frenando)
  float tau_d_s;          // constante del filtro de la derivada (s)
  float t_retencion_s;    // tiempo que mantiene la última orden si no ve la línea (huecos)
  float t_busqueda_s;     // tiempo de búsqueda antes de dar la línea por perdida
  float u_busqueda;       // corrección durante la búsqueda
  float vbusqueda_rel;    // velocidad relativa durante la búsqueda
};

ParamControl param_por_defecto();

struct SalidaControl {
  float izq, der;       // órdenes de rueda, -1 a 1
  float error_mm;       // error usado en este ciclo
  float u;              // corrección aplicada
  bool  buscando;       // sin ver la línea más allá del tiempo de retención
  bool  linea_perdida;  // se acabó el tiempo de búsqueda: hay que parar
};

class ControladorLinea {
 public:
  explicit ControladorLinea(const ParamControl& p);
  void fijar(const ParamControl& p);
  const ParamControl& param() const { return p_; }
  void reiniciar();
  SalidaControl actualizar(const posicion::Estimacion& est, float dt_s);

 private:
  ParamControl p_;
  PID   pid_;
  float t_sin_linea_ = 0.0f;
  float ultimo_error_ = 0.0f;
  float ultima_u_ = 0.0f;
  float ultimo_signo_ = 1.0f;
};
