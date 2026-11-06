#include "nucleo_v2.h"

#include <math.h>

namespace v2 {

namespace {

constexpr float G = 9.81f;
constexpr float DOS_PI = 6.2831853f;
constexpr float RANGO_CAL_MIN = 150.0f;         // cuentas blanco-negro mínimas por sensor (como V1)
constexpr uint32_t T_CAL_MAX_MS = 10000;        // C03: barrido manual ≤ 10 s (meta de la Fase 2)
constexpr uint32_t ANTIRREBOTE_MS = 30;

sf::Robot robot_v2() {
  sf::Robot r;
  r.motor = sf::Motor{cfg2::MOTOR_V_NOM, cfg2::MOTOR_RPM, cfg2::MOTOR_PAR_BLOQUEO, cfg2::MOTOR_I_BLOQUEO, cfg2::MOTOR_I_VACIO};
  r.diam = cfg2::D_LLANTA;
  r.W = cfg2::W_VIA;
  r.masa = cfg2::MASA;
  r.L = cfg2::L_BARRA;
  r.n_sens = cfg2::N_SENSORES;
  r.paso = cfg2::PASO_ARCO;
  r.v_max_motor = cfg2::MOTOR_LIMITE_V;
  return r;
}

sf::ParamSF param_control(const Parametros& p, float v_max, float a_lat) {
  sf::ParamSF s;
  s.v_max = v_max;
  s.a_lat = a_lat;
  s.a_lon = p.a_lon;
  s.k_pp = p.k_pp;
  s.kp = p.kp;
  s.kd = p.kd;
  s.tau_d = p.tau_d;
  s.tau_k = p.tau_k;
  s.piso = p.piso;
  s.fuente_k = static_cast<int>(p.fuente_k + 0.5f);
  s.t_perdida = p.t_perdida;
  return s;
}

bool pulso(bool crudo, bool& prev, bool& estable, uint32_t& t_cambio, uint32_t t) {
  if (crudo != prev) { prev = crudo; t_cambio = t; return false; }
  if (crudo != estable && (uint32_t)(t - t_cambio) >= ANTIRREBOTE_MS) { estable = crudo; return estable; }
  return false;
}

}  // namespace

NucleoV2::NucleoV2()
    : ctrl_(param_control(Parametros{}, 1.0f, 5.0f), robot_v2()),
      mot_(ModeloMotor::desde_ficha(cfg2::MOTOR_V_NOM, cfg2::MOTOR_RPM, cfg2::MOTOR_PAR_BLOQUEO, cfg2::MOTOR_I_BLOQUEO,
                                    cfg2::MOTOR_I_VACIO)),
      term_i_(cfg2::MOTOR_R, cfg2::MOTOR_RTH, cfg2::MOTOR_CTH),
      term_d_(cfg2::MOTOR_R, cfg2::MOTOR_RTH, cfg2::MOTOR_CTH) {
  cal_.reiniciar(N);
  defecto();
  mapa_.reiniciar(ParamMapa{});
}

void NucleoV2::defecto() {
  p_ = Parametros{};
  aplicar_parametros();
}

void NucleoV2::aplicar_parametros() {
  ParamSuccion s;
  s.mando_crucero = p_.mando_esc;
  s.dp_min = p_.dp_min;
  s.area = cfg2::AREA_CAMARA;
  s.fraccion_ruedas = cfg2::FRACCION_RUEDAS;
  suc_.configurar(s);
}

void NucleoV2::cargar(const Guardado& g) {
  p_ = g.p;
  cal_.reiniciar(N);
  for (int i = 0; i < N; ++i) { cal_.minimo[i] = g.cal_min[i]; cal_.maximo[i] = g.cal_max[i]; }
  cal_ok_ = cal_.lista(RANGO_CAL_MIN);
  suc_.fijar_cero(g.cero_presion);
  aplicar_parametros();
}

void NucleoV2::guardar(Guardado& g) const {
  g.p = p_;
  for (int i = 0; i < N; ++i) { g.cal_min[i] = cal_.minimo[i]; g.cal_max[i] = cal_.maximo[i]; }
  g.cero_presion = suc_.cero();
  g.sesgo_giro = 0.0f;
  g.reservado = 0;
  sellar(g);
}

void NucleoV2::leer_linea(const Entradas& in) {
  const posicion::ModoSensor modo{true, true, 4095};   // resta de ambiente; más luz = menos tensión (QRE1113 + 10 kΩ)
  int crudos[N];
  for (int i = 0; i < N; ++i) {
    refl_[i] = posicion::reflectancia(modo, in.encendido[i], in.ambiente[i]);
    crudos[i] = in.encendido[i];
  }
  if (maq_.estado() == Estado::CALIBRACION) cal_.muestrear(refl_);
  posicion::normalizar(cal_, refl_, osc_);
  lect_ = sf::estimar_coord(osc_, cfg2::SENSOR_Y, N);
  // lecturas imposibles (barra desconectada, sin alimentación o robot levantado) sostenidas 200 ms
  const bool mal = posicion::lecturas_imposibles(crudos, N, 4095);
  if (mal && !sens_mal_) t_sens_mal_ = in.t_ms;
  sens_mal_ = mal;
}

void NucleoV2::motores(const Entradas& in, Salidas& out) {
  const float r = cfg2::D_LLANTA * 0.5f;
  float d[2] = {sal_.izq, sal_.der};
  const float w[2] = {w_i_, w_d_};
  const float i_med[2] = {in.i_izq, in.i_der};
  LazoCorriente* lazo[2] = {&lazo_i_, &lazo_d_};
  EstimadorTermico* term[2] = {&term_i_, &term_d_};
  for (int k = 0; k < 2; ++k) {
    const float i_t = term[k]->limite(p_.i_lim, 0.5f, p_.t_reduce, p_.t_max);   // derrateo térmico
    const float i_ef = lazo[k]->actualizar(i_med[k], i_t, in.dt);                // corrección con IPROPI
    d[k] = limitar_ciclo(mot_, d[k], w[k], in.v_bat, i_ef, cfg2::MOTOR_LIMITE_V);
    const float i_mod = fabsf(mot_.corriente(d[k], in.v_bat, w[k]));
    term[k]->paso(i_mod > i_med[k] ? i_mod : i_med[k], in.dt);
  }
  (void)r;
  out.ciclo_izq = p_.invertir_izq > 0.5f ? -d[0] : d[0];
  out.ciclo_der = p_.invertir_der > 0.5f ? -d[1] : d[1];
  // rueda trabada: ciclo alto sin giro durante 0.3 s (C10)
  const bool ti = fabsf(d[0]) > 0.5f && fabsf(w_i_) < 2.0f, td = fabsf(d[1]) > 0.5f && fabsf(w_d_) < 2.0f;
  if (ti && !trab_i_) t_trabada_i_ = in.t_ms;
  if (td && !trab_d_) t_trabada_d_ = in.t_ms;
  trab_i_ = ti; trab_d_ = td;
}

void NucleoV2::ciclo(const Entradas& in, Salidas& out) {
  const uint32_t t = in.t_ms;
  Eventos ev;
  ev.start = pulso(in.btn_start, start_prev_, start_estable_, t_start_, t);
  ev.cal = pulso(in.btn_cal, cal_prev_, cal_estable_, t_cal_, t);

  // ---- batería (filtrada; crítica si se sostiene 0.5 s bajo el umbral)
  if (!bat_iniciada_) { v_bat_f_ = in.v_bat; bat_iniciada_ = true; }
  else v_bat_f_ += 0.1f * (in.v_bat - v_bat_f_);
  const bool baja = v_bat_f_ < p_.v_bat_critica;
  if (baja && !bat_baja_) t_bat_baja_ = t;
  bat_baja_ = baja;
  ev.bateria_permite = v_bat_f_ >= p_.v_bat_baja;
  ev.bateria_critica = baja && (t - t_bat_baja_) >= 500u;

  // ---- línea, ruedas
  leer_linea(in);
  const float k_enc = DOS_PI / cfg2::CUENTAS_VUELTA / in.dt;
  w_i_ = in.d_enc_izq * p_.enc_izq * k_enc;
  w_d_ = in.d_enc_der * p_.enc_der * k_enc;
  const float r = cfg2::D_LLANTA * 0.5f;
  const float v = 0.5f * (w_i_ + w_d_) * r;

  // ---- succión
  if (maq_.ventilador_encendido()) suc_.encender(t);
  else suc_.apagar();
  if (in.baro_nueva) {
    suc_.muestra(in.p_amb, in.p_cam, in.baro_ok, t);
    // cero de presión con el ventilador apagado y el robot quieto (LISTO, ESPERA, CALIBRACION)
    const Estado e = maq_.estado();
    if (in.baro_ok && (e == Estado::LISTO || e == Estado::ESPERA || e == Estado::CALIBRACION))
      suc_.fijar_cero(suc_.cero() + 0.02f * ((in.p_amb - in.p_cam) - suc_.cero()));
  }
  suc_.actualizar(t);
  ev.succion_lista = suc_.listo_para_correr();
  out.esc = suc_.mando();

  // ---- adherencia disponible: la succión confirmada suma carga normal (F_s sobre las ruedas motrices)
  const float fs = suc_.fuerza();
  const float a_lat = p_.a_lat_sin * (cfg2::MASA * G + fs) / (cfg2::MASA * G);
  const float a_fr = p_.a_fr_mapa * (cfg2::MASA * G + fs) / (cfg2::MASA * G);
  v_tope_ = suc_.con_succion() ? p_.v_con : p_.v_sin;

  // ---- mapa (solo corriendo, con el giroscopio funcionando)
  const bool corriendo = maq_.motores_habilitados();
  if (corriendo && p_.usar_mapa > 0.5f && in.imu_ok) {
    mapa_.avanzar(v * in.dt, in.gz * in.dt);
    if (mapa_.modo() == Mapa::Modo::INVALIDO) mapa_.reiniciar(ParamMapa{});   // la pista cambió: aprende otra vez
    if (mapa_.tomar_cierre()) mapa_.calcular_perfil(a_lat, p_.a_acc_mapa, a_fr, p_.v_max_mapa);
    if (mapa_.perfil_listo()) {
      const float vp = mapa_.v_perfil(fabsf(v) * p_.adelanto_mapa);
      v_tope_ = vp < p_.v_max_mapa ? vp : p_.v_max_mapa;
    }
  }

  // ---- derrape: la guiñada del giroscopio no coincide con la de las ruedas (pérdida de adherencia)
  const float guinada_enc = (w_d_ - w_i_) * r / cfg2::W_VIA;
  const bool der = corriendo && in.imu_ok && fabsf(v) > 0.3f && fabsf(in.gz - guinada_enc) > 1.5f;
  if (der && !derrape_) t_derrape_ = t;
  derrape_ = der;
  const bool derrapando = der && (t - t_derrape_) >= 30u;
  if (derrapando) { const float vr = 0.7f * fabsf(v); if (vr < v_tope_) v_tope_ = vr; }

  // ---- control
  if (corriendo) {
    if (maq_.recien_arrancado()) { ctrl_.reiniciar(); lazo_i_.reiniciar(); lazo_d_.reiniciar(); }
    sf::ParamSF ps = param_control(p_, v_tope_, a_lat);
    if (!in.imu_ok && ps.fuente_k == 2) ps.fuente_k = 3;     // sin giroscopio: curvatura de los encoders
    ctrl_.fijar(ps);
    sal_ = ctrl_.actualizar(lect_, in.dt, v_bat_f_, in.gz, w_i_, w_d_);
  } else {
    sal_ = sf::Salida{0, 0, 0, false, false};
  }
  ev.buscando = corriendo && (!lect_.visible || derrapando);
  ev.linea_perdida = corriendo && sal_.linea_perdida;
  motores(in, out);

  // ---- fallas
  if (in.nfault && !nf_) t_nfault_ = t;
  nf_ = in.nfault;
  ev.falla_motor = (nf_ && (t - t_nfault_) >= 20u) || (trab_i_ && (t - t_trabada_i_) >= 300u) ||
                   (trab_d_ && (t - t_trabada_d_) >= 300u);
  ev.falla_sensores = corriendo && sens_mal_ && (t - t_sens_mal_) >= 200u;
  ev.sobrecalentado = term_i_.sobrecalentado(p_.t_max) || term_d_.sobrecalentado(p_.t_max);

  // ---- calibración (C03: barrido manual; los motores no se mueven)
  ev.autoprueba_hecha = in.autoprueba_hecha;
  ev.autoprueba = in.autoprueba;
  ev.cal_guardada_ok = cal_ok_;
  ev.cal_suficiente = cal_.lista(RANGO_CAL_MIN);
  ev.cal_tiempo_agotado = maq_.estado() == Estado::CALIBRACION && (t - t_cal_inicio_) >= T_CAL_MAX_MS;

  if (maq_.actualizar(ev, t)) {
    const Estado e = maq_.estado();
    if (e == Estado::CALIBRACION) { cal_.reiniciar(N); t_cal_inicio_ = t; }
    if (previo_ == Estado::CALIBRACION) {
      cal_ok_ = (e == Estado::LISTO);
      melodia_ = cal_ok_ ? Melodia::CAL_BIEN : Melodia::CAL_MAL;
      t_melodia_ = t;
    }
    if (e == Estado::ARRANQUE) mapa_.reiniciar(ParamMapa{});          // el mapa se aprende en cada ronda
    previo_ = e;
  }

  // ---- salidas
  const Estado e = maq_.estado();
  out.despierto = maq_.motores_habilitados() || maq_.frenado_activo();
  out.frenar = maq_.frenado_activo();
  if (!maq_.motores_habilitados()) { out.ciclo_izq = out.ciclo_der = 0.0f; }
  AvisoSucc a = AvisoSucc::APAGADO;
  if (maq_.ventilador_encendido()) a = suc_.con_succion() ? AvisoSucc::OK : AvisoSucc::SIN_SUCCION;
  out.ind = indicar(e, maq_.error(), t - maq_.desde_ms(), t, a, melodia_, t - t_melodia_);
}

}  // namespace v2
