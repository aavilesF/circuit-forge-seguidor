// V2 · Consola de texto por USB (CDC). Solo interpreta: el ciclo principal ejecuta. C++17 puro (se prueba en la PC).
// No hay comunicación inalámbrica (prohibida por el reglamento): la consola es por el cable USB-C del módulo.
//
//   ?                 ayuda                      t            telemetría a 50 Hz (encender/apagar)
//   e                 estado y diagnóstico       r            lecturas crudas de los 16 sensores
//   p                 lista de parámetros        set <p> <v>  cambia un parámetro (con rango)
//   w                 guarda en la flash         defecto      vuelve a los valores de fábrica
//   m                 mapa (largo, vueltas, error de localización)
//   prueba <i> <d>    motores 2 s con ciclo i, d (−0.5..0.5) — solo detenido y con las ruedas en el aire
//   esc <m>           ventilador 2 s con mando m (0..1) — solo detenido
//   cero              cero de presión (ventilador apagado)
#pragma once
#include <stdint.h>

namespace v2 {

enum class Orden : uint8_t {
  NADA, AYUDA, ESTADO, TELEMETRIA, CRUDOS, PARAMETROS, FIJAR, GUARDAR, DEFECTO, MAPA, PRUEBA, ESC, CERO,
  DESCONOCIDA, FALTA_VALOR
};

struct Comando {
  Orden orden = Orden::NADA;
  char nombre[24] = {0};
  float a = 0.0f, b = 0.0f;
};

class LineaConsola {
 public:
  // Agrega un carácter; devuelve true cuando hay una línea completa (CR o LF) en linea().
  bool alimentar(char c);
  const char* linea() const { return buf_; }

 private:
  char buf_[64] = {0};
  int n_ = 0;
  bool lista_ = false;
};

Comando interpretar(const char* linea);
bool leer_float(const char*& s, float* v);   // número decimal con signo y exponente opcional; avanza s

}  // namespace v2
