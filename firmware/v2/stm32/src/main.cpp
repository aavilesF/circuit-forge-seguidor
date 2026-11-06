// Speed Follower V2 — firmware del STM32G474CEU6 (módulo WeAct en la PCB principal V2).
//
// Ciclo de 1 kHz (TIM6): barra de 16 sensores con resta de luz ambiente (2 multiplexores leídos a la vez por ADC1 y
// ADC2), encoders, giroscopio, corrientes IPROPI, batería y, cada 5 ms, los dos barómetros -> v2::NucleoV2::ciclo()
// (máquina de estados, control sf::ControlSF de V1, mapa de la vuelta, límite de corriente y estimador térmico,
// supervisor de la succión, LED y zumbador) -> PWM de los DRV8874, DShot300 al ESC, LED y zumbador.
// Fuera del ciclo: consola por USB (CDC). Sin comunicación inalámbrica (prohibida por el reglamento).
//
// Seguridad (igual que V1 y FASE2 §7): nada se mueve sin START (R08); calibración manual sin motores (C03); límite de
// 1.5 A por motor y estimador térmico (FASE35 §3); nSLEEP en bajo fuera de la carrera.
#include <math.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#include "../../config_v2.h"
#include "../../logica/consola.h"
#include "../../logica/nucleo_v2.h"
#include "hw_v2.h"
#include "usb_cdc.h"

namespace {

// ------------------------------------------------------------------ sensores I2C (registros de ism330dhcx-pid y lps22df-pid de ST)
constexpr uint8_t IMU = 0x6A;               // ISM330DHCX, SA0 a GND (R29)
constexpr uint8_t BARO_CAMARA = 0x5D;       // LPS22DF U3 (cara inferior, en la chimenea), SA0 a 3V3
constexpr uint8_t BARO_AMBIENTE = 0x5C;     // LPS22DF U4, SA0 a GND
constexpr float GIRO_RAD_LSB = 0.070f * 3.14159265f / 180.0f;   // ±2000 dps: 70 mdps/LSB [V]

bool imu_iniciar() {
  uint8_t id = 0;
  if (!hw2::i2c_leer(IMU, 0x0F, &id, 1) || id != 0x6B) return false;          // WHO_AM_I = 0x6B
  return hw2::i2c_escribir(IMU, 0x12, 0x44) &&                                // CTRL3_C: BDU, IF_INC
         hw2::i2c_escribir(IMU, 0x10, 0x8C) &&                                // CTRL1_XL: 1.66 kHz, ±8 g
         hw2::i2c_escribir(IMU, 0x11, 0x8C);                                  // CTRL2_G: 1.66 kHz, ±2000 dps
}

bool imu_gz(float* gz) {
  uint8_t b[2];
  if (!hw2::i2c_leer(IMU, 0x26, b, 2)) return false;                         // OUTZ_L_G, OUTZ_H_G
  *gz = int16_t(b[0] | (b[1] << 8)) * GIRO_RAD_LSB;
  return true;
}

bool baro_iniciar(uint8_t dir) {
  uint8_t id = 0;
  if (!hw2::i2c_leer(dir, 0x0F, &id, 1) || id != 0xB4) return false;          // WHO_AM_I = 0xB4
  return hw2::i2c_escribir(dir, 0x11, 0x08) &&                                // CTRL_REG2: BDU
         hw2::i2c_escribir(dir, 0x10, (0x08 << 3) | 0x00);                    // CTRL_REG1: 200 Hz, promedio de 4
}

bool baro_pa(uint8_t dir, float* pa) {
  uint8_t b[3];
  if (!hw2::i2c_leer(dir, 0x28, b, 3)) return false;                          // PRESS_OUT_XL..H
  const uint32_t raw = uint32_t(b[0]) | (uint32_t(b[1]) << 8) | (uint32_t(b[2]) << 16);
  *pa = raw * (100.0f / 4096.0f);                                              // 4096 LSB/hPa [V]
  return true;
}

// ------------------------------------------------------------------ estado
v2::NucleoV2 nucleo;
v2::Entradas in;
v2::Salidas out;
v2::LineaConsola linea;
bool imu_ok = false, baro_ok = false, telemetria = false;
float sesgo_giro = 0.0f;
int32_t enc_i0 = 0, enc_d0 = 0;
uint32_t prueba_hasta = 0, esc_hasta = 0;
float prueba_i = 0, prueba_d = 0, esc_prueba = 0;
float p_amb = 0, p_cam = 0;
uint32_t t_inicio = 0;
uint32_t ciclo_max_us = 0;

void wr(const char* s) { usb::escribir(s); }
void wr_int(int32_t v) {
  char b[12]; int i = 11; b[i] = 0;
  const bool neg = v < 0;
  uint32_t u = neg ? uint32_t(-v) : uint32_t(v);
  do { b[--i] = char('0' + u % 10); u /= 10; } while (u && i > 1);
  if (neg) b[--i] = '-';
  wr(b + i);
}
void wr_f(float v, int dec = 3) {
  if (v != v) { wr("nan"); return; }
  if (v < 0) { wr("-"); v = -v; }
  if (v > 2e9f) { wr("inf"); return; }
  float esc = 1.0f;
  for (int k = 0; k < dec; ++k) esc *= 10.0f;
  const uint32_t t = uint32_t(v * esc + 0.5f);
  wr_int(int32_t(t / uint32_t(esc)));
  if (dec == 0) return;
  wr(".");
  uint32_t fr = t % uint32_t(esc);
  char b[8];
  for (int k = dec - 1; k >= 0; --k) { b[k] = char('0' + fr % 10); fr /= 10; }
  b[dec] = 0;
  wr(b);
}

void ayuda() {
  wr("Speed Follower V2 — consola USB\r\n"
     "  ?  ayuda | e estado | t telemetria | r crudos | p parametros | m mapa\r\n"
     "  set <p> <v> | w guardar | defecto | cero (presion, ventilador apagado)\r\n"
     "  prueba <i> <d> (2 s, detenido, ruedas en el aire) | esc <0..1> (2 s, detenido)\r\n");
}

void estado() {
  wr("estado "); wr(v2::nombre(nucleo.maquina().estado()));
  wr(" | error "); wr_int(int(nucleo.maquina().error()));
  wr(" | bateria "); wr_f(in.v_bat, 2);
  wr(" V | reloj "); wr(hw2::reloj_con_cristal() ? "HSE" : "HSI16");
  wr(" | IMU "); wr(imu_ok ? "ok" : "FALLA");
  wr(" | barometros "); wr(baro_ok ? "ok" : "FALLA");
  wr("\r\n  calibracion "); wr(nucleo.cal_valida() ? "valida" : "no");
  wr(" | dP "); wr_f(nucleo.succion().dp(), 0); wr(" Pa (cero "); wr_f(nucleo.succion().cero(), 0);
  wr(") | F "); wr_f(nucleo.succion().fuerza(), 2);
  wr(" N | T motor "); wr_f(nucleo.temp_izq(), 1); wr("/"); wr_f(nucleo.temp_der(), 1);
  wr(" K | ciclo max "); wr_int(int32_t(ciclo_max_us)); wr(" us\r\n");
}

void parametros() {
  int n;
  const v2::EntradaParam* t = v2::tabla_parametros(&n);
  for (int i = 0; i < n; ++i) {
    wr("  "); wr(t[i].nombre); wr(" = "); wr_f(*v2::campo(nucleo.prm(), t[i]), 4);
    wr("  ["); wr_f(t[i].min, 3); wr(", "); wr_f(t[i].max, 3); wr("]\r\n");
  }
}

void mapa() {
  const v2::Mapa& m = nucleo.mapa();
  const char* modo = m.modo() == v2::Mapa::Modo::CERRADO ? "cerrado" : (m.modo() == v2::Mapa::Modo::APRENDIENDO ? "aprendiendo" : "invalido");
  wr("mapa "); wr(modo); wr(" | largo "); wr_f(m.largo(), 3); wr(" m | posicion "); wr_f(m.posicion(), 3);
  wr(" m | vueltas "); wr_int(m.vueltas()); wr(" | error "); wr_f(m.error_ultimo(), 2);
  wr(" 1/m | perfil "); wr(m.perfil_listo() ? "si" : "no"); wr("\r\n");
}

bool detenido() {
  const v2::Estado e = nucleo.maquina().estado();
  return e == v2::Estado::ESPERA || e == v2::Estado::LISTO || e == v2::Estado::PARADA || e == v2::Estado::ERROR;
}

void guardar() {
  static_assert(sizeof(v2::Guardado) % 8 == 0, "la imagen de la flash debe ser múltiplo de 8 bytes");
  static_assert(sizeof(v2::Guardado) <= 2048, "la imagen no cabe en 2 KB");
  v2::Guardado g{};
  nucleo.guardar(g);
  g.sesgo_giro = sesgo_giro;
  v2::sellar(g);
  wr(hw2::flash_guardar(&g, sizeof(g)) ? "guardado en flash\r\n" : "ERROR al guardar\r\n");
}

void consola() {
  int c;
  while ((c = usb::leer()) >= 0) {
    if (!linea.alimentar(char(c))) continue;
    const v2::Comando k = v2::interpretar(linea.linea());
    switch (k.orden) {
      case v2::Orden::AYUDA: ayuda(); break;
      case v2::Orden::ESTADO: estado(); break;
      case v2::Orden::TELEMETRIA: telemetria = !telemetria; break;
      case v2::Orden::CRUDOS:
        for (int i = 0; i < v2::N; ++i) { wr_int(in.ambiente[i]); wr("/"); wr_int(in.encendido[i]); wr(i + 1 < v2::N ? " " : "\r\n"); }
        break;
      case v2::Orden::PARAMETROS: parametros(); break;
      case v2::Orden::FIJAR:
        if (v2::fijar(nucleo.prm(), k.nombre, k.a)) { nucleo.aplicar_parametros(); wr("ok\r\n"); }
        else wr("parametro desconocido o fuera de rango\r\n");
        break;
      case v2::Orden::GUARDAR: if (detenido()) guardar(); else wr("solo detenido\r\n"); break;
      case v2::Orden::DEFECTO: nucleo.defecto(); wr("valores de fabrica (sin guardar)\r\n"); break;
      case v2::Orden::MAPA: mapa(); break;
      case v2::Orden::PRUEBA:
        if (detenido() && fabsf(k.a) <= 0.5f && fabsf(k.b) <= 0.5f) { prueba_i = k.a; prueba_d = k.b; prueba_hasta = hw2::ms() + 2000; }
        else wr("solo detenido, |ciclo| <= 0.5\r\n");
        break;
      case v2::Orden::ESC:
        if (detenido() && k.a >= 0.0f && k.a <= 1.0f) { esc_prueba = k.a; esc_hasta = hw2::ms() + 2000; }
        else wr("solo detenido, 0..1\r\n");
        break;
      case v2::Orden::CERO:
        if (detenido() && baro_ok) { nucleo.fijar_cero_presion(p_amb - p_cam); wr("cero de presion fijado\r\n"); }
        else wr("solo detenido y con barometros\r\n");
        break;
      case v2::Orden::FALTA_VALOR: wr("faltan valores\r\n"); break;
      case v2::Orden::DESCONOCIDA: wr("? para ayuda\r\n"); break;
      default: break;
    }
  }
}

void telemetria_linea() {
  // t_ms, estado, e_mm, visible, v_tope, v_izq, v_der, ciclo_i, ciclo_d, I_i, I_d, T_i, T_d, dP, mapa_s, vueltas
  wr_int(int32_t(in.t_ms)); wr(","); wr_int(int(nucleo.maquina().estado())); wr(",");
  wr_f(nucleo.lectura().e * 1000.0f, 1); wr(","); wr_int(nucleo.lectura().visible); wr(",");
  wr_f(nucleo.v_tope(), 2); wr(","); wr_f(nucleo.v_rueda_izq(), 2); wr(","); wr_f(nucleo.v_rueda_der(), 2); wr(",");
  wr_f(out.ciclo_izq, 3); wr(","); wr_f(out.ciclo_der, 3); wr(",");
  wr_f(in.i_izq, 2); wr(","); wr_f(in.i_der, 2); wr(",");
  wr_f(nucleo.temp_izq(), 1); wr(","); wr_f(nucleo.temp_der(), 1); wr(",");
  wr_f(nucleo.succion().dp(), 0); wr(","); wr_f(nucleo.mapa().posicion(), 3); wr(","); wr_int(nucleo.mapa().vueltas());
  wr("\r\n");
}

}  // namespace

int main() {
  hw2::iniciar();
  usb::iniciar();
  const v2::Guardado* g = static_cast<const v2::Guardado*>(hw2::flash_datos());
  if (v2::valido(*g)) { nucleo.cargar(*g); sesgo_giro = g->sesgo_giro; }
  imu_ok = imu_iniciar();
  baro_ok = baro_iniciar(BARO_CAMARA) && baro_iniciar(BARO_AMBIENTE);
  t_inicio = hw2::ms();
  enc_i0 = hw2::encoder_izq();
  enc_d0 = hw2::encoder_der();
  float suma_giro = 0.0f;
  int n_giro = 0;

  for (;;) {
    while (!hw2::tick_control()) consola();
    const uint32_t c0 = hw2::ciclos();
    const uint32_t t = hw2::ms();
    in.t_ms = t;
    in.dt = 0.001f;
    hw2::leer_barra(in.ambiente, in.encendido, uint32_t(nucleo.prm().t_emisor_us));
    const int32_t ei = hw2::encoder_izq(), ed = hw2::encoder_der();
    in.d_enc_izq = ei - enc_i0; in.d_enc_der = ed - enc_d0;
    enc_i0 = ei; enc_d0 = ed;
    float gz = 0.0f;
    const bool g_ok = imu_ok && imu_gz(&gz);
    in.imu_ok = g_ok;
    // sesgo del giroscopio: promedio en la autoprueba (robot quieto, 0.5 s) y ajuste lento en LISTO
    const v2::Estado e = nucleo.maquina().estado();
    if (g_ok && e == v2::Estado::INICIO) { suma_giro += gz; ++n_giro; }
    if (g_ok && e == v2::Estado::LISTO && fabsf(gz - sesgo_giro) < 0.05f) sesgo_giro += 0.001f * (gz - sesgo_giro);
    in.gz = gz - sesgo_giro;
    hw2::corrientes(&in.i_izq, &in.i_der);
    in.v_bat = hw2::v_bateria();
    in.btn_start = hw2::boton_start();
    in.btn_cal = hw2::boton_cal();
    in.nfault = hw2::nfault();
    in.baro_nueva = false;
    if (baro_ok && t % 5 == 0) {
      const bool ok = baro_pa(BARO_AMBIENTE, &p_amb) && baro_pa(BARO_CAMARA, &p_cam);
      in.baro_nueva = true; in.baro_ok = ok; in.p_amb = p_amb; in.p_cam = p_cam;
    }
    // autoprueba (INICIO): 0.5 s quieto para el sesgo del giroscopio y revisión de periféricos
    in.autoprueba_hecha = (t - t_inicio) >= 500u;
    if (in.autoprueba_hecha && n_giro > 0 && e == v2::Estado::INICIO) { sesgo_giro = suma_giro / n_giro; suma_giro = 0; n_giro = 0; }
    in.autoprueba = !imu_ok ? v2::Error::IMU : (!baro_ok ? v2::Error::BAROMETROS : v2::Error::NINGUNO);

    nucleo.ciclo(in, out);

    // pruebas de la consola (solo detenido): motores y ventilador 2 s
    float di = out.ciclo_izq, dd = out.ciclo_der, esc = out.esc;
    bool despierto = out.despierto, frenar = out.frenar;
    if (detenido() && (int32_t)(prueba_hasta - t) > 0) { di = prueba_i; dd = prueba_d; despierto = true; frenar = false; }
    if (detenido() && (int32_t)(esc_hasta - t) > 0) esc = esc_prueba;
    hw2::motores(di, dd, despierto, frenar);
    hw2::esc_dshot(esc > 0.0f ? uint16_t(48.0f + esc * 1999.0f) : 0);       // 0 = parado (DShot: 48..2047 = acelerador)
    hw2::leds(out.ind.verde, out.ind.amarillo, out.ind.rojo, out.ind.succion);
    hw2::zumbador(out.ind.tono_hz);
    if (telemetria && usb::conectado() && t % 20 == 0) telemetria_linea();
    const uint32_t us = (hw2::ciclos() - c0) / (hw2::F_CPU / 1000000u);
    if (us > ciclo_max_us) ciclo_max_us = us;
  }
}
