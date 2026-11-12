// Robot casero · filtro de las lecturas de los sensores (C++ puro, se prueba en la PC).
//
// Por qué: en placa fenólica los cables de los sensores son largos y pasan junto a los del motor (PWM de 20 kHz);
// aparecen picos sueltos y ruido. Por canal se hace:
//   1. mediana de las 3 últimas muestras → quita un pico aislado sin retrasar un escalón más de 1 periodo;
//   2. pasa-bajas de primer orden  y += a·(m − y)  → a = 1 lo desactiva; a = 0.5 a 400 Hz ≈ 3.6 ms de constante.
// El sobremuestreo (promediar varias lecturas del ADC en el mismo ciclo) se hace en el hardware (hw::leer).
#pragma once
#include "parametros.h"

namespace filtro {

float mediana3(float a, float b, float c);

struct Canal {
  float h[3] = {0.0f, 0.0f, 0.0f};
  int n = 0;           // muestras recibidas (hasta 3)
  float y = 0.0f;      // salida
  void reiniciar() { n = 0; y = 0.0f; }
  float paso(float x, float alfa);
};

struct Arreglo {
  Canal c[par::MAX_SENSORES];
  void reiniciar() { for (auto& k : c) k.reiniciar(); }
  // Filtra en sitio v[0..n-1]
  void aplicar(float* v, int n, float alfa) { for (int i = 0; i < n && i < par::MAX_SENSORES; ++i) v[i] = c[i].paso(v[i], alfa); }
};

}  // namespace filtro
