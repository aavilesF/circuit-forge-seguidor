// V2 · Mapa de la vuelta y perfil de velocidad factible.
// C++17 puro: se prueba en la PC contra el simulador (perfil_vuelta de sim/v2/fase1_v2.py, vectores dorados).
//
// Reglamento (FASE1_AUDITORIA §4): mapas y memoria permitidos, sin radio; la pista PUEDE cambiar entre rondas. Por eso
// el mapa se aprende en cada ronda: la vuelta 1 es reactiva y graba la curvatura (giroscopio / distancia de los
// encoders, una muestra cada 1 cm); al reconocer el cierre de la vuelta calcula el perfil factible (frenado y
// aceleración dentro de la adherencia) y en las vueltas siguientes lo usa, verificando a cada paso que la pista sigue
// coincidiendo. Si deja de coincidir, el mapa se declara inválido y el robot vuelve a reactivo (y aprende otra vez).
#pragma once
#include <stdint.h>

namespace v2 {

// Perfil factible sobre topes cap[0..n) (uno por tramo de largo ds) desde v_ini, conociendo toda la pista: pasada hacia
// atrás con a_fr y hacia adelante con a_acc. vel[0..n] (n + 1 nodos). Igual a perfil_vuelta(..., horizonte=None).
// Devuelve la desaceleración máxima exigida (≤ a_fr si es factible).
float perfil_factible(const float* cap, int n, float a_acc, float a_fr, float ds, float v_ini, float* vel);

// Lo mismo en una vuelta cerrada que se repite (el robot llega en movimiento): vel[0..n), cíclico.
void perfil_ciclico(const float* cap, int n, float a_acc, float a_fr, float ds, float* vel);

// Tope por curvatura: v ≤ sqrt(a_lat / |κ|), y ≤ v_max.
float tope_curvatura(float kappa, float a_lat, float v_max);

struct ParamMapa {
  float ds = 0.01f;            // m por muestra
  float largo_min = 1.5f;      // m: no se busca el cierre antes
  float giro_firma = 0.5f;     // rad de giro acumulado que debe tener la firma de inicio (incluye la primera curva)
  float firma_max = 3.0f;      // m, largo máximo de la firma
  float tol_rumbo = 0.35f;     // rad: el giro de una vuelta debe ser 2πk ± tol (k = 0 en un ocho)
  float err_cierre = 1.5f;     // 1/m RMS: diferencia de curvatura aceptada al cerrar
  float ventana_loc = 0.6f;    // m de curvatura medida para localizarse en el mapa
  float busqueda = 0.12f;      // m: corrección máxima de posición por comparación
  float cada = 0.25f;          // m entre comparaciones
  float err_loc = 2.0f;        // 1/m RMS: más que esto es "no coincide"
  int   fallos_max = 3;        // comparaciones seguidas que no coinciden -> mapa inválido
};

class Mapa {
 public:
  static constexpr int MAX = 3000;              // 30 m a 1 cm
  enum class Modo : uint8_t { APRENDIENDO, CERRADO, INVALIDO };

  void reiniciar(const ParamMapa& p);
  // Una vez por ciclo de control: ds (m, avance de los encoders) y dpsi (rad, giro medido por el giroscopio).
  void avanzar(float ds, float dpsi);

  Modo modo() const { return modo_; }
  int muestras() const { return modo_ == Modo::CERRADO ? n_ : i_; }
  float largo() const { return n_ * p_.ds; }
  float posicion() const { return (pos_ + frac_ / p_.ds) * p_.ds; }   // m desde el inicio del mapa
  int vueltas() const { return vueltas_; }
  float error_ultimo() const { return err_ult_; }
  const float* curvatura() const { return k_; }
  bool tomar_cierre() { const bool c = cierre_nuevo_; cierre_nuevo_ = false; return c; }

  // Perfil para las vueltas con mapa: lo llama el ciclo principal (fuera de la interrupción) al cerrar.
  void calcular_perfil(float a_lat, float a_acc, float a_fr, float v_max);
  bool perfil_listo() const { return perfil_ok_ && modo_ == Modo::CERRADO; }
  float v_perfil(float adelanto_m) const;        // tope de velocidad del perfil adelanto_m más adelante

 private:
  void muestra(float kappa, float dpsi);
  void buscar_cierre();
  void localizar();
  float err_rms(const float* a, int ia, const float* b, int ib, int n, int mod_b) const;

  ParamMapa p_;
  Modo modo_ = Modo::APRENDIENDO;
  float k_[MAX];          // curvatura de cada muestra (1/m)
  float psi_[MAX];        // rumbo acumulado al final de cada muestra (rad)
  float v_[MAX];          // perfil (m/s)
  float med_[128];        // curvatura medida reciente (anillo) para localizarse
  int   i_ = 0;           // muestras grabadas (aprendiendo)
  int   n_ = 0;           // muestras de una vuelta (cerrado)
  int   pos_ = 0;         // muestra actual en el mapa
  int   w_firma_ = 0;
  int   mejor_n_ = 0;
  float mejor_err_ = 1e9f;
  int   desde_ = 0;       // muestras desde la última comparación
  int   fallos_ = 0;
  int   vueltas_ = 0;
  int   im_ = 0;          // índice del anillo med_
  int   nm_ = 0;
  float acum_ds_ = 0, acum_dpsi_ = 0, psi_tot_ = 0, frac_ = 0;
  float err_ult_ = 0;
  float giro_ = 0;        // giro acumulado de la firma de inicio (rad)
  int   marca_ = -1;
  bool  cierre_nuevo_ = false;
  bool  perfil_ok_ = false;
};

}  // namespace v2
