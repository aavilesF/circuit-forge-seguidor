#include "filtro.h"

namespace filtro {

float mediana3(float a, float b, float c) {
  if (a > b) { const float t = a; a = b; b = t; }
  if (b > c) { const float t = b; b = c; c = t; }
  if (a > b) { const float t = a; a = b; b = t; }
  return b;
}

float Canal::paso(float x, float alfa) {
  if (alfa <= 0.0f) alfa = 0.01f;
  if (alfa > 1.0f) alfa = 1.0f;
  h[0] = h[1];
  h[1] = h[2];
  h[2] = x;
  if (n < 3) ++n;
  // con menos de 3 muestras no hay mediana: se usa la última (arranque sin transitorio)
  const float m = (n < 3) ? x : mediana3(h[0], h[1], h[2]);
  y = (n == 1) ? m : y + alfa * (m - y);
  return y;
}

}  // namespace filtro
