#include "ajustes.h"

#include <string.h>

namespace casero {

#define E(campo_, mn, mx) {#campo_, offsetof(Ajustes, campo_), mn, mx}
static const EntradaAjuste TABLA[] = {
    E(kp, 0.0f, 1.0f), E(ki, 0.0f, 5.0f), E(kd, 0.0f, 0.1f), E(vbase, 0.0f, 1.0f),
    E(freno, 0.0f, 1.0f), E(error_ref, 1.0f, 100.0f), E(vmin_rel, 0.0f, 1.0f), E(u_max, 0.05f, 2.0f),
    E(rueda_min, -1.0f, 0.5f), E(tau_d, 0.0f, 0.2f), E(t_ret, 0.0f, 0.5f), E(t_busq, 0.0f, 5.0f),
    E(u_busq, 0.0f, 1.0f), E(v_busq, 0.0f, 1.0f),
    E(pwm_max, 0.1f, 1.0f), E(v_motor_max, 1.0f, 9.0f), E(i_max, 0.1f, 1.5f), E(i_total, 0.2f, 3.0f),
    E(rampa, 0.5f, 100.0f), E(m_R, 0.5f, 50.0f), E(m_ke, 0.005f, 0.5f), E(m_tau, 0.005f, 1.0f),
    E(vm_fijo, 2.7f, 10.8f), E(vm_bateria, 0.0f, 1.0f), E(inv_izq, 0.0f, 1.0f), E(inv_der, 0.0f, 1.0f),
    E(lento, 0.0f, 1.0f), E(alfa, 0.05f, 1.0f), E(sobremuestreo, 1.0f, 4.0f), E(t_emisor_us, 20.0f, 1000.0f),
    E(bat_baja, 5.0f, 9.0f), E(bat_critica, 5.0f, 9.0f), E(caida_d1, 0.0f, 1.0f),
    E(t_cal_max, 2.0f, 15.0f), E(t_cal_extra, 0.0f, 5.0f), E(usar_nfault, 0.0f, 1.0f), E(zumb_activo, 0.0f, 1.0f),
};
#undef E

const EntradaAjuste* tabla_ajustes(int* n) {
  *n = static_cast<int>(sizeof(TABLA) / sizeof(TABLA[0]));
  return TABLA;
}

float* campo(Ajustes& a, const EntradaAjuste& e) {
  return reinterpret_cast<float*>(reinterpret_cast<char*>(&a) + e.desp);
}

bool fijar(Ajustes& a, const char* nombre, float v) {
  int n;
  const EntradaAjuste* t = tabla_ajustes(&n);
  for (int i = 0; i < n; ++i) {
    if (strcmp(t[i].nombre, nombre) == 0) {
      if (!(v >= t[i].min && v <= t[i].max)) return false;   // también rechaza NaN
      *campo(a, t[i]) = v;
      return true;
    }
  }
  return false;
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
  l.pwm_max = a.pwm_max; l.v_motor_max = a.v_motor_max; l.i_max = a.i_max; l.i_total = a.i_total; l.rampa = a.rampa;
  return l;
}

Tiempos a_tiempos(const Ajustes& a) {
  Tiempos t;
  t.cal_max_ms = static_cast<uint32_t>(a.t_cal_max * 1000.0f + 0.5f);
  t.cal_extra_ms = static_cast<uint32_t>(a.t_cal_extra * 1000.0f + 0.5f);
  return t;
}

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
         g.n_cal >= 0 && g.n_cal <= MAX_CAL;
}

}  // namespace casero
