// Pruebas de la lógica pura (posición, PID, control). Se compilan con g++, sin Arduino.
// Uso: pruebas/ejecutar.sh
#include <cstdio>
#include <cmath>
#include "../firmware/seguidor/parametros.h"
#include "../firmware/seguidor/posicion.h"
#include "../firmware/seguidor/pid.h"
#include "../firmware/seguidor/control.h"

static int fallos = 0, total = 0;
#define CHECK(cond, msg) do { ++total; if (!(cond)) { ++fallos; std::printf("FALLO: %s  (%s:%d)\n", msg, __FILE__, __LINE__); } } while (0)
static bool cerca(float a, float b, float tol) { return std::fabs(a - b) <= tol; }

// Oscuridad de una línea de ancho w centrada en xl, vista por cada sensor (cobertura 0..1 de un
// sensor puntual con apertura ap).
static void oscuridad_linea(const posicion::Geometria& g, float xl, float w, float ap, float* d) {
  for (int i = 0; i < g.n; ++i) {
    float a0 = g.x[i] - ap / 2, a1 = g.x[i] + ap / 2;
    float l0 = xl - w / 2, l1 = xl + w / 2;
    float ov = std::fmax(0.f, std::fmin(a1, l1) - std::fmax(a0, l0));
    d[i] = ov / ap;
  }
}

int main() {
  using namespace posicion;

  // --- Geometría ---
  Geometria g8 = geometria_recta(8, 9.525f, 100.f);
  CHECK(g8.n == 8, "8 sensores");
  CHECK(cerca(g8.x[0], -33.3375f, 1e-3f) && cerca(g8.x[7], 33.3375f, 1e-3f), "extremos simétricos 8 sensores");
  Geometria g24 = geometria_arco(24, 8.f, 150.f, 100.f);
  CHECK(cerca(g24.x[0], -g24.x[23], 1e-3f), "arco simétrico en x");
  CHECK(cerca(g24.y[0], g24.y[23], 1e-3f), "arco simétrico en y");
  CHECK(g24.y[0] < g24.y[11], "extremos del arco más atrás que el centro");

  // --- Posición: línea centrada y desplazada ---
  float d[par::MAX_SENSORES];
  oscuridad_linea(g8, 0.f, 25.f, 8.f, d);
  Estimacion e = estimar_posicion(g8, d, par::UMBRAL_RUIDO, par::CONFIANZA_MIN);
  CHECK(e.linea_visible && cerca(e.pos_mm, 0.f, 0.01f), "línea centrada -> 0");

  for (float xl = -20.f; xl <= 20.f; xl += 5.f) {
    oscuridad_linea(g8, xl, 25.f, 8.f, d);
    e = estimar_posicion(g8, d, par::UMBRAL_RUIDO, par::CONFIANZA_MIN);
    CHECK(e.linea_visible, "línea visible");
    CHECK((xl == 0.f) || (e.pos_mm * xl > 0.f), "signo correcto (+ derecha)");
    CHECK(cerca(e.pos_mm, xl, 5.5f), "posición cercana a la real (error < 5.5 mm)");
  }

  // Simetría
  oscuridad_linea(g8, 12.f, 25.f, 8.f, d);
  float p1 = estimar_posicion(g8, d, 0.1f, 0.3f).pos_mm;
  oscuridad_linea(g8, -12.f, 25.f, 8.f, d);
  float p2 = estimar_posicion(g8, d, 0.1f, 0.3f).pos_mm;
  CHECK(cerca(p1, -p2, 1e-3f), "simetría izquierda/derecha");

  // Sin línea
  for (int i = 0; i < 8; ++i) d[i] = 0.f;
  CHECK(!estimar_posicion(g8, d, 0.1f, 0.3f).linea_visible, "sin línea -> no visible");

  // Ruido bajo el umbral se ignora
  for (int i = 0; i < 8; ++i) d[i] = 0.08f;
  CHECK(!estimar_posicion(g8, d, 0.1f, 0.3f).linea_visible, "ruido bajo umbral no cuenta");

  // --- Reflectancia ---
  ModoSensor m1{false, false, 4095};
  CHECK(cerca(reflectancia(m1, 1000, 0), 1000.f, 1e-3f), "sin resta, directo");
  ModoSensor m2{false, true, 4095};
  CHECK(cerca(reflectancia(m2, 1000, 0), 3095.f, 1e-3f), "luz baja voltaje, invertido");
  ModoSensor m3{true, true, 4095};
  CHECK(cerca(reflectancia(m3, 1000, 3000), 2000.f, 1e-3f), "resta ambiente, fototransistor");
  CHECK(reflectancia(m3, 3500, 3000) == 0.f, "no negativa");

  // --- Calibración ---
  Calibracion cal; cal.reiniciar(2);
  CHECK(!cal.lista(100.f), "no lista sin muestras");
  float r[2] = {500.f, 2000.f}; cal.muestrear(r);
  float r2[2] = {2500.f, 400.f}; cal.muestrear(r2);
  CHECK(cal.lista(100.f), "lista tras ver ambos extremos");
  float o[2]; float rb[2] = {2500.f, 2000.f}; normalizar(cal, rb, o);
  CHECK(cerca(o[0], 0.f, 1e-3f) && cerca(o[1], 0.f, 1e-3f), "blanco -> oscuridad 0");
  float rn[2] = {500.f, 400.f}; normalizar(cal, rn, o);
  CHECK(cerca(o[0], 1.f, 1e-3f) && cerca(o[1], 1.f, 1e-3f), "negro -> oscuridad 1");
  float rf[2] = {9000.f, -10.f}; normalizar(cal, rf, o);
  CHECK(o[0] >= 0.f && o[0] <= 1.f && o[1] >= 0.f && o[1] <= 1.f, "recorta fuera de rango");

  // --- PID ---
  PID pid(2.f, 0.f, 0.f); pid.limites(-1.f, 1.f);
  CHECK(cerca(pid.calcular(0.25f, 0.002f), 0.5f, 1e-5f), "P puro");
  CHECK(cerca(pid.calcular(10.f, 0.002f), 1.f, 1e-5f), "saturación");
  CHECK(cerca(pid.calcular(-10.f, 0.002f), -1.f, 1e-5f), "saturación negativa");

  PID pd(0.f, 0.f, 1.f); pd.limites(-100.f, 100.f); pd.filtro_derivada(0.f);
  pd.calcular(0.f, 0.01f);
  CHECK(cerca(pd.calcular(0.1f, 0.01f), 10.f, 1e-3f), "D: sin golpe inicial y pendiente correcta");

  PID pi(0.f, 1.f, 0.f); pi.limites(-0.5f, 0.5f);
  for (int i = 0; i < 2000; ++i) pi.calcular(1.f, 0.01f);   // 20 s con error constante
  CHECK(cerca(pi.calcular(1.f, 0.01f), 0.5f, 1e-4f), "I satura en el límite");
  float u_despues = 0.f;
  for (int i = 0; i < 100; ++i) u_despues = pi.calcular(-1.f, 0.01f);  // error cambia de signo
  CHECK(u_despues < 0.5f, "anti-windup: sale rápido de saturación");
  CHECK(cerca(pid.calcular(1.f, 0.f), pid.calcular(1.f, 0.f), 1e-9f), "dt=0 no rompe");

  // --- Control ---
  ParamControl pc = param_por_defecto();
  ControladorLinea ctl(pc);
  Estimacion linea_der{15.f, 2.f, true};
  SalidaControl s = ctl.actualizar(linea_der, 0.002f);
  CHECK(s.izq > s.der, "línea a la derecha -> rueda izquierda más rápida");
  ctl.reiniciar();
  Estimacion linea_izq{-15.f, 2.f, true};
  s = ctl.actualizar(linea_izq, 0.002f);
  CHECK(s.der > s.izq, "línea a la izquierda -> rueda derecha más rápida");
  ctl.reiniciar();
  Estimacion centro{0.f, 2.f, true};
  s = ctl.actualizar(centro, 0.002f);
  CHECK(cerca(s.izq, s.der, 1e-6f) && cerca(s.izq, pc.vbase, 1e-6f), "centrado -> recto a vbase");

  // Pérdida de línea: retiene, busca, se detiene
  ctl.reiniciar();
  ctl.actualizar(linea_der, 0.002f);
  Estimacion nada{0.f, 0.f, false};
  s = ctl.actualizar(nada, 0.002f);
  CHECK(!s.buscando, "hueco corto: no busca todavía");
  for (int i = 0; i < 40; ++i) s = ctl.actualizar(nada, 0.002f);  // ~80 ms
  CHECK(s.buscando && !s.linea_perdida, "tras retención: busca");
  CHECK(s.izq > s.der, "busca hacia el último lado visto (derecha)");
  for (int i = 0; i < 1000; ++i) s = ctl.actualizar(nada, 0.002f);  // +2 s
  CHECK(s.linea_perdida && s.izq == 0.f && s.der == 0.f, "línea perdida -> paro");

  // Límites siempre respetados
  ctl.reiniciar();
  bool ok = true;
  for (float x = -60.f; x <= 60.f; x += 0.5f) {
    Estimacion ee{x, 3.f, true};
    SalidaControl ss = ctl.actualizar(ee, 0.002f);
    if (ss.izq > 1.f + 1e-6f || ss.der > 1.f + 1e-6f || ss.izq < pc.rueda_min - 1e-6f || ss.der < pc.rueda_min - 1e-6f) ok = false;
  }
  CHECK(ok, "ruedas siempre dentro de [rueda_min, 1]");

  std::printf("%d pruebas, %d fallos\n", total, fallos);
  return fallos ? 1 : 0;
}
