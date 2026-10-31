// Controlador PID discreto con saturación, anti-windup y derivada filtrada.
// C++ puro: se prueba en la computadora y lo usa el simulador.
#pragma once

class PID {
 public:
  PID() {}
  PID(float kp, float ki, float kd) : kp_(kp), ki_(ki), kd_(kd) {}

  void  fijar(float kp, float ki, float kd) { kp_ = kp; ki_ = ki; kd_ = kd; }
  void  limites(float salida_min, float salida_max) { min_ = salida_min; max_ = salida_max; }
  void  filtro_derivada(float tau_s) { tau_ = tau_s < 0.0f ? 0.0f : tau_s; }
  void  reiniciar();

  // error: lo que se quiere corregir. dt_s: tiempo real desde la llamada anterior.
  float calcular(float error, float dt_s);

  float integral() const { return integ_; }
  float derivada() const { return d_filt_; }

 private:
  float kp_ = 0.0f, ki_ = 0.0f, kd_ = 0.0f;
  float min_ = -1.0f, max_ = 1.0f;
  float tau_ = 0.01f;           // constante del filtro de la derivada (s)
  float integ_ = 0.0f;          // integral del error
  float e_prev_ = 0.0f;
  float d_filt_ = 0.0f;
  float ultima_ = 0.0f;
  bool  inicializado_ = false;  // evita el golpe de derivada en la primera muestra
};
