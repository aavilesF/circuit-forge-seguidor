// Robot de emergencia · autocalibración girando sobre la línea (consola `autocal`). C++ puro, se prueba en la PC.
//
// Se guía por los SENSORES, no por tiempos (las RPM reales del N20 no se conocen):
//   1. DERECHA: gira a la derecha (izq +u, der −u). La línea se corre a la izquierda de la barra; termina cuando el
//      sensor activo de más a la izquierda ya vio blanco y negro (contraste ≥ `contraste`).
//   2. IZQUIERDA: gira al otro lado hasta que el sensor de más a la derecha también lo vio y TODOS los activos
//      tienen contraste (calibración lista).
//   3. CENTRAR: con la calibración nueva, gira hacia la línea hasta tenerla a ≤ centro_mm del centro.
// Cada fase tiene tiempo máximo (t_max; la 2.ª el doble). Si se acaba en 1 o 2 → FALLA (se conserva la calibración
// anterior). Si se acaba en 3, la calibración es buena pero el robot no quedó centrado.
// Requisitos: robot CENTRADO sobre la línea al empezar e inversiones de motores y sensores ya comprobadas. Si en la
// fase 1 la línea aparece primero en el sensor de la derecha, el giro va al revés: FALLA inmediata (al_reves()).
#pragma once
#include <stdint.h>

#include "posicion.h"

namespace autocal {

enum class Fase : uint8_t { DERECHA, IZQUIERDA, CENTRAR, LISTA, FALLA };
const char* nombre(Fase f);

struct Param {
  float u = 0.20f;          // mando de giro (fracción del máximo)
  float t_max_s = 1.5f;     // s máximos por fase
  float contraste = 150.0f; // cuentas mínimas blanco-negro por sensor
  float centro_mm = 4.0f;   // tolerancia para dar por centrado
  float umbral = 0.10f, confianza = 0.30f;   // los de la estimación de posición
  uint32_t mascara = 0xFFFFu; // todos (solo cuentan los bits de los n sensores)
};

struct Salida {
  float izq = 0.0f, der = 0.0f;   // mando de cada rueda (−1..1), antes de inversiones
  bool termino = false;
  bool cal_ok = false;            // todos los sensores activos con contraste
  bool centrado = false;
};

class AutoCal {
 public:
  // Reinicia `cal` para n sensores y empieza en DERECHA.
  void iniciar(int n, const Param& p, posicion::Calibracion& cal);
  // refl: reflectancia (ya filtrada) de este ciclo, en orden físico (0 = izquierda).
  Salida paso(const float* refl, posicion::Calibracion& cal, const posicion::Geometria& g, float dt_s);
  Fase fase() const { return f_; }
  bool al_reves() const { return al_reves_; }   // FALLA porque el giro fue al revés (revisar inversiones)

 private:
  void cambiar(Fase f) { f_ = f; t_ = 0.0f; }
  float contraste_req(const posicion::Calibracion& cal) const;
  Param p_;
  Fase f_ = Fase::FALLA;
  float t_ = 0.0f;
  int n_ = 0, izq_ = -1, der_ = -1;
  bool cal_ok_ = false, centrado_ = false, al_reves_ = false;
};

}  // namespace autocal
