// V2 · Parámetros ajustables (consola USB) y su guardado. C++17 puro.
// Los valores por defecto salen de config_v2.h (generado del diseño) y de las fases 1-3.5; los de control son el
// punto de partida de V1 escalado al motor de V2 [S] y se ajustan en la pista (consola `set`).
#pragma once
#include <stddef.h>
#include <stdint.h>

#include "../config_v2.h"

namespace v2 {

struct Parametros {
  // ---- control (sf::ParamSF de V1)
  float v_sin = 1.18f;        // m/s crucero reactivo sin succión (T12, referencia) [C]
  float v_con = 1.31f;        // m/s crucero reactivo con succión confirmada (T12, faldón de 2 mm) [C]
  float a_lat_sin = cfg2::FACTOR_PLAN * cfg2::MU_REF * 9.81f;   // m/s² en curva sin succión [C]
  float a_lon = 4.0f;         // m/s² rampa de velocidad del controlador reactivo [S]
  // Ganancias de V1 (C3m, config_maestra.h) × 0.83: velocidad por unidad de ciclo a 7.4 V = 3.62 m/s en V1 y 4.34 m/s
  // en V2 [C]; mismo controlador (sf::ControlSF). Punto de partida [S]: se ajustan en la pista.
  float k_pp = 0.29f, kp = 68.0f, kd = 4.7f;
  float tau_d = 0.004f, tau_k = 0.073f, piso = -0.11f;
  float fuente_k = 2.0f;      // 2 = C3g (giroscopio); 3 = C3e (encoders) si el IMU falla
  float t_perdida = 0.3f;     // s de búsqueda antes de parar (C07)
  // ---- mapa
  float usar_mapa = 1.0f;     // 0 = siempre reactivo
  float a_acc_mapa = 8.0f;    // m/s² del perfil (≤ 10.5 de T10) [S]
  float a_fr_mapa = 6.0f;     // m/s² de frenado del perfil sin succión (≤ μ·g·factor) [S]
  float adelanto_mapa = 0.06f;// s de anticipación del perfil (retardo del lazo) [S]
  float v_max_mapa = 2.0f;    // m/s tope en recta con mapa (meta V2)
  // ---- succión
  float mando_esc = 0.70f;    // 0..1 [S: ajustar con la prueba de báscula]
  float dp_min = 150.0f;      // Pa
  // ---- motores
  float i_lim = cfg2::I_LIMITE_FIRMWARE;   // A
  float t_reduce = 40.0f, t_max = cfg2::MOTOR_DT_MAX;    // K (FASE35 §3)
  float invertir_izq = 0.0f, invertir_der = 1.0f;        // montaje espejado [S: verificar con `prueba`]
  float enc_izq = 1.0f, enc_der = -1.0f;                 // signo de cada encoder [S: verificar]
  // ---- sensores
  float t_emisor_us = 200.0f; // µs de espera con los emisores encendidos (como V1) [S]
  float v_bat_baja = 6.8f, v_bat_critica = 6.4f;         // V (V1; 2S bajo carga) [S]
};

struct EntradaParam { const char* nombre; size_t desplazamiento; float min, max; };
// Tabla para la consola: nombre, posición dentro de Parametros y rango aceptado.
const EntradaParam* tabla_parametros(int* n);
float* campo(Parametros& p, const EntradaParam& e);
bool fijar(Parametros& p, const char* nombre, float valor);      // false si no existe o está fuera de rango

// Imagen en flash: parámetros + calibración + cero de presión + sesgo del giroscopio, con CRC32.
struct Guardado {
  uint32_t magia, version;
  Parametros p;
  float cal_min[cfg2::N_SENSORES], cal_max[cfg2::N_SENSORES];
  float cero_presion, sesgo_giro;
  uint32_t reservado;
  uint32_t crc;
};
constexpr uint32_t MAGIA = 0x43463256u;      // "CF2V"
constexpr uint32_t VERSION_GUARDADO = 1;
uint32_t crc32(const void* datos, uint32_t n);
void sellar(Guardado& g);                   // magia, versión y CRC
bool valido(const Guardado& g);

}  // namespace v2
