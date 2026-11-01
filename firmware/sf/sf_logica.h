// Lógica pura del Speed Follower (C++17, sin Arduino). Traducción 1:1 de speed-follower/sim/control.py
// (ControlSF) y de _estimar() de simular.py, verificada con vectores dorados (pruebas/test_sf.cpp).
// Unidades SI. Convención: e > 0 = línea a la DERECHA del robot.
#pragma once
#include <stdint.h>

namespace sf {

// Motor DC con reductora, modelo lineal desde datos de ficha (valores a v_nom, salida de la reductora).
struct Motor {
  float v_nom;   // V
  float rpm0;    // RPM sin carga
  float ts;      // N·m par de bloqueo
  float i_s;     // A corriente de bloqueo
  float i0;      // A corriente sin carga
  float R() const { return v_nom / i_s; }
  float w0() const { return rpm0 * 6.2831853f / 60.0f; }
  float ke() const { return (v_nom - i0 * R()) / w0(); }
  float kt() const { return ts / (i_s - i0); }
};

// Pololu HPCB 12 V 15:1 (ficha Pololu): 2200 RPM, 0.25 kg·cm, 0.75 A, 0.08 A sin carga.
constexpr float KGCM = 0.0980665f;
inline Motor motor_pololu_12v_15() { return Motor{12.0f, 2200.0f, 0.25f * KGCM, 0.75f, 0.08f}; }
// GA12-N20 6 V 1000 RPM: SOLO RPM e I0 publicados; par y bloqueo SUPUESTOS hasta medir P1.
inline Motor motor_ga12_n20_6v_supuesto() { return Motor{6.0f, 1000.0f, 0.30f * KGCM, 0.67f, 0.2f}; }

struct Robot {
  Motor motor;
  float diam = 0.033f;        // m
  float W = 0.085f;           // m entre ruedas
  float masa = 0.20f;         // kg
  float L = 0.130f;           // m cuello
  int   n_sens = 8;
  float paso = 0.0095f;       // m
  float v_max_motor = 99.0f;  // V; 6.0 para motores de 6 V en 2S
  float r() const { return diam * 0.5f; }
  float semibarra() const { return (n_sens - 1) * paso * 0.5f; }
};

struct ParamSF {
  float v_max = 1.2f;         // m/s
  float a_lat = 4.0f;         // m/s²
  float a_lon = 4.0f;         // m/s²
  float k_pp = 1.0f;
  float kp = 120.0f;          // ciclo por metro
  float kd = 4.0f;            // ciclo·s por metro
  float tau_d = 0.004f;       // s
  float tau_k = 0.030f;       // s
  bool  permitir_inversion = false;
  float e_critico = 0.80f;
  float d_inv = 0.30f;
  bool  ff_acel = true;
  bool  freno_activo = false; // probado en simulación (S9): no aporta; apagado
  float t_perdida = 0.30f;    // s sin ver la línea antes de declararla perdida
  int   fuente_k = 0;
  float piso = 0.0f;          // ciclo mínimo de la rueda interior (0 = sin inversión; < 0 permite frenar con contracorriente)         // curvatura del perfil: 0 = solo error (C2), 1 = + modelo del motor (C3m), 2 = + giroscopio (C3g)
};

// Estimación de la línea a partir de lecturas normalizadas (0 blanco, 1 negro), igual que simular._estimar.
struct Lectura {
  float e;        // m
  bool visible;
  bool borde;     // la línea toca un sensor extremo
};
Lectura estimar(const float* lect, int n, float paso, float umbral = 0.25f);
// Igual, con la coordenada lateral real de cada sensor (barra en arco o paso no uniforme).
// y[i] en m, positivo a la IZQUIERDA del robot; índice 0 = extremo derecho. e > 0 = línea a la derecha.
Lectura estimar_coord(const float* lect, const float* y, int n, float umbral = 0.25f);

struct Salida {
  float izq, der;     // ciclo de PWM con signo, -1..1 (relativo a Vbat)
  float v_cmd;        // m/s
  bool  inversion;    // una rueda negativa y la otra positiva
  bool  linea_perdida;
};

class ControlSF {
 public:
  ControlSF(const ParamSF& p, const Robot& r) : p_(p), r_(r) {}
  void reiniciar() { inicial_ = true; de_f_ = 0; k_f_ = 0; km_f_ = 0; v_cmd_ = 0; e_ult_ = 0; t_sin_ = 0; dl_ant_ = 0; dr_ant_ = 0; }
  void fijar(const ParamSF& p) { p_ = p; }
  const ParamSF& param() const { return p_; }
  // Núcleo idéntico al del simulador (sim/nucleo.py paso_sf): e ya decidido (último visto si no se ve la línea).
  // gz = velocidad de guiñada medida (rad/s), solo con fuente_k = 2.
  Salida paso(float e, bool borde, float dt, float v_bat, float gz = 0.0f);
  // Envoltura para el firmware: maneja la pérdida de línea.
  Salida actualizar(const Lectura& l, float dt, float v_bat, float gz = 0.0f);

 private:
  float ff(float v, float a, float v_bat) const;
  ParamSF p_;
  Robot r_;
  bool  inicial_ = true;
  float e_f_ = 0, de_f_ = 0, k_f_ = 0, km_f_ = 0, v_cmd_ = 0;
  float dl_ant_ = 0, dr_ant_ = 0;   // última salida (para la curvatura del modelo, C3m)
  float e_ult_ = 0, t_sin_ = 0;
};

}  // namespace sf
