// Speed Follower Circuit Forge — firmware del STM32G431CBT6 (PCB-chasis).
//
// Ciclo de control a 1 kHz (TIM6): lectura de los 16 sensores con resta de luz ambiente (ADC1 y ADC2 en paralelo),
// normalización con la calibración, estimación de la línea (sf::estimar_coord), encoders, controlador
// sf::ControlSF (el mismo código verificado contra el simulador) y PWM al DRV8833.
//
// Seguridad: el robot NO se mueve hasta pulsar START (regla R08) con calibración válida y batería suficiente;
// se detiene si pierde la línea más de T_PERDIDA, con batería crítica, con nFAULT del puente H, con una rueda
// trabada o con lecturas imposibles de los sensores. START durante la carrera también detiene.
//
// Calibración (regla C03): CAL -> durante ≤ 10 s se desliza el robot A MANO sobre la línea (los motores quedan
// apagados); termina con CAL o al agotar el tiempo; se guarda en la flash si todos los sensores vieron blanco y negro.
#include <math.h>
#include <stdint.h>
#include <string.h>

#include "../../config_maestra.h"
#include "../../logica/estados.h"
#include "../../logica/parametros.h"
#include "../../logica/posicion.h"
#include "../../logica/sf_logica.h"
#include "hw.h"

namespace {

constexpr int N = cfg::N_SENSORES;
constexpr uint32_t MAGIA = 0x43464631u;          // "CFF1"
constexpr uint32_t VERSION = 3;

struct Guardado {                                // lo que se conserva en la flash (múltiplo de 8 bytes)
  uint32_t magia, version;
  float v_max, a_lat, a_lon, k_pp, kp, kd, tau_d, tau_k, piso;
  int32_t fuente;
  int32_t modo_seguro;
  float cal_min[N], cal_max[N];
  uint32_t crc;
};
static_assert(sizeof(Guardado) % 8 == 0, "tamaño de Guardado");

uint32_t crc32(const void* p, uint32_t n) {
  const uint8_t* b = static_cast<const uint8_t*>(p);
  uint32_t c = 0xFFFFFFFFu;
  for (uint32_t i = 0; i < n; ++i) {
    c ^= b[i];
    for (int k = 0; k < 8; ++k) c = (c >> 1) ^ (0xEDB88320u & (0u - (c & 1u)));
  }
  return ~c;
}

sf::Robot robot() {
  sf::Robot r;
  r.motor = sf::Motor{cfg::MOTOR_V_NOM, cfg::MOTOR_RPM, cfg::MOTOR_PAR_BLOQUEO, cfg::MOTOR_I_BLOQUEO, cfg::MOTOR_I_VACIO};
  r.diam = cfg::D_LLANTA; r.W = cfg::W_VIA; r.masa = cfg::MASA; r.L = cfg::L_CUELLO;
  r.n_sens = N; r.v_max_motor = cfg::MOTOR_LIMITE_V;
  return r;
}

sf::ParamSF parametros(bool seguro) {
  sf::ParamSF p;
  if (!seguro) {
    p.v_max = cfg::V_MAX; p.a_lat = cfg::A_LAT; p.a_lon = cfg::A_LON; p.k_pp = cfg::K_PP; p.kp = cfg::KP; p.kd = cfg::KD;
    p.tau_d = cfg::TAU_D; p.tau_k = cfg::TAU_K; p.piso = cfg::PISO; p.fuente_k = cfg::FUENTE_CURVATURA;
  } else {
    p.v_max = cfg::SEG_V_MAX; p.a_lat = cfg::SEG_A_LAT; p.a_lon = cfg::SEG_A_LON; p.k_pp = cfg::SEG_K_PP; p.kp = cfg::SEG_KP;
    p.kd = cfg::SEG_KD; p.tau_d = cfg::SEG_TAU_D; p.tau_k = cfg::SEG_TAU_K; p.piso = cfg::SEG_PISO; p.fuente_k = cfg::SEG_FUENTE;
  }
  p.t_perdida = cfg::T_PERDIDA;
  return p;
}

// ------------------------------------------------------------------ estado global
sf::ParamSF prm = parametros(false);
bool modo_seguro = false;
sf::ControlSF control(prm, robot());
posicion::Calibracion cal;
MaquinaEstados maquina;
Boton boton_start, boton_cal;
MonitorBateria bateria(cfg::V_BATERIA_BAJA, cfg::V_BATERIA_CRITICA, 500);
uint16_t raw_apagado[N], raw_encendido[N];
float refl[N], osc[N];
float v_bat = 0.0f;
int32_t enc_l0 = 0, enc_r0 = 0;
float w_l = 0.0f, w_r = 0.0f;
uint32_t t_bloqueo_ms = 0, t_sensores_mal_ms = 0;
bool telemetria = false;
uint32_t prueba_hasta = 0;
float prueba_l = 0.0f, prueba_r = 0.0f;
sf::Salida ultima{0, 0, 0, false, false};
sf::Lectura lectura{0, false, false};

// ------------------------------------------------------------------ formato sin printf
void wr(const char* s) { hw::serie_escribir(s); }
void wr_int(int32_t v) {
  char b[12]; int i = 11; b[i] = 0;
  const bool neg = v < 0;
  uint32_t u = neg ? uint32_t(-v) : uint32_t(v);
  do { b[--i] = char('0' + u % 10); u /= 10; } while (u && i > 1);
  if (neg) b[--i] = '-';
  wr(b + i);
}
void wr_f(float v, int dec = 3) {
  if (v < 0) { wr("-"); v = -v; }
  int32_t ent = int32_t(v);
  wr_int(ent);
  wr(".");
  float fr = v - float(ent);
  for (int k = 0; k < dec; ++k) { fr *= 10.0f; const int d = int(fr); char c[2] = {char('0' + d), 0}; wr(c); fr -= d; }
}

// ------------------------------------------------------------------ memoria
void guardar() {
  Guardado g{};
  g.magia = MAGIA; g.version = VERSION;
  g.v_max = prm.v_max; g.a_lat = prm.a_lat; g.a_lon = prm.a_lon; g.k_pp = prm.k_pp; g.kp = prm.kp; g.kd = prm.kd;
  g.tau_d = prm.tau_d; g.tau_k = prm.tau_k; g.piso = prm.piso; g.fuente = prm.fuente_k; g.modo_seguro = modo_seguro;
  for (int i = 0; i < N; ++i) { g.cal_min[i] = cal.minimo[i]; g.cal_max[i] = cal.maximo[i]; }
  g.crc = crc32(&g, offsetof(Guardado, crc));
  wr(hw::flash_guardar(&g, sizeof(g)) ? "guardado en flash\r\n" : "ERROR al guardar en flash\r\n");
}

void cargar() {
  const Guardado* g = static_cast<const Guardado*>(hw::flash_datos());
  cal.reiniciar(N);
  if (g->magia != MAGIA || g->version != VERSION || g->crc != crc32(g, offsetof(Guardado, crc))) {
    wr("flash sin datos validos: parametros del YAML, sin calibracion\r\n");
    return;
  }
  prm.v_max = g->v_max; prm.a_lat = g->a_lat; prm.a_lon = g->a_lon; prm.k_pp = g->k_pp; prm.kp = g->kp; prm.kd = g->kd;
  prm.tau_d = g->tau_d; prm.tau_k = g->tau_k; prm.piso = g->piso; prm.fuente_k = g->fuente; modo_seguro = g->modo_seguro;
  for (int i = 0; i < N; ++i) { cal.minimo[i] = g->cal_min[i]; cal.maximo[i] = g->cal_max[i]; }
  control.fijar(prm);
  wr("parametros y calibracion cargados de la flash\r\n");
}

// ------------------------------------------------------------------ consola
char linea[64];
int n_linea = 0;

void imprimir_parametros() {
  wr(modo_seguro ? "modo SEGURO" : "modo COMPETENCIA");
  wr("  v_max "); wr_f(prm.v_max); wr("  a_lat "); wr_f(prm.a_lat); wr("  a_lon "); wr_f(prm.a_lon);
  wr("  k_pp "); wr_f(prm.k_pp); wr("  kp "); wr_f(prm.kp); wr("  kd "); wr_f(prm.kd);
  wr("  tau_k "); wr_f(prm.tau_k, 4); wr("  piso "); wr_f(prm.piso); wr("  fuente "); wr_int(prm.fuente_k);
  wr("\r\nyaml "); wr(cfg::HUELLA_YAML); wr("  motor "); wr(cfg::MOTOR); wr("\r\n");
}

bool comando_motor_permitido() {
  const Estado e = maquina.estado();
  return e == Estado::ESPERA || e == Estado::LISTO || e == Estado::PARADA;
}

void ejecutar(char* c) {
  if (!strcmp(c, "?") || !strcmp(c, "ayuda")) {
    wr("t telemetria | r lecturas | p parametros | set <v_max|a_lat|a_lon|k_pp|kp|kd|tau_k|piso|fuente> <valor>\r\n"
       "modo comp|seguro | w guardar | defecto | prueba <izq> <der> (2 s, ruedas en el aire) | c calibrar\r\n");
  } else if (!strcmp(c, "t")) {
    telemetria = !telemetria;
  } else if (!strcmp(c, "r")) {
    for (int i = 0; i < N; ++i) { wr("S"); wr_int(i + 1); wr(" amb "); wr_int(raw_apagado[i]); wr(" emi "); wr_int(raw_encendido[i]);
      wr(" cal "); wr_f(cal.minimo[i], 0); wr("-"); wr_f(cal.maximo[i], 0); wr(" osc "); wr_f(osc[i], 2); wr("\r\n"); }
    wr("vbat "); wr_f(v_bat, 2); wr(" enc "); wr_int(hw::encoder_izq()); wr(" "); wr_int(hw::encoder_der()); wr("\r\n");
  } else if (!strcmp(c, "p")) {
    imprimir_parametros();
  } else if (!strncmp(c, "set ", 4)) {
    char* nombre = c + 4;
    char* val = strchr(nombre, ' ');
    if (!val) { wr("uso: set nombre valor\r\n"); return; }
    *val++ = 0;
    float v = 0, s = 1, esc = 0;
    if (*val == '-') { s = -1; ++val; }
    for (; *val; ++val) {
      if (*val == '.') { esc = 1; continue; }
      if (*val < '0' || *val > '9') break;
      if (esc > 0) { esc *= 10; v += (*val - '0') / esc; } else v = v * 10 + (*val - '0');
    }
    v *= s;
    if (!strcmp(nombre, "v_max")) prm.v_max = v;
    else if (!strcmp(nombre, "a_lat")) prm.a_lat = v;
    else if (!strcmp(nombre, "a_lon")) prm.a_lon = v;
    else if (!strcmp(nombre, "k_pp")) prm.k_pp = v;
    else if (!strcmp(nombre, "kp")) prm.kp = v;
    else if (!strcmp(nombre, "kd")) prm.kd = v;
    else if (!strcmp(nombre, "tau_k")) prm.tau_k = v;
    else if (!strcmp(nombre, "piso")) prm.piso = v;
    else if (!strcmp(nombre, "fuente")) prm.fuente_k = int(v);
    else { wr("parametro desconocido\r\n"); return; }
    control.fijar(prm);
    imprimir_parametros();
  } else if (!strcmp(c, "modo comp") || !strcmp(c, "modo seguro")) {
    modo_seguro = !strcmp(c, "modo seguro");
    prm = parametros(modo_seguro);
    control.fijar(prm);
    imprimir_parametros();
  } else if (!strcmp(c, "defecto")) {
    modo_seguro = false; prm = parametros(false); control.fijar(prm); imprimir_parametros();
  } else if (!strcmp(c, "w")) {
    if (comando_motor_permitido()) guardar(); else wr("detener el robot antes de guardar\r\n");
  } else if (!strncmp(c, "prueba ", 7)) {
    if (!comando_motor_permitido()) { wr("solo con el robot detenido\r\n"); return; }
    char* a = c + 7;
    float v[2] = {0, 0};
    for (int k = 0; k < 2 && *a; ++k) {
      while (*a == ' ') ++a;
      float s = 1, x = 0, esc = 0;
      if (*a == '-') { s = -1; ++a; }
      for (; *a && *a != ' '; ++a) { if (*a == '.') { esc = 1; continue; } if (esc > 0) { esc *= 10; x += (*a - '0') / esc; } else x = x * 10 + (*a - '0'); }
      v[k] = s * x;
    }
    prueba_l = fmaxf(-0.5f, fminf(0.5f, v[0])); prueba_r = fmaxf(-0.5f, fminf(0.5f, v[1]));
    prueba_hasta = hw::ms() + 2000;
    wr("prueba de motores 2 s (ciclo limitado a 0.5)\r\n");
  } else if (!strcmp(c, "c")) {
    wr("usar el boton CAL (la calibracion es manual, regla C03)\r\n");
  } else if (*c) {
    wr("? para ayuda\r\n");
  }
}

void consola() {
  int ch;
  while ((ch = hw::serie_leer()) >= 0) {
    if (ch == '\r' || ch == '\n') {
      linea[n_linea] = 0;
      if (n_linea) ejecutar(linea);
      n_linea = 0;
    } else if (n_linea < int(sizeof(linea)) - 1) {
      linea[n_linea++] = char(ch);
    }
  }
}

// ------------------------------------------------------------------ ciclo de control
void ciclo(float dt) {
  const uint32_t ahora = hw::ms();
  // sensores
  hw::leer_sensores(raw_apagado, raw_encendido, &v_bat, cfg::RESTA_AMBIENTE, cfg::T_EMISOR_US);
  const posicion::ModoSensor modo{cfg::RESTA_AMBIENTE, true, par::ADC_MAX};
  int raw_i[N];
  for (int i = 0; i < N; ++i) {
    refl[i] = posicion::reflectancia(modo, raw_encendido[i], raw_apagado[i]);
    raw_i[i] = raw_encendido[i];
  }
  posicion::normalizar(cal, refl, osc);
  lectura = sf::estimar_coord(osc, cfg::SENSOR_Y, N, cfg::UMBRAL);
  bateria.muestra(v_bat, ahora);

  // encoders: velocidad angular de cada rueda (rad/s)
  const int32_t el = hw::encoder_izq(), er = hw::encoder_der();
  const float k = 6.2831853f / cfg::CPR_RUEDA / dt;
  w_l = float(el - enc_l0) * k; w_r = float(er - enc_r0) * k;
  enc_l0 = el; enc_r0 = er;

  // eventos para la máquina de estados
  Eventos ev;
  ev.start = boton_start.actualizar(hw::boton_start(), ahora);
  ev.cal = boton_cal.actualizar(hw::boton_cal(), ahora);
  ev.cal_guardada_ok = cal.lista(cfg::RANGO_CAL_MIN);
  ev.bateria_permite = bateria.permite_arranque();
  ev.bateria_critica = bateria.critica();
  if (maquina.estado() == Estado::CALIBRANDO) {
    cal.muestrear(refl);
    ev.cal_suficiente = cal.lista(cfg::RANGO_CAL_MIN);
    ev.cal_tiempo_agotado = ahora - maquina.desde_ms() > uint32_t(cfg::T_CALIBRACION_MAX * 1000.0f);
  }
  if (maquina.motores_habilitados()) {
    // rueda trabada: ciclo alto sin giro sostenido
    const bool trabada = (fabsf(ultima.izq) > 0.5f && fabsf(w_l) < 1.0f) || (fabsf(ultima.der) > 0.5f && fabsf(w_r) < 1.0f);
    if (!trabada) t_bloqueo_ms = ahora;
    ev.falla_motor = hw::falla_driver() || (ahora - t_bloqueo_ms > uint32_t(cfg::T_BLOQUEO * 1000.0f));
    if (!posicion::lecturas_imposibles(raw_i, N, par::ADC_MAX)) t_sensores_mal_ms = ahora;
    ev.falla_sensores = ahora - t_sensores_mal_ms > 200;
    ev.buscando = !lectura.visible;
  }
  const Estado antes = maquina.estado();
  const bool cambio = maquina.actualizar(ev, ahora);
  if (cambio && maquina.estado() == Estado::CALIBRANDO) cal.reiniciar(N);
  if (cambio && antes == Estado::CALIBRANDO && maquina.estado() == Estado::LISTO) guardar();
  if (maquina.recien_arrancado()) { control.reiniciar(); t_bloqueo_ms = ahora; t_sensores_mal_ms = ahora; }

  // motores
  if (maquina.motores_habilitados()) {
    ultima = control.actualizar(lectura, dt, v_bat, 0.0f, w_l, w_r);
    if (ultima.linea_perdida) {
      Eventos e2; e2.linea_perdida = true;
      maquina.actualizar(e2, ahora);
      hw::motores_apagar();
    } else {
      hw::motores(ultima.izq, ultima.der);
    }
  } else if (prueba_hasta && int32_t(prueba_hasta - ahora) > 0 && comando_motor_permitido()) {
    hw::motores(prueba_l, prueba_r);
  } else {
    prueba_hasta = 0;
    ultima = sf::Salida{0, 0, 0, false, false};
    hw::motores_apagar();
  }

  // indicadores
  const Estado e = maquina.estado();
  const bool parpadeo = (ahora / 150) & 1;
  hw::led_ok(e == Estado::LISTO || e == Estado::SIGUIENDO || e == Estado::RECUPERANDO || (e == Estado::CALIBRANDO && parpadeo));
  hw::led_error(e == Estado::ERROR || (bateria.valida() && !bateria.permite_arranque() && parpadeo) ||
                (e == Estado::PARADA && maquina.motivo() != Motivo::BOTON && parpadeo) ||
                (e == Estado::ESPERA && maquina.motivo() == Motivo::CAL_INSUFICIENTE && parpadeo));
  if (cambio) {
    wr("estado "); wr(nombre_estado(maquina.estado()));
    if (e == Estado::ESPERA && maquina.motivo() == Motivo::CAL_INSUFICIENTE)
      wr(" (calibracion insuficiente: algun sensor no vio blanco y negro; repetir con CAL)");
    wr("\r\n");
  }
}

void telemetria_50hz() {
  static uint32_t t = 0;
  if (!telemetria || hw::ms() - t < 20) return;
  t = hw::ms();
  wr(nombre_estado(maquina.estado())); wr(" e "); wr_f(lectura.e * 1000.0f, 1); wr(" v "); wr_f(ultima.v_cmd, 2);
  wr(" d "); wr_f(ultima.izq, 2); wr(" "); wr_f(ultima.der, 2); wr(" w "); wr_f(w_l, 1); wr(" "); wr_f(w_r, 1);
  wr(" vb "); wr_f(v_bat, 2); wr("\r\n");
}

}  // namespace

int main() {
  hw::iniciar();
  wr("\r\nSpeed Follower Circuit Forge - STM32G431 - yaml "); wr(cfg::HUELLA_YAML); wr("\r\n");
  cargar();
  imprimir_parametros();
  uint32_t t_prev = hw::ciclos();
  while (true) {
    consola();
    telemetria_50hz();
    if (!hw::tick_control()) continue;
    const uint32_t t = hw::ciclos();
    float dt = float(t - t_prev) / float(hw::F_CPU);
    t_prev = t;
    if (dt <= 0.0f || dt > 0.01f) dt = cfg::PERIODO_MIN_US * 1e-6f;
    ciclo(dt);
  }
}
