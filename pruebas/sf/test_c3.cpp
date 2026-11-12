// El firmware (sf_logica.cpp) debe reproducir al simulador (sim/nucleo.py paso_sf) para
// C2, C3m, C3g y C3e, y la estimación con coordenadas de la barra vigente. Robot y parámetros desde
// config_maestra.h (generada del YAML). Compilado por ejecutar.sh con ASan/UBSan.
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

#include "../../firmware/config_maestra.h"
#include "../../firmware/logica/sf_logica.h"

static std::vector<std::vector<double>> leer(const char* ruta) {
  std::ifstream f(ruta);
  if (!f) { std::printf("no se pudo abrir %s\n", ruta); std::exit(1); }
  std::string linea;
  std::getline(f, linea);
  std::vector<std::vector<double>> filas;
  while (std::getline(f, linea)) {
    std::vector<double> v;
    std::stringstream ss(linea);
    std::string c;
    while (std::getline(ss, c, ',')) v.push_back(std::atof(c.c_str()));
    filas.push_back(v);
  }
  return filas;
}

int main() {
  sf::Robot r;
  r.motor = sf::Motor{cfg::MOTOR_V_NOM, cfg::MOTOR_RPM, cfg::MOTOR_PAR_BLOQUEO, cfg::MOTOR_I_BLOQUEO, cfg::MOTOR_I_VACIO};
  r.v_max_motor = cfg::MOTOR_LIMITE_V;
  r.diam = cfg::D_LLANTA; r.W = cfg::W_VIA; r.masa = cfg::MASA; r.L = cfg::L_CUELLO;
  int fallos = 0;
  double peor = 0;
  const auto filas = leer("dorados_c3.csv");
  for (int fuente = 0; fuente <= 3; ++fuente) {
    sf::ParamSF p;
    p.v_max = cfg::V_MAX; p.a_lat = cfg::A_LAT; p.a_lon = cfg::A_LON; p.k_pp = cfg::K_PP;
    p.kp = cfg::KP; p.kd = cfg::KD; p.tau_d = cfg::TAU_D; p.tau_k = cfg::TAU_K; p.fuente_k = fuente; p.piso = -0.4f;   // igual al generador
    sf::ControlSF c(p, r);
    double peor_f = 0;
    for (const auto& v : filas) {
      if ((int)v[0] != fuente) continue;
      const sf::Salida s = c.paso((float)v[2], false, (float)v[3], (float)v[4], (float)v[5], (float)v[6], (float)v[7]);
      peor_f = std::fmax(peor_f, std::fmax(std::fabs(s.izq - v[8]), std::fmax(std::fabs(s.der - v[9]), std::fabs(s.v_cmd - v[10]))));
    }
    std::printf("fuente %d: diferencia máxima %.2e\n", fuente, peor_f);
    if (peor_f > 2e-4) ++fallos;
    peor = std::fmax(peor, peor_f);
  }
  const auto fc = leer("dorados_coord.csv");
  const int n = cfg::N_SENSORES;
  double peor_e = 0;
  int dif_bool = 0;
  for (const auto& v : fc) {
    float lect[cfg::N_SENSORES];
    for (int i = 0; i < n; ++i) lect[i] = (float)v[i];
    const sf::Lectura l = sf::estimar_coord(lect, cfg::SENSOR_Y, n, cfg::UMBRAL);
    if ((int)l.visible != (int)v[n] || (int)l.borde != (int)v[n + 2]) ++dif_bool;
    peor_e = std::fmax(peor_e, std::fabs(l.e - v[n + 1]));
  }
  std::printf("estimar_coord: %zu casos, diferencia máxima %.2e m, banderas distintas %d\n", fc.size(), peor_e, dif_bool);
  if (peor_e > 1e-6 || dif_bool) ++fallos;
  std::printf("%s\n", fallos ? "FALLA: firmware distinto del simulador" : "firmware = simulador (C2, C3m, C3g, C3e, estimar_coord)");
  return fallos ? 1 : 0;
}
