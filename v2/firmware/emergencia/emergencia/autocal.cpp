#include "autocal.h"

#include <math.h>

#include "utiles.h"

namespace autocal {

const char* nombre(Fase f) {
  switch (f) {
    case Fase::DERECHA: return "girando a la derecha";
    case Fase::IZQUIERDA: return "girando a la izquierda";
    case Fase::CENTRAR: return "centrando";
    case Fase::LISTA: return "lista";
    case Fase::FALLA: return "falla";
  }
  return "?";
}

void AutoCal::iniciar(int n, const Param& p, posicion::Calibracion& cal) {
  p_ = p;
  n_ = n;
  cal.reiniciar(n);
  izq_ = util::primer_activo(p.mascara, n);
  der_ = util::ultimo_activo(p.mascara, n);
  cal_ok_ = centrado_ = al_reves_ = false;
  cambiar(izq_ >= 0 && der_ > izq_ ? Fase::DERECHA : Fase::FALLA);
}

// Contraste que exige la autocalibración para decir que un sensor "vio la línea": el mínimo configurado, pero nunca
// menos del 40 % del blanco más claro visto. Así el ruido (decenas de cuentas) no se confunde con la línea negra
// (miles de cuentas de diferencia) aunque `contraste` sea bajo.
float AutoCal::contraste_req(const posicion::Calibracion& cal) const {
  float blanco = 0.0f;
  for (int i = 0; i < cal.n; ++i)
    if (util::activo(p_.mascara, i) && cal.maximo[i] > blanco) blanco = cal.maximo[i];
  const float rel = 0.4f * blanco;
  return rel > p_.contraste ? rel : p_.contraste;
}

Salida AutoCal::paso(const float* refl, posicion::Calibracion& cal, const posicion::Geometria& g, float dt) {
  Salida s;
  if (dt > 0.0f) t_ += dt;
  float u = 0.0f;
  switch (f_) {
    case Fase::DERECHA: {
      cal.muestrear(refl);
      u = p_.u;
      const float req = contraste_req(cal);
      if (util::contraste_ok(cal, izq_, req)) cambiar(Fase::IZQUIERDA);
      else if (util::contraste_ok(cal, der_, req)) { al_reves_ = true; cambiar(Fase::FALLA); }
      else if (t_ > p_.t_max_s) cambiar(Fase::FALLA);
      // Al girar a la derecha la línea se va hacia la izquierda de la barra: si la ve primero el sensor de la DERECHA,
      // el robot gira al revés (inversiones mal) y se aborta antes de dar media vuelta y "encontrarla" por detrás.
      break;
    }
    case Fase::IZQUIERDA:
      cal.muestrear(refl);
      u = -p_.u;
      if (util::contraste_ok(cal, der_, contraste_req(cal)) && util::cal_lista(cal, contraste_req(cal), p_.mascara)) {
        cal_ok_ = true;
        cambiar(Fase::CENTRAR);
      } else if (t_ > 2.0f * p_.t_max_s) {
        cambiar(Fase::FALLA);
      }
      break;
    case Fase::CENTRAR: {
      cal.muestrear(refl);
      float osc[par::MAX_SENSORES];
      posicion::normalizar(cal, refl, osc);
      util::enmascarar(osc, n_, p_.mascara);
      const posicion::Estimacion e = posicion::estimar_posicion(g, osc, p_.umbral, p_.confianza);
      if (e.linea_visible && fabsf(e.pos_mm) <= p_.centro_mm) {
        centrado_ = true;
        cambiar(Fase::LISTA);
      } else if (t_ > p_.t_max_s) {
        cambiar(Fase::LISTA);   // calibración buena, pero no quedó centrado
      } else {
        // línea a la derecha (pos > 0) → girar a la derecha (u > 0); al terminar la fase 2 la línea quedó a la derecha
        const float lado = e.linea_visible ? (e.pos_mm > 0.0f ? 1.0f : -1.0f) : 1.0f;
        u = lado * 0.6f * p_.u;
      }
      break;
    }
    case Fase::LISTA:
    case Fase::FALLA:
      break;
  }
  s.izq = u;
  s.der = -u;
  s.termino = (f_ == Fase::LISTA || f_ == Fase::FALLA);
  if (s.termino) s.izq = s.der = 0.0f;
  s.cal_ok = cal_ok_;
  s.centrado = centrado_;
  return s;
}

}  // namespace autocal
