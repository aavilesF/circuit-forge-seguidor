// Speed Follower - Circuit Forge - firmware de PRUEBAS (ESP32, Arduino).
// Solo orquesta: lee el hardware, alimenta la lógica pura y aplica sus decisiones.
//   sf_logica.*  control C2 (PD + feed-forward + perfil de velocidad)   C++ puro, verificado contra Python
//   posicion.*   calibración (mín/máx por sensor) y normalización        C++ puro, probado en PC
//   estados.*    máquina de estados, botones, batería                    C++ puro, probado en PC
//   hardware_sf.* pines, ADC, PWM, driver DRV8833 o TB6612               depende del ESP32
// Los motores se alimentan directo de la batería 2S; el feed-forward ya divide entre Vbat,
// así que no hay "compensación" aparte. (Este firmware es independiente de firmware/seguidor
// y NO toca su bandera MOTOR_DESDE_BATERIA.)
// NO incluir WiFi.h ni BluetoothSerial.h: el reglamento prohíbe comunicación inalámbrica.
#include <Preferences.h>
#include "pines_sf.h"
#include "parametros.h"
#include "posicion.h"
#include "estados.h"
#include "sf_logica.h"
#include "hardware_sf.h"

static constexpr uint32_t VERSION_NVS = 2;              // subir si cambia ParamSF o Calibracion (2: fuente_k)
static constexpr uint32_t CAL_MAX_MS = 10000;           // reglamento: 15 s para calibrar y colocar
static constexpr uint32_t BATERIA_PERIODO_MS = 20;
static constexpr uint32_t FALLA_SENSORES_MS = 300;
static constexpr uint32_t TELEMETRIA_CADA = 20;         // 25 Hz a 500 Hz
static constexpr float V_BAT_MIN_FF = 5.0f;             // si la lectura es absurda, no dividir entre ~0

static const sf::Robot robot = robot_configurado();
static sf::ParamSF ps = parametros_maestros();
static sf::ControlSF ctl(ps, robot);
static posicion::Calibracion cal;
static MaquinaEstados maquina;
static Boton boton_start, boton_cal;
static MonitorBateria bateria(BATERIA_MIN_V, BATERIA_CRITICA_V, 300);
static Preferences nvs;

static float refl[par::MAX_SENSORES], osc[par::MAX_SENSORES];
static int raw_on[par::MAX_SENSORES];
static uint32_t t_prev_us = 0, t_bat_ms = 0, t_falla_ms = 0, ciclos = 0, t_ciclo_max_us = 0;
static bool falla_activa = false, telemetria = false, ult_buscando = false;

static float v_bat_ff() { const float v = bateria.voltaje(); return v > V_BAT_MIN_FF ? v : 8.4f; }

// ---------------------------------------------------------------- memoria no volátil
static void guardar() {
  nvs.begin("speedf", false);
  nvs.putUInt("ver", VERSION_NVS);
  nvs.putBytes("ps", &ps, sizeof(ps));
  nvs.putBytes("cal", &cal, sizeof(cal));
  nvs.end();
}
static void cargar() {
  nvs.begin("speedf", true);
  if (nvs.getUInt("ver", 0) == VERSION_NVS) {
    if (nvs.getBytesLength("ps") == sizeof(ps)) nvs.getBytes("ps", &ps, sizeof(ps));
    if (nvs.getBytesLength("cal") == sizeof(cal)) {
      nvs.getBytes("cal", &cal, sizeof(cal));
      if (cal.n != NUM_SENSORES) cal.reiniciar(NUM_SENSORES);
    }
  }
  nvs.end();
}

// ---------------------------------------------------------------- consola serie (USB, solo con el robot detenido)
static void imprimir_parametros() {
  Serial.printf("v_max=%.2f a_lat=%.2f a_lon=%.2f k_pp=%.2f kp=%.1f kd=%.2f tau_d=%.4f tau_k=%.3f "
                "inv=%d e_crit=%.2f d_inv=%.2f ff_acel=%d t_perdida=%.2f\n",
                ps.v_max, ps.a_lat, ps.a_lon, ps.k_pp, ps.kp, ps.kd, ps.tau_d, ps.tau_k,
                ps.permitir_inversion, ps.e_critico, ps.d_inv, ps.ff_acel, ps.t_perdida);
}
static bool poner(const String& k, float v) {
  if (k == "v_max") ps.v_max = v; else if (k == "a_lat") ps.a_lat = v; else if (k == "a_lon") ps.a_lon = v;
  else if (k == "k_pp") ps.k_pp = v; else if (k == "kp") ps.kp = v; else if (k == "kd") ps.kd = v;
  else if (k == "tau_d") ps.tau_d = v; else if (k == "tau_k") ps.tau_k = v;
  else if (k == "inv") ps.permitir_inversion = v != 0; else if (k == "e_crit") ps.e_critico = v;
  else if (k == "d_inv") ps.d_inv = v; else if (k == "ff_acel") ps.ff_acel = v != 0;
  else if (k == "t_perdida") ps.t_perdida = v; else if (k == "fuente_k") ps.fuente_k = (int)v; else if (k == "piso") ps.piso = v; else return false;
  ctl.fijar(ps);
  return true;
}
static void leer_normalizado() { hw::leer_reflectancia(refl, raw_on); posicion::normalizar(cal, refl, osc); }

static void consola() {
  if (!Serial.available()) return;
  String l = Serial.readStringUntil('\n'); l.trim();
  if (l.length() == 0) return;
  if (l == "ayuda") {
    Serial.println("comandos: get | set <clave> <valor> | save | load | defecto | sens | crudo | bat | diag | tel 0/1 | m <izq> <der> [ms]");
    Serial.println("claves: v_max a_lat a_lon k_pp kp kd tau_d tau_k inv e_crit d_inv ff_acel t_perdida fuente_k piso");
  } else if (l == "get") imprimir_parametros();
  else if (l == "save") { guardar(); Serial.println("guardado"); }
  else if (l == "load") { cargar(); ctl.fijar(ps); imprimir_parametros(); }
  else if (l == "defecto") { ps = parametros_maestros(); ctl.fijar(ps); imprimir_parametros(); }
  else if (l == "bat") Serial.printf("bateria: %.2f V (filtrada)\n", bateria.voltaje());
  else if (l == "diag") {
    const uint32_t t0 = micros(); leer_normalizado(); const uint32_t t1 = micros();
    Serial.printf("lectura+normalizacion de %d sensores: %lu us | ciclo max en marcha: %lu us | bateria %.2f V | estado %s\n",
                  NUM_SENSORES, (unsigned long)(t1 - t0), (unsigned long)t_ciclo_max_us, bateria.voltaje(),
                  nombre_estado(maquina.estado()));
  } else if (l == "crudo") {
    hw::leer_crudo(raw_on);
    for (int i = 0; i < NUM_SENSORES; ++i) Serial.printf("%d ", raw_on[i]);
    Serial.println();
  } else if (l == "sens") {
    leer_normalizado();
    for (int i = 0; i < NUM_SENSORES; ++i) Serial.printf("%.2f ", osc[i]);
    const sf::Lectura le = sf::estimar_coord(osc, cfg::SENSOR_Y, NUM_SENSORES, cfg::UMBRAL);
    Serial.printf("| e=%.1f mm visible=%d borde=%d\n", le.e * 1000.0f, le.visible, le.borde);
  } else if (l.startsWith("tel ")) telemetria = l.substring(4).toInt() != 0;
  else if (l.startsWith("set ")) {
    const int sp = l.indexOf(' ', 4);
    if (sp < 0 || !poner(l.substring(4, sp), l.substring(sp + 1).toFloat())) Serial.println("uso: set <clave> <valor>");
    else imprimir_parametros();
  } else if (l.startsWith("m ")) {   // ruedas en el aire: m 0.3 0.3 [ms]. Ciclo relativo a la batería.
    const int sp = l.indexOf(' ', 2);
    if (sp < 0) { Serial.println("uso: m <izq> <der> [ms]"); return; }
    const int sp2 = l.indexOf(' ', sp + 1);
    const float a = l.substring(2, sp).toFloat();
    const float b = (sp2 < 0 ? l.substring(sp + 1) : l.substring(sp + 1, sp2)).toFloat();
    long ms = sp2 < 0 ? 1000 : l.substring(sp2 + 1).toInt();
    ms = ms < 0 ? 0 : (ms > 5000 ? 5000 : ms);
    hw::motores(a, b); delay((unsigned long)ms); hw::motores_apagar(); Serial.println("ok");
  } else Serial.println("comando desconocido (escribe: ayuda)");
}

// ---------------------------------------------------------------- LED según estado
static void led_estado(uint32_t ahora) {
  switch (maquina.estado()) {
    case Estado::ESPERA:     hw::led((ahora / 500) % 2); break;
    case Estado::CALIBRANDO: hw::led((ahora / 75) % 2); break;
    case Estado::LISTO:      hw::led(maquina.motivo() == Motivo::BATERIA_ARRANQUE ? (ahora / 150) % 4 == 0 : true); break;
    case Estado::PARADA:     hw::led((ahora / 150) % 2); break;
    case Estado::ERROR:      hw::led((ahora / 100) % 10 < 2); break;
    default: break;
  }
}

// ---------------------------------------------------------------- setup / loop
void setup() {
  Serial.begin(115200);
  hw::iniciar();
  cal.reiniciar(NUM_SENSORES);
  cargar();
  ctl.fijar(ps);
  for (int i = 0; i < 20; ++i) bateria.muestra(hw::voltaje_bateria(), millis());
  Serial.println("Circuit Forge - Speed Follower (firmware de pruebas). Escribe 'ayuda'.");
  imprimir_parametros();
}

void loop() {
  const uint32_t ahora = millis();
  Eventos ev;
  ev.start = boton_start.actualizar(hw::boton_start(), ahora);
  ev.cal = boton_cal.actualizar(hw::boton_cal(), ahora);
  if (ahora - t_bat_ms >= BATERIA_PERIODO_MS) { t_bat_ms = ahora; bateria.muestra(hw::voltaje_bateria(), ahora); }
  ev.bateria_permite = bateria.permite_arranque();
  ev.bateria_critica = bateria.critica();
  ev.cal_guardada_ok = cal.lista(par::RANGO_CAL_MIN);

  const Estado e = maquina.estado();
  if (e == Estado::CALIBRANDO) {
    hw::leer_reflectancia(refl, nullptr);
    cal.muestrear(refl);
    ev.cal_suficiente = cal.lista(par::RANGO_CAL_MIN);
    ev.cal_tiempo_agotado = ahora - maquina.desde_ms() > CAL_MAX_MS;
  }

  bool ciclo_control = false;
  sf::Salida s{};
  sf::Lectura le{};
  if (maquina.motores_habilitados()) {
    const uint32_t ahora_us = micros();
    if (ahora_us - t_prev_us >= cfg::PERIODO_MIN_US) {
      ciclo_control = true;
      const float dt = (ahora_us - t_prev_us) * 1e-6f;   // dt real
      t_prev_us = ahora_us;
      leer_normalizado();
      le = sf::estimar_coord(osc, cfg::SENSOR_Y, NUM_SENSORES, cfg::UMBRAL);
      s = ctl.actualizar(le, dt, v_bat_ff());
      if (posicion::lecturas_imposibles(raw_on, NUM_SENSORES, par::ADC_MAX)) {
        if (!falla_activa) { falla_activa = true; t_falla_ms = ahora; }
      } else falla_activa = false;
      ult_buscando = !le.visible;
      ev.linea_perdida = s.linea_perdida;
      hw::led(le.visible);
      const uint32_t dur = micros() - ahora_us;
      if (dur > t_ciclo_max_us) t_ciclo_max_us = dur;
    }
    ev.buscando = ult_buscando;
    ev.falla_sensores = falla_activa && (ahora - t_falla_ms >= FALLA_SENSORES_MS);
  }

  const bool cambio = maquina.actualizar(ev, ahora);
  const Estado n = maquina.estado();
  if (maquina.recien_arrancado()) {
    ctl.fijar(ps);
    ctl.reiniciar();
    t_prev_us = micros();
    t_ciclo_max_us = 0;
    falla_activa = false;
    ult_buscando = false;
  }
  if (cambio && n == Estado::CALIBRANDO) cal.reiniciar(NUM_SENSORES);
  if (cambio && e == Estado::CALIBRANDO && n == Estado::LISTO) guardar();
  if (cambio && maquina.motivo() == Motivo::CAL_INSUFICIENTE) Serial.println("calibracion insuficiente: algun sensor no vio blanco y negro");
  if (cambio) Serial.printf("estado: %s\n", nombre_estado(n));

  if (maquina.motores_habilitados()) {
    if (ciclo_control) {
      hw::motores(s.izq, s.der);
      if (telemetria && (++ciclos % TELEMETRIA_CADA) == 0)
        Serial.printf("%lu,%.1f,%.2f,%.3f,%.3f,%d\n", (unsigned long)t_ciclo_max_us, le.e * 1000.0f, s.v_cmd, s.izq, s.der, s.inversion);
    }
  } else {
    hw::motores_apagar();
    led_estado(ahora);
    if (n != Estado::CALIBRANDO) consola();
  }
}
