// V2 · Supervisor de la succión: mando del ESC, presión de la cámara y modo degradado.
// C++17 puro (se prueba en la PC).
//
// FASE1_FISICA §8 y FASE2_COMPONENTES §7: el robot no confía en la succión a ciegas. ΔP = presión ambiente − presión de
// la cámara (dos LPS22DF; el cero se toma en la calibración con el ventilador apagado). Al arrancar: ventilador en
// rampa con las ruedas frenadas, se confirma ΔP y recién entonces se sueltan los motores. Si ΔP cae (faldón gastado,
// escalón, ventilador) el perfil pasa al de "sin succión" y el LED de SUCCIÓN parpadea; si vuelve, se recupera.
#pragma once
#include <stdint.h>

namespace v2 {

struct ParamSuccion {
  float mando_crucero = 0.70f;   // 0..1 (fracción del acelerador del ESC) [S: ajustar con la prueba de báscula]
  float rampa_s = 0.6f;          // s de 0 al mando de crucero
  float dp_min = 150.0f;         // Pa: por debajo, la succión se considera perdida [S]
  float t_arranque_max = 1.5f;   // s: si ΔP no llega a dp_min, se corre sin succión
  float t_perdida = 0.05f;       // s con ΔP < dp_min para pasar a degradado (τ más rápido de T7b: 50 ms)
  float t_recupera = 0.3f;       // s con ΔP ≥ dp_min para volver
  float area = 0.0049f;          // m², cámara de 70 × 70 mm
  float fraccion_ruedas = 0.96f; // fracción de la fuerza sobre las ruedas motrices
  float alfa = 0.2f;             // filtro de ΔP (por muestra de 5 ms)
};

class SupervisorSuccion {
 public:
  enum class Estado : uint8_t { APAGADO, ARRANQUE, OK, DEGRADADO, SIN_SENSOR };

  void configurar(const ParamSuccion& p) { p_ = p; }
  // Cero de presión (calibración, ventilador apagado): diferencia ambiente − cámara en reposo.
  void fijar_cero(float dp_reposo) { cero_ = dp_reposo; }
  float cero() const { return cero_; }

  void encender(uint32_t ahora_ms);
  void apagar();
  // Nueva lectura de los dos barómetros (Pa). validas = false si alguno no respondió.
  void muestra(float p_ambiente, float p_camara, bool validas, uint32_t ahora_ms);
  // Una vez por ciclo de control.
  void actualizar(uint32_t ahora_ms);

  Estado estado() const { return e_; }
  float mando() const { return mando_; }          // 0..1 para el ESC
  float dp() const { return dp_f_; }              // Pa, filtrada y sin el cero
  float fuerza() const;                           // N sobre las ruedas motrices (0 si no hay succión confirmada)
  bool listo_para_correr() const { return e_ == Estado::OK || e_ == Estado::DEGRADADO || e_ == Estado::SIN_SENSOR; }
  bool con_succion() const { return e_ == Estado::OK; }

 private:
  ParamSuccion p_;
  Estado e_ = Estado::APAGADO;
  float cero_ = 0.0f, dp_f_ = 0.0f, mando_ = 0.0f;
  bool valida_ = false, hay_muestra_ = false;
  uint32_t t_inicio_ = 0, t_bajo_ = 0, t_alto_ = 0, t_ult_ = 0;
  bool bajo_ = false, alto_ = false;
};

}  // namespace v2
