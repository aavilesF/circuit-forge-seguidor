// V2 · Modelo del motor #5183, límite de corriente por motor y estimador térmico I²t.
// C++17 puro (sin dependencias del MCU): se prueba en la PC (firmware/v2/pruebas).
//
// Por qué (FASE35_CORRECCIONES §3): frenar a la adherencia completa pide ≤ 1.57 A; más corriente solo patina la llanta
// y calienta el motor. El DRV8874 recorta a ITRIP ≈ 1.56 A por hardware; el firmware limita a 1.5 A y, si la elevación
// estimada del devanado pasa de 40 K, baja el límite; a 50 K declara error y apaga los motores.
//
// Modelo (fase lenta del DRV8874 en modo PH/EN: EN = 0 frena con los dos transistores bajos [V SLVSF66A]):
//   corriente del devanado I = (d · Vbat − ke · ω) / R      d = ciclo con signo, ω = velocidad de la rueda
// Para |I| ≤ Imax el ciclo debe quedar en [(ke·ω − Imax·R)/Vbat, (ke·ω + Imax·R)/Vbat].
#pragma once
#include <stdint.h>

namespace v2 {

struct ModeloMotor {
  float R = 4.0f;      // Ω
  float ke = 0.0f;     // V·s/rad en la salida de la reductora
  float kt = 0.0f;     // N·m/A en la salida
  float i0 = 0.15f;    // A sin carga

  // Desde la ficha (valores a la tensión nominal, en la salida de la reductora): R = V/Ibloqueo,
  // ke = (V − I0·R)/ω0, kt = par de bloqueo / (Ibloqueo − I0). Igual que sf::Motor de V1.
  static ModeloMotor desde_ficha(float v_nom, float rpm0, float par_bloqueo, float i_bloqueo, float i_vacio);
  float corriente(float ciclo, float v_bat, float w) const { return (ciclo * v_bat - ke * w) / R; }
};

// Recorta el ciclo pedido para que la corriente del modelo no pase de ±i_max. También aplica el tope de tensión
// efectiva del motor (|d| ≤ v_lim / v_bat). Devuelve el ciclo aplicado.
float limitar_ciclo(const ModeloMotor& m, float ciclo, float w, float v_bat, float i_max, float v_lim);

// Corrige el modelo con la corriente medida por IPROPI (|I|, el DRV8874 mide el transistor bajo [V]):
// si la medida pasa del límite, reduce el límite efectivo del modelo (k < 1); se recupera despacio.
class LazoCorriente {
 public:
  void reiniciar() { k_ = 1.0f; }
  // i_medida: |I| en A; i_lim: límite vigente; dt en s. Devuelve el límite efectivo a usar en limitar_ciclo().
  float actualizar(float i_medida, float i_lim, float dt);
  float k() const { return k_; }

 private:
  float k_ = 1.0f;
};

// Estimador térmico de primer orden del devanado: Cth · dT/dt = I²·R − T/Rth (T = elevación sobre el ambiente).
// Constantes [E]: Rth 40 K/W, Cth 3 J/K (Pololu no las publica). Se integra con la corriente estimada o medida.
class EstimadorTermico {
 public:
  EstimadorTermico(float R, float Rth, float Cth) : R_(R), Rth_(Rth), Cth_(Cth) {}
  void paso(float i, float dt);
  float elevacion() const { return T_; }
  void fijar(float T) { T_ = T; }
  // Límite de corriente según la elevación: i_nom hasta t_reduce; baja en línea recta hasta i_min en t_max.
  float limite(float i_nom, float i_min, float t_reduce, float t_max) const;
  bool sobrecalentado(float t_max) const { return T_ >= t_max; }

 private:
  float R_, Rth_, Cth_;
  float T_ = 0.0f;
};

}  // namespace v2
