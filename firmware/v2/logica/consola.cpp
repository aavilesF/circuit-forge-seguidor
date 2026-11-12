#include "consola.h"

#include <string.h>

namespace v2 {

bool LineaConsola::alimentar(char c) {
  if (lista_) { n_ = 0; lista_ = false; }
  if (c == '\r' || c == '\n') {
    if (n_ == 0) return false;                 // líneas vacías (CR LF) se ignoran
    buf_[n_] = 0;
    lista_ = true;
    return true;
  }
  if (c == 8 || c == 127) { if (n_ > 0) --n_; return false; }   // retroceso
  if (n_ < static_cast<int>(sizeof(buf_)) - 1 && c >= 32 && c < 127) buf_[n_++] = c;
  return false;
}

static void saltar(const char*& s) { while (*s == ' ' || *s == '\t') ++s; }

bool leer_float(const char*& s, float* v) {
  saltar(s);
  const char* p = s;
  float signo = 1.0f;
  if (*p == '+' || *p == '-') { if (*p == '-') signo = -1.0f; ++p; }
  float ent = 0.0f;
  bool hay = false;
  while (*p >= '0' && *p <= '9') { ent = ent * 10.0f + float(*p - '0'); ++p; hay = true; }
  if (*p == '.') {
    ++p;
    float esc = 0.1f;
    while (*p >= '0' && *p <= '9') { ent += float(*p - '0') * esc; esc *= 0.1f; ++p; hay = true; }
  }
  if (!hay) return false;
  if (*p == 'e' || *p == 'E') {
    ++p;
    int se = 1, ex = 0;
    if (*p == '+' || *p == '-') { if (*p == '-') se = -1; ++p; }
    if (!(*p >= '0' && *p <= '9')) return false;
    while (*p >= '0' && *p <= '9') { ex = ex * 10 + (*p - '0'); ++p; if (ex > 38) return false; }
    for (int k = 0; k < ex; ++k) ent = se > 0 ? ent * 10.0f : ent / 10.0f;
  }
  if (*p != 0 && *p != ' ' && *p != '\t') return false;
  *v = signo * ent;
  s = p;
  return true;
}

static bool palabra(const char*& s, char* out, int n) {
  saltar(s);
  int k = 0;
  while (*s && *s != ' ' && *s != '\t') {
    if (k < n - 1) out[k++] = *s;
    ++s;
  }
  out[k] = 0;
  return k > 0;
}

Comando interpretar(const char* linea) {
  Comando c;
  const char* s = linea;
  char w[24];
  if (!palabra(s, w, sizeof(w))) return c;
  if (!strcmp(w, "?") || !strcmp(w, "ayuda")) c.orden = Orden::AYUDA;
  else if (!strcmp(w, "e")) c.orden = Orden::ESTADO;
  else if (!strcmp(w, "t")) c.orden = Orden::TELEMETRIA;
  else if (!strcmp(w, "r")) c.orden = Orden::CRUDOS;
  else if (!strcmp(w, "p")) c.orden = Orden::PARAMETROS;
  else if (!strcmp(w, "w")) c.orden = Orden::GUARDAR;
  else if (!strcmp(w, "defecto")) c.orden = Orden::DEFECTO;
  else if (!strcmp(w, "m")) c.orden = Orden::MAPA;
  else if (!strcmp(w, "cero")) c.orden = Orden::CERO;
  else if (!strcmp(w, "set")) {
    c.orden = (palabra(s, c.nombre, sizeof(c.nombre)) && leer_float(s, &c.a)) ? Orden::FIJAR : Orden::FALTA_VALOR;
  } else if (!strcmp(w, "prueba")) {
    c.orden = (leer_float(s, &c.a) && leer_float(s, &c.b)) ? Orden::PRUEBA : Orden::FALTA_VALOR;
  } else if (!strcmp(w, "esc")) {
    c.orden = leer_float(s, &c.a) ? Orden::ESC : Orden::FALTA_VALOR;
  } else {
    c.orden = Orden::DESCONOCIDA;
  }
  return c;
}

}  // namespace v2
