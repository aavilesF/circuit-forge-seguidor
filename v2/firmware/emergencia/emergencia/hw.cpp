#include "hw.h"

#include <Arduino.h>
#include <esp_idf_version.h>
#include <esp_task_wdt.h>

#include "config.h"
#include "utiles.h"

namespace hw {

// ---- PWM (LEDC). La API cambió en arduino-esp32 3.x; se soportan las dos.
// En ambas, ledcWrite con el tope (2^bits − 1) deja la salida 100 % en alto (sin pulso bajo).
static const uint32_t PWM_TOPE = (1u << PWM_BITS) - 1;
#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
static void pwm_iniciar(int pin, int) { ledcAttach(pin, PWM_FREC_HZ, PWM_BITS); }
static void pwm_escribir(int pin, int, uint32_t duty) { ledcWrite(pin, duty); }
#else
static void pwm_iniciar(int pin, int canal) { ledcSetup(canal, PWM_FREC_HZ, PWM_BITS); ledcAttachPin(pin, canal); }
static void pwm_escribir(int, int canal, uint32_t duty) { ledcWrite(canal, duty); }
#endif

static const int PIN_IN[2][2] = {{PIN_AIN1, PIN_AIN2}, {PIN_BIN1, PIN_BIN2}};
static const int CANAL_IN[2][2] = {{CANAL_AIN1, CANAL_AIN2}, {CANAL_BIN1, CANAL_BIN2}};
static const int PIN_S[4] = {PIN_MUX_S0, PIN_MUX_S1, PIN_MUX_S2, PIN_MUX_S3};
static bool emis_on = false, despierto_ = false;
static int canal_actual = -1;

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

  for (int b = 0; b < 4; ++b) { pinMode(PIN_S[b], OUTPUT); digitalWrite(PIN_S[b], LOW); }
  canal_actual = 0;
  pinMode(PIN_MUX_SIG, INPUT);
  pinMode(PIN_BATERIA, INPUT);
  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);          // 0 a ~3.1 V; el pull-up de 10 kΩ a 3V3 satura en negro (no importa)
}

void emisores(bool on) { digitalWrite(PIN_EMISORES, on ? HIGH : LOW); emis_on = on; }
bool emisores_encendidos() { return emis_on; }

// Solo se escriben los bits de selección que cambian (de C0 a C7, S3 no se toca nunca).
void seleccionar_canal(int canal, uint32_t t_mux_us) {
  canal &= 0x0F;
  if (canal == canal_actual) return;
  const util::BitsMux b = util::bits_mux(canal);
  const uint8_t nuevo[4] = {b.s0, b.s1, b.s2, b.s3};
  for (int k = 0; k < 4; ++k) {
    const bool cambia = canal_actual < 0 || ((canal_actual >> k) & 1) != nuevo[k];
    if (cambia) digitalWrite(PIN_S[k], nuevo[k] ? HIGH : LOW);
  }
  canal_actual = canal;
  if (t_mux_us) delayMicroseconds(t_mux_us);
}

int leer_canal(int canal, const ConfigLectura& c) {
  seleccionar_canal(canal, c.t_mux_us);
  for (int k = 0; k < c.descartes; ++k) (void)analogRead(PIN_MUX_SIG);   // carga del ADC del canal anterior
  const int n = c.sobremuestreo < 1 ? 1 : c.sobremuestreo;
  int s = 0;
  for (int k = 0; k < n; ++k) s += analogRead(PIN_MUX_SIG);
  return (s + n / 2) / n;
}

static void barrer(int* v, const ConfigLectura& c) {
  for (int i = 0; i < NUM_SENSORES; ++i) v[i] = leer_canal(util::canal_de_sensor(i, NUM_SENSORES, c.invertidos), c);
}

uint32_t leer_sensores(int* on, int* off, const ConfigLectura& c) {
  const uint32_t t0 = micros();
  if (c.resta_ambiente) {                   // GUIA 3: primero con LED apagados (luz ambiente)…
    emisores(false);
    delayMicroseconds(c.t_emisor_us);
    barrer(off, c);
  } else {
    for (int i = 0; i < NUM_SENSORES; ++i) off[i] = 0;
  }
  emisores(true);                           // …luego encendidos
  delayMicroseconds(c.t_emisor_us);
  barrer(on, c);
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

// ---- watchdog. Los dos núcleos lo arrancan a 5 s vigilando solo la tarea ociosa del núcleo 0; aquí se acorta y se
// suscribe la tarea de loop() (setup() corre en ella).
bool vigilante_iniciar(uint32_t ms) {
#if ESP_IDF_VERSION_MAJOR >= 5
  esp_task_wdt_config_t cfg = {};
  cfg.timeout_ms = ms;
  cfg.idle_core_mask = 1u << 0;   // igual que la configuración de fábrica (ociosa del núcleo 0)
  cfg.trigger_panic = true;
  esp_err_t r = esp_task_wdt_reconfigure(&cfg);
  if (r == ESP_ERR_INVALID_STATE) r = esp_task_wdt_init(&cfg);
  if (r != ESP_OK) return false;
#else
  const uint32_t s = ms < 1000 ? 1 : (ms + 999) / 1000;   // IDF 4.4 trabaja en segundos
  if (esp_task_wdt_init(s, true) != ESP_OK) return false;
#endif
  const esp_err_t a = esp_task_wdt_add(nullptr);
  return a == ESP_OK || a == ESP_ERR_INVALID_ARG;   // INVALID_ARG = ya estaba suscrita
}

void vigilante_alimentar() { esp_task_wdt_reset(); }

uint32_t cpu_mhz() { return getCpuFrequencyMhz(); }

const char* version_nucleo() {
#if defined(ESP_ARDUINO_VERSION_MAJOR)
#define TXT2(x) #x
#define TXT(x) TXT2(x)
  return "arduino-esp32 " TXT(ESP_ARDUINO_VERSION_MAJOR) "." TXT(ESP_ARDUINO_VERSION_MINOR) "." TXT(ESP_ARDUINO_VERSION_PATCH);
#undef TXT
#undef TXT2
#else
  return "arduino-esp32 (version desconocida)";
#endif
}

}  // namespace hw
