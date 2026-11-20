// Robot de emergencia · parámetros ajustables por la consola USB (`set clave valor`) y guardados en la memoria del ESP32
// con versión y CRC32 (idea de V2, parametros_v2). C++ puro.
// [S] = punto de partida (V1 o estimado): se ajusta en la pista. [E] estimado. [C] calculado.
#pragma once
#include <stddef.h>
#include <stdint.h>

#include "control.h"
#include "estados.h"
#include "motor.h"

namespace casero {

struct Ajustes {
  // ---- control de línea (ParamControl de V1). Mando normalizado: 1 = ciclo máximo permitido
  // [S] de la simulación en lazo cerrado del robot casero (pruebas/test_casero.cpp, -DBARRIDO): kp 0.008–0.014 da
  // ≤ 10 mm de desvío de la barra en curvas de 200–600 mm hasta vbase 0.7; los valores de V1 (kp 0.04, kd 0.002)
  // OSCILAN con este motor y estas ruedas. Se afinan en la pista.
  float kp = 0.010f, ki = 0.0f, kd = 0.0004f;
  float vbase = 0.35f;                         // [S] primera vuelta prudente (~0.45 m/s con N20 de 1000 rpm y rueda de 28 mm)
  float freno = 0.30f, error_ref = 30.0f, vmin_rel = 0.50f, u_max = 0.60f, rueda_min = -0.30f;
  float tau_d = 0.010f, t_ret = 0.060f, t_busq = 1.5f, u_busq = 0.35f, v_busq = 0.40f;
  // ---- motores y DRV8833
  float pwm_max = 0.90f;       // tope de ciclo (el DRV8833 es más débil que el DRV8874)
  float v_motor_max = 6.0f;    // V sobre el N20 de 6 V
  float i_max = 1.2f;          // A por motor (DRV8833: 1.5 A RMS) [V/C]
  float i_total = 2.0f;        // A entre los dos (MP1584 #2) [E]
  float rampa = 6.0f;          // 1/s
  float m_R = 6.0f, m_ke = 0.0533f, m_tau = 0.08f;   // modelo del N20 [E]: medir corriente de bloqueo
  float vm_fijo = 6.0f;        // V a la salida del MP1584 U2 (+6V_MOT); el DRV8833 nunca va a la batería directa
  float inv_izq = 0.0f, inv_der = 1.0f;   // motores espejados [P: verificar con `m 0.3 0` y `m 0 0.3`]
  float lento = 1.0f;          // 1 = decaimiento lento (freno entre pulsos; más lineal), 0 = rápido
  // ---- sensores
  float alfa = 0.6f;           // pasa-bajas (1 = sin filtro)
  float sobremuestreo = 1.0f;  // lecturas del ADC promediadas por canal y ciclo (1..4)
  float t_emisor_us = 150.0f;  // espera tras prender/apagar los LED IR [S]
  // ---- batería (2S). El divisor mide VBAT_SW directo (sin diodo). Umbrales [E]: falta definirlos con Alan (GUIA 7.6)
  float bat_baja = 6.8f, bat_critica = 6.4f;
  // ---- calibración
  float t_cal_max = 15.0f, t_cal_extra = 1.0f;   // s
};

struct EntradaAjuste { const char* nombre; size_t desp; float min, max; };
const EntradaAjuste* tabla_ajustes(int* n);
float* campo(Ajustes& a, const EntradaAjuste& e);
bool fijar(Ajustes& a, const char* nombre, float valor);   // false si no existe o está fuera de rango

ParamControl a_control(const Ajustes& a);
motor::Modelo a_modelo(const Ajustes& a);
motor::Limites a_limites(const Ajustes& a);
Tiempos a_tiempos(const Ajustes& a);

// Imagen guardada en la memoria no volátil (Preferences del ESP32)
constexpr int MAX_CAL = 16;
struct Guardado {
  uint32_t magia, version;
  Ajustes a;
  int32_t n_cal;
  float cal_min[MAX_CAL], cal_max[MAX_CAL];
  uint32_t crc;
};
constexpr uint32_t MAGIA = 0x454D4552u;   // "EMER": no carga datos del firmware histórico
constexpr uint32_t VERSION = 1;
uint32_t crc32(const void* datos, size_t n);
void sellar(Guardado& g);                 // pone magia, versión y CRC
bool valido(const Guardado& g);

}  // namespace casero
