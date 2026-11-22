#include "hw_casero.h"

#include <Arduino.h>

#include "config.h"

namespace hw {

// ---- PWM (LEDC). La API cambió en arduino-esp32 3.x; se soportan las dos.
static const uint32_t PWM_TOPE = (1u << PWM_BITS) - 1;   // escribir el tope = 100 % fijo (ledcWrite, 2.x y 3.x)
#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
static void pwm_iniciar(int pin, int) { ledcAttach(pin, PWM_FREC_HZ, PWM_BITS); }
static void pwm_escribir(int pin, int, uint32_t duty) { ledcWrite(pin, duty); }
static void tono(int pin, int, uint16_t hz) { ledcWriteTone(pin, hz); }
static void tono_iniciar(int pin, int) { ledcAttach(pin, 2000, 8); ledcWrite(pin, 0); }
static void tono_soltar(int pin) { ledcDetach(pin); }
#else
static void pwm_iniciar(int pin, int canal) { ledcSetup(canal, PWM_FREC_HZ, PWM_BITS); ledcAttachPin(pin, canal); }
static void pwm_escribir(int, int canal, uint32_t duty) { ledcWrite(canal, duty); }
static void tono(int, int canal, uint16_t hz) { ledcWriteTone(canal, hz); }
static void tono_iniciar(int pin, int canal) { ledcSetup(canal, 2000, 8); ledcAttachPin(pin, canal); ledcWrite(canal, 0); }
static void tono_soltar(int pin) { ledcDetachPin(pin); }
#endif

static const int PIN_IN[2][2] = {{PIN_AIN1, PIN_AIN2}, {PIN_BIN1, PIN_BIN2}};
static const int CANAL_IN[2][2] = {{CANAL_AIN1, CANAL_AIN2}, {CANAL_BIN1, CANAL_BIN2}};
static bool zumb_pwm = false;

void iniciar() {
  // Primero el puente dormido y las entradas en 0: el DRV8833 no mueve nada mientras arranca todo.
  pinMode(PIN_NSLEEP, OUTPUT);
  digitalWrite(PIN_NSLEEP, LOW);
  for (int m = 0; m < 2; ++m)
    for (int k = 0; k < 2; ++k) {
      pwm_iniciar(PIN_IN[m][k], CANAL_IN[m][k]);
      pwm_escribir(PIN_IN[m][k], CANAL_IN[m][k], 0);
    }
  pinMode(PIN_NFAULT, INPUT_PULLUP);
  pinMode(PIN_START, INPUT_PULLUP);
  pinMode(PIN_CAL, INPUT_PULLUP);
  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, LOW);
  pinMode(PIN_ZUMBADOR, OUTPUT);
  digitalWrite(PIN_ZUMBADOR, LOW);
  pinMode(PIN_EMISORES, OUTPUT);
  digitalWrite(PIN_EMISORES, LOW);

  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);          // 0 a ~3.1 V; la salida de los sensores llega a 3.3 V (satura en negro)
#if SENSORES_DIRECTOS
  for (int i = 0; i < NUM_SENSORES; ++i) pinMode(PINES_SENSORES[i], INPUT);
#else
  pinMode(PIN_MUX_S0, OUTPUT); pinMode(PIN_MUX_S1, OUTPUT); pinMode(PIN_MUX_S2, OUTPUT); pinMode(PIN_MUX_S3, OUTPUT);
  pinMode(PIN_MUX_SIG, INPUT);
#endif
  pinMode(PIN_BATERIA, INPUT);
}

void emisores(bool on) { digitalWrite(PIN_EMISORES, on ? HIGH : LOW); }

static int leer_promedio(int pin, int n) {
  int s = 0;
  for (int k = 0; k < n; ++k) s += analogRead(pin);
  return s / n;
}

static void barrer(int* v, int n_prom) {
#if SENSORES_DIRECTOS
  for (int i = 0; i < NUM_SENSORES; ++i) v[i] = leer_promedio(PINES_SENSORES[i], n_prom);
#else
  for (int a = 0; a < NUM_SENSORES; ++a) {
    digitalWrite(PIN_MUX_S0, a & 1); digitalWrite(PIN_MUX_S1, (a >> 1) & 1);
    digitalWrite(PIN_MUX_S2, (a >> 2) & 1); digitalWrite(PIN_MUX_S3, (a >> 3) & 1);
    delayMicroseconds(4);                   // asentamiento del multiplexor [P: verificar]
    v[a] = leer_promedio(PIN_MUX_SIG, n_prom);
  }
#endif
}

uint32_t leer_sensores(int* on, int* off, bool resta, uint32_t t_emisor_us, int n_prom) {
  const uint32_t t0 = micros();
  if (n_prom < 1) n_prom = 1;
  emisores(true);
  delayMicroseconds(t_emisor_us);
  barrer(on, n_prom);
  if (resta) {
    emisores(false);
    delayMicroseconds(t_emisor_us);
    barrer(off, n_prom);
  } else {
    for (int i = 0; i < NUM_SENSORES; ++i) off[i] = 0;
  }
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

void driver_despierto(bool d) { digitalWrite(PIN_NSLEEP, d ? HIGH : LOW); }
bool driver_falla() { return digitalRead(PIN_NFAULT) == LOW; }

float v_divisor() {
  uint32_t mv = 0;
  for (int k = 0; k < 4; ++k) mv += analogReadMilliVolts(PIN_BATERIA);   // usa la calibración de fábrica del ADC
  return (mv / 4.0f) * 0.001f * DIVISOR_BATERIA;
}

bool boton_start() { return digitalRead(PIN_START) == LOW; }
bool boton_cal() { return digitalRead(PIN_CAL) == LOW; }
void led(bool e) { digitalWrite(PIN_LED, e ? HIGH : LOW); }

void zumbador(uint16_t hz, bool activo) {
  static uint16_t ultimo = 0xFFFF;
  static bool ultimo_activo = true;
  if (hz == ultimo && activo == ultimo_activo) return;
  ultimo = hz;
  ultimo_activo = activo;
  if (activo) {                             // zumbador activo: solo encender/apagar
    if (zumb_pwm) { tono_soltar(PIN_ZUMBADOR); zumb_pwm = false; pinMode(PIN_ZUMBADOR, OUTPUT); }
    digitalWrite(PIN_ZUMBADOR, hz ? HIGH : LOW);
    return;
  }
  if (!zumb_pwm) { tono_iniciar(PIN_ZUMBADOR, CANAL_ZUMB); zumb_pwm = true; }
  tono(PIN_ZUMBADOR, CANAL_ZUMB, hz);
}

}  // namespace hw
