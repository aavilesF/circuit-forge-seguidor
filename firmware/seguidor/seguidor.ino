// Seguidor de línea - Circuit Forge - ESP32 (Arduino framework).
// Toda la lógica de seguimiento está en posicion.* / pid.* / control.* (C++ puro, probada en PC).
// Este archivo solo une el hardware con esa lógica y maneja el estado del robot.
//
// Estados:  ESPERA -> (CAL) -> CALIBRANDO -> LISTO -> (START) -> SIGUIENDO -> PARADA
//
// NO incluir WiFi.h ni BluetoothSerial.h: el reglamento prohíbe comunicación inalámbrica.
#include <Preferences.h>
#include "pines.h"
#include "parametros.h"
#include "posicion.h"
#include "pid.h"
#include "control.h"
#include "hardware.h"

enum class Estado { ESPERA, CALIBRANDO, LISTO, SIGUIENDO, PARADA };

static Estado estado = Estado::ESPERA;
static posicion::Geometria geom;
static posicion::Calibracion cal;
static ParamControl pc;
static ControladorLinea ctl(param_por_defecto());
static Preferences nvs;

static float refl[par::MAX_SENSORES];
static float osc[par::MAX_SENSORES];
static unsigned long t_prev_us = 0, t_estado_ms = 0;
static bool telemetria = false;
static float vbase_perfil = 0.4f;
static posicion::Estimacion ultima_est{0, 0, false};

// ---------------------------------------------------------------- utilidades
static void cambiar(Estado e) { estado = e; t_estado_ms = millis(); }

static bool flanco_boton(bool (*leer)(), bool& previo) {
  bool ahora = leer();
  bool pulso = ahora && !previo;
  previo = ahora;
  return pulso;
}

static void parpadeo(unsigned periodo_ms) { hw::led((millis() / (periodo_ms / 2)) % 2 == 0); }

static void guardar() {
  nvs.begin("seguidor", false);
  nvs.putBytes("pc", &pc, sizeof(pc));
  nvs.putBytes("cal", &cal, sizeof(cal));
  nvs.end();
}

static void cargar() {
  nvs.begin("seguidor", true);
  if (nvs.getBytesLength("pc") == sizeof(pc)) nvs.getBytes("pc", &pc, sizeof(pc));
  if (nvs.getBytesLength("cal") == sizeof(cal)) {
    nvs.getBytes("cal", &cal, sizeof(cal));
    if (cal.n != NUM_SENSORES) cal.reiniciar(NUM_SENSORES);  // perfil de sensor distinto
  }
  nvs.end();
}

// ---------------------------------------------------------------- consola serie (USB)
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

static void consola() {
  if (!Serial.available()) return;
  String l = Serial.readStringUntil('\n'); l.trim();
  if (l.length() == 0) return;
  if (estado == Estado::SIGUIENDO) { return; }          // sin comandos mientras corre
  if (l == "ayuda") {
    Serial.println("comandos: get | set <clave> <valor> | save | load | defecto | sens | crudo | bat | tel 0/1 | m <izq> <der>");
    Serial.println("claves: kp ki kd vbase freno error_ref vmin_rel u_max");
  } else if (l == "get") imprimir_parametros();
  else if (l == "save") { guardar(); Serial.println("guardado"); }
  else if (l == "load") { cargar(); ctl.fijar(pc); imprimir_parametros(); }
  else if (l == "defecto") { pc = param_por_defecto(); ctl.fijar(pc); imprimir_parametros(); }
  else if (l == "bat") Serial.printf("bateria: %.2f V\n", hw::voltaje_bateria());
  else if (l == "crudo") { int raw[par::MAX_SENSORES]; hw::leer_crudo(raw); for (int i = 0; i < NUM_SENSORES; ++i) Serial.printf("%d ", raw[i]); Serial.println(); }
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
  } else if (l.startsWith("m ")) {   // prueba de motores (ruedas en el aire): m 0.3 0.3
    int sp = l.indexOf(' ', 2);
    float a = l.substring(2, sp).toFloat(), b = l.substring(sp + 1).toFloat();
    hw::motores(a, b); delay(1000); hw::motores_apagar(); Serial.println("ok");
  } else Serial.println("comando desconocido (escribe: ayuda)");
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
  Serial.println("Circuit Forge - seguidor listo. Escribe 'ayuda'.");
  imprimir_parametros();
}

void loop() {
  static bool prev_start = false, prev_cal = false;
  const bool p_start = flanco_boton(hw::boton_start, prev_start);
  const bool p_cal = flanco_boton(hw::boton_cal, prev_cal);

  switch (estado) {
    case Estado::ESPERA:
      parpadeo(1000);
      consola();
      if (p_cal) { cal.reiniciar(NUM_SENSORES); cambiar(Estado::CALIBRANDO); }
      else if (p_start && cal.lista(par::RANGO_CAL_MIN)) cambiar(Estado::LISTO);  // calibración guardada
      break;

    case Estado::CALIBRANDO: {
      // Se mueve el robot a mano para que cada sensor vea blanco y negro.
      parpadeo(150);
      hw::leer_reflectancia(refl);
      cal.muestrear(refl);
      const bool tiempo = millis() - t_estado_ms > 10000;   // el reglamento da 15 s en total
      if (p_cal || tiempo) {
        if (cal.lista(par::RANGO_CAL_MIN)) { guardar(); cambiar(Estado::LISTO); }
        else { Serial.println("calibracion insuficiente: algun sensor no vio blanco y negro"); cambiar(Estado::ESPERA); }
      }
      break;
    }

    case Estado::LISTO:
      hw::led(true);
      consola();
      vbase_perfil = 0.25f + 0.75f * hw::perfil_velocidad();   // perilla: 25 % a 100 % de vbase de la consola
      if (p_start) {
        if (hw::voltaje_bateria() < BATERIA_MIN_V) { Serial.println("bateria baja: no arranca"); break; }
        ParamControl corrida = pc;
        corrida.vbase = pc.vbase * vbase_perfil;
        ctl.fijar(corrida);
        ctl.reiniciar();
        t_prev_us = micros();
        cambiar(Estado::SIGUIENDO);
      }
      if (p_cal) cambiar(Estado::ESPERA);
      break;

    case Estado::SIGUIENDO: {
      const unsigned long ahora = micros();
      if (ahora - t_prev_us < par::PERIODO_CONTROL_US) break;
      const float dt = (ahora - t_prev_us) * 1e-6f;           // dt REAL, no el nominal
      t_prev_us = ahora;

      hw::leer_reflectancia(refl);
      posicion::normalizar(cal, refl, osc);
      ultima_est = posicion::estimar_posicion(geom, osc, par::UMBRAL_RUIDO, par::CONFIANZA_MIN);
      const SalidaControl s = ctl.actualizar(ultima_est, dt);

      if (s.linea_perdida || p_start || hw::voltaje_bateria() < BATERIA_MIN_V - 0.4f) {
        hw::motores_apagar();
        ctl.fijar(pc);
        cambiar(Estado::PARADA);
        break;
      }
      hw::motores(s.izq, s.der);
      hw::led(ultima_est.linea_visible);
      if (telemetria) Serial.printf("%.0f,%.2f,%.3f,%.3f\n", dt * 1e6f, ultima_est.pos_mm, s.izq, s.der);
      break;
    }

    case Estado::PARADA:
      hw::motores_apagar();
      parpadeo(300);
      consola();
      if (p_cal || p_start) cambiar(Estado::LISTO);
      break;
  }
}
