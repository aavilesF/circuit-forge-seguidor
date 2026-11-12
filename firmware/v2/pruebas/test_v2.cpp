// V2 · Pruebas del firmware en la PC (g++ con ASan/UBSan): firmware/v2/pruebas/ejecutar.sh
//
//  1. perfil_factible() = perfil_vuelta() del simulador (sim/v2/fase1_v2.py), vectores dorados en P1-P4.
//  2. perfil_ciclico(): topes, aceleración y frenado respetados; continuidad al cerrar la vuelta.
//  3. Límite de corriente del motor y estimador térmico (FASE35 §3).
//  4. Supervisor de la succión: arranque, pérdida (50 ms), recuperación, sin barómetros.
//  5. Máquina de estados: secuencias y bloqueos (R08: nada se mueve sin START; C03: calibración manual).
//  6. Consola y parámetros: interpretación, rangos, CRC de la imagen en flash.
//  7. Mapa: cierre de vuelta y localización con la curvatura de P1-P4 (con ruido); cambio de pista -> inválido.
//  8. Lazo cerrado: el núcleo completo (nucleo_v2) sigue P1-P4 con un modelo cinemático y de motor; 3 vueltas.
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <random>
#include <string>
#include <vector>

#include "../logica/consola.h"
#include "../logica/estados_v2.h"
#include "../logica/indicadores.h"
#include "../logica/mapa.h"
#include "../logica/motor_v2.h"
#include "../logica/nucleo_v2.h"
#include "../logica/parametros_v2.h"
#include "../logica/succion.h"

static int fallas = 0, pruebas = 0;
#define VERIFICAR(c, ...)                                                   \
  do {                                                                      \
    ++pruebas;                                                              \
    if (!(c)) {                                                             \
      ++fallas;                                                             \
      printf("  FALLA %s:%d: %s | ", __FILE__, __LINE__, #c);               \
      printf(__VA_ARGS__);                                                  \
      printf("\n");                                                         \
    }                                                                       \
  } while (0)

static std::string DATOS;

// ------------------------------------------------------------------------------------------------ 1. vectores dorados
static void prueba_perfil_oro() {
  printf("1. perfil_factible contra el simulador\n");
  FILE* f = fopen((DATOS + "/oro_perfil.txt").c_str(), "r");
  VERIFICAR(f != nullptr, "no se encontró oro_perfil.txt");
  if (!f) return;
  char pista[8];
  float ds, a_acc, a_fr, v_ini;
  int n;
  double t_oro, a_oro;
  int casos = 0;
  double peor = 0;
  while (fscanf(f, "%7s %f %f %f %f %d %lf %lf", pista, &ds, &a_acc, &a_fr, &v_ini, &n, &t_oro, &a_oro) == 8) {
    std::vector<float> cap(n), oro(n + 1), vel(n + 1);
    for (int i = 0; i < n; ++i) if (fscanf(f, "%f", &cap[i]) != 1) return;
    for (int i = 0; i <= n; ++i) if (fscanf(f, "%f", &oro[i]) != 1) return;
    const float a_req = v2::perfil_factible(cap.data(), n, a_acc, a_fr, ds, v_ini, vel.data());
    double dmax = 0, t = 0;
    for (int i = 0; i <= n; ++i) dmax = fmax(dmax, fabs(vel[i] - oro[i]));
    for (int i = 0; i < n; ++i) t += 2.0 * ds / fmax(vel[i] + vel[i + 1], 1e-9);
    peor = fmax(peor, dmax);
    VERIFICAR(dmax < 2e-4, "%s: diferencia de velocidad %.2e m/s", pista, dmax);
    VERIFICAR(fabs(t - t_oro) < 1e-3 * t_oro, "%s: tiempo %.4f s contra %.4f s", pista, t, t_oro);
    VERIFICAR(fabs(a_req - a_oro) < 1e-2 * (1 + a_oro), "%s: a_req %.4f contra %.4f", pista, a_req, a_oro);
    ++casos;
  }
  fclose(f);
  printf("   %d perfiles, diferencia máxima %.2e m/s\n", casos, peor);
  VERIFICAR(casos == 8, "casos leídos: %d", casos);
}

// ------------------------------------------------------------------------------------------------ 2. perfil cíclico
static void prueba_perfil_ciclico() {
  printf("2. perfil cíclico\n");
  const int n = 400;
  const float ds = 0.01f, a_acc = 8.0f, a_fr = 6.0f;
  std::vector<float> cap(n), v(n);
  for (int i = 0; i < n; ++i) cap[i] = (i > 150 && i < 200) || (i > 350 && i < 380) ? 0.9f : 2.0f;
  v2::perfil_ciclico(cap.data(), n, a_acc, a_fr, ds, v.data());
  bool ok_tope = true, ok_acc = true, ok_fr = true;
  for (int i = 0; i < n; ++i) {
    const float a = v[i], b = v[(i + 1) % n];
    if (a > cap[i] + 1e-5f) ok_tope = false;
    if ((b * b - a * a) / (2 * ds) > a_acc * 1.001f) ok_acc = false;
    if ((a * a - b * b) / (2 * ds) > a_fr * 1.001f) ok_fr = false;
  }
  VERIFICAR(ok_tope, "supera algún tope");
  VERIFICAR(ok_acc, "acelera más que a_acc (también al cerrar la vuelta)");
  VERIFICAR(ok_fr, "frena más que a_fr (también al cerrar la vuelta)");
  VERIFICAR(fabsf(v[160] - 0.9f) < 1e-4f, "dentro de la curva: %.3f", v[160]);
}

// ------------------------------------------------------------------------------------------------ 3. motor
static void prueba_motor() {
  printf("3. límite de corriente y estimador térmico\n");
  const v2::ModeloMotor m = v2::ModeloMotor::desde_ficha(cfg2::MOTOR_V_NOM, cfg2::MOTOR_RPM, cfg2::MOTOR_PAR_BLOQUEO,
                                                         cfg2::MOTOR_I_BLOQUEO, cfg2::MOTOR_I_VACIO);
  VERIFICAR(fabsf(m.R - 4.0f) < 1e-4f, "R %.3f", m.R);
  // kt = par de bloqueo / (I bloqueo − I vacío), como sf::Motor de V1 (0.0182); FASE35 usó par / I bloqueo (0.0164).
  // El límite de corriente solo usa R y ke.
  VERIFICAR(fabsf(m.kt - cfg2::MOTOR_PAR_BLOQUEO / (cfg2::MOTOR_I_BLOQUEO - cfg2::MOTOR_I_VACIO)) < 1e-6f, "kt %.5f", m.kt);
  VERIFICAR(fabsf(m.ke * 2100.0f * 6.2831853f / 60.0f - (6.0f - 0.15f * 4.0f)) < 1e-3f, "ke %.5f", m.ke);
  std::mt19937 g(1);
  std::uniform_real_distribution<float> U(-1, 1);
  bool ok = true, ok_v = true;
  for (int k = 0; k < 20000; ++k) {
    const float d = U(g), w = 250.0f * U(g), vb = 6.4f + 2.0f * (U(g) + 1) * 0.5f, imax = 1.5f;
    const float dl = v2::limitar_ciclo(m, d, w, vb, imax, 6.0f);
    const float i = m.corriente(dl, vb, w);
    // con |ke·ω| > 6 V el tope de tensión puede impedir llegar a la banda: entonces el ciclo queda en el tope
    if (fabsf(i) > imax + 1e-3f && fabsf(fabsf(dl) - 6.0f / vb) > 1e-5f) ok = false;
    if (fabsf(dl) * vb > 6.0f + 1e-4f) ok_v = false;
  }
  VERIFICAR(ok, "la corriente del modelo supera 1.5 A");
  VERIFICAR(ok_v, "la tensión efectiva supera 6 V");
  // frenado a 2 m/s (ω = 125 rad/s): el ciclo inverso queda limitado a −1.5 A
  const float w2 = 2.0f / 0.016f;
  const float d_fr = v2::limitar_ciclo(m, -1.0f, w2, 7.4f, 1.5f, 6.0f);
  VERIFICAR(fabsf(m.corriente(d_fr, 7.4f, w2) + 1.5f) < 1e-3f, "frenado: %.3f A", m.corriente(d_fr, 7.4f, w2));
  v2::EstimadorTermico T(cfg2::MOTOR_R, cfg2::MOTOR_RTH, cfg2::MOTOR_CTH);
  for (int k = 0; k < 2000000; ++k) T.paso(1.0f, 1e-3f);           // 2000 s a 1 A: régimen = I²R·Rth = 160 K
  VERIFICAR(fabsf(T.elevacion() - 160.0f) < 1.0f, "régimen %.1f K", T.elevacion());
  T.fijar(45.0f);
  VERIFICAR(fabsf(T.limite(1.5f, 0.5f, 40.0f, 50.0f) - 1.0f) < 1e-4f, "derrateo a 45 K");
  VERIFICAR(T.limite(1.5f, 0.5f, 40.0f, 50.0f) < 1.5f && !T.sobrecalentado(50.0f), "45 K");
  T.fijar(50.0f);
  VERIFICAR(T.sobrecalentado(50.0f) && T.limite(1.5f, 0.5f, 40.0f, 50.0f) == 0.0f, "50 K = error");
  v2::LazoCorriente L;
  float lim = 1.5f;
  for (int k = 0; k < 50; ++k) lim = L.actualizar(2.0f, 1.5f, 1e-3f);
  VERIFICAR(lim < 1.4f, "IPROPI por encima del límite: el límite efectivo baja (%.2f A)", lim);
}

// ------------------------------------------------------------------------------------------------ 4. succión
static void prueba_succion() {
  printf("4. supervisor de la succión\n");
  v2::SupervisorSuccion s;
  v2::ParamSuccion p;
  s.configurar(p);
  s.fijar_cero(0.0f);
  uint32_t t = 0;
  s.encender(t);
  float dp = 0;
  using E = v2::SupervisorSuccion::Estado;
  for (; t < 2000; ++t) {
    dp = 500.0f * (t < 600 ? t / 600.0f : 1.0f);
    if (t % 5 == 0) s.muestra(101325.0f, 101325.0f - dp, true, t);
    s.actualizar(t);
    if (s.estado() == E::OK) break;
  }
  VERIFICAR(s.estado() == E::OK && t >= 600 && t < 900, "OK a los %u ms", t);
  VERIFICAR(fabsf(s.mando() - p.mando_crucero) < 1e-4f, "mando de crucero");
  VERIFICAR(fabsf(s.fuerza() - 500.0f * 0.0049f * 0.96f) < 0.15f, "fuerza %.2f N", s.fuerza());
  const uint32_t t0 = t;
  for (; t < t0 + 500; ++t) {                     // faldón levantado: ΔP cae a 50 Pa
    if (t % 5 == 0) s.muestra(101325.0f, 101325.0f - 50.0f, true, t);
    s.actualizar(t);
    if (s.estado() == E::DEGRADADO) break;
  }
  VERIFICAR(s.estado() == E::DEGRADADO && t - t0 < 120, "degradado a los %u ms", t - t0);
  VERIFICAR(s.fuerza() == 0.0f && s.listo_para_correr(), "sin fuerza en degradado, sigue corriendo");
  const uint32_t t1 = t;
  for (; t < t1 + 1000; ++t) {
    if (t % 5 == 0) s.muestra(101325.0f, 101325.0f - 480.0f, true, t);
    s.actualizar(t);
    if (s.estado() == E::OK) break;
  }
  VERIFICAR(s.estado() == E::OK && t - t1 >= 300, "recupera a los %u ms", t - t1);
  for (uint32_t k = 0; k < 300; ++k, ++t) s.actualizar(t);       // barómetros mudos
  VERIFICAR(s.estado() == E::SIN_SENSOR && s.listo_para_correr(), "sin barómetros: corre sin succión");
  v2::SupervisorSuccion s2;
  s2.configurar(p);
  s2.encender(0);
  uint32_t k2 = 0;
  for (; k2 < 3000; ++k2) {                       // el ventilador no levanta presión
    if (k2 % 5 == 0) s2.muestra(101325.0f, 101320.0f, true, k2);
    s2.actualizar(k2);
    if (s2.estado() != E::ARRANQUE) break;
  }
  VERIFICAR(s2.estado() == E::DEGRADADO && k2 >= 1500 && k2 < 1510, "sin presión: degradado a los %u ms", k2);
}

// ------------------------------------------------------------------------------------------------ 5. estados
static void prueba_estados() {
  printf("5. máquina de estados\n");
  using v2::Estado;
  v2::MaquinaV2 m;
  v2::Eventos ev;
  uint32_t t = 0;
  ev.autoprueba_hecha = false;
  m.actualizar(ev, t);
  VERIFICAR(m.estado() == Estado::INICIO, "espera la autoprueba");
  ev.autoprueba_hecha = true;
  ev.autoprueba = v2::Error::BAROMETROS;
  m.actualizar(ev, ++t);
  VERIFICAR(m.estado() == Estado::ERROR && m.error() == v2::Error::BAROMETROS, "error de barómetros");
  ev = v2::Eventos{}; ev.autoprueba_hecha = true; ev.cal = true;
  m.actualizar(ev, ++t);
  VERIFICAR(m.estado() == Estado::INICIO, "CAL desde ERROR repite la autoprueba");
  ev.cal = false;
  m.actualizar(ev, ++t);
  VERIFICAR(m.estado() == Estado::ESPERA, "sin calibración: ESPERA");
  ev.start = true;
  m.actualizar(ev, ++t);
  VERIFICAR(m.estado() == Estado::ESPERA && !m.motores_habilitados(), "START sin calibración no arranca (R08)");
  ev.start = false; ev.cal = true;
  m.actualizar(ev, ++t);
  VERIFICAR(m.estado() == Estado::CALIBRACION && !m.motores_habilitados(), "CAL: calibración manual (C03)");
  ev.cal = false; ev.cal_tiempo_agotado = true; ev.cal_suficiente = false;
  m.actualizar(ev, ++t);
  VERIFICAR(m.estado() == Estado::ESPERA && m.motivo() == v2::Motivo::CAL_INSUFICIENTE, "contraste insuficiente");
  ev = v2::Eventos{}; ev.autoprueba_hecha = true; ev.cal = true;
  m.actualizar(ev, ++t);
  ev.cal = true; ev.cal_suficiente = true;
  m.actualizar(ev, ++t);
  VERIFICAR(m.estado() == Estado::LISTO, "calibración buena: LISTO");
  ev = v2::Eventos{}; ev.autoprueba_hecha = true; ev.start = true; ev.bateria_permite = false;
  m.actualizar(ev, ++t);
  VERIFICAR(m.estado() == Estado::LISTO && m.motivo() == v2::Motivo::BATERIA_ARRANQUE, "batería baja: no arranca");
  ev.bateria_permite = true;
  t = 1000;
  m.actualizar(ev, t);
  VERIFICAR(m.estado() == Estado::ARRANQUE && m.ventilador_encendido() && m.frenado_activo() &&
                !m.motores_habilitados(), "ARRANQUE: ventilador y freno, sin tracción");
  m.actualizar(ev, t + 100);                      // el dedo sigue en START: no detiene (bloqueo de 0.5 s)
  VERIFICAR(m.estado() == Estado::ARRANQUE, "START dentro del bloqueo no detiene");
  ev.start = false; ev.succion_lista = true;
  m.actualizar(ev, t + 200);
  VERIFICAR(m.estado() == Estado::SIGUIENDO && m.recien_arrancado() && m.motores_habilitados(), "SIGUIENDO");
  ev.buscando = true;
  m.actualizar(ev, t + 300);
  VERIFICAR(m.estado() == Estado::RECUPERACION, "RECUPERACION");
  ev.buscando = false;
  m.actualizar(ev, t + 310);
  VERIFICAR(m.estado() == Estado::SIGUIENDO, "vuelve a SIGUIENDO");
  ev.sobrecalentado = true;
  m.actualizar(ev, t + 320);
  VERIFICAR(m.estado() == Estado::ERROR && m.error() == v2::Error::TEMPERATURA && !m.motores_habilitados(),
            "motor caliente: ERROR 6");
  // nueva carrera: START detiene después del bloqueo
  v2::MaquinaV2 m2;
  v2::Eventos e2; e2.autoprueba_hecha = true; e2.cal_guardada_ok = true;
  m2.actualizar(e2, 0);
  VERIFICAR(m2.estado() == Estado::LISTO, "con calibración guardada: LISTO directo");
  e2.start = true; m2.actualizar(e2, 10);
  e2.start = false; e2.succion_lista = true; m2.actualizar(e2, 20);
  e2.start = true; m2.actualizar(e2, 900);
  VERIFICAR(m2.estado() == Estado::PARADA && m2.motivo() == v2::Motivo::BOTON, "START detiene");
  e2.start = false; e2.linea_perdida = false; e2.start = true; m2.actualizar(e2, 1000);
  VERIFICAR(m2.estado() == Estado::LISTO, "START desde PARADA: LISTO");
  // indicadores
  const v2::Indicadores er = v2::indicar(Estado::ERROR, v2::Error::BAROMETROS, 1000, 0, v2::AvisoSucc::APAGADO);
  int destellos = 0;
  bool prev = false;
  for (uint32_t k = 0; k < 400 * 4 + 1200; ++k) {
    const bool r = v2::indicar(Estado::ERROR, v2::Error::BAROMETROS, 1000, k, v2::AvisoSucc::APAGADO).rojo;
    if (r && !prev) ++destellos;
    prev = r;
  }
  VERIFICAR(destellos == 4 && er.tono_hz == 0, "error 4 = 4 destellos (%d)", destellos);
}

// ------------------------------------------------------------------------------------------------ 6. consola
static void prueba_consola() {
  printf("6. consola y parámetros\n");
  v2::LineaConsola L;
  const char* txt = "set kp 70.5\r\n";
  bool lista = false;
  for (const char* c = txt; *c; ++c) lista |= L.alimentar(*c);
  VERIFICAR(lista, "línea completa");
  v2::Comando c = v2::interpretar(L.linea());
  VERIFICAR(c.orden == v2::Orden::FIJAR && !strcmp(c.nombre, "kp") && fabsf(c.a - 70.5f) < 1e-5f, "set kp 70.5");
  c = v2::interpretar("prueba -0.2 0.25");
  VERIFICAR(c.orden == v2::Orden::PRUEBA && fabsf(c.a + 0.2f) < 1e-6f && fabsf(c.b - 0.25f) < 1e-6f, "prueba");
  VERIFICAR(v2::interpretar("set kp").orden == v2::Orden::FALTA_VALOR, "falta valor");
  VERIFICAR(v2::interpretar("set kp 1x").orden == v2::Orden::FALTA_VALOR, "número mal escrito");
  VERIFICAR(v2::interpretar("zzz").orden == v2::Orden::DESCONOCIDA, "desconocida");
  VERIFICAR(v2::interpretar("esc 2e-1").orden == v2::Orden::ESC && fabsf(v2::interpretar("esc 2e-1").a - 0.2f) < 1e-6f,
            "exponente");
  v2::Parametros p;
  VERIFICAR(v2::fijar(p, "kp", 70.0f) && p.kp == 70.0f, "fijar kp");
  VERIFICAR(!v2::fijar(p, "i_lim", 2.4f) && p.i_lim == 1.5f, "i_lim no puede pasar de 1.6 A (FASE35)");
  VERIFICAR(!v2::fijar(p, "no_existe", 1.0f), "parámetro inexistente");
  VERIFICAR(!v2::fijar(p, "kp", NAN), "NaN rechazado");
  int n;
  const v2::EntradaParam* t = v2::tabla_parametros(&n);
  bool rangos = true;
  v2::Parametros def;
  for (int i = 0; i < n; ++i) {
    const float v = *v2::campo(def, t[i]);
    if (!(v >= t[i].min && v <= t[i].max)) { rangos = false; printf("   %s = %g fuera de [%g, %g]\n", t[i].nombre, v, t[i].min, t[i].max); }
  }
  VERIFICAR(rangos, "los valores de fábrica están dentro de sus rangos");
  v2::Guardado g{};
  g.p = p;
  v2::sellar(g);
  VERIFICAR(v2::valido(g), "CRC válido");
  g.p.kp += 1.0f;
  VERIFICAR(!v2::valido(g), "CRC detecta el cambio");
}

// ------------------------------------------------------------------------------------------------ pistas
struct PistaPrueba {
  std::string nombre;
  std::vector<float> x, y, h, k;
  std::vector<char> hueco;
  float largo() const { return x.size() * 0.001f; }
};

static bool cargar_pista(const std::string& clave, PistaPrueba& p) {
  FILE* f = fopen((DATOS + "/pistas_" + clave + ".csv").c_str(), "r");
  if (!f) return false;
  p.nombre = clave;
  float a, b, c, d, e;
  while (fscanf(f, "%f,%f,%f,%f,%f", &a, &b, &c, &d, &e) == 5) {
    p.x.push_back(a); p.y.push_back(b); p.h.push_back(c); p.k.push_back(d); p.hueco.push_back(e > 0.5f);
  }
  fclose(f);
  return !p.x.empty();
}

// ------------------------------------------------------------------------------------------------ 7. mapa
static void prueba_mapa() {
  printf("7. mapa: cierre y localización\n");
  const char* claves[] = {"P1", "P2", "P3", "P4"};
  std::mt19937 g(7);
  std::normal_distribution<float> ruido(0.0f, 0.4f);              // 1/m de ruido en la curvatura de cada ciclo
  for (const char* cl : claves) {
    PistaPrueba P;
    if (!cargar_pista(cl, P)) { VERIFICAR(false, "falta la pista %s", cl); continue; }
    v2::Mapa m;
    m.reiniciar(v2::ParamMapa{});
    const int n = static_cast<int>(P.x.size());
    const float v = 1.2f, dt = 1e-3f;
    double s = 0;
    int vueltas_cerrado = -1;
    double s_cierre = 0;
    double peor_loc = 0;
    for (int paso = 0; s < 3.2 * P.largo(); ++paso) {
      const double s1 = s + v * dt;
      const int i0 = static_cast<int>(s * 1000) % n, i1 = static_cast<int>(s1 * 1000) % n;
      float dpsi = P.h[i1] - P.h[i0];
      while (dpsi > 3.14159f) dpsi -= 6.2831853f;
      while (dpsi < -3.14159f) dpsi += 6.2831853f;
      m.avanzar(v * dt, dpsi + ruido(g) * v * dt);
      s = s1;
      if (m.modo() == v2::Mapa::Modo::CERRADO) {
        if (vueltas_cerrado < 0) { vueltas_cerrado = 0; s_cierre = s; }
        // error de localización: posición en el mapa contra la real (el mapa empieza en s = 0)
        double real = fmod(s, P.largo());
        double e = fabs(m.posicion() - real);
        e = fmin(e, P.largo() - e);
        if (s > s_cierre + 0.3) peor_loc = fmax(peor_loc, e);
      }
    }
    VERIFICAR(m.modo() == v2::Mapa::Modo::CERRADO, "%s: el mapa no cerró", cl);
    VERIFICAR(fabs(m.largo() - P.largo()) < 0.03, "%s: largo %.3f m contra %.3f m", cl, m.largo(), P.largo());
    VERIFICAR(s_cierre < P.largo() + 3.5, "%s: cierre a los %.2f m (vuelta de %.2f m)", cl, s_cierre, P.largo());
    VERIFICAR(peor_loc < 0.05, "%s: error de localización %.3f m", cl, peor_loc);
    m.calcular_perfil(7.06f, 8.0f, 6.0f, 2.0f);
    VERIFICAR(m.perfil_listo(), "%s: perfil", cl);
    printf("   %s: vuelta %.3f m, mapa %.3f m, cierre a %.2f m, localización ≤ %.1f mm, vueltas %d\n", cl, P.largo(),
           m.largo(), s_cierre, peor_loc * 1000, m.vueltas());
    // la pista cambia (otra pista): el mapa debe declararse inválido en menos de 1.5 m
    PistaPrueba Q;
    cargar_pista(strcmp(cl, "P2") ? "P2" : "P1", Q);
    double s2 = 0;
    const int nq = static_cast<int>(Q.x.size());
    while (m.modo() == v2::Mapa::Modo::CERRADO && s2 < 3.0) {
      const double s3 = s2 + v * dt;
      float dpsi = Q.h[static_cast<int>(s3 * 1000 + 300) % nq] - Q.h[static_cast<int>(s2 * 1000 + 300) % nq];
      while (dpsi > 3.14159f) dpsi -= 6.2831853f;
      while (dpsi < -3.14159f) dpsi += 6.2831853f;
      m.avanzar(v * dt, dpsi);
      s2 = s3;
    }
    VERIFICAR(m.modo() == v2::Mapa::Modo::INVALIDO, "%s: la pista cambió y el mapa sigue válido", cl);
  }
}

// ------------------------------------------------------------------------------------------------ 8. lazo cerrado
struct Simulador {
  const PistaPrueba& P;
  double x, y, th, wl = 0, wr = 0;
  int ir = 0;              // índice de la pista más cercano al eje
  v2::ModeloMotor mot;
  float dp_ventilador = 500.0f;   // Pa con el ventilador al mando de crucero [S]
  explicit Simulador(const PistaPrueba& p)
      : P(p), mot(v2::ModeloMotor::desde_ficha(cfg2::MOTOR_V_NOM, cfg2::MOTOR_RPM, cfg2::MOTOR_PAR_BLOQUEO,
                                                cfg2::MOTOR_I_BLOQUEO, cfg2::MOTOR_I_VACIO)) {
    x = p.x[0]; y = p.y[0]; th = p.h[0];
  }
  // distancia con signo de un punto a la línea (búsqueda local alrededor de i0)
  float distancia(double px, double py, int i0, bool* hueco) const {
    const int n = static_cast<int>(P.x.size());
    double mejor = 1e9; int im = i0;
    for (int d = -60; d <= 260; ++d) {
      const int i = ((i0 + d) % n + n) % n;
      const double e = (px - P.x[i]) * (px - P.x[i]) + (py - P.y[i]) * (py - P.y[i]);
      if (e < mejor) { mejor = e; im = i; }
    }
    *hueco = P.hueco[im];
    const double nx = -sin(P.h[im]), ny = cos(P.h[im]);
    return static_cast<float>((px - P.x[im]) * nx + (py - P.y[im]) * ny);
  }
  void actualizar_indice() {
    const int n = static_cast<int>(P.x.size());
    double mejor = 1e9; int im = ir;
    for (int d = -20; d <= 120; ++d) {
      const int i = ((ir + d) % n + n) % n;
      const double e = (x - P.x[i]) * (x - P.x[i]) + (y - P.y[i]) * (y - P.y[i]);
      if (e < mejor) { mejor = e; im = i; }
    }
    ir = im;
  }
  void sensores(v2::Entradas& in) const {
    const float ancho = 0.019f;                   // línea de 19 mm [S]
    for (int i = 0; i < cfg2::N_SENSORES; ++i) {
      const double sx = x + cfg2::SENSOR_X[i] * cos(th) - cfg2::SENSOR_Y[i] * sin(th);
      const double sy = y + cfg2::SENSOR_X[i] * sin(th) + cfg2::SENSOR_Y[i] * cos(th);
      bool h;
      const float d = fabsf(distancia(sx, sy, ir + 110, &h));
      float negro = h ? 0.0f : fminf(1.0f, fmaxf(0.0f, (ancho * 0.5f + 0.0015f - d) / 0.003f));
      in.ambiente[i] = 3950;
      in.encendido[i] = static_cast<uint16_t>(3950 - (3000 * (1 - negro) + 150 * negro));
    }
  }
  // un paso de 1 ms con los ciclos aplicados (modelo de motor y masa repartida en las dos ruedas)
  void paso(float dl, float dr, float vbat, float dt, float* il, float* irr) {
    const float r = cfg2::D_LLANTA * 0.5f, m = cfg2::MASA;
    const float a_max = cfg2::MU_REF * 9.81f * 1.6f;            // adherencia con succión (cota para el modelo)
    float I[2] = {mot.corriente(dl, vbat, static_cast<float>(wl)), mot.corriente(dr, vbat, static_cast<float>(wr))};
    double* w[2] = {&wl, &wr};
    for (int k = 0; k < 2; ++k) {
      const float i0 = fabsf(static_cast<float>(*w[k])) > 1.0f ? copysignf(mot.i0, static_cast<float>(*w[k])) : 0.0f;
      float a = mot.kt * (I[k] - i0) / r / (0.5f * m);          // m/s² de la mitad del robot
      a = fmaxf(-a_max, fminf(a_max, a));
      *w[k] += a / r * dt;
    }
    *il = fabsf(I[0]); *irr = fabsf(I[1]);
    const double v = r * (wl + wr) * 0.5, wz = r * (wr - wl) / cfg2::W_VIA;
    x += v * cos(th) * dt; y += v * sin(th) * dt; th += wz * dt;
    actualizar_indice();
  }
};

static void prueba_lazo_cerrado() {
  printf("8. lazo cerrado (núcleo completo sobre P1-P4)\n");
  const char* claves[] = {"P1", "P2", "P3", "P4"};
  for (const char* cl : claves) {
    PistaPrueba P;
    if (!cargar_pista(cl, P)) { VERIFICAR(false, "falta la pista %s", cl); continue; }
    v2::NucleoV2 nucleo;
    // calibración guardada (blanco ≈ 3000 cuentas de reflectancia, negro ≈ 150)
    v2::Guardado g{};
    nucleo.guardar(g);
    for (int i = 0; i < cfg2::N_SENSORES; ++i) { g.cal_min[i] = 150; g.cal_max[i] = 3000; }
    v2::sellar(g);
    nucleo.cargar(g);
    Simulador sim(P);
    v2::Entradas in;
    v2::Salidas out;
    const float dt = 1e-3f;
    double s_rec = 0;            // distancia recorrida por el eje sobre la pista
    int ir_ant = 0, vueltas = 0;
    double t_vuelta[4] = {0, 0, 0, 0}, t_ult = 0;
    double peor_e = 0, peor_i = 0;
    bool error = false, parada = false;
    float enc_acum_l = 0, enc_acum_r = 0;
    const int n = static_cast<int>(P.x.size());
    double t_inicio = -1;
    for (uint32_t ms = 0; ms < 40000; ++ms) {
      in.t_ms = ms;
      in.dt = dt;
      sim.sensores(in);
      in.btn_start = (ms >= 100 && ms < 160);
      in.v_bat = 7.6f;
      in.gz = static_cast<float>(cfg2::D_LLANTA * 0.5f * (sim.wr - sim.wl) / cfg2::W_VIA);
      // encoders: cuentas en el ciclo (con el signo de fábrica: izquierdo +, derecho −)
      enc_acum_l += static_cast<float>(sim.wl * dt / 6.2831853 * cfg2::CUENTAS_VUELTA);
      enc_acum_r += static_cast<float>(sim.wr * dt / 6.2831853 * cfg2::CUENTAS_VUELTA);
      in.d_enc_izq = static_cast<int32_t>(enc_acum_l); enc_acum_l -= in.d_enc_izq;
      in.d_enc_der = -static_cast<int32_t>(enc_acum_r); enc_acum_r += in.d_enc_der;
      in.baro_nueva = (ms % 5 == 0);
      in.p_amb = 101325.0f;
      in.p_cam = 101325.0f - sim.dp_ventilador * (out.esc / nucleo.prm().mando_esc);
      nucleo.ciclo(in, out);
      // el puente: ciclos con el signo de montaje (invertir_der = 1 por defecto)
      const float dl = out.ciclo_izq * (nucleo.prm().invertir_izq > 0.5f ? -1.0f : 1.0f);
      const float dr = out.ciclo_der * (nucleo.prm().invertir_der > 0.5f ? -1.0f : 1.0f);
      float il, irr;
      sim.paso(out.frenar ? 0.0f : dl, out.frenar ? 0.0f : dr, in.v_bat, dt, &il, &irr);
      in.i_izq = il; in.i_der = irr;
      peor_i = fmax(peor_i, fmax(il, irr));
      const v2::Estado e = nucleo.maquina().estado();
      if (e == v2::Estado::ERROR) { error = true; break; }
      if (e == v2::Estado::PARADA) { parada = true; break; }
      if (e == v2::Estado::SIGUIENDO && t_inicio < 0) t_inicio = ms * 1e-3;
      // avance sobre la pista y vueltas
      int di = sim.ir - ir_ant;
      if (di < -n / 2) di += n;
      ir_ant = sim.ir;
      if (t_inicio >= 0) {
        s_rec += di * 0.001;
        // desvío de la barra: centro del arco de sensores (en el eje del robot, a L delante) contra la línea
        bool h;
        const double bx = sim.x + cfg2::L_BARRA * cos(sim.th), by = sim.y + cfg2::L_BARRA * sin(sim.th);
        peor_e = fmax(peor_e, fabsf(sim.distancia(bx, by, sim.ir + 100, &h)));
        if (s_rec >= (vueltas + 1) * P.largo()) {
          t_vuelta[vueltas] = ms * 1e-3 - (vueltas ? t_ult : t_inicio);
          t_ult = ms * 1e-3;
          if (++vueltas == 3) break;
        }
      }
    }
    VERIFICAR(!error, "%s: ERROR %d", cl, static_cast<int>(nucleo.maquina().error()));
    VERIFICAR(!parada, "%s: PARADA (motivo %d)", cl, static_cast<int>(nucleo.maquina().motivo()));
    VERIFICAR(vueltas == 3, "%s: %d vueltas", cl, vueltas);
    VERIFICAR(peor_e < 0.025, "%s: la barra se alejó %.1f mm de la línea (semibarra 40.5 mm)", cl, peor_e * 1000);
    VERIFICAR(peor_i < cfg2::I_LIMITE_FIRMWARE * 1.06, "%s: corriente %.2f A", cl, peor_i);
    VERIFICAR(nucleo.mapa().modo() == v2::Mapa::Modo::CERRADO && nucleo.mapa().perfil_listo(), "%s: sin mapa", cl);
    VERIFICAR(vueltas < 3 || t_vuelta[2] < t_vuelta[0], "%s: la vuelta con mapa no es más rápida", cl);
    printf("   %s (%.2f m): vueltas %.2f / %.2f / %.2f s, desvío de la barra ≤ %.1f mm, I ≤ %.2f A, mapa %.2f m, T %.1f/%.1f K\n", cl,
           P.largo(), t_vuelta[0], t_vuelta[1], t_vuelta[2], peor_e * 1000, peor_i, nucleo.mapa().largo(),
           nucleo.temp_izq(), nucleo.temp_der());
  }
}

int main(int argc, char** argv) {
  DATOS = argc > 1 ? argv[1] : ".";
  prueba_perfil_oro();
  prueba_perfil_ciclico();
  prueba_motor();
  prueba_succion();
  prueba_estados();
  prueba_consola();
  prueba_mapa();
  prueba_lazo_cerrado();
  printf("%d verificaciones, %d fallas\n", pruebas, fallas);
  return fallas ? 1 : 0;
}
