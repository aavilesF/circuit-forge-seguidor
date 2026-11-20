// Robot de emergencia · del mando del control (−1..1) al ciclo de PWM de cada entrada del DRV8833. C++ puro.
// Base: firmware/robot-casero (HISTÓRICO), con rampa de frenado propia y comentarios del hardware vigente.
//
// El DRV8833 entrega 1.5 A RMS por puente y se protege por sobrecorriente desde 2 A (mín.) [V TI SLVSAR1]; no mide
// corriente y nFAULT no está conectado (P13). Por eso el firmware, sin sensor, protege en este orden:
//   1. tope de ciclo: |d| ≤ min(pwm_max, v_motor_max / v_puente). El puente recibe +6V_MOT del MP1584 U2 (6.0 V):
//      con v_motor_max = 6 V manda pwm_max;
//   2. rampa: al ACELERAR |Δd| ≤ rampa·dt; al FRENAR (bajar |d| o invertir) |Δd| ≤ rampa_freno·dt. Los arranques y
//      reversas bruscas son los que piden más corriente; frenar puede ser más rápido;
//   3. límite de corriente con un MODELO del motor y la velocidad ESTIMADA (no hay encoders):
//        I = (d·V − ke·ω)/R  →  d ∈ [(ke·ω − Imax·R)/V, (ke·ω + Imax·R)/V]
//        ω estimada: primer orden hacia la velocidad sin carga, dω/dt = (d·V/ke − ω)/τ   (τ grande = más prudente)
//   4. suma de las dos corrientes estimadas ≤ i_total (lo que aguanta el MP1584 U2 sin caerse).
// Las constantes del motor son [E] hasta medir el N20 real (corriente de bloqueo con multímetro, RPM sin carga).
// Las PARADAS (START, USB, errores) no pasan por la rampa: el programa principal pone el puente en freno directo.
#pragma once

namespace motor {

struct Modelo {
  float R = 6.0f;      // Ω (6 V / ~1 A de bloqueo) [E]
  float ke = 0.0533f;  // V·s/rad en la rueda: (6 − 0.07·6) / (1000 rpm) [E]
  float tau = 0.08f;   // s, constante para la velocidad estimada (cargado, prudente) [E]
  // v_nom: V; rpm0: RPM sin carga en la salida; i_bloqueo, i_vacio: A
  static Modelo desde_ficha(float v_nom, float rpm0, float i_bloqueo, float i_vacio, float tau_s);
  float corriente(float d, float v, float w) const { return (d * v - ke * w) / R; }
};

struct Limites {
  float pwm_max = 0.90f;      // tope absoluto del ciclo
  float v_motor_max = 6.0f;   // V efectivos máximos sobre el motor (N20 de 6 V)
  float i_max = 1.2f;         // A por motor (< 1.5 A RMS del DRV8833)
  float i_total = 2.0f;       // A entre los dos motores
  float rampa = 6.0f;         // 1/s al acelerar: de 0 a 100 % en ~170 ms
  float rampa_freno = 6.0f;   // 1/s al frenar o invertir (≥ rampa normalmente)
};

// Fracción de tiempo en ALTO de cada entrada del puente (0..1)
struct Puente { float in1, in2; };
enum class Decaimiento { LENTO, RAPIDO };

// Tabla 2 de TI: adelante lento = IN1 1, IN2 PWM; atrás lento = IN1 PWM, IN2 1; rápido: PWM/0 y 0/PWM.
// d = ciclo efectivo con signo (−1..1). d = 0 en lento = freno (1,1).
Puente drv8833(float d, Decaimiento k);
inline Puente libre() { return {0.0f, 0.0f}; }
inline Puente freno() { return {1.0f, 1.0f}; }

class Accionamiento {
 public:
  void configurar(const Modelo& m, const Limites& l) { m_ = m; l_ = l; }
  void reiniciar() { d_[0] = d_[1] = w_[0] = w_[1] = i_[0] = i_[1] = 0.0f; }
  // cmd: −1..1 pedido por el control; v_fuente: voltaje en VCC del DRV8833 (V); dt en s
  void actualizar(float cmd_izq, float cmd_der, float v_fuente, float dt);
  float ciclo(int k) const { return d_[k]; }       // 0 = izq, 1 = der
  float corriente(int k) const { return i_[k]; }   // A estimados
  float velocidad(int k) const { return w_[k]; }   // rad/s estimados en la rueda
  float tope(float v_fuente) const;                // ciclo máximo permitido

 private:
  Modelo m_;
  Limites l_;
  float d_[2] = {0, 0}, w_[2] = {0, 0}, i_[2] = {0, 0};
};

}  // namespace motor
