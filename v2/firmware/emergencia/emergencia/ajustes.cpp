#include "ajustes.h"

#include <string.h>

namespace robot {

#define E(campo_, mn, mx, txt) {#campo_, offsetof(Ajustes, campo_), mn, mx, txt}
static const EntradaAjuste TABLA[] = {
    // control
    E(kp, 0.0f, 1.0f, "PID: proporcional (por mm)"), E(ki, 0.0f, 5.0f, "PID: integral"),
    E(kd, 0.0f, 0.1f, "PID: derivada"), E(vbase, 0.0f, 1.0f, "velocidad base (fraccion del maximo)"),
    E(freno, 0.0f, 1.0f, "fraccion de vbase que se quita en curva"), E(error_ref, 1.0f, 100.0f, "mm con freno de curva completo"),
    E(vmin_rel, 0.0f, 1.0f, "piso de velocidad en curva"), E(u_max, 0.05f, 2.0f, "saturacion de la correccion"),
    E(rueda_min, -1.0f, 0.5f, "minimo por rueda (negativo = reversa)"), E(tau_d, 0.0f, 0.2f, "s, filtro de la derivada"),
    E(t_ret, 0.0f, 0.5f, "s, retencion en huecos"), E(t_busq, 0.0f, 5.0f, "s, busqueda antes de parar"),
    E(u_busq, 0.0f, 1.0f, "giro durante la busqueda"), E(v_busq, 0.0f, 1.0f, "velocidad relativa en la busqueda"),
    // motores
    E(pwm_max, 0.1f, 1.0f, "tope de ciclo PWM"), E(v_motor_max, 1.0f, 9.0f, "V maximos sobre el motor"),
    E(i_max, 0.1f, 1.5f, "A estimados por motor"), E(i_total, 0.2f, 3.0f, "A estimados entre los dos"),
    E(rampa, 0.5f, 100.0f, "1/s al acelerar"), E(rampa_freno, 0.5f, 100.0f, "1/s al frenar o invertir"),
    E(m_R, 0.5f, 50.0f, "ohm del N20 (6 V / I bloqueo)"), E(m_ke, 0.005f, 0.5f, "V*s/rad del N20"),
    E(m_tau, 0.005f, 1.0f, "s, constante de velocidad estimada"), E(vm_fijo, 2.7f, 10.8f, "V del MP1584 de motores"),
    E(caida_reg, 0.0f, 2.0f, "V de caida del MP1584 de motores"), E(inv_izq, 0.0f, 1.0f, "1 = invierte motor izquierdo"),
    E(inv_der, 0.0f, 1.0f, "1 = invierte motor derecho"), E(cruzar, 0.0f, 1.0f, "1 = intercambia motores izq/der"),
    E(lento, 0.0f, 1.0f, "1 = decaimiento lento, 0 = rapido"),
    // sensores
    E(inv_sens, 0.0f, 1.0f, "1 = SEN1 a la derecha"), E(mascara, 1.0f, (float)MASCARA_TODOS, "bits de sensores en uso (63 = los 6)"),
    E(paso_mm, 5.0f, 30.0f, "mm entre sensores"), E(alfa, 0.05f, 1.0f, "pasa-bajas (1 = sin filtro)"),
    E(sobremuestreo, 1.0f, 4.0f, "lecturas ADC promediadas"), E(descartes, 0.0f, 3.0f, "lecturas tiradas al cambiar canal"),
    E(t_emisor_us, 20.0f, 1000.0f, "us tras prender/apagar los LED IR"), E(t_mux_us, 1.0f, 100.0f, "us tras cambiar el canal"),
    E(umbral, 0.0f, 0.5f, "oscuridad ignorada"), E(confianza, 0.05f, 4.0f, "suma minima para ver la linea"),
    E(contraste, 20.0f, 3000.0f, "cuentas minimas blanco-negro"), E(t_negro, 0.0f, 3.0f, "s todo negro antes de parar (0 = no)"),
    // batería
    E(bat_baja, 5.0f, 9.0f, "V de aviso"), E(bat_critica, 5.0f, 9.0f, "V de parada"),
    // calibración y arranque
    E(t_cal_max, 2.0f, 15.0f, "s maximos de calibracion"), E(t_cal_extra, 0.0f, 5.0f, "s extra tras ver contraste"),
    E(ac_u, 0.05f, 0.6f, "giro de autocal"), E(ac_t, 0.3f, 5.0f, "s maximos por fase de autocal"),
    E(t_arranque, 0.0f, 5.0f, "s entre START y arrancar"),
};
#undef E

const EntradaAjuste* tabla_ajustes(int* n) {
  *n = static_cast<int>(sizeof(TABLA) / sizeof(TABLA[0]));
  return TABLA;
}

float* campo(Ajustes& a, const EntradaAjuste& e) {
  return reinterpret_cast<float*>(reinterpret_cast<char*>(&a) + e.desp);
}

const EntradaAjuste* buscar(const char* nombre) {
  int n;
  const EntradaAjuste* t = tabla_ajustes(&n);
  for (int i = 0; i < n; ++i) if (strcmp(t[i].nombre, nombre) == 0) return &t[i];
  return nullptr;
}

static bool es_bit(float v) { return v == 0.0f || v == 1.0f; }

bool coherente(const Ajustes& a, const char** motivo) {
  const char* m = nullptr;
  if (!(a.bat_critica < a.bat_baja)) m = "bat_critica debe ser menor que bat_baja";
  else if (!es_bit(a.inv_izq) || !es_bit(a.inv_der) || !es_bit(a.cruzar) || !es_bit(a.lento) || !es_bit(a.inv_sens))
    m = "inv_izq, inv_der, cruzar, lento e inv_sens solo valen 0 o 1";
  else if (a.mascara != static_cast<float>(static_cast<int>(a.mascara))) m = "mascara debe ser entera (1..63)";
  else if (a.sobremuestreo != static_cast<float>(static_cast<int>(a.sobremuestreo)) ||
           a.descartes != static_cast<float>(static_cast<int>(a.descartes)))
    m = "sobremuestreo y descartes deben ser enteros";
  else if (a.rueda_min > a.vbase) m = "rueda_min no puede pasar de vbase";
  if (motivo) *motivo = m;
  return m == nullptr;
}

bool fijar(Ajustes& a, const char* nombre, float v) {
  const EntradaAjuste* e = buscar(nombre);
  if (!e) return false;
  if (!(v >= e->min && v <= e->max)) return false;   // también rechaza NaN
  Ajustes prueba = a;
  *campo(prueba, *e) = v;
  if (!coherente(prueba, nullptr)) return false;
  a = prueba;
  return true;
}

// Perfiles [S]: simulación en lazo cerrado (curvas de 200–600 mm con 8 sensores; pista recta → R150 → R200 con 6
// sensores en pruebas/modelo_pista.py; paso 12.7 mm, N20 de 1000 rpm [E]).
// El robot real puede necesitar otros valores: se parte de aquí y se ajusta con `set`.
// v_recta [S] (turbo, v2.1): elegido con pruebas/modelo_pista.py (pista recta → R150 → recta → R200, 5 semillas de
// ruido): normal 0.42 = vuelta −7 % con el mismo desvío; rápido 0.55 = −3 % y +0.5 mm (0.60 ya sube 1.3 mm y 0.65
// satura ruedas). seguro: desactivado.
struct Perfil { const char* nombre; float vbase, pwm_max, rampa, rampa_freno, kp, kd, freno, v_recta; };
static const Perfil PERFILES[] = {
    {"seguro", 0.25f, 0.80f, 4.0f, 8.0f, 0.010f, 0.0004f, 0.30f, 0.0f},
    {"normal", 0.35f, 0.90f, 6.0f, 12.0f, 0.010f, 0.0004f, 0.30f, 0.42f},
    {"rapido", 0.50f, 1.00f, 8.0f, 16.0f, 0.012f, 0.0006f, 0.40f, 0.55f},
};

bool aplicar_perfil(Ajustes& a, const char* nombre) {
  for (const Perfil& p : PERFILES) {
    if (strcmp(p.nombre, nombre) != 0) continue;
    a.vbase = p.vbase; a.pwm_max = p.pwm_max; a.rampa = p.rampa; a.rampa_freno = p.rampa_freno;
    a.kp = p.kp; a.kd = p.kd; a.freno = p.freno;
    if (a.rueda_min > a.vbase) a.rueda_min = -0.30f;
    return true;
  }
  return false;
}

bool aplicar_perfil(Ajustes& a, Turbo& t, const char* nombre) {
  if (!aplicar_perfil(a, nombre)) return false;
  for (const Perfil& p : PERFILES)
    if (strcmp(p.nombre, nombre) == 0) t.v_recta = p.v_recta;
  return true;
}

ParamControl a_control(const Ajustes& a) {
  ParamControl p;
  p.kp = a.kp; p.ki = a.ki; p.kd = a.kd; p.vbase = a.vbase;
  p.freno_error = a.freno; p.error_ref_mm = a.error_ref; p.vmin_rel = a.vmin_rel; p.u_max = a.u_max;
  p.rueda_min = a.rueda_min; p.tau_d_s = a.tau_d; p.t_retencion_s = a.t_ret; p.t_busqueda_s = a.t_busq;
  p.u_busqueda = a.u_busq; p.vbusqueda_rel = a.v_busq;
  return p;
}

motor::Modelo a_modelo(const Ajustes& a) {
  motor::Modelo m;
  m.R = a.m_R; m.ke = a.m_ke; m.tau = a.m_tau;
  return m;
}

motor::Limites a_limites(const Ajustes& a) {
  motor::Limites l;
  l.pwm_max = a.pwm_max; l.v_motor_max = a.v_motor_max; l.i_max = a.i_max; l.i_total = a.i_total;
  l.rampa = a.rampa; l.rampa_freno = a.rampa_freno;
  return l;
}

Tiempos a_tiempos(const Ajustes& a) {
  Tiempos t;
  t.cal_max_ms = static_cast<uint32_t>(a.t_cal_max * 1000.0f + 0.5f);
  t.cal_extra_ms = static_cast<uint32_t>(a.t_cal_extra * 1000.0f + 0.5f);
  t.arranque_ms = static_cast<uint32_t>(a.t_arranque * 1000.0f + 0.5f);
  return t;
}

ParamControl a_control(const Ajustes& a, const Turbo& t) {
  ParamControl p = a_control(a);
  p.v_recta = t.v_recta;
  p.recta_e_in = t.recta_e_in;
  p.recta_e_out = t.recta_e_out;
  p.t_confirmar_s = t.recta_t_conf;
  p.t_acel_s = t.recta_t_acel;
  return p;
}

uint32_t mascara(const Ajustes& a) { return static_cast<uint32_t>(a.mascara) & MASCARA_TODOS; }

uint32_t crc32(const void* datos, size_t n) {
  const uint8_t* p = static_cast<const uint8_t*>(datos);
  uint32_t c = 0xFFFFFFFFu;
  for (size_t i = 0; i < n; ++i) {
    c ^= p[i];
    for (int k = 0; k < 8; ++k) c = (c >> 1) ^ (0xEDB88320u & (0u - (c & 1u)));
  }
  return ~c;
}

void sellar(Guardado& g) {
  g.magia = MAGIA;
  g.version = VERSION;
  g.crc = crc32(&g, offsetof(Guardado, crc));
}

bool valido(const Guardado& g) {
  return g.magia == MAGIA && g.version == VERSION && g.crc == crc32(&g, offsetof(Guardado, crc)) &&
         g.n_cal >= 0 && g.n_cal <= MAX_CAL && coherente(g.a, nullptr);
}

bool adaptar_a_sensores(Guardado& g, int n) {
  const uint32_t todos = (n >= 32) ? 0xFFFFFFFFu : ((1u << n) - 1u);
  bool cambio = false;
  if (g.n_cal != n) {                       // calibración de otra barra: no se reutiliza
    g.n_cal = 0;
    for (int i = 0; i < MAX_CAL; ++i) g.cal_min[i] = g.cal_max[i] = 0.0f;
    g.a.mascara = static_cast<float>(todos);
    cambio = true;
  }
  const uint32_t m = static_cast<uint32_t>(g.a.mascara);
  if ((m & ~todos) != 0u || (m & todos) == 0u) {   // bits de sensores que ya no existen, o ninguno activo
    g.a.mascara = static_cast<float>((m & todos) ? (m & todos) : todos);
    cambio = true;
  }
  return cambio;
}

// ---- turbo
#define T(campo_, mn, mx, txt) {#campo_, offsetof(Turbo, campo_), mn, mx, txt}
static const EntradaAjuste TABLA_TURBO[] = {
    T(v_recta, 0.0f, 1.0f, "turbo: velocidad en recta (<= vbase = apagado)"),
    T(recta_e_in, 0.5f, 10.0f, "turbo: mm de error para entrar"),
    T(recta_e_out, 1.0f, 20.0f, "turbo: mm de error que lo cancela"),
    T(recta_t_conf, 0.0f, 2.0f, "turbo: s de recta limpia antes de acelerar"),
    T(recta_t_acel, 0.05f, 5.0f, "turbo: s para llegar a v_recta"),
};
#undef T

const EntradaAjuste* tabla_turbo(int* n) {
  *n = static_cast<int>(sizeof(TABLA_TURBO) / sizeof(TABLA_TURBO[0]));
  return TABLA_TURBO;
}

float* campo(Turbo& t, const EntradaAjuste& e) {
  return reinterpret_cast<float*>(reinterpret_cast<char*>(&t) + e.desp);
}

const EntradaAjuste* buscar_turbo(const char* nombre) {
  int n;
  const EntradaAjuste* t = tabla_turbo(&n);
  for (int i = 0; i < n; ++i) if (strcmp(t[i].nombre, nombre) == 0) return &t[i];
  return nullptr;
}

bool coherente(const Turbo& t, const char** motivo) {
  const char* m = nullptr;
  if (!(t.recta_e_in < t.recta_e_out)) m = "recta_e_in debe ser menor que recta_e_out (histeresis)";
  if (motivo) *motivo = m;
  return m == nullptr;
}

bool fijar(Turbo& t, const char* nombre, float v) {
  const EntradaAjuste* e = buscar_turbo(nombre);
  if (!e || !(v >= e->min && v <= e->max)) return false;
  Turbo prueba = t;
  *campo(prueba, *e) = v;
  if (!coherente(prueba, nullptr)) return false;
  t = prueba;
  return true;
}

void sellar(GuardadoTurbo& g) {
  g.magia = MAGIA_TURBO;
  g.version = VERSION_TURBO;
  g.crc = crc32(&g, offsetof(GuardadoTurbo, crc));
}

bool valido(const GuardadoTurbo& g) {
  if (g.magia != MAGIA_TURBO || g.version != VERSION_TURBO || g.crc != crc32(&g, offsetof(GuardadoTurbo, crc)))
    return false;
  int n;
  const EntradaAjuste* tb = tabla_turbo(&n);
  Turbo t = g.t;
  for (int i = 0; i < n; ++i) {
    const float v = *campo(t, tb[i]);
    if (!(v >= tb[i].min && v <= tb[i].max)) return false;
  }
  return coherente(g.t, nullptr);
}

}  // namespace robot
