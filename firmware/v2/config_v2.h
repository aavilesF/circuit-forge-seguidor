// GENERADO por firmware/v2/herramientas/generar_config.py — no editar a mano.
// Tipos: [V] verificado (ficha) · [C] calculado · [E] estimado · [S] supuesto · [P] pendiente de medición.
#pragma once
#include <stdint.h>

namespace cfg2 {

// ---- barra de sensores (barra_sensores.py, robot_v2.yaml)
constexpr int   N_SENSORES = 16;
constexpr float L_BARRA = 0.1250f;          // m, radio del arco medido desde el eje de las ruedas [S]
constexpr float PASO_ARCO = 0.0055f;       // m [S]
// coordenada lateral (m, + a la IZQUIERDA) y longitudinal (m, adelante del eje) de S1..S16
constexpr float SENSOR_Y[N_SENSORES] = {0.04051f, 0.03526f, 0.02996f, 0.02459f, 0.01917f, 0.01372f, 0.00824f, 0.00275f, -0.00275f, -0.00824f, -0.01372f, -0.01917f, -0.02459f, -0.02996f, -0.03526f, -0.04051f};
constexpr float SENSOR_X[N_SENSORES] = {0.11826f, 0.11992f, 0.12136f, 0.12256f, 0.12352f, 0.12424f, 0.12473f, 0.12497f, 0.12497f, 0.12473f, 0.12424f, 0.12352f, 0.12256f, 0.12136f, 0.11992f, 0.11826f};
// multiplexor (0 = U17 -> SENS_A/PA0, 1 = U18 -> SENS_B/PA1) y canal (S2..S0) de cada sensor
constexpr uint8_t SENSOR_MUX[N_SENSORES] = {0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1};
constexpr uint8_t SENSOR_CANAL[N_SENSORES] = {0, 1, 2, 3, 4, 5, 6, 7, 7, 6, 5, 4, 3, 2, 1, 0};

// ---- ruedas, masa
constexpr float D_LLANTA = 0.0320f;        // m [V Pololu #1087]
constexpr float W_VIA = 0.0850f;           // m [S]
constexpr float MASA = 0.1552f;            // kg, CAD (piezas impresas sólidas) [C/E]
constexpr float MU_REF = 0.80f;           // adherencia llanta-pista [S, P01: medir]
constexpr float FACTOR_PLAN = 0.90f;      // fracción de la adherencia que usa el plan [S]

// ---- motor Pololu #5183 (15.25:1 HPCB 6 V, encoder 12 CPR) [V pololu.com/product/5183]
constexpr float MOTOR_V_NOM = 6.0f;
constexpr float MOTOR_RPM = 2100.0f;           // sin carga a V_NOM
constexpr float MOTOR_PAR_BLOQUEO = 0.024517f;   // N·m (0.25 kg·cm, extrapolado por Pololu)
constexpr float MOTOR_I_BLOQUEO = 1.50f;      // A
constexpr float MOTOR_I_VACIO = 0.15f;        // A
constexpr float MOTOR_REDUCCION = 15.25f;     // [V]
constexpr float CUENTAS_VUELTA = 12.0f * MOTOR_REDUCCION;   // 4 flancos de A y B: 12 por vuelta del motor [V] = 183 [C]
constexpr float MOTOR_LIMITE_V = 6.0f;       // V efectivos máximos en el motor (6 V nominales) [S]
constexpr float MOTOR_R = 4.00f;             // Ω [C]
constexpr float MOTOR_KT = 0.01635f;         // N·m/A en la salida [C]
constexpr float MOTOR_RTH = 40.0f;           // K/W [E]
constexpr float MOTOR_CTH = 3.0f;            // J/K [E]
constexpr float MOTOR_DT_MAX = 50.0f;        // K, elevación admitida [S]

// ---- puente H DRV8874 (principal.py) [V SLVSF66A]
constexpr float R_IPROPI = 1500.0f;         // Ω (R19/R21)
constexpr float A_IPROPI = 0.000450f;          // A/A
constexpr float V_IPROPI_POR_A = R_IPROPI * A_IPROPI; // V/A = 0.6750
constexpr float I_TRIP = 1.563f;            // A, VREF 1.055 V (R25 10000 / R26 4700) [C]
constexpr float I_LIMITE_FIRMWARE = 1.5f;     // A por motor, frenado y arranque (FASE35_CORRECCIONES §3) [C]
constexpr float F_PWM = 20000.0f;             // Hz [S]

// ---- batería (divisor R3/R4)
constexpr float DIV_BATERIA = 4.03030f;   // (100000 + 33000) / 33000 [C]

// ---- succión (robot_v2.yaml: cámara y Fase 3.5)
constexpr float AREA_CAMARA = 0.004900f;    // m² (70 × 70 mm) [V]
constexpr float FRACCION_RUEDAS = 0.96f;     // fracción de la succión sobre las ruedas motrices [C, FASE3_ENTREGA1 §6]
constexpr float DP0_CONSERVADOR = 500.0f;   // Pa [S]

}  // namespace cfg2
