// Lógica V1 (firmware/seguidor, rama main), probada en PC, más el "turbo" de recta (v2.1). Con v_recta ≤ vbase el
// turbo no actúa y la salida es idéntica a la V1.
// Controlador de seguimiento de línea: convierte la posición estimada de la línea
// en órdenes de velocidad para las dos ruedas. C++ puro (lo usa también el simulador).
//
// Turbo de recta (sin encoders: solo sensores, derivada del error y permiso externo):
//   ENTRA (tras t_confirmar_s seguidos): línea visible, |error| < recta_e_in, |de/dt| < recta_de_in,
//         confianza ≥ recta_conf_in, sin búsqueda y con permiso del programa (SIGUIENDO, batería y ciclo bien).
//   SALE al instante (g = 0): línea no visible (también en huecos), búsqueda, confianza < recta_conf_out o permiso
//         retirado; y tras recta_n_out ciclos seguidos (5 ms) con |error| > recta_e_out, o con el error ya fuera de
//         recta_e_in y alejándose del centro a más de recta_de_out. Histéresis: in < out. La derivada del turbo es
//         propia (filtro recta_tau_de_s): la del PID es demasiado ruidosa para esta decisión.
//   Velocidad base efectiva = vbase + g·(v_recta − vbase), con g subiendo de 0 a 1 en t_acel_s y cayendo a 0 en el
//   acto. La caída física la dan rampa_freno del motor (más rápida que la subida del turbo) y el freno en curva.
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
  // ---- turbo de recta (v_recta ≤ vbase = desactivado)
  float v_recta = 0.0f;          // velocidad base en recta confiable (misma escala que vbase)
  float recta_e_in = 3.0f;       // mm: |error| para entrar
  float recta_e_out = 6.0f;      // mm: |error| que cancela
  float recta_de_in = 40.0f;     // mm/s: |derivada del error| para entrar
  float recta_de_out = 150.0f;   // mm/s: |derivada del error| que cancela (si el error ya pasó recta_e_in y crece)
  float recta_conf_in = 1.2f;    // confianza mínima para entrar
  float recta_conf_out = 0.8f;   // confianza que cancela
  float t_confirmar_s = 0.15f;   // s seguidos cumpliendo la entrada
  float t_acel_s = 0.5f;         // s para pasar de vbase a v_recta
  float recta_tau_de_s = 0.04f;  // s: filtro de la derivada propia del turbo (la del PID, 10 ms, es muy ruidosa)
  int   recta_n_out = 2;         // ciclos seguidos con error/derivada fuera para cancelar (2 = 5 ms: ignora picos)
};

ParamControl param_por_defecto();

struct SalidaControl {
  float izq, der;       // órdenes de rueda, -1 a 1
  float error_mm;       // error usado en este ciclo
  float u;              // corrección aplicada
  bool  buscando;       // sin ver la línea más allá del tiempo de retención
  bool  linea_perdida;  // se acabó el tiempo de búsqueda: hay que parar
  float turbo;          // 0..1: fracción del turbo aplicada (0 = vbase)
  float v;              // velocidad base efectiva usada (antes de sumar u)
};

class ControladorLinea {
 public:
  explicit ControladorLinea(const ParamControl& p);
  void fijar(const ParamControl& p);
  const ParamControl& param() const { return p_; }
  void reiniciar();
  // turbo_permitido: lo da el programa (estado SIGUIENDO, batería sin aviso, ciclo a tiempo, sin "todo negro").
  SalidaControl actualizar(const posicion::Estimacion& est, float dt_s, bool turbo_permitido = true);
  bool en_recta() const { return recta_; }

 private:
  void cancelar_turbo() { g_ = 0.0f; recta_ = false; t_ok_ = 0.0f; n_fuera_ = 0; }
  ParamControl p_;
  PID   pid_;
  float t_sin_linea_ = 0.0f;
  float ultimo_error_ = 0.0f;
  float ultima_u_ = 0.0f;
  float ultimo_signo_ = 1.0f;
  float g_ = 0.0f, t_ok_ = 0.0f;
  bool  recta_ = false;
  float de_t_ = 0.0f, e_t_ = 0.0f;   // derivada propia del turbo y error anterior
  bool  ini_t_ = false;
  int   n_fuera_ = 0;
};
