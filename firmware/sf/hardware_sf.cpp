#include "hardware_sf.h"
#include "posicion.h"
#include "parametros.h"

namespace hw {

#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
static void pwm_iniciar(int pin, int) { ledcAttach(pin, PWM_FREC_HZ, PWM_BITS); }
static void pwm_escribir(int pin, int, uint32_t d) { ledcWrite(pin, d); }
#else
static void pwm_iniciar(int pin, int canal) { ledcSetup(canal, PWM_FREC_HZ, PWM_BITS); ledcAttachPin(pin, canal); }
static void pwm_escribir(int, int canal, uint32_t d) { ledcWrite(canal, d); }
#endif
static constexpr uint32_t PWM_MAX = (1u << PWM_BITS) - 1;
static inline uint32_t a_cuentas(float x) { if (x < 0) x = 0; if (x > 1) x = 1; return uint32_t(x * PWM_MAX + 0.5f); }

#if DRIVER == DRIVER_DRV8833
// DRV8833, decaimiento lento. Ficha TI SLVSAR1E, tabla 2 "PWM control of motor speed" (consultada 31 oct 2026):
//   xIN1 = 1, xIN2 = PWM -> "Forward PWM, slow decay";  xIN1 = PWM, xIN2 = 1 -> "Reverse PWM, slow decay".
//   Con 1/1 el puente frena (slow decay) y con 1/0 conduce adelante, así que el ciclo de IN2 es (1 - d).
//   nSLEEP: tras despertar la ficha pide hasta 1 ms (tWAKE) antes de que las salidas respondan.
static void un_motor(int p1, int c1, int p2, int c2, float d, bool inv) {
  if (inv) d = -d;
  if (d >= 0) { pwm_escribir(p1, c1, PWM_MAX); pwm_escribir(p2, c2, a_cuentas(1.0f - d)); }
  else        { pwm_escribir(p2, c2, PWM_MAX); pwm_escribir(p1, c1, a_cuentas(1.0f + d)); }
}
static bool despierto = false;
void motores(float izq, float der) {
  if (!despierto) { digitalWrite(PIN_SLEEP, HIGH); delay(1); despierto = true; }   // tWAKE, una sola vez por arranque
  un_motor(PIN_AIN1, 0, PIN_AIN2, 1, izq, INVERTIR_IZQ);
  un_motor(PIN_BIN1, 2, PIN_BIN2, 3, der, INVERTIR_DER);
}
void motores_apagar() {
  pwm_escribir(PIN_AIN1, 0, 0); pwm_escribir(PIN_AIN2, 1, 0);
  pwm_escribir(PIN_BIN1, 2, 0); pwm_escribir(PIN_BIN2, 3, 0);   // 0/0 = coast
  digitalWrite(PIN_SLEEP, LOW);
  despierto = false;
}
static void iniciar_driver() {
  pinMode(PIN_SLEEP, OUTPUT); digitalWrite(PIN_SLEEP, LOW);
  pwm_iniciar(PIN_AIN1, 0); pwm_iniciar(PIN_AIN2, 1); pwm_iniciar(PIN_BIN1, 2); pwm_iniciar(PIN_BIN2, 3);
  motores_apagar();
}
#else
// TB6612FNG: IN fijo según el sentido, PWM en el pin PWM (PWM bajo = freno corto).
static void un_motor(int pwm, int canal, int in1, int in2, float d, bool inv) {
  if (inv) d = -d;
  const bool adelante = d >= 0;
  digitalWrite(in1, adelante ? HIGH : LOW); digitalWrite(in2, adelante ? LOW : HIGH);
  pwm_escribir(pwm, canal, a_cuentas(adelante ? d : -d));
}
void motores(float izq, float der) {
  digitalWrite(PIN_STBY, HIGH);
  un_motor(PIN_PWMA, 0, PIN_AIN1, PIN_AIN2, izq, INVERTIR_IZQ);
  un_motor(PIN_PWMB, 1, PIN_BIN1, PIN_BIN2, der, INVERTIR_DER);
}
void motores_apagar() { pwm_escribir(PIN_PWMA, 0, 0); pwm_escribir(PIN_PWMB, 1, 0); digitalWrite(PIN_STBY, LOW); }
static void iniciar_driver() {
  pinMode(PIN_STBY, OUTPUT); digitalWrite(PIN_STBY, LOW);
  pinMode(PIN_AIN1, OUTPUT); pinMode(PIN_AIN2, OUTPUT); pinMode(PIN_BIN1, OUTPUT); pinMode(PIN_BIN2, OUTPUT);
  pwm_iniciar(PIN_PWMA, 0); pwm_iniciar(PIN_PWMB, 1);
  motores_apagar();
}
#endif

static inline void emisores(bool on) { digitalWrite(PIN_EMISORES, (on == EMISOR_ACTIVO_ALTO) ? HIGH : LOW); }
static inline void direccion(int a) {
  digitalWrite(PIN_MUX_S0, a & 1); digitalWrite(PIN_MUX_S1, (a >> 1) & 1);
  digitalWrite(PIN_MUX_S2, (a >> 2) & 1); digitalWrite(PIN_MUX_S3, (a >> 3) & 1);
}
static void barrer(int* dst) {
  for (int a = 0; a < NUM_SENSORES; ++a) { direccion(a); delayMicroseconds(MUX_ESTABLECIMIENTO_US); dst[a] = analogRead(PIN_MUX_SIG); }
}
void leer_crudo(int* raw) { emisores(true); delayMicroseconds(EMISOR_ESTABLECIMIENTO_US); barrer(raw); }
void leer_reflectancia(float* refl, int* raw_on) {
  static const posicion::ModoSensor modo = {RESTA_AMBIENTE, ALTO_ES_NEGRO, par::ADC_MAX};
  int on[par::MAX_SENSORES], off[par::MAX_SENSORES];
  if (RESTA_AMBIENTE) { emisores(true); delayMicroseconds(EMISOR_ESTABLECIMIENTO_US); }   // sin resta: emisores siempre encendidos
  barrer(on);
  if (RESTA_AMBIENTE) { emisores(false); delayMicroseconds(EMISOR_ESTABLECIMIENTO_US); barrer(off); }
  for (int i = 0; i < NUM_SENSORES; ++i) refl[i] = posicion::reflectancia(modo, on[i], RESTA_AMBIENTE ? off[i] : 0);
  if (raw_on) for (int i = 0; i < NUM_SENSORES; ++i) raw_on[i] = on[i];
}
bool boton_start() { return digitalRead(PIN_START) == LOW; }
bool boton_cal() { return digitalRead(PIN_CAL) == LOW; }
void led(bool e) { digitalWrite(PIN_LED, e ? HIGH : LOW); }
float voltaje_bateria() { return analogReadMilliVolts(PIN_BATERIA) * 0.001f * DIVISOR_BAT; }

void iniciar() {
  iniciar_driver();
  pinMode(PIN_MUX_S0, OUTPUT); pinMode(PIN_MUX_S1, OUTPUT); pinMode(PIN_MUX_S2, OUTPUT); pinMode(PIN_MUX_S3, OUTPUT);
  pinMode(PIN_EMISORES, OUTPUT); emisores(!RESTA_AMBIENTE);   // sin resta de luz ambiente quedan encendidos
  pinMode(PIN_MUX_SIG, INPUT);
  pinMode(PIN_START, INPUT_PULLUP); pinMode(PIN_CAL, INPUT_PULLUP); pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_BATERIA, INPUT);
  analogReadResolution(12);
  analogSetPinAttenuation(PIN_MUX_SIG, ADC_11db);
  analogSetPinAttenuation(PIN_BATERIA, ADC_11db);
  // Sin WiFi ni Bluetooth (reglamento).
}
}  // namespace hw
