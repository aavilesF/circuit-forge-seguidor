#include "parametros_v2.h"

#include <string.h>

namespace v2 {

#define P(nombre, mn, mx) {#nombre, offsetof(Parametros, nombre), mn, mx}
static const EntradaParam TABLA[] = {
    P(v_sin, 0.1f, 3.0f), P(v_con, 0.1f, 3.0f), P(a_lat_sin, 1.0f, 20.0f), P(a_lon, 0.5f, 20.0f),
    P(k_pp, 0.0f, 5.0f), P(kp, 0.0f, 500.0f), P(kd, 0.0f, 50.0f), P(tau_d, 0.001f, 0.1f), P(tau_k, 0.001f, 0.5f),
    P(piso, -1.0f, 0.5f), P(fuente_k, 0.0f, 3.0f), P(t_perdida, 0.05f, 1.0f),
    P(usar_mapa, 0.0f, 1.0f), P(a_acc_mapa, 0.5f, 15.0f), P(a_fr_mapa, 0.5f, 20.0f), P(adelanto_mapa, 0.0f, 0.3f),
    P(v_max_mapa, 0.2f, 3.5f),
    P(mando_esc, 0.0f, 1.0f), P(dp_min, 0.0f, 2000.0f),
    P(i_lim, 0.2f, 1.6f), P(t_reduce, 10.0f, 80.0f), P(t_max, 20.0f, 90.0f),
    P(invertir_izq, 0.0f, 1.0f), P(invertir_der, 0.0f, 1.0f), P(enc_izq, -1.0f, 1.0f), P(enc_der, -1.0f, 1.0f),
    P(t_emisor_us, 20.0f, 1000.0f), P(v_bat_baja, 5.0f, 8.4f), P(v_bat_critica, 5.0f, 8.4f),
};
#undef P

const EntradaParam* tabla_parametros(int* n) {
  *n = static_cast<int>(sizeof(TABLA) / sizeof(TABLA[0]));
  return TABLA;
}

float* campo(Parametros& p, const EntradaParam& e) {
  return reinterpret_cast<float*>(reinterpret_cast<uint8_t*>(&p) + e.desplazamiento);
}

bool fijar(Parametros& p, const char* nombre, float valor) {
  int n;
  const EntradaParam* t = tabla_parametros(&n);
  for (int i = 0; i < n; ++i) {
    if (strcmp(t[i].nombre, nombre) != 0) continue;
    if (!(valor >= t[i].min && valor <= t[i].max)) return false;   // también rechaza NaN
    *campo(p, t[i]) = valor;
    return true;
  }
  return false;
}

uint32_t crc32(const void* datos, uint32_t n) {
  const uint8_t* b = static_cast<const uint8_t*>(datos);
  uint32_t c = 0xFFFFFFFFu;
  for (uint32_t i = 0; i < n; ++i) {
    c ^= b[i];
    for (int k = 0; k < 8; ++k) c = (c >> 1) ^ (0xEDB88320u & (0u - (c & 1u)));
  }
  return ~c;
}

void sellar(Guardado& g) {
  g.magia = MAGIA;
  g.version = VERSION_GUARDADO;
  g.crc = crc32(&g, offsetof(Guardado, crc));
}

bool valido(const Guardado& g) {
  return g.magia == MAGIA && g.version == VERSION_GUARDADO && g.crc == crc32(&g, offsetof(Guardado, crc));
}

}  // namespace v2
