// Robot de EMERGENCIA (placa perforada, D-V2-40) · ESP32 DevKit 30 pines + DRV8833 + 2 × N20 6 V + 8 TCRT5000 con
// CD74HC4067. Hardware: v2/electronica/prototipo-emergencia/GUIA-FIRMWARE.md y robot_emergencia_unificado.kicad_sch.
//
// Base (EM-07): lógica probada en PC (posición, PID, control, filtro, motor) del firmware histórico, adaptada al
// hardware vigente: 8 sensores por mux, START en GPIO4, sin zumbador, sin ventilador, sin nFAULT, batería medida
// directo (sin diodo) y motores a +6V_MOT (MP1584 U2).
//
// Ciclo de control a 400 Hz: leer 8 sensores (luz ambiente restada, sobremuestreo, mediana + pasa-bajas) →
// posición de la línea → PID con freno en curva, retención en huecos y búsqueda → tope de PWM, rampas y límite de
// corriente → DRV8833 en decaimiento lento.
//
// Botones: CAL = calibrar (≤ 15 s, se pasa el robot a mano sobre la línea) · START = arrancar (tras t_arranque) /
// parar. Consola USB a 115200, fin de línea "\n": escribir `ayuda`. En marcha, cualquier tecla PARA el robot.
// Sin WiFi ni Bluetooth (reglamento): no se incluyen WiFi.h, BluetoothSerial.h ni BLE.
#include <Preferences.h>

#include "ajustes.h"
#include "autocal.h"
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

using namespace robot;

static const char* VERSION_FW = "emergencia 2.1 (20 nov 2026)";

static Ajustes aj;
static Turbo tb;                       // turbo de recta: clave de memoria propia ("t")
static Maquina maq;
static ControladorLinea ctl(param_por_defecto());
static motor::Accionamiento acc;
static posicion::Geometria geom;
static posicion::Calibracion cal, cal_respaldo;
static bool cal_valida = false;
static filtro::Arreglo filt;
static Preferences nvs;
static hw::ConfigLectura cfg_lect;
static uint32_t mask = 0xFFu;
static bool inv_aplicado = SENSORES_INVERTIDOS != 0;

static int crudo_on[par::MAX_SENSORES], crudo_off[par::MAX_SENSORES];
static float refl[par::MAX_SENSORES], osc[par::MAX_SENSORES];
static posicion::Estimacion est{0.0f, 0.0f, false};
static int n_oscuros = 0;
static SalidaControl sal{};
static float vbat_f = 0.0f;
static bool hay_bat = false, bat_baja = false, bat_crit = false, aviso_bat = false, bat_alta = false, aviso_alta = false;
static uint32_t t_bat_crit = 0, t_bat_med = 0, t_todo_negro = 0;
static bool telemetria = false, armando_antes = false;
static uint32_t t_lectura_us = 0, t_ciclo_max_us = 0, n_ciclos = 0;
static unsigned long t_prev_us = 0;
static bool parar_usb = false, cal_consola = false, vigilante_ok = false;

// Diagnóstico: congela el barrido de sensores para medir con multímetro (`emis 1`, `mux <n>`). No deja arrancar.
static bool diag_emis = false;
static int diag_mux = -1;
static bool diag_activo() { return diag_emis || diag_mux >= 0; }

enum class Monitor : uint8_t { NADA, SENS, CRUDO, POS, BAT, BOT };
static Monitor monitor = Monitor::NADA;
static uint32_t t_monitor = 0;

static util::Boton b_start, b_cal;

// ------------------------------------------------------------------ calibración y memoria
static void actualizar_cal_valida() { cal_valida = util::cal_lista(cal, aj.contraste, mask); }

static void espejar_calibracion() {       // inv_sens cambió: el sensor lógico i pasa a ser el n−1−i
  for (int i = 0, j = cal.n - 1; i < j; ++i, --j) {
    const float a = cal.minimo[i], b = cal.maximo[i];
    cal.minimo[i] = cal.minimo[j]; cal.maximo[i] = cal.maximo[j];
    cal.minimo[j] = a; cal.maximo[j] = b;
  }
}

static void aplicar_ajustes() {
  ctl.fijar(a_control(aj, tb));
  acc.configurar(a_modelo(aj), a_limites(aj));
  maq.fijar_tiempos(a_tiempos(aj));
  geom = posicion::geometria_recta(NUM_SENSORES, aj.paso_mm, DIST_SENSOR_EJE_MM);
  mask = mascara(aj);
  const bool inv = aj.inv_sens > 0.5f;
  if (inv != inv_aplicado) { espejar_calibracion(); filt.reiniciar(); inv_aplicado = inv; }
  cfg_lect.resta_ambiente = RESTA_AMBIENTE != 0;
  cfg_lect.invertidos = inv;
  cfg_lect.t_emisor_us = static_cast<uint32_t>(aj.t_emisor_us);
  cfg_lect.t_mux_us = static_cast<uint32_t>(aj.t_mux_us);
  cfg_lect.sobremuestreo = static_cast<int>(aj.sobremuestreo);
  cfg_lect.descartes = static_cast<int>(aj.descartes);
  actualizar_cal_valida();
}

static void guardar() {
  Guardado g{};
  g.a = aj;
  g.n_cal = cal.n;
  for (int i = 0; i < MAX_CAL; ++i) {
    g.cal_min[i] = i < cal.n ? cal.minimo[i] : 0.0f;
    g.cal_max[i] = i < cal.n ? cal.maximo[i] : 0.0f;
  }
  sellar(g);
  GuardadoTurbo gt{};
  gt.t = tb;
  sellar(gt);
  nvs.begin("emergencia", false);
  nvs.putBytes("g", &g, sizeof(g));
  nvs.putBytes("t", &gt, sizeof(gt));     // clave aparte: el formato de "g" no cambia
  nvs.end();
}

static bool cargar() {                    // ajustes y calibración se guardan juntos: son coherentes entre sí
  Guardado g;
  nvs.begin("emergencia", true);
  const bool ok = nvs.getBytesLength("g") == sizeof(g) && nvs.getBytes("g", &g, sizeof(g)) == sizeof(g) && valido(g);
  nvs.end();
  if (!ok) return false;
  aj = g.a;
  inv_aplicado = aj.inv_sens > 0.5f;      // la calibración guardada ya está en el orden de estos ajustes
  cal.reiniciar(NUM_SENSORES);
  if (g.n_cal == NUM_SENSORES)
    for (int i = 0; i < NUM_SENSORES; ++i) { cal.minimo[i] = g.cal_min[i]; cal.maximo[i] = g.cal_max[i]; }
  return true;
}

// Turbo: si no hay datos válidos (firmware anterior o memoria vacía) queda de fábrica = DESACTIVADO.
static bool cargar_turbo() {
  GuardadoTurbo gt;
  nvs.begin("emergencia", true);
  const bool ok =
      nvs.getBytesLength("t") == sizeof(gt) && nvs.getBytes("t", &gt, sizeof(gt)) == sizeof(gt) && valido(gt);
  nvs.end();
  tb = ok ? gt.t : Turbo();
  return ok;
}

// ------------------------------------------------------------------ sensores y batería
static void leer_sensores() {
  t_lectura_us = hw::leer_sensores(crudo_on, crudo_off, cfg_lect);
  static const posicion::ModoSensor modo = {RESTA_AMBIENTE != 0, LUZ_BAJA_VOLTAJE != 0, par::ADC_MAX};
  for (int i = 0; i < NUM_SENSORES; ++i) refl[i] = posicion::reflectancia(modo, crudo_on[i], crudo_off[i]);
  filt.aplicar(refl, NUM_SENSORES, aj.alfa);
}

static void estimar() {
  posicion::normalizar(cal, refl, osc);
  util::enmascarar(osc, NUM_SENSORES, mask);
  est = posicion::estimar_posicion(geom, osc, aj.umbral, aj.confianza);
  n_oscuros = util::contar_oscuros(osc, NUM_SENSORES, par::OSCURO_TODOS, mask);
}

static void medir_bateria(uint32_t t) {
  if (t - t_bat_med < 20) return;              // cada 20 ms
  t_bat_med = t;
  const float v = hw::v_bateria();
  hay_bat = v > 3.0f;                          // con solo USB el divisor marca ~0 V
  const float vbat = hay_bat ? v : 0.0f;
  vbat_f = (vbat_f <= 0.0f || !hay_bat) ? vbat : vbat_f + 0.2f * (vbat - vbat_f);   // ≈ 100 ms
  bat_baja = hay_bat && vbat_f < aj.bat_baja;
  if (hay_bat && vbat_f < aj.bat_critica) { if (!t_bat_crit) t_bat_crit = t ? t : 1; }
  else t_bat_crit = 0;
  bat_crit = t_bat_crit && (t - t_bat_crit > 500);   // la batería baja de golpe al acelerar: se exige 0.5 s
  if (bat_baja && !aviso_bat) Serial.printf("AVISO: bateria baja %.2f V (umbral %.2f V)\n", vbat_f, aj.bat_baja);
  aviso_bat = bat_baja;
  bat_alta = hay_bat && vbat_f > BAT_MAX_2S;   // solo aviso: no bloquea nada
  if (bat_alta && !aviso_alta)
    Serial.printf("AVISO: bateria %.2f V supera %.1f V, el maximo razonable de una 2S Li-ion (8.4 V cargada). "
                  "Revisa la bateria/fuente o la calibracion (escribe `bat`)\n", vbat_f, BAT_MAX_2S);
  aviso_alta = bat_alta;
}

// ------------------------------------------------------------------ motores
// izq/der son las ruedas del robot. Motor físico 0 = AIN (M1), 1 = BIN (M2). `cruzar` intercambia los lados.
static void salida_motores(float izq, float der, float dt) {
  const float ci = aj.inv_izq > 0.5f ? -izq : izq;
  const float cd = aj.inv_der > 0.5f ? -der : der;
  const bool x = aj.cruzar > 0.5f;
  acc.actualizar(x ? cd : ci, x ? ci : cd, util::v_puente(hay_bat, vbat_f, aj.vm_fijo, aj.caida_reg), dt);
  const motor::Decaimiento k = aj.lento > 0.5f ? motor::Decaimiento::LENTO : motor::Decaimiento::RAPIDO;
  for (int m = 0; m < 2; ++m) {
    const motor::Puente p = motor::drv8833(acc.ciclo(m), k);
    hw::puente(m, p.in1, p.in2);
  }
}
static float ciclo_rueda(int lado) {           // 0 = izquierda, 1 = derecha (ciclo real, con signo físico)
  return acc.ciclo(aj.cruzar > 0.5f ? 1 - lado : lado);
}

static void motores_quietos(bool frenar) {     // directo al puente, sin rampa: parada inmediata
  acc.reiniciar();
  const motor::Puente p = frenar ? motor::freno() : motor::libre();
  hw::puente(0, p.in1, p.in2);
  hw::puente(1, p.in1, p.in2);
}

static void esperar_ms(uint32_t ms) {          // delay que no dispara el watchdog
  const uint32_t t0 = millis();
  while (millis() - t0 < ms) { hw::vigilante_alimentar(); delay(1); }
}

static bool hay_tecla() {                       // consume lo recibido; true si llegó algo
  bool hubo = false;
  while (Serial.available()) { Serial.read(); hubo = true; }
  return hubo;
}

static bool puede_mover(const char* que) {
  if (maq.motores() || maq.estado() == Estado::CALIBRACION || maq.armando()) {
    Serial.printf("%s: no disponible en %s\n", que, nombre(maq.estado()));
    return false;
  }
  if (!hay_bat) { Serial.printf("%s: sin bateria (solo USB): los motores no tienen voltaje\n", que); return false; }
  if (bat_crit) { Serial.printf("%s: bateria critica (%.2f V)\n", que, vbat_f); return false; }
  if (diag_activo()) { Serial.printf("%s: sal primero del diagnostico (`emis 0`, `mux off`)\n", que); return false; }
  return true;
}

static void terminar_movimiento() {
  motores_quietos(true);
  esperar_ms(150);
  motores_quietos(false);
  hw::driver_despierto(maq.despierto(millis()));
  t_prev_us = micros();                        // el ciclo de control no cuenta este tiempo como atraso
}

// ------------------------------------------------------------------ pruebas con motores (bloqueantes, con watchdog)
static void prueba_motor(float a, float b, int ms) {
  if (!puede_mover("m")) return;
  if (ms < 50) ms = 50;
  if (ms > 3000) ms = 3000;
  Serial.println("motores girando: envia cualquier tecla para parar");
  hw::driver_despierto(true);
  delay(2);                                    // despertar del DRV8833 (tWAKE ≤ 1 ms)
  acc.reiniciar();
  const uint32_t t0 = millis();
  uint32_t tp = micros();
  bool cortado = false;
  while (millis() - t0 < (uint32_t)ms) {       // pasa por el tope, las rampas y el límite de corriente
    hw::vigilante_alimentar();
    if (hay_tecla()) { cortado = true; break; }
    const uint32_t ahora = micros();
    const float dt = (ahora - tp) * 1e-6f;
    tp = ahora;
    salida_motores(a, b, dt > 0.0f ? dt : 1e-3f);
    delay(2);
  }
  const float ci = ciclo_rueda(0), cd = ciclo_rueda(1);
  terminar_movimiento();
  Serial.printf("%s · ciclo final izq=%.2f der=%.2f (signo = sentido electrico, ya con inv_izq/inv_der)\n",
                cortado ? "PARADO" : "ok", ci, cd);
}

static void autocalibrar() {
  if (!puede_mover("autocal")) return;
  const Estado e0 = maq.estado();
  if (e0 != Estado::ESPERA && e0 != Estado::LISTO && e0 != Estado::PARADA) {
    Serial.println("autocal: solo en ESPERA, LISTO o PARADA");
    return;
  }
  Serial.println("autocal: robot SOBRE la linea; va a girar solo. Cualquier tecla cancela");
  cal_respaldo = cal;
  autocal::Param p;
  p.u = aj.ac_u; p.t_max_s = aj.ac_t; p.contraste = aj.contraste; p.umbral = aj.umbral; p.confianza = aj.confianza;
  p.mascara = mask;
  autocal::AutoCal ac;
  ac.iniciar(NUM_SENSORES, p, cal);
  hw::driver_despierto(true);
  delay(2);
  acc.reiniciar();
  autocal::Salida s;
  autocal::Fase f_prev = ac.fase();
  const char* fallo = nullptr;
  const uint32_t t0 = millis();
  uint32_t tp = micros();
  while (true) {
    hw::vigilante_alimentar();
    if (hay_tecla()) { fallo = "cancelada por teclado"; break; }
    const uint32_t ahora = micros();
    if (ahora - tp < par::PERIODO_CONTROL_US) continue;
    const float dt = (ahora - tp) * 1e-6f;
    tp = ahora;
    leer_sensores();
    medir_bateria(millis());
    if (!hay_bat || bat_crit) { fallo = "bateria"; break; }
    s = ac.paso(refl, cal, geom, dt);
    if (ac.fase() != f_prev) { f_prev = ac.fase(); Serial.printf("  autocal: %s\n", autocal::nombre(f_prev)); }
    if (s.termino) break;
    salida_motores(s.izq, s.der, dt);
    if (millis() - t0 > 20000) { fallo = "tiempo total"; break; }
  }
  terminar_movimiento();
  if (!fallo && ac.al_reves()) fallo = "giro al reves: revisa inv_izq / inv_der / cruzar con `m` e inv_sens con `sens`";
  if (!fallo && ac.fase() == autocal::Fase::FALLA) fallo = "no vio la linea con todos los sensores (centra el robot sobre la linea)";
  if (fallo || !s.cal_ok) {
    cal = cal_respaldo;
    actualizar_cal_valida();
    Serial.printf("autocal FALLO: %s. Se conserva la calibracion anterior (%s)\n", fallo ? fallo : "sin contraste",
                  cal_valida ? "valida" : "NO valida");
    return;
  }
  actualizar_cal_valida();
  guardar();
  maq.calibracion_externa(cal_valida, millis());
  Serial.printf("autocal OK (guardada)%s -> %s\n", s.centrado ? ", robot centrado" : ", NO quedo centrado: acomodalo a mano",
                nombre(maq.estado()));
}

// ------------------------------------------------------------------ consola USB
static char linea[96];
static int n_linea = 0;

static float* valor_de(const EntradaAjuste& e, bool es_turbo) { return es_turbo ? campo(tb, e) : campo(aj, e); }

static void imprimir_ajuste(const EntradaAjuste& e, bool con_rango, bool es_turbo = false) {
  const float v = *valor_de(e, es_turbo);
  if (con_rango) Serial.printf("%-13s = %-9g [%g .. %g]  %s\n", e.nombre, v, e.min, e.max, e.ayuda);
  else Serial.printf("%s=%g", e.nombre, v);
}

static void imprimir_turbo_estado() {
  if (tb.v_recta > aj.vbase)
    Serial.printf("turbo ACTIVO en recta: vbase %.2f -> v_recta %.2f en %.2f s (tras %.2f s de recta limpia)\n", aj.vbase,
                  tb.v_recta, tb.recta_t_acel, tb.recta_t_conf);
  else Serial.printf("turbo APAGADO (v_recta %.2f <= vbase %.2f)\n", tb.v_recta, aj.vbase);
}

static void imprimir_ajustes() {
  int n;
  const EntradaAjuste* t = tabla_ajustes(&n);
  for (int i = 0; i < n; ++i) { imprimir_ajuste(t[i], false); Serial.print((i % 6 == 5) ? "\n" : "  "); }
  Serial.println();
  t = tabla_turbo(&n);
  for (int i = 0; i < n; ++i) { imprimir_ajuste(t[i], false, true); Serial.print("  "); }
  Serial.println();
  imprimir_turbo_estado();
}

static void imprimir_pines() {
  Serial.printf("mux S0=%d S1=%d S2=%d S3=%d SIG=%d · EMIT_EN=%d · START=%d CAL=%d · LED=%d · VBAT=%d\n", PIN_MUX_S0,
                PIN_MUX_S1, PIN_MUX_S2, PIN_MUX_S3, PIN_MUX_SIG, PIN_EMISORES, PIN_START, PIN_CAL, PIN_LED, PIN_BATERIA);
  Serial.printf("DRV8833 AIN1=%d AIN2=%d (M1) · BIN1=%d BIN2=%d (M2) · nSLEEP=%d · sin nFAULT, zumbador ni ventilador\n",
                PIN_AIN1, PIN_AIN2, PIN_BIN1, PIN_BIN2, PIN_NSLEEP);
  Serial.printf("%d sensores, paso %.2f mm, SEN1 a la %s, mascara %lu · motores: inv_izq=%d inv_der=%d cruzar=%d\n",
                NUM_SENSORES, aj.paso_mm, aj.inv_sens > 0.5f ? "DERECHA" : "izquierda", (unsigned long)mask,
                (int)aj.inv_izq, (int)aj.inv_der, (int)aj.cruzar);
}

static void imprimir_sensores() {
  Serial.print("izq ");
  for (int i = 0; i < NUM_SENSORES; ++i) {
    if (util::activo(mask, i)) Serial.printf("%.2f ", osc[i]);
    else Serial.print(" --  ");
  }
  Serial.printf("der | pos=%+.1f mm visible=%d negros=%d cal=%s\n", est.pos_mm, est.linea_visible, n_oscuros,
                cal_valida ? "si" : "NO");
}

static void imprimir_crudo() {
  Serial.print("on : "); for (int i = 0; i < NUM_SENSORES; ++i) Serial.printf("%4d ", crudo_on[i]);
  Serial.print("\noff: "); for (int i = 0; i < NUM_SENSORES; ++i) Serial.printf("%4d ", crudo_off[i]);
  Serial.print("\ndif: "); for (int i = 0; i < NUM_SENSORES; ++i) Serial.printf("%4d ", crudo_off[i] - crudo_on[i]);
  Serial.println("   (izquierda -> derecha; dif grande = blanco, chica = negro)");
}

static void imprimir_calibracion() {
  Serial.printf("calibracion %s (contraste minimo %.0f cuentas)\n", cal_valida ? "valida" : "NO valida", aj.contraste);
  for (int i = 0; i < cal.n; ++i) {
    const int c = util::canal_de_sensor(i, NUM_SENSORES, aj.inv_sens > 0.5f);
    const float r = cal.maximo[i] - cal.minimo[i];
    Serial.printf("  pos %d = SEN%d (C%d): negro=%.0f blanco=%.0f contraste=%.0f %s\n", i + 1, c + 1, c,
                  cal.minimo[i], cal.maximo[i], r > 0 ? r : 0.0f,
                  !util::activo(mask, i) ? "(ignorado)" : (r >= aj.contraste ? "ok" : "<- FALTA"));
  }
}

static void imprimir_estado() {
  Serial.printf("estado=%s%s error=%d ultima parada: %s · cal=%s · bateria=%.2f V%s%s\n", nombre(maq.estado()),
                maq.armando() ? " (arrancando)" : "", (int)maq.error(), nombre(maq.motivo()), cal_valida ? "si" : "NO",
                vbat_f, hay_bat ? (bat_crit ? " (CRITICA)" : (bat_baja ? " (BAJA)" : (bat_alta ? " (SOBRE 8.6 V: revisar)" : "")))
                                : " (solo USB)",
                diag_activo() ? " · DIAGNOSTICO (emis/mux): START bloqueado" : "");
  imprimir_turbo_estado();
}

static void diag_canal(int c, bool es_sensor) {
  const bool antes = hw::emisores_encendidos();
  hw::ConfigLectura k = cfg_lect;
  k.sobremuestreo = 4;
  hw::emisores(false);
  delayMicroseconds(k.t_emisor_us);
  const int off = hw::leer_canal(c, k);
  hw::emisores(true);
  delayMicroseconds(k.t_emisor_us);
  const int on = hw::leer_canal(c, k);
  hw::emisores(antes);
  if (diag_mux >= 0) hw::seleccionar_canal(diag_mux, k.t_mux_us);   // vuelve al canal fijado con `mux`
  Serial.printf("%s%d (C%d): LED encendidos=%d apagados=%d dif=%d", es_sensor ? "SEN" : "canal ", es_sensor ? c + 1 : c,
                c, on, off, off - on);
  if (off - on < 40) Serial.print("  <- casi sin reflejo: negro, sensor lejos del piso o LED IR apagado");
  if (off < 300 && on < 300) Serial.print("  <- SIG casi en 0: revisa pull-up de 10k o corto a GND");
  Serial.println();
}

static void imprimir_monitor() {
  switch (monitor) {
    case Monitor::SENS: imprimir_sensores(); break;
    case Monitor::CRUDO: imprimir_crudo(); break;
    case Monitor::POS: Serial.printf("pos=%+6.1f mm visible=%d confianza=%.2f negros=%d\n", est.pos_mm, est.linea_visible,
                                     est.confianza, n_oscuros); break;
    case Monitor::BAT: Serial.printf("bateria %.2f V · VP %.0f mV · ADC %d · factor %.4f\n", vbat_f, hw::mv_pin_bateria(),
                                     hw::adc_crudo_bateria(), FACTOR_BATERIA); break;
    case Monitor::BOT: Serial.printf("START=%d CAL=%d\n", hw::boton_start(), hw::boton_cal()); break;
    case Monitor::NADA: break;
  }
}

static void ayuda() {
  Serial.println("--- informacion:  ver | pines | estado | perf");
  Serial.println("--- ajustes:      get [clave] | rangos | set <clave> <valor> | save | load | defecto | perfil seguro|normal|rapido");
  Serial.println("--- sensores:     sens | crudo | sensor <1-8> | canal <0-15> | mux <0-15>|off | emis 0|1 | mon sens|crudo|pos|bat|bot");
  Serial.println("--- calibracion:  calibrar (igual que CAL) | autocal (gira solo sobre la linea) | cal (ver resultado)");
  Serial.println("--- motores:      m <izq> <der> [ms]  (-1..1, RUEDAS EN EL AIRE) | stop");
  Serial.println("--- otros:        botones | bat | tel 0|1 | reiniciar");
  Serial.println("En marcha la consola no responde: cualquier tecla PARA el robot. `mon` se detiene con cualquier tecla.");
}

static void ejecutar(char* l) {
  char* c = strtok(l, " \t");
  if (!c) return;
  char* a1 = strtok(nullptr, " \t");
  char* a2 = strtok(nullptr, " \t");
  char* a3 = strtok(nullptr, " \t");
  float fa = 0.0f, fb = 0.0f;
  int ia = 0;
  if (!strcmp(c, "ayuda") || !strcmp(c, "?") || !strcmp(c, "help")) ayuda();
  else if (!strcmp(c, "ver")) Serial.printf("%s · %s · CPU %lu MHz · compilado %s %s · watchdog %s\n", VERSION_FW,
                                            hw::version_nucleo(), (unsigned long)hw::cpu_mhz(), __DATE__, __TIME__,
                                            vigilante_ok ? "activo" : "NO activo");
  else if (!strcmp(c, "estado")) imprimir_estado();
  else if (!strcmp(c, "pines")) imprimir_pines();
  else if (!strcmp(c, "get")) {
    if (!a1) imprimir_ajustes();
    else if (const EntradaAjuste* e = buscar(a1)) imprimir_ajuste(*e, true);
    else if (const EntradaAjuste* et = buscar_turbo(a1)) imprimir_ajuste(*et, true, true);
    else Serial.println("clave desconocida (escribe: rangos)");
  } else if (!strcmp(c, "rangos")) {
    int n;
    const EntradaAjuste* t = tabla_ajustes(&n);
    for (int i = 0; i < n; ++i) imprimir_ajuste(t[i], true);
    t = tabla_turbo(&n);
    for (int i = 0; i < n; ++i) imprimir_ajuste(t[i], true, true);
  } else if (!strcmp(c, "set")) {
    const char* motivo = nullptr;
    const EntradaAjuste* e = a1 ? buscar(a1) : nullptr;
    const EntradaAjuste* et = (a1 && !e) ? buscar_turbo(a1) : nullptr;
    const EntradaAjuste* x = e ? e : et;
    if (!x || !util::leer_float(a2, &fa)) Serial.println("uso: set <clave> <numero>   (claves y rangos: rangos)");
    else if (!(fa >= x->min && fa <= x->max)) Serial.printf("%s fuera de rango [%g .. %g]\n", a1, x->min, x->max);
    else if (e && !fijar(aj, a1, fa)) {
      Ajustes p = aj;
      *campo(p, *e) = fa;
      coherente(p, &motivo);
      Serial.printf("rechazado: %s\n", motivo ? motivo : "?");
    } else if (et && !fijar(tb, a1, fa)) {
      Turbo p = tb;
      *campo(p, *et) = fa;
      coherente(p, &motivo);
      Serial.printf("rechazado: %s\n", motivo ? motivo : "?");
    } else {
      aplicar_ajustes();
      Serial.printf("%s=%g (falta `save` para guardarlo)%s\n", a1, fa,
                    !strcmp(a1, "inv_sens") ? " · calibracion espejada" : "");
      if (et || !strcmp(a1, "vbase")) imprimir_turbo_estado();
    }
  } else if (!strcmp(c, "perfil")) {
    if (!a1 || !aplicar_perfil(aj, tb, a1)) Serial.println("uso: perfil seguro | normal | rapido");
    else {
      aplicar_ajustes();
      Serial.printf("perfil %s: vbase=%g pwm_max=%g rampa=%g/%g kp=%g kd=%g freno=%g v_recta=%g (falta `save`)\n", a1,
                    aj.vbase, aj.pwm_max, aj.rampa, aj.rampa_freno, aj.kp, aj.kd, aj.freno, tb.v_recta);
      imprimir_turbo_estado();
    }
  } else if (!strcmp(c, "save")) { guardar(); Serial.println("guardado (ajustes, calibracion y turbo)"); }
  else if (!strcmp(c, "load")) {
    const bool ok = cargar();
    const bool ok_t = cargar_turbo();
    if (ok) aplicar_ajustes();
    Serial.printf("%s · turbo %s\n", ok ? "cargado" : "no hay ajustes validos guardados",
                  ok_t ? "cargado" : "de fabrica (apagado)");
    if (!ok && ok_t) aplicar_ajustes();
  } else if (!strcmp(c, "defecto")) {
    aj = Ajustes();
    tb = Turbo();
    aplicar_ajustes();
    Serial.println("valores de fabrica, turbo apagado (falta `save`)");
  }
  else if (!strcmp(c, "sens")) imprimir_sensores();
  else if (!strcmp(c, "crudo")) imprimir_crudo();
  else if (!strcmp(c, "cal")) imprimir_calibracion();
  else if (!strcmp(c, "calibrar")) cal_consola = true;
  else if (!strcmp(c, "autocal")) autocalibrar();
  else if (!strcmp(c, "sensor")) {
    if (!util::leer_int(a1, 1, NUM_SENSORES, &ia)) Serial.printf("uso: sensor <1-%d>   (SEN1 = C0 ... SEN8 = C7)\n", NUM_SENSORES);
    else diag_canal(ia - 1, true);
  } else if (!strcmp(c, "canal")) {
    if (!util::leer_int(a1, 0, 15, &ia)) Serial.println("uso: canal <0-15>");
    else diag_canal(ia, false);
  } else if (!strcmp(c, "mux")) {
    if (a1 && !strcmp(a1, "off")) { diag_mux = -1; Serial.println("mux libre: vuelve el barrido"); }
    else if (util::leer_int(a1, 0, 15, &ia)) {
      diag_mux = ia;
      hw::seleccionar_canal(ia, cfg_lect.t_mux_us);
      const util::BitsMux b = util::bits_mux(ia);
      Serial.printf("mux fijo en C%d (S3..S0 = %d%d%d%d). Mide SIG (GPIO34) con el multimetro. `mux off` para salir\n", ia,
                    b.s3, b.s2, b.s1, b.s0);
    } else Serial.println("uso: mux <0-15> | mux off");
  } else if (!strcmp(c, "emis")) {
    if (!util::leer_int(a1, 0, 1, &ia)) Serial.println("uso: emis 0 | emis 1");
    else {
      diag_emis = ia == 1;
      hw::emisores(diag_emis);
      Serial.printf("emisores %s\n", diag_emis ? "ENCENDIDOS fijos (barrido detenido; `emis 0` para salir)" : "en modo normal");
    }
  } else if (!strcmp(c, "mon")) {
    if (a1 && !strcmp(a1, "sens")) monitor = Monitor::SENS;
    else if (a1 && !strcmp(a1, "crudo")) monitor = Monitor::CRUDO;
    else if (a1 && !strcmp(a1, "pos")) monitor = Monitor::POS;
    else if (a1 && !strcmp(a1, "bat")) monitor = Monitor::BAT;
    else if (a1 && !strcmp(a1, "bot")) monitor = Monitor::BOT;
    else { Serial.println("uso: mon sens | crudo | pos | bat | bot   (cualquier tecla lo detiene)"); return; }
    Serial.println("monitor a 10 Hz: cualquier tecla lo detiene");
  } else if (!strcmp(c, "botones")) {
    Serial.printf("START=%s CAL=%s (lectura directa del pin)\n", hw::boton_start() ? "OPRIMIDO" : "suelto",
                  hw::boton_cal() ? "OPRIMIDO" : "suelto");
  } else if (!strcmp(c, "bat")) {
    const int crudo = hw::adc_crudo_bateria();
    const float mv = hw::mv_pin_bateria();
    Serial.printf("ADC crudo GPIO36 = %d / 4095 · VP = %.3f V\n", crudo, mv * 0.001f);
    Serial.printf("factor aplicado = %.4f (medido 10.0 V / 2.1 V) · nominal 100k/33k = %.3f (solo referencia)\n",
                  FACTOR_BATERIA, DIVISOR_BATERIA);
    Serial.printf("bateria = %.2f V ahora, %.2f V filtrada%s\n", util::volts_bateria(mv, FACTOR_BATERIA), vbat_f,
                  !hay_bat ? " · solo USB (KCD1 apagado o sin bateria)"
                           : (bat_alta ? " · SOBRE el maximo de una 2S Li-ion: revisar" : ""));
    Serial.printf("umbrales: baja < %.2f V · critica < %.2f V (0.5 s, para en marcha) · aviso > %.1f V · puente %.2f V\n",
                  aj.bat_baja, aj.bat_critica, BAT_MAX_2S, util::v_puente(hay_bat, vbat_f, aj.vm_fijo, aj.caida_reg));
  } else if (!strcmp(c, "perf")) {
    Serial.printf("lectura de sensores %lu us, ciclo maximo %lu us (periodo %lu us, limite en marcha %lu us)\n",
                  (unsigned long)t_lectura_us, (unsigned long)t_ciclo_max_us, par::PERIODO_CONTROL_US, par::CICLO_MAX_US);
    t_ciclo_max_us = 0;
  } else if (!strcmp(c, "tel")) {
    if (!util::leer_int(a1, 0, 1, &ia)) Serial.println("uso: tel 0 | tel 1");
    else {
      telemetria = ia == 1;
      if (telemetria)
        Serial.println("telemetria en marcha (100 Hz): t_ms,estado,pos_mm,visible,u,ciclo_izq,ciclo_der,vbat,turbo,v");
    }
  } else if (!strcmp(c, "m")) {
    if (!util::leer_float(a1, &fa) || !util::leer_float(a2, &fb) || fa < -1 || fa > 1 || fb < -1 || fb > 1 ||
        (a3 && !util::leer_int(a3, 50, 3000, &ia)))
      Serial.println("uso: m <izq> <der> [ms]   valores -1..1, ms 50..3000   ej. m 0.3 0");
    else prueba_motor(fa, fb, a3 ? ia : 1000);
  } else if (!strcmp(c, "stop")) {
    motores_quietos(false);
    hw::driver_despierto(false);
    Serial.println("motores sueltos y puente dormido");
  } else if (!strcmp(c, "reiniciar")) { Serial.println("reiniciando..."); Serial.flush(); ESP.restart(); }
  else Serial.println("comando desconocido (escribe: ayuda)");
}

// Acepta fin de línea "\n", "\r" o "\r\n" (Monitor Serie de Arduino en cualquier modo; PlatformIO manda "\r\n").
static void consola() {
  static char previo = 0;
  while (Serial.available()) {
    const char ch = (char)Serial.read();
    const bool lf_tras_cr = (ch == '\n' && previo == '\r');
    previo = ch;
    if (lf_tras_cr) continue;
    if (monitor != Monitor::NADA) {             // cualquier tecla detiene el monitor
      monitor = Monitor::NADA;
      hay_tecla();
      n_linea = 0;
      previo = 0;
      Serial.println("monitor detenido");
      return;
    }
    if (ch == '\n' || ch == '\r') { linea[n_linea] = 0; n_linea = 0; ejecutar(linea); }
    else if (n_linea < (int)sizeof(linea) - 1) linea[n_linea++] = ch;
  }
}

// ------------------------------------------------------------------ setup / loop
void setup() {
  hw::iniciar();                               // primero: puente dormido y entradas en 0
  Serial.setTxBufferSize(2048);                // la telemetría no bloquea el ciclo de control esperando al UART
  Serial.begin(115200);
  cal.reiniciar(NUM_SENSORES);
  const bool hay = cargar();
  cargar_turbo();                              // clave aparte; si no hay datos válidos, turbo apagado
  aplicar_ajustes();
  b_start.ms_estable = b_cal.ms_estable = ANTIRREBOTE_MS;
  maq.reiniciar(millis());
  vigilante_ok = hw::vigilante_iniciar(par::WDT_MS);
  t_prev_us = micros();
  Serial.printf("\nRobot de emergencia · %s · %s · %d sensores con CD74HC4067\n", VERSION_FW, hw::version_nucleo(),
                NUM_SENSORES);
  Serial.printf("ajustes %s · calibracion %s · watchdog %s · vbase=%g. Escribe 'ayuda'.\n",
                hay ? "guardados" : "de fabrica (perfil seguro)", cal_valida ? "guardada" : "NO", vigilante_ok ? "ok" : "FALLO",
                aj.vbase);
  imprimir_turbo_estado();
}

void loop() {
  hw::vigilante_alimentar();
  const uint32_t t = millis();
  if (maq.motores() || maq.armando()) { if (hay_tecla()) parar_usb = true; }   // cualquier byte por USB = parar
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
  estimar();
  const bool todo_negro = n_oscuros > 0 && n_oscuros >= util::contar_activos(mask, NUM_SENSORES);
  if (todo_negro && maq.motores()) { if (!t_todo_negro) t_todo_negro = t ? t : 1; }
  else t_todo_negro = 0;
  // Permiso del turbo: solo en SIGUIENDO (no en recuperación), con batería sin aviso, ciclo a tiempo (≤ 2 periodos),
  // sin "todo negro", sin tecla USB pendiente y sin diagnóstico. Si falta cualquiera, el control lo cancela al instante.
  const bool turbo_ok = maq.estado() == Estado::SIGUIENDO && hay_bat && !bat_baja && !bat_crit &&
                        dt_us <= 2 * par::PERIODO_CONTROL_US && !todo_negro && !parar_usb && !diag_activo();
  if (maq.motores()) sal = ctl.actualizar(est, dt, turbo_ok);

  Entradas in;
  in.start = b_start.pulso(hw::boton_start(), t);
  in.cal = b_cal.pulso(hw::boton_cal(), t) || cal_consola;
  cal_consola = false;
  if (diag_activo() && (in.start || in.cal)) {
    Serial.println("diagnostico activo (emis/mux): sal con `emis 0` y `mux off` antes de usar START o CAL");
    in.start = in.cal = false;
  }
  in.cal_lista = antes == Estado::CALIBRACION && util::cal_lista(cal, aj.contraste, mask);
  in.cal_valida = cal_valida;
  in.linea_visible = est.linea_visible;
  in.buscando = maq.motores() && sal.buscando;
  in.linea_perdida = maq.motores() && sal.linea_perdida;
  in.levantado = aj.t_negro > 0.0f && t_todo_negro && (t - t_todo_negro) >= (uint32_t)(aj.t_negro * 1000.0f);
  in.hay_bateria = hay_bat;
  in.bat_critica = bat_crit;
  in.parar = parar_usb;
  in.falla_ciclo = maq.motores() && dt_us > par::CICLO_MAX_US;
  if (parar_usb && maq.armando()) in.start = true;   // tecla durante la espera de arranque: la cancela
  parar_usb = false;

  // ---- estado y acciones al entrar
  const Estado e = maq.paso(in, t);
  if (maq.entro()) {
    if (e == Estado::CALIBRACION) { cal_respaldo = cal; cal.reiniciar(NUM_SENSORES); }
    if (antes == Estado::CALIBRACION) {
      if (maq.fin_cal() == FinCal::BIEN) { actualizar_cal_valida(); guardar(); }
      else { cal = cal_respaldo; actualizar_cal_valida(); }   // faltó contraste: se conserva la anterior
      Serial.printf("calibracion %s\n", maq.fin_cal() == FinCal::BIEN ? "OK (guardada)" : "INSUFICIENTE: repetir (escribe `cal`)");
    }
    if (e == Estado::SIGUIENDO && antes == Estado::LISTO) { ctl.fijar(a_control(aj, tb)); ctl.reiniciar(); acc.reiniciar(); sal = SalidaControl{}; }
    if (e == Estado::PARADA || e == Estado::ERROR) {
      if (e == Estado::ERROR) Serial.printf("ERROR %d: %s\n", (int)maq.error(), nombre(maq.motivo()));
      else Serial.printf("parada: %s\n", nombre(maq.motivo()));
    }
    Serial.printf("-> %s\n", nombre(e));
  } else if (maq.rechazo() && in.start) {
    Serial.println(!cal_valida ? "START rechazado: falta calibrar (CAL o `calibrar`)"
                               : (!hay_bat ? "START rechazado: sin bateria (solo USB)" : "START rechazado: bateria critica"));
  }
  if (maq.armando() != armando_antes) {
    armando_antes = maq.armando();
    if (armando_antes) Serial.printf("arranca en %.1f s (START o cualquier tecla cancela)\n", aj.t_arranque);
    else if (e == Estado::LISTO) Serial.println("arranque cancelado");
  }

  // ---- salidas
  hw::driver_despierto(maq.despierto(t));
  if (maq.motores()) salida_motores(sal.izq, sal.der, dt);
  else motores_quietos(maq.frenando(t));

  Contexto cx{e, maq.error(), maq.desde(t), t, est.linea_visible, maq.fin_cal(), t - maq.t_fin_cal(), maq.rechazo(),
              t - maq.t_rechazo(), bat_baja, maq.armando(), a_tiempos(aj).cal_max_ms};
  hw::led(indicar(cx).led);

  if (telemetria && maq.motores() && (++n_ciclos % 4 == 0))
    Serial.printf("%lu,%s,%.1f,%d,%.3f,%.3f,%.3f,%.2f,%.2f,%.3f\n", (unsigned long)t, nombre(e), est.pos_mm,
                  (int)est.linea_visible, sal.u, ciclo_rueda(0), ciclo_rueda(1), vbat_f, sal.turbo, sal.v);
  if (monitor != Monitor::NADA && !maq.motores() && t - t_monitor >= 100) { t_monitor = t; imprimir_monitor(); }
  const uint32_t dur = micros() - ahora;
  if (dur > t_ciclo_max_us) t_ciclo_max_us = dur;
}
