#include "hw.h"

#include <Arduino.h>

#include "config.h"
#include "utiles.h"

namespace hw {

// ---- PWM (LEDC). La API cambió en arduino-esp32 3.x; se soportan las dos.
static const uint32_t PWM_TOPE = (1u << PWM_BITS) - 1;   // escribir el tope = 100 % fijo
#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
static void pwm_iniciar(int pin, int) { ledcAttach(pin, PWM_FREC_HZ, PWM_BITS); }
static void pwm_escribir(int pin, int, uint32_t duty) { ledcWrite(pin, duty); }
#else
static void pwm_iniciar(int pin, int canal) { ledcSetup(canal, PWM_FREC_HZ, PWM_BITS); ledcAttachPin(pin, canal); }
static void pwm_escribir(int, int canal, uint32_t duty) { ledcWrite(canal, duty); }
#endif

static const int PIN_IN[2][2] = {{PIN_AIN1, PIN_AIN2}, {PIN_BIN1, PIN_BIN2}};
static const int CANAL_IN[2][2] = {{CANAL_AIN1, CANAL_AIN2}, {CANAL_BIN1, CANAL_BIN2}};
static bool emis_on = false, despierto_ = false;

void iniciar() {
  // Primero el puente dormido y las entradas en 0: el DRV8833 no mueve nada mientras arranca todo.
  pinMode(PIN_NSLEEP, OUTPUT);
  digitalWrite(PIN_NSLEEP, LOW);
  despierto_ = false;
  for (int m = 0; m < 2; ++m)
    for (int k = 0; k < 2; ++k) {
      pinMode(PIN_IN[m][k], OUTPUT);
      digitalWrite(PIN_IN[m][k], LOW);
      pwm_iniciar(PIN_IN[m][k], CANAL_IN[m][k]);
      pwm_escribir(PIN_IN[m][k], CANAL_IN[m][k], 0);
    }
  pinMode(PIN_START, INPUT_PULLUP);
  pinMode(PIN_CAL, INPUT_PULLUP);
  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, LOW);
  pinMode(PIN_EMISORES, OUTPUT);
  digitalWrite(PIN_EMISORES, LOW);
  emis_on = false;

  pinMode(PIN_MUX_S0, OUTPUT); pinMode(PIN_MUX_S1, OUTPUT); pinMode(PIN_MUX_S2, OUTPUT); pinMode(PIN_MUX_S3, OUTPUT);
  pinMode(PIN_MUX_SIG, INPUT);
  pinMode(PIN_BATERIA, INPUT);
  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);          // 0 a ~3.1 V; el pull-up de 10 kΩ a 3V3 satura en negro (no importa)
}

void emisores(bool on) { digitalWrite(PIN_EMISORES, on ? HIGH : LOW); emis_on = on; }
bool emisores_encendidos() { return emis_on; }

static void seleccionar(int canal) {
  const util::BitsMux b = util::bits_mux(canal);
  digitalWrite(PIN_MUX_S0, b.s0); digitalWrite(PIN_MUX_S1, b.s1);
  digitalWrite(PIN_MUX_S2, b.s2); digitalWrite(PIN_MUX_S3, b.s3);
  delayMicroseconds(MUX_ASENTAMIENTO_US);
}

int leer_canal(int canal, int n) {
  if (n < 1) n = 1;
  seleccionar(canal);
  int s = 0;
  for (int k = 0; k < n; ++k) s += analogRead(PIN_MUX_SIG);
  return s / n;
}

static void barrer(int* v, int n_prom) {
  for (int i = 0; i < NUM_SENSORES; ++i)
    v[i] = leer_canal(util::canal_de_sensor(i, NUM_SENSORES, SENSORES_INVERTIDOS != 0), n_prom);
}

uint32_t leer_sensores(int* on, int* off, bool resta, uint32_t t_emisor_us, int n_prom) {
  const uint32_t t0 = micros();
  if (resta) {                              // GUIA 3: primero con LED apagados (luz ambiente)…
    emisores(false);
    delayMicroseconds(t_emisor_us);
    barrer(off, n_prom);
  } else {
    for (int i = 0; i < NUM_SENSORES; ++i) off[i] = 0;
  }
  emisores(true);                           // …luego encendidos
  delayMicroseconds(t_emisor_us);
  barrer(on, n_prom);
  emisores(false);                          // apagados entre ciclos: menos consumo y calor
  return micros() - t0;
}

void puente(int m, float in1, float in2) {
  if (m < 0 || m > 1) return;
  const float v[2] = {in1, in2};
  for (int k = 0; k < 2; ++k) {
    float x = v[k] < 0.0f ? 0.0f : (v[k] > 1.0f ? 1.0f : v[k]);
    pwm_escribir(PIN_IN[m][k], CANAL_IN[m][k], static_cast<uint32_t>(x * PWM_TOPE + 0.5f));
  }
}

void driver_despierto(bool d) {
  if (d == despierto_) return;
  digitalWrite(PIN_NSLEEP, d ? HIGH : LOW);
  despierto_ = d;
}
bool driver_esta_despierto() { return despierto_; }

float mv_pin_bateria() {
  uint32_t mv = 0;
  for (int k = 0; k < 4; ++k) mv += analogReadMilliVolts(PIN_BATERIA);   // usa la calibración de fábrica del ADC
  return mv / 4.0f;
}

float v_bateria() { return util::volts_bateria(mv_pin_bateria(), DIVISOR_BATERIA); }

bool boton_start() { return digitalRead(PIN_START) == LOW; }
bool boton_cal() { return digitalRead(PIN_CAL) == LOW; }
void led(bool e) { digitalWrite(PIN_LED, e ? HIGH : LOW); }

}  // namespace hw
