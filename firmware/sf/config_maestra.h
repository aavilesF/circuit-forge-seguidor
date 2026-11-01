// GENERADO por herramientas/generar_config_firmware.py — NO EDITAR A MANO.
// Fuente: config/robot_maestro.yaml (versión 2, sha256 33129ce01581dca9).
// Para cambiar un valor: editar el YAML, regenerar y correr pruebas/ejecutar_todo.sh.
#pragma once

namespace cfg {
constexpr const char* HUELLA_YAML = "33129ce01581dca9";
constexpr const char* MOTOR = "Chihai CHF-GM12-N20 12V 2200 RPM i10 (con encoder)";
constexpr const char* BARRA = "recta8_tcrt";
constexpr const char* MCU = "esp32_analogread";
constexpr const char* CONTROL = "C3m";

// Motor (datos del fabricante a V_nom; ver YAML para el origen de cada valor)
constexpr float MOTOR_V_NOM = 12.0f;
constexpr float MOTOR_RPM = 2200.0f;
constexpr float MOTOR_PAR_BLOQUEO = 0.01666526f;   // N·m
constexpr float MOTOR_I_BLOQUEO = 0.5f;
constexpr float MOTOR_I_VACIO = 0.05f;
constexpr float MOTOR_LIMITE_V = 99.0f;      // 99 = sin límite

// Geometría y masa
constexpr float L_CUELLO = 0.11f;
constexpr float W_VIA = 0.085f;
constexpr float D_LLANTA = 0.034f;
constexpr float MASA = 0.1319f;

// Barra de sensores: posición de cada sensor en el marco del cuerpo (x adelante, y izquierda),
// índice 0 = extremo derecho. La estimación usa y (sf::estimar_coord).
constexpr int N_SENSORES = 8;
constexpr float SENSOR_X[N_SENSORES] = {0.11f, 0.11f, 0.11f, 0.11f, 0.11f, 0.11f, 0.11f, 0.11f};
constexpr float SENSOR_Y[N_SENSORES] = {0.02975f, 0.02125f, 0.01275f, 0.00425f, -0.00425f, -0.01275f, -0.02125f, -0.02975f};
constexpr float UMBRAL = 0.25f;

// Control
constexpr unsigned long PERIODO_MIN_US = 1000;
constexpr float T_PERDIDA = 0.3f;
constexpr float V_MAX = 0.9588f;
constexpr float A_LAT = 9.692f;
constexpr float A_LON = 2.0f;
constexpr float K_PP = 1.5f;
constexpr float KP = 48.7166f;
constexpr float KD = 8.0461f;
constexpr float TAU_D = 0.004f;
constexpr float TAU_K = 0.0213f;
constexpr float PISO = -0.3531f;   // ciclo mínimo de la rueda interior
constexpr int FUENTE_CURVATURA = 1;   // 0 error (C2), 1 modelo del motor (C3m), 2 giroscopio (C3g)

// Batería
constexpr float V_BATERIA_BAJA = 6.8f;
}  // namespace cfg
