// Simulador en lazo cerrado del seguidor de línea.
// Usa EXACTAMENTE el mismo código de posición, PID y control que el firmware.
//
// Modelo (ver docs/simulacion.md):
//   * pista dibujada en un mapa binario de 0.5 mm/celda (línea de 25 mm, huecos de 5 mm)
//   * robot diferencial: v = (vD + vI)/2,  w = (vD - vI)/L
//   * motores: respuesta de primer orden con constante tau_m
//   * sensores: apertura circular, ganancia/offset distintos por sensor, ruido, retardo
//
// Uso:  simular [clave=valor ...] [csv=archivo.csv] [barrido=1]
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cmath>
#include <string>
#include <vector>
#include <deque>
#include <map>
#include <random>
#include <algorithm>
#include "../firmware/seguidor/parametros.h"
#include "../firmware/seguidor/posicion.h"
#include "../firmware/seguidor/pid.h"
#include "../firmware/seguidor/control.h"

using std::vector;

// ---------------------------------------------------------------- pista
struct Pista {
  vector<float> px, py, pth;      // línea central cada ~0.25 mm
  vector<bool>  hueco;            // true: ahí no hay vinilo
  float step = 0.25f;
  // mapa binario
  float x0 = -100, y0 = -100;     // origen (mm)
  float res = 0.5f;               // mm por celda
  int   nx = 0, ny = 0;
  vector<unsigned char> mapa;
  float cx = 0, cy = 0, cth = 0;  // cursor

  void inicio(float x, float y, float th) { cx = x; cy = y; cth = th; add(false); }
  void add(bool h) { px.push_back(cx); py.push_back(cy); pth.push_back(cth); hueco.push_back(h); }
  void recta(float L, bool h = false) {
    int n = int(L / step + 0.5f);
    for (int i = 0; i < n; ++i) { cx += step * std::cos(cth); cy += step * std::sin(cth); add(h); }
  }
  // grados > 0: curva a la izquierda; < 0: a la derecha
  void arco(float r, float grados) {
    float ang = grados * float(M_PI) / 180.f;
    int n = int(std::fabs(ang) * r / step + 0.5f);
    float dth = ang / n;
    for (int i = 0; i < n; ++i) {
      cth += dth * 0.5f; cx += step * std::cos(cth); cy += step * std::sin(cth); cth += dth * 0.5f; add(false);
    }
  }
  void construir_mapa(float ancho) {
    float minx = 1e9, maxx = -1e9, miny = 1e9, maxy = -1e9;
    for (size_t i = 0; i < px.size(); ++i) { minx = std::min(minx, px[i]); maxx = std::max(maxx, px[i]); miny = std::min(miny, py[i]); maxy = std::max(maxy, py[i]); }
    x0 = minx - 150; y0 = miny - 150;
    nx = int((maxx - minx + 300) / res) + 1; ny = int((maxy - miny + 300) / res) + 1;
    mapa.assign(size_t(nx) * ny, 0);
    for (size_t i = 0; i < px.size(); ++i) {
      if (hueco[i]) continue;
      float nxv = -std::sin(pth[i]), nyv = std::cos(pth[i]);
      for (float l = -ancho / 2; l <= ancho / 2; l += res * 0.5f) {
        float x = px[i] + nxv * l, y = py[i] + nyv * l;
        int ix = int((x - x0) / res), iy = int((y - y0) / res);
        if (ix >= 0 && ix < nx && iy >= 0 && iy < ny) mapa[size_t(iy) * nx + ix] = 1;
      }
    }
  }
  bool negro(float x, float y) const {
    int ix = int((x - x0) / res), iy = int((y - y0) / res);
    if (ix < 0 || ix >= nx || iy < 0 || iy >= ny) return false;
    return mapa[size_t(iy) * nx + ix] != 0;
  }
  // cobertura 0..1 de un sensor circular de radio r en (x,y)
  float cobertura(float x, float y, float r) const {
    static const float k[9][2] = {{0,0},{1,0},{-1,0},{0,1},{0,-1},{.7071f,.7071f},{-.7071f,.7071f},{.7071f,-.7071f},{-.7071f,-.7071f}};
    int c = 0;
    for (auto& a : k) c += negro(x + a[0] * r, y + a[1] * r);
    return c / 9.f;
  }
};

// Pista de prueba legal: cabe en 2.44 x 1.22 m, SIN cruces, líneas separadas >= 200 mm,
// curvas de radio >= 150 mm, huecos de 5 mm, una S y dos esquinas de 90 grados (radio 150 mm).
Pista pista_prueba() {
  Pista p; p.inicio(100, 120, 0);
  p.recta(300); p.recta(5, true); p.recta(395);        // recta con hueco de 5 mm
  p.arco(200, 180);                                    // vuelta en U a la izquierda
  p.recta(250); p.recta(5, true); p.recta(245);        // segundo hueco
  p.arco(200, -180);                                   // vuelta en U a la derecha
  p.recta(300); p.arco(200, 45); p.arco(200, -45);     // S suave hacia arriba
  p.recta(300);
  p.arco(150, -90); p.recta(300); p.arco(150, 90);     // dos esquinas de 90 grados
  p.recta(150); p.recta(5, true); p.recta(145);        // tercer hueco
  p.construir_mapa(par::ANCHO_LINEA_MM);
  return p;
}

// ---------------------------------------------------------------- configuración
struct Config {
  // robot / sensores
  int   n_sens = 8;
  std::string geom = "recta";   // recta | arco
  float paso = 9.525f;          // mm entre sensores (recta) o a lo largo del arco
  float radio_arco = 80.f;      // mm
  float dist_eje = 100.f;       // mm del eje a los sensores
  float L = 75.f;               // separación entre ruedas, mm
  float apertura = 4.f;         // radio de la mancha del sensor, mm
  float ruido = 15.f;           // cuentas ADC (desviación estándar)
  int   retardo = 2;            // ciclos de control de retardo de lectura
  // motores
  float vmax = 1400.f;          // mm/s con comando 1.0 (carga)
  float tau_m = 0.060f;         // s
  // control (se llena con los valores por defecto y se sobreescribe)
  ParamControl pc = param_por_defecto();
  // simulación
  float tmax = 40.f;
  float offset_ini = 0.f;       // desplazamiento lateral inicial, mm
  unsigned semilla = 1;
  float mu = 0.9f;              // agarre supuesto de las llantas
  // escenarios
  bool  fin_es_meta = true;     // false: la línea se acaba y se mide cómo se detiene el robot
  float perturb_t = -1.f;       // s; si >= 0, en ese instante se desplaza el robot de lado
  float perturb_mm = 0.f;       // + a la izquierda de la línea
  float tol_estab_mm = 3.f;     // banda para el tiempo de establecimiento
};

struct Resultado {
  bool  completo = false;
  std::string fin = "";
  float tiempo = 0.f;
  float error_medio = 0.f, error_max = 0.f;
  float vmedia = 0.f;
  float alat_max = 0.f;         // mm/s^2
  float frac_derrape = 0.f;     // fracción de tiempo con a_lat > mu*g
  float longitud = 0.f;
  float sobreimpulso_mm = 0.f;  // máximo cruce al lado contrario del desplazamiento inicial
  float t_estab = -1.f;         // s desde el inicio (o la perturbación) hasta quedar en ±tol
  int   n_perdidas = 0;         // veces que pasó de ver la línea a no verla
  float t_sin_linea = 0.f;      // s acumulados sin ver la línea
  float t_parada = -1.f;        // s desde que se acaba la línea hasta que el control se rinde
  float dist_parada = 0.f;      // mm recorridos después del final de la línea
};

struct Muestra { float t, x, y, th, err, pos_est, izq, der, v; };

Resultado correr(const Config& cfg, const Pista& pista, vector<Muestra>* traza = nullptr) {
  using namespace posicion;
  std::mt19937 rng(cfg.semilla);
  std::normal_distribution<float> gauss(0.f, 1.f);

  Geometria g = (cfg.geom == "arco") ? geometria_arco(cfg.n_sens, cfg.paso, cfg.radio_arco, cfg.dist_eje)
                                      : geometria_recta(cfg.n_sens, cfg.paso, cfg.dist_eje);
  // características de cada sensor (blanco/negro distintos por sensor)
  float blanco[par::MAX_SENSORES], negro[par::MAX_SENSORES];
  for (int i = 0; i < g.n; ++i) {
    blanco[i] = 2800.f + 800.f * (rng() % 1000) / 1000.f;
    negro[i]  = 400.f + 500.f * (rng() % 1000) / 1000.f;
  }
  // calibración: barrido sobre blanco y negro con ruido
  Calibracion cal; cal.reiniciar(g.n);
  for (int k = 0; k < 50; ++k) {
    float r[par::MAX_SENSORES] = {};
    for (int i = 0; i < g.n; ++i) r[i] = blanco[i] + cfg.ruido * gauss(rng);
    cal.muestrear(r);
    for (int i = 0; i < g.n; ++i) r[i] = negro[i] + cfg.ruido * gauss(rng);
    cal.muestrear(r);
  }

  ControladorLinea ctl(cfg.pc);
  const float dt_ctl = par::PERIODO_CONTROL_US * 1e-6f;
  const int sub = 4; const float dt = dt_ctl / sub;

  // estado
  float X = pista.px[0] - std::sin(pista.pth[0]) * cfg.offset_ini;
  float Y = pista.py[0] + std::cos(pista.pth[0]) * cfg.offset_ini;
  float th = pista.pth[0];
  float vI = 0, vD = 0, cmdI = 0, cmdD = 0;
  size_t idx = 0;
  std::deque<Estimacion> cola;
  Estimacion vacia{0, 0, false};
  for (int i = 0; i < cfg.retardo; ++i) cola.push_back(vacia);

  Resultado R;
  double suma_err = 0, suma_v = 0; long n_ctl = 0, n_der = 0;
  bool visto_prev = false, perturbado = false, al_final = false;
  float t_ref = 0.f, signo_ini = 0.f, t_fin = 0.f, x_fin = 0.f, y_fin = 0.f, t_fuera_banda = 0.f;
  float t = 0.f;
  const float g_mm = 9810.f;

  while (t < cfg.tmax) {
    // --- lectura de sensores (verdad física + modelo de ruido) ---
    float fx = std::cos(th), fy = std::sin(th), rx = std::sin(th), ry = -std::cos(th);
    float refl[par::MAX_SENSORES] = {}, osc[par::MAX_SENSORES] = {};
    for (int i = 0; i < g.n; ++i) {
      float sx = X + g.y[i] * fx + g.x[i] * rx;
      float sy = Y + g.y[i] * fy + g.x[i] * ry;
      float cov = pista.cobertura(sx, sy, cfg.apertura);
      refl[i] = blanco[i] + (negro[i] - blanco[i]) * cov + cfg.ruido * gauss(rng);
    }
    normalizar(cal, refl, osc);
    Estimacion est = estimar_posicion(g, osc, par::UMBRAL_RUIDO, par::CONFIANZA_MIN);
    cola.push_back(est); Estimacion usada = cola.front(); cola.pop_front();

    SalidaControl s = ctl.actualizar(usada, dt_ctl);
    cmdI = s.izq; cmdD = s.der;

    // --- error verdadero respecto a la línea y avance ---
    // error medido en el centro de la barra de sensores (lo que importa para seguir la línea)
    const float Px = X + cfg.dist_eje * std::cos(th), Py = Y + cfg.dist_eje * std::sin(th);
    size_t mejor = idx; float dmin = 1e9f;
    size_t a = idx > 400 ? idx - 400 : 0, b = std::min(pista.px.size(), idx + 1600);
    for (size_t k = a; k < b; ++k) {
      float dx = pista.px[k] - Px, dy = pista.py[k] - Py; float d2 = dx * dx + dy * dy;
      if (d2 < dmin) { dmin = d2; mejor = k; }
    }
    idx = mejor; float dist = std::sqrt(dmin);
    // error con signo: + si la barra de sensores está a la izquierda de la línea
    const float con_signo = -std::sin(pista.pth[idx]) * (Px - pista.px[idx]) + std::cos(pista.pth[idx]) * (Py - pista.py[idx]);
    if (!al_final) { suma_err += dist; R.error_max = std::max(R.error_max, dist); ++n_ctl; }
    if (signo_ini == 0.f && std::fabs(con_signo) > 1.f) signo_ini = con_signo > 0 ? 1.f : -1.f;
    if (signo_ini != 0.f && !al_final) R.sobreimpulso_mm = std::max(R.sobreimpulso_mm, -signo_ini * con_signo);
    if (dist > cfg.tol_estab_mm && !al_final) t_fuera_banda = t;
    if (visto_prev && !usada.linea_visible) ++R.n_perdidas;
    if (!usada.linea_visible) R.t_sin_linea += dt_ctl;
    visto_prev = usada.linea_visible;
    if (!cfg.fin_es_meta && !al_final && idx + 4 >= pista.px.size()) { al_final = true; t_fin = t; x_fin = X; y_fin = Y; }

    // perturbación: empujón lateral al robot (choque, rebote, polvo)
    if (cfg.perturb_t >= 0.f && !perturbado && t >= cfg.perturb_t) {
      perturbado = true; t_ref = t;
      X += -std::sin(th) * cfg.perturb_mm; Y += std::cos(th) * cfg.perturb_mm;
      signo_ini = cfg.perturb_mm > 0 ? 1.f : -1.f; R.sobreimpulso_mm = 0.f;
    }

    // --- física (4 subpasos) ---
    float alat = 0.f;
    for (int k = 0; k < sub; ++k) {
      vI += (cmdI * cfg.vmax - vI) * dt / cfg.tau_m;
      vD += (cmdD * cfg.vmax - vD) * dt / cfg.tau_m;
      float v = 0.5f * (vI + vD), w = (vD - vI) / cfg.L;
      X += v * std::cos(th) * dt; Y += v * std::sin(th) * dt; th += w * dt;
      alat = std::fabs(v * w);
    }
    R.alat_max = std::max(R.alat_max, alat);
    if (alat > cfg.mu * g_mm) ++n_der;
    float v = 0.5f * (vI + vD); suma_v += v;
    t += dt_ctl;
    if (traza) traza->push_back({t, X, Y, th, dist, usada.pos_mm, cmdI, cmdD, v});

    if (cfg.fin_es_meta && idx + 80 >= pista.px.size()) { R.completo = true; R.fin = "meta"; break; }
    if (s.linea_perdida) {
      R.fin = "linea_perdida";
      if (al_final) { R.completo = true; R.t_parada = t - t_fin; R.dist_parada = std::hypot(X - x_fin, Y - y_fin); }
      break;
    }
    if (dist > 70.f && !al_final) { R.fin = "salio"; break; }
  }
  R.t_estab = (t_fuera_banda > t_ref) ? t_fuera_banda - t_ref : 0.f;
  if (R.fin.empty()) R.fin = "tiempo";
  R.tiempo = t;
  R.error_medio = n_ctl ? float(suma_err / n_ctl) : 0.f;
  R.vmedia = n_ctl ? float(suma_v / n_ctl) : 0.f;
  R.frac_derrape = n_ctl ? float(n_der) / n_ctl : 0.f;
  R.longitud = idx * pista.step;
  return R;
}

// ---------------------------------------------------------------- escenarios reproducibles
// Cada escenario aísla una situación de la pista (reglamento: curvas < 90° de radio > 15 cm,
// secciones en U, discontinuidades de hasta 5 mm). Mismas semillas = mismos resultados.
struct Escenario { const char* nombre; const char* que_mide; };
static const Escenario ESCENARIOS[] = {
  {"recta_desplazado", "arranca 20 mm fuera de la línea: sobreimpulso y establecimiento"},
  {"curva_90_r150",    "curva de 90 grados con el radio mínimo del reglamento"},
  {"U_r150",           "sección en U de radio 150 mm"},
  {"S_r150",           "S con radio 150 mm (cambio de sentido de giro)"},
  {"huecos_5mm",       "tres discontinuidades de 5 mm en recta"},
  {"empujon_izq",      "empujón lateral de 30 mm a la izquierda a mitad de recta"},
  {"empujon_der",      "empujón lateral de 30 mm a la derecha a mitad de recta"},
  {"fin_de_linea",     "la línea se acaba: tiempo y distancia hasta que el robot se detiene"},
  {"pista_completa",   "pista de prueba de 4.4 m (todas las situaciones juntas)"},
};

static Pista pista_escenario(const std::string& n, Config& c) {
  Pista p; p.inicio(100, 300, 0);
  if (n == "recta_desplazado") { p.recta(1500); c.offset_ini = 20.f; }
  else if (n == "curva_90_r150") { p.recta(400); p.arco(150, -90); p.recta(500); }
  else if (n == "U_r150") { p.recta(400); p.arco(150, 180); p.recta(500); }
  else if (n == "S_r150") { p.recta(300); p.arco(150, 80); p.arco(150, -80); p.recta(400); }
  else if (n == "huecos_5mm") { for (int i = 0; i < 3; ++i) { p.recta(300); p.recta(5, true); } p.recta(300); }
  else if (n == "empujon_izq") { p.recta(1800); c.perturb_t = 1.0f; c.perturb_mm = 30.f; }
  else if (n == "empujon_der") { p.recta(1800); c.perturb_t = 1.0f; c.perturb_mm = -30.f; }
  else if (n == "fin_de_linea") { p.recta(600); c.fin_es_meta = false; }
  else { return pista_prueba(); }
  p.construir_mapa(par::ANCHO_LINEA_MM);
  return p;
}

struct Controlador { const char* nombre; void (*aplicar)(ParamControl&); };
static const Controlador CONTROLADORES[] = {
  {"P",            [](ParamControl& p) { p.kd = 0.f; p.ki = 0.f; }},
  {"PD",           [](ParamControl&) {}},                                   // valores por defecto
  {"PID",          [](ParamControl& p) { p.ki = 0.3f; }},
  {"PD_sin_freno", [](ParamControl& p) { p.freno_error = 0.f; }},
  {"PD_agresivo",  [](ParamControl& p) { p.kp = 0.08f; p.kd = 0.004f; }},
};

static void correr_escenarios(const Config& base, bool comparar) {
  std::printf("escenario,controlador,sensores,fin,ok,tiempo_s,err_medio_mm,err_max_mm,sobreimpulso_mm,t_estab_s,perdidas,t_sin_linea_s,t_parada_s,dist_parada_mm,alat_max_g\n");
  for (const auto& e : ESCENARIOS) {
    for (const auto& k : CONTROLADORES) {
      if (!comparar && std::string(k.nombre) != "PD") continue;
      Config c = base; k.aplicar(c.pc);
      Pista p = pista_escenario(e.nombre, c);
      Resultado r = correr(c, p);
      std::printf("%s,%s,%d,%s,%d,%.2f,%.2f,%.1f,%.1f,%.2f,%d,%.2f,%.2f,%.0f,%.2f\n", e.nombre, k.nombre, c.n_sens,
                  r.fin.c_str(), int(r.completo), r.tiempo, r.error_medio, r.error_max, r.sobreimpulso_mm, r.t_estab,
                  r.n_perdidas, r.t_sin_linea, r.t_parada, r.dist_parada, r.alat_max / 9810.f);
    }
  }
}

// ---------------------------------------------------------------- argumentos
static bool fijar(Config& c, const std::string& k, const std::string& v) {
  float f = std::strtof(v.c_str(), nullptr);
  if (k == "sensores") c.n_sens = int(f);
  else if (k == "geom") c.geom = v;
  else if (k == "paso") c.paso = f;
  else if (k == "radio_arco") c.radio_arco = f;
  else if (k == "dist_eje") c.dist_eje = f;
  else if (k == "L") c.L = f;
  else if (k == "apertura") c.apertura = f;
  else if (k == "ruido") c.ruido = f;
  else if (k == "retardo") c.retardo = int(f);
  else if (k == "vmax") c.vmax = f;
  else if (k == "tau_m") c.tau_m = f;
  else if (k == "tmax") c.tmax = f;
  else if (k == "offset") c.offset_ini = f;
  else if (k == "semilla") c.semilla = unsigned(f);
  else if (k == "mu") c.mu = f;
  else if (k == "kp") c.pc.kp = f;
  else if (k == "ki") c.pc.ki = f;
  else if (k == "kd") c.pc.kd = f;
  else if (k == "vbase") c.pc.vbase = f;
  else if (k == "freno") c.pc.freno_error = f;
  else if (k == "error_ref") c.pc.error_ref_mm = f;
  else if (k == "vmin_rel") c.pc.vmin_rel = f;
  else if (k == "u_max") c.pc.u_max = f;
  else if (k == "rueda_min") c.pc.rueda_min = f;
  else if (k == "retencion") c.pc.t_retencion_s = f;
  else if (k == "busqueda") c.pc.t_busqueda_s = f;
  else if (k == "u_busqueda") c.pc.u_busqueda = f;
  else return false;
  return true;
}

static void imprimir(const char* etiqueta, const Config& c, const Resultado& r) {
  std::printf("%-22s sens=%2d %-5s kp=%.4f kd=%.4f vbase=%.2f -> %-13s t=%5.2fs err_med=%5.2fmm err_max=%5.1fmm v_med=%4.0fmm/s alat_max=%.2fg derrape=%4.1f%%\n",
              etiqueta, c.n_sens, c.geom.c_str(), c.pc.kp, c.pc.kd, c.pc.vbase, r.fin.c_str(), r.tiempo, r.error_medio, r.error_max,
              r.vmedia, r.alat_max / 9810.f, 100.f * r.frac_derrape);
}

int main(int argc, char** argv) {
  Config cfg; std::string csv, modo;
  for (int i = 1; i < argc; ++i) {
    std::string a = argv[i]; auto p = a.find('=');
    if (p == std::string::npos) { std::fprintf(stderr, "argumento invalido: %s\n", a.c_str()); return 2; }
    std::string k = a.substr(0, p), v = a.substr(p + 1);
    if (k == "csv") csv = v; else if (k == "modo") modo = v;
    else if (!fijar(cfg, k, v)) { std::fprintf(stderr, "clave desconocida: %s\n", k.c_str()); return 2; }
  }
  if (modo == "escenarios" || modo == "comparar") { correr_escenarios(cfg, modo == "comparar"); return 0; }
  Pista pista = pista_prueba();
  std::printf("# pista: %zu puntos, longitud %.0f mm\n", pista.px.size(), pista.px.size() * pista.step);

  if (modo == "barrido_vbase") {
    // un renglón por velocidad base: CSV vbase,completo,tiempo,err_medio,err_max,derrape
    std::printf("vbase,fin,tiempo,err_medio,err_max,vmedia,alat_g,derrape\n");
    for (float vb = 0.10f; vb <= 1.001f; vb += 0.05f) {
      Config c = cfg; c.pc.vbase = vb;
      Resultado r = correr(c, pista);
      std::printf("%.2f,%s,%.2f,%.2f,%.1f,%.0f,%.2f,%.3f\n", vb, r.fin.c_str(), r.tiempo, r.error_medio, r.error_max, r.vmedia, r.alat_max / 9810.f, r.frac_derrape);
    }
    return 0;
  }
  if (modo == "barrido_pid") {
    std::printf("kp,kd,fin,tiempo,err_medio,err_max,derrape\n");
    for (float kp : {0.004f, 0.006f, 0.008f, 0.010f, 0.012f, 0.016f, 0.020f, 0.028f, 0.040f})
      for (float kd : {0.0f, 0.0002f, 0.0005f, 0.0008f, 0.0012f, 0.0020f, 0.0035f}) {
        Config c = cfg; c.pc.kp = kp; c.pc.kd = kd;
        Resultado r = correr(c, pista);
        std::printf("%.4f,%.4f,%s,%.2f,%.2f,%.1f,%.3f\n", kp, kd, r.fin.c_str(), r.tiempo, r.error_medio, r.error_max, r.frac_derrape);
      }
    return 0;
  }
  vector<Muestra> traza;
  Resultado r = correr(cfg, pista, csv.empty() ? nullptr : &traza);
  imprimir("corrida", cfg, r);
  if (!csv.empty()) {
    FILE* f = std::fopen(csv.c_str(), "w");
    if (!f) { std::fprintf(stderr, "no pude abrir %s\n", csv.c_str()); return 2; }
    std::fprintf(f, "t,x,y,th,err,pos_est,izq,der,v\n");
    for (auto& m : traza) std::fprintf(f, "%.4f,%.2f,%.2f,%.5f,%.3f,%.3f,%.3f,%.3f,%.1f\n", m.t, m.x, m.y, m.th, m.err, m.pos_est, m.izq, m.der, m.v);
    std::fclose(f);
    // pista para graficar
    std::string pf = csv + ".pista.csv"; FILE* g2 = std::fopen(pf.c_str(), "w");
    if (g2) { std::fprintf(g2, "x,y,hueco\n"); for (size_t i = 0; i < pista.px.size(); i += 4) std::fprintf(g2, "%.2f,%.2f,%d\n", pista.px[i], pista.py[i], int(pista.hueco[i])); std::fclose(g2); }
  }
  return r.completo ? 0 : 1;
}
