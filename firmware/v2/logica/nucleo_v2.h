// V2 · Núcleo del firmware: todo lo que decide el robot en cada ciclo de 1 kHz, sin tocar el hardware.
// main.cpp junta las entradas (ADC, encoders, IMU, barómetros, botones), llama a ciclo() y aplica las salidas
// (PWM, freno, nSLEEP, ESC, LED, zumbador). Así el mismo código corre en la PC con un modelo de la pista
// (firmware/v2/pruebas) y en el STM32G474.
#pragma once
#include <stdint.h>

#include "../../logica/posicion.h"
#include "../../logica/sf_logica.h"
#include "../config_v2.h"
#include "estados_v2.h"
#include "indicadores.h"
#include "mapa.h"
#include "motor_v2.h"
#include "parametros_v2.h"
#include "succion.h"

namespace v2 {

constexpr int N = cfg2::N_SENSORES;

struct Entradas {
  uint32_t t_ms = 0;
  float dt = 0.001f;
  uint16_t ambiente[N] = {0}, encendido[N] = {0};   // cuentas de 12 bits con emisores apagados y encendidos
  int32_t d_enc_izq = 0, d_enc_der = 0;             // cuentas en este ciclo (ya con el signo del montaje)
  float gz = 0.0f;                                  // rad/s (positivo = giro a la izquierda), sin sesgo
  bool imu_ok = true;
  float i_izq = 0.0f, i_der = 0.0f;                 // A medidos por IPROPI (|I|)
  float v_bat = 7.4f;
  bool btn_start = false, btn_cal = false;          // nivel crudo (true = presionado)
  bool nfault = false;                              // nFAULT en bajo (falla o recorte de corriente)
  bool baro_nueva = false, baro_ok = true;          // hay lectura nueva de los dos barómetros
  float p_amb = 0.0f, p_cam = 0.0f;                 // Pa
  bool autoprueba_hecha = true;
  Error autoprueba = Error::NINGUNO;
};

struct Salidas {
  float ciclo_izq = 0.0f, ciclo_der = 0.0f;         // −1..1, con signo (PH = dirección, EN = |ciclo|)
  bool despierto = false;                           // nSLEEP en alto
  bool frenar = false;                              // EN = 0 con el puente despierto (freno de bajo lado)
  float esc = 0.0f;                                 // 0..1
  Indicadores ind;
};

class NucleoV2 {
 public:
  NucleoV2();
  void defecto();                                   // parámetros de fábrica
  void cargar(const Guardado& g);                   // desde la flash (ya validada)
  void guardar(Guardado& g) const;
  void ciclo(const Entradas& in, Salidas& out);

  // acceso para la consola y la telemetría
  Parametros& prm() { return p_; }
  const MaquinaV2& maquina() const { return maq_; }
  const Mapa& mapa() const { return mapa_; }
  const SupervisorSuccion& succion() const { return suc_; }
  SupervisorSuccion& succion() { return suc_; }
  const posicion::Calibracion& cal() const { return cal_; }
  const sf::Lectura& lectura() const { return lect_; }
  const sf::Salida& control() const { return sal_; }
  float temp_izq() const { return term_i_.elevacion(); }
  float temp_der() const { return term_d_.elevacion(); }
  float v_rueda_izq() const { return w_i_ * cfg2::D_LLANTA * 0.5f; }
  float v_rueda_der() const { return w_d_ * cfg2::D_LLANTA * 0.5f; }
  float v_tope() const { return v_tope_; }
  bool cal_valida() const { return cal_ok_; }
  void fijar_cero_presion(float dp) { suc_.fijar_cero(dp); }
  void aplicar_parametros();                        // tras `set`: actualiza el controlador y el supervisor

 private:
  void leer_linea(const Entradas& in);
  void motores(const Entradas& in, Salidas& out);

  Parametros p_;
  posicion::Calibracion cal_;
  bool cal_ok_ = false;
  sf::ControlSF ctrl_;
  sf::Lectura lect_{0, false, false};
  sf::Salida sal_{0, 0, 0, false, false};
  MaquinaV2 maq_;
  Mapa mapa_;
  SupervisorSuccion suc_;
  ModeloMotor mot_;
  LazoCorriente lazo_i_, lazo_d_;
  EstimadorTermico term_i_, term_d_;
  float refl_[N] = {0}, osc_[N] = {0};
  float w_i_ = 0, w_d_ = 0, v_tope_ = 0;
  // botones y batería
  bool start_prev_ = false, cal_prev_ = false;
  uint32_t t_start_ = 0, t_cal_ = 0;
  bool start_estable_ = false, cal_estable_ = false;
  float v_bat_f_ = 0.0f;
  uint32_t t_bat_baja_ = 0;
  bool bat_baja_ = false, bat_iniciada_ = false;
  // fallas
  uint32_t t_sens_mal_ = 0, t_trabada_i_ = 0, t_trabada_d_ = 0, t_nfault_ = 0;
  bool sens_mal_ = false, trab_i_ = false, trab_d_ = false, nf_ = false;
  // derrape: guiñada del giroscopio contra la de los encoders
  uint32_t t_derrape_ = 0;
  bool derrape_ = false;
  // calibración
  uint32_t t_cal_inicio_ = 0;
  Melodia melodia_ = Melodia::NINGUNA;
  uint32_t t_melodia_ = 0;
  Estado previo_ = Estado::INICIO;
};

}  // namespace v2
