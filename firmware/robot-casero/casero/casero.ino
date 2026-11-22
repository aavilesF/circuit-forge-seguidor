// Robot casero (Plan B) · Firmware V3 · ESP32 DevKit 30 pines + DRV8833 + 2 × MP1584 + barra de 8 sensores.
//
// De V1 (rama main): posicion.* (calibración y posición de la línea), pid.* y control.* (ControladorLinea), sin cambios.
// De V2: máquina de estados con recuperación, indicadores por estado, límite de corriente con modelo del motor,
//        parámetros con CRC en memoria y consola por USB.
// Nuevo: filtro de sensores (mediana + pasa-bajas), puente DRV8833 en decaimiento lento, tope de PWM y rampa.
//
// Botones: CAL = calibrar (≤ 15 s, se pasa el robot a mano sobre la línea) · START = arrancar / parar.
// Consola USB a 115200: escribir `ayuda`. Sin WiFi ni Bluetooth (reglamento): no se incluyen WiFi.h ni BluetoothSerial.h.
#include <Preferences.h>

#include "ajustes.h"
#include "config.h"
#include "control.h"
#include "estados.h"
#include "filtro.h"
#include "hw_casero.h"
#include "indicadores.h"
#include "motor.h"
#include "parametros.h"
#include "posicion.h"

using namespace casero;

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
static bool hay_bat = false, bat_baja = false, bat_crit = false;
static uint32_t t_bat_crit = 0, t_falla = 0, t_bat_med = 0;
static bool telemetria = false;
static uint32_t t_lectura_us = 0, t_ciclo_max_us = 0, n_ciclos = 0;
static unsigned long t_prev_us = 0;

// ------------------------------------------------------------------ botones sin rebote (25 ms)
struct Boton {
  bool estable = false, crudo = false;
  uint32_t t_cambio = 0;
  bool pulso(bool lectura, uint32_t t) {        // true una vez al oprimir
    if (lectura != crudo) { crudo = lectura; t_cambio = t; }
    if (crudo != estable && t - t_cambio >= 25) { estable = crudo; return estable; }
    return false;
  }
};
static Boton b_start, b_cal;

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
  nvs.begin("casero", false);
  nvs.putBytes("g", &g, sizeof(g));
  nvs.end();
}

static bool cargar() {
  Guardado g;
  nvs.begin("casero", true);
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
  const float v = hw::v_divisor();
  hay_bat = v > 3.0f;                          // con solo USB el divisor marca ~0 V
  vbat = hay_bat ? v + aj.caida_d1 : 0.0f;
  vbat_f = (vbat_f <= 0.0f || !hay_bat) ? vbat : vbat_f + 0.2f * (vbat - vbat_f);   // ≈ 100 ms
  bat_baja = hay_bat && vbat_f < aj.bat_baja;
  if (hay_bat && vbat_f < aj.bat_critica) { if (!t_bat_crit) t_bat_crit = t ? t : 1; }
  else t_bat_crit = 0;
  bat_crit = t_bat_crit && (t - t_bat_crit > 500);   // la LiPo baja de golpe al acelerar: se exige 0.5 s
}

static float v_puente() {
  if (!hay_bat) return 0.0f;
  return aj.vm_bateria > 0.5f ? vbat_f : aj.vm_fijo;
}

// ------------------------------------------------------------------ motores
static void salida_motores(float izq, float der, float dt) {
  const float ci = aj.inv_izq > 0.5f ? -izq : izq;
  const float cd = aj.inv_der > 0.5f ? -der : der;
  acc.actualizar(ci, cd, v_puente(), dt);
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

static void imprimir_sensores() {
  posicion::normalizar(cal, refl, osc);
  const posicion::Estimacion e = posicion::estimar_posicion(geom, osc, par::UMBRAL_RUIDO, par::CONFIANZA_MIN);
  for (int i = 0; i < NUM_SENSORES; ++i) Serial.printf("%.2f ", osc[i]);
  Serial.printf("| pos=%.1f mm visible=%d cal=%s\n", e.pos_mm, e.linea_visible, cal_valida ? "si" : "NO");
}

static void prueba_motor(float a, float b, int ms) {
  if (!hay_bat) { Serial.println("sin bateria (solo USB): los motores no tienen voltaje"); return; }
  if (ms < 50) ms = 50;
  if (ms > 3000) ms = 3000;
  hw::driver_despierto(true);
  delay(2);                                    // despertar del DRV8833 (tWAKE)
  acc.reiniciar();
  const uint32_t t0 = millis();
  uint32_t tp = micros();
  while (millis() - t0 < (uint32_t)ms) {       // pasa por el tope, la rampa y el límite de corriente
    const uint32_t ahora = micros();
    const float dt = (ahora - tp) * 1e-6f;
    tp = ahora;
    salida_motores(a, b, dt > 0.0f ? dt : 1e-3f);
    delay(2);
  }
  motores_quietos(true);
  delay(150);
  motores_quietos(false);
  hw::driver_despierto(false);
  Serial.printf("ok (ciclo final izq=%.2f der=%.2f, corriente estimada %.2f/%.2f A)\n", acc.ciclo(0), acc.ciclo(1),
                acc.corriente(0), acc.corriente(1));
}

static void ejecutar(char* l) {
  char* c = strtok(l, " ");
  if (!c) return;
  if (!strcmp(c, "ayuda")) {
    Serial.println("estado | get | set <clave> <valor> | save | load | defecto | sens | crudo | bat | perf | tel 0/1");
    Serial.println("m <izq> <der> [ms]  prueba de motores, -1..1 (RUEDAS EN EL AIRE) | cal  inicia la calibracion");
  } else if (!strcmp(c, "estado")) {
    Serial.printf("estado=%s error=%d cal=%s bateria=%.2f V%s\n", nombre(maq.estado()), (int)maq.error(),
                  cal_valida ? "si" : "NO", vbat_f, hay_bat ? (bat_baja ? " (BAJA)" : "") : " (solo USB)");
  } else if (!strcmp(c, "get")) imprimir_ajustes();
  else if (!strcmp(c, "set")) {
    char* k = strtok(nullptr, " ");
    char* v = strtok(nullptr, " ");
    if (!k || !v || !fijar(aj, k, atof(v))) Serial.println("uso: set <clave> <valor> (clave de `get`, dentro de su rango)");
    else { aplicar_ajustes(); Serial.printf("%s=%g (falta `save` para guardarlo)\n", k, atof(v)); }
  } else if (!strcmp(c, "save")) { guardar(); Serial.println("guardado"); }
  else if (!strcmp(c, "load")) { Serial.println(cargar() ? "cargado" : "no hay datos validos"); aplicar_ajustes(); }
  else if (!strcmp(c, "defecto")) { aj = Ajustes(); aplicar_ajustes(); Serial.println("valores por defecto (falta `save`)"); }
  else if (!strcmp(c, "sens")) imprimir_sensores();
  else if (!strcmp(c, "crudo")) {
    Serial.print("on : "); for (int i = 0; i < NUM_SENSORES; ++i) Serial.printf("%4d ", crudo_on[i]);
    Serial.print("\noff: "); for (int i = 0; i < NUM_SENSORES; ++i) Serial.printf("%4d ", crudo_off[i]);
    Serial.println();
  } else if (!strcmp(c, "bat")) Serial.printf("bateria %.2f V (divisor %.2f V + D1 %.2f V)%s\n", vbat_f, hw::v_divisor(),
                                                aj.caida_d1, hay_bat ? "" : " · solo USB");
  else if (!strcmp(c, "perf")) {
    Serial.printf("lectura de sensores %lu us, ciclo maximo %lu us (periodo %lu us), nFAULT=%d\n",
                  (unsigned long)t_lectura_us, (unsigned long)t_ciclo_max_us, par::PERIODO_CONTROL_US, hw::driver_falla());
    t_ciclo_max_us = 0;
  } else if (!strcmp(c, "tel")) { char* v = strtok(nullptr, " "); telemetria = v && atoi(v); }
  else if (!strcmp(c, "m")) {
    char* a = strtok(nullptr, " "); char* b = strtok(nullptr, " "); char* ms = strtok(nullptr, " ");
    if (!a || !b) Serial.println("uso: m <izq> <der> [ms]   ej. m 0.3 0");
    else prueba_motor(atof(a), atof(b), ms ? atoi(ms) : 1000);
  } else if (!strcmp(c, "cal")) Serial.println("oprime el boton CAL (la consola no inicia la calibracion para no mover nada por error)");
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
  cal.reiniciar(NUM_SENSORES);
  const bool hay = cargar();
  geom = BARRA_EN_ARCO ? posicion::geometria_arco(NUM_SENSORES, PASO_SENSORES_MM, RADIO_ARCO_MM, DIST_SENSOR_EJE_MM)
                       : posicion::geometria_recta(NUM_SENSORES, PASO_SENSORES_MM, DIST_SENSOR_EJE_MM);
  aplicar_ajustes();
  maq.reiniciar(millis());
  Serial.printf("\nRobot casero V3 · %d sensores %s · ajustes %s · calibracion %s. Escribe 'ayuda'.\n", NUM_SENSORES,
                SENSORES_DIRECTOS ? "directos" : "con 74HC4067", hay ? "guardados" : "por defecto",
                cal_valida ? "guardada" : "NO");
}

void loop() {
  const uint32_t t = millis();
  if (!maq.motores()) consola();               // sin comandos mientras corre

  const unsigned long ahora = micros();
  if (ahora - t_prev_us < par::PERIODO_CONTROL_US) return;
  const float dt = (ahora - t_prev_us) * 1e-6f;  // dt real, no el nominal
  t_prev_us = ahora;

  // ---- entradas
  leer_sensores();
  medir_bateria(t);
  const Estado antes = maq.estado();
  if (antes == Estado::CALIBRACION) cal.muestrear(refl);
  posicion::normalizar(cal, refl, osc);
  est = posicion::estimar_posicion(geom, osc, par::UMBRAL_RUIDO, par::CONFIANZA_MIN);
  if (maq.motores()) sal = ctl.actualizar(est, dt);

  const bool falla = aj.usar_nfault > 0.5f && hw::driver_falla();
  if (falla) { if (!t_falla) t_falla = t ? t : 1; } else t_falla = 0;

  Entradas in;
  in.start = b_start.pulso(hw::boton_start(), t);
  in.cal = b_cal.pulso(hw::boton_cal(), t);
  in.cal_lista = antes == Estado::CALIBRACION && cal.lista(par::RANGO_CAL_MIN);
  in.cal_valida = cal_valida;
  in.linea_visible = est.linea_visible;
  in.buscando = maq.motores() && sal.buscando;
  in.linea_perdida = maq.motores() && sal.linea_perdida;
  in.hay_bateria = hay_bat;
  in.bat_critica = bat_crit;
  in.falla_driver = t_falla && (t - t_falla > 5);   // nFAULT bajo > 5 ms (la protección del DRV8833 reintenta cada 1.35 ms)

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
    if (e == Estado::ERROR) Serial.printf("ERROR %d (%s)\n", (int)maq.error(), maq.error() == Error::BATERIA ? "bateria" : "driver");
    Serial.printf("-> %s\n", nombre(e));
  }

  // ---- salidas
  hw::driver_despierto(maq.despierto(t));
  if (maq.motores()) salida_motores(sal.izq, sal.der, dt);
  else motores_quietos(maq.frenando(t));

  Contexto cx{e, maq.error(), maq.desde(t), t, est.linea_visible, maq.fin_cal(), t - maq.t_fin_cal(), maq.rechazo(),
              t - maq.t_rechazo(), bat_baja, a_tiempos(aj).cal_max_ms};
  const Indicacion ind = indicar(cx);
  hw::led(ind.led);
  hw::zumbador(ind.tono_hz, aj.zumb_activo > 0.5f);

  if (telemetria && maq.motores() && (++n_ciclos % 4 == 0))
    Serial.printf("%.1f,%d,%.3f,%.3f,%.2f\n", est.pos_mm, (int)est.linea_visible, acc.ciclo(0), acc.ciclo(1), vbat_f);
  const uint32_t dur = micros() - ahora;
  if (dur > t_ciclo_max_us) t_ciclo_max_us = dur;
}
