// Robot de emergencia · parámetros ajustables por la consola USB (`set clave valor`) y guardados en la memoria del
// ESP32 (`save`) con versión y CRC32. C++ puro. Todo lo que depende del montaje real está aquí, con un valor inicial
// SEGURO: mañana solo se corrigen inversiones, se calibra y se sube la velocidad, sin recompilar.
// Marcas: [S] punto de partida de la simulación (pruebas/test_emergencia.cpp, -DBARRIDO): se afina en la pista ·
// [E] estimado · [C] calculado · [P] pendiente de medir en el robot.
#pragma once
#include <stddef.h>
#include <stdint.h>

#include "config.h"
#include "control.h"
#include "estados.h"
#include "motor.h"

namespace robot {

struct Ajustes {
  // ---- control de línea. Mando normalizado: 1 = ciclo máximo permitido. Error en mm (+ = línea a la derecha).
  float kp = 0.010f, ki = 0.0f, kd = 0.0004f;   // [S]
  float vbase = 0.25f;         // perfil SEGURO para la primera vuelta (`perfil normal` / `perfil rapido` la suben)
  float freno = 0.30f;         // fracción de vbase que se quita en curva (error ≥ error_ref)
  float error_ref = 30.0f;     // mm de error con el que se aplica todo el freno de curva
  float vmin_rel = 0.50f;      // piso de la velocidad relativa en curva
  float u_max = 0.60f;         // saturación de la corrección del PID
  float rueda_min = -0.30f;    // velocidad mínima de una rueda (negativa = puede girar hacia atrás en curva cerrada)
  float tau_d = 0.010f;        // s, filtro de la derivada
  float t_ret = 0.060f;        // s, retención en huecos (sigue con la última orden)
  float t_busq = 1.5f;         // s, búsqueda girando al último lado visto; después se para (línea perdida)
  float u_busq = 0.35f, v_busq = 0.40f;   // giro y velocidad relativa durante la búsqueda
  // ---- motores y DRV8833
  float pwm_max = 0.80f;       // tope de ciclo (perfil seguro; hasta 1.0)
  float v_motor_max = 6.0f;    // V efectivos máximos sobre el N20 de 6 V
  float i_max = 1.2f;          // A por motor (DRV8833: 1.5 A RMS) [V/C]
  float i_total = 2.0f;        // A entre los dos (MP1584 U2) [E]
  float rampa = 4.0f;          // 1/s al acelerar (0 → 100 % en 250 ms)
  float rampa_freno = 8.0f;    // 1/s al frenar o invertir
  float m_R = 6.0f, m_ke = 0.0533f, m_tau = 0.08f;   // modelo del N20 [E]: medir corriente de bloqueo (R = 6 V / I)
  float vm_fijo = 6.0f;        // V a la salida del MP1584 U2 (+6V_MOT) [P: ajustarlo con multímetro, EM-04]
  float caida_reg = 0.6f;      // V que pierde el MP1584 U2 cuando la batería baja de ~6.6 V [E]
  float inv_izq = MOTOR_IZQ_INVERTIDO, inv_der = MOTOR_DER_INVERTIDO;   // [P] sentido de cada motor
  float cruzar = MOTORES_CRUZADOS;   // 1 = intercambia izquierda y derecha (motor de AIN montado a la derecha)
  float lento = 1.0f;          // 1 = decaimiento lento (freno entre pulsos; más lineal), 0 = rápido
  // ---- sensores
  float inv_sens = SENSORES_INVERTIDOS;   // 1 = SEN1 está a la DERECHA [P]
  float mascara = 255.0f;      // bits de sensores en uso (1 = izquierda … 128 = derecha); ej. 239 ignora el 5.º
  float paso_mm = PASO_SENSORES_MM;       // separación entre sensores [P]
  float alfa = 0.6f;           // pasa-bajas (1 = sin filtro)
  float sobremuestreo = 2.0f;  // lecturas del ADC promediadas por canal y ciclo (1..4)
  float descartes = 1.0f;      // lecturas tiradas tras cambiar de canal (carga del ADC del canal anterior)
  float t_emisor_us = 150.0f;  // espera tras prender/apagar los LED IR [S]
  float t_mux_us = MUX_ASENTAMIENTO_US;   // espera tras cambiar el canal del mux
  float umbral = 0.10f;        // oscuridad menor a esto se ignora al calcular la posición
  float confianza = 0.30f;     // suma mínima de oscuridad para "ver" la línea
  float contraste = 150.0f;    // cuentas: contraste mínimo blanco-negro de cada sensor para aceptar la calibración
  float t_negro = 0.50f;       // s con TODOS los sensores negros (robot levantado) antes de parar; 0 = no se revisa
  // ---- batería 2S. El divisor mide VBAT_SW directo (sin diodo). Umbrales [E]: confirmarlos con Alan
  float bat_baja = 6.8f, bat_critica = 6.4f;
  // ---- calibración y arranque
  float t_cal_max = 15.0f, t_cal_extra = 1.0f;   // s (reglamento: 15 s para calibrar y colocar)
  float ac_u = 0.20f;          // giro de la autocalibración (`autocal`)
  float ac_t = 1.0f;           // s máximos por fase de la autocalibración
  float t_arranque = 0.5f;     // s entre START y el arranque (para retirar la mano); 0 = inmediato
};

struct EntradaAjuste { const char* nombre; size_t desp; float min, max; const char* ayuda; };
const EntradaAjuste* tabla_ajustes(int* n);
float* campo(Ajustes& a, const EntradaAjuste& e);
const EntradaAjuste* buscar(const char* nombre);
bool fijar(Ajustes& a, const char* nombre, float valor);   // false si no existe, está fuera de rango o rompe coherente()
bool coherente(const Ajustes& a, const char** motivo);     // relaciones entre parámetros (bat_critica < bat_baja…)

// Perfiles de velocidad: cambian solo vbase, pwm_max, rampas, kp, kd y el freno en curva (no tocan inversiones,
// calibración ni sensores). Devuelve false si el nombre no existe.
bool aplicar_perfil(Ajustes& a, const char* nombre);

ParamControl a_control(const Ajustes& a);
motor::Modelo a_modelo(const Ajustes& a);
motor::Limites a_limites(const Ajustes& a);
Tiempos a_tiempos(const Ajustes& a);
uint32_t mascara(const Ajustes& a);

// Imagen guardada en la memoria no volátil (Preferences del ESP32)
constexpr int MAX_CAL = 16;
struct Guardado {
  uint32_t magia, version;
  Ajustes a;
  int32_t n_cal;
  float cal_min[MAX_CAL], cal_max[MAX_CAL];
  uint32_t crc;
};
constexpr uint32_t MAGIA = 0x454D4552u;   // "EMER"
constexpr uint32_t VERSION = 2;           // 2: parámetros de sensores, arranque y autocalibración
uint32_t crc32(const void* datos, size_t n);
void sellar(Guardado& g);                 // pone magia, versión y CRC
bool valido(const Guardado& g);

// ---- Turbo de recta (v2.1). Se guarda en su PROPIA clave de memoria ("t"): el bloque "g" (Ajustes, inversiones y
// calibración) no cambia de formato, así que lo ya guardado sigue siendo válido sin migración. Si "t" no existe o
// está dañada, el turbo queda desactivado. Solo lo ajustable va aquí; el resto son constantes de ParamControl
// (derivada propia 40 ms, |de/dt| 40/150 mm/s, confianza 1.2/0.8, 2 ciclos), validadas en pruebas/modelo_pista.py.
struct Turbo {
  float v_recta = 0.0f;        // velocidad en recta confiable; ≤ vbase = DESACTIVADO (perfil seguro y fábrica)
  float recta_e_in = 3.0f;     // mm: |error| para entrar a modo recta
  float recta_e_out = 6.0f;    // mm: |error| que lo cancela (2 ciclos seguidos)
  float recta_t_conf = 0.15f;  // s seguidos de recta limpia antes de acelerar
  float recta_t_acel = 0.5f;   // s para pasar de vbase a v_recta (la caída es inmediata)
};
const EntradaAjuste* tabla_turbo(int* n);
float* campo(Turbo& t, const EntradaAjuste& e);
const EntradaAjuste* buscar_turbo(const char* nombre);
bool coherente(const Turbo& t, const char** motivo);
bool fijar(Turbo& t, const char* nombre, float valor);
ParamControl a_control(const Ajustes& a, const Turbo& t);
// Perfil completo: además de lo de aplicar_perfil(a, …) fija v_recta (seguro = desactivado).
bool aplicar_perfil(Ajustes& a, Turbo& t, const char* nombre);

struct GuardadoTurbo {
  uint32_t magia, version;
  Turbo t;
  uint32_t crc;
};
constexpr uint32_t MAGIA_TURBO = 0x5455524Bu;   // "TURK"
constexpr uint32_t VERSION_TURBO = 1;
void sellar(GuardadoTurbo& g);
bool valido(const GuardadoTurbo& g);

}  // namespace robot
