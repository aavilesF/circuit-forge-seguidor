#include "posicion.h"
#include <math.h>

namespace posicion {

static int limitar_n(int n) {
  if (n > par::MAX_SENSORES) return par::MAX_SENSORES;
  if (n < 1) return 1;
  return n;
}

Geometria geometria_recta(int n, float paso_mm, float dist_eje_mm) {
  Geometria g{};
  g.n = limitar_n(n);
  for (int i = 0; i < g.n; ++i) {
    g.x[i] = (i - (g.n - 1) * 0.5f) * paso_mm;
    g.y[i] = dist_eje_mm;
  }
  return g;
}

Geometria geometria_arco(int n, float paso_arco_mm, float radio_mm, float dist_eje_mm) {
  Geometria g{};
  g.n = limitar_n(n);
  const float dtheta = paso_arco_mm / radio_mm;
  for (int i = 0; i < g.n; ++i) {
    const float th = (i - (g.n - 1) * 0.5f) * dtheta;
    g.x[i] = radio_mm * sinf(th);
    g.y[i] = dist_eje_mm - radio_mm + radio_mm * cosf(th);
  }
  return g;
}

float reflectancia(const ModoSensor& modo, int raw_on, int raw_off) {
  float r;
  if (modo.resta_ambiente) {
    r = modo.luz_baja_voltaje ? float(raw_off - raw_on) : float(raw_on - raw_off);
  } else {
    r = modo.luz_baja_voltaje ? float(modo.adc_max - raw_on) : float(raw_on);
  }
  return r < 0.0f ? 0.0f : r;
}

void Calibracion::reiniciar(int n_sensores) {
  n = limitar_n(n_sensores);
  for (int i = 0; i < n; ++i) {
    minimo[i] = 1e9f;
    maximo[i] = -1e9f;
  }
}

void Calibracion::muestrear(const float* refl) {
  for (int i = 0; i < n; ++i) {
    if (refl[i] < minimo[i]) minimo[i] = refl[i];
    if (refl[i] > maximo[i]) maximo[i] = refl[i];
  }
}

bool Calibracion::lista(float rango_minimo) const {
  if (n <= 0) return false;
  for (int i = 0; i < n; ++i) {
    if (maximo[i] - minimo[i] < rango_minimo) return false;
  }
  return true;
}

void normalizar(const Calibracion& cal, const float* refl, float* oscuridad) {
  for (int i = 0; i < cal.n; ++i) {
    const float rango = cal.maximo[i] - cal.minimo[i];
    if (rango <= 1e-6f) {
      oscuridad[i] = 0.0f;  // sensor sin calibrar: se trata como blanco
      continue;
    }
    float d = 1.0f - (refl[i] - cal.minimo[i]) / rango;
    if (d < 0.0f) d = 0.0f;
    if (d > 1.0f) d = 1.0f;
    oscuridad[i] = d;
  }
}

bool lecturas_imposibles(const int* raw, int n, int adc_max, int margen) {
  if (n <= 0) return true;
  bool todos_bajos = true, todos_altos = true;
  for (int i = 0; i < n; ++i) {
    if (raw[i] > margen) todos_bajos = false;
    if (raw[i] < adc_max - margen) todos_altos = false;
  }
  return todos_bajos || todos_altos;
}

Estimacion estimar_posicion(const Geometria& g, const float* oscuridad,
                            float umbral_ruido, float confianza_min) {
  float escala = 1.0f - umbral_ruido;
  if (escala < 0.05f) escala = 0.05f;

  float suma = 0.0f, momento = 0.0f;
  for (int i = 0; i < g.n; ++i) {
    float d = (oscuridad[i] - umbral_ruido) / escala;
    if (d <= 0.0f) continue;
    if (d > 1.0f) d = 1.0f;
    suma += d;
    momento += d * g.x[i];
  }

  Estimacion e{0.0f, suma, false};
  if (suma >= confianza_min) {
    e.linea_visible = true;
    e.pos_mm = momento / suma;
  }
  return e;
}

}  // namespace posicion
