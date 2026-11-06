// Robot casero · pruebas de la lógica en la PC (sin Arduino).  Ejecutar: ./ejecutar.sh
// Cubre lo nuevo del firmware V3 (filtro, DRV8833, límites del motor, estados, indicadores, ajustes) y una
// simulación en lazo cerrado de toda la cadena: sensores → filtro → posición → PID → motores → cinemática.
// La lógica de V1 (posicion/pid/control) ya tiene sus pruebas en pruebas/test_logica.cpp (rama main).
#include <math.h>
#include <stdio.h>
#include <string.h>

#include <random>

#include "../casero/ajustes.h"
#include "../casero/control.h"
#include "../casero/estados.h"
#include "../casero/filtro.h"
#include "../casero/indicadores.h"
#include "../casero/motor.h"
#include "../casero/posicion.h"

static int fallas = 0, total = 0;
#define CHECK(c, ...)                                     \
  do {                                                    \
    ++total;                                              \
    if (!(c)) {                                           \
      ++fallas;                                           \
      printf("FALLA %s:%d  %s  ", __FILE__, __LINE__, #c); \
      printf(__VA_ARGS__);                                \
      printf("\n");                                       \
    }                                                     \
  } while (0)
#define CERCA(a, b, tol) CHECK(fabs((a) - (b)) <= (tol), "%g vs %g", (double)(a), (double)(b))

using namespace casero;

// ------------------------------------------------------------------------------------------------ filtro
static void prueba_filtro() {
  CERCA(filtro::mediana3(1, 9, 5), 5, 0);
  CERCA(filtro::mediana3(9, 1, 5), 5, 0);
  CERCA(filtro::mediana3(5, 5, 1), 5, 0);
  filtro::Canal c;
  for (int i = 0; i < 5; ++i) c.paso(1000, 1.0f);
  CERCA(c.paso(4000, 1.0f), 1000, 0);           // un pico aislado no pasa
  CERCA(c.paso(1000, 1.0f), 1000, 0);
  c.paso(3000, 1.0f);
  CERCA(c.paso(3000, 1.0f), 3000, 0);           // un escalón real pasa con 1 muestra de retraso
  filtro::Canal p;
  p.paso(0, 0.5f);
  float y = 0;
  for (int i = 0; i < 30; ++i) y = p.paso(100, 0.5f);
  CERCA(y, 100, 0.01);                          // el pasa-bajas converge
  filtro::Canal q;
  CERCA(q.paso(777, 0.2f), 777, 0);             // la primera muestra pasa directa (sin transitorio desde 0)
}

// ------------------------------------------------------------------------------------------------ DRV8833
static void prueba_drv8833() {
  using motor::Decaimiento;
  motor::Puente p = motor::drv8833(1.0f, Decaimiento::LENTO);
  CHECK(p.in1 == 1.0f && p.in2 == 0.0f, "adelante 100%%");
  p = motor::drv8833(0.3f, Decaimiento::LENTO);
  CHECK(p.in1 == 1.0f && fabsf(p.in2 - 0.7f) < 1e-6f, "adelante lento: IN2 en alto 70%% (freno)");
  p = motor::drv8833(0.0f, Decaimiento::LENTO);
  CHECK(p.in1 == 1.0f && p.in2 == 1.0f, "cero en lento = freno");
  p = motor::drv8833(-0.3f, Decaimiento::LENTO);
  CHECK(fabsf(p.in1 - 0.7f) < 1e-6f && p.in2 == 1.0f, "atrás lento");
  p = motor::drv8833(-2.0f, Decaimiento::LENTO);
  CHECK(p.in1 == 0.0f && p.in2 == 1.0f, "atrás 100%% (recortado)");
  p = motor::drv8833(0.4f, Decaimiento::RAPIDO);
  CHECK(fabsf(p.in1 - 0.4f) < 1e-6f && p.in2 == 0.0f, "adelante rápido");
  p = motor::drv8833(-0.4f, Decaimiento::RAPIDO);
  CHECK(p.in1 == 0.0f && fabsf(p.in2 - 0.4f) < 1e-6f, "atrás rápido");
  // ciclo efectivo = fracción del tiempo en (1,0): en lento es 1 − in2
  for (float d = 0.0f; d <= 1.0f; d += 0.1f) {
    p = motor::drv8833(d, Decaimiento::LENTO);
    CERCA(p.in1 * (1.0f - p.in2), d, 1e-5);
  }
}

// ------------------------------------------------------------------------------------------------ límites del motor
static void prueba_accionamiento() {
  motor::Accionamiento a;
  motor::Limites l;              // pwm_max 0.9, v_motor_max 6, i_max 1.2, i_total 2, rampa 6
  motor::Modelo m;
  a.configurar(m, l);
  CERCA(a.tope(6.0f), 0.90, 1e-6);            // con el MP1584 a 6 V manda el pwm_max
  CERCA(a.tope(8.4f), 6.0 / 8.4, 1e-6);       // VM directo de la LiPo llena: tope por voltaje del N20
  // rampa: en 10 ms el ciclo sube como máximo 0.06
  a.reiniciar();
  a.actualizar(1.0f, 1.0f, 6.0f, 0.010f);
  CERCA(a.ciclo(0), 0.06, 1e-5);
  // llega al tope y no lo pasa
  for (int i = 0; i < 300; ++i) a.actualizar(1.0f, 1.0f, 6.0f, 0.0025f);
  CERCA(a.ciclo(0), 0.90, 1e-4);
  // reversa brusca a toda velocidad: la corriente estimada nunca pasa de i_max
  float imax = 0.0f;
  for (int i = 0; i < 400; ++i) {
    a.actualizar(-1.0f, 1.0f, 6.0f, 0.0025f);
    imax = fmaxf(imax, fabsf(a.corriente(0)));
  }
  CHECK(imax <= l.i_max + 1e-3f, "reversa: corriente estimada %.3f A > %.2f A", imax, l.i_max);
  CERCA(a.ciclo(0), -0.90, 1e-3);
  // motor de baja resistencia (bloqueo 3 A): arranque desde parado limitado por corriente y por la suma
  motor::Modelo duro = motor::Modelo::desde_ficha(6.0f, 1000.0f, 3.0f, 0.1f, 0.08f);
  motor::Limites rapida = l;
  rapida.rampa = 100.0f;
  a.configurar(duro, rapida);
  a.reiniciar();
  float suma = 0.0f, i1 = 0.0f;
  for (int i = 0; i < 200; ++i) {
    a.actualizar(1.0f, 1.0f, 6.0f, 0.0025f);
    i1 = fmaxf(i1, fabsf(a.corriente(0)));
    suma = fmaxf(suma, fabsf(a.corriente(0)) + fabsf(a.corriente(1)));
  }
  CHECK(i1 <= l.i_max + 1e-3f, "arranque: %.3f A por motor", i1);
  CHECK(suma <= l.i_total + 1e-3f, "arranque: %.3f A en total", suma);
  // sin voltaje (solo USB) no hay ciclo
  a.actualizar(1.0f, 1.0f, 0.0f, 0.0025f);
  CHECK(a.ciclo(0) == 0.0f && a.ciclo(1) == 0.0f, "sin VM");
  // ficha → modelo
  motor::Modelo f = motor::Modelo::desde_ficha(6.0f, 1000.0f, 1.0f, 0.07f, 0.08f);
  CERCA(f.R, 6.0, 1e-5);
  CERCA(f.ke, (6.0 - 0.07 * 6.0) / (1000.0 * 2 * M_PI / 60.0), 1e-5);
}

// ------------------------------------------------------------------------------------------------ estados
static void prueba_estados() {
  Maquina m;
  Entradas in;
  uint32_t t = 1000;
  m.reiniciar(t);
  CHECK(m.estado() == Estado::INICIO, "arranca en INICIO");
  m.paso(in, t + 500);
  CHECK(m.estado() == Estado::INICIO, "INICIO dura 0.8 s");
  m.paso(in, t + 800);
  CHECK(m.estado() == Estado::ESPERA && m.entro(), "→ ESPERA");
  CHECK(!m.despierto(t + 800), "puente dormido en ESPERA");
  t += 1000;
  in.start = true;
  m.paso(in, t);
  CHECK(m.estado() == Estado::ESPERA && m.rechazo(), "START sin calibración: no arranca y avisa");
  in.start = false;
  in.cal = true;
  m.paso(in, t += 10);
  CHECK(m.estado() == Estado::CALIBRACION, "CAL → CALIBRACION");
  in.cal = false;
  // sin contraste: a los 15 s termina MAL y regresa a ESPERA
  const uint32_t t_cal = t;
  m.paso(in, t_cal + 14999);
  CHECK(m.estado() == Estado::CALIBRACION, "sigue antes de 15 s");
  m.paso(in, t_cal + 15000);
  CHECK(m.estado() == Estado::ESPERA && m.fin_cal() == FinCal::MAL, "15 s sin contraste → ESPERA (mal)");
  // con contraste: termina sola 1 s después
  in.cal = true;
  m.paso(in, t = t_cal + 16000);
  in.cal = false;
  in.cal_lista = true;
  m.paso(in, t + 2000);
  CHECK(m.estado() == Estado::CALIBRACION, "empieza a contar el segundo extra");
  in.cal_lista = false;
  m.paso(in, t + 2500);                          // se perdió el contraste: se reinicia la cuenta
  in.cal_lista = true;
  m.paso(in, t + 2600);
  m.paso(in, t + 3500);
  CHECK(m.estado() == Estado::CALIBRACION, "la cuenta se reinició");
  m.paso(in, t + 3600);
  CHECK(m.estado() == Estado::LISTO && m.fin_cal() == FinCal::BIEN, "fin automático → LISTO");
  CHECK(m.despierto(t + 3600), "LISTO despierta el puente");
  in.cal_lista = false;
  in.cal_valida = true;
  // START sin batería: no arranca
  t += 4000;
  in.hay_bateria = false;
  in.start = true;
  m.paso(in, t);
  CHECK(m.estado() == Estado::LISTO && m.rechazo(), "sin batería no arranca");
  in.hay_bateria = true;
  m.paso(in, t += 10);
  CHECK(m.estado() == Estado::SIGUIENDO && m.motores(), "START → SIGUIENDO");
  in.start = false;
  in.linea_visible = true;
  m.paso(in, t += 10);
  CHECK(m.estado() == Estado::SIGUIENDO, "sigue");
  in.linea_visible = false;
  in.buscando = true;
  m.paso(in, t += 10);
  CHECK(m.estado() == Estado::RECUPERACION && m.motores(), "sin línea → RECUPERACION");
  in.linea_visible = true;
  in.buscando = false;
  m.paso(in, t += 10);
  CHECK(m.estado() == Estado::SIGUIENDO, "recupera la línea");
  in.linea_visible = false;
  in.buscando = true;
  m.paso(in, t += 10);
  in.linea_perdida = true;
  m.paso(in, t += 10);
  CHECK(m.estado() == Estado::PARADA && !m.motores(), "línea perdida → PARADA");
  CHECK(m.frenando(t + 100) && m.despierto(t + 100), "frena al principio");
  CHECK(!m.frenando(t + 300) && !m.despierto(t + 300), "luego suelta y duerme");
  in.linea_perdida = in.buscando = false;
  in.start = true;
  m.paso(in, t += 500);
  CHECK(m.estado() == Estado::LISTO, "PARADA + START → LISTO (otro START para correr)");
  m.paso(in, t += 10);
  CHECK(m.estado() == Estado::SIGUIENDO, "corre otra vez");
  in.start = false;
  in.bat_critica = true;
  m.paso(in, t += 10);
  CHECK(m.estado() == Estado::ERROR && m.error() == Error::BATERIA, "batería crítica en marcha → ERROR 1");
  in.bat_critica = false;
  in.start = true;
  m.paso(in, t += 10);
  CHECK(m.estado() == Estado::ESPERA && m.error() == Error::NINGUNO, "START borra el error");
  // calibración guardada: START en ESPERA → LISTO; falla del driver
  m.paso(in, t += 10);
  CHECK(m.estado() == Estado::LISTO, "con calibración guardada");
  m.paso(in, t += 10);
  in.start = false;
  in.falla_driver = true;
  m.paso(in, t += 10);
  CHECK(m.estado() == Estado::ERROR && m.error() == Error::DRIVER, "nFAULT → ERROR 2");
  // CAL o START terminan la calibración antes de tiempo
  Maquina k;
  Entradas e2;
  k.reiniciar(0);
  k.paso(e2, 900);
  e2.cal = true;
  k.paso(e2, 1000);
  e2.cal = false;
  e2.cal_lista = true;
  k.paso(e2, 1100);
  e2.start = true;
  k.paso(e2, 1200);
  CHECK(k.estado() == Estado::LISTO && k.fin_cal() == FinCal::BIEN, "START termina la calibración");
}

// ------------------------------------------------------------------------------------------------ indicadores
static Contexto ctx(Estado e, uint32_t te, uint32_t t) {
  return Contexto{e, Error::NINGUNO, te, t, false, FinCal::NINGUNO, 100000, false, 100000, false, 15000};
}

static void prueba_indicadores() {
  Contexto c = ctx(Estado::SIGUIENDO, 5000, 20000);
  c.linea_visible = true;
  CHECK(indicar(c).led && indicar(c).tono_hz == 0, "siguiendo: LED = línea, silencio");
  c.linea_visible = false;
  CHECK(!indicar(c).led, "siguiendo sin línea: LED apagado");
  // ERROR 2: dos destellos por ciclo de 2 s
  Contexto e = ctx(Estado::ERROR, 5000, 0);
  e.error = Error::DRIVER;
  int flancos = 0;
  bool prev = false;
  for (uint32_t t = 0; t < 2000; ++t) {
    e.t_ms = t;
    const bool l = indicar(e).led;
    if (l && !prev) ++flancos;
    prev = l;
  }
  CHECK(flancos == 2, "error 2 = %d destellos", flancos);
  // melodía de calibración buena: sube
  Contexto f = ctx(Estado::LISTO, 1000, 50000);
  f.fin_cal = FinCal::BIEN;
  f.t_desde_fin_cal = 10;
  const uint16_t n1 = indicar(f).tono_hz;
  f.t_desde_fin_cal = 310;
  const uint16_t n3 = indicar(f).tono_hz;
  CHECK(n1 > 0 && n3 > n1, "melodía ascendente %u → %u", n1, n3);
  f.fin_cal = FinCal::MAL;
  f.t_desde_fin_cal = 10;
  const uint16_t m1 = indicar(f).tono_hz;
  f.t_desde_fin_cal = 310;
  CHECK(indicar(f).tono_hz < m1, "melodía descendente");
  // calibración: tic cada segundo
  Contexto k = ctx(Estado::CALIBRACION, 2010, 0);
  CHECK(indicar(k).tono_hz > 0, "tic al cumplir 2 s");
  k.t_estado_ms = 2500;
  CHECK(indicar(k).tono_hz == 0, "silencio entre tics");
  // rechazo: pitido grave
  Contexto r = ctx(Estado::ESPERA, 3000, 3000);
  r.rechazo = true;
  r.t_desde_rechazo = 50;
  CHECK(indicar(r).tono_hz > 0, "rechazo suena");
}

// ------------------------------------------------------------------------------------------------ ajustes
static void prueba_ajustes() {
  Ajustes a;
  CHECK(fijar(a, "kp", 0.05f) && a.kp == 0.05f, "fijar kp");
  CHECK(!fijar(a, "kp", 5.0f) && a.kp == 0.05f, "fuera de rango");
  CHECK(!fijar(a, "nada", 1.0f), "clave desconocida");
  CHECK(!fijar(a, "vbase", NAN), "NaN");
  CHECK(!fijar(a, "t_cal_max", 20.0f), "la calibración no puede pasar de 15 s");
  int n;
  const EntradaAjuste* t = tabla_ajustes(&n);
  Ajustes d;
  for (int i = 0; i < n; ++i) {
    const float v = *campo(d, t[i]);
    CHECK(v >= t[i].min && v <= t[i].max, "%s por defecto (%g) fuera de su rango", t[i].nombre, v);
    for (int j = i + 1; j < n; ++j) CHECK(strcmp(t[i].nombre, t[j].nombre) != 0, "nombre repetido %s", t[i].nombre);
  }
  CHECK(n * sizeof(float) == sizeof(Ajustes), "la tabla cubre todos los campos (%d de %zu)", n, sizeof(Ajustes) / sizeof(float));
  Guardado g{};
  g.a = a;
  g.n_cal = 8;
  sellar(g);
  CHECK(valido(g), "imagen sellada válida");
  g.a.kd += 0.001f;
  CHECK(!valido(g), "un cambio rompe el CRC");
  const uint8_t prueba[] = {'1', '2', '3', '4', '5', '6', '7', '8', '9'};
  CHECK(crc32(prueba, 9) == 0xCBF43926u, "CRC32 estándar");
  CHECK(a_tiempos(Ajustes()).cal_max_ms == 15000, "15 s");
}

// ------------------------------------------------------------------------------------------------ lazo cerrado
// Pista: círculo de radio Rc (línea de 25 mm). Robot: 2 ruedas de 28 mm a 80 mm [E], barra de 8 sensores a 9.525 mm,
// 100 mm delante del eje. Sensores con ruido gaussiano y picos; motor real con τ distinto al del modelo del firmware.
struct Sim {
  double x, y, th, wl = 0, wr = 0;
};

static double simular(double Rc, double v_fuente, double segundos, bool* perdio, double* v_media,
                      const Ajustes& aj = Ajustes()) {
  const double r = 0.014, W = 0.080, tau_real = 0.05;
  const int N = 8;
  posicion::Geometria g = posicion::geometria_recta(N, 9.525f, 100.0f);
  posicion::Calibracion cal;
  cal.reiniciar(N);
  for (int i = 0; i < N; ++i) { cal.minimo[i] = 200; cal.maximo[i] = 3700; }
  filtro::Arreglo fil;
  ControladorLinea ctl(a_control(aj));
  ctl.reiniciar();
  motor::Accionamiento acc;
  acc.configurar(a_modelo(aj), a_limites(aj));
  acc.reiniciar();
  std::mt19937 rng(7);
  std::normal_distribution<double> ruido(0.0, 40.0);
  std::uniform_real_distribution<double> u01(0.0, 1.0);
  const posicion::ModoSensor modo = {true, true, 4095};
  Sim s{Rc / 1000.0, 0.0, M_PI / 2};       // en la línea, avanzando en sentido antihorario
  const double dt = 0.0025;
  double peor = 0, dist = 0;
  *perdio = false;
  for (int k = 0; k < (int)(segundos / dt); ++k) {
    // sensores
    float refl[16];
    const double hx = cos(s.th), hy = sin(s.th), rx = sin(s.th), ry = -cos(s.th);
    for (int i = 0; i < N; ++i) {
      const double px = s.x + (g.y[i] * hx + g.x[i] * rx) / 1000.0, py = s.y + (g.y[i] * hy + g.x[i] * ry) / 1000.0;
      const double d = fabs(sqrt(px * px + py * py) * 1000.0 - Rc);
      double osc = (15.0 - d) / 5.0;
      osc = osc < 0 ? 0 : (osc > 1 ? 1 : osc);
      double on = 300 + osc * 3500 + ruido(rng);
      if (u01(rng) < 0.01) on += 2000;                                 // pico aislado
      const double off = 4000 + ruido(rng);
      refl[i] = posicion::reflectancia(modo, (int)on, (int)off);
    }
    fil.aplicar(refl, N, aj.alfa);
    float osc[16];
    posicion::normalizar(cal, refl, osc);
    const posicion::Estimacion e = posicion::estimar_posicion(g, osc, 0.10f, 0.30f);
    const SalidaControl sc = ctl.actualizar(e, (float)dt);
    if (sc.linea_perdida) { *perdio = true; break; }
    acc.actualizar(sc.izq, sc.der, (float)v_fuente, (float)dt);
    // motor "real" y cinemática
    const double ke = aj.m_ke;
    s.wl += dt / (tau_real + dt) * (acc.ciclo(0) * v_fuente / ke - s.wl);
    s.wr += dt / (tau_real + dt) * (acc.ciclo(1) * v_fuente / ke - s.wr);
    const double v = r * (s.wl + s.wr) / 2, w = r * (s.wr - s.wl) / W;
    s.x += v * cos(s.th) * dt;
    s.y += v * sin(s.th) * dt;
    s.th += w * dt;
    dist += v * dt;
    if (k * dt > 1.0) {                                                // después del transitorio
      // desvío de la BARRA de sensores (el eje corta la curva por geometría: en R = 200 mm queda 27 mm adentro)
      const double bx = s.x + 0.100 * cos(s.th), by = s.y + 0.100 * sin(s.th);
      peor = fmax(peor, fabs(sqrt(bx * bx + by * by) * 1000.0 - Rc));
    }
  }
  *v_media = dist / segundos;
  return peor;
}

static void prueba_lazo() {
  for (double Rc : {600.0, 300.0, 200.0}) {
    for (double vf : {6.0, 8.4}) {
      bool perdio;
      double vm;
      const double peor = simular(Rc, vf, 6.0, &perdio, &vm);
      printf("  lazo: R=%3.0f mm VM=%.1f V → desvío máx. de la barra %.1f mm, %.2f m/s%s\n", Rc, vf, peor, vm,
             perdio ? " (PERDIÓ LA LÍNEA)" : "");
      CHECK(!perdio, "perdió la línea en R=%g", Rc);
      CHECK(peor < 25.0, "desvío %.1f mm en R=%g", peor, Rc);
      CHECK(vm > 0.3, "velocidad media %.2f m/s", vm);
    }
  }
}

#ifdef BARRIDO
int main() {
  for (float vb : {0.35f, 0.5f, 0.7f})
  for (float kp : {0.008f, 0.010f, 0.012f})
    for (float kd : {0.0002f, 0.0004f, 0.0008f}) {
      Ajustes a;
      a.kp = kp; a.kd = kd; a.vbase = vb;
      printf("vbase=%.2f ", vb);
      double peor = 0, vmin = 9;
      bool p_any = false;
      for (double Rc : {600.0, 300.0, 200.0}) for (double vf : {6.0, 8.4}) {
        bool p; double vm;
        peor = fmax(peor, simular(Rc, vf, 6.0, &p, &vm, a));
        vmin = fmin(vmin, vm); p_any |= p;
      }
      printf("kp=%.4f kd=%.4f peor=%.1f vmin=%.2f %s\n", kp, kd, peor, vmin, p_any ? "PERDIO" : "");
    }
}
#else
int main() {
  prueba_filtro();
  prueba_drv8833();
  prueba_accionamiento();
  prueba_estados();
  prueba_indicadores();
  prueba_ajustes();
  prueba_lazo();
  printf("%d/%d comprobaciones OK\n", total - fallas, total);
  return fallas ? 1 : 0;
}
#endif
