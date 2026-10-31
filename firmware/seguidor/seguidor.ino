// Seguidor de línea - Circuit Forge - ESP32 (Arduino framework).
// Este archivo solo orquesta: lee el hardware, alimenta la lógica pura y aplica sus decisiones.
//   posicion.*  calibración y posición de la línea      (C++ puro, probado en PC)
//   pid.*       PID con anti-windup                      (C++ puro, probado en PC)
//   control.*   del error a las ruedas, búsqueda         (C++ puro, probado en PC)
//   estados.*   máquina de estados, botones, batería     (C++ puro, probado en PC)
//   hardware.*  pines, ADC, PWM                          (depende del ESP32)
//
// NO incluir WiFi.h ni BluetoothSerial.h: el reglamento prohíbe comunicación inalámbrica.
#include <Preferences.h>
#include "pines.h"
#include "parametros.h"
#include "posicion.h"
#include "pid.h"
#include "control.h"
#include "estados.h"
#include "hardware.h"

// Versión del formato guardado en memoria. Subirla si cambia ParamControl o Calibracion:
// así un firmware nuevo no lee bytes con otro significado.
static constexpr uint32_t VERSION_NVS = 2;
static constexpr uint32_t CAL_MAX_MS = 10000;          // reglamento: 15 s para calibrar y colocar
static constexpr uint32_t BATERIA_PERIODO_MS = 20;     // la batería se lee fuera del ciclo crítico
static constexpr uint32_t FALLA_SENSORES_MS = 300;
static constexpr uint32_t TELEMETRIA_CADA = 20;        // 1 de cada 20 ciclos (25 Hz a 500 Hz)

static posicion::Geometria geom;
static posicion::Calibracion cal;
static ParamControl pc;
static ControladorLinea ctl(param_por_defecto());
static MaquinaEstados maquina;
static Boton boton_start, boton_cal;
static MonitorBateria bateria(BATERIA_MIN_V, BATERIA_CRITICA_V, 300);
static Preferences nvs;

static float refl[par::MAX_SENSORES];
static float osc[par::MAX_SENSORES];
static int raw_on[par::MAX_SENSORES];
static uint32_t t_prev_us = 0, t_bat_ms = 0, t_falla_ms = 0, ciclos = 0;
static bool falla_activa = false, telemetria = false;
static bool ult_buscando = false;   // se conserva entre ciclos: el lazo de control no corre en cada loop()
static uint32_t t_lectura_us = 0, t_ciclo_max_us = 0;

// ---------------------------------------------------------------- memoria no volátil
static void guardar() {
  nvs.begin("seguidor", false);
  nvs.putUInt("ver", VERSION_NVS);
  nvs.putBytes("pc", &pc, sizeof(pc));
  nvs.putBytes("cal", &cal, sizeof(cal));
  nvs.end();
}

static void cargar() {
  nvs.begin("seguidor", true);
  if (nvs.getUInt("ver", 0) == VERSION_NVS) {
    if (nvs.getBytesLength("pc") == sizeof(pc)) nvs.getBytes("pc", &pc, sizeof(pc));
    if (nvs.getBytesLength("cal") == sizeof(cal)) {
      nvs.getBytes("cal", &cal, sizeof(cal));
      if (cal.n != NUM_SENSORES) cal.reiniciar(NUM_SENSORES);  // cambió el perfil de sensor
    }
  }
  nvs.end();
}

// ---------------------------------------------------------------- consola serie (USB, solo en pruebas)
static void imprimir_parametros() {
  Serial.printf("kp=%.5f ki=%.5f kd=%.5f vbase=%.3f freno=%.2f error_ref=%.1f vmin_rel=%.2f u_max=%.2f\n",
                pc.kp, pc.ki, pc.kd, pc.vbase, pc.freno_error, pc.error_ref_mm, pc.vmin_rel, pc.u_max);
}

static bool poner(const String& k, float v) {
  if (k == "kp") pc.kp = v; else if (k == "ki") pc.ki = v; else if (k == "kd") pc.kd = v;
  else if (k == "vbase") pc.vbase = v; else if (k == "freno") pc.freno_error = v;
  else if (k == "error_ref") pc.error_ref_mm = v; else if (k == "vmin_rel") pc.vmin_rel = v;
  else if (k == "u_max") pc.u_max = v; else return false;
  ctl.fijar(pc);
  return true;
}

static void diagnostico() {
  const uint32_t t0 = micros();
  hw::leer_reflectancia(refl, raw_on);
  const uint32_t t1 = micros();
  Serial.printf("lectura de %d sensores: %lu us | ciclo max en marcha: %lu us | bateria %.2f V | estado %s\n",
                NUM_SENSORES, (unsigned long)(t1 - t0), (unsigned long)t_ciclo_max_us, bateria.voltaje(),
                nombre_estado(maquina.estado()));
}

static void consola() {
  if (!Serial.available()) return;
  String l = Serial.readStringUntil('\n'); l.trim();
  if (l.length() == 0) return;
  if (l == "ayuda") {
    Serial.println("comandos: get | set <clave> <valor> | save | load | defecto | sens | crudo | bat | diag | tel 0/1 | m <izq> <der>");
    Serial.println("claves: kp ki kd vbase freno error_ref vmin_rel u_max");
  } else if (l == "get") imprimir_parametros();
  else if (l == "save") { guardar(); Serial.println("guardado"); }
  else if (l == "load") { cargar(); ctl.fijar(pc); imprimir_parametros(); }
  else if (l == "defecto") { pc = param_por_defecto(); ctl.fijar(pc); imprimir_parametros(); }
  else if (l == "bat") Serial.printf("bateria: %.2f V (filtrada)\n", bateria.voltaje());
  else if (l == "diag") diagnostico();
  else if (l == "crudo") { hw::leer_crudo(raw_on); for (int i = 0; i < NUM_SENSORES; ++i) Serial.printf("%d ", raw_on[i]); Serial.println(); }
  else if (l == "sens") {
    hw::leer_reflectancia(refl); posicion::normalizar(cal, refl, osc);
    for (int i = 0; i < NUM_SENSORES; ++i) Serial.printf("%.2f ", osc[i]);
    posicion::Estimacion e = posicion::estimar_posicion(geom, osc, par::UMBRAL_RUIDO, par::CONFIANZA_MIN);
    Serial.printf("| pos=%.1f mm visible=%d\n", e.pos_mm, e.linea_visible);
  } else if (l.startsWith("tel ")) telemetria = l.substring(4).toInt() != 0;
  else if (l.startsWith("set ")) {
    int sp = l.indexOf(' ', 4);
    if (sp < 0 || !poner(l.substring(4, sp), l.substring(sp + 1).toFloat())) Serial.println("uso: set <clave> <valor>");
    else imprimir_parametros();
  } else if (l.startsWith("m ")) {   // prueba de motores con las ruedas en el aire: m 0.3 0.3
    int sp = l.indexOf(' ', 2);
    if (sp < 0) { Serial.println("uso: m <izq> <der>"); return; }
    float a = l.substring(2, sp).toFloat(), b = l.substring(sp + 1).toFloat();
    if (MOTOR_DESDE_BATERIA) { a = compensar_bateria(a, bateria.voltaje(), V_MOTOR_NOMINAL); b = compensar_bateria(b, bateria.voltaje(), V_MOTOR_NOMINAL); }
    hw::motores(a, b); delay(1000); hw::motores_apagar(); Serial.println("ok");
  } else Serial.println("comando desconocido (escribe: ayuda)");
}

// ---------------------------------------------------------------- LED: patrón según estado
static void led_estado(uint32_t ahora) {
  switch (maquina.estado()) {
    case Estado::ESPERA:      hw::led((ahora / 500) % 2); break;          // lento
    case Estado::CALIBRANDO:  hw::led((ahora / 75) % 2); break;           // rápido
    case Estado::LISTO:       hw::led(maquina.motivo() == Motivo::BATERIA_ARRANQUE ? (ahora / 150) % 4 == 0 : true); break;
    case Estado::PARADA:      hw::led((ahora / 150) % 2); break;
    case Estado::ERROR:       hw::led((ahora / 100) % 10 < 2); break;     // doble destello
    default: break;                                                        // en marcha lo maneja el lazo
  }
}

// ---------------------------------------------------------------- setup / loop
void setup() {
  Serial.begin(115200);
  hw::iniciar();
  geom = ARCO ? posicion::geometria_arco(NUM_SENSORES, PASO_MM, RADIO_ARCO_MM, par::DIST_SENSOR_EJE_MM)
              : posicion::geometria_recta(NUM_SENSORES, PASO_MM, par::DIST_SENSOR_EJE_MM);
  pc = param_por_defecto();
  cal.reiniciar(NUM_SENSORES);
  cargar();
  ctl.fijar(pc);
  for (int i = 0; i < 20; ++i) bateria.muestra(hw::voltaje_bateria(), millis());
  Serial.println("Circuit Forge - seguidor listo. Escribe 'ayuda'.");
  imprimir_parametros();
}

void loop() {
  const uint32_t ahora = millis();
  Eventos ev;
  ev.start = boton_start.actualizar(hw::boton_start(), ahora);
  ev.cal = boton_cal.actualizar(hw::boton_cal(), ahora);

  // Batería: cada 20 ms, filtrada (fuera del cálculo de control).
  if (ahora - t_bat_ms >= BATERIA_PERIODO_MS) { t_bat_ms = ahora; bateria.muestra(hw::voltaje_bateria(), ahora); }
  ev.bateria_permite = bateria.permite_arranque();
  ev.bateria_critica = bateria.critica();
  ev.cal_guardada_ok = cal.lista(par::RANGO_CAL_MIN);

  const Estado e = maquina.estado();

  if (e == Estado::CALIBRANDO) {
    hw::leer_reflectancia(refl);
    cal.muestrear(refl);
    ev.cal_suficiente = cal.lista(par::RANGO_CAL_MIN);
    ev.cal_tiempo_agotado = ahora - maquina.desde_ms() > CAL_MAX_MS;
  }

  bool ciclo_control = false;
  SalidaControl s{};
  if (e == Estado::SIGUIENDO || e == Estado::RECUPERANDO) {
    const uint32_t ahora_us = micros();
    if (ahora_us - t_prev_us >= par::PERIODO_CONTROL_US) {
      ciclo_control = true;
      const float dt = (ahora_us - t_prev_us) * 1e-6f;   // dt REAL, no el nominal
      t_prev_us = ahora_us;

      hw::leer_reflectancia(refl, raw_on);
      posicion::normalizar(cal, refl, osc);
      const posicion::Estimacion est = posicion::estimar_posicion(geom, osc, par::UMBRAL_RUIDO, par::CONFIANZA_MIN);
      s = ctl.actualizar(est, dt);

      // Falla de sensores: lecturas imposibles sostenidas.
      if (posicion::lecturas_imposibles(raw_on, NUM_SENSORES, par::ADC_MAX)) {
        if (!falla_activa) { falla_activa = true; t_falla_ms = ahora; }
      } else falla_activa = false;
      ult_buscando = s.buscando;
      ev.linea_perdida = s.linea_perdida;
      hw::led(est.linea_visible);
      const uint32_t dur = micros() - ahora_us;
      if (dur > t_ciclo_max_us) t_ciclo_max_us = dur;
    }
    ev.buscando = ult_buscando;
    ev.falla_sensores = falla_activa && (ahora - t_falla_ms >= FALLA_SENSORES_MS);
  }

  const bool cambio = maquina.actualizar(ev, ahora);
  const Estado n = maquina.estado();

  if (maquina.recien_arrancado()) {
    ParamControl corrida = pc;
    corrida.vbase = pc.vbase * (0.25f + 0.75f * hw::perfil_velocidad());   // perilla: 25 % a 100 %
    ctl.fijar(corrida);
    ctl.reiniciar();
    t_prev_us = micros();
    t_ciclo_max_us = 0;
    falla_activa = false;
    ult_buscando = false;
  }
  if (cambio && n == Estado::CALIBRANDO) cal.reiniciar(NUM_SENSORES);
  if (cambio && e == Estado::CALIBRANDO && n == Estado::LISTO) guardar();
  if (cambio && maquina.motivo() == Motivo::CAL_INSUFICIENTE) Serial.println("calibracion insuficiente: algun sensor no vio blanco y negro");
  if (cambio && (n == Estado::PARADA || n == Estado::ERROR)) ctl.fijar(pc);
  if (cambio) Serial.printf("estado: %s\n", nombre_estado(n));

  if (maquina.motores_habilitados()) {
    if (ciclo_control) {
      float izq = s.izq, der = s.der;
      if (MOTOR_DESDE_BATERIA) {
        izq = compensar_bateria(izq, bateria.voltaje(), V_MOTOR_NOMINAL);
        der = compensar_bateria(der, bateria.voltaje(), V_MOTOR_NOMINAL);
      }
      hw::motores(izq, der);
      if (telemetria && (++ciclos % TELEMETRIA_CADA) == 0)
        Serial.printf("%lu,%.2f,%.3f,%.3f\n", (unsigned long)t_ciclo_max_us, s.error_mm, s.izq, s.der);
    }
  } else {
    hw::motores_apagar();
    led_estado(ahora);
    if (n != Estado::CALIBRANDO) consola();   // la consola nunca corre con el robot en marcha
  }
}
