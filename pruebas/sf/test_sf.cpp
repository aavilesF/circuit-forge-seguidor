// Pruebas de la lógica del Speed Follower (C++ puro). Compara con la referencia Python (vectores dorados)
// y verifica propiedades de seguridad. Uso: ./ejecutar.sh
#include <cstdio>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#include <fstream>
#include <sstream>
#include <random>
#include "../../firmware/sf/sf_logica.h"

static int fallos = 0, total = 0;
#define CHECK(c, m) do { ++total; if (!(c)) { ++fallos; std::printf("FALLO: %s (%s:%d)\n", m, __FILE__, __LINE__); } } while (0)

static std::vector<std::vector<std::string>> leer_csv(const char* ruta) {
  std::vector<std::vector<std::string>> filas; std::ifstream f(ruta); std::string l;
  std::getline(f, l);
  while (std::getline(f, l)) { if (!l.empty() && l.back() == '\r') l.pop_back(); std::vector<std::string> c; std::stringstream ss(l); std::string x; while (std::getline(ss, x, ',')) c.push_back(x); if (l.back() == ',') c.push_back(""); filas.push_back(c); }
  return filas;
}

static sf::Motor motor_12v_10() { return sf::Motor{12.0f, 3400.0f, 0.17f * sf::KGCM, 0.75f, 0.08f}; }

static void caso(const std::string& n, sf::Robot& r, sf::ParamSF& p) {
  r = sf::Robot{}; p = sf::ParamSF{};
  r.L = 0.13f; r.n_sens = 8; r.paso = 0.0095f;
  if (n == "pololu15") { r.motor = sf::motor_pololu_12v_15(); p.v_max = 1.2f; p.kp = 120; p.kd = 4; p.a_lat = 4; }
  else if (n == "ga12_6v") { r.motor = sf::motor_ga12_n20_6v_supuesto(); r.v_max_motor = 6.0f; p.v_max = 1.3f; p.kp = 80; p.kd = 2; p.a_lat = 4; }
  else if (n == "inversion") { r.motor = sf::motor_pololu_12v_15(); p.v_max = 1.2f; p.kp = 200; p.kd = 6; p.a_lat = 4; p.permitir_inversion = true; }
  else if (n == "freno") { r.motor = motor_12v_10(); p.v_max = 1.4f; p.kp = 120; p.kd = 4; p.a_lat = 6; p.a_lon = 6; p.freno_activo = true; }
}

int main() {
  // ---- 1. Vectores dorados del control (Python = referencia)
  auto filas = leer_csv("dorados_control.csv");
  CHECK(filas.size() == 12000, "12000 filas doradas");
  std::string actual; sf::Robot r; sf::ParamSF p; sf::ControlSF* c = nullptr;
  double err_max = 0; int malos = 0;
  for (auto& f : filas) {
    if (f[0] != actual) { actual = f[0]; caso(actual, r, p); delete c; c = new sf::ControlSF(p, r); }
    const float e = std::stof(f[2]), dt = std::stof(f[4]), vb = std::stof(f[5]);
    const bool borde = f[3] == "1";
    sf::Salida s = c->paso(e, borde, dt, vb);
    const double d = std::fmax(std::fabs(s.izq - std::stod(f[6])), std::fmax(std::fabs(s.der - std::stod(f[7])), std::fabs(s.v_cmd - std::stod(f[8]))));
    err_max = std::fmax(err_max, d);
    if (d > 2e-3) ++malos;
  }
  delete c;
  std::printf("control vs Python: diferencia máxima %.2e en 12000 pasos (4 configuraciones)\n", err_max);
  CHECK(malos == 0, "C++ reproduce a Python con tolerancia 2e-3");

  // ---- 2. Vectores dorados de la estimación
  auto fe = leer_csv("dorados_estimar.csv");
  int malos_e = 0;
  for (auto& f : fe) {
    const int n = std::stoi(f[0]); const float paso = std::stof(f[1]);
    float l[12]; for (int i = 0; i < n; ++i) l[i] = std::stof(f[2 + i]);
    sf::Lectura le = sf::estimar(l, n, paso);
    const bool vis = f[14] == "1"; const float e = std::stof(f[15]); const bool bo = f[16] == "1";
    if (le.visible != vis || (vis && (std::fabs(le.e - e) > 1e-5f || le.borde != bo))) {
      if (malos_e < 3) std::printf("  estimar distinto: n=%d vis %d/%d e %.6f/%.6f borde %d/%d\n", n, le.visible, vis, le.e, e, le.borde, bo);
      ++malos_e;
    }
  }
  CHECK(malos_e == 0, "estimar() igual a Python en 500 casos");

  // ---- 3. Propiedades de seguridad (entradas aleatorias)
  std::mt19937 rng(3); std::uniform_real_distribution<float> U(-1, 1);
  sf::Robot rb; rb.motor = sf::motor_pololu_12v_15(); sf::ParamSF ps;
  sf::ControlSF cs(ps, rb);
  int inv = 0; bool en_limite = true, rampa_ok = true; float v_prev = 0;
  for (int k = 0; k < 20000; ++k) {
    const float e = 0.04f * U(rng); const float dt = 0.001f + 0.0005f * (U(rng) + 1); const float vb = 7.4f + 0.9f * U(rng);
    sf::Salida s = cs.paso(e, std::fabs(e) > 0.03f, dt, vb);
    inv += s.inversion;
    if (std::fabs(s.izq) > 1.0f + 1e-6f || std::fabs(s.der) > 1.0f + 1e-6f) en_limite = false;
    if (std::fabs(s.v_cmd - v_prev) > ps.a_lon * dt + 1e-5f) rampa_ok = false;
    v_prev = s.v_cmd;
  }
  CHECK(inv == 0, "sin permitir_inversion nunca hay una rueda negativa y otra positiva");
  CHECK(en_limite, "ciclos dentro de [-1, 1]");
  CHECK(rampa_ok, "la velocidad pedida respeta la rampa a_lon");

  // motor de 6 V en 2S: nunca más de 6 V promedio
  sf::Robot r6; r6.motor = sf::motor_ga12_n20_6v_supuesto(); r6.v_max_motor = 6.0f; sf::ParamSF p6; p6.v_max = 5.0f;
  sf::ControlSF c6(p6, r6); bool v6 = true;
  for (int k = 0; k < 5000; ++k) { sf::Salida s = c6.paso(0.0f, false, 0.001f, 8.4f); if (s.izq * 8.4f > 6.0f + 1e-3f || s.der * 8.4f > 6.0f + 1e-3f) v6 = false; }
  CHECK(v6, "motor de 6 V limitado a 6 V promedio con batería llena");

  // curvatura alta -> la velocidad pedida baja
  sf::ControlSF cc(ps, rb);
  for (int k = 0; k < 3000; ++k) cc.paso(0.0f, false, 0.001f, 7.4f);
  const float v_recta = cc.paso(0.0f, false, 0.001f, 7.4f).v_cmd;
  for (int k = 0; k < 600; ++k) cc.paso(0.03f, false, 0.001f, 7.4f);
  const float v_curva = cc.paso(0.03f, false, 0.001f, 7.4f).v_cmd;
  const float v_teo = std::sqrt(ps.a_lat * rb.L * rb.L / (2 * 0.03f));
  CHECK(v_recta > 1.19f && std::fabs(v_curva - v_teo) < 0.03f, "frena en curva: v = sqrt(a_lat·L²/(2e))");

  // línea a la derecha -> rueda izquierda más rápida
  sf::ControlSF cd(ps, rb);
  for (int k = 0; k < 500; ++k) cd.paso(0.0f, false, 0.001f, 7.4f);
  sf::Salida sd = cd.paso(0.01f, false, 0.001f, 7.4f);
  CHECK(sd.izq > sd.der, "e > 0 (línea a la derecha) -> izquierda más rápida");

  // pérdida de línea: mantiene la última corrección y se detiene a los t_perdida
  sf::ControlSF cl(ps, rb);
  for (int k = 0; k < 500; ++k) cl.actualizar(sf::Lectura{0.01f, true, false}, 0.001f, 7.4f);
  sf::Salida s1 = cl.actualizar(sf::Lectura{0, false, false}, 0.001f, 7.4f);
  CHECK(!s1.linea_perdida && s1.izq > s1.der, "sin línea: sigue girando hacia el último lado");
  sf::Salida s2{};
  for (int k = 0; k < 320; ++k) s2 = cl.actualizar(sf::Lectura{0, false, false}, 0.001f, 7.4f);
  CHECK(s2.linea_perdida && s2.izq == 0.0f && s2.der == 0.0f, "tras 0.3 s sin línea: paro");

  std::printf("%d pruebas, %d fallos\n", total, fallos);
  return fallos ? 1 : 0;
}
