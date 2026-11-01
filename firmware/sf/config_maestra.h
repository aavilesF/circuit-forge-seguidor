// GENERADO por herramientas/generar_config_firmware.py — NO EDITAR A MANO.
// Fuente: config/robot_maestro.yaml (versión 2, sha256 f41089aaade14afb).
// Para cambiar un valor: editar el YAML, regenerar y correr pruebas/ejecutar_todo.sh.
#pragma once

namespace cfg {
constexpr const char* HUELLA_YAML = "f41089aaade14afb";
constexpr const char* MOTOR = "Pololu HPCB 12V 10:1";
constexpr const char* BARRA = "arco16";
constexpr const char* MCU = "stm32g431";
constexpr const char* CONTROL = "C3m";

// Motor (datos del fabricante a V_nom; ver YAML para el origen de cada valor)
constexpr float MOTOR_V_NOM = 12.0f;
constexpr float MOTOR_RPM = 3400.0f;
constexpr float MOTOR_PAR_BLOQUEO = 0.01667131f;   // N·m
constexpr float MOTOR_I_BLOQUEO = 0.75f;
constexpr float MOTOR_I_VACIO = 0.08f;
constexpr float MOTOR_LIMITE_V = 99.0f;      // 99 = sin límite

// Geometría y masa
constexpr float L_CUELLO = 0.1f;
constexpr float W_VIA = 0.085f;
constexpr float D_LLANTA = 0.034f;
constexpr float MASA = 0.1214f;

// Barra de sensores: posición de cada sensor en el marco del cuerpo (x adelante, y izquierda),
// índice 0 = extremo derecho. La estimación usa y (sf::estimar_coord).
constexpr int N_SENSORES = 16;
constexpr float SENSOR_X[N_SENSORES] = {0.08887204f, 0.09160212f, 0.09396296f, 0.09594505f, 0.0975404f, 0.09874257f, 0.09954671f, 0.0999496f, 0.0999496f, 0.09954671f, 0.09874257f, 0.0975404f, 0.09594505f, 0.09396296f, 0.09160212f, 0.08887204f};
constexpr float SENSOR_Y[N_SENSORES] = {0.04584497f, 0.04011299f, 0.03421932f, 0.02818771f, 0.02204248f, 0.0158084f, 0.009510604f, 0.003174467f, -0.003174467f, -0.009510604f, -0.0158084f, -0.02204248f, -0.02818771f, -0.03421932f, -0.04011299f, -0.04584497f};
constexpr float UMBRAL = 0.25f;

// Control
constexpr unsigned long PERIODO_MIN_US = 1000;
constexpr float T_PERDIDA = 0.3f;
constexpr float V_MAX = 1.8f;
constexpr float A_LAT = 4.5f;
constexpr float A_LON = 4.0f;
constexpr float K_PP = 1.0f;
constexpr float KP = 30.0f;
constexpr float KD = 1.0f;
constexpr float TAU_D = 0.004f;
constexpr float TAU_K = 0.03f;
constexpr float PISO = 0.0f;   // ciclo mínimo de la rueda interior
constexpr int FUENTE_CURVATURA = 1;   // 0 error (C2), 1 modelo del motor (C3m), 2 giroscopio (C3g)

// Batería
constexpr float V_BATERIA_BAJA = 6.8f;
}  // namespace cfg
