// GENERADO por herramientas/generar_config_firmware.py — NO EDITAR A MANO.
// Fuente: config/robot_maestro.yaml (versión 3, sha256 bf693fc2d7198c42).
// Para cambiar un valor: editar el YAML, regenerar y correr pruebas/ejecutar_todo.sh.
#pragma once

namespace cfg {
constexpr const char* HUELLA_YAML = "bf693fc2d7198c42";
constexpr const char* MOTOR = "Pololu HPCB 12V 10:1";
constexpr const char* BARRA = "arco16q";
constexpr const char* MCU = "stm32g431";
constexpr const char* CONTROL = "C3m";

// Motor (datos del fabricante a V_nom, salida de la reductora; ver el YAML para el origen de cada valor)
constexpr float MOTOR_V_NOM = 12.0f;
constexpr float MOTOR_RPM = 3400.0f;
constexpr float MOTOR_PAR_BLOQUEO = 0.01667131f;   // N·m
constexpr float MOTOR_I_BLOQUEO = 0.75f;
constexpr float MOTOR_I_VACIO = 0.08f;
constexpr float MOTOR_LIMITE_V = 99.0f;      // 99 = sin límite
constexpr float RELACION = 9.96f;
constexpr float CPR_RUEDA = 119.52f;   // cuentas del encoder por vuelta de rueda (4 flancos)

// Geometría y masa
constexpr float L_CUELLO = 0.11f;
constexpr float W_VIA = 0.085f;
constexpr float D_LLANTA = 0.032f;
constexpr float MASA = 0.113f;

// Barra: posición de cada sensor en el marco del cuerpo (x adelante, y izquierda); índice 0 = S1 (izquierda).
constexpr int N_SENSORES = 16;
constexpr float SENSOR_X[N_SENSORES] = {0.1012191f, 0.1033823f, 0.1052482f, 0.1068114f, 0.1080674f, 0.1090126f, 0.1096442f, 0.1099604f, 0.1099604f, 0.1096442f, 0.1090126f, 0.1080674f, 0.1068114f, 0.1052482f, 0.1033823f, 0.1012191f};
constexpr float SENSOR_Y[N_SENSORES] = {0.04306617f, 0.03757782f, 0.03198138f, 0.02629297f, 0.02052892f, 0.01470584f, 0.008840456f, 0.002949646f, -0.002949646f, -0.008840456f, -0.01470584f, -0.02052892f, -0.02629297f, -0.03198138f, -0.03757782f, -0.04306617f};
constexpr float UMBRAL = 0.25f;
constexpr bool RESTA_AMBIENTE = true;
constexpr unsigned T_EMISOR_US = 200;

// Control (vigente: competencia) y modo seguro
constexpr unsigned long PERIODO_MIN_US = 1000;
constexpr float T_PERDIDA = 0.3f;
constexpr float V_MAX = 0.8165f;
constexpr float A_LAT = 7.6438f;
constexpr float A_LON = 2.2819f;
constexpr float K_PP = 0.2917f;
constexpr float KP = 82.4472f;
constexpr float KD = 5.6277f;
constexpr float TAU_D = 0.004f;
constexpr float TAU_K = 0.0728f;
constexpr float PISO = -0.1295f;   // ciclo mínimo de la rueda interior
constexpr int FUENTE_CURVATURA = 1;   // 0 C2, 1 C3m, 2 C3g, 3 C3e
// Modo seguro (C3e, 100 % en las 6 plantas de incertidumbre; se elige con la consola)
constexpr float SEG_V_MAX = 0.6327f;
constexpr float SEG_A_LAT = 4.9703f;
constexpr float SEG_A_LON = 4.3242f;
constexpr float SEG_K_PP = 1.1744f;
constexpr float SEG_KP = 33.6163f;
constexpr float SEG_KD = 0.2319f;
constexpr float SEG_TAU_D = 0.004f;
constexpr float SEG_TAU_K = 0.0214f;
constexpr float SEG_PISO = -0.3905f;
constexpr int SEG_FUENTE = 3;

// Puente H, batería y seguridad
constexpr unsigned F_PWM = 20000;
constexpr float V_BATERIA_BAJA = 6.8f;
constexpr float V_BATERIA_CRITICA = 6.4f;
constexpr float T_BLOQUEO = 0.3f;
constexpr bool INVERTIR_MOTOR_IZQ = false;
constexpr bool INVERTIR_MOTOR_DER = true;
constexpr bool INVERTIR_ENCODER_IZQ = false;
constexpr bool INVERTIR_ENCODER_DER = true;
constexpr unsigned UART_BAUDIOS = 115200;
constexpr float T_CALIBRACION_MAX = 10.0f;
constexpr float RANGO_CAL_MIN = 150.0f;
}  // namespace cfg
