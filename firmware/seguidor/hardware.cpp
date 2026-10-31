#include "hardware.h"
#include "pines.h"

namespace hw {

// ---- PWM: la API de ledc cambió en arduino-esp32 3.x ---------------------
#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
  static void pwm_iniciar(int pin, int /*canal*/) { ledcAttach(pin, PWM_FREC_HZ, PWM_BITS); }
  static void pwm_escribir(int pin, int /*canal*/, uint32_t duty) { ledcWrite(pin, duty); }
#else
  static void pwm_iniciar(int pin, int canal) { ledcSetup(canal, PWM_FREC_HZ, PWM_BITS); ledcAttachPin(pin, canal); }
  static void pwm_escribir(int /*pin*/, int canal, uint32_t duty) { ledcWrite(canal, duty); }
#endif

static constexpr int CANAL_A = 0, CANAL_B = 1;
static constexpr uint32_t PWM_MAX = (1u << PWM_BITS) - 1;

static void un_motor(int pin_pwm, int canal, int pin_in1, int pin_in2, float cmd, bool invertir) {
  if (invertir) cmd = -cmd;
  if (cmd > 1.f) cmd = 1.f;
  if (cmd < -1.f) cmd = -1.f;
  const bool adelante = cmd >= 0.f;
  digitalWrite(pin_in1, adelante ? HIGH : LOW);
  digitalWrite(pin_in2, adelante ? LOW : HIGH);
  pwm_escribir(pin_pwm, canal, uint32_t((adelante ? cmd : -cmd) * PWM_MAX + 0.5f));
}

void motores(float izq, float der) {
  digitalWrite(PIN_STBY, HIGH);
  un_motor(PIN_PWMA, CANAL_A, PIN_AIN1, PIN_AIN2, izq, INVERTIR_IZQ);
  un_motor(PIN_PWMB, CANAL_B, PIN_BIN1, PIN_BIN2, der, INVERTIR_DER);
}

void motores_apagar() {
  pwm_escribir(PIN_PWMA, CANAL_A, 0);
  pwm_escribir(PIN_PWMB, CANAL_B, 0);
  digitalWrite(PIN_STBY, LOW);
}

// ---- Sensores --------------------------------------------------------------
static inline void emisores(bool on) { digitalWrite(PIN_EMISORES, on ? HIGH : LOW); }

static inline void direccion(int a) {
  digitalWrite(PIN_MUX_S0, a & 1);
  digitalWrite(PIN_MUX_S1, (a >> 1) & 1);
  digitalWrite(PIN_MUX_S2, (a >> 2) & 1);
  digitalWrite(PIN_MUX_S3, (a >> 3) & 1);
}

// Barre las 16 direcciones; el multiplexor 1 da los canales 0..15 y el 2 los 16..31.
static void barrer(int* dst) {
  const int n = NUM_SENSORES;
  const int pasos = n < 16 ? n : 16;
  for (int a = 0; a < pasos; ++a) {
    direccion(a);
    delayMicroseconds(4);                 // tiempo de establecimiento del multiplexor (VERIFICAR con osciloscopio o prueba)
    dst[a] = analogRead(PIN_MUX_SIG1);
    if (a + 16 < n) dst[a + 16] = analogRead(PIN_MUX_SIG2);
  }
}

void leer_crudo(int* raw) {
  emisores(true);
  delayMicroseconds(30);
  barrer(raw);
}

void leer_reflectancia(float* refl) {
  static const posicion::ModoSensor modo = {RESTA_AMBIENTE, ALTO_ES_NEGRO, par::ADC_MAX};
  int on[par::MAX_SENSORES], off[par::MAX_SENSORES];
  emisores(true);
  delayMicroseconds(30);
  barrer(on);
  if (RESTA_AMBIENTE) {
    emisores(false);
    delayMicroseconds(30);
    barrer(off);
  }
  for (int i = 0; i < NUM_SENSORES; ++i) refl[i] = posicion::reflectancia(modo, on[i], RESTA_AMBIENTE ? off[i] : 0);
}

// ---- Interfaz --------------------------------------------------------------
bool boton_start() { return digitalRead(PIN_START) == LOW; }
bool boton_cal()   { return digitalRead(PIN_CAL) == LOW; }
void led(bool e)   { digitalWrite(PIN_LED, e ? HIGH : LOW); }

float perfil_velocidad() {
  return analogRead(PIN_PERFIL) / float(par::ADC_MAX);
}

float voltaje_bateria() {
  return analogReadMilliVolts(PIN_BATERIA) * 0.001f * DIVISOR_BAT;
}

void iniciar() {
  // Salidas en estado seguro ANTES que cualquier otra cosa: motores apagados.
  pinMode(PIN_STBY, OUTPUT);   digitalWrite(PIN_STBY, LOW);
  pinMode(PIN_AIN1, OUTPUT);   pinMode(PIN_AIN2, OUTPUT);
  pinMode(PIN_BIN1, OUTPUT);   pinMode(PIN_BIN2, OUTPUT);
  pwm_iniciar(PIN_PWMA, CANAL_A);
  pwm_iniciar(PIN_PWMB, CANAL_B);
  motores_apagar();

  pinMode(PIN_MUX_S0, OUTPUT); pinMode(PIN_MUX_S1, OUTPUT);
  pinMode(PIN_MUX_S2, OUTPUT); pinMode(PIN_MUX_S3, OUTPUT);
  pinMode(PIN_EMISORES, OUTPUT); emisores(false);
  pinMode(PIN_MUX_SIG1, INPUT); pinMode(PIN_MUX_SIG2, INPUT);

  pinMode(PIN_START, INPUT_PULLUP);
  pinMode(PIN_CAL, INPUT_PULLUP);
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_PERFIL, INPUT);
  pinMode(PIN_BATERIA, INPUT);

  analogReadResolution(12);
  analogSetPinAttenuation(PIN_MUX_SIG1, ADC_11db);
  analogSetPinAttenuation(PIN_MUX_SIG2, ADC_11db);
  analogSetPinAttenuation(PIN_PERFIL, ADC_11db);
  analogSetPinAttenuation(PIN_BATERIA, ADC_11db);
  // No se inicializa WiFi ni Bluetooth: el reglamento prohíbe comunicación inalámbrica.
}

}  // namespace hw
