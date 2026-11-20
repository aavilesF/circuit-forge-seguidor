// Robot de EMERGENCIA (placa perforada, D-V2-40) · ESP32 DevKit 30 pines + DRV8833 + 2 × N20 6 V + 8 TCRT5000 con
// CD74HC4067. Hardware: v2/electronica/prototipo-emergencia/GUIA-FIRMWARE.md y robot_emergencia_unificado.kicad_sch.
//
// Base (EM-07): lógica del firmware HISTÓRICO firmware/robot-casero (posición, PID, control, filtro, motor, estados y
// ajustes, probados en PC), adaptada al hardware vigente: 8 sensores por mux, START en GPIO4, sin zumbador, sin
// ventilador, sin nFAULT, batería medida directo (sin diodo) y motores siempre a 6.0 V (MP1584 U2).
//
// Botones: CAL = calibrar (≤ 15 s, se pasa el robot a mano sobre la línea) · START = arrancar / parar.
// Consola USB a 115200: escribir `ayuda`. Sin WiFi ni Bluetooth (reglamento): no se incluyen WiFi.h ni BluetoothSerial.h.
#include <Preferences.h>

#include "ajustes.h"
#include "config.h"
#include "control.h"
#include "estados.h"
#include "filtro.h"
#include "hw.h"
#include "indicadores.h"
#include "motor.h"
#include "parametros.h"
#include "posicion.h"
#include "utiles.h"

using namespace casero;

static const char* VERSION_FW = "emergencia 1.0 (19 nov 2026)";

static Ajustes aj;
static Maquina maq;
static ControladorLinea ctl(param_por_defecto());
static motor::Accionamiento acc;
static posicion::Geometria geom;
static posicion::Calibracion cal, cal_respaldo;
static bool cal_valida = false;
static filtro::Arreglo filt;
static Preferences nvs;

static int crudo_on[par::MAX_SENSORES], crudo_off[par::MAX_SENSORES];
static float refl[par::MAX_SENSORES], osc[par::MAX_SENSORES];
static posicion::Estimacion est{0.0f, 0.0f, false};
static SalidaControl sal{};
static float vbat = 0.0f, vbat_f = 0.0f;
static bool hay_bat = false, bat_baja = false, bat_crit = false, aviso_bat = false;
static uint32_t t_bat_crit = 0, t_bat_med = 0;
static bool telemetria = false;
static uint32_t t_lectura_us = 0, t_ciclo_max_us = 0, n_ciclos = 0;
static unsigned long t_prev_us = 0;
static bool parar_usb = false;

// Diagnóstico: congela el barrido de sensores para medir con multímetro (`emis 1`, `mux <n>`). No deja arrancar.
static bool diag_emis = false;
static int diag_mux = -1;
static bool diag_activo() { return diag_emis || diag_mux >= 0; }

static util::Boton b_start, b_cal;

// ------------------------------------------------------------------ memoria
static void guardar() {
  Guardado g{};
  g.a = aj;
  g.n_cal = cal.n;
  for (int i = 0; i < MAX_CAL; ++i) {
    g.cal_min[i] = i < cal.n ? cal.minimo[i] : 0.0f;
    g.cal_max[i] = i < cal.n ? cal.maximo[i] : 0.0f;
  }
  sellar(g);
  nvs.begin("emergencia", false);
  nvs.putBytes("g", &g, sizeof(g));
  nvs.end();
}

static bool cargar() {
  Guardado g;
  nvs.begin("emergencia", true);
  const bool ok = nvs.getBytesLength("g") == sizeof(g) && nvs.getBytes("g", &g, sizeof(g)) == sizeof(g) && valido(g);
  nvs.end();
  if (!ok) return false;
  aj = g.a;
  if (g.n_cal == NUM_SENSORES) {
    cal.reiniciar(NUM_SENSORES);
    for (int i = 0; i < NUM_SENSORES; ++i) { cal.minimo[i] = g.cal_min[i]; cal.maximo[i] = g.cal_max[i]; }
    cal_valida = cal.lista(par::RANGO_CAL_MIN);
  }
  return true;
}

static void aplicar_ajustes() {
  ctl.fijar(a_control(aj));
  acc.configurar(a_modelo(aj), a_limites(aj));
  maq.fijar_tiempos(a_tiempos(aj));
}

// ------------------------------------------------------------------ sensores y batería
static void leer_sensores() {
  t_lectura_us = hw::leer_sensores(crudo_on, crudo_off, RESTA_AMBIENTE, (uint32_t)aj.t_emisor_us, (int)aj.sobremuestreo);
  static const posicion::ModoSensor modo = {RESTA_AMBIENTE != 0, LUZ_BAJA_VOLTAJE != 0, par::ADC_MAX};
  for (int i = 0; i < NUM_SENSORES; ++i) refl[i] = posicion::reflectancia(modo, crudo_on[i], crudo_off[i]);
  filt.aplicar(refl, NUM_SENSORES, aj.alfa);
}

static void medir_bateria(uint32_t t) {
  if (t - t_bat_med < 20) return;              // cada 20 ms
  t_bat_med = t;
  const float v = hw::v_bateria();
  hay_bat = v > 3.0f;                          // con solo USB el divisor marca ~0 V
  vbat = hay_bat ? v : 0.0f;
  vbat_f = (vbat_f <= 0.0f || !hay_bat) ? vbat : vbat_f + 0.2f * (vbat - vbat_f);   // ≈ 100 ms
  bat_baja = hay_bat && vbat_f < aj.bat_baja;
  if (hay_bat && vbat_f < aj.bat_critica) { if (!t_bat_crit) t_bat_crit = t ? t : 1; }
  else t_bat_crit = 0;
  bat_crit = t_bat_crit && (t - t_bat_crit > 500);   // la LiPo baja de golpe al acelerar: se exige 0.5 s
  if (bat_baja && !aviso_bat) Serial.printf("AVISO: bateria baja %.2f V (umbral %.2f V)\n", vbat_f, aj.bat_baja);
  aviso_bat = bat_baja;
}

// El DRV8833 se alimenta de +6V_MOT (MP1584 U2). Sin batería (solo USB) no hay voltaje en el puente.
static float v_puente() { return hay_bat ? aj.vm_fijo : 0.0f; }

// ------------------------------------------------------------------ motores
static void salida_motores(float izq, float der, float dt) {
  const float ci = aj.inv_izq > 0.5f ? -izq : izq;
  const float cd = aj.inv_der > 0.5f ? -der : der;
  acc.actualizar(ci, cd, v_puente(), dt);       // tope de PWM, rampa y límite de corriente (motor.h)
  const motor::Decaimiento k = aj.lento > 0.5f ? motor::Decaimiento::LENTO : motor::Decaimiento::RAPIDO;
  for (int m = 0; m < 2; ++m) {
    const motor::Puente p = motor::drv8833(acc.ciclo(m), k);
    hw::puente(m, p.in1, p.in2);
  }
}

static void motores_quietos(bool frenar) {
  acc.reiniciar();
  const motor::Puente p = frenar ? motor::freno() : motor::libre();
  hw::puente(0, p.in1, p.in2);
  hw::puente(1, p.in1, p.in2);
}

// ------------------------------------------------------------------ consola USB
static char linea[64];
static int n_linea = 0;

static void imprimir_ajustes() {
  int n;
  const EntradaAjuste* t = tabla_ajustes(&n);
  for (int i = 0; i < n; ++i) Serial.printf("%s=%g%s", t[i].nombre, *campo(aj, t[i]), (i % 6 == 5) ? "\n" : "  ");
  Serial.println();
}

static void imprimir_pines() {
  Serial.printf("mux S0=%d S1=%d S2=%d S3=%d SIG=%d · EMIT_EN=%d · START=%d CAL=%d · LED=%d · VBAT=%d\n", PIN_MUX_S0,
                PIN_MUX_S1, PIN_MUX_S2, PIN_MUX_S3, PIN_MUX_SIG, PIN_EMISORES, PIN_START, PIN_CAL, PIN_LED, PIN_BATERIA);
  Serial.printf("DRV8833 AIN1=%d AIN2=%d (izq) · BIN1=%d BIN2=%d (der) · nSLEEP=%d · sin nFAULT, zumbador ni ventilador\n",
                PIN_AIN1, PIN_AIN2, PIN_BIN1, PIN_BIN2, PIN_NSLEEP);
  Serial.printf("%d sensores, paso %.2f mm, SEN1 a la %s\n", NUM_SENSORES, PASO_SENSORES_MM,
                SENSORES_INVERTIDOS ? "DERECHA" : "izquierda");
}

static void imprimir_sensores() {
  posicion::normalizar(cal, refl, osc);
  const posicion::Estimacion e = posicion::estimar_posicion(geom, osc, par::UMBRAL_RUIDO, par::CONFIANZA_MIN);
  Serial.print("izq ");
  for (int i = 0; i < NUM_SENSORES; ++i) Serial.printf("%.2f ", osc[i]);
  Serial.printf("der | pos=%.1f mm visible=%d cal=%s\n", e.pos_mm, e.linea_visible, cal_valida ? "si" : "NO");
}

static void imprimir_calibracion() {
  Serial.printf("calibracion %s (contraste minimo %.0f cuentas)\n", cal_valida ? "valida" : "NO valida", par::RANGO_CAL_MIN);
  for (int i = 0; i < cal.n; ++i)
    Serial.printf("  SEN%d (C%d): min=%.0f max=%.0f rango=%.0f\n", i + 1,
                  util::canal_de_sensor(i, NUM_SENSORES, SENSORES_INVERTIDOS != 0), cal.minimo[i], cal.maximo[i],
                  cal.maximo[i] - cal.minimo[i]);
}

static bool hay_tecla() {                       // consume lo recibido; true si llegó algo
  bool hubo = false;
  while (Serial.available()) { Serial.read(); hubo = true; }
  return hubo;
}

static void prueba_motor(float a, float b, int ms) {
  if (!hay_bat) { Serial.println("sin bateria (solo USB): los motores no tienen voltaje"); return; }
  if (maq.estado() == Estado::CALIBRACION) { Serial.println("termina la calibracion primero"); return; }
  if (ms < 50) ms = 50;
  if (ms > 3000) ms = 3000;
  Serial.println("motores girando: envia cualquier tecla para parar");
  hw::driver_despierto(true);
  delay(2);                                    // despertar del DRV8833 (tWAKE)
  acc.reiniciar();
  const uint32_t t0 = millis();
  uint32_t tp = micros();
  bool cortado = false;
  while (millis() - t0 < (uint32_t)ms) {       // pasa por el tope, la rampa y el límite de corriente
    if (hay_tecla()) { cortado = true; break; }
    const uint32_t ahora = micros();
    const float dt = (ahora - tp) * 1e-6f;
    tp = ahora;
    salida_motores(a, b, dt > 0.0f ? dt : 1e-3f);
    delay(2);
  }
  const float c0 = acc.ciclo(0), c1 = acc.ciclo(1), i0 = acc.corriente(0), i1 = acc.corriente(1);
  motores_quietos(true);
  delay(150);
  motores_quietos(false);
  hw::driver_despierto(maq.despierto(millis()));
  t_prev_us = micros();                        // el ciclo de control no cuenta este tiempo como atraso
  Serial.printf("%s (ciclo final izq=%.2f der=%.2f, corriente estimada %.2f/%.2f A)\n", cortado ? "PARADO" : "ok", c0, c1,
                i0, i1);
}

static void leer_canal_diag(int c) {
  const int n = 16;
  const bool antes = hw::emisores_encendidos();
  hw::emisores(false);
  delayMicroseconds((uint32_t)aj.t_emisor_us);
  const int off = hw::leer_canal(c, n);
  hw::emisores(true);
  delayMicroseconds((uint32_t)aj.t_emisor_us);
  const int on = hw::leer_canal(c, n);
  hw::emisores(antes);
  Serial.printf("C%d: LED encendidos=%d apagados=%d diferencia=%d (negro = alto, blanco = bajo)\n", c, on, off, off - on);
}

static void ejecutar(char* l) {
  char* c = strtok(l, " ");
  if (!c) return;
  if (!strcmp(c, "ayuda") || !strcmp(c, "?")) {
    Serial.println("estado | ver | pines | get | set <clave> <valor> | save | load | defecto");
    Serial.println("sens | crudo | cal | canal <0-15> | mux <0-15>|off | emis 0/1 | botones | bat | perf | tel 0/1");
    Serial.println("m <izq> <der> [ms]  prueba de motores, -1..1 (RUEDAS EN EL AIRE) | stop");
    Serial.println("En marcha la consola no responde: cualquier tecla PARA el robot.");
  } else if (!strcmp(c, "ver")) Serial.println(VERSION_FW);
  else if (!strcmp(c, "estado")) {
    Serial.printf("estado=%s error=%d cal=%s bateria=%.2f V%s%s\n", nombre(maq.estado()), (int)maq.error(),
                  cal_valida ? "si" : "NO", vbat_f, hay_bat ? (bat_baja ? " (BAJA)" : "") : " (solo USB)",
                  diag_activo() ? " · DIAGNOSTICO (emis/mux): START bloqueado" : "");
  } else if (!strcmp(c, "pines")) imprimir_pines();
  else if (!strcmp(c, "get")) imprimir_ajustes();
  else if (!strcmp(c, "set")) {
    char* k = strtok(nullptr, " ");
    char* v = strtok(nullptr, " ");
    if (!k || !v || !fijar(aj, k, atof(v))) Serial.println("uso: set <clave> <valor> (clave de `get`, dentro de su rango)");
    else { aplicar_ajustes(); Serial.printf("%s=%g (falta `save` para guardarlo)\n", k, atof(v)); }
  } else if (!strcmp(c, "save")) { guardar(); Serial.println("guardado"); }
  else if (!strcmp(c, "load")) { Serial.println(cargar() ? "cargado" : "no hay datos validos"); aplicar_ajustes(); }
  else if (!strcmp(c, "defecto")) { aj = Ajustes(); aplicar_ajustes(); Serial.println("valores por defecto (falta `save`)"); }
  else if (!strcmp(c, "sens")) imprimir_sensores();
  else if (!strcmp(c, "cal")) imprimir_calibracion();
  else if (!strcmp(c, "crudo")) {
    Serial.print("on : "); for (int i = 0; i < NUM_SENSORES; ++i) Serial.printf("%4d ", crudo_on[i]);
    Serial.print("\noff: "); for (int i = 0; i < NUM_SENSORES; ++i) Serial.printf("%4d ", crudo_off[i]);
    Serial.println("   (orden: izquierda -> derecha)");
  } else if (!strcmp(c, "canal")) {
    char* v = strtok(nullptr, " ");
    const int n = v ? atoi(v) : -1;
    if (!v || n < 0 || n > 15) Serial.println("uso: canal <0-15>   (SEN1 = C0 ... SEN8 = C7)");
    else leer_canal_diag(n);
  } else if (!strcmp(c, "mux")) {
    char* v = strtok(nullptr, " ");
    if (v && !strcmp(v, "off")) { diag_mux = -1; Serial.println("mux libre: vuelve el barrido"); }
    else if (v && atoi(v) >= 0 && atoi(v) <= 15) {
      diag_mux = atoi(v);
      hw::leer_canal(diag_mux, 1);
      const util::BitsMux b = util::bits_mux(diag_mux);
      Serial.printf("mux fijo en C%d (S3..S0 = %d%d%d%d). Mide SIG con el multimetro. `mux off` para salir\n", diag_mux, b.s3,
                    b.s2, b.s1, b.s0);
    } else Serial.println("uso: mux <0-15> | mux off");
  } else if (!strcmp(c, "emis")) {
    char* v = strtok(nullptr, " ");
    diag_emis = v && atoi(v);
    hw::emisores(diag_emis);
    Serial.printf("emisores %s%s\n", diag_emis ? "ENCENDIDOS fijos" : "en modo normal",
                  diag_emis ? " (barrido detenido; `emis 0` para salir)" : "");
  } else if (!strcmp(c, "botones")) {
    Serial.printf("START=%s CAL=%s (lectura directa del pin)\n", hw::boton_start() ? "OPRIMIDO" : "suelto",
                  hw::boton_cal() ? "OPRIMIDO" : "suelto");
  } else if (!strcmp(c, "bat")) {
    Serial.printf("bateria %.2f V (pin GPIO36 %.0f mV x %.3f)%s · baja < %.2f V, critica < %.2f V\n", vbat_f,
                  hw::mv_pin_bateria(), DIVISOR_BATERIA, hay_bat ? "" : " · solo USB", aj.bat_baja, aj.bat_critica);
  } else if (!strcmp(c, "perf")) {
    Serial.printf("lectura de sensores %lu us, ciclo maximo %lu us (periodo %lu us, limite en marcha %lu us)\n",
                  (unsigned long)t_lectura_us, (unsigned long)t_ciclo_max_us, par::PERIODO_CONTROL_US, par::CICLO_MAX_US);
    t_ciclo_max_us = 0;
  } else if (!strcmp(c, "tel")) { char* v = strtok(nullptr, " "); telemetria = v && atoi(v); }
  else if (!strcmp(c, "m")) {
    char* a = strtok(nullptr, " "); char* b = strtok(nullptr, " "); char* ms = strtok(nullptr, " ");
    if (!a || !b) Serial.println("uso: m <izq> <der> [ms]   ej. m 0.3 0");
    else prueba_motor(atof(a), atof(b), ms ? atoi(ms) : 1000);
  } else if (!strcmp(c, "stop")) { motores_quietos(false); hw::driver_despierto(false); Serial.println("motores sueltos"); }
  else Serial.println("comando desconocido (escribe: ayuda)");
}

static void consola() {
  while (Serial.available()) {
    const char ch = (char)Serial.read();
    if (ch == '\r') continue;
    if (ch == '\n') { linea[n_linea] = 0; n_linea = 0; ejecutar(linea); }
    else if (n_linea < (int)sizeof(linea) - 1) linea[n_linea++] = ch;
  }
}

// ------------------------------------------------------------------ setup / loop
void setup() {
  hw::iniciar();                               // primero: puente dormido y entradas en 0
  Serial.begin(115200);
  b_start.ms_estable = b_cal.ms_estable = ANTIRREBOTE_MS;
  cal.reiniciar(NUM_SENSORES);
  const bool hay = cargar();
  geom = posicion::geometria_recta(NUM_SENSORES, PASO_SENSORES_MM, DIST_SENSOR_EJE_MM);
  aplicar_ajustes();
  maq.reiniciar(millis());
  t_prev_us = micros();
  Serial.printf("\nRobot de emergencia · %s · %d sensores con CD74HC4067 · ajustes %s · calibracion %s. Escribe 'ayuda'.\n",
                VERSION_FW, NUM_SENSORES, hay ? "guardados" : "por defecto", cal_valida ? "guardada" : "NO");
}

void loop() {
  const uint32_t t = millis();
  if (maq.motores()) { if (hay_tecla()) parar_usb = true; }   // en marcha: cualquier byte por USB = parar
  else consola();

  const unsigned long ahora = micros();
  if (ahora - t_prev_us < par::PERIODO_CONTROL_US) return;
  const unsigned long dt_us = ahora - t_prev_us;
  const float dt = dt_us * 1e-6f;              // dt real, no el nominal
  t_prev_us = ahora;

  // ---- entradas
  if (!diag_activo()) leer_sensores();         // en diagnóstico se congela el barrido (emis/mux fijos)
  medir_bateria(t);
  const Estado antes = maq.estado();
  if (antes == Estado::CALIBRACION) cal.muestrear(refl);
  posicion::normalizar(cal, refl, osc);
  est = posicion::estimar_posicion(geom, osc, par::UMBRAL_RUIDO, par::CONFIANZA_MIN);
  if (maq.motores()) sal = ctl.actualizar(est, dt);

  Entradas in;
  in.start = b_start.pulso(hw::boton_start(), t);
  in.cal = b_cal.pulso(hw::boton_cal(), t);
  if (diag_activo() && (in.start || in.cal)) {
    Serial.println("diagnostico activo (emis/mux): sal con `emis 0` y `mux off` antes de usar START o CAL");
    in.start = in.cal = false;
  }
  in.cal_lista = antes == Estado::CALIBRACION && cal.lista(par::RANGO_CAL_MIN);
  in.cal_valida = cal_valida;
  in.linea_visible = est.linea_visible;
  in.buscando = maq.motores() && sal.buscando;
  in.linea_perdida = maq.motores() && sal.linea_perdida;
  in.hay_bateria = hay_bat;
  in.bat_critica = bat_crit;
  in.parar = parar_usb;
  in.falla_ciclo = maq.motores() && dt_us > par::CICLO_MAX_US;
  parar_usb = false;

  // ---- estado y acciones al entrar
  const Estado e = maq.paso(in, t);
  if (maq.entro()) {
    if (e == Estado::CALIBRACION) { cal_respaldo = cal; cal.reiniciar(NUM_SENSORES); }
    if (antes == Estado::CALIBRACION) {
      if (maq.fin_cal() == FinCal::BIEN) { cal_valida = true; guardar(); }
      else cal = cal_respaldo;                 // faltó contraste: se conserva la calibración anterior
      Serial.printf("calibracion %s\n", maq.fin_cal() == FinCal::BIEN ? "OK (guardada)" : "INSUFICIENTE: repetir");
    }
    if (e == Estado::SIGUIENDO && antes == Estado::LISTO) { ctl.fijar(a_control(aj)); ctl.reiniciar(); acc.reiniciar(); sal = SalidaControl{}; }
    if (e == Estado::ERROR)
      Serial.printf("ERROR %d (%s)\n", (int)maq.error(), maq.error() == Error::BATERIA ? "bateria critica" : "ciclo de control atrasado");
    if (in.parar && e == Estado::PARADA) Serial.println("parada por la consola USB");
    Serial.printf("-> %s\n", nombre(e));
  } else if (maq.rechazo() && in.start) {
    Serial.println(!cal_valida ? "START rechazado: falta calibrar (CAL)" : "START rechazado: sin bateria o bateria critica");
  }

  // ---- salidas
  hw::driver_despierto(maq.despierto(t));
  if (maq.motores()) salida_motores(sal.izq, sal.der, dt);
  else motores_quietos(maq.frenando(t));

  Contexto cx{e, maq.error(), maq.desde(t), t, est.linea_visible, maq.fin_cal(), t - maq.t_fin_cal(), maq.rechazo(),
              t - maq.t_rechazo(), bat_baja, a_tiempos(aj).cal_max_ms};
  hw::led(indicar(cx).led);

  if (telemetria && maq.motores() && (++n_ciclos % 4 == 0))
    Serial.printf("%.1f,%d,%.3f,%.3f,%.2f\n", est.pos_mm, (int)est.linea_visible, acc.ciclo(0), acc.ciclo(1), vbat_f);
  const uint32_t dur = micros() - ahora;
  if (dur > t_ciclo_max_us) t_ciclo_max_us = dur;
}
