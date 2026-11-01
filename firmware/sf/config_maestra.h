// GENERADO por herramientas/generar_config_firmware.py — NO EDITAR A MANO.
// Fuente: config/robot_maestro.yaml (versión 2, sha256 95d41c667e1ac062).
// Para cambiar un valor: editar el YAML, regenerar y correr pruebas/ejecutar_todo.sh.
#pragma once

namespace cfg {
constexpr const char* HUELLA_YAML = "95d41c667e1ac062";
constexpr const char* MOTOR = "Pololu HPCB 12V 15:1";
constexpr const char* BARRA = "arco16c";
constexpr const char* MCU = "esp32_analogread";
constexpr const char* CONTROL = "C2";

// Motor (datos del fabricante a V_nom; ver YAML para el origen de cada valor)
constexpr float MOTOR_V_NOM = 12.0f;
constexpr float MOTOR_RPM = 2200.0f;
constexpr float MOTOR_PAR_BLOQUEO = 0.02451663f;   // N·m
constexpr float MOTOR_I_BLOQUEO = 0.75f;
constexpr float MOTOR_I_VACIO = 0.08f;
constexpr float MOTOR_LIMITE_V = 99.0f;      // 99 = sin límite

// Geometría y masa
constexpr float L_CUELLO = 0.11f;
constexpr float W_VIA = 0.085f;
constexpr float D_LLANTA = 0.034f;
constexpr float MASA = 0.1214f;

// Barra de sensores: posición de cada sensor en el marco del cuerpo (x adelante, y izquierda),
// índice 0 = extremo derecho. La estimación usa y (sf::estimar_coord).
constexpr int N_SENSORES = 16;
constexpr float SENSOR_X[N_SENSORES] = {0.1009231f, 0.1031585f, 0.105087f, 0.106703f, 0.1080015f, 0.1089789f, 0.109632f, 0.1099591f, 0.1099591f, 0.109632f, 0.1089789f, 0.1080015f, 0.106703f, 0.105087f, 0.1031585f, 0.1009231f};
constexpr float SENSOR_Y[N_SENSORES] = {0.0437553f, 0.03818805f, 0.03250722f, 0.0267297f, 0.02087267f, 0.01495356f, 0.008989962f, 0.002999628f, -0.002999628f, -0.008989962f, -0.01495356f, -0.02087267f, -0.0267297f, -0.03250722f, -0.03818805f, -0.0437553f};
constexpr float UMBRAL = 0.25f;

// Control
constexpr unsigned long PERIODO_MIN_US = 1000;
constexpr float T_PERDIDA = 0.3f;
constexpr float V_MAX = 1.2012f;
constexpr float A_LAT = 4.7758f;
constexpr float A_LON = 6.9268f;
constexpr float K_PP = 1.2387f;
constexpr float KP = 15.9363f;
constexpr float KD = 10.0005f;
constexpr float TAU_D = 0.004f;
constexpr float TAU_K = 0.0754f;
constexpr float PISO = -0.3108f;   // ciclo mínimo de la rueda interior
constexpr int FUENTE_CURVATURA = 0;   // 0 error (C2), 1 modelo del motor (C3m), 2 giroscopio (C3g)

// Batería
constexpr float V_BATERIA_BAJA = 6.8f;
}  // namespace cfg
