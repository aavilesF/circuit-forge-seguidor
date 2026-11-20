// Robot de emergencia · pruebas de la lógica en la PC (sin Arduino).  Ejecutar: ./ejecutar.sh  o  .\ejecutar.ps1
// Adaptadas de firmware/robot-casero/pruebas/test_casero.cpp (HISTÓRICO) al hardware vigente: 8 sensores por mux,
// paso 12.7 mm, motores siempre a 6 V, sin zumbador ni nFAULT. Nuevas: mapa de pines contra la GUIA, bits del mux,
// orden físico, batería sin diodo, antirrebote, parada por USB y por ciclo atrasado.
#define _USE_MATH_DEFINES   // M_PI en MinGW/MSVC
#include <math.h>
#include <stdio.h>
#include <string.h>

#include <random>

#include "../emergencia/ajustes.h"
#include "../emergencia/autocal.h"
#include "../emergencia/config.h"
#include "../emergencia/control.h"
#include "../emergencia/estados.h"
#include "../emergencia/filtro.h"
#include "../emergencia/indicadores.h"
#include "../emergencia/motor.h"
#include "../emergencia/posicion.h"
#include "../emergencia/utiles.h"

static int fallas = 0, total = 0;
#define CHECK(c, ...)                                     \
  do {                                                    \
    ++total;                                              \
    if (!(c)) {                                           \
      ++fallas;                                           \
      printf("FALLA %s:%d  %s  ", __FILE__, __LINE__, #c); \
      printf(__VA_ARGS__);                                \
      printf("\n");                                       \
    }                                                     \
  } while (0)
#define CERCA(a, b, tol) CHECK(fabs((a) - (b)) <= (tol), "%g vs %g", (double)(a), (double)(b))

using namespace robot;

// ------------------------------------------------------------------------------------------------ filtro
static void prueba_filtro() {
  CERCA(filtro::mediana3(1, 9, 5), 5, 0);
  CERCA(filtro::mediana3(9, 1, 5), 5, 0);
  CERCA(filtro::mediana3(5, 5, 1), 5, 0);
  filtro::Canal c;
  for (int i = 0; i < 5; ++i) c.paso(1000, 1.0f);
  CERCA(c.paso(4000, 1.0f), 1000, 0);           // un pico aislado no pasa
  CERCA(c.paso(1000, 1.0f), 1000, 0);
  c.paso(3000, 1.0f);
  CERCA(c.paso(3000, 1.0f), 3000, 0);           // un escalón real pasa con 1 muestra de retraso
  filtro::Canal p;
  p.paso(0, 0.5f);
  float y = 0;
  for (int i = 0; i < 30; ++i) y = p.paso(100, 0.5f);
  CERCA(y, 100, 0.01);                          // el pasa-bajas converge
  filtro::Canal q;
  CERCA(q.paso(777, 0.2f), 777, 0);             // la primera muestra pasa directa (sin transitorio desde 0)
}

// ------------------------------------------------------------------------------------------------ DRV8833
static void prueba_drv8833() {
  using motor::Decaimiento;
  motor::Puente p = motor::drv8833(1.0f, Decaimiento::LENTO);
  CHECK(p.in1 == 1.0f && p.in2 == 0.0f, "adelante 100%%");
  p = motor::drv8833(0.3f, Decaimiento::LENTO);
  CHECK(p.in1 == 1.0f && fabsf(p.in2 - 0.7f) < 1e-6f, "adelante lento: IN2 en alto 70%% (freno)");
  p = motor::drv8833(0.0f, Decaimiento::LENTO);
  CHECK(p.in1 == 1.0f && p.in2 == 1.0f, "cero en lento = freno");
  p = motor::drv8833(-0.3f, Decaimiento::LENTO);
  CHECK(fabsf(p.in1 - 0.7f) < 1e-6f && p.in2 == 1.0f, "atrás lento");
  p = motor::drv8833(-2.0f, Decaimiento::LENTO);
  CHECK(p.in1 == 0.0f && p.in2 == 1.0f, "atrás 100%% (recortado)");
  p = motor::drv8833(0.4f, Decaimiento::RAPIDO);
  CHECK(fabsf(p.in1 - 0.4f) < 1e-6f && p.in2 == 0.0f, "adelante rápido");
  p = motor::drv8833(-0.4f, Decaimiento::RAPIDO);
  CHECK(p.in1 == 0.0f && fabsf(p.in2 - 0.4f) < 1e-6f, "atrás rápido");
  // ciclo efectivo = fracción del tiempo en (1,0): en lento es 1 − in2
  for (float d = 0.0f; d <= 1.0f; d += 0.1f) {
    p = motor::drv8833(d, Decaimiento::LENTO);
    CERCA(p.in1 * (1.0f - p.in2), d, 1e-5);
  }
}

// ------------------------------------------------------------------------------------------------ límites del motor
static void prueba_accionamiento() {
  motor::Accionamiento a;
  motor::Limites l;              // pwm_max 0.9, v_motor_max 6, i_max 1.2, i_total 2, rampa 6
  motor::Modelo m;
  a.configurar(m, l);
  CERCA(a.tope(6.0f), 0.90, 1e-6);            // con el MP1584 a 6 V manda el pwm_max
  CERCA(a.tope(8.4f), 6.0 / 8.4, 1e-6);       // VM directo de la LiPo llena: tope por voltaje del N20
  // rampa: en 10 ms el ciclo sube como máximo 0.06
  a.reiniciar();
  a.actualizar(1.0f, 1.0f, 6.0f, 0.010f);
  CERCA(a.ciclo(0), 0.06, 1e-5);
  // llega al tope y no lo pasa
  for (int i = 0; i < 300; ++i) a.actualizar(1.0f, 1.0f, 6.0f, 0.0025f);
  CERCA(a.ciclo(0), 0.90, 1e-4);
  // reversa brusca a toda velocidad: la corriente estimada nunca pasa de i_max
  float imax = 0.0f;
  for (int i = 0; i < 400; ++i) {
    a.actualizar(-1.0f, 1.0f, 6.0f, 0.0025f);
    imax = fmaxf(imax, fabsf(a.corriente(0)));
  }
  CHECK(imax <= l.i_max + 1e-3f, "reversa: corriente estimada %.3f A > %.2f A", imax, l.i_max);
  CERCA(a.ciclo(0), -0.90, 1e-3);
  // motor de baja resistencia (bloqueo 3 A): arranque desde parado limitado por corriente y por la suma
  motor::Modelo duro = motor::Modelo::desde_ficha(6.0f, 1000.0f, 3.0f, 0.1f, 0.08f);
  motor::Limites rapida = l;
  rapida.rampa = 100.0f;
  a.configurar(duro, rapida);
  a.reiniciar();
  float suma = 0.0f, i1 = 0.0f;
  for (int i = 0; i < 200; ++i) {
    a.actualizar(1.0f, 1.0f, 6.0f, 0.0025f);
    i1 = fmaxf(i1, fabsf(a.corriente(0)));
    suma = fmaxf(suma, fabsf(a.corriente(0)) + fabsf(a.corriente(1)));
  }
  CHECK(i1 <= l.i_max + 1e-3f, "arranque: %.3f A por motor", i1);
  CHECK(suma <= l.i_total + 1e-3f, "arranque: %.3f A en total", suma);
  // sin voltaje (solo USB) no hay ciclo
  a.actualizar(1.0f, 1.0f, 0.0f, 0.0025f);
  CHECK(a.ciclo(0) == 0.0f && a.ciclo(1) == 0.0f, "sin VM");
  // ficha → modelo
  motor::Modelo f = motor::Modelo::desde_ficha(6.0f, 1000.0f, 1.0f, 0.07f, 0.08f);
  CERCA(f.R, 6.0, 1e-5);
  CERCA(f.ke, (6.0 - 0.07 * 6.0) / (1000.0 * 2 * M_PI / 60.0), 1e-5);
}

// ------------------------------------------------------------------------------------------------ estados
static void prueba_estados() {
  Maquina m;
  Entradas in;
  uint32_t t = 1000;
  m.reiniciar(t);
  CHECK(m.estado() == Estado::INICIO, "arranca en INICIO");
  m.paso(in, t + 500);
  CHECK(m.estado() == Estado::INICIO, "INICIO dura 0.8 s");
  m.paso(in, t + 800);
  CHECK(m.estado() == Estado::ESPERA && m.entro(), "→ ESPERA");
  CHECK(!m.despierto(t + 800), "puente dormido en ESPERA");
  t += 1000;
  in.start = true;
  m.paso(in, t);
  CHECK(m.estado() == Estado::ESPERA && m.rechazo(), "START sin calibración: no arranca y avisa");
  in.start = false;
  in.cal = true;
  m.paso(in, t += 10);
  CHECK(m.estado() == Estado::CALIBRACION, "CAL → CALIBRACION");
  in.cal = false;
  // sin contraste: a los 15 s termina MAL y regresa a ESPERA
  const uint32_t t_cal = t;
  m.paso(in, t_cal + 14999);
  CHECK(m.estado() == Estado::CALIBRACION, "sigue antes de 15 s");
  m.paso(in, t_cal + 15000);
  CHECK(m.estado() == Estado::ESPERA && m.fin_cal() == FinCal::MAL, "15 s sin contraste → ESPERA (mal)");
  // con contraste: termina sola 1 s después
  in.cal = true;
  m.paso(in, t = t_cal + 16000);
  in.cal = false;
  in.cal_lista = true;
  m.paso(in, t + 2000);
  CHECK(m.estado() == Estado::CALIBRACION, "empieza a contar el segundo extra");
  in.cal_lista = false;
  m.paso(in, t + 2500);                          // se perdió el contraste: se reinicia la cuenta
  in.cal_lista = true;
  m.paso(in, t + 2600);
  m.paso(in, t + 3500);
  CHECK(m.estado() == Estado::CALIBRACION, "la cuenta se reinició");
  m.paso(in, t + 3600);
  CHECK(m.estado() == Estado::LISTO && m.fin_cal() == FinCal::BIEN, "fin automático → LISTO");
  CHECK(m.despierto(t + 3600), "LISTO despierta el puente");
  in.cal_lista = false;
  in.cal_valida = true;
  // START sin batería: no arranca
  t += 4000;
  in.hay_bateria = false;
  in.start = true;
  m.paso(in, t);
  CHECK(m.estado() == Estado::LISTO && m.rechazo(), "sin batería no arranca");
  in.hay_bateria = true;
  m.paso(in, t += 10);
  CHECK(m.estado() == Estado::SIGUIENDO && m.motores(), "START → SIGUIENDO");
  in.start = false;
  in.linea_visible = true;
  m.paso(in, t += 10);
  CHECK(m.estado() == Estado::SIGUIENDO, "sigue");
  in.linea_visible = false;
  in.buscando = true;
  m.paso(in, t += 10);
  CHECK(m.estado() == Estado::RECUPERACION && m.motores(), "sin línea → RECUPERACION");
  in.linea_visible = true;
  in.buscando = false;
  m.paso(in, t += 10);
  CHECK(m.estado() == Estado::SIGUIENDO, "recupera la línea");
  in.linea_visible = false;
  in.buscando = true;
  m.paso(in, t += 10);
  in.linea_perdida = true;
  m.paso(in, t += 10);
  CHECK(m.estado() == Estado::PARADA && !m.motores(), "línea perdida → PARADA");
  CHECK(m.frenando(t + 100) && m.despierto(t + 100), "frena al principio");
  CHECK(!m.frenando(t + 300) && !m.despierto(t + 300), "luego suelta y duerme");
  in.linea_perdida = in.buscando = false;
  in.start = true;
  m.paso(in, t += 500);
  CHECK(m.estado() == Estado::LISTO, "PARADA + START → LISTO (otro START para correr)");
  m.paso(in, t += 10);
  CHECK(m.estado() == Estado::SIGUIENDO, "corre otra vez");
  in.start = false;
  in.bat_critica = true;
  m.paso(in, t += 10);
  CHECK(m.estado() == Estado::ERROR && m.error() == Error::BATERIA, "batería crítica en marcha → ERROR 1");
  in.bat_critica = false;
  in.start = true;
  m.paso(in, t += 10);
  CHECK(m.estado() == Estado::ESPERA && m.error() == Error::NINGUNO, "START borra el error");
  // calibración guardada: START en ESPERA → LISTO; falla del driver
  m.paso(in, t += 10);
  CHECK(m.estado() == Estado::LISTO, "con calibración guardada");
  m.paso(in, t += 10);
  in.start = false;
  in.falla_ciclo = true;
  m.paso(in, t += 10);
  CHECK(m.estado() == Estado::ERROR && m.error() == Error::CICLO, "ciclo de control atrasado en marcha → ERROR 2");
  // CAL o START terminan la calibración antes de tiempo
  Maquina k;
  Entradas e2;
  k.reiniciar(0);
  k.paso(e2, 900);
  e2.cal = true;
  k.paso(e2, 1000);
  e2.cal = false;
  e2.cal_lista = true;
  k.paso(e2, 1100);
  e2.start = true;
  k.paso(e2, 1200);
  CHECK(k.estado() == Estado::LISTO && k.fin_cal() == FinCal::BIEN, "START termina la calibración");
}

// ------------------------------------------------------------------------------------------------ indicadores
static Contexto ctx(Estado e, uint32_t te, uint32_t t) {
  return Contexto{e, Error::NINGUNO, te, t, false, FinCal::NINGUNO, 100000, false, 100000, false, false, 15000};
}

static int flancos_led(Contexto c, uint32_t desde, uint32_t hasta) {
  int n = 0;
  bool prev = false;
  for (uint32_t t = desde; t < hasta; ++t) {
    c.t_ms = t;
    const bool l = indicar(c).led;
    if (l && !prev) ++n;
    prev = l;
  }
  return n;
}

static void prueba_indicadores() {
  Contexto c = ctx(Estado::SIGUIENDO, 5000, 20000);
  c.linea_visible = true;
  CHECK(indicar(c).led, "siguiendo: LED = ve la línea");
  c.linea_visible = false;
  CHECK(!indicar(c).led, "siguiendo sin línea: LED apagado");
  Contexto e = ctx(Estado::ERROR, 5000, 0);
  e.error = Error::BATERIA;
  CHECK(flancos_led(e, 0, 1600) == 1, "error 1 = 1 destello");
  e.error = Error::CICLO;
  CHECK(flancos_led(e, 0, 2000) == 2, "error 2 = 2 destellos");
  CHECK(flancos_led(ctx(Estado::ESPERA, 0, 0), 0, 1000) == 1, "ESPERA 1 Hz");
  CHECK(flancos_led(ctx(Estado::CALIBRACION, 1000, 0), 0, 1000) == 5, "CALIBRACION 5 Hz");
  CHECK(flancos_led(ctx(Estado::CALIBRACION, 13000, 0), 0, 1000) == 10, "últimos 3 s de calibración 10 Hz");
  Contexto f = ctx(Estado::LISTO, 1000, 50000);
  f.fin_cal = FinCal::MAL;
  f.t_desde_fin_cal = 150;
  CHECK(!indicar(f).led, "calibración mala: el LED parpadea (apagado a los 150 ms)");
  f.fin_cal = FinCal::BIEN;
  CHECK(indicar(f).led, "calibración buena: LED fijo");
  Contexto r = ctx(Estado::LISTO, 3000, 3000);
  r.rechazo = true;
  r.t_desde_rechazo = 150;
  CHECK(!indicar(r).led, "rechazo: destellos sobre el LED fijo de LISTO");
  Contexto b = ctx(Estado::LISTO, 3000, 3050);
  b.bat_baja = true;
  CHECK(!indicar(b).led, "batería baja: apagón corto en LISTO");
  b.t_ms = 3500;
  CHECK(indicar(b).led, "batería baja: el resto del tiempo LED fijo");
}

// ------------------------------------------------------------------------------------------------ hardware vigente
// Mapa de pines de GUIA-FIRMWARE.md, sección 2 (también lo compara pruebas/verificar_pines.py con el esquema).
static void prueba_config() {
  CHECK(NUM_SENSORES == 8, "8 sensores (D-V2-41)");
  CHECK(PIN_MUX_S0 == 25 && PIN_MUX_S1 == 26 && PIN_MUX_S2 == 27 && PIN_MUX_S3 == 33, "S0..S3 = 25, 26, 27, 33");
  CHECK(PIN_MUX_SIG == 34 && PIN_EMISORES == 13, "SIG = 34, EMIT_EN = 13");
  CHECK(PIN_START == 4 && PIN_CAL == 14, "START = 4, CAL = 14");
  CHECK(PIN_BATERIA == 36 && PIN_NSLEEP == 16, "VBAT = 36, nSLEEP = 16");
  CHECK(PIN_AIN1 == 19 && PIN_AIN2 == 21 && PIN_BIN1 == 22 && PIN_BIN2 == 23, "motores 19, 21, 22, 23");
  const int pines[] = {PIN_MUX_S0, PIN_MUX_S1, PIN_MUX_S2, PIN_MUX_S3, PIN_MUX_SIG, PIN_EMISORES, PIN_START, PIN_CAL,
                       PIN_BATERIA, PIN_NSLEEP, PIN_AIN1, PIN_AIN2, PIN_BIN1, PIN_BIN2, PIN_LED};
  const int n = sizeof(pines) / sizeof(pines[0]);
  for (int i = 0; i < n; ++i) {
    CHECK(pines[i] < 6 || pines[i] > 11, "GPIO%d es de la memoria flash", pines[i]);
    CHECK(pines[i] != 15 && pines[i] != 17, "GPIO%d debe quedar libre (nFAULT / ventilador)", pines[i]);
    for (int j = i + 1; j < n; ++j) CHECK(pines[i] != pines[j], "GPIO%d repetido", pines[i]);
  }
  // salidas: no pueden ser los GPIO 34–39 (solo entrada); SIG y VBAT deben estar en el ADC1 (32–39)
  const int salidas[] = {PIN_MUX_S0, PIN_MUX_S1, PIN_MUX_S2, PIN_MUX_S3, PIN_EMISORES, PIN_NSLEEP,
                         PIN_AIN1, PIN_AIN2, PIN_BIN1, PIN_BIN2, PIN_LED};
  for (int p : salidas) CHECK(p < 34, "GPIO%d es solo entrada", p);
  CHECK(PIN_MUX_SIG >= 32 && PIN_MUX_SIG <= 39 && PIN_BATERIA >= 32 && PIN_BATERIA <= 39, "lecturas analógicas en ADC1");
#ifdef PIN_ZUMBADOR
  CHECK(false, "no debe existir PIN_ZUMBADOR (D-V2-05)");
#endif
#ifdef PIN_NFAULT
  CHECK(false, "no debe existir PIN_NFAULT (P13)");
#endif
#ifdef PIN_VENTILADOR
  CHECK(false, "no debe existir PIN_VENTILADOR (EM-01)");
#endif
}

static void prueba_utiles() {
  // tabla de la GUIA, sección 3: S3 es el MSB
  for (int c = 0; c < 16; ++c) {
    const util::BitsMux b = util::bits_mux(c);
    CHECK(b.s0 + 2 * b.s1 + 4 * b.s2 + 8 * b.s3 == c, "canal %d", c);
  }
  CHECK(util::bits_mux(5).s0 == 1 && util::bits_mux(5).s1 == 0 && util::bits_mux(5).s2 == 1 && util::bits_mux(5).s3 == 0,
        "SEN6 = C5 = 0101");
  CHECK(util::bits_mux(7).s3 == 0, "los 8 sensores no usan S3");
  // orden físico
  CHECK(util::canal_de_sensor(0, 8, false) == 0 && util::canal_de_sensor(7, 8, false) == 7, "SEN1 a la izquierda");
  CHECK(util::canal_de_sensor(0, 8, true) == 7 && util::canal_de_sensor(7, 8, true) == 0, "invertido: SEN8 a la izquierda");
  bool usados[8] = {};
  for (int i = 0; i < 8; ++i) usados[util::canal_de_sensor(i, 8, true)] = true;
  for (int i = 0; i < 8; ++i) CHECK(usados[i], "invertido cubre C%d", i);
  // batería: 8.4 V → 2.084 V en el pin (100k/33k), sin caída de diodo
  CERCA(util::volts_bateria(2084.2f, DIVISOR_BATERIA), 8.40, 0.01);
  CERCA(util::volts_bateria(0.0f, DIVISOR_BATERIA), 0.0, 1e-6);
  // calibración medida (20 nov): 2.1 V en GPIO36 → ~10.0 V de batería
  CERCA(util::volts_bateria(2100.0f, FACTOR_BATERIA), 10.0, 0.01);
  // batería definitiva 2S Li-ion (8.4 V cargada): umbrales ordenados, ≥ 3.0 V/celda y máximo dentro del ADC
  const Ajustes ab;
  CHECK(ab.bat_critica < ab.bat_baja && ab.bat_baja < 8.4f && 8.4f < BAT_MAX_2S, "umbrales 2S Li-ion ordenados");
  CHECK(ab.bat_critica / 2.0f >= 3.0f, "bat_critica >= 3.0 V por celda");
  CHECK(BAT_MAX_2S / FACTOR_BATERIA < 3.0f, "el maximo esperado cabe en el rango del ADC (11 dB)");
  // antirrebote: un rebote de 10 ms no cuenta; oprimido estable 25 ms → un solo pulso
  util::Boton b;
  int pulsos = 0;
  uint32_t t = 1000;
  for (int k = 0; k < 10; ++k) pulsos += b.pulso(true, t++);      // 10 ms oprimido
  for (int k = 0; k < 10; ++k) pulsos += b.pulso(false, t++);     // suelta
  CHECK(pulsos == 0, "rebote corto ignorado (%d)", pulsos);
  for (int k = 0; k < 3; ++k) { pulsos += b.pulso(true, t++); pulsos += b.pulso(false, t++); }   // ruido de contacto
  for (int k = 0; k < 100; ++k) pulsos += b.pulso(true, t++);     // ya estable
  CHECK(pulsos == 1, "una pulsación = un pulso (%d)", pulsos);
  for (int k = 0; k < 100; ++k) pulsos += b.pulso(false, t++);
  CHECK(pulsos == 1, "soltar no da pulso");
}

static void prueba_paradas() {
  Maquina m;
  Entradas in;
  m.reiniciar(0);
  m.paso(in, 900);
  in.cal_valida = true;
  in.start = true;
  m.paso(in, 1000);
  m.paso(in, 1010);
  CHECK(m.estado() == Estado::SIGUIENDO, "corre");
  in.start = false;
  in.parar = true;
  m.paso(in, 1020);
  CHECK(m.estado() == Estado::PARADA && !m.motores(), "byte por USB en marcha → PARADA");
  CHECK(m.frenando(1100) && !m.despierto(1400), "frena y luego duerme el puente");
  in.parar = false;
  in.start = true;
  m.paso(in, 1500);
  m.paso(in, 1510);
  in.start = false;
  in.buscando = true;
  m.paso(in, 1520);
  CHECK(m.estado() == Estado::RECUPERACION, "recuperación");
  in.parar = true;
  m.paso(in, 1530);
  CHECK(m.estado() == Estado::PARADA, "parar también en RECUPERACION");
  in.parar = false;
  in.buscando = false;
  in.falla_ciclo = true;
  m.paso(in, 1540);
  CHECK(m.estado() == Estado::PARADA, "ciclo lento fuera de marcha no causa error");
  in.falla_ciclo = false;
  in.parar = true;                                   // fuera de marcha `parar` no hace nada
  in.start = true;
  m.paso(in, 2000);
  CHECK(m.estado() == Estado::LISTO, "PARADA + START → LISTO");
  in.start = false;
  m.paso(in, 2010);
  CHECK(m.estado() == Estado::LISTO && m.despierto(2010), "parar en LISTO no cambia nada");
}

// ------------------------------------------------------------------------------------------------ ajustes
static void prueba_ajustes() {
  Ajustes a;
  CHECK(fijar(a, "kp", 0.05f) && a.kp == 0.05f, "fijar kp");
  CHECK(!fijar(a, "kp", 5.0f) && a.kp == 0.05f, "fuera de rango");
  CHECK(!fijar(a, "nada", 1.0f), "clave desconocida");
  CHECK(!fijar(a, "vbase", NAN), "NaN");
  CHECK(!fijar(a, "t_cal_max", 20.0f), "la calibración no puede pasar de 15 s");
  int n;
  const EntradaAjuste* t = tabla_ajustes(&n);
  Ajustes d;
  for (int i = 0; i < n; ++i) {
    const float v = *campo(d, t[i]);
    CHECK(v >= t[i].min && v <= t[i].max, "%s por defecto (%g) fuera de su rango", t[i].nombre, v);
    for (int j = i + 1; j < n; ++j) CHECK(strcmp(t[i].nombre, t[j].nombre) != 0, "nombre repetido %s", t[i].nombre);
  }
  CHECK(n * sizeof(float) == sizeof(Ajustes), "la tabla cubre todos los campos (%d de %zu)", n, sizeof(Ajustes) / sizeof(float));
  Guardado g{};
  g.a = a;
  g.n_cal = 8;
  sellar(g);
  CHECK(valido(g), "imagen sellada válida");
  g.a.kd += 0.001f;
  CHECK(!valido(g), "un cambio rompe el CRC");
  const uint8_t prueba[] = {'1', '2', '3', '4', '5', '6', '7', '8', '9'};
  CHECK(crc32(prueba, 9) == 0xCBF43926u, "CRC32 estándar");
  CHECK(a_tiempos(Ajustes()).cal_max_ms == 15000, "15 s");
}

// ------------------------------------------------------------------------------------------------ lazo cerrado
// Pista: círculo de radio Rc (línea de 25 mm). Robot: 2 ruedas de 28 mm a 80 mm [E], barra recta de 8 sensores a
// 12.7 mm, 100 mm delante del eje [P]. Sensores con ruido gaussiano y picos; motor real con τ distinto al del modelo del firmware.
struct Sim {
  double x, y, th, wl = 0, wr = 0;
};

static double simular(double Rc, double v_fuente, double segundos, bool* perdio, double* v_media,
                      const Ajustes& aj = Ajustes()) {
  const double r = 0.014, W = 0.080, tau_real = 0.05;
  const int N = 8;
  posicion::Geometria g = posicion::geometria_recta(N, PASO_SENSORES_MM, DIST_SENSOR_EJE_MM);
  posicion::Calibracion cal;
  cal.reiniciar(N);
  for (int i = 0; i < N; ++i) { cal.minimo[i] = 200; cal.maximo[i] = 3700; }
  filtro::Arreglo fil;
  ControladorLinea ctl(a_control(aj));
  ctl.reiniciar();
  motor::Accionamiento acc;
  acc.configurar(a_modelo(aj), a_limites(aj));
  acc.reiniciar();
  std::mt19937 rng(7);
  std::normal_distribution<double> ruido(0.0, 40.0);
  std::uniform_real_distribution<double> u01(0.0, 1.0);
  const posicion::ModoSensor modo = {true, true, 4095};
  Sim s{Rc / 1000.0, 0.0, M_PI / 2};       // en la línea, avanzando en sentido antihorario
  const double dt = 0.0025;
  double peor = 0, dist = 0;
  *perdio = false;
  for (int k = 0; k < (int)(segundos / dt); ++k) {
    // sensores
    float refl[16];
    const double hx = cos(s.th), hy = sin(s.th), rx = sin(s.th), ry = -cos(s.th);
    for (int i = 0; i < N; ++i) {
      const double px = s.x + (g.y[i] * hx + g.x[i] * rx) / 1000.0, py = s.y + (g.y[i] * hy + g.x[i] * ry) / 1000.0;
      const double d = fabs(sqrt(px * px + py * py) * 1000.0 - Rc);
      double osc = (15.0 - d) / 5.0;
      osc = osc < 0 ? 0 : (osc > 1 ? 1 : osc);
      double on = 300 + osc * 3500 + ruido(rng);
      if (u01(rng) < 0.01) on += 2000;                                 // pico aislado
      const double off = 4000 + ruido(rng);
      refl[i] = posicion::reflectancia(modo, (int)on, (int)off);
    }
    fil.aplicar(refl, N, aj.alfa);
    float osc[16];
    posicion::normalizar(cal, refl, osc);
    const posicion::Estimacion e = posicion::estimar_posicion(g, osc, 0.10f, 0.30f);
    const SalidaControl sc = ctl.actualizar(e, (float)dt);
    if (sc.linea_perdida) { *perdio = true; break; }
    acc.actualizar(sc.izq, sc.der, (float)v_fuente, (float)dt);
    // motor "real" y cinemática
    const double ke = aj.m_ke;
    s.wl += dt / (tau_real + dt) * (acc.ciclo(0) * v_fuente / ke - s.wl);
    s.wr += dt / (tau_real + dt) * (acc.ciclo(1) * v_fuente / ke - s.wr);
    const double v = r * (s.wl + s.wr) / 2, w = r * (s.wr - s.wl) / W;
    s.x += v * cos(s.th) * dt;
    s.y += v * sin(s.th) * dt;
    s.th += w * dt;
    dist += v * dt;
    if (k * dt > 1.0) {                                                // después del transitorio
      // desvío de la BARRA de sensores (el eje corta la curva por geometría: en R = 200 mm queda 27 mm adentro)
      const double bx = s.x + 0.100 * cos(s.th), by = s.y + 0.100 * sin(s.th);
      peor = fmax(peor, fabs(sqrt(bx * bx + by * by) * 1000.0 - Rc));
    }
  }
  *v_media = dist / segundos;
  return peor;
}

static Ajustes con_perfil(const char* p) {
  Ajustes a;
  aplicar_perfil(a, p);
  return a;
}

static void prueba_lazo() {
  // velocidad media mínima esperada por perfil (N20 de 1000 rpm [E]; con otro motor cambia la escala, no la forma)
  const struct { const char* p; double vmin; } casos[] = {{"seguro", 0.20}, {"normal", 0.30}, {"rapido", 0.45}};
  for (const auto& c : casos) {
    const Ajustes a = con_perfil(c.p);
    for (double Rc : {600.0, 300.0, 200.0}) {
      bool perdio;
      double vm;
      const double peor = simular(Rc, 6.0, 6.0, &perdio, &vm, a);
      printf("  lazo %-6s: R=%3.0f mm → desvío máx. de la barra %4.1f mm, %.2f m/s%s\n", c.p, Rc, peor, vm,
             perdio ? " (PERDIÓ LA LÍNEA)" : "");
      CHECK(!perdio, "%s perdió la línea en R=%g", c.p, Rc);
      CHECK(peor < 15.0, "%s: desvío %.1f mm en R=%g", c.p, peor, Rc);
      CHECK(vm > c.vmin, "%s: velocidad media %.2f m/s", c.p, vm);
    }
  }
}

// ------------------------------------------------------------------------------------------------ autocalibración
// Robot parado sobre una recta (línea en x = 0, robot mirando a +y). Gira en el sitio con el mismo modelo de motor.
struct ResAutocal { autocal::Fase fase; bool cal_ok, centrado, al_reves; double t_s, angulo_final_deg; };

static ResAutocal simular_autocal(bool hay_linea, bool motores_al_reves, uint32_t mascara_s) {
  const double r = 0.014, W = 0.080, tau_real = 0.05, dt = 0.0025;
  const int N = 8;
  Ajustes aj;
  posicion::Geometria g = posicion::geometria_recta(N, aj.paso_mm, DIST_SENSOR_EJE_MM);
  posicion::Calibracion cal;
  filtro::Arreglo fil;
  motor::Accionamiento acc;
  acc.configurar(a_modelo(aj), a_limites(aj));
  acc.reiniciar();
  autocal::Param p;
  p.u = aj.ac_u; p.t_max_s = aj.ac_t; p.contraste = aj.contraste; p.mascara = mascara_s;
  autocal::AutoCal ac;
  ac.iniciar(N, p, cal);
  std::mt19937 rng(11);
  std::normal_distribution<double> ruido(0.0, 40.0);
  const posicion::ModoSensor modo = {true, true, 4095};
  Sim s{0.0, 0.0, M_PI / 2};
  autocal::Salida o;
  double t = 0;
  for (int k = 0; k < 8000; ++k, t += dt) {
    float refl[16];
    const double hx = cos(s.th), rx = sin(s.th);
    for (int i = 0; i < N; ++i) {
      const double px = s.x + (g.y[i] * hx + g.x[i] * rx) / 1000.0;
      const double d = hay_linea ? fabs(px * 1000.0) : 1e9;
      double osc = (15.0 - d) / 5.0;
      osc = osc < 0 ? 0 : (osc > 1 ? 1 : osc);
      refl[i] = posicion::reflectancia(modo, (int)(300 + osc * 3500 + ruido(rng)), (int)(4000 + ruido(rng)));
    }
    fil.aplicar(refl, N, aj.alfa);
    o = ac.paso(refl, cal, g, (float)dt);
    if (o.termino) break;
    const float iz = motores_al_reves ? -o.izq : o.izq, de = motores_al_reves ? -o.der : o.der;
    acc.actualizar(iz, de, 6.0f, (float)dt);
    s.wl += dt / (tau_real + dt) * (acc.ciclo(0) * 6.0 / aj.m_ke - s.wl);
    s.wr += dt / (tau_real + dt) * (acc.ciclo(1) * 6.0 / aj.m_ke - s.wr);
    s.th += r * (s.wr - s.wl) / W * dt;
  }
  return ResAutocal{ac.fase(), o.cal_ok, o.centrado, ac.al_reves(), t, (s.th - M_PI / 2) * 180.0 / M_PI};
}

static void prueba_autocal() {
  ResAutocal r = simular_autocal(true, false, 0xFF);
  printf("  autocal: %s en %.2f s, cal_ok=%d centrado=%d, ángulo final %+.1f°\n", autocal::nombre(r.fase), r.t_s, r.cal_ok,
         r.centrado, r.angulo_final_deg);
  CHECK(r.fase == autocal::Fase::LISTA && r.cal_ok && r.centrado, "autocal sobre la línea");
  CHECK(r.t_s < 6.0, "autocal tardó %.2f s", r.t_s);
  CHECK(fabs(r.angulo_final_deg) < 10.0, "termina casi derecho (%.1f°)", r.angulo_final_deg);
  r = simular_autocal(true, false, 0xFF & ~(1u << 4));   // 5.º sensor ignorado
  CHECK(r.fase == autocal::Fase::LISTA && r.cal_ok, "autocal con un sensor ignorado");
  r = simular_autocal(false, false, 0xFF);
  CHECK(r.fase == autocal::Fase::FALLA && !r.cal_ok, "sin línea: FALLA");
  CHECK(r.t_s <= 1.1 && !r.al_reves, "sin línea: falla por tiempo de la fase 1 (%.2f s)", r.t_s);
  r = simular_autocal(true, true, 0xFF);
  CHECK(r.fase == autocal::Fase::FALLA && !r.cal_ok && r.al_reves, "motores al revés: FALLA (no da una calibración falsa)");
  CHECK(r.t_s < 0.5 && fabs(r.angulo_final_deg) < 60.0, "motores al revés: aborta pronto (%.2f s, %.0f°)", r.t_s,
        r.angulo_final_deg);
  posicion::Calibracion c;
  autocal::AutoCal a;
  autocal::Param p;
  p.mascara = 0x01;   // un solo sensor: no hay posición
  a.iniciar(8, p, c);
  CHECK(a.fase() == autocal::Fase::FALLA, "con un solo sensor activo no empieza");
}

// ------------------------------------------------------------------------------------------------ nuevas (v2.0)
static void prueba_utiles2() {
  CHECK(util::contar_activos(0xFF, 8) == 8 && util::contar_activos(0xEF, 8) == 7, "contar activos");
  CHECK(util::primer_activo(0xFE, 8) == 1 && util::ultimo_activo(0x7F, 8) == 6, "extremos activos");
  posicion::Calibracion c;
  c.reiniciar(8);
  for (int i = 0; i < 8; ++i) { c.minimo[i] = 200; c.maximo[i] = 3000; }
  CHECK(util::cal_lista(c, 150, 0xFF), "calibración completa");
  c.maximo[3] = 250;   // el 4.º sensor no vio blanco
  CHECK(!util::cal_lista(c, 150, 0xFF), "un sensor sin contraste invalida la calibración");
  CHECK(util::cal_lista(c, 150, 0xFF & ~(1u << 3)), "…salvo que esté ignorado en la máscara");
  CHECK(!util::cal_lista(c, 150, 0x08), "con un solo sensor (el malo) no sirve");
  float o[8] = {1, 1, 1, 1, 1, 1, 1, 1};
  util::enmascarar(o, 8, 0x7F);
  CHECK(o[7] == 0.0f && o[6] == 1.0f, "enmascarar pone en blanco el ignorado");
  CHECK(util::contar_oscuros(o, 8, 0.7f, 0x7F) == 7, "todos los activos negros");
  CERCA(util::v_puente(true, 8.0f, 6.0f, 0.6f), 6.0, 1e-6);
  CERCA(util::v_puente(true, 6.2f, 6.0f, 0.6f), 5.6, 1e-5);   // el regulador ya no alcanza
  CERCA(util::v_puente(false, 8.0f, 6.0f, 0.6f), 0.0, 1e-6);
  float f;
  int k;
  CHECK(util::leer_float("0.012", &f) && fabsf(f - 0.012f) < 1e-7f, "número válido");
  CHECK(!util::leer_float("x", &f) && !util::leer_float("0.1x", &f) && !util::leer_float("", &f) &&
            !util::leer_float(nullptr, &f) && !util::leer_float("nan", &f),
        "texto inválido rechazado (antes atof daba 0)");
  CHECK(util::leer_int("7", 0, 15, &k) && k == 7, "entero válido");
  CHECK(!util::leer_int("16", 0, 15, &k) && !util::leer_int("2.5", 0, 15, &k) && !util::leer_int("-1", 0, 15, &k),
        "entero fuera de rango o con decimales");
}

static void prueba_rampa_freno() {
  motor::Accionamiento a;
  motor::Limites l;
  l.rampa = 4.0f;
  l.rampa_freno = 12.0f;
  l.pwm_max = 1.0f;
  l.i_max = 1.5f;
  l.i_total = 3.0f;
  motor::Modelo m = motor::Modelo::desde_ficha(6.0f, 1000.0f, 0.5f, 0.05f, 0.08f);   // motor suave: no limita corriente
  a.configurar(m, l);
  a.reiniciar();
  a.actualizar(1.0f, 1.0f, 6.0f, 0.010f);
  CERCA(a.ciclo(0), 0.04, 1e-5);                 // acelera con rampa (4/s)
  for (int i = 0; i < 400; ++i) a.actualizar(0.6f, 0.6f, 6.0f, 0.0025f);
  CERCA(a.ciclo(0), 0.6, 1e-4);
  a.actualizar(0.0f, 0.0f, 6.0f, 0.010f);
  CERCA(a.ciclo(0), 0.48, 1e-4);                 // frena con rampa_freno (12/s)
  for (int i = 0; i < 400; ++i) a.actualizar(-0.6f, -0.6f, 6.0f, 0.0025f);
  CHECK(a.ciclo(0) < -0.59f, "llega a reversa");
  a.actualizar(0.6f, 0.6f, 6.0f, 0.010f);
  CHECK(a.ciclo(0) > -0.6f + 0.11f, "salir de reversa también es frenar (%.3f)", a.ciclo(0));
}

static void prueba_estados2() {
  // arranque diferido
  Maquina m;
  Tiempos tp;
  tp.arranque_ms = 500;
  m.fijar_tiempos(tp);
  Entradas in;
  m.reiniciar(0);
  m.paso(in, 900);
  in.cal_valida = true;
  in.start = true;
  m.paso(in, 1000);                           // ESPERA → LISTO
  m.paso(in, 1010);                           // START en LISTO: arma
  in.start = false;
  CHECK(m.estado() == Estado::LISTO && m.armando() && !m.motores(), "START arma sin mover");
  m.paso(in, 1500);
  CHECK(m.armando(), "a los 490 ms sigue esperando");
  m.paso(in, 1510);
  CHECK(m.estado() == Estado::SIGUIENDO && !m.armando(), "a los 500 ms arranca");
  // cancelar con START, CAL, o por perder la batería
  Maquina c;
  c.fijar_tiempos(tp);
  c.reiniciar(0);
  c.paso(in, 900);
  in.start = true;
  c.paso(in, 1000);
  c.paso(in, 1010);
  in.start = false;
  CHECK(c.armando(), "armado");
  in.start = true;
  c.paso(in, 1100);
  in.start = false;
  CHECK(c.estado() == Estado::LISTO && !c.armando(), "segundo START cancela");
  c.paso(in, 2000);
  CHECK(c.estado() == Estado::LISTO, "no arranca solo después de cancelar");
  in.start = true;
  c.paso(in, 2010);
  in.start = false;
  in.cal = true;
  c.paso(in, 2020);
  in.cal = false;
  CHECK(c.estado() == Estado::CALIBRACION, "CAL cancela y calibra");
  Maquina b;
  b.fijar_tiempos(tp);
  b.reiniciar(0);
  b.paso(in, 900);
  in.start = true;
  b.paso(in, 1000);
  b.paso(in, 1010);
  in.start = false;
  in.hay_bateria = false;
  b.paso(in, 1100);
  CHECK(b.estado() == Estado::LISTO && !b.armando() && b.rechazo(), "sin batería durante la espera: no arranca");
  in.hay_bateria = true;

  // paradas en marcha con su motivo
  struct { const char* que; void (*poner)(Entradas&); Estado fin; Motivo mot; } casos[] = {
      {"CAL", [](Entradas& e) { e.cal = true; }, Estado::PARADA, Motivo::CAL},
      {"USB", [](Entradas& e) { e.parar = true; }, Estado::PARADA, Motivo::USB},
      {"levantado", [](Entradas& e) { e.levantado = true; }, Estado::PARADA, Motivo::LEVANTADO},
      {"línea perdida", [](Entradas& e) { e.linea_perdida = true; }, Estado::PARADA, Motivo::LINEA_PERDIDA},
      {"sin batería", [](Entradas& e) { e.hay_bateria = false; }, Estado::ERROR, Motivo::SIN_BATERIA},
      {"batería crítica", [](Entradas& e) { e.bat_critica = true; }, Estado::ERROR, Motivo::BATERIA},
      {"ciclo", [](Entradas& e) { e.falla_ciclo = true; }, Estado::ERROR, Motivo::CICLO},
  };
  for (const auto& k : casos) {
    Maquina q;
    Entradas e;
    e.cal_valida = true;
    q.reiniciar(0);
    q.paso(e, 900);
    e.start = true;
    q.paso(e, 1000);
    q.paso(e, 1010);
    e.start = false;
    q.paso(e, 1020);
    CHECK(q.estado() == Estado::SIGUIENDO, "%s: corre", k.que);
    k.poner(e);
    q.paso(e, 1030);
    CHECK(q.estado() == k.fin && q.motivo() == k.mot && !q.motores(), "%s: para con su motivo", k.que);
    CHECK(q.frenando(1100) && q.despierto(1100), "%s: frena al parar", k.que);
    CHECK(!q.frenando(1400) && !q.despierto(1400), "%s: luego suelta y duerme el puente", k.que);
    CHECK(nombre(q.motivo()) && strlen(nombre(q.motivo())) > 2, "%s: motivo con texto", k.que);
  }
  // ERROR fuera de marcha no frena (no hay nada que frenar); calibración externa
  Maquina x;
  x.reiniciar(0);
  CHECK(!x.calibracion_externa(true, 10), "en INICIO no se acepta calibración externa");
  x.paso(in, 900);
  CHECK(x.calibracion_externa(true, 1000) && x.estado() == Estado::LISTO && x.fin_cal() == FinCal::BIEN,
        "autocal buena → LISTO");
  CHECK(x.calibracion_externa(false, 1100) && x.estado() == Estado::ESPERA, "autocal mala → ESPERA");
}

static void prueba_indicadores2() {
  Contexto a = ctx(Estado::LISTO, 100, 0);
  a.armando = true;
  CHECK(flancos_led(a, 0, 1000) >= 12, "esperando el arranque: parpadeo muy rápido (%d)", flancos_led(a, 0, 1000));
  a.armando = false;
  CHECK(flancos_led(a, 0, 1000) <= 1, "LISTO normal: fijo");
}

static void prueba_ajustes2() {
  Ajustes a;
  const char* motivo = nullptr;
  CHECK(coherente(a, &motivo), "fábrica coherente (%s)", motivo ? motivo : "");
  CHECK(!fijar(a, "bat_critica", 7.0f), "bat_critica ≥ bat_baja rechazado");
  CHECK(!fijar(a, "inv_izq", 0.5f), "inversión solo 0/1");
  CHECK(!fijar(a, "mascara", 100.5f), "máscara entera");
  CHECK(!fijar(a, "sobremuestreo", 2.5f), "sobremuestreo entero");
  CHECK(fijar(a, "inv_sens", 1.0f) && a.inv_sens == 1.0f, "inv_sens por consola");
  CHECK(fijar(a, "mascara", 239.0f) && mascara(a) == 239u, "máscara por consola");
  int n;
  const EntradaAjuste* t = tabla_ajustes(&n);
  for (int i = 0; i < n; ++i) CHECK(t[i].ayuda && strlen(t[i].ayuda) > 3, "%s sin ayuda", t[i].nombre);
  CHECK(buscar("kp") && !buscar("zumb_activo") && !buscar("usar_nfault") && !buscar("caida_d1") && !buscar("vm_bateria"),
        "sin parámetros del hardware histórico");
  for (const char* p : {"seguro", "normal", "rapido"}) {
    Ajustes b;
    b.inv_izq = 1.0f; b.mascara = 127.0f;
    CHECK(aplicar_perfil(b, p), "perfil %s existe", p);
    CHECK(coherente(b, nullptr), "perfil %s coherente", p);
    CHECK(b.inv_izq == 1.0f && b.mascara == 127.0f, "perfil %s no toca inversiones ni sensores", p);
    for (int i = 0; i < n; ++i) {
      const float v = *campo(b, t[i]);
      CHECK(v >= t[i].min && v <= t[i].max, "perfil %s: %s=%g fuera de rango", p, t[i].nombre, v);
    }
  }
  Ajustes s = con_perfil("seguro"), r = con_perfil("rapido");
  CHECK(s.vbase < r.vbase && s.pwm_max <= r.pwm_max, "el perfil rápido es más rápido");
  Ajustes d;
  CHECK(d.vbase == s.vbase && d.pwm_max == s.pwm_max && d.rampa == s.rampa, "fábrica = perfil seguro");
  CHECK(!aplicar_perfil(d, "turbo"), "perfil desconocido");
  Guardado g{};
  g.a = Ajustes();
  g.a.bat_critica = 8.0f;   // incoherente (corrupción o versión vieja)
  sellar(g);
  CHECK(!valido(g), "no se cargan ajustes incoherentes aunque el CRC esté bien");
  CHECK(a_tiempos(Ajustes()).arranque_ms == 500, "t_arranque 0.5 s → 500 ms");
}

// ------------------------------------------------------------------------------------------------ turbo de recta (v2.1)
static posicion::Estimacion est_linea(float pos, float conf = 2.0f, bool vis = true) {
  return posicion::Estimacion{pos, conf, vis};
}

static ParamControl param_turbo(const char* perfil) {
  Ajustes a;
  Turbo t;
  aplicar_perfil(a, t, perfil);
  return a_control(a, t);
}

static void prueba_turbo_control() {
  const float dt = 0.0025f;
  // 1. apagado (v_recta <= vbase): salida idéntica a la V1, turbo siempre 0
  {
    ParamControl p0 = param_turbo("seguro");
    ParamControl p1 = p0;
    p1.v_recta = p1.vbase;
    ControladorLinea a(p0), b(p1);
    std::mt19937 rng(5);
    std::uniform_real_distribution<float> u(-40.0f, 40.0f), u01(0.0f, 1.0f);
    bool iguales = true;
    for (int k = 0; k < 4000; ++k) {
      const posicion::Estimacion e = est_linea(u(rng), 2.0f, u01(rng) > 0.05f);
      const SalidaControl sa = a.actualizar(e, dt), sb = b.actualizar(e, dt);
      iguales = iguales && sa.izq == sb.izq && sa.der == sb.der && sa.turbo == 0.0f && sb.turbo == 0.0f;
    }
    CHECK(iguales, "turbo apagado: salida idéntica y turbo = 0");
  }
  for (const char* perfil : {"normal", "rapido"}) {
    const ParamControl p = param_turbo(perfil);
    CHECK(p.v_recta > p.vbase, "%s: turbo activo en el perfil", perfil);
    // 2. aceleración progresiva: espera t_confirmar y sube a ritmo dt/t_acel; llega a 1
    ControladorLinea c(p);
    float g_prev = 0.0f, salto = 0.0f;
    int ciclos_sin = 0;
    for (int k = 0; k < 400; ++k) {
      const float g = c.actualizar(est_linea(0.0f), dt).turbo;
      if (g == 0.0f) ++ciclos_sin;
      salto = fmaxf(salto, g - g_prev);
      g_prev = g;
    }
    CHECK(ciclos_sin >= (int)(p.t_confirmar_s / dt) - 1, "%s: confirma la recta antes de acelerar (%d ciclos)", perfil,
          ciclos_sin);
    CHECK(salto <= dt / p.t_acel_s + 1e-6f, "%s: el turbo sube progresivo (salto %.4f)", perfil, salto);
    CHECK(g_prev == 1.0f, "%s: llega al turbo completo", perfil);
    const SalidaControl lleno = c.actualizar(est_linea(0.0f), dt);
    CERCA(lleno.v, p.v_recta, 1e-5);
    // 3. cancelaciones inmediatas (mismo ciclo)
    auto lleno_otra_vez = [&]() { for (int k = 0; k < 400; ++k) c.actualizar(est_linea(0.0f), dt); };
    CHECK(c.actualizar(est_linea(0.0f, 0.0f, false), dt).turbo == 0.0f, "%s: se cancela al no ver la línea (hueco)", perfil);
    lleno_otra_vez();
    CHECK(c.actualizar(est_linea(0.0f, 0.5f), dt).turbo == 0.0f, "%s: se cancela con confianza baja", perfil);
    lleno_otra_vez();
    CHECK(c.actualizar(est_linea(0.0f), dt, false).turbo == 0.0f, "%s: se cancela sin permiso (batería/ciclo/estado)", perfil);
    lleno_otra_vez();
    // 4. error fuera: un ciclo suelto (ruido) no cancela; dos seguidos (5 ms) sí
    CHECK(c.actualizar(est_linea(8.0f), dt).turbo > 0.0f, "%s: un pico de 8 mm no lo cancela", perfil);
    CHECK(c.actualizar(est_linea(8.0f), dt).turbo == 0.0f, "%s: 8 mm sostenidos 5 ms lo cancelan", perfil);
    // 5. histéresis: con 4.5 mm (entre in y out) no entra, pero si ya estaba dentro sigue
    ControladorLinea h(p);
    for (int k = 0; k < 400; ++k) h.actualizar(est_linea(4.5f), dt);
    CHECK(h.actualizar(est_linea(4.5f), dt).turbo == 0.0f, "%s: con 4.5 mm no entra", perfil);
    for (int k = 0; k < 400; ++k) h.actualizar(est_linea(0.0f), dt);
    CHECK(h.actualizar(est_linea(4.5f), dt).turbo > 0.0f && h.actualizar(est_linea(4.5f), dt).turbo > 0.0f,
          "%s: dentro del modo recta, 4.5 mm no lo cancela (histéresis)", perfil);
    // 6. error que cambia rápido cerca del centro: no entra
    ControladorLinea d(p);
    float tq = 0.0f;
    bool entro = false;
    for (int k = 0; k < 400; ++k, tq += dt) entro |= d.actualizar(est_linea(2.5f * sinf(2.0f * 3.14159f * 8.0f * tq)), dt).turbo > 0.0f;
    CHECK(!entro, "%s: con el error oscilando rápido no entra", perfil);
    // 7. reiniciar (cada arranque) lo apaga; la búsqueda nunca tiene turbo
    lleno_otra_vez();
    c.reiniciar();
    CHECK(c.actualizar(est_linea(0.0f), dt).turbo == 0.0f, "%s: reiniciar apaga el turbo", perfil);
    lleno_otra_vez();
    SalidaControl sb{};
    for (int k = 0; k < 40; ++k) sb = c.actualizar(est_linea(0.0f, 0.0f, false), dt);
    CHECK(sb.buscando && sb.turbo == 0.0f && fabsf(sb.v - p.vbase * p.vbusqueda_rel) < 1e-5f,
          "%s: en búsqueda no hay turbo (v = vbase·v_busq)", perfil);
  }
}

static void prueba_turbo_ajustes() {
  // el bloque "g" no cambia de formato: inversiones y calibración guardadas siguen válidas
  CHECK(sizeof(Ajustes) == 48 * sizeof(float), "Ajustes sigue con 48 campos (%zu B)", sizeof(Ajustes));
  CHECK(VERSION == 2, "versión del bloque g sin cambios");
  Turbo t0;
  CHECK(!(t0.v_recta > Ajustes().vbase), "de fábrica el turbo está apagado");
  CHECK(!(a_control(Ajustes()).v_recta > a_control(Ajustes()).vbase), "a_control sin turbo: apagado");
  struct { const char* p; float vr; } esperado[] = {{"seguro", 0.0f}, {"normal", 0.42f}, {"rapido", 0.55f}};
  for (const auto& e : esperado) {
    Ajustes a;
    Turbo t;
    a.inv_izq = 1.0f;
    CHECK(aplicar_perfil(a, t, e.p) && t.v_recta == e.vr && a.inv_izq == 1.0f, "perfil %s: v_recta %.2f", e.p, e.vr);
  }
  int n;
  const EntradaAjuste* tt = tabla_turbo(&n);
  CHECK(n * sizeof(float) == sizeof(Turbo), "la tabla del turbo cubre todos sus campos");
  Turbo d;
  for (int i = 0; i < n; ++i) {
    const float v = *campo(d, tt[i]);
    CHECK(v >= tt[i].min && v <= tt[i].max, "turbo %s de fábrica fuera de rango", tt[i].nombre);
    CHECK(buscar(tt[i].nombre) == nullptr, "turbo %s choca con un nombre de Ajustes", tt[i].nombre);
  }
  CHECK(!fijar(d, "recta_e_in", 8.0f), "histéresis: recta_e_in >= recta_e_out rechazado");
  CHECK(fijar(d, "v_recta", 0.40f) && d.v_recta == 0.40f, "v_recta por consola");
  GuardadoTurbo g{};
  g.t = d;
  sellar(g);
  CHECK(valido(g), "imagen del turbo válida");
  g.t.v_recta = 0.5f;
  CHECK(!valido(g), "un cambio rompe el CRC del turbo");
  g.t = d;
  g.t.recta_e_in = 50.0f;
  sellar(g);
  CHECK(!valido(g), "no se carga un turbo fuera de rango aunque el CRC esté bien");
}

// ------------------------------------------------------------------------------------------------ pista con curvas
// recta 1 m → curva R150 a la izquierda (180°) → recta 0.6 m → curva R200 a la derecha (180°) → recta 0.6 m.
// Igual que pruebas/modelo_pista.py (rectas paralelas a ≥ 20 cm, como pide el reglamento).
struct Prim { bool arco; double ax, ay, ux, uy, L, cx, cy, R, a0, barrido, s0, largo; };
struct PistaS {
  Prim p[5];
  int n = 0;
  double largo = 0.0, entrada[2] = {0, 0};
  void recta(double ax, double ay, double ux, double uy, double L) {
    p[n++] = Prim{false, ax, ay, ux, uy, L, 0, 0, 0, 0, 0, largo, L};
    largo += L;
  }
  void arco(double cx, double cy, double R, double a0, double barrido) {
    p[n++] = Prim{true, 0, 0, 0, 0, 0, cx, cy, R, a0, barrido, largo, R * fabs(barrido)};
    largo += R * fabs(barrido);
  }
  explicit PistaS(double l1 = 1.0, double r1 = 0.15, double l2 = 0.6, double r2 = 0.20, double l3 = 0.6) {
    recta(0, 0, 0, 1, l1);
    entrada[0] = largo;
    arco(-r1, l1, r1, 0.0, M_PI);
    recta(-2 * r1, l1, 0, -1, l2);
    entrada[1] = largo;
    arco(-2 * r1 - r2, l1 - l2, r2, 0.0, -M_PI);
    recta(-2 * r1 - 2 * r2, l1 - l2, 0, 1, l3);
  }
  double dist(double px, double py, double* s) const {
    double mejor = 1e9, sm = 0;
    for (int i = 0; i < n; ++i) {
      const Prim& q = p[i];
      double d, sc;
      if (!q.arco) {
        double t = (px - q.ax) * q.ux + (py - q.ay) * q.uy;
        t = t < 0 ? 0 : (t > q.L ? q.L : t);
        d = hypot(px - (q.ax + t * q.ux), py - (q.ay + t * q.uy));
        sc = q.s0 + t;
      } else {
        const double phi = atan2(py - q.cy, px - q.cx);
        double delta = q.barrido > 0 ? phi - q.a0 : q.a0 - phi;
        delta = fmod(fmod(delta, 2 * M_PI) + 2 * M_PI, 2 * M_PI);
        if (delta <= fabs(q.barrido)) {
          d = fabs(hypot(px - q.cx, py - q.cy) - q.R);
          sc = q.s0 + q.R * delta;
        } else {
          const double a1 = q.a0 + q.barrido;
          const double e0 = hypot(px - (q.cx + q.R * cos(q.a0)), py - (q.cy + q.R * sin(q.a0)));
          const double e1 = hypot(px - (q.cx + q.R * cos(a1)), py - (q.cy + q.R * sin(a1)));
          d = e0 < e1 ? e0 : e1;
          sc = e0 < e1 ? q.s0 : q.s0 + q.largo;
        }
      }
      if (d < mejor) { mejor = d; sm = sc; }
    }
    if (s) *s = sm;
    return mejor;
  }
};

struct ResPista {
  bool termino = false, perdio = false, turbo_en_curva = false;
  int busquedas = 0, cambios = 0;
  double peor = 0, t = 0, cancel_mm[2] = {-1, -1};
};

static ResPista simular_pista(const ParamControl& pc, const Ajustes& aj, const PistaS& pista, double ruido, double picos,
                              double t_max, int borrar_desde_ms = -1, int borrar_hasta_ms = -1) {
  const double r = 0.014, W = 0.080, tau_real = 0.05, dt = 0.0025, V = 6.0;
  const int N = 8;
  posicion::Geometria g = posicion::geometria_recta(N, aj.paso_mm, DIST_SENSOR_EJE_MM);
  posicion::Calibracion cal;
  cal.reiniciar(N);
  for (int i = 0; i < N; ++i) { cal.minimo[i] = 200; cal.maximo[i] = 3700; }
  filtro::Arreglo fil;
  ControladorLinea ctl(pc);
  ctl.reiniciar();
  motor::Accionamiento acc;
  acc.configurar(a_modelo(aj), a_limites(aj));
  acc.reiniciar();
  std::mt19937 rng(7);
  std::normal_distribution<double> nd(0.0, ruido);
  std::uniform_real_distribution<double> u01(0.0, 1.0);
  const posicion::ModoSensor modo = {true, true, 4095};
  Sim s{0.0, 0.0, M_PI / 2};
  ResPista res;
  int k_entrada = 0;
  double dist = 0, d_entrada = 0;
  bool buscando_prev = false, en_curva_con_turbo = false;
  float turbo_prev = 0.0f;
  for (int k = 0; k * dt < t_max; ++k) {
    float refl[16];
    const double hx = cos(s.th), hy = sin(s.th), rx = sin(s.th), ry = -cos(s.th);
    for (int i = 0; i < N; ++i) {
      const double px = s.x + (g.y[i] * hx + g.x[i] * rx) / 1000.0, py = s.y + (g.y[i] * hy + g.x[i] * ry) / 1000.0;
      const double d = pista.dist(px, py, nullptr) * 1000.0;
      double osc = (15.0 - d) / 5.0;
      osc = osc < 0 ? 0 : (osc > 1 ? 1 : osc);
      double on = 300 + osc * 3500 + nd(rng);
      if (u01(rng) < picos) on += 2000;
      refl[i] = posicion::reflectancia(modo, (int)on, (int)(4000 + nd(rng)));
    }
    fil.aplicar(refl, N, aj.alfa);
    float osc[16];
    posicion::normalizar(cal, refl, osc);
    const int ms = (int)(k * dt * 1000.0);
    if (ms >= borrar_desde_ms && ms < borrar_hasta_ms) for (int i = 0; i < N; ++i) osc[i] = 0.0f;
    const posicion::Estimacion e = posicion::estimar_posicion(g, osc, aj.umbral, aj.confianza);
    const SalidaControl sc = ctl.actualizar(e, (float)dt);
    if (sc.linea_perdida) { res.perdio = true; break; }
    if (sc.buscando && !buscando_prev) ++res.busquedas;
    buscando_prev = sc.buscando;
    if ((sc.turbo > 0.0f) != (turbo_prev > 0.0f)) ++res.cambios;
    acc.actualizar(sc.izq, sc.der, (float)V, (float)dt);
    s.wl += dt / (tau_real + dt) * (acc.ciclo(0) * V / aj.m_ke - s.wl);
    s.wr += dt / (tau_real + dt) * (acc.ciclo(1) * V / aj.m_ke - s.wr);
    const double v = r * (s.wl + s.wr) / 2;
    s.x += v * cos(s.th) * dt;
    s.y += v * sin(s.th) * dt;
    s.th += r * (s.wr - s.wl) / W * dt;
    dist += v * dt;
    const double bx = s.x + 0.100 * cos(s.th), by = s.y + 0.100 * sin(s.th);
    double sb;
    const double db = pista.dist(bx, by, &sb) * 1000.0;
    if (k * dt > 0.5) res.peor = fmax(res.peor, db);
    if (k_entrada < 2 && sb >= pista.entrada[k_entrada]) {   // la barra entra a la curva
      en_curva_con_turbo = sc.turbo > 0.0f;
      d_entrada = dist;
      res.cancel_mm[k_entrada] = en_curva_con_turbo ? -2 : 0;   // -2 = pendiente de cancelar
      ++k_entrada;
    }
    if (en_curva_con_turbo && sc.turbo == 0.0f) {
      res.cancel_mm[k_entrada - 1] = (dist - d_entrada) * 1000.0;
      en_curva_con_turbo = false;
    }
    turbo_prev = sc.turbo;
    if (sb >= pista.largo - 0.15) { res.termino = true; res.t = (k + 1) * dt; break; }
  }
  res.turbo_en_curva = en_curva_con_turbo || res.cancel_mm[0] == -2 || res.cancel_mm[1] == -2;
  return res;
}

static void prueba_pista() {
  const PistaS pista;
  for (const char* perfil : {"seguro", "normal", "rapido"}) {
    Ajustes a;
    Turbo t;
    aplicar_perfil(a, t, perfil);
    const ResPista sin = simular_pista(a_control(a), a, pista, 40.0, 0.01, 30.0);
    const ResPista con = simular_pista(a_control(a, t), a, pista, 40.0, 0.01, 30.0);
    printf("  pista %-6s: sin turbo %.2f s / %.1f mm · con turbo %.2f s / %.1f mm · cancelado %.0f y %.0f mm dentro\n",
           perfil, sin.t, sin.peor, con.t, con.peor, con.cancel_mm[0], con.cancel_mm[1]);
    for (const ResPista* r : {&sin, &con}) {
      CHECK(r->termino && !r->perdio && r->busquedas == 0, "%s: completa la pista sin perder la línea", perfil);
      CHECK(r->peor < 30.0, "%s: desvío %.1f mm", perfil, r->peor);
    }
    CHECK(!con.turbo_en_curva, "%s: el turbo no sigue activo dentro de la curva", perfil);
    for (double c : con.cancel_mm) CHECK(c < 100.0, "%s: turbo cancelado %.0f mm dentro (el eje está a 100 mm)", perfil, c);
    if (t.v_recta > a.vbase) {
      CHECK(con.t < sin.t, "%s: el turbo acorta la vuelta (%.2f vs %.2f s)", perfil, con.t, sin.t);
      CHECK(con.peor <= sin.peor + 5.0, "%s: el turbo no aumenta el desvío más de 5 mm", perfil);
      // ruido triple en una recta larga: el turbo no parpadea
      const ResPista rr = simular_pista(a_control(a, t), a, PistaS(4.0), 120.0, 0.03, 6.0);
      CHECK(rr.cambios <= 6, "%s: el turbo parpadea con ruido (%d cambios)", perfil, rr.cambios);
      // línea borrada 120 ms en la recta: busca, la encuentra y termina
      const ResPista rb = simular_pista(a_control(a, t), a, pista, 40.0, 0.01, 30.0, 1500, 1620);
      CHECK(rb.termino && !rb.perdio && rb.busquedas >= 1, "%s: se recupera tras perder la línea", perfil);
    } else {
      CHECK(fabs(con.t - sin.t) < 1e-9 && fabs(con.peor - sin.peor) < 1e-9, "%s: sin turbo = igual que antes", perfil);
    }
  }
}

#ifdef BARRIDO
// Barrido de ganancias por velocidad: imprime el peor desvío y la velocidad mínima en las 3 curvas.
int main() {
  for (float vb : {0.25f, 0.35f, 0.50f, 0.60f})
    for (float kp : {0.008f, 0.010f, 0.012f, 0.014f})
      for (float kd : {0.0002f, 0.0004f, 0.0006f, 0.0008f}) {
        Ajustes a = con_perfil(vb < 0.3f ? "seguro" : (vb < 0.45f ? "normal" : "rapido"));
        a.kp = kp; a.kd = kd; a.vbase = vb;
        double peor = 0, vmin = 9;
        bool p_any = false;
        for (double Rc : {600.0, 300.0, 200.0}) {
          bool p; double vm;
          peor = fmax(peor, simular(Rc, 6.0, 6.0, &p, &vm, a));
          vmin = fmin(vmin, vm); p_any |= p;
        }
        printf("vbase=%.2f kp=%.4f kd=%.4f peor=%5.1f vmin=%.2f %s\n", vb, kp, kd, peor, vmin, p_any ? "PERDIO" : "");
      }
}
#else
int main() {
  prueba_filtro();
  prueba_drv8833();
  prueba_accionamiento();
  prueba_rampa_freno();
  prueba_estados();
  prueba_estados2();
  prueba_indicadores();
  prueba_indicadores2();
  prueba_config();
  prueba_utiles();
  prueba_utiles2();
  prueba_paradas();
  prueba_ajustes();
  prueba_ajustes2();
  prueba_autocal();
  prueba_lazo();
  prueba_turbo_control();
  prueba_turbo_ajustes();
  prueba_pista();
  printf("%d/%d comprobaciones OK\n", total - fallas, total);
  return fallas ? 1 : 0;
}
#endif
